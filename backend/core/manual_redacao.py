"""
Módulo de consulta RAG (via SQLite FTS5) ao Manual de Redação da
Presidência da República. Usado pela ferramenta de leitura
'consultar_manual_redacao' (ver core/tools_schema.py).
"""

import logging
import sqlite3

from backend.database.connection import get_connection
from backend.core.config import MANUAL_REDACAO_TOP_K, MANUAL_REDACAO_MAX_CHARS_POR_TRECHO

logger = logging.getLogger(__name__)

TIPOS_VALIDOS = {
    "oficio",
    "exposicao_motivos",
    "mensagem",
    "email",
    "geral",
    "elaboracao_normativa",
    "processo_legislativo",
}


def _montar_query_fts(termo_busca: str) -> str:
    """
    Monta uma query segura para FTS5 MATCH a partir de texto livre do
    usuário, tratando cada palavra como termo obrigatório (AND implícito)
    e escapando aspas duplas.
    """
    palavras = [p.strip() for p in termo_busca.split() if p.strip()]
    termos_escapados = [f'"{p.replace(chr(34), "")}"' for p in palavras]
    return " ".join(termos_escapados)


def consultar_manual(
    tipo_documento: str | None = None,
    termo_busca: str | None = None,
    limite: int | None = None,
) -> str:
    """
    Consulta o Manual de Redação da Presidência da República.

    Args:
        tipo_documento: um de TIPOS_VALIDOS, ou None/"geral" para não filtrar.
        termo_busca: palavras-chave opcionais para refinar a busca textual.
        limite: número máximo de trechos retornados (padrão: MANUAL_REDACAO_TOP_K).

    Returns:
        Texto formatado com os trechos encontrados, pronto para ser
        devolvido ao modelo como resultado de ferramenta de leitura. Cada
        trecho é truncado em MANUAL_REDACAO_MAX_CHARS_POR_TRECHO caracteres
        para evitar estourar o contexto do modelo (ver OLLAMA_NUM_CTX /
        LLAMA_NUM_CTX em core/config.py).
    """
    limite = limite or MANUAL_REDACAO_TOP_K

    if tipo_documento and tipo_documento not in TIPOS_VALIDOS:
        tipo_documento = None  # ignora filtro inválido em vez de falhar

    conn = get_connection()
    cursor = conn.cursor()

    condicoes = []
    parametros: list = []

    if termo_busca and termo_busca.strip():
        query_fts = _montar_query_fts(termo_busca)
        condicoes.append("manual_redacao_fts MATCH ?")
        parametros.append(query_fts)

    if tipo_documento:
        condicoes.append("tipo_documento = ?")
        parametros.append(tipo_documento)

    where_clause = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
    ordenacao = "ORDER BY bm25(manual_redacao_fts)" if termo_busca else ""

    sql = f"""
        SELECT secao, conteudo FROM manual_redacao_fts
        {where_clause}
        {ordenacao}
        LIMIT ?
    """
    parametros.append(limite)

    try:
        cursor.execute(sql, parametros)
        linhas = cursor.fetchall()
    except sqlite3.OperationalError as error:
        logger.error(f"Erro ao consultar manual_redacao_fts: {error}")
        return (
            "O Manual de Redação da Presidência da República ainda não foi "
            "carregado no banco de dados. Execute "
            "'python backend/database/ingest_manual_redacao.py' a partir da raiz do monorepo."
        )

    if not linhas:
        return (
            "Nenhum trecho do Manual de Redação foi encontrado para os critérios informados. "
            "Prossiga com a formatação padrão de documentos oficiais em português do Brasil."
        )

    partes = ["Trecho(s) do Manual de Redação da Presidência da República:"]
    for linha in linhas:
        secao = linha["secao"] if isinstance(linha, sqlite3.Row) else linha[0]
        conteudo = linha["conteudo"] if isinstance(linha, sqlite3.Row) else linha[1]
        if len(conteudo) > MANUAL_REDACAO_MAX_CHARS_POR_TRECHO:
            conteudo = conteudo[:MANUAL_REDACAO_MAX_CHARS_POR_TRECHO].rstrip() + " [...]"
        partes.append(f"\n[{secao}]\n{conteudo}")

    return "\n".join(partes)