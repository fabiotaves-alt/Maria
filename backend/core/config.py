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

# Configurações do llama-server (suportam override via ENV).
# Modelos em teste: qwen2.5-omni-3b (leve) e qwen2.5-omni-7b (pesado).
LLAMA_BASE_URL = os.getenv("LLAMA_BASE_URL", "http://localhost:8080")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "qwen2.5-omni-3b")  # use "qwen2.5-omni-7b" p/ modelo pesado
LLAMA_TIMEOUT = int(os.getenv("LLAMA_TIMEOUT", "240"))
LLAMA_NUM_CTX = int(os.getenv("LLAMA_NUM_CTX", "4096"))
LLAMA_NUM_PREDICT = int(os.getenv("LLAMA_NUM_PREDICT", "400"))
LLAMA_TEMPERATURE_TOOLS = float(os.getenv("LLAMA_TEMPERATURE_TOOLS", "0.1"))
LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL = os.getenv("LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL", "true").lower() == "true"
# Teto de tokens para composição de documento narrativo. 600 (antes 300):
# o valor anterior TRUNCAVA a tool call de criar_documento (lista de args
# sem fechamento) exatamente nos casos que precisam de mais texto — o parser
# não conseguia extrair e a tarefa falhava. É teto, não geração fixa.
LLAMA_NUM_PREDICT_DOCUMENTO = int(os.getenv("LLAMA_NUM_PREDICT_DOCUMENTO", "600"))
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
LLAMA_REPEAT_LAST_N = int(os.getenv("LLAMA_REPEAT_LAST_N", "128"))
# Penalidade de repetição de tokens. 1.1 (default clássico do llama.cpp para
# chat): suficiente contra repetições próximas sem penalizar os tokens
# estruturais do tool call (colchetes/aspas/vírgulas). 1.3 + presence/frequency
# 0.1 derrubaram a acurácia de 100% para 76% (run_20260905_170437). O loop de
# FRASE inteira (task 8) é coberto por DRY + janela 128, não por repeat_penalty.
# Reversível via ENV: LLAMA_REPEAT_PENALTY=1.0.
LLAMA_REPEAT_PENALTY = float(os.getenv("LLAMA_REPEAT_PENALTY", "1.1"))
# 0.0 (desativado): frequency/presence penalizam tokens JÁ VISTOS — inclusive o
# nome canônico da ferramenta (presente no system prompt) e os tokens
# estruturais do JSON. Com 0.1, o modelo trocava "criar_planilha" por
# "create_planilha" e gerava JSON malformado (run_20260905_170437). Não usar.
LLAMA_FREQUENCY_PENALTY = float(os.getenv("LLAMA_FREQUENCY_PENALTY", "0.0"))
LLAMA_PRESENCE_PENALTY = float(os.getenv("LLAMA_PRESENCE_PENALTY", "0.0"))
# DRY (Don't Repeat Yourself): penaliza sequências já emitidas — a defesa
# CORRETA contra loops de frase (que o repeat_penalty, limitado à janela, não
# pega), sem atingir tokens estruturais isolados (sequências <=
# dry_allowed_length ficam isentas). 0.0 = desativado; 0.8 = referência.
LLAMA_DRY_MULTIPLIER = float(os.getenv("LLAMA_DRY_MULTIPLIER", "0.8"))
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

# ---- Limites de linhas por modelo (planilhas) ----
# Aplicados automaticamente pelo excel_handler conforme LLAMA_MODEL ativo.
# Configuráveis via ENV para ajuste sem alteração de código.
# v4.3.x: usados também para controle de paginação na visualização em tempo real.
MAX_LINHAS_POR_CHAMADA_3B = int(os.getenv("MAX_LINHAS_POR_CHAMADA_3B", "50"))
MAX_LINHAS_POR_CHAMADA_7B = int(os.getenv("MAX_LINHAS_POR_CHAMADA_7B", "150"))
MAX_LINHAS_EXTRACAO_3B = int(os.getenv("MAX_LINHAS_EXTRACAO_3B", "50"))
MAX_LINHAS_EXTRACAO_7B = int(os.getenv("MAX_LINHAS_EXTRACAO_7B", "150"))


def get_max_linhas_por_chamada() -> int:
    """
    Retorna o limite de linhas por chamada conforme o modelo ativo (LLAMA_MODEL).
    Automático — não exposto ao modelo nem ao usuário.
    """
    if "7b" in LLAMA_MODEL.lower():
        return MAX_LINHAS_POR_CHAMADA_7B
    return MAX_LINHAS_POR_CHAMADA_3B

