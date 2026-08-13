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
from core.ollama_client import OllamaClient, OllamaClientError, OllamaTimeoutError
from core.tools_schema import TOOLS_SCHEMA, executar_ferramenta_real

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

    def __init__(self, cliente: OllamaClient | None = None, num_predict: int | None = None):
        self.cliente = cliente or OllamaClient(num_predict=num_predict)

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
        tokens_gerados = 0
        tokens_por_segundo = 0.0
        confirmation_completed = not task.confirm_sequence

        try:
            resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo = self._enviar_com_retry(sessao, task)
            if time.monotonic() - inicio > BENCHMARK_TASK_TIMEOUT:
                raise TimeoutError(
                    f"Tarefa excedeu o timeout de {BENCHMARK_TASK_TIMEOUT} segundos."
                )

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
                        break
                    ambiguidades += 1
                    if ambiguidades >= 2:
                        resposta_textual = "Ação cancelada por ambiguidade."
                        confirmation_completed = True
                        break

            if time.monotonic() - inicio > BENCHMARK_TASK_TIMEOUT:
                raise TimeoutError(
                    f"Tarefa excedeu o timeout de {BENCHMARK_TASK_TIMEOUT} segundos."
                )

        except (PermissionError, OSError, ValueError, TimeoutError) as error:
            logger.error("Erro na tarefa %s: %s", task.id, error)
            errors.append({"kind": type(error).__name__, "message": str(error)})
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
        keyword_match = (
            not task.expected_keywords
            or any(keyword.lower() in resposta_textual.lower() for keyword in task.expected_keywords)
        )
        language_ok = resposta_em_portugues(resposta_textual)

        return MariaTaskResult(
            task_id=task.id,
            task_name=task.name,
            category=task.category.value,
            model=self.cliente.model,
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
        )

    @staticmethod
    def _garantir_planilha_existente(task: MariaTask) -> None:
        """Cria fixtures declaradas pelo contexto da tarefa, se necessário."""
        match = re.search(r"planilha\s+([^\s]+)\.xlsx\s+já foi criada", " ".join(
            message["content"] for message in task.context
        ), re.IGNORECASE)
        if not match:
            return

        caminho = os.path.join(BENCHMARK_ARQUIVOS_DIR, match.group(1) + ".xlsx")
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
                metodo_metricas = getattr(self.cliente, "chat_com_tools_stream_com_metricas", None)
                if callable(metodo_metricas):
                    resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo = (
                        metodo_metricas(
                            mensagem_usuario=task.user_message,
                            historico=historico,
                            tools=TOOLS_SCHEMA,
                        )
                    )
                    return resposta_textual, tool_call_final, tokens_gerados, tokens_por_segundo

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
                return resposta_textual, tool_call_final, 0, 0.0
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

    def run_repeated(self, task: "MariaTask", repeticoes: int) -> list["MariaTaskResult"]:
        """Executa a mesma tarefa N vezes e retorna a lista de resultados individuais."""
        return [self.run(task) for _ in range(repeticoes)]