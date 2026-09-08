"""
Testes unitários TDD para backend/core/tool_call_json_parser.py.
"""
import unittest

from backend.core.tool_call_json_parser import extrair_tool_call_json


class TestToolCallJsonParser(unittest.TestCase):
    def test_parser_json_extrai_formato_ferramenta(self):
        conteudo = '{"ferramenta":"criar_planilha","nome_arquivo":"estoque","colunas":["Item","Qtd"]}'
        res = extrair_tool_call_json(conteudo)
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "criar_planilha")
        self.assertEqual(res["arguments"], {"nome_arquivo": "estoque", "colunas": ["Item", "Qtd"]})
        self.assertEqual(res.get("_fonte"), "json")
        self.assertFalse(res.get("_reparado", False))

    def test_parser_json_strip_cercas_codigo(self):
        conteudo = '```json\n{"ferramenta": "criar_documento", "nome_arquivo": "oficio", "titulo": "Ofício", "conteudo": "Texto"}\n```'
        res = extrair_tool_call_json(conteudo)
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "criar_documento")
        self.assertEqual(res["arguments"]["nome_arquivo"], "oficio")

    def test_parser_json_scan_balanceado(self):
        conteudo = 'Aqui está a chamada:\n{"ferramenta": "extrair_dados_planilha", "nome_arquivo": "dados.xlsx"}\nEspero ter ajudado.'
        res = extrair_tool_call_json(conteudo)
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "extrair_dados_planilha")
        self.assertEqual(res["arguments"]["nome_arquivo"], "dados.xlsx")

    def test_parser_json_reparo_truncamento(self):
        conteudo = '{"ferramenta": "criar_planilha", "nome_arquivo": "parcial", "colunas": ["A", "B"], "linhas": [{"A": 1, "B": 2}'
        res = extrair_tool_call_json(conteudo)
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "criar_planilha")
        self.assertTrue(res.get("_reparado", False))

    def test_parser_json_rejeita_ferramenta_desconhecida(self):
        conteudo = '{"ferramenta": "deletar_banco_dados", "confirmar": true}'
        res = extrair_tool_call_json(conteudo)
        self.assertIsNone(res)

    def test_normalizacao_controle_preserva_linhas(self):
        conteudo = '{"Ferramenta": "criar_planilha", "Nome_Arquivo": "teste", "Colunas": ["English Description"], "Linhas": [{"English Description": "Product A"}]}'
        res = extrair_tool_call_json(conteudo)
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "criar_planilha")
        args = res["arguments"]
        self.assertIn("nome_arquivo", args)
        self.assertIn("colunas", args)
        self.assertIn("linhas", args)
        # Chaves dentro de linhas NÃO podem ter sido convertidas para lowercase!
        self.assertEqual(args["linhas"], [{"English Description": "Product A"}])


if __name__ == "__main__":
    unittest.main()

