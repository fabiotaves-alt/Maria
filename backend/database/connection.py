"""
backend/database/connection.py
--------------------------------
Conexão com o banco SQLite do Maria.
Processo de vida longa (subprocess único por sessão do app) — conexão
única reaproveitada durante todo o ciclo de vida do processo.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "shared" / "maria.db"

_conn = None


def get_conn() -> sqlite3.Connection:
    """Retorna a conexão SQLite única do processo, criando-a na primeira chamada."""
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
        _conn.execute("PRAGMA journal_mode = WAL")
        _conn.execute("PRAGMA synchronous = NORMAL")
        _conn.execute("PRAGMA foreign_keys = ON")
    return _conn