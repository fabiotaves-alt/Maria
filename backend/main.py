"""
Script principal da MARIA - Assistente de IA de Escritório.

Responsabilidades:
    - Inicializar o controller (lógica de negócio)
    - Delegar toda a interface para ui_terminal.InterfaceTerminal
    - Encapsular: LlamaClient, ChatSession, ferramentas, persistência

Uso:
    python main.py
"""


import sys
import argparse
import logging
from pathlib import Path


# Garantir que a raiz do monorepo esteja no sys.path quando o script é
# executado diretamente (ex.: python backend/main.py --bridge), permitindo
# imports como `from backend.core.config import ...` sejam resolvidos.
_RAIZ_MONOREPO = str(Path(__file__).resolve().parent.parent)
if _RAIZ_MONOREPO not in sys.path:
    sys.path.insert(0, _RAIZ_MONOREPO)


from backend.core.config import LOG_LEVEL
from backend.core.maria_controller import MariaController
from backend.bridge.servidores import _modo_bridge, _modo_bridge_http
from backend.bridge.servidores import (  # re-export p/ compat com testes/patches
    _carregar_token_api,
    _criar_app_http,
)
from backend.bridge.comandos import (  # re-export p/ compat com testes/patches
    _despachar_comando,
    _responder_bridge,
    _get_system_status,
)

from backend.ui_terminal import InterfaceTerminal


# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════
# Ponto de entrada
# ═════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="MARIA - Assistente de IA de Escritório")
    parser.add_argument(
        "-m", "--modelo",
        dest="modelo",
        default=None,
        help="Nome do modelo Ollama a usar nesta execução (ex: qwen3:8b). "
             "Se omitido, usa OLLAMA_MODEL do ambiente/config.py."
    )
    parser.add_argument(
        "--bridge",
        action="store_true",
        help="Executa em modo bridge (JSON por linha no stdin/stdout) para integração com o frontend JavaFX."
    )
    parser.add_argument(
        "--bridge-http",
        action="store_true",
        help="Executa em modo bridge HTTP (REST) para o frontend Tauri."
    )
    parser.add_argument(
        "--porta",
        type=int,
        default=8081,
        help="Porta do servidor HTTP quando --bridge-http é usado (padrão: 8081)."
    )
    args = parser.parse_args()

    # Verificar dependências
    try:
        import requests  # noqa: F401
    except ImportError:
        print("\n[ERRO] A biblioteca 'requests' não está instalada.")
        print("Instale com: pip install requests\n")
        sys.exit(1)

    # Modo bridge HTTP (frontend Tauri)
    if args.bridge_http:
        try:
            import flask  # noqa: F401
            import flask_cors  # noqa: F401
        except ImportError as e:
            print(f"\n[ERRO] Biblioteca faltando: {e}")
            print("Instale com: pip install flask flask-cors\n")
            sys.exit(1)
        _modo_bridge_http(modelo=args.modelo, porta=args.porta)
        return

    # Modo bridge (frontend JavaFX)
    if args.bridge:
        _modo_bridge(modelo=args.modelo)
        return

    # Criar controller e interface
    controller = MariaController(modelo=args.modelo)
    interface = InterfaceTerminal(controller, imagem_banner="maria_opening.png")

    # Delegar totalmente para a interface
    interface.iniciar()


if __name__ == "__main__":
    main()
