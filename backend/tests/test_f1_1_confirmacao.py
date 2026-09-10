"""
Testes de regressão para o ramo de confirmação de _cmd_chat (F1.1).

Usa MagicMock para controller — sem LLM real, sem rede. Cobre os 4 estados
do roteamento: confirmar, cancelar, resposta ambígua e fluxo normal com
tool call (envelope estruturado).

Executar:
    uv run pytest backend/tests/test_f1_1_confirmacao.py -v
"""
from unittest.mock import MagicMock

# Importa a função diretamente para isolar do dispatch completo
from backend.bridge.comandos import _cmd_chat


def _mock_controller(tem_pendente: bool = False, acao: dict | None = None):
    """Cria um controller fake com estado de ação pendente configurável."""
    ctrl = MagicMock()
    ctrl.tem_acao_pendente.return_value = tem_pendente
    ctrl.sessao = MagicMock()
    ctrl.sessao.acao_pendente = acao or {
        "name": "criar_planilha",
        "arguments": {"nome_arquivo": "teste", "colunas": ["A"]},
    }
    return ctrl


class TestCmdChatConfirmacao:
    """Testa os 4 estados do ramo de confirmação em _cmd_chat."""

    def test_confirmar_executa_acao_e_retorna_string(self):
        """'sim' com ação pendente deve executar a ação e devolver string simples."""
        ctrl = _mock_controller(tem_pendente=True)
        ctrl.processar_confirmacao.return_value = (True, "Planilha criada com sucesso: teste.xlsx")

        status, dados, erro = _cmd_chat(ctrl, {"mensagem": "sim"})

        assert status == "ok"
        assert isinstance(dados, str)
        assert "criada" in dados.lower()
        assert erro is None
        ctrl.processar_confirmacao.assert_called_once_with("sim")

    def test_cancelar_retorna_string_cancelamento(self):
        """'não' com ação pendente deve cancelar e devolver string."""
        ctrl = _mock_controller(tem_pendente=True)
        ctrl.processar_confirmacao.return_value = (False, "Ação cancelada.")

        status, dados, erro = _cmd_chat(ctrl, {"mensagem": "não"})

        assert status == "ok"
        assert isinstance(dados, str)
        assert "cancelada" in dados.lower()
        assert erro is None

    def test_resposta_ambigua_retorna_envelope_com_confirmacao_pendente(self):
        """Resposta ambígua deve retornar envelope objeto com confirmacao_pendente."""
        acao = {"name": "criar_planilha", "arguments": {"nome_arquivo": "rel", "colunas": ["X"]}}
        ctrl = _mock_controller(tem_pendente=True, acao=acao)
        ctrl.processar_confirmacao.return_value = (
            None,
            "Não entendi. Você confirma? Responda sim ou não.",
        )

        status, dados, erro = _cmd_chat(ctrl, {"mensagem": "talvez"})

        assert status == "ok"
        assert isinstance(dados, dict)
        assert "confirmacao_pendente" in dados
        assert dados["confirmacao_pendente"]["ferramenta"] == "criar_planilha"
        assert "mensagem" in dados
        assert erro is None

    def test_chat_normal_com_tool_call_retorna_envelope(self):
        """Fluxo normal que resulta em tool call deve retornar envelope com confirmacao_pendente."""
        ctrl = _mock_controller(tem_pendente=False)
        # enviar_mensagem gera um chunk de texto + tool_chunk None
        ctrl.enviar_mensagem.return_value = iter([
            ("Vou criar a planilha para você. ", None),
            (None, {"name": "criar_planilha", "arguments": {"nome_arquivo": "dados", "colunas": ["A"]}}),
        ])
        ctrl.finalizar_mensagem.return_value = (True, {"name": "criar_planilha", "arguments": {}})
        ctrl.get_mensagem_confirmacao.return_value = "Posso criar a planilha? (sim ou não)"
        ctrl.sessao.acao_pendente = {
            "name": "criar_planilha",
            "arguments": {"nome_arquivo": "dados", "colunas": ["A"]},
        }

        status, dados, erro = _cmd_chat(ctrl, {"mensagem": "crie uma planilha de dados"})

        assert status == "ok"
        assert isinstance(dados, dict)
        assert "confirmacao_pendente" in dados
        assert dados["confirmacao_pendente"]["ferramenta"] == "criar_planilha"
        # Texto narrado pelo modelo deve aparecer na mensagem
        assert "planilha" in dados["mensagem"].lower()
        assert erro is None
