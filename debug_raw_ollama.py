"""Diagnóstico: mostra o JSON bruto do Ollama para uma mensagem específica,
sem nenhum parsing da MARIA (nem fallback, nem extração de tool call).

Uso:
    python debug_raw_ollama.py "Crie um documento chamado pauta_reuniao, titulo Pauta, com conteúdo: reunião às 10 horas e revisão das tarefas."
"""
import sys
import json
import requests
from core.config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_NUM_CTX,
    OLLAMA_NUM_PREDICT, OLLAMA_NUM_THREAD, OLLAMA_KEEP_ALIVE,
)
from core.tools_schema import TOOLS_SCHEMA

if len(sys.argv) < 2:
    raise SystemExit('Uso: python debug_raw_ollama.py "mensagem do usuário"')

mensagem_usuario = sys.argv[1]

# Mesmo system prompt usado em chat_com_tools_stream_com_metricas / chat_com_tools_stream
system_prompt = """Você é a MARIA, uma assistente virtual de escritório.
Quando o usuário pedir para criar planilhas, documentos ou editar arquivos, você DEVE usar as ferramentas disponíveis.
Responda sempre em português do Brasil."""

payload = {
    "model": OLLAMA_MODEL,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": mensagem_usuario},
    ],
    "tools": TOOLS_SCHEMA,
    "stream": True,
    "think": False,
    "options": {
        "num_ctx": OLLAMA_NUM_CTX,
        "num_predict": OLLAMA_NUM_PREDICT,
        "num_thread": OLLAMA_NUM_THREAD,
        "temperature": 0.1,
    },
    "keep_alive": OLLAMA_KEEP_ALIVE,
}

with requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, stream=True, timeout=120) as resp:
    for linha in resp.iter_lines():
        if not linha:
            continue
        data = json.loads(linha.decode("utf-8"))
        print(json.dumps(data, ensure_ascii=False, indent=2))