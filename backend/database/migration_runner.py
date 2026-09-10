"""
Runner de migrations do banco MARIA — controle de versão do schema SQLite.

Substitui a execução direta de DDL em `schema.py`: cada evolução futura do
schema vira um arquivo `NNN_descricao.sql` em `backend/database/migrations/`,
aplicado uma única vez em ordem numérica (prefixo `NNN_`) e registrado na
tabela `schema_migrations` + `PRAGMA user_version`.

Responsabilidades:
1. Criar a tabela de controle `schema_migrations` na primeira execução.
2. Aplicar migrations pendentes dentro de BEGIN/COMMIT (atomicidade).
3. Registrar a versão em `schema_migrations` e em `PRAGMA user_version`
   (health checks rápidos via `SELECT * FROM pragma_user_version`).
4. Tolerar ausência de FTS5: statements `CREATE VIRTUAL TABLE ... fts5`
   são executados fora da transação principal com try/except individual —
   SQLite compilado sem FTS5 gera warning e a migration segue registrada.

Regra para migrations futuras: NUNCA renomear/remover colunas existentes —
apenas `ADD COLUMN` com DEFAULT (compatibilidade com o frontend Rust/rusqlite).

PRAGMAs `foreign_keys`/`journal_mode`/`busy_timeout` são responsabilidade de
`backend/database/connection.py:get_connection()` — não repetir aqui.
"""

import logging
import re
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

PASTA_MIGRATIONS = Path(__file__).resolve().parent / "migrations"
_PADRAO_ARQUIVO = re.compile(r"^(\d+)_(.+)\.sql$")


def _criar_tabela_controle(conn: sqlite3.Connection) -> None:
    """Cria a tabela de controle de migrations, se ainda não existir."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            versao INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            aplicado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def _listar_migrations() -> list[tuple[int, str, Path]]:
    """Lista migrations (versao, nome, caminho) ordenadas pelo prefixo numérico."""
    encontradas: list[tuple[int, str, Path]] = []
    for caminho in PASTA_MIGRATIONS.glob("*.sql"):
        casamento = _PADRAO_ARQUIVO.match(caminho.name)
        if casamento is None:
            logger.warning(
                "Arquivo em migrations/ sem prefixo numérico ignorado: %s",
                caminho.name,
            )
            continue
        encontradas.append((int(casamento.group(1)), caminho.name, caminho))
    return sorted(encontradas, key=lambda item: item[0])


def _separar_statements(sql: str) -> list[str]:
    """Divide o conteúdo de um .sql em statements individuais.

    Remove linhas de comentário (`--`) e separa por `;`. Suficiente para os
    arquivos controlados deste projeto (sem `;` dentro de literais).
    """
    linhas_sem_comentario = "\n".join(
        linha for linha in sql.splitlines() if not linha.strip().startswith("--")
    )
    return [
        parte.strip()
        for parte in linhas_sem_comentario.split(";")
        if parte.strip()
    ]


def _eh_statement_fts5(statement: str) -> bool:
    """True se o statement cria uma tabela virtual FTS5 (tratamento tolerante)."""
    return (
        "CREATE VIRTUAL TABLE" in statement.upper()
        and "FTS5" in statement.upper()
    )


def _aplicar_migration(
    conn: sqlite3.Connection, versao: int, nome: str, caminho: Path
) -> None:
    """
    Aplica uma migration individual.

    Statements normais rodam em BEGIN/COMMIT com `PRAGMA user_version` dentro
    da mesma transação (atomicidade). Statements FTS5 rodam depois, tolerantes
    a `sqlite3.OperationalError` (módulo fts5 ausente).
    """
    sql = caminho.read_text(encoding="utf-8")
    statements = _separar_statements(sql)
    normais = [s for s in statements if not _eh_statement_fts5(s)]
    fts5 = [s for s in statements if _eh_statement_fts5(s)]

    # Transação principal
    try:
        conn.execute("BEGIN")
        for statement in normais:
            conn.execute(statement)
        conn.execute(f"PRAGMA user_version = {versao}")
    except Exception as error:  # noqa: BLE001 — re-lança com contexto claro
        conn.execute("ROLLBACK")
        raise RuntimeError(
            f"Migration '{nome}' (versão {versao}) falhou e foi revertida: {error}"
        ) from error
    else:
        conn.execute("COMMIT")

    # Registro pós-commit bem-sucedido
    conn.execute(
        "INSERT INTO schema_migrations (versao, nome) VALUES (?, ?)",
        (versao, nome),
    )
    conn.commit()
    logger.info("Migration '%s' aplicada (user_version=%d)", nome, versao)

    # FTS5 tolerante — fora da transação principal
    for statement in fts5:
        try:
            conn.execute(statement)
            conn.commit()
        except sqlite3.OperationalError as error:
            logger.warning(
                "FTS5 indisponível; statement ignorado em '%s': %s", nome, error
            )


def run_migrations(conn: sqlite3.Connection | None = None) -> list[str]:
    """
    Aplica todas as migrations pendentes, em ordem numérica.

    Args:
        conn: conexão opcional. Se None, usa `get_connection()` (default).

    Returns:
        Nomes das migrations efetivamente aplicadas nesta execução.

    Raises:
        RuntimeError: se uma migration normal falhar (transação revertida).
    """
    if conn is None:
        from backend.database.connection import get_connection

        conn = get_connection()

    _criar_tabela_controle(conn)

    aplicadas: list[str] = []
    for versao, nome, caminho in _listar_migrations():
        ja_aplicada = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE versao = ?", (versao,)
        ).fetchone()
        if ja_aplicada is not None:
            continue
        _aplicar_migration(conn, versao, nome, caminho)
        aplicadas.append(nome)
    return aplicadas


if __name__ == "__main__":
    from backend.database.connection import get_connection

    aplicadas = run_migrations(get_connection())
    print(f"✅ Migrations aplicadas: {aplicadas or 'nenhuma pendente'}")
