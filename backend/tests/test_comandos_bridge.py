"""Testes de regressao para os comandos do bridge.

Cobrem os 7 bugs corrigidos na analise de 2026-09-03:
  - BUG 1: carregar_sessao (dict acessado como objeto, filename em vez de caminho)
  - BUG 2: criar_automacao (coluna acao NOT NULL omitida no INSERT)
  - BUG 3: listar_automacoes / toggle_automacao (coluna ativa inexistente no schema)
  - BUG 4: exportar_conversa (importava exportar_sessao inexistente)
  - BUG 5: ler_planilha_resumo (usava newline literal em vez de newline real)
  - BUG 7: listar_memoria (nao devolvia id, necessario para deletar_memoria)

Executar:
    python -m pytest tests/test_comandos_bridge.py -v
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import openpyxl

from backend.core.chat_session import ChatSession
from backend.core.session_storage import (
    exportar_sessao,
    salvar_sessao,
)


class _BaseComandosBridgeTest(unittest.TestCase):
    """Base: DB isolado + mock de controller + pasta de sessoes temporaria."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "teste_comandos.db")

        import backend.database.connection as connection_module
        from backend.database.schema import init_db as _init_db

        connection_module._CONNECTION = None
        connection_module._DB_PATH = Path(self.db_path)
        _init_db()

        self.sessao_dir = os.path.join(self.temp_dir.name, "sessoes")
        os.makedirs(self.sessao_dir, exist_ok=True)
        self._original_pasta_sessoes = os.environ.get("PASTA_SESSOES")
        os.environ["PASTA_SESSOES"] = self.sessao_dir

        self.controller = MagicMock()
        self.controller.modelo = None

    def tearDown(self):
        import backend.database.connection as connection_module

        connection_module.close_connection()
        connection_module._CONNECTION = None
        connection_module._DB_PATH = None

        if self._original_pasta_sessoes is not None:
            os.environ["PASTA_SESSOES"] = self._original_pasta_sessoes
        else:
            os.environ.pop("PASTA_SESSOES", None)

        self.temp_dir.cleanup()

    def _despachar(self, comando: str, payload: dict):
        """Helper: despacho um comando do bridge com o controller mockado."""
        from backend.bridge.comandos import _despachar_comando
        return _despachar_comando(self.controller, comando, payload)


class TestCarregarSessao(_BaseComandosBridgeTest):
    """BUG 1: carregar_sessao acessava dict como objeto + caminho incorreto."""

    def test_carregar_sessao_por_nome_arquivo(self):
        """Deve resolver nome_arquivo via listar_sessoes e acessar dados[historico]."""
        sessao = ChatSession()
        sessao.adicionar_mensagem("user", "Ola")
        sessao.adicionar_mensagem("assistant", "Oi! Como posso ajudar?")
        salvar_sessao(sessao.to_dict(), "sessao_20260101_120000.json")

        status, dados, erro = self._despachar(
            "carregar_sessao", {"nome": "sessao_20260101_120000.json"}
        )
        self.assertEqual(status, "ok", erro)
        self.assertIsInstance(dados, list)
        self.assertEqual(len(dados), 2)
        self.assertEqual(dados[0]["role"], "user")
        self.assertEqual(dados[0]["conteudo"], "Ola")
        self.assertEqual(dados[1]["role"], "assistant")
        self.assertEqual(dados[1]["conteudo"], "Oi! Como posso ajudar?")

    def test_carregar_sessao_por_caminho_absoluto(self):
        """Deve aceitar caminho absoluto diretamente."""
        sessao = ChatSession()
        sessao.adicionar_mensagem("user", "Teste caminho absoluto")
        caminho = salvar_sessao(sessao.to_dict(), "sessao_20260101_130000.json")

        status, dados, erro = self._despachar(
            "carregar_sessao", {"nome": caminho}
        )
        self.assertEqual(status, "ok", erro)
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]["conteudo"], "Teste caminho absoluto")

    def test_carregar_sessao_nome_vazio_retorna_erro(self):
        """Campo nome vazio deve retornar erro, nao AttributeError."""
        status, dados, erro = self._despachar("carregar_sessao", {"nome": ""})
        self.assertEqual(status, "erro")
        self.assertIn("vazio", erro)


class TestCriarAutomacao(_BaseComandosBridgeTest):
    """BUG 2: criar_automacao omitia coluna acao (TEXT NOT NULL)."""

    def test_criar_automacao_com_acao_explicita(self):
        """INSERT deve incluir a coluna acao para nao violar NOT NULL."""
        status, dados, erro = self._despachar("criar_automacao", {
            "nome": "Auto Com Acao",
            "descricao": "Automacao de teste",
            "gatilho": "manual",
            "acao": "criar_documento",
            "passos": [{"tipo": "documento"}],
        })
        self.assertEqual(status, "ok", erro)
        self.assertIn("criada", dados)

    def test_criar_automacao_acao_default_vazio_nao_viola_not_null(self):
        """acao default vazio deve passar no NOT NULL do schema."""
        status, dados, erro = self._despachar("criar_automacao", {
            "nome": "Auto Sem Acao",
            "gatilho": "manual",
        })
        self.assertEqual(status, "ok", erro)

    def test_criar_automacao_nome_vazio_retorna_erro(self):
        """Nome vazio deve retornar erro de validacao."""
        status, dados, erro = self._despachar("criar_automacao", {"nome": ""})
        self.assertEqual(status, "erro")
        self.assertIn("vazio", erro)

    def test_criar_automacao_persiste_no_banco(self):
        """Automacao criada deve aparecer em listar_automacoes."""
        self._despachar("criar_automacao", {
            "nome": "Auto Persistida",
            "gatilho": "cron",
            "acao": "enviar_email",
        })
        status, dados, _ = self._despachar("listar_automacoes", {})
        self.assertEqual(status, "ok")
        nomes = [a["nome"] for a in dados]
        self.assertIn("Auto Persistida", nomes)


class TestListarEToggleAutomacao(_BaseComandosBridgeTest):
    """BUG 3: SQL usava coluna ativa (inexistente) em vez de ativo."""

    def test_listar_automacoes_usa_coluna_ativo_no_sql(self):
        """listar_automacoes deve funcionar sem OperationalError."""
        self._despachar("criar_automacao", {
            "nome": "Auto Listar", "gatilho": "manual", "acao": "",
        })
        status, dados, erro = self._despachar("listar_automacoes", {})
        self.assertEqual(status, "ok", erro)
        self.assertIsInstance(dados, list)
        self.assertEqual(len(dados), 1)

    def test_listar_automacoes_chave_json_ativa_frontend(self):
        """JSON de saida usa chave ativa (contrato frontend), nao ativo."""
        self._despachar("criar_automacao", {
            "nome": "Auto JSON", "gatilho": "manual", "acao": "",
        })
        _, dados, _ = self._despachar("listar_automacoes", {})
        autom = dados[0]
        self.assertIn("ativa", autom)
        self.assertNotIn("ativo", autom)

    def test_toggle_automacao_usa_coluna_ativo_no_sql(self):
        """toggle_automacao deve funcionar sem OperationalError."""
        self._despachar("criar_automacao", {
            "nome": "Auto Toggle", "gatilho": "manual", "acao": "",
        })
        _, listar, _ = self._despachar("listar_automacoes", {})
        auto_id = listar[0]["id"]
        status, dados, erro = self._despachar("toggle_automacao", {"id": auto_id})
        self.assertEqual(status, "ok", erro)
        self.assertIn("ativa", dados)
        self.assertIsInstance(dados["ativa"], bool)

    def test_toggle_automacao_id_vazio_retorna_erro(self):
        """ID vazio deve retornar erro de validacao."""
        status, dados, erro = self._despachar("toggle_automacao", {"id": None})
        self.assertEqual(status, "erro")
        self.assertIn("vazio", erro)


class TestExportarConversa(_BaseComandosBridgeTest):
    """BUG 4: exportar_conversa importava exportar_sessao inexistente."""

    def test_exportar_conversa_formato_txt(self):
        """Deve exportar sessao para .txt sem ImportError."""
        sessao = ChatSession()
        sessao.adicionar_mensagem("user", "Teste exportacao txt")
        sessao.adicionar_mensagem("assistant", "Resposta teste")
        self.controller.sessao = sessao

        status, dados, erro = self._despachar(
            "exportar_conversa", {"formato": "txt"}
        )
        self.assertEqual(status, "ok", erro)
        self.assertTrue(dados.startswith("Exportado:"))
        caminho = dados.replace("Exportado: ", "")
        self.assertTrue(os.path.exists(caminho))
        self.assertTrue(caminho.endswith(".txt"))

    def test_exportar_conversa_formato_json(self):
        """Deve exportar sessao para .json sem ImportError."""
        sessao = ChatSession()
        sessao.adicionar_mensagem("user", "Teste exportacao json")
        self.controller.sessao = sessao

        status, dados, erro = self._despachar(
            "exportar_conversa", {"formato": "json"}
        )
        self.assertEqual(status, "ok", erro)
        caminho = dados.replace("Exportado: ", "")
        self.assertTrue(caminho.endswith(".json"))
        self.assertTrue(os.path.exists(caminho))

    def test_exportar_sessao_funcao_importavel(self):
        """exportar_sessao deve estar disponivel em session_storage."""
        sessao = ChatSession()
        sessao.adicionar_mensagem("user", "Teste direto")
        caminho = exportar_sessao(sessao, formato="txt")
        self.assertTrue(os.path.exists(caminho))
        self.assertTrue(caminho.endswith(".txt"))

    def test_exportar_sessao_formato_default_txt(self):
        """Formato padrao deve ser txt quando nao especificado."""
        sessao = ChatSession()
        sessao.adicionar_mensagem("user", "Default")
        caminho = exportar_sessao(sessao)
        self.assertTrue(caminho.endswith(".txt"))

    def test_exportar_sessao_conteudo_txt_legivel(self):
        """Conteudo do .txt deve ser legivel com rotulos de role."""
        sessao = ChatSession()
        sessao.adicionar_mensagem("user", "Pergunta")
        sessao.adicionar_mensagem("assistant", "Resposta")
        caminho = exportar_sessao(sessao, formato="txt")

        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
        self.assertIn("[Usu", conteudo)
        self.assertIn("[MARIA]", conteudo)
        self.assertIn("Pergunta", conteudo)
        self.assertIn("Resposta", conteudo)


class TestLerPlanilhaResumo(_BaseComandosBridgeTest):
    """BUG 5: ler_planilha_resumo usava newline literal em vez de newline real."""

    def _criar_planilha(self, name="teste.xlsx"):
        caminho = os.path.join(self.temp_dir.name, name)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws["A1"] = "Coluna1"
        ws["B1"] = "Coluna2"
        ws["A2"] = "Dado1"
        ws["B2"] = "Dado2"
        ws["A3"] = "Dado3"
        ws["B3"] = "Dado4"
        wb.save(caminho)
        wb.close()
        return caminho

    def test_analisar_dados_planilha_newline_real(self):
        """Resumo da planilha deve usar newline real, nao literal."""
        xlsx_path = self._criar_planilha()
        status, dados, erro = self._despachar("analisar_dados", {"caminho": xlsx_path})
        self.assertEqual(status, "ok", erro)
        self.assertIsInstance(dados, str)
        self.assertNotIn(chr(92) + "n", dados)
        self.assertIn(chr(10), dados)
        self.assertIn("Coluna1", dados)


class TestMemoria(_BaseComandosBridgeTest):
    """BUG 7: listar_memoria nao devolvia id (necessario para deletar_memoria)."""

    def test_listar_memoria_retorna_id(self):
        """listar_memoria deve incluir id no SELECT e na resposta JSON."""
        self._despachar("salvar_memoria", {
            "fato": "O usuario gosta de cafe",
            "categoria": "preferencias",
            "relevancia": 2.0,
        })
        status, dados, erro = self._despachar("listar_memoria", {})
        self.assertEqual(status, "ok", erro)
        self.assertIsInstance(dados, list)
        self.assertEqual(len(dados), 1)
        self.assertIn("id", dados[0])
        self.assertIn("fato", dados[0])
        self.assertIn("categoria", dados[0])
        self.assertIn("relevancia", dados[0])

    def test_listar_memoria_id_usavel_em_deletar(self):
        """BUG 7 (fluxo): id retornado por listar_memoria deve funcionar em deletar."""
        self._despachar("salvar_memoria", {
            "fato": "Fato para deletar", "categoria": "geral",
        })
        _, listar, _ = self._despachar("listar_memoria", {})
        mem_id = listar[0]["id"]

        status, dados, erro = self._despachar("deletar_memoria", {"id": mem_id})
        self.assertEqual(status, "ok", erro)

        _, listar_depois, _ = self._despachar("listar_memoria", {})
        self.assertEqual(len(listar_depois), 0)

    def test_deletar_memoria_id_vazio_retorna_erro(self):
        """deletar_memoria sem id deve retornar erro de validacao."""
        status, dados, erro = self._despachar("deletar_memoria", {"id": None})
        self.assertEqual(status, "erro")
        self.assertIn("vazio", erro)

    def test_listar_memoria_lista_vazia(self):
        """Sem memorias salvas, listar_memoria deve retornar lista vazia."""
        status, dados, erro = self._despachar("listar_memoria", {})
        self.assertEqual(status, "ok", erro)
        self.assertEqual(dados, [])


class TestDespacharComando(_BaseComandosBridgeTest):
    """Testes gerais do despacho de comandos."""

    def test_comando_desconhecido_retorna_erro(self):
        """Comando nao registrado deve retornar erro, nao crash."""
        status, dados, erro = self._despachar("comando_inexistente", {})
        self.assertEqual(status, "erro")
        self.assertIn("desconhecido", erro.lower())

    def test_ping_retorna_pong(self):
        """Comando ping deve retornar pong."""
        status, dados, _ = self._despachar("ping", {})
        self.assertEqual(status, "ok")
        self.assertEqual(dados, "pong")


if __name__ == "__main__":
    unittest.main()
