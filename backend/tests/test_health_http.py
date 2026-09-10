"""Testes do endpoint GET /health (Tarefa 1.2 — Fase 1).

Cobre os cenários da especificação sem depender de llama-server real:
- healthy quando todos os checks passam (llama, banco, disco);
- degraded quando llama fora do ar / banco falho / disco insuficiente;
- rota acessível sem token (mesmo tratamento do /ping);
- HTTP 200 sempre, com o estado no corpo JSON.
"""

import sqlite3
import unittest
from contextlib import ExitStack
from unittest import mock


class TestHealthHttp(unittest.TestCase):
    """Testes de comportamento da rota /health."""

    def setUp(self):
        from backend.main import _criar_app_http, _carregar_token_api

        self.token = _carregar_token_api()
        self.app = _criar_app_http(None, self.token)
        self.client = self.app.test_client()

    @staticmethod
    def _conexao_memoria():
        return sqlite3.connect(":memory:")

    def _patches_ok(self, conn, livre_bytes=10 * 1024**3):
        stack = ExitStack()
        stack.enter_context(
            mock.patch(
                "requests.get", return_value=mock.Mock(ok=True, status_code=200)
            )
        )
        stack.enter_context(
            mock.patch(
                "backend.database.connection.get_connection", return_value=conn
            )
        )
        stack.enter_context(
            mock.patch(
                "psutil.disk_usage", return_value=mock.Mock(free=livre_bytes)
            )
        )
        return stack

    def test_health_healthy_quando_tudo_ok(self):
        conn = self._conexao_memoria()
        try:
            with self._patches_ok(conn):
                resp = self.client.get("/health")
        finally:
            conn.close()

        self.assertEqual(resp.status_code, 200)
        dados = resp.get_json()
        self.assertEqual(dados["status"], "healthy")
        self.assertTrue(dados["checks"]["llama_server"]["ok"])
        self.assertIn("latencia_ms", dados["checks"]["llama_server"])
        self.assertTrue(dados["checks"]["banco_dados"]["ok"])
        self.assertIsNone(dados["checks"]["banco_dados"]["erro"])
        self.assertTrue(dados["checks"]["disco"]["ok"])
        self.assertIn("livre_gb", dados["checks"]["disco"])
        self.assertEqual(dados["versao"], "4.2.5")
        self.assertIn("timestamp", dados)
        self.assertIn("modelo", dados)

    def test_health_degradado_quando_llama_fora(self):
        conn = self._conexao_memoria()
        try:
            with mock.patch(
                "requests.get", side_effect=RuntimeError("conexao recusada")
            ), mock.patch(
                "backend.database.connection.get_connection", return_value=conn
            ), mock.patch(
                "psutil.disk_usage", return_value=mock.Mock(free=10 * 1024**3)
            ):
                resp = self.client.get("/health")
        finally:
            conn.close()

        self.assertEqual(resp.status_code, 200)
        dados = resp.get_json()
        self.assertEqual(dados["status"], "degraded")
        self.assertFalse(dados["checks"]["llama_server"]["ok"])
        self.assertIn("erro", dados["checks"]["llama_server"])

    def test_health_degradado_quando_banco_falho(self):
        conn = self._conexao_memoria()
        try:
            with mock.patch(
                "requests.get", return_value=mock.Mock(ok=True, status_code=200)
            ), mock.patch(
                "backend.database.connection.get_connection",
                side_effect=sqlite3.OperationalError("db corrompido"),
            ), mock.patch(
                "psutil.disk_usage", return_value=mock.Mock(free=10 * 1024**3)
            ):
                resp = self.client.get("/health")
        finally:
            conn.close()

        self.assertEqual(resp.status_code, 200)
        dados = resp.get_json()
        self.assertEqual(dados["status"], "degraded")
        self.assertFalse(dados["checks"]["banco_dados"]["ok"])
        self.assertIn("erro", dados["checks"]["banco_dados"])

    def test_health_degradado_quando_disco_insuficiente(self):
        conn = self._conexao_memoria()
        try:
            with self._patches_ok(conn, livre_bytes=100 * 1024**2):  # < 500 MB
                resp = self.client.get("/health")
        finally:
            conn.close()

        self.assertEqual(resp.status_code, 200)
        dados = resp.get_json()
        self.assertEqual(dados["status"], "degraded")
        self.assertFalse(dados["checks"]["disco"]["ok"])
        self.assertLess(dados["checks"]["disco"]["livre_gb"], 0.5)

    def test_health_acessivel_sem_token(self):
        conn = self._conexao_memoria()
        try:
            with self._patches_ok(conn):
                # Sem header Authorization — deve ser 200 (igual ao /ping).
                resp = self.client.get("/health")
        finally:
            conn.close()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "healthy")
