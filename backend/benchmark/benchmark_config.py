"""Configurações do benchmark da MARIA.

Este módulo não importa o config.py da aplicação para evitar colisões.
"""
import os

BENCHMARK_RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
BENCHMARK_ARQUIVOS_DIR = os.path.join(
    BENCHMARK_RESULTS_DIR, "arquivos_gerados_benchmark"
)
BENCHMARK_TASK_TIMEOUT = int(os.getenv("BENCHMARK_TASK_TIMEOUT", "400"))
BENCHMARK_MAX_RETRIES = int(os.getenv("BENCHMARK_MAX_RETRIES", "2"))
BENCHMARK_RETRY_BACKOFF_SECONDS = float(
    os.getenv("BENCHMARK_RETRY_BACKOFF_SECONDS", "3.0")
)
BENCHMARK_WARMUP_TIMEOUT = int(os.getenv("BENCHMARK_WARMUP_TIMEOUT", "300"))
# Número padrão de repetições por tarefa. O valor escolhido pelo usuário
# (menu de avaliação ou --repeticoes na CLI) SEMPRE prevalece sobre este
# default — o main() do run_benchmark usa args.repeticoes, não esta constante.
BENCHMARK_REPETICOES = int(os.getenv("BENCHMARK_REPETICOES", "2"))

# Timeout POR CHAMADA individual ao modelo (s). O BENCHMARK_TASK_TIMEOUT (400s)
# continua como timeout TOTAL da tarefa (incluindo retries e continuacoes); a
# separacao permite identificar se uma tarefa estourou por uma chamada lenta
# ou pelo acumulo de varias chamadas.
# Default 300s: a ~1.8 tok/s (7B Q4_K_M em CPU), uma chamada com
# max_tokens=400 leva ~220s. O default anterior (120s) gerava falso negativo
# estrutural em documentos narrativos (tasks 8, 10, 15).
BENCHMARK_TIMEOUT_POR_CHAMADA = int(
    os.getenv("BENCHMARK_TIMEOUT_POR_CHAMADA", "300")
)
