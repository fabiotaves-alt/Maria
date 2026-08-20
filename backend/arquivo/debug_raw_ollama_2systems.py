"""Reproduz a duplicação de system prompt do código real, isolando essa
única variável em relação ao debug_raw_ollama.py (que manda só 1 system).

Uso:
    python debug_raw_ollama_2systems.py "Crie uma planilha de gastos com colunas Data e Valor."
"""
import sys
import json
import requests
from backend.core.config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_NUM_CTX,
    OLLAMA_NUM_PREDICT, OLLAMA_NUM_THREAD, OLLAMA_KEEP_ALIVE,
    OLLAMA_ENVIAR_THINK_PARAM, OLLAMA_THINK_HABILITADO, OLLAMA_TEMPERATURE_TOOLS,
)
from backend.core.tools_schema import TOOLS_SCHEMA
from backend.core.chat_session import ChatSession

if len(sys.argv) < 2:
    raise SystemExit('Uso: python debug_raw_ollama_2systems.py "mensagem do usuário"')

mensagem_usuario = sys.argv[1]

system_prompt_curto = """Você é a MARIA, uma assistente virtual de escritório.
Quando o usuário pedir para criar planilhas, documentos ou editar arquivos, você DEVE usar as ferramentas disponíveis.
Responda sempre em português do Brasil."""

# Mesmo valor que get_historico_com_system() injeta para uma ChatSession nova
system_prompt_longo = ChatSession.SYSTEM_PROMPT

mensagens = [
    {"role": "system", "content": system_prompt_curto},
    {"role": "system", "content": system_prompt_longo},
    {"role": "user", "content": mensagem_usuario},
]

payload = {
    "model": OLLAMA_MODEL,
    "messages": mensagens,
    "tools": TOOLS_SCHEMA,
    "stream": True,
    "options": {
        "num_ctx": OLLAMA_NUM_CTX,
        "num_predict": OLLAMA_NUM_PREDICT,
        "num_thread": OLLAMA_NUM_THREAD,
        "temperature": OLLAMA_TEMPERATURE_TOOLS,
    },
    "keep_alive": OLLAMA_KEEP_ALIVE,
}
if OLLAMA_ENVIAR_THINK_PARAM:
    payload["think"] = OLLAMA_THINK_HABILITADO

print("Enviando requisição com 2 mensagens system (reproduzindo o bug)...", file=sys.stderr)

with requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, stream=True, timeout=300) as resp:
    for linha in resp.iter_lines():
        if not linha:
            continue
        data = json.loads(linha.decode("utf-8"))
        print(json.dumps(data, ensure_ascii=False, indent=2))