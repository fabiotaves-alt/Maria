"""
backend/database/schema.py
----------------------------
Schema do banco de dados do Maria (maria.db).
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo        TEXT    DEFAULT NULL,
    criado_em     TEXT    NOT NULL,
    atualizado_em TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS mensagens (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    conversa_id   INTEGER NOT NULL,
    autor         TEXT    NOT NULL,
    texto         TEXT    NOT NULL,
    criado_em     TEXT    NOT NULL,
    FOREIGN KEY (conversa_id) REFERENCES conversas(id)
);
CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id);

CREATE TABLE IF NOT EXISTS memoria (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    chave         TEXT    NOT NULL UNIQUE,
    valor         TEXT    NOT NULL,
    atualizado_em TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS arquivos_indexados (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    caminho       TEXT    NOT NULL,
    tipo          TEXT    DEFAULT NULL,
    resumo        TEXT    DEFAULT NULL,
    indexado_em   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS automacoes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT    NOT NULL,
    gatilho       TEXT    NOT NULL,
    acao          TEXT    NOT NULL,
    ativo         INTEGER NOT NULL DEFAULT 1,
    criado_em     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT
);
"""


def init_db(conn) -> None:
    """Executa o schema completo na conexão fornecida."""
    conn.executescript(SCHEMA)
    conn.commit()