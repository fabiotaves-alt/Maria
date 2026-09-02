"""Runner que executa uma MariaTask usando o código real da MARIA."""
import logging
import os
import re
import sys
import time

from openpyxl import Workbook

# Os módulos da aplicação são módulos locais, não um pacote instalado.
MARIA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if MARIA_ROOT not in sys.path:
    sys.path.insert(0, MARIA_ROOT)

from core.chat_session import ChatSession, interpretar_confirmacao
from core.llama_client import (
    LlamaClient as OllamaClient,
    LlamaClientError as OllamaClientError,
    LlamaTimeoutError as OllamaTimeoutError,
    _montar_mensagens_com_reforco,
    montar_sampler_params,
)
from core.tools_schema import TOOLS_SCHEMA, executar_ferramenta_real, FERRAMENTAS_LEITURA
from core.tool_chaining import encadear_leitura_stream

from ..benchmark_config import (
    BENCHMARK_ARQUIVOS_DIR,
    BENCHMARK_MAX_RETRIES,
    BENCHMARK_RETRY_BACKOFF_SECONDS,
    BENCHMARK_TASK_TIMEOUT,
)
from ..analysis.language_check import resposta_em_portugues
from ..tasks.task_schema import MariaTask, MariaTaskResult

logger = logging.getLogger(__name__)


class MariaRunner:
    """Executa tarefas MARIA sem passar pelo loop interativo da CLI."""

    def __init__(
        self,
        cliente: OllamaClient | None = None,
        num_predict: int | None = None,
        modelo_carregado: str | None = None,
    ):
        self.cliente = cliente or OllamaClient(num_predict=num_predict)
        # Usa o modelo efetivamente carregado no llama-server se disponível,
        # caso contrário fallback para o model do cliente ou LLAMA_MODEL.
        self.modelo_efetivo = modelo_carregado or getattr(cliente, "model", None)
        # Snapshot único dos parâmetros de sampler efetivos (config atual).
        self.sampler_params = montar_sampler_params()

    def run(self, task: MariaTask) -> MariaTaskResult:
        original_pasta = os.environ.get("PASTA_ARQUIVOS_GERADOS")
        os.environ["PASTA_ARQUIVOS_GERADOS"] = BENCHMARK_ARQUIVOS_DIR
        os.makedirs(BENCHMARK_ARQUIVOS_DIR, exist_ok=True)
        self._garantir_planilha_existente(task)

        inicio = time.monotonic()
        sessao = ChatSession()
        for message in task.context:
            sessao.adicionar_mensagem(message["role"], message["content"])

        errors: list[dict] = []
        tool_call_final = None
        resposta_textual = ""
        prompt_enviado: list[dict] = []
        resposta_bruta_modelo = ""
        tokens_gerados = 0
        tokens_por_segundo = 0.0
        ttft_ms = None
        confirmation_completed = not task.confirm_sequence

        try:
            resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo, ttft_ms, prompt_enviado = self._enviar_com_retry(sessao, task)
            resposta_bruta_modelo = resposta_textual
            if time.monotonic() - inicio > BENCHMARK_TASK_TIMEOUT:
                raise TimeoutError(
                    f"Tarefa excedeu o timeout de {BENCHMARK_TASK_TIMEOUT} segundos."
                )

            if tool_call_final and tool_call_final.get("name") in FERRAMENTAS_LEITURA:
                historico_continuacao = sessao.get_historico_com_system()

                def _apos_chamada_de_continuacao(duracao_chamada: float, tokens_chamada: int) -> None:
                    """Timeout POR CHAMADA (não acumulado) + soma dos tokens da
                    continuação a tokens_gerados, que antes só refletia a
                    primeira chamada (mascarando o custo real da tarefa)."""
                    nonlocal tokens_gerados
                    if duracao_chamada > BENCHMARK_TASK_TIMEOUT:
                        raise TimeoutError(
                            f"Uma chamada de continuação (leitura) excedeu o "
                            f"timeout de {BENCHMARK_TASK_TIMEOUT} segundos."
                        )
                    tokens_gerados += tokens_chamada

                resposta_continuacao = ""
                novo_tool_call_final = None
                for chunk, tool_chunk in encadear_leitura_stream(
                    self.cliente, historico_continuacao, tool_call_final, TOOLS_SCHEMA,
                    apos_cada_chamada=_apos_chamada_de_continuacao,
                ):
                    if chunk is not None:
                        resposta_continuacao += chunk
                    if tool_chunk is not None:
                        novo_tool_call_final = tool_chunk

                tool_call_final = novo_tool_call_final
                if resposta_continuacao.strip():
                    resposta_textual = resposta_continuacao
                    # A resposta bruta do modelo inclui a continuação (leitura encadeada).
                    resposta_bruta_modelo = (resposta_bruta_modelo + "\n" + resposta_continuacao).strip()

            if tool_call_final and task.confirm_sequence:
                ambiguidades = 0
                for resposta_usuario in task.confirm_sequence:
                    resultado = interpretar_confirmacao(resposta_usuario)
                    if resultado is True:
                        caminho = executar_ferramenta_real(
                            tool_call_final["name"], tool_call_final["arguments"]
                        )
                        resposta_textual = caminho
                        confirmation_completed = True
                        break
                    if resultado is False:
                        resposta_textual = "Ação cancelada."
                        confirmation_completed = True
                        tool_call_final = None  # ferramenta não foi executada
                        break
                    ambiguidades += 1
                    if ambiguidades >= 2:
                        resposta_textual = "Ação cancelada por ambiguidade."
                        confirmation_completed = True
                        tool_call_final = None  # ferramenta não foi executada
                        break

            if time.monotonic() - inicio > BENCHMARK_TASK_TIMEOUT:
                raise TimeoutError(
                    f"Tarefa excedeu o timeout de {BENCHMARK_TASK_TIMEOUT} segundos."
                )

        except (PermissionError, OSError, ValueError, TimeoutError) as error:
            logger.error("Erro na tarefa %s: %s", task.id, error)
            errors.append({"kind": type(error).__name__, "message": str(error)})
            if not resposta_textual.strip():
                resposta_textual = f"[ERRO] {error}"
        except OllamaClientError as error:
            logger.error("Erro do Ollama na tarefa %s: %s", task.id, error)
            errors.append({"kind": "OllamaClientError", "message": str(error)})
        except Exception as error:
            logger.exception("Erro inesperado na tarefa %s", task.id)
            errors.append({"kind": "InternalError", "message": str(error)})
        finally:
            if original_pasta is None:
                os.environ.pop("PASTA_ARQUIVOS_GERADOS", None)
            else:
                os.environ["PASTA_ARQUIVOS_GERADOS"] = original_pasta

        latency_ms = (time.monotonic() - inicio) * 1000
        detected_name = tool_call_final.get("name") if tool_call_final else None
        if task.tools_aceitos is not None:
            tool_correct = detected_name in task.tools_aceitos
        elif task.expected_tool is not None:
            tool_correct = detected_name == task.expected_tool
        else:
            tool_correct = detected_name is None
        args_correct = self._argumentos_compativeis(
            (tool_call_final or {}).get("arguments", {}), task.expected_args_subset
        )
        keyword_match = (
            not task.expected_keywords
            or any(keyword.lower() in resposta_textual.lower() for keyword in task.expected_keywords)
        )
        language_ok = resposta_em_portugues(resposta_textual)

        return MariaTaskResult(
            task_id=task.id,
            task_name=task.name,
            category=task.category.value,
            model=self.modelo_efetivo or self.cliente.model,
            tool_detected=detected_name,
            tool_correct=tool_correct,
            confirmation_completed=confirmation_completed,
            keyword_match=keyword_match,
            runtime_ok=not errors,
            final_message=resposta_textual,
            latency_ms=latency_ms,
            errors=errors,
            raw_tool_args=(tool_call_final or {}).get("arguments", {}),
            language_ok=language_ok,
            tokens_gerados=tokens_gerados,
            tokens_por_segundo=tokens_por_segundo,
            args_correct=args_correct,
            ttft_ms=ttft_ms,
            prompt_enviado=prompt_enviado,
            resposta_bruta_modelo=resposta_bruta_modelo,
            sampler_params=self.sampler_params,
        )

    @staticmethod
    def _argumentos_compativeis(obtidos: dict, esperados: dict | None) -> bool:
        """Verifica se os argumentos obtidos contêm, com valores iguais,
        todas as chaves declaradas em `esperados` (comparação de
        subconjunto — campos extras nos argumentos obtidos, como
        'descricao', não invalidam o resultado). Retorna True quando
        `esperados` é None (tarefa não define critério de argumento)."""
        if esperados is None:
            return True
        if not isinstance(obtidos, dict):
            return False
        return all(
            chave in obtidos and obtidos[chave] == valor
            for chave, valor in esperados.items()
        )

    @staticmethod
    def _garantir_planilha_existente(task: MariaTask) -> None:
        """Cria fixtures declaradas pelo contexto da tarefa, se necessário."""
        match = re.search(r"planilha\s+([^\s]+)\.xlsx\s+já foi criada", " ".join(
            message["content"] for message in task.context
        ), re.IGNORECASE)
        if not match:
            return

        # Extrair nome do arquivo sem extensão para evitar duplicação
        nome_arquivo = match.group(1)
        if nome_arquivo.endswith('.xlsx'):
            nome_arquivo = nome_arquivo[:-5]
        
        caminho = os.path.join(BENCHMARK_ARQUIVOS_DIR, nome_arquivo + ".xlsx")
        if os.path.exists(caminho):
            return

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Dados"
        worksheet.cell(row=1, column=1, value="Fixture do benchmark")
        workbook.save(caminho)

    def _enviar_com_retry(self, sessao: ChatSession, task: MariaTask):
        tentativas = 0
        while True:
            try:
                historico = sessao.get_historico_com_system()
                # Prompt EXATAMENTE como será enviado ao modelo (mesma montagem
                # de chat_com_tools_stream_com_metricas via _montar_mensagens_com_reforco).
                prompt_enviado = _montar_mensagens_com_reforco(historico, task.user_message)
                metodo_metricas = getattr(self.cliente, "chat_com_tools_stream_com_metricas", None)
                if callable(metodo_metricas):
                    resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo, ttft_ms = (
                        metodo_metricas(
                            mensagem_usuario=task.user_message,
                            historico=historico,
                            tools=TOOLS_SCHEMA,
                        )
                    )
                    return resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo, ttft_ms, prompt_enviado

                resposta_textual = ""
                tool_call_final = None
                for chunk, tool_chunk in self.cliente.chat_com_tools_stream(
                    mensagem_usuario=task.user_message,
                    historico=historico,
                    tools=TOOLS_SCHEMA,
                ):
                    if chunk is not None:
                        resposta_textual += chunk
                    if tool_chunk is not None:
                        tool_call_final = tool_chunk
                return resposta_textual, tool_call_final, 0, 0.0, None, prompt_enviado
            except OllamaTimeoutError:
                raise
            except OllamaClientError:
                tentativas += 1
                if tentativas > BENCHMARK_MAX_RETRIES:
                    raise
                logger.warning(
                    "Tentativa %s/%s falhou para a tarefa %s; aguardando %.1fs",
                    tentativas,
                    BENCHMARK_MAX_RETRIES,
                    task.id,
                    BENCHMARK_RETRY_BACKOFF_SECONDS,
                )
                time.sleep(BENCHMARK_RETRY_BACKOFF_SECONDS)

    def run_repeated(
        self, task: "MariaTask", repeticoes: int, apos_cada_execucao=None
    ) -> list["MariaTaskResult"]:
        """Executa a mesma tarefa N vezes e retorna a lista de resultados individuais.

        apos_cada_execucao: callback opcional f(indice_execucao: int, resultado:
            MariaTaskResult), chamado logo após cada execução individual ser
            concluída — usado para exibir progresso em tempo real no terminal.
        """
        resultados = []
        for indice in range(1, repeticoes + 1):
            resultado = self.run(task)
            resultados.append(resultado)
            if apos_cada_execucao is not None:
                apos_cada_execucao(indice, resultado)
        return resultados
