"""Testes de injeção de dependências do MariaController (Tarefa 1.3 — Fase 1).

Valida a Opção B:
1. `MariaController(cliente=...)` usa o cliente injetado (sem @patch de módulo);
2. `MariaController(tool_executor=...)` usa o executor injetado em
   `processar_confirmacao` (escrita) e repassa ao `encadear_leitura_stream`
   (leitura via tool_chaining) — sem tocar no sistema de arquivos real.
"""

import unittest
from unittest import mock

from backend.core.maria_controller import MariaController


class _ClienteFalso:
    """Cliente estrutural mínimo (satisfaz LLMClientProtocol no uso testado)."""

    model = "modelo-fake"


class TestInjecaoCliente(unittest.TestCase):
    def test_controller_aceita_cliente_injetado(self):
        cliente = _ClienteFalso()
        controller = MariaController(cliente=cliente)
        controller.inicializar()
        # O injetado deve ser preservado — LlamaClient NÃO deve ser criado.
        self.assertIs(controller.cliente, cliente)
        self.assertEqual(controller.cliente.model, "modelo-fake")

    def test_controller_sem_cliente_ainda_cria_llama_real(self):
        controller = MariaController(modelo="modelo-teste")
        controller.inicializar()
        from backend.core.llama_client import LlamaClient

        self.assertIsInstance(controller.cliente, LlamaClient)
        self.assertEqual(controller.cliente.model, "modelo-teste")


class TestInjecaoToolExecutor(unittest.TestCase):
    def test_processar_confirmacao_usa_executor_injetado(self):
        executor = mock.MagicMock()
        executor.executar_real.return_value = "Arquivo criado (fake)"

        controller = MariaController(cliente=_ClienteFalso(), tool_executor=executor)
        controller.inicializar()
        controller.sessao.definir_acao_pendente(
            {"name": "criar_planilha", "arguments": {"nome_arquivo": "gastos"}}
        )

        with mock.patch("backend.application.maria_controller.salvar_sessao") as salvar:
            status, mensagem = controller.processar_confirmacao("sim")

        self.assertTrue(status)
        self.assertEqual(mensagem, "Arquivo criado (fake)")
        executor.executar_real.assert_called_once_with(
            "criar_planilha", {"nome_arquivo": "gastos"}
        )
        salvar.assert_called_once()
        self.assertFalse(controller.sessao.tem_acao_pendente())


class TestInjecaoExecutarLeitura(unittest.TestCase):
    def test_encadear_leitura_stream_usa_executor_injetado(self):
        from backend.application.tool_chaining import encadear_leitura_stream

        chamadas = []

        def executor_fake(nome, args):
            chamadas.append(nome)
            return f"resultado:{nome}"

        class ClienteFalsoContinuacao:
            def continuar_com_resultado_ferramenta_stream(self, **kwargs):
                yield None, {"name": "editar_planilha", "arguments": {}}

        list(
            encadear_leitura_stream(
                ClienteFalsoContinuacao(),
                historico_com_system=[{"role": "system", "content": "sistema"}],
                tool_call_inicial={"name": "listar_arquivos", "arguments": {}},
                tools=[],
                executar_leitura=executor_fake,
            )
        )

        # O executor injetado foi chamado (não o executar_ferramenta_leitura real).
        self.assertEqual(chamadas, ["listar_arquivos"])

    def test_sem_executor_injetado_usa_fallback_global(self):
        from unittest.mock import patch as _patch

        from backend.application import tool_chaining
        from backend.application.tool_chaining import encadear_leitura_stream

        chamadas = []

        def executor_real_fake(nome, args):
            chamadas.append(nome)
            return f"resultado:{nome}"

        class ClienteFalsoContinuacao:
            def continuar_com_resultado_ferramenta_stream(self, **kwargs):
                yield None, {"name": "editar_planilha", "arguments": {}}

        with _patch.object(
            tool_chaining, "executar_ferramenta_leitura", side_effect=executor_real_fake
        ):
            list(
                encadear_leitura_stream(
                    ClienteFalsoContinuacao(),
                    historico_com_system=[{"role": "system", "content": "sistema"}],
                    tool_call_inicial={"name": "listar_arquivos", "arguments": {}},
                    tools=[],
                )
            )

        self.assertEqual(chamadas, ["listar_arquivos"])


if __name__ == "__main__":
    unittest.main()
