"""
Módulo compartilhado de encadeamento de ferramentas de leitura.

Usado tanto pela aplicação interativa (main.py, via MariaController) quanto
pelo benchmark (benchmark/runners/maria_runner.py) para garantir que ambos
os caminhos tenham o mesmo comportamento: ferramentas de leitura
(listar_arquivos, resumir_documento) são executadas sem confirmação e o
resultado é reenviado ao modelo até MAX_PASSOS_LEITURA vezes, ou até uma
ferramenta de escrita (ou nenhuma ferramenta) ser retornada.
"""

import logging
import time

from core.config import MAX_PASSOS_LEITURA
from core.tools_schema import FERRAMENTAS_LEITURA, executar_ferramenta_leitura

logger = logging.getLogger(__name__)


def encadear_leitura_stream(cliente, historico_com_system, tool_call_inicial, tools, apos_cada_chamada=None):
    """
    Generator que encadeia ferramentas de leitura a partir de uma tool call
    já obtida (`tool_call_inicial`), reenviando o resultado ao modelo via
    `cliente.continuar_com_resultado_ferramenta_stream` até encontrar uma
    ferramenta de escrita, nenhuma ferramenta, ou atingir MAX_PASSOS_LEITURA.

    Args:
        cliente: instância de OllamaClient (ou compatível).
        historico_com_system: histórico JÁ incluindo o system prompt (mesmo
            formato de ChatSession.get_historico_com_system()).
        tool_call_inicial: {"name": str, "arguments": dict} da primeira
            chamada ao modelo, ou None.
        tools: schema de ferramentas (TOOLS_SCHEMA).
        apos_cada_chamada: callback opcional `f(duracao_segundos: float)`,
            chamado logo após CADA chamada individual de continuação ser
            concluída. Se levantar uma exceção (ex.: TimeoutError), ela
            propaga normalmente e interrompe o encadeamento nesse ponto —
            usado pelo benchmark para aplicar timeout POR CHAMADA.

    Yields:
        (chunk_texto | None, None) durante o streaming de texto; o último
        item sempre é (None, tool_call_final), onde tool_call_final é a
        ferramenta de escrita encontrada, ou None.
    """
    tool_call_atual = tool_call_inicial
    passos = 0

    while (
        tool_call_atual
        and tool_call_atual.get("name") in FERRAMENTAS_LEITURA
        and passos < MAX_PASSOS_LEITURA
    ):
        try:
            resultado_ferramenta = executar_ferramenta_leitura(
                tool_call_atual["name"], tool_call_atual.get("arguments", {})
            )
        except (PermissionError, OSError, ValueError) as error:
            logger.error(f"Erro ao executar ferramenta de leitura: {error}")
            resultado_ferramenta = f"Erro ao acessar o sistema de arquivos: {error}"

        novo_tool_call = None
        inicio_chamada = time.monotonic()

        for chunk, tool_chunk in cliente.continuar_com_resultado_ferramenta_stream(
            historico=historico_com_system,
            tool_call=tool_call_atual,
            resultado=resultado_ferramenta,
            tools=tools,
        ):
            if chunk is not None:
                yield chunk, None
            if tool_chunk is not None:
                novo_tool_call = tool_chunk

        if apos_cada_chamada is not None:
            apos_cada_chamada(time.monotonic() - inicio_chamada)

        tool_call_atual = novo_tool_call
        passos += 1

    if tool_call_atual and tool_call_atual.get("name") in FERRAMENTAS_LEITURA:
        logger.warning("Limite de passos de leitura atingido sem resposta final.")
        aviso = (
            "\n\nNão consegui concluir a consulta após várias tentativas. "
            "Tente reformular o pedido."
        )
        yield aviso, None
        tool_call_atual = None

    yield None, tool_call_atual