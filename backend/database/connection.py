"""
Módulo de conexão com o banco de dados do Maria.
Padrão reaproveitado do NYC Analista de Dados.
"""
import sqlite3
import threading
from pathlib import Path
from typing import Optional

_DB_PATH: Optional[Path] = None
_CONNECTION: Optional[sqlite3.Connection] = None
_LOCK = threading.Lock()


def init_db(db_path: str | Path) -> None:
    """Configura o caminho do banco antes da primeira conexão."""
    global _DB_PATH
    _DB_PATH = Path(db_path)
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)



def get_connection() -> sqlite3.Connection:
    """
    Retorna a conexão compartilhada com o banco, criando-a de forma
    thread-safe na primeira chamada. `check_same_thread=False` é
    necessário porque o servidor HTTP (Flask, threaded=True) atende cada
    requisição em uma thread própria; a serialização de acesso concorrente
    fica a cargo do SQLite (WAL + busy_timeout).
    """
    global _CONNECTION, _DB_PATH

    if _CONNECTION is not None:
        return _CONNECTION

    with _LOCK:
        if _CONNECTION is None:
            if _DB_PATH is None:
                _DB_PATH = Path(__file__).parent.parent.parent / "shared" / "maria.db"
                _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

            conexao = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
            conexao.execute("PRAGMA foreign_keys = ON")
            conexao.execute("PRAGMA journal_mode = WAL")
            conexao.execute("PRAGMA busy_timeout = 5000")
            conexao.row_factory = sqlite3.Row
            _CONNECTION = conexao

    return _CONNECTION


def close_connection() -> None:
    """Fecha a conexão atual."""
    global _CONNECTION
    with _LOCK:
        if _CONNECTION is not None:
            _CONNECTION.close()
            _CONNECTION = None

