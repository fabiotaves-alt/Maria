"""Storage SQLite para o benchmark MARIA (fase B3)."""
import json
import os
import sqlite3
from contextlib import contextmanager

from .benchmark_config import BENCHMARK_RESULTS_DIR

DB_PATH = os.path.join(BENCHMARK_RESULTS_DIR, "benchmark.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    modelo TEXT NOT NULL,
    prompt_hash TEXT,
    config_json TEXT
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    task_id INTEGER,
    task_name TEXT,
    category TEXT,
    model TEXT,
    tool_detected TEXT,
    tool_correct INTEGER,
    args_correct INTEGER,
    tool_call_fonte TEXT,
    parse_suspeito INTEGER,
    latency_ms REAL,
    tokens_por_segundo REAL,
    runtime_ok INTEGER,
    finish_reason TEXT,
    fallbacks_json TEXT,
    correcoes_json TEXT,
    dados_arquivo_validos INTEGER,
    contexto_ok INTEGER,
    correction_attempts INTEGER
);

CREATE INDEX IF NOT EXISTS idx_results_run_id ON results(run_id);
CREATE INDEX IF NOT EXISTS idx_results_task_id ON results(task_id);
"""


@contextmanager
def _conectar():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except sqlite3.OperationalError:
        conn.rollback()
        raise
    finally:
        conn.close()


def inicializar_schema() -> None:
    with _conectar() as conn:
        conn.executescript(_SCHEMA)


def registrar_run(modelo: str, prompt_hash: str | None, config: dict) -> int:
    from datetime import datetime, timezone
    inicializar_schema()
    with _conectar() as conn:
        cursor = conn.execute(
            "INSERT INTO runs (timestamp, modelo, prompt_hash, config_json) VALUES (?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), modelo, prompt_hash, json.dumps(config, ensure_ascii=False)),
        )
        return cursor.lastrowid


def registrar_resultados(run_id: int, resultados: list) -> None:
    def _campo(r, nome, default=None):
        if isinstance(r, dict):
            return r.get(nome, default)
        return getattr(r, nome, default)

    linhas = []
    for r in resultados:
        linhas.append((
            run_id,
            _campo(r, "task_id"),
            _campo(r, "task_name"),
            _campo(r, "category"),
            _campo(r, "model"),
            _campo(r, "tool_detected"),
            int(bool(_campo(r, "tool_correct", False))),
            int(bool(_campo(r, "args_correct", True))),
            _campo(r, "tool_call_fonte"),
            int(bool(_campo(r, "parse_suspeito", False))),
            _campo(r, "latency_ms"),
            _campo(r, "tokens_por_segundo"),
            int(bool(_campo(r, "runtime_ok", True))),
            _campo(r, "finish_reason"),
            json.dumps(_campo(r, "fallbacks", []), ensure_ascii=False),
            json.dumps(_campo(r, "correcoes", []), ensure_ascii=False),
            int(bool(_campo(r, "dados_arquivo_validos", True))),
            int(bool(_campo(r, "contexto_ok", True))),
            _campo(r, "correction_attempts", 0),
        ))

    with _conectar() as conn:
        conn.executemany(
            "INSERT INTO results (run_id, task_id, task_name, category, model, tool_detected, "
            "tool_correct, args_correct, tool_call_fonte, parse_suspeito, latency_ms, "
            "tokens_por_segundo, runtime_ok, finish_reason, fallbacks_json, correcoes_json, "
            "dados_arquivo_validos, contexto_ok, correction_attempts) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            linhas,
        )


def agrupar_por_modelo_task_fonte(run_id: int | None = None) -> list[dict]:
    query = (
        "SELECT model, task_id, task_name, tool_call_fonte, COUNT(*) AS execucoes, "
        "SUM(tool_correct) AS acertos, AVG(latency_ms) AS latencia_media_ms FROM results"
    )
    params = ()
    if run_id is not None:
        query += " WHERE run_id = ?"
        params = (run_id,)
    query += " GROUP BY model, task_id, tool_call_fonte ORDER BY model, task_id"

    with _conectar() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
