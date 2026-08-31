"""
Script de ingestão do Manual de Redação da Presidência da República
para a tabela FTS5 'manual_redacao_fts' (RAG textual local).

Lê backend/docs/manual_redacao_presidencia.md, segmenta por cabeçalhos
Markdown (##, ###, ####, #####, ######), classifica cada trecho por
tipo_documento com base no número da seção, e popula a tabela FTS5.

Também grava um JSON intermediário (backend/database/manual_redacao_chunks.json)
para depuração/auditoria — não é lido em tempo de execução pela aplicação.

Uso (a partir da raiz do monorepo):
    python backend/database/ingest_manual_redacao.py
"""

import json
import logging
import re
import sys
from pathlib import Path

_RAIZ_MONOREPO = str(Path(__file__).resolve().parent.parent.parent)
if _RAIZ_MONOREPO not in sys.path:
    sys.path.insert(0, _RAIZ_MONOREPO)

from backend.database.connection import get_connection
from backend.database.schema import init_db

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CAMINHO_MANUAL = Path(__file__).resolve().parent.parent / "docs" / "manual_redacao_presidencia.md"
CAMINHO_JSON_SAIDA = Path(__file__).resolve().parent / "manual_redacao_chunks.json"

TAMANHO_MINIMO_CHUNK = 30  # descarta cabeçalhos "vazios" (ex: só título de capítulo)

_HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$', re.MULTILINE)
_NUM_RE = re.compile(r'^(\d+(?:\.\d+)*)\b')


def _limpar_titulo(titulo: str) -> str:
    """Remove marcações Markdown/HTML residuais de um título de seção."""
    titulo = re.sub(r'\*\*|~~', '', titulo)
    titulo = re.sub(r'<sup>.*?</sup>|<u>.*?</u>|</?sup>|</?u>', '', titulo)
    titulo = re.sub(r'_{2,}', '', titulo)
    titulo = re.sub(r'\s+', ' ', titulo).strip()
    return titulo


def _classificar_tipo_documento(secao: str) -> str:
    """
    Classifica uma seção pelo número inicial do título.

    Mapeamento (fato do domínio: desde a 3a edição, aviso e memorando
    foram unificados sob "ofício" — não existem categorias separadas
    para eles):
        5.x        -> oficio                  (padrão ofício)
        6.2.x      -> exposicao_motivos
        6.3.x      -> mensagem
        6.4.x      -> email
        1-4, 6, 7-12 -> geral                  (estilo, gramática, ortografia)
        13-25      -> elaboracao_normativa
        26+        -> processo_legislativo
        sem número -> geral
    """
    match = _NUM_RE.match(secao)
    if not match:
        return "geral"

    numero = match.group(1)
    topo = numero.split(".")[0]

    if topo == "5":
        return "oficio"
    if numero.startswith("6.2"):
        return "exposicao_motivos"
    if numero.startswith("6.3"):
        return "mensagem"
    if numero.startswith("6.4"):
        return "email"
    if topo in {"1", "2", "3", "4", "6", "7", "8", "9", "10", "11", "12"}:
        return "geral"
    if topo in {str(n) for n in range(13, 26)}:
        return "elaboracao_normativa"
    try:
        if int(topo) >= 26:
            return "processo_legislativo"
    except ValueError:
        pass
    return "geral"


def extrair_chunks(texto_markdown: str) -> list[dict]:
    """
    Segmenta o texto em chunks por cabeçalho Markdown.
    Cada chunk contém o conteúdo entre um cabeçalho e o próximo
    (de qualquer nível), evitando duplicação de texto entre pai/filho.
    """
    headings = [
        (m.start(), m.end(), m.group(2))
        for m in _HEADING_RE.finditer(texto_markdown)
    ]

    chunks = []
    for i, (inicio, fim_titulo, titulo_bruto) in enumerate(headings):
        inicio_corpo = fim_titulo + 1
        fim_corpo = headings[i + 1][0] if i + 1 < len(headings) else len(texto_markdown)
        corpo = texto_markdown[inicio_corpo:fim_corpo].strip()
        corpo = re.sub(r'\n{3,}', '\n\n', corpo)

        if len(corpo) < TAMANHO_MINIMO_CHUNK:
            continue

        secao = _limpar_titulo(titulo_bruto)
        chunks.append({
            "tipo_documento": _classificar_tipo_documento(secao),
            "secao": secao,
            "conteudo": corpo,
        })

    return chunks


def ingerir(caminho_manual: Path = CAMINHO_MANUAL) -> int:
    """
    Executa a ingestão completa: lê o .md, gera os chunks, salva o JSON
    de depuração e popula a tabela FTS5 (limpando dados anteriores antes).

    Returns:
        Número de chunks inseridos.

    Raises:
        FileNotFoundError: se o arquivo do manual não existir.
    """
    if not caminho_manual.exists():
        raise FileNotFoundError(
            f"Manual não encontrado em '{caminho_manual}'. "
            "Copie o arquivo para backend/docs/manual_redacao_presidencia.md."
        )

    texto = caminho_manual.read_text(encoding="utf-8")
    chunks = extrair_chunks(texto)

    CAMINHO_JSON_SAIDA.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(f"JSON de depuração salvo em: {CAMINHO_JSON_SAIDA}")

    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM manual_redacao_fts")
        cursor.executemany(
            "INSERT INTO manual_redacao_fts (tipo_documento, secao, conteudo) VALUES (?, ?, ?)",
            [(c["tipo_documento"], c["secao"], c["conteudo"]) for c in chunks],
        )
        conn.commit()
    except Exception as error:
        conn.rollback()
        raise RuntimeError(f"Falha ao popular manual_redacao_fts: {error}") from error

    return len(chunks)


if __name__ == "__main__":
    total = ingerir()
    print(f"✅ {total} trechos do Manual de Redação inseridos em shared/maria.db (tabela manual_redacao_fts).")