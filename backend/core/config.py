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
