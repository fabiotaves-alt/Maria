"""
Testes unitários TDD para backend/domain/validacao_tool_call.py.
"""
import unittest

from backend.domain.validacao_tool_call import validar_tool_call_determinístico


class TestValidacaoToolCall(unittest.TestCase):
    def test_validacao_linhas_tipo_invalido(self):
        tool_call = {
            "name": "criar_planilha",
            "arguments": {"nome_arquivo": "teste", "colunas": ["Nome"], "linhas": "invalido"}
        }
        res = validar_tool_call_determinístico(tool_call)
        self.assertTrue(res["bloqueante"])
        self.assertTrue(len(res["erros"]) > 0)
        self.assertIn("linhas", res["erros"][0])

    def test_validacao_linhas_case_insensitive(self):
        tool_call = {
            "name": "criar_planilha",
            "arguments": {
                "nome_arquivo": "teste",
                "colunas": ["Peso", "Nome"],
                "linhas": [{"peso": 70, "nome": "Maria"}]
            }
        }
        res = validar_tool_call_determinístico(tool_call)
        self.assertFalse(res["bloqueante"])
        tc_corrigida = res["tool_call"]
        linhas = tc_corrigida["arguments"]["linhas"]
        # 'peso' e 'nome' devem ser normalizados para 'Peso' e 'Nome' por corresponderem a colunas
        self.assertIn("Peso", linhas[0])
        self.assertIn("Nome", linhas[0])
        self.assertEqual(linhas[0]["Peso"], 70)

    def test_validacao_derivar_colunas(self):
        tool_call = {
            "name": "criar_planilha",
            "arguments": {
                "nome_arquivo": "teste",
                "linhas": [{"Item": "Caneta", "Preço": 2.50}]
            }
        }
        res = validar_tool_call_determinístico(tool_call)
        self.assertFalse(res["bloqueante"])
        tc_corrigida = res["tool_call"]
        self.assertIn("colunas", tc_corrigida["arguments"])
        self.assertEqual(tc_corrigida["arguments"]["colunas"], ["Item", "Preço"])


if __name__ == "__main__":
    unittest.main()

