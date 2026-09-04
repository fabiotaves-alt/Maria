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

# ------------------------------------------------------------------
# System Prompt da MARIA (carregado de arquivo externo)
# ------------------------------------------------------------------
_SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")


def _carregar_system_prompt() -> str:
    """Carrega o system prompt do arquivo. Falha explicitamente se não encontrar."""
    try:
        with open(_SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise RuntimeError(
            f"System prompt não encontrado: {_SYSTEM_PROMPT_PATH}\n"
            "Crie o arquivo backend/core/system_prompt.txt com as instruções do sistema."
        ) from None


MARIA_SYSTEM_PROMPT = _carregar_system_prompt()

# Configurações do Ollama (LEGADO — caminho não utilizado em produção; mantido por compatibilidade)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "240"))

# Parâmetros de geração do modelo (otimização de performance)
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "400"))
OLLAMA_NUM_THREAD = int(os.getenv("OLLAMA_NUM_THREAD", "4"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")

# ---- Comportamento do modelo (concentrado aqui; ajustável por modelo via ENV) ----
# Controla se o campo "think" é enviado no payload do Ollama. Desative para
# modelos que não suportam esse campo.
OLLAMA_ENVIAR_THINK_PARAM = os.getenv("OLLAMA_ENVIAR_THINK_PARAM", "true").lower() == "true"
# Valor enviado no campo "think" quando OLLAMA_ENVIAR_THINK_PARAM é True.
OLLAMA_THINK_HABILITADO = os.getenv("OLLAMA_THINK_HABILITADO", "false").lower() == "true"
# Temperatura usada nas chamadas de tool calling (mais baixa = mais determinístico).
OLLAMA_TEMPERATURE_TOOLS = float(os.getenv("OLLAMA_TEMPERATURE_TOOLS", "0.1"))
# Controla se o fallback de extração de tool call vazada como texto (comportamento
# observado no Qwen3.5) é tentado. Desative para modelos que não apresentam esse
# comportamento (ver Item 3).
OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL = os.getenv("OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL", "true").lower() == "true"
# Orçamento de tokens para respostas que compõem documentos narrativos
# (carta, relatório, ata, comunicado) — maior que o padrão, pois o modelo
# precisa redigir o conteúdo inteiro antes de emitir a tool call.
OLLAMA_NUM_PREDICT_DOCUMENTO = int(os.getenv("OLLAMA_NUM_PREDICT_DOCUMENTO", "600"))
# Orçamento de tokens para a chamada de CONTINUAÇÃO após uma ferramenta de
# leitura (listar_arquivos/resumir_documento) — menor que o padrão, pois
# nesse ponto o modelo só precisa decidir a próxima ferramenta.
OLLAMA_NUM_PREDICT_CONTINUACAO = int(os.getenv("OLLAMA_NUM_PREDICT_CONTINUACAO", "200"))

# Configurações do llama-server (suportam override via ENV).
# Modelos em teste: qwen2.5-omni-3b (leve) e qwen2.5-omni-7b (pesado).
LLAMA_BASE_URL = os.getenv("LLAMA_BASE_URL", "http://localhost:8080")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "qwen2.5-omni-3b")  # use "qwen2.5-omni-7b" p/ modelo pesado
LLAMA_TIMEOUT = int(os.getenv("LLAMA_TIMEOUT", "240"))
LLAMA_NUM_CTX = int(os.getenv("LLAMA_NUM_CTX", "4096"))
LLAMA_NUM_PREDICT = int(os.getenv("LLAMA_NUM_PREDICT", "400"))
LLAMA_TEMPERATURE_TOOLS = float(os.getenv("LLAMA_TEMPERATURE_TOOLS", "0.1"))
LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL = os.getenv("LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL", "true").lower() == "true"
LLAMA_NUM_PREDICT_DOCUMENTO = int(os.getenv("LLAMA_NUM_PREDICT_DOCUMENTO", "300"))
LLAMA_NUM_PREDICT_CONTINUACAO = int(os.getenv("LLAMA_NUM_PREDICT_CONTINUACAO", "200"))

# Temperatura usada SOMENTE nas chamadas de correção de tool call inválida
# (ver core/tool_chaining.py: validar_e_corrigir_tool_call_stream). Mais alta
# que LLAMA_TEMPERATURE_TOOLS para dar flexibilidade ao modelo na correção.
LLAMA_TEMPERATURE_TOOLS_RETRY = float(os.getenv("LLAMA_TEMPERATURE_TOOLS_RETRY", "0.25"))

# Número máximo de tentativas de correção de uma tool call de ESCRITA inválida
# antes de desistir e prosseguir sem ferramenta (ver tool_chaining.py).
MAX_TENTATIVAS_CORRECAO_FERRAMENTA = int(os.getenv("MAX_TENTATIVAS_CORRECAO_FERRAMENTA", "2"))

# ---- Parâmetros de sampler do llama-server (llama.cpp) ----
# Defaults idênticos aos do llama-server; enviá-los explicitamente no payload
# permite configurar (via ENV) e auditar (benchmark) cada valor. O servidor
# ignora campos desconhecidos com warning, então o payload permanece seguro.
LLAMA_REPEAT_LAST_N = int(os.getenv("LLAMA_REPEAT_LAST_N", "64"))
LLAMA_REPEAT_PENALTY = float(os.getenv("LLAMA_REPEAT_PENALTY", "1.0"))
LLAMA_FREQUENCY_PENALTY = float(os.getenv("LLAMA_FREQUENCY_PENALTY", "0.0"))
LLAMA_PRESENCE_PENALTY = float(os.getenv("LLAMA_PRESENCE_PENALTY", "0.0"))
LLAMA_DRY_MULTIPLIER = float(os.getenv("LLAMA_DRY_MULTIPLIER", "0.0"))
LLAMA_DRY_BASE = float(os.getenv("LLAMA_DRY_BASE", "1.75"))
LLAMA_DRY_ALLOWED_LENGTH = int(os.getenv("LLAMA_DRY_ALLOWED_LENGTH", "2"))
LLAMA_DRY_PENALTY_LAST_N = int(os.getenv("LLAMA_DRY_PENALTY_LAST_N", "64"))
LLAMA_TOP_K = int(os.getenv("LLAMA_TOP_K", "40"))
LLAMA_TOP_P = float(os.getenv("LLAMA_TOP_P", "0.95"))
LLAMA_MIN_P = float(os.getenv("LLAMA_MIN_P", "0.05"))
LLAMA_XTC_PROBABILITY = float(os.getenv("LLAMA_XTC_PROBABILITY", "0.0"))
LLAMA_XTC_THRESHOLD = float(os.getenv("LLAMA_XTC_THRESHOLD", "0.1"))
LLAMA_TYPICAL_P = float(os.getenv("LLAMA_TYPICAL_P", "1.0"))
LLAMA_TOP_N_SIGMA = float(os.getenv("LLAMA_TOP_N_SIGMA", "-1.0"))

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

# Manual de Redação da Presidência da República (RAG via FTS5)
MANUAL_REDACAO_TOP_K = int(os.getenv("MANUAL_REDACAO_TOP_K", "5"))
MANUAL_REDACAO_MAX_CHARS_POR_TRECHO = int(os.getenv("MANUAL_REDACAO_MAX_CHARS_POR_TRECHO", "800"))

# ---- Ambiente de execução ----
# "development" habilita origens extras de CORS (ex.: Vite dev server).
# Qualquer outro valor (padrão: "production") aplica a configuração mais restrita.
MARIA_ENV = os.getenv("MARIA_ENV", "production").strip().lower()

