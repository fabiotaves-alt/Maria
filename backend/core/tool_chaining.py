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

from backend.core.config import (
    MAX_PASSOS_LEITURA,
    MAX_TENTATIVAS_CORRECAO_FERRAMENTA,
    LLAMA_TEMPERATURE_TOOLS_RETRY,
)
from backend.core.tools_schema import (
    FERRAMENTAS_LEITURA,
    executar_ferramenta_leitura,
    validar_argumentos_obrigatorios,
)
from backend.core.client_protocol import LLMClientProtocol

logger = logging.getLogger(__name__)


def encadear_leitura_stream(cliente: LLMClientProtocol, historico_com_system, tool_call_inicial, tools, apos_cada_chamada=None):
    """
    Generator que encadeia ferramentas de leitura a partir de uma tool call
    já obtida (`tool_call_inicial`), reenviando o resultado ao modelo via
    `cliente.continuar_com_resultado_ferramenta_stream` até encontrar uma
    ferramenta de escrita, nenhuma ferramenta, ou atingir MAX_PASSOS_LEITURA.

    Args:
        cliente: instância de LlamaClient (ou compatível).
        historico_com_system: histórico JÁ incluindo o system prompt (mesmo
            formato de ChatSession.get_historico_com_system()).
        tool_call_inicial: {"name": str, "arguments": dict} da primeira
            chamada ao modelo, ou None.
        tools: schema de ferramentas (TOOLS_SCHEMA).
        apos_cada_chamada: callback opcional `f(duracao_segundos: float,
            tokens_gerados: int)`, chamado logo após CADA chamada individual
            de continuação ser concluída. Se levantar uma exceção (ex.:
            TimeoutError), ela propaga normalmente e interrompe o
            encadeamento nesse ponto — usado pelo benchmark para aplicar
            timeout POR CHAMADA e somar os tokens da continuação ao total
            da tarefa.

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
        metricas_chamada: dict = {}
        inicio_chamada = time.monotonic()

        for chunk, tool_chunk in cliente.continuar_com_resultado_ferramenta_stream(
            historico=historico_com_system,
            tool_call=tool_call_atual,
            resultado=resultado_ferramenta,
            tools=tools,
            metricas_saida=metricas_chamada,
        ):
            if chunk is not None:
                yield chunk, None
            if tool_chunk is not None:
                novo_tool_call = tool_chunk

        if apos_cada_chamada is not None:
            apos_cada_chamada(time.monotonic() - inicio_chamada, metricas_chamada.get("tokens_gerados", 0))

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


FERRAMENTAS_ESCRITA = {"criar_planilha", "criar_documento", "editar_planilha"}


def validar_e_corrigir_tool_call_stream(cliente: LLMClientProtocol, historico_com_system, tool_call_atual, tools, apos_cada_chamada=None):
    """
    Generator que valida uma tool call de ESCRITA contra o schema (campos
    obrigatórios, tipos, sanitização de nome_arquivo) ANTES da confirmação do
    usuário. Ferramentas de leitura não são tratadas aqui (já resolvidas por
    encadear_leitura_stream) e NÃO há verificação de existência de arquivo.

    Se a validação falhar, o erro é reenviado ao modelo via
    cliente.continuar_com_resultado_ferramenta_stream (mesmo padrão de
    encadear_leitura_stream), com temperatura de correção
    (LLAMA_TEMPERATURE_TOOLS_RETRY), até MAX_TENTATIVAS_CORRECAO_FERRAMENTA
    vezes.

    Args:
        cliente: instância de LlamaClient.
        historico_com_system: histórico já incluindo o system prompt.
        tool_call_atual: {"name": str, "arguments": dict} da última tool call
            obtida, ou None.
        tools: schema de ferramentas (TOOLS_SCHEMA).
        apos_cada_chamada: callback opcional f(duracao_segundos, tokens_gerados),
            chamado após CADA chamada de correção. Se levantar exceção (ex.:
            TimeoutError), ela propaga e interrompe o processo nesse ponto.

    Yields:
        (chunk_texto | None, None) durante o streaming de correção.
        Último item: (None, {"tool_call": dict | None, "tentativas": int}).
    """
    if not tool_call_atual or tool_call_atual.get("name") not in FERRAMENTAS_ESCRITA:
        yield None, {"tool_call": tool_call_atual, "tentativas": 0, "correcoes": []}
        return

    tentativas = 0
    correcoes: list[dict] = []
    while tentativas < MAX_TENTATIVAS_CORRECAO_FERRAMENTA:
        try:
            validar_argumentos_obrigatorios(
                tool_call_atual["name"], tool_call_atual.get("arguments", {})
            )
            yield None, {"tool_call": tool_call_atual, "tentativas": tentativas, "correcoes": correcoes}
            return
        except ValueError as erro:
            tentativas += 1
            erro_str = str(erro)
            # Auto-sanitização de path traversal: em vez de devolver o erro ao
            # modelo (que responde com texto em vez de corrigir), corrige o
            # nome_arquivo e retenta a validação imediatamente. A correção é
            # registrada (antes → depois) para o log/relatório do benchmark.
            if "path traversal" in erro_str.lower() and "nome_arquivo" in tool_call_atual.get("arguments", {}):
                from backend.core.tools_schema import _sanitizar_nome_seguro
                nome_antes = tool_call_atual["arguments"]["nome_arquivo"]
                nome_depois = _sanitizar_nome_seguro(nome_antes)
                tool_call_atual["arguments"]["nome_arquivo"] = nome_depois
                if nome_antes != nome_depois:
                    correcoes.append({
                        "campo": "nome_arquivo",
                        "antes": nome_antes,
                        "depois": nome_depois,
                    })
                continue
            feedback = f"Erro na chamada da ferramenta: {erro}"
            logger.warning(
                "Tool call inválida (tentativa %s/%s): %s",
                tentativas, MAX_TENTATIVAS_CORRECAO_FERRAMENTA, feedback,
            )

            novo_tool_call = None
            metricas_chamada: dict = {}
            inicio_chamada = time.monotonic()

            for chunk, tool_chunk in cliente.continuar_com_resultado_ferramenta_stream(
                historico=historico_com_system,
                tool_call=tool_call_atual,
                resultado=feedback,
                tools=tools,
                metricas_saida=metricas_chamada,
                temperatura_override=LLAMA_TEMPERATURE_TOOLS_RETRY,
            ):
                if chunk is not None:
                    yield chunk, None
                if tool_chunk is not None:
                    novo_tool_call = tool_chunk

            if apos_cada_chamada is not None:
                apos_cada_chamada(time.monotonic() - inicio_chamada, metricas_chamada.get("tokens_gerados", 0))

            tool_call_atual = novo_tool_call
            if not tool_call_atual or tool_call_atual.get("name") not in FERRAMENTAS_ESCRITA:
                yield None, {"tool_call": tool_call_atual, "tentativas": tentativas, "correcoes": correcoes}
                return

    logger.warning("Limite de %s correções atingido sem tool call válida.", MAX_TENTATIVAS_CORRECAO_FERRAMENTA)
    yield None, {"tool_call": None, "tentativas": tentativas, "correcoes": correcoes}