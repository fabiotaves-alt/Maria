"""
Schema do banco de dados MARIA — SQLite compartilhado.

A criação/evolução do schema é versionada por migrations em
`backend/database/migrations/` e executada por `backend/database/migration_runner.py`.

Este módulo apenas delega:
- `init_db()` aplica as migrations pendentes na conexão atual (idempotente);
- `limpar_tudo()` reseta o banco (apenas testes/desenvolvimento).

Tabelas gerenciadas pelas migrations (001_initial.sql):
- conversas, mensagens, memoria, arquivos_indexados, automacoes,
  configuracoes e manual_redacao_fts (FTS5 — tolerante a ausência do módulo).
"""

from backend.database.connection import get_connection, close_connection
from backend.database.migration_runner import run_migrations


def init_db():
    """Aplica migrations pendentes — cria o schema se necessário (idempotente)."""
    run_migrations(get_connection())


def limpar_tudo():
    """Reseta o banco de dados (apenas para testes/desenvolvimento).

    Inclui a tabela de controle `schema_migrations` e o `PRAGMA user_version`,
    para que a próxima chamada a `init_db()` reaplique as migrations do zero.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS mensagens")
    cursor.execute("DROP TABLE IF EXISTS automacoes")
    cursor.execute("DROP TABLE IF EXISTS arquivos_indexados")
    cursor.execute("DROP TABLE IF EXISTS memoria")
    cursor.execute("DROP TABLE IF EXISTS configuracoes")
    cursor.execute("DROP TABLE IF EXISTS conversas")
    cursor.execute("DROP TABLE IF EXISTS manual_redacao_fts")
    cursor.execute("DROP TABLE IF EXISTS schema_migrations")
    cursor.execute("PRAGMA user_version = 0")

    conn.commit()


if __name__ == "__main__":
    init_db()
    print("✅ Banco de dados inicializado com sucesso!")
    print("📁 Local: shared/maria.db")
