"""
Smoke test multimodal (visão/áudio) do MARIA — isolado do smoke funcional.

Requer llama-server com n_ctx suficiente para o payload com imagem (>= 4096).
Roda em CPU (3B) pode levar vários minutos; timeout configurável via --timeout.

Uso (a partir da raiz do monorepo):
    $env:PYTHONUTF8='1'
    uv run python docs/dev_base/smoke_multimodal.py --image backend/maria_opening.png
    uv run python docs/dev_base/smoke_multimodal.py --audio caminho/para/audio.wav --timeout 600
"""

import argparse
import os
import sys
from pathlib import Path

# Garantir que a raiz do monorepo esteja no sys.path (docs/dev_base → raiz = 2 níveis acima)
_RAIZ = str(Path(__file__).resolve().parent.parent.parent)
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

# Timeout lido ANTES de importar backend.config (que lê LLAMA_TIMEOUT no import).
_parser = argparse.ArgumentParser(description="Smoke multimodal (visão/áudio) do MARIA.")
_parser.add_argument("--image", help="Caminho para imagem de teste (opcional)")
_parser.add_argument("--audio", help="Caminho para arquivo .wav de teste (opcional)")
_parser.add_argument("--timeout", type=int, default=600, help="Timeout por chamada em segundos (default 600)")
_args = _parser.parse_args()

if _args.timeout:
    os.environ["LLAMA_TIMEOUT"] = str(_args.timeout)

import requests  # noqa: E402

from backend.application.maria_controller import MariaController  # noqa: E402
from backend.config import LLAMA_BASE_URL, LLAMA_MODEL, LLAMA_TIMEOUT  # noqa: E402

_resultados: list[tuple[str, bool, str]] = []


def _ok(item: str, msg: str = "") -> None:
    _resultados.append((item, True, msg))
    print(f"  [OK]   {item}" + (f" — {msg}" if msg else ""))


def _fail(item: str, msg: str) -> None:
    _resultados.append((item, False, msg))
    print(f"  [FALHA] {item} — {msg}")


def _info(msg: str) -> None:
    print(f"  [info] {msg}")


def _obter_n_ctx() -> int | None:
    """Lê o contexto efetivo do servidor via /v1/models (meta.n_ctx)."""
    try:
        r = requests.get(f"{LLAMA_BASE_URL}/v1/models", timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                return data[0].get("meta", {}).get("n_ctx")
    except Exception:
        pass
    return None


def testar_visao(cliente, image_path: str) -> None:
    print("\n[Visão]")
    if not Path(image_path).exists():
        _fail("Visão", f"arquivo não encontrado: {image_path}")
        return
    n_ctx = _obter_n_ctx()
    if n_ctx is not None and n_ctx < 3000:
        _info(f"n_ctx={n_ctx} < 3000 — payload de imagem (~2080 tokens) pode estourar; pulando visão.")
        return
    try:
        texto, _ = cliente.chat(
            [{"role": "user", "content": "Descreva brevemente o que você vê nesta imagem."}],
            image_path=image_path,
        )
        if texto:
            _ok("Visão", texto[:120])
        else:
            _fail("Visão", "resposta vazia")
    except Exception as e:
        _fail("Visão", f"{e}")


def testar_audio(cliente, audio_path: str) -> None:
    print("\n[Áudio]")
    if not Path(audio_path).exists():
        _fail("Áudio", f"arquivo não encontrado: {audio_path}")
        return
    try:
        texto, _ = cliente.chat(
            [{"role": "user", "content": "Transcreva o áudio enviado."}],
            audio_path=audio_path,
        )
        if texto:
            _ok("Áudio", texto[:120])
        else:
            _fail("Áudio", "resposta vazia")
    except Exception as e:
        _fail("Áudio", f"{e}")


def main() -> None:
    print("=== Smoke multimodal (visão/áudio) ===")
    print(f"URL: {LLAMA_BASE_URL}  |  Modelo: {LLAMA_MODEL}  |  Timeout: {LLAMA_TIMEOUT}s")
    n_ctx = _obter_n_ctx()
    if n_ctx is not None:
        _info(f"n_ctx do servidor: {n_ctx}")

    controller = MariaController()
    controller.inicializar()

    if _args.image:
        testar_visao(controller.cliente, _args.image)
    else:
        _info("Visão pulada (use --image)")

    if _args.audio:
        testar_audio(controller.cliente, _args.audio)
    else:
        _info("Áudio pulado (use --audio)")

    passou = sum(1 for _, ok, _ in _resultados if ok)
    total = len(_resultados)
    if total == 0:
        print("\nNada a testar — informe --image e/ou --audio.")
        sys.exit(0)
    print(f"\n=== Resultado: {passou}/{total} itens passaram ===")
    for item, ok, msg in _resultados:
        status = "OK   " if ok else "FALHA"
        detalhe = f" — {msg}" if msg and not ok else ""
        print(f"  [{status}] {item}{detalhe}")
    sys.exit(0 if passou == total else 1)


if __name__ == "__main__":
    main()
