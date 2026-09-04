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

from backend.core.config import MARIA_ENV
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
    `shared/.bridge_token`, restringindo a permissão de leitura ao
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
        """Rejeita requisições sem token válido (exceto /ping)."""
        if request.path == "/ping":
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
