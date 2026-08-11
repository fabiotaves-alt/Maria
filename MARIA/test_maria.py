"""
Testes unitários para os módulos do projeto MARIA.
Cobre lógica determinística de chat_session.py e tools_schema.py.

Executar:
    python -m unittest test_maria.py
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
from chat_session import ChatSession, interpretar_confirmacao
from tools_schema import (
    simular_execucao_ferramenta,
    executar_ferramenta_real,
    FERRAMENTA_CRIAR_PLANILHA,
    FERRAMENTA_CRIAR_DOCUMENTO,
    FERRAMENTA_EDITAR_PLANILHA,
)
from excel_handler import criar_planilha_real, editar_planilha_real
from file_utils import gerar_nome_unico, garantir_pasta_arquivos


class TestChatSession(unittest.TestCase):
    """Testes para a classe ChatSession."""
    
    def setUp(self):
        """Configura uma sessão fresca para cada teste."""
        self.sessao = ChatSession(max_mensagens=5)
    
    def test_adicionar_mensagem_user(self):
        """Testa adição de mensagem do usuário."""
        self.sessao.adicionar_mensagem("user", "Olá")
        self.assertEqual(self.sessao.contar_mensagens(), 1)
        self.assertEqual(self.sessao.get_ultima_mensagem_usuario(), "Olá")
    
    def test_adicionar_mensagem_assistant(self):
        """Testa adição de mensagem do assistente."""
        self.sessao.adicionar_mensagem("assistant", "Olá! Como posso ajudar?")
        self.assertEqual(self.sessao.contar_mensagens(), 1)
    
    def test_limite_historico_preserva_system_prompt(self):
        """Testa que o limite de histórico funciona corretamente sem system prompt interno."""
        # O histórico interno não contém mais system prompt
        # Adicionar 10 mensagens (mais que o limite de 5)
        for i in range(10):
            self.sessao.adicionar_mensagem("user", f"Mensagem {i}")
            self.sessao.adicionar_mensagem("assistant", f"Resposta {i}")
        
        # Verificar que get_historico_com_system injeta exatamente UM system prompt
        historico_completo = self.sessao.get_historico_com_system()
        self.assertEqual(historico_completo[0]["role"], "system")
        self.assertIn("MARIA", historico_completo[0]["content"])
        
        # Verificar que há apenas UM system prompt no histórico retornado
        system_prompts = [m for m in historico_completo if m["role"] == "system"]
        self.assertEqual(len(system_prompts), 1)
        
        # Verificar que histórico tem no máximo 5 mensagens user/assistant + 1 system
        self.assertLessEqual(len(historico_completo), 6)  # 5 msgs + 1 system
    
    def test_get_historico_com_system_adiciona_automaticamente(self):
        """Testa que get_historico_com_system adiciona system prompt se não existir."""
        self.sessao.adicionar_mensagem("user", "Olá")
        
        historico = self.sessao.get_historico_com_system()
        
        self.assertEqual(len(historico), 2)  # system + user msg
        self.assertEqual(historico[0]["role"], "system")
        self.assertIn("MARIA", historico[0]["content"])

    def test_system_prompt_exige_portugues(self):
        """Testa que o prompt exige português mesmo em esclarecimentos."""
        self.assertIn("Nunca responda em inglês", ChatSession.SYSTEM_PROMPT)
    
    def test_get_historico_sem_system_exclui_system_prompt(self):
        """Testa que get_historico_sem_system exclui system prompt."""
        self.sessao.adicionar_mensagem("user", "Olá")
        
        historico_com_system = self.sessao.get_historico_com_system()
        historico_sem_system = self.sessao.get_historico_sem_system()
        
        self.assertEqual(len(historico_com_system), 2)  # system + user msg
        self.assertEqual(len(historico_sem_system), 1)  # apenas user msg
        
        # Nenhum item em sem_system deve ter role system
        for msg in historico_sem_system:
            self.assertNotEqual(msg["role"], "system")
    
    def test_limpar_historico(self):
        """Testa que limpar_historico esvazia o histórico interno."""
        self.sessao.adicionar_mensagem("user", "Olá")
        self.sessao.limpar_historico()
        
        self.assertEqual(self.sessao.contar_mensagens(), 0)
        self.assertEqual(self.sessao.historico, [])
        historico = self.sessao.get_historico_com_system()
        self.assertEqual(len(historico), 1)
        self.assertEqual(historico[0]["role"], "system")
    
    def test_role_invalido_raises_error(self):
        """Testa que role inválido levanta ValueError."""
        with self.assertRaises(ValueError):
            self.sessao.adicionar_mensagem("invalid_role", "teste")
    
    def test_acao_pendente_inicialmente_vazia(self):
        """Testa que ação pendente inicia como None."""
        self.assertIsNone(self.sessao.acao_pendente)
        self.assertFalse(self.sessao.tem_acao_pendente())
    
    def test_definir_e_limpar_acao_pendente(self):
        """Testa definição e limpeza de ação pendente."""
        tool_call = {"name": "criar_planilha", "arguments": {"nome_arquivo": "teste"}}
        self.sessao.definir_acao_pendente(tool_call)
        
        self.assertTrue(self.sessao.tem_acao_pendente())
        self.assertEqual(self.sessao.acao_pendente["name"], "criar_planilha")
        self.assertEqual(self.sessao.acao_pendente["arguments"]["nome_arquivo"], "teste")
        self.assertEqual(self.sessao.tentativas_confirmacao_ambigua, 0)
        
        self.sessao.limpar_acao_pendente()
        self.assertFalse(self.sessao.tem_acao_pendente())
        self.assertIsNone(self.sessao.acao_pendente)


class TestInterpretarConfirmacao(unittest.TestCase):
    """Testes para a função interpretar_confirmacao."""
    
    def test_respostas_afirmativas(self):
        """Testa respostas afirmativas retornando True."""
        afirmativas = ["sim", "Sim", "SIM", "pode", "confirmo", "ok", "OK", 
                       "vai", "isso", "claro", "com certeza", "certeza", "vale", "bora"]
        for resposta in afirmativas:
            with self.subTest(resposta=resposta):
                self.assertIs(interpretar_confirmacao(resposta), True)
    
    def test_respostas_negativas(self):
        """Testa respostas negativas retornando False."""
        negativas = ["não", "Não", "NAO", "nao", "cancela", "para", "esquece",
                     "jamais", "de jeito nenhum", "nem pensar", "aborta", "desiste"]
        for resposta in negativas:
            with self.subTest(resposta=resposta):
                self.assertIs(interpretar_confirmacao(resposta), False)
    
    def test_respostas_ambiguas(self):
        """Testa respostas ambíguas retornando None."""
        ambiguas = ["talvez", "hummm", "bla bla", "", "   ", "quero ver", "depois"]
        for resposta in ambiguas:
            with self.subTest(resposta=resposta):
                self.assertIsNone(interpretar_confirmacao(resposta))


class TestExecucaoReal(unittest.TestCase):
    """Testes para execução real de criação de arquivos."""
    
    def setUp(self):
        """Configura pasta temporária para testes."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_pasta = os.environ.get("PASTA_ARQUIVOS_GERADOS")
        os.environ["PASTA_ARQUIVOS_GERADOS"] = self.temp_dir.name
    
    def tearDown(self):
        """Limpa pasta temporária."""
        self.temp_dir.cleanup()
        if self.original_pasta:
            os.environ["PASTA_ARQUIVOS_GERADOS"] = self.original_pasta
        else:
            os.environ.pop("PASTA_ARQUIVOS_GERADOS", None)
    
    def test_criar_planilha_real(self):
        """Testa criação real de planilha Excel."""
        argumentos = {
            "nome_arquivo": "teste_planilha",
            "colunas": ["Data", "Descrição", "Valor"],
            "descricao": "Planilha de teste"
        }
        
        resultado = executar_ferramenta_real("criar_planilha", argumentos)
        
        self.assertIn("Planilha criada com sucesso:", resultado)
        caminho = resultado.split(": ")[1]
        self.assertTrue(os.path.exists(caminho))
        self.assertTrue(caminho.endswith(".xlsx"))
    
    def test_criar_documento_real(self):
        """Testa criação real de documento Word."""
        argumentos = {
            "nome_arquivo": "teste_documento",
            "titulo": "Documento de Teste",
            "conteudo": "Primeiro parágrafo do documento.\n\nSegundo parágrafo do documento."
        }
        
        resultado = executar_ferramenta_real("criar_documento", argumentos)
        
        self.assertIn("Documento criado com sucesso:", resultado)
        caminho = resultado.split(": ")[1]
        self.assertTrue(os.path.exists(caminho))
        self.assertTrue(caminho.endswith(".docx"))

    def test_editar_planilha_real_sobrescreve_arquivo_existente(self):
        """Testa que editar_planilha_real sobrescreve uma planilha existente."""
        criar_planilha_real("teste_edicao", ["A", "B"], "original")

        caminho = editar_planilha_real(
            "teste_edicao",
            colunas=["X", "Y", "Z"],
            linhas=[{"X": 1, "Y": 2, "Z": 3}]
        )

        self.assertTrue(os.path.exists(caminho))
        self.assertTrue(caminho.endswith("teste_edicao.xlsx"))

    def test_editar_planilha_real_arquivo_inexistente_levanta_value_error(self):
        """Testa erro ao editar uma planilha inexistente."""
        with self.assertRaises(ValueError):
            editar_planilha_real("planilha_que_nao_existe", colunas=["A", "B"])


class TestGerarNomeUnico(unittest.TestCase):
    """Testes para função gerar_nome_unico."""
    
    def setUp(self):
        """Configura pasta temporária para testes."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_pasta = os.environ.get("PASTA_ARQUIVOS_GERADOS")
        os.environ["PASTA_ARQUIVOS_GERADOS"] = self.temp_dir.name
    
    def tearDown(self):
        """Limpa pasta temporária."""
        self.temp_dir.cleanup()
        if self.original_pasta:
            os.environ["PASTA_ARQUIVOS_GERADOS"] = self.original_pasta
        else:
            os.environ.pop("PASTA_ARQUIVOS_GERADOS", None)
    
    def test_conflito_gera_sufixo(self):
        """Testa que conflito de nome gera sufixo _1."""
        # Criar primeiro arquivo manualmente
        pasta = garantir_pasta_arquivos()
        primeiro_arquivo = os.path.join(pasta, "relatorio.xlsx")
        with open(primeiro_arquivo, "w") as f:
            f.write("teste")
        
        # Chamar gerar_nome_unico novamente
        nome_unico = gerar_nome_unico("relatorio", ".xlsx")
        
        self.assertEqual(nome_unico, "relatorio_1.xlsx")


class TestFluxoConfirmacao(unittest.TestCase):
    """Testes para fluxo de confirmação com ambiguidade."""
    
    def test_cancelamento_automatico_ambiguidade_repetida(self):
        """Testa cancelamento automático após duas respostas ambíguas."""
        sessao = ChatSession()
        
        # Definir ação pendente
        tool_call = {"name": "criar_planilha", "arguments": {"nome_arquivo": "teste"}}
        sessao.definir_acao_pendente(tool_call)
        
        # Primeira resposta ambígua
        resultado1 = interpretar_confirmacao("talvez")
        self.assertIsNone(resultado1)
        sessao.tentativas_confirmacao_ambigua += 1
        
        # Segunda resposta ambígua
        resultado2 = interpretar_confirmacao("hummm")
        self.assertIsNone(resultado2)
        sessao.tentativas_confirmacao_ambigua += 1
        
        # Verificar que deve cancelar automaticamente (contador >= 2)
        self.assertGreaterEqual(sessao.tentativas_confirmacao_ambigua, 2)
        
        # Simular cancelamento automático
        if sessao.tentativas_confirmacao_ambigua >= 2:
            sessao.limpar_acao_pendente()
        
        self.assertFalse(sessao.tem_acao_pendente())
        self.assertEqual(sessao.tentativas_confirmacao_ambigua, 0)


class TestRegressao(unittest.TestCase):
    """Testes de regressão para bugs conhecidos."""
    
    def test_simulacao_documento_sem_escape_literal(self):
        """Testa que string de simulação de criar_documento não contém \\\" literal."""
        argumentos = {
            "nome_arquivo": "relatorio",
            "titulo": "Relatório Mensal",
            "conteudo": "Conteúdo de teste"
        }
        
        resultado = simular_execucao_ferramenta("criar_documento", argumentos)
        
        # Verificar que não há escape literal de aspas duplas
        self.assertNotIn('\\"', resultado)
        # A string deve conter aspas normais, não escaped
        self.assertIn("Relatório Mensal", resultado)
    
    @patch('ollama_client.requests.Session')
    def test_chat_com_tools_tool_calls_malformado(self, mock_session_class):
        """Testa que chat_com_tools não quebra com tool_calls malformado."""
        from ollama_client import OllamaClient
        
        # Mock da sessão e response
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": "Resposta do modelo",
                "tool_calls": []  # Lista vazia
            }
        }
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen2.5:7b"}]}
        )
        
        cliente = OllamaClient()
        conteudo, tool_call = cliente.chat_com_tools(
            mensagem_usuario="teste",
            historico=[{"role": "user", "content": "teste"}],
            tools=[FERRAMENTA_CRIAR_PLANILHA]
        )
        
        self.assertEqual(conteudo, "Resposta do modelo")
        self.assertIsNone(tool_call)
    
    @patch('ollama_client.requests.Session')
    def test_chat_com_tools_tool_calls_sem_function(self, mock_session_class):
        """Testa que chat_com_tools lida com tool_call sem 'function'."""
        from ollama_client import OllamaClient
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": "Resposta do modelo",
                "tool_calls": [{"id": "123"}]  # Sem 'function'
            }
        }
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen2.5:7b"}]}
        )
        
        cliente = OllamaClient()
        conteudo, tool_call = cliente.chat_com_tools(
            mensagem_usuario="teste",
            historico=[{"role": "user", "content": "teste"}],
            tools=[FERRAMENTA_CRIAR_PLANILHA]
        )
        
        self.assertEqual(conteudo, "Resposta do modelo")
        self.assertIsNone(tool_call)
    
    @patch('ollama_client.requests.Session')
    def test_chat_com_tools_tool_calls_sem_name(self, mock_session_class):
        """Testa que chat_com_tools lida com tool_call sem 'name'."""
        from ollama_client import OllamaClient
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": "Resposta do modelo",
                "tool_calls": [{"function": {"arguments": "{}"}}]  # Sem 'name'
            }
        }
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen2.5:7b"}]}
        )
        
        cliente = OllamaClient()
        conteudo, tool_call = cliente.chat_com_tools(
            mensagem_usuario="teste",
            historico=[{"role": "user", "content": "teste"}],
            tools=[FERRAMENTA_CRIAR_PLANILHA]
        )
        
        self.assertEqual(conteudo, "Resposta do modelo")
        self.assertIsNone(tool_call)

    @patch('ollama_client.requests.Session')
    def test_chat_com_tools_stream_tool_calls_vazio_nao_quebra(self, mock_session_class):
        """Testa streaming com tool_calls vazio."""
        from ollama_client import OllamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        linhas_stream = [
            json.dumps({"message": {"content": "Olá", "tool_calls": []}}).encode("utf-8"),
            json.dumps({"message": {"content": "!", "tool_calls": []}, "done": True}).encode("utf-8"),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas_stream)
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen2.5:7b"}]}
        )

        chunks = list(OllamaClient(model="qwen2.5:7b").chat_com_tools_stream(
            mensagem_usuario="oi",
            historico=[],
            tools=[FERRAMENTA_CRIAR_PLANILHA]
        ))

        self.assertEqual("".join(chunk for chunk, _ in chunks if chunk), "Olá!")
        self.assertIsNone(chunks[-1][1])

    def test_timeout_de_streaming_nao_faz_retry(self):
        """Testa que timeout de geração é propagado sem nova tentativa."""
        from benchmark.runners.maria_runner import MariaRunner
        from benchmark.tasks.task_schema import MariaTask
        from ollama_client import OllamaClient, OllamaTimeoutError

        class ClienteComTimeout(OllamaClient):
            def __init__(self):
                self.model = "qwen2.5:7b"
                self.chamadas = 0

            def chat_com_tools_stream(self, **kwargs):
                self.chamadas += 1
                raise OllamaTimeoutError("timeout de teste")

        cliente = ClienteComTimeout()
        runner = MariaRunner(cliente=cliente)
        task = MariaTask(999, "Timeout", "Teste", "Olá")

        with self.assertRaises(OllamaTimeoutError):
            runner._enviar_com_retry(ChatSession(), task)

        self.assertEqual(cliente.chamadas, 1)


class TestOllamaClientErrorModeloNaoInstalado(unittest.TestCase):
    """Testes para erro claro quando modelo não está instalado."""
    
    @patch('ollama_client.requests.Session')
    def test_modelo_nao_instalado_levanta_erro_claro(self, mock_session_class):
        """Testa que OllamaClientError é levantado com mensagem clara quando modelo não existe."""
        from ollama_client import OllamaClient, OllamaClientError
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock de /api/tags retornando lista sem o modelo esperado
        mock_tags_response = MagicMock()
        mock_tags_response.status_code = 200
        mock_tags_response.json.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "mistral"}
            ]
        }
        mock_session.get.return_value = mock_tags_response
        
        cliente = OllamaClient(model="qwen2.5:7b")
        
        with self.assertRaises(OllamaClientError) as context:
            cliente._check_connection()
        
        # Verificar mensagem de erro clara
        erro_msg = str(context.exception)
        self.assertIn("não está instalado", erro_msg)
        self.assertIn("qwen2.5:7b", erro_msg)
        self.assertIn("ollama pull", erro_msg)


if __name__ == "__main__":
    unittest.main()
