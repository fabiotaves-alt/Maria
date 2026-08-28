"""
Script de validação do llama-server ao vivo.
Requer que o llama-server esteja rodando em LLAMA_BASE_URL (padrão: http://localhost:8080).

Uso:
    python backend/tests/validate_llama_server.py
    python backend/tests/validate_llama_server.py --image caminho/para/imagem.jpg
    python backend/tests/validate_llama_server.py --audio caminho/para/audio.wav
"""

import argparse
import sys
from pathlib import Path

# Garantir que a raiz do monorepo esteja no sys.path
_RAIZ = str(Path(__file__).resolve().parent.parent.parent)
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from backend.core.llama_client import LlamaClient, LlamaClientError, LlamaTimeoutError
from backend.core.config import LLAMA_BASE_URL, LLAMA_MODEL


def _ok(msg: str):
    print(f"  ✓ {msg}")


def _fail(msg: str):
    print(f"  ✗ {msg}")


def testar_conexao(cliente: LlamaClient) -> bool:
    print("\n[1] Conexão básica (GET /v1/models)")
    import requests
    try:
        r = requests.get(f"{LLAMA_BASE_URL}/v1/models", timeout=5)
        if r.status_code == 200:
            modelos = [m.get("id", "") for m in r.json().get("data", [])]
            _ok(f"Servidor acessível. Modelos: {modelos or '(lista vazia)'}")
            return True
        else:
            _fail(f"Status inesperado: {r.status_code}")
            return False
    except Exception as e:
        _fail(f"Falha de conexão: {e}")
        return False


def testar_chat_texto(cliente: LlamaClient) -> bool:
    print("\n[2] Chat texto simples")
    try:
        texto, tool_call = cliente.chat(
            [{"role": "user", "content": "Responda apenas com a palavra: ok"}]
        )
        if texto:
            _ok(f"Resposta recebida: {texto[:80]!r}")
            return True
        else:
            _fail("Resposta vazia")
            return False
    except (LlamaClientError, LlamaTimeoutError) as e:
        _fail(f"Erro: {e}")
        return False


def testar_streaming(cliente: LlamaClient) -> bool:
    print("\n[3] Streaming")
    try:
        metricas: dict = {}
        chunks = []
        for chunk, _ in cliente.chat_stream(
            [{"role": "user", "content": "Conte de 1 a 5 separados por vírgula."}],
            metricas_saida=metricas,
        ):
            if chunk:
                chunks.append(chunk)
        texto = "".join(chunks)
        if texto:
            _ok(f"Streaming OK. Tokens: {metricas.get('tokens_gerados', '?')}. "
                f"TTFT: {metricas.get('ttft', '?')}s. "
                f"Velocidade: {metricas.get('tokens_por_segundo', '?')} tok/s")
            _ok(f"Texto: {texto[:80]!r}")
            return True
        else:
            _fail("Nenhum chunk recebido")
            return False
    except (LlamaClientError, LlamaTimeoutError) as e:
        _fail(f"Erro: {e}")
        return False


def testar_visao(cliente: LlamaClient, image_path: str) -> bool:
    print(f"\n[4] Visão (imagem: {image_path})")
    try:
        texto, _ = cliente.chat(
            [{"role": "user", "content": "Descreva brevemente o que você vê nesta imagem."}],
            image_path=image_path,
        )
        if texto:
            _ok(f"Descrição recebida: {texto[:120]!r}")
            return True
        else:
            _fail("Resposta vazia para imagem")
            return False
    except (LlamaClientError, LlamaTimeoutError) as e:
        _fail(f"Erro: {e}")
        return False


def testar_audio(cliente: LlamaClient, audio_path: str) -> bool:
    print(f"\n[5] Áudio (arquivo: {audio_path})")
    try:
        texto, _ = cliente.chat(
            [{"role": "user", "content": "Transcreva o áudio enviado."}],
            audio_path=audio_path,
        )
        if texto:
            _ok(f"Transcrição recebida: {texto[:120]!r}")
            return True
        else:
            _fail("Resposta vazia para áudio")
            return False
    except (LlamaClientError, LlamaTimeoutError) as e:
        _fail(f"Erro: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Valida o llama-server ao vivo.")
    parser.add_argument("--image", help="Caminho para imagem de teste (opcional)")
    parser.add_argument("--audio", help="Caminho para arquivo .wav de teste (opcional)")
    args = parser.parse_args()

    print(f"=== Validação do llama-server ===")
    print(f"URL: {LLAMA_BASE_URL}  |  Modelo: {LLAMA_MODEL}")

    cliente = LlamaClient()
    resultados = []

    resultados.append(testar_conexao(cliente))
    if not resultados[-1]:
        print("\n[ABORTADO] Servidor inacessível. Verifique se o llama-server está rodando.")
        sys.exit(1)

    resultados.append(testar_chat_texto(cliente))
    resultados.append(testar_streaming(cliente))

    if args.image:
        if Path(args.image).exists():
            resultados.append(testar_visao(cliente, args.image))
        else:
            print(f"\n[4] Visão — arquivo não encontrado: {args.image}")
            resultados.append(False)
    else:
        print("\n[4] Visão — pulado (use --image para testar)")

    if args.audio:
        if Path(args.audio).exists():
            resultados.append(testar_audio(cliente, args.audio))
        else:
            print(f"\n[5] Áudio — arquivo não encontrado: {args.audio}")
            resultados.append(False)
    else:
        print("\n[5] Áudio — pulado (use --audio para testar)")

    passou = sum(resultados)
    total = len(resultados)
    print(f"\n=== Resultado: {passou}/{total} testes passaram ===")
    sys.exit(0 if passou == total else 1)


if __name__ == "__main__":
    main()
