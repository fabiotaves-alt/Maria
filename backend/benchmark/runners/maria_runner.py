"""Runner que executa uma MariaTask usando o código real da MARIA."""
import logging
import os
import re
import shutil
import sys
import time
import unicodedata
from typing import Any

from openpyxl import Workbook

# Os módulos da aplicação são módulos locais, não um pacote instalado.
MARIA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if MARIA_ROOT not in sys.path:
    sys.path.insert(0, MARIA_ROOT)

from core.chat_session import ChatSession, interpretar_confirmacao
from core.config import LLAMA_NUM_CTX
from core.llama_client import (
    LlamaClient,
    LlamaClientError,
    LlamaTimeoutError,
    _montar_mensagens_com_reforco,
    montar_sampler_params,
)
from core.client_protocol import LLMClientProtocol
from core.tools_schema import TOOLS_SCHEMA, executar_ferramenta_real, FERRAMENTAS_LEITURA
from core.tool_chaining import encadear_leitura_stream, validar_e_corrigir_tool_call_stream, FERRAMENTAS_ESCRITA

from ..benchmark_config import (
    BENCHMARK_ARQUIVOS_DIR,
    BENCHMARK_MAX_RETRIES,
    BENCHMARK_RETRY_BACKOFF_SECONDS,
    BENCHMARK_TASK_TIMEOUT,
    BENCHMARK_TIMEOUT_POR_CHAMADA,
)
from ..utils import MARGEM_RESERVA_RESPOSTA, estimar_tokens_calibrado
from ..analysis.language_check import resposta_em_portugues
from ..tasks.task_schema import MariaTask, MariaTaskResult

logger = logging.getLogger(__name__)

# Marcadores de estouro de contexto na mensagem de erro do llama-server.
# 'contexto' sozinho cobre mensagens localizadas em português (ex: o pre-check
# do próprio runner); os demais são os erros em inglês do llama.cpp.
MARCAS_CONTEXTO = (
    "exceeds the available context size",
    "exceeds the context size",
    "context size",
    "too many tokens",
    "excede o contexto",
    "contexto",
)


def _eh_erro_de_contexto(mensagem: str) -> bool:
    """True se a mensagem de erro indica estouro de contexto do servidor."""
    texto = (mensagem or "").lower()
    return any(marca in texto for marca in MARCAS_CONTEXTO)


class MariaRunner:
    """Executa tarefas MARIA sem passar pelo loop interativo da CLI."""

    def __init__(
        self,
        cliente: LLMClientProtocol | None = None,
        num_predict: int | None = None,
        modelo_carregado: str | None = None,
        ctx_size: int | None = None,
    ):
        self.cliente = cliente or LlamaClient(num_predict=num_predict)
        # Usa o modelo efetivamente carregado no llama-server se disponível,
        # caso contrário fallback para o model do cliente ou LLAMA_MODEL.
        self.modelo_efetivo = modelo_carregado or getattr(cliente, "model", None)
        # Contexto efetivo: valor real detectado no servidor (meta.n_ctx de
        # /v1/models) quando repassado pelo run_benchmark; fallback para o
        # valor configurado (LLAMA_NUM_CTX).
        self.ctx_size = int(ctx_size) if ctx_size else LLAMA_NUM_CTX
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
        contexto_ok = True
        correction_attempts = 0
        finish_reason: str | None = None
        degeneracao_detectada = False
        cadeia_ferramentas: list[str] = []
        tool_call_inicial: dict = {}

        try:
            (
                resposta_textual, tool_call_final, tokens_gerados,
                tokens_por_segundo, ttft_ms, prompt_enviado, extras,
            ) = self._enviar_com_retry(sessao, task)
            # Registro da cadeia de ferramentas: a tool call inicial é a
            # verificação de leitura (ex.: listar_arquivos) que dispara o
            # encadeamento; as demais entram via detected_name no fim do run().
            if tool_call_final:
                tool_call_inicial = dict(tool_call_final)
                nome_inicial = tool_call_final.get("name")
                if nome_inicial and nome_inicial not in cadeia_ferramentas:
                    cadeia_ferramentas.append(nome_inicial)
            finish_reason = (extras or {}).get("finish_reason")
            degeneracao_detectada = bool((extras or {}).get("degeneracao_detectada"))
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
                    if duracao_chamada > BENCHMARK_TIMEOUT_POR_CHAMADA:
                        raise TimeoutError(
                            f"Uma chamada de continuação (leitura) excedeu o "
                            f"timeout de {BENCHMARK_TIMEOUT_POR_CHAMADA} segundos "
                            f"(limite por chamada, não acumulado)."
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

            correction_attempts = 0
            if tool_call_final and tool_call_final.get("name") in FERRAMENTAS_ESCRITA:
                historico_validacao = sessao.get_historico_com_system()

                def _apos_chamada_de_correcao(duracao_chamada: float, tokens_chamada: int) -> None:
                    nonlocal tokens_gerados
                    if duracao_chamada > BENCHMARK_TIMEOUT_POR_CHAMADA:
                        raise TimeoutError(
                            f"Uma chamada de correção de tool call excedeu o "
                            f"timeout de {BENCHMARK_TIMEOUT_POR_CHAMADA} segundos "
                            f"(limite por chamada, não acumulado)."
                        )
                    tokens_gerados += tokens_chamada

                resposta_correcao = ""
                resultado_validacao = None
                for chunk, resultado in validar_e_corrigir_tool_call_stream(
                    self.cliente, historico_validacao, tool_call_final, TOOLS_SCHEMA,
                    apos_cada_chamada=_apos_chamada_de_correcao,
                ):
                    if chunk is not None:
                        resposta_correcao += chunk
                    if resultado is not None:
                        resultado_validacao = resultado

                if resultado_validacao is not None:
                    tool_call_final = resultado_validacao["tool_call"]
                    correction_attempts = resultado_validacao["tentativas"]
                    if tool_call_final is None:
                        # Sem tool call após as tentativas de correção: não há
                        # nada a confirmar/executar; a tarefa segue sem ferramenta.
                        confirmation_completed = True
                if resposta_correcao.strip():
                    resposta_textual = resposta_correcao
                    resposta_bruta_modelo = (resposta_bruta_modelo + "\n" + resposta_correcao).strip()

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
        except LlamaClientError as error:
            erro_str = str(error)
            # Detecta estouro de contexto do llama-server (prompt > ctx_size).
            if _eh_erro_de_contexto(erro_str):
                contexto_ok = False
                logger.error("ERRO DE CONTEXTO na tarefa %s: %s", task.id, error)
            else:
                logger.error("Erro do Llama na tarefa %s: %s", task.id, error)
            errors.append({"kind": "LlamaClientError", "message": erro_str})
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
        if detected_name and detected_name not in cadeia_ferramentas:
            cadeia_ferramentas.append(detected_name)
        # Tarefas com ferramenta obrigatória na cadeia (ex.: verificar com
        # listar_arquivos antes de responder): todas as ferramentas exigidas
        # precisam ter sido chamadas e a execução precisa terminar em texto
        # (nenhuma ferramenta de escrita pendente ao final).
        if task.tools_obrigatorios:
            tool_correct = (
                all(nome in cadeia_ferramentas for nome in task.tools_obrigatorios)
                and detected_name is None
            )
        elif task.tools_aceitos is not None:
            tool_correct = detected_name in task.tools_aceitos
        elif task.expected_tool is not None:
            tool_correct = detected_name == task.expected_tool
        else:
            tool_correct = detected_name is None
        args_correct = self._argumentos_compativeis(
            (tool_call_final or {}).get("arguments", {}), task.expected_args_subset
        )
        texto_norm = MariaRunner._normalizar_texto(resposta_textual)
        keyword_match = (
            not task.expected_keywords
            or any(MariaRunner._normalizar_texto(kw) in texto_norm for kw in task.expected_keywords)
        )
        language_ok = resposta_em_portugues(resposta_textual)

        # Diagnóstico de parser: sem tool call detectada mas com padrão de
        # chamada conhecida na resposta bruta → suspeita de falha do parser,
        # não de "modelo não chamou".
        parse_suspeito = False
        if tool_call_final is None and resposta_bruta_modelo:
            from backend.core.tool_call_textual_parser import POSITIONAL_MAP
            nomes = "|".join(re.escape(nome) for nome in POSITIONAL_MAP)
            if re.search(rf"\b({nomes})\s*[:(]", resposta_bruta_modelo):
                parse_suspeito = True

        # Motivo de falha por geração degenerada (loop de repetição): aparece
        # na seção "Tarefas com falha" do relatório em vez de erro genérico.
        if degeneracao_detectada:
            errors.append({
                "kind": "DegenerateGeneration",
                "message": (
                    "Geração degenerada detectada: repetição excessiva de um "
                    "mesmo caractere; stream interrompido para evitar desperdício "
                    "de tokens."
                ),
            })

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
            contexto_ok=contexto_ok,
            correction_attempts=correction_attempts,
            confirmacao_elegivel=bool(task.confirm_sequence),
            parse_suspeito=parse_suspeito,
            finish_reason=finish_reason,
            prompt_enviado=prompt_enviado,
            resposta_bruta_modelo=resposta_bruta_modelo,
            sampler_params=self.sampler_params,
            cadeia_ferramentas=cadeia_ferramentas,
            tool_call_inicial=tool_call_inicial,
        )

    @staticmethod
    def _normalizar_texto(texto: str) -> str:
        """Remove acentos e converte para minúsculas.

        Evita falsos negativos como 'não encontrado' vs 'nao encontrado'.
        """
        texto = texto.lower()
        texto = unicodedata.normalize('NFKD', texto)
        return ''.join(c for c in texto if not unicodedata.combining(c))

    @staticmethod
    def _normalizar_valor(chave: str, valor: Any) -> Any:
        """Normaliza o valor de um argumento antes da comparação.

        - nome_arquivo: remove extensões conhecidas (.xlsx, .xls, .docx, .doc)
        - listas: preserva como lista (a comparação usa set)
        - demais: retorna inalterado
        """
        if chave == 'nome_arquivo' and isinstance(valor, str):
            for ext in ('.xlsx', '.xls', '.docx', '.doc'):
                if valor.lower().endswith(ext):
                    return valor[:-len(ext)]
        return valor

    @staticmethod
    def _argumentos_compativeis(obtidos: dict, esperados: dict | None) -> bool:
        """Verifica se os argumentos obtidos contêm, com valores equivalentes,
        todas as chaves declaradas em `esperados`. Normalizações aplicadas:
        - Chaves do dict são convertidas para minúsculas.
        - nome_arquivo tem extensão removida.
        - Listas (ex: colunas) são comparadas como conjuntos (ordem não importa).
        Retorna True quando `esperados` é None (tarefa não define critério
        de argumento)."""
        if esperados is None:
            return True
        if not isinstance(obtidos, dict):
            return False

        # --- 1. Normaliza chaves para minusculas ---
        obtidos_norm = {k.lower(): v for k, v in obtidos.items()}

        # --- 2. Verifica subconjunto esperado ---
        for chave, valor_esperado in esperados.items():
            chave_lc = chave.lower()
            if chave_lc not in obtidos_norm:
                return False
            valor_obtido = obtidos_norm[chave_lc]

            # --- 3. Normaliza valores por campo ---
            valor_obtido = MariaRunner._normalizar_valor(chave_lc, valor_obtido)
            valor_esperado = MariaRunner._normalizar_valor(chave_lc, valor_esperado)

            # --- 4. Compara listas como conjuntos (ordem nao importa) ---
            if isinstance(valor_esperado, list) and isinstance(valor_obtido, list):
                set_obtido = {str(x).strip() for x in valor_obtido}
                set_esperado = {str(x).strip() for x in valor_esperado}
                if set_obtido != set_esperado:
                    return False
            # --- 5. Comparacao direta para demais tipos ---
            elif valor_obtido != valor_esperado:
                return False

        return True

    @staticmethod
    def _garantir_planilha_existente(task: MariaTask) -> None:
        """Cria as fixtures declaradas em `task.fixtures`, se necessário."""
        for nome_arquivo in task.fixtures:
            if nome_arquivo.endswith(".xlsx"):
                nome_arquivo = nome_arquivo[:-5]

            caminho = os.path.join(BENCHMARK_ARQUIVOS_DIR, nome_arquivo + ".xlsx")
            if os.path.exists(caminho):
                continue

            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "Dados"
            worksheet.cell(row=1, column=1, value="Fixture do benchmark")
            workbook.save(caminho)

    @staticmethod
    def _verificar_timeout_por_chamada(inicio_tentativa: float) -> None:
        """Timeout POR CHAMADA individual ao modelo (não acumulado com retries).

        Diferencia uma tarefa que falhou por UMA chamada lenta de uma que
        estourou pelo acumulo de várias chamadas/continuações.
        """
        duracao_s = time.monotonic() - inicio_tentativa
        if duracao_s > BENCHMARK_TIMEOUT_POR_CHAMADA:
            raise TimeoutError(
                f"Chamada ao modelo excedeu {BENCHMARK_TIMEOUT_POR_CHAMADA}s "
                f"(timeout por chamada). Latência: {duracao_s:.1f}s"
            )

    def _verificar_contexto_disponivel(self, prompt_enviado: list[dict]) -> None:
        """Aborta ANTES de enviar se o prompt estimado não couber no contexto.

        Estimativa calibrada no warmup (fator medido via /tokenize) com margem
        de MARGEM_RESERVA_RESPOSTA (30% do contexto) reservada à resposta do
        modelo. Levanta LlamaClientError com marcador de contexto — o run()
        classifica contexto_ok=False e o retry é pulado (estouro de contexto é
        determinístico: tentar de novo não resolve).
        """
        prompt_texto = " ".join(str(m.get("content") or "") for m in prompt_enviado)
        prompt_tokens = estimar_tokens_calibrado(prompt_texto)
        limite = int(self.ctx_size * (1 - MARGEM_RESERVA_RESPOSTA))
        if prompt_tokens > limite:
            reserva = int(self.ctx_size * MARGEM_RESERVA_RESPOSTA)
            raise LlamaClientError(
                f"Prompt de ~{prompt_tokens} tokens excede o contexto disponivel "
                f"de {self.ctx_size} tokens (margem de reserva: {reserva}). "
                f"Reduza o system prompt ou aumente --ctx-size do servidor."
            )

    def _enviar_com_retry(self, sessao: ChatSession, task: MariaTask):
        tentativas = 0
        while True:
            try:
                historico = sessao.get_historico_com_system()
                # Prompt EXATAMENTE como será enviado ao modelo (mesma montagem
                # de chat_com_tools_stream_com_metricas via _montar_mensagens_com_reforco).
                prompt_enviado = _montar_mensagens_com_reforco(historico, task.user_message)
                # Pre-check: evita desperdiçar uma execução com prompt que não cabe.
                self._verificar_contexto_disponivel(prompt_enviado)
                inicio_tentativa = time.monotonic()
                metodo_metricas = getattr(self.cliente, "chat_com_tools_stream_com_metricas", None)
                if callable(metodo_metricas):
                    extras: dict = {}
                    resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo, ttft_ms = (
                        metodo_metricas(
                            mensagem_usuario=task.user_message,
                            historico=historico,
                            tools=TOOLS_SCHEMA,
                            extras_saida=extras,
                        )
                    )
                    self._verificar_timeout_por_chamada(inicio_tentativa)
                    return resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo, ttft_ms, prompt_enviado, extras

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
                self._verificar_timeout_por_chamada(inicio_tentativa)
                return resposta_textual, tool_call_final, 0, 0.0, None, prompt_enviado, {}
            except LlamaTimeoutError:
                raise
            except LlamaClientError as error:
                # Estouro de contexto é determinístico: retry não resolve.
                if _eh_erro_de_contexto(str(error)):
                    raise
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
            # Limpa arquivos gerados em execuções anteriores para garantir
            # isolamento de estado entre repetições da mesma tarefa.
            if os.path.isdir(BENCHMARK_ARQUIVOS_DIR):
                for item in os.listdir(BENCHMARK_ARQUIVOS_DIR):
                    item_path = os.path.join(BENCHMARK_ARQUIVOS_DIR, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except OSError:
                        pass
            resultado = self.run(task)
            resultados.append(resultado)
            if apos_cada_execucao is not None:
                apos_cada_execucao(indice, resultado)
        return resultados
