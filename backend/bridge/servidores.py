"""Transporte do bridge: stdin/stdout (frontend JavaFX) e HTTP (frontend Tauri).

Funções movidas integralmente de `backend/main.py` na divisão de módulos —
sem alterações de lógica.
"""

import json
import logging
import os
import secrets
import sys
from pathlib import Path

from datetime import datetime, timezone

from backend.config import (
    LLAMA_BASE_URL,
    LLAMA_MODEL,
    MARIA_ENV,
    PASTA_ARQUIVOS_GERADOS,
    __version__,
)
from backend.core.maria_controller import MariaController
from backend.core.paths import RAIZ_MONOREPO
from backend.bridge.comandos import _despachar_comando, _responder_bridge

logger = logging.getLogger(__name__)


def _modo_bridge(modelo: str | None = None):
    """
    Modo de integração com o frontend JavaFX.

    Lê requisições JSON por linha do stdin no formato:
        {"id": "...", "comando": "...", "payload": {...}}

    Comandos suportados:
        ping       → responde {"status": "ok", "dados": "pong"}
        chat       → envia mensagem ao modelo e responde com o texto final
        encerrar   → encerra o processo

    Responde JSON por linha no stdout no formato:
        {"id": "...", "status": "ok|erro", "dados": ..., "mensagemErro": ...}
    """
    # Inicializar banco de dados
    from backend.database.schema import init_db

    try:
        init_db()
        logger.info("Banco de dados inicializado")
    except Exception as e:
        logger.warning(f"Falha ao inicializar DB: {e}")

    controller = MariaController(modelo=modelo)
    try:
        controller.inicializar()
    except Exception as error:
        _responder_bridge("", "erro", mensagem_erro=f"Falha ao inicializar: {error}")
        return

    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue

        try:
            requisicao = json.loads(linha)
        except json.JSONDecodeError as error:
            _responder_bridge("", "erro", mensagem_erro=f"JSON inválido: {error}")
            continue

        identificador = requisicao.get("id", "")
        comando = requisicao.get("comando", "")
        payload = requisicao.get("payload") or {}

        status, dados, mensagem_erro = _despachar_comando(controller, comando, payload)
        _responder_bridge(identificador, status, dados=dados, mensagem_erro=mensagem_erro)

        if comando == "encerrar":
            break


def _carregar_token_api() -> str:
    """
    Gera o token da API bridge HTTP e o persiste atomicamente em
    `frontend-tauri/shared/.bridge_token`, restringindo a permissão de leitura ao
    usuário atual (POSIX). O frontend Tauri relê este arquivo a cada
    chamada (ver `call_python_backend` em main.rs), portanto não é
    necessário nenhum mecanismo adicional de sincronização.
    """
    caminho = Path(RAIZ_MONOREPO) / "frontend-tauri" / "shared" / ".bridge_token"
    token = secrets.token_hex(32)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    arquivo_temp = caminho.with_suffix(".tmp")
    try:
        arquivo_temp.write_text(token, encoding="utf-8")
        os.replace(arquivo_temp, caminho)  # rename atômico no mesmo filesystem
        if os.name == "posix":
            os.chmod(caminho, 0o600)
    finally:
        arquivo_temp.unlink(missing_ok=True)

    logger.info("Token da API bridge HTTP regenerado")
    return token


def _criar_app_http(controller: "MariaController", token: str):
    """
    App Flask que expõe o protocolo bridge via HTTP. Único endpoint POST /chat,
    aceitando {"id","comando","dados"} e respondendo {"id","status","dados","mensagemErro"}.
    Contrato consumido por frontend-tauri/src-tauri/src/main.rs (PythonRequest/PythonResponse).

    Segurança:
        - Autenticação obrigatória via header `Authorization: Bearer <token>`
          (/ping permanece aberto como health check, sem dados sensíveis).
        - CORS restrito às origens do frontend Tauri (dev e produção).
    """
    from flask import Flask, request, jsonify
    from flask_cors import CORS

    app = Flask(__name__)
    _ORIGENS_BASE = ["tauri://localhost", "http://tauri.localhost"]
    _ORIGENS_DEV_EXTRA = ["http://localhost:5173"]  # Vite dev server

    origens_cors = _ORIGENS_BASE + (_ORIGENS_DEV_EXTRA if MARIA_ENV == "development" else [])
    if MARIA_ENV != "development":
        logger.info("MARIA_ENV=%s: CORS restrito às origens de produção do Tauri.", MARIA_ENV)

    CORS(
        app,
        origins=origens_cors,
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.before_request
    def _exigir_autenticacao():
        """Rejeita requisições sem token válido (exceto /ping e /health)."""
        if request.path in ("/ping", "/health"):
            return None
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or not secrets.compare_digest(auth[7:], token):
            logger.warning("Requisição sem token válido rejeitada (rota: %s)", request.path)
            return jsonify({"id": "", "status": "erro", "dados": None,
                            "mensagemErro": "Não autorizado: token inválido ou ausente."}), 401
        return None

    @app.route("/chat", methods=["POST"])
    def _rota_unica():
        corpo = request.get_json(silent=True) or {}
        identificador = corpo.get("id", "")
        comando = corpo.get("comando", "")
        payload = corpo.get("dados") or {}

        if not comando:
            return jsonify({"id": identificador, "status": "erro", "dados": None,
                             "mensagemErro": "Campo 'comando' vazio."}), 400

        status, dados, mensagem_erro = _despachar_comando(controller, comando, payload)
        return jsonify({"id": identificador, "status": status, "dados": dados,
                         "mensagemErro": mensagem_erro})

    @app.route("/ping", methods=["GET"])
    def _health_check():
        return jsonify({"status": "ok", "dados": "pong"})

    @app.route("/health", methods=["GET"])
    def _rota_health():
        """
        Health check estendido, sem autenticação (mesmo tratamento do /ping).

        Retorna HTTP 200 sempre — o estado vai no corpo:
        {"status": "healthy"|"degraded", "timestamp", "checks", "versao", "modelo"}.
        Nenhuma exceção deve propagar: falhas viram `ok: false` no check
        correspondente e o status geral vira "degraded".
        """
        import time

        try:
            import requests
        except ImportError:
            requests = None

        checks: dict = {}

        # 1) llama-server: GET /v1/models com timeout de 2s
        inicio = time.monotonic()
        try:
            if requests is None:
                raise RuntimeError("Biblioteca 'requests' não instalada.")
            resposta = requests.get(f"{LLAMA_BASE_URL}/v1/models", timeout=2)
            checks["llama_server"] = {
                "ok": bool(resposta.ok),
                "latencia_ms": round((time.monotonic() - inicio) * 1000),
            }
            if not resposta.ok:
                checks["llama_server"]["erro"] = f"HTTP {resposta.status_code}"
        except Exception as error:  # noqa: BLE001 — health nunca propaga exceção
            checks["llama_server"] = {
                "ok": False,
                "latencia_ms": round((time.monotonic() - inicio) * 1000),
                "erro": str(error),
            }

        # 2) banco de dados: SELECT 1 na conexão SQLite
        try:
            from backend.database.connection import get_connection

            get_connection().execute("SELECT 1").fetchone()
            checks["banco_dados"] = {"ok": True, "erro": None}
        except Exception as error:  # noqa: BLE001
            checks["banco_dados"] = {"ok": False, "erro": str(error)}

        # 3) disco: espaço livre na pasta de arquivos gerados (mín. 500 MB)
        try:
            import psutil

            pasta_disco = Path(PASTA_ARQUIVOS_GERADOS)
            if not pasta_disco.is_absolute():
                pasta_disco = Path(RAIZ_MONOREPO) / pasta_disco
            caminho_disco = pasta_disco if pasta_disco.exists() else Path(RAIZ_MONOREPO)
            uso = psutil.disk_usage(str(caminho_disco))
            limite_bytes = 500 * 1024 * 1024
            checks["disco"] = {
                "ok": uso.free >= limite_bytes,
                "livre_gb": round(uso.free / (1024**3), 2),
            }
        except Exception as error:  # noqa: BLE001
            checks["disco"] = {"ok": False, "livre_gb": None, "erro": str(error)}

        saudavel = all(item.get("ok") for item in checks.values())
        return jsonify(
            {
                "status": "healthy" if saudavel else "degraded",
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "checks": checks,
                "versao": __version__,
                "modelo": (
                    controller.modelo if controller is not None else None
                ) or LLAMA_MODEL,
            }
        )

    return app


def _modo_bridge_http(modelo: str | None = None, porta: int = 8081):
    from backend.database.schema import init_db
    try:
        init_db()
        logger.info("Banco de dados inicializado")
    except Exception as e:
        logger.warning(f"Falha ao inicializar DB: {e}")

    controller = MariaController(modelo=modelo)
    try:
        controller.inicializar()
    except Exception as error:
        logger.error(f"Falha ao inicializar controller: {error}")
        raise SystemExit(f"Falha ao inicializar: {error}")

    app = _criar_app_http(controller, _carregar_token_api())
    logger.info(f"Servidor HTTP bridge iniciado em http://127.0.0.1:{porta}")
    app.run(host="127.0.0.1", port=porta, debug=False, use_reloader=False)
