"""Configuração do benchmark."""
import os

# Modelos a testar
MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-5-sonnet-20241022",
    "gemini-2.5-flash",
    "qwen2.5:7b",
]

# Superfícies a comparar
SURFACES = ["lia", "python"]

# Número de repetições por tarefa (para medir variância)
REPETITIONS = 3

# Timeout para execução de código (ms)
EXECUTION_TIMEOUT_MS = 5000

# Diretório de resultados
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# Diretório de prompts
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

# Configuração do Ollama
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5:7b"

# Configuração do Google Gemini
GEMINI_MODEL = "gemini-2.5-flash"

# Critérios de decisão
THRESHOLDS = {
    "advance": 15.0,      # pp de vantagem para avançar
    "marginal": 5.0,      # pp para considerar marginal
    "minimum_tasks": 50,  # mínimo de tarefas para validade
}
