"""
Módulo de configurações do projeto MARIA.
Centraliza todas as configurações para evitar hardcoded em múltiplos arquivos.
Suporta override via variáveis de ambiente.
"""

import os

# Carregar variáveis de ambiente de arquivo .env se existir (opcional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv não instalado, usar apenas variáveis de ambiente do sistema
    pass

# Configurações do Ollama (suportam override via ENV)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "240"))

# Parâmetros de geração do modelo (otimização de performance)
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "2048"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "400"))
OLLAMA_NUM_THREAD = int(os.getenv("OLLAMA_NUM_THREAD", "2"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")

# Configurações da sessão de chat
MAX_MENSAGENS_HISTORICO = int(os.getenv("MAX_MENSAGENS_HISTORICO", "12"))

# Configurações de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Pasta para arquivos gerados
PASTA_ARQUIVOS_GERADOS = os.getenv("PASTA_ARQUIVOS_GERADOS", "arquivos_gerados")

# Pasta para sessões salvas (histórico de conversa persistente entre execuções)
PASTA_SESSOES = os.getenv("PASTA_SESSOES", "sessoes_salvas")

# ---- Acesso de leitura a arquivos (somente leitura, nunca escrita) ----
EXTENSOES_LEITURA = {".txt", ".md", ".csv", ".log", ".docx"}
MAX_CHARS_LEITURA = int(os.getenv("MAX_CHARS_LEITURA", "6000"))
MAX_TAMANHO_ARQUIVO_MB = int(os.getenv("MAX_TAMANHO_ARQUIVO_MB", "5"))
MAX_PASSOS_LEITURA = int(os.getenv("MAX_PASSOS_LEITURA", "3"))
