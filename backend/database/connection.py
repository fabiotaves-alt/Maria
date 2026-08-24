"""
Módulo de conexão com o banco de dados do Maria.
Padrão reaproveitado do NYC Analista de Dados.
"""
import sqlite3
from pathlib import Path
from typing import Optional

_DB_PATH: Optional[Path] = None
_CONNECTION: Optional[sqlite3.Connection] = None


def init_db(db_path: str | Path) -> None:
    """Inicializa o caminho do banco de dados."""
    global _DB_PATH
    _DB_PATH = Path(db_path)
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão com o banco, aplicando PRAGMAs recomendados."""
    global _CONNECTION, _DB_PATH
    
    if _DB_PATH is None:
        # Caminho padrão para desenvolvimento
        _DB_PATH = Path(__file__).parent.parent.parent / "shared" / "maria.db"
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if _CONNECTION is None:
        _CONNECTION = sqlite3.connect(str(_DB_PATH))
        _CONNECTION.execute("PRAGMA foreign_keys = ON")
        _CONNECTION.execute("PRAGMA journal_mode = WAL")
        _CONNECTION.row_factory = sqlite3.Row
    
    return _CONNECTION


def close_connection() -> None:
    """Fecha a conexão atual."""
    global _CONNECTION
    if _CONNECTION is not None:
        _CONNECTION.close()
        _CONNECTION = None
