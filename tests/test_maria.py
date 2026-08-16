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
import time
from unittest.mock import patch, MagicMock
from core.chat_session import ChatSession, interpretar_confirmacao
from core.ollama_client import _montar_mensagens_com_reforco
from core.tools_schema import (
    simular_execucao_ferramenta,
    executar_ferramenta_real,
    validar_argumentos_obrigatorios,
    FERRAMENTA_CRIAR_PLANILHA,
    FERRAMENTA_EDITAR_PLANILHA,
    executar_ferramenta_leitura,
)
from core.excel_handler import criar_planilha_real, editar_planilha_real
from core.file_utils import (
    gerar_nome_unico,
    garantir_pasta_arquivos,
    resolver_caminho_permitido,
    listar_arquivos,
    ler_documento,
)
from core.session_storage import salvar_sessao, listar_sessoes_salvas, carregar_sessao
from benchmark.analysis.language_check import resposta_em_portugues
from benchmark.analysis.metrics import calculate_maria_metrics
from benchmark.tasks.task_schema import MariaTaskResult
from core.ollama_client import OllamaClient


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


class TestBenchmarkLanguageCompliance(unittest.TestCase):
    """Testes para a checagem de conformidade de idioma do benchmark."""

    def test_resposta_em_portugues_identifica_portugues(self):
        self.assertTrue(resposta_em_portugues("Por favor, responda em português."))
        self.assertTrue(resposta_em_portugues("Claro, vou ajudar você com isso."))

    def test_resposta_em_portugues_rejeita_inglês_significativo(self):
        self.assertFalse(resposta_em_portugues("Please provide the details in English."))
        self.assertFalse(resposta_em_portugues("Sure, I can help you with that."))

    def test_resposta_em_portugues_tolerancia_a_texto_misto(self):
        self.assertFalse(resposta_em_portugues("Por favor, please continue em português."))
        self.assertTrue(resposta_em_portugues("Por favor, não use termos em inglês."))


class TestBenchmarkMetrics(unittest.TestCase):
    """Testes para cálculo de métricas agregadas do benchmark."""

    def test_calculate_maria_metrics_includes_language_compliance(self):
        results = [
            MariaTaskResult(
                task_id=1,
                task_name="Teste 1",
                category="categoria",
                model="maria",
                tool_detected="criar_planilha",
                tool_correct=True,
                confirmation_completed=True,
                keyword_match=True,
                runtime_ok=True,
                final_message="Tudo certo.",
                latency_ms=100.0,
                errors=[],
                raw_tool_args={},
                language_ok=True,
            ),
            MariaTaskResult(
                task_id=2,
                task_name="Teste 2",
                category="categoria",
                model="maria",
                tool_detected="criar_planilha",
                tool_correct=False,
                confirmation_completed=False,
                keyword_match=False,
                runtime_ok=False,
                final_message="Houve um problema.",
                latency_ms=200.0,
                errors=[{"kind": "OllamaClientError", "message": "Falha"}],
                raw_tool_args={},
                language_ok=False,
            ),
        ]

        metrics = calculate_maria_metrics(results)

        self.assertEqual(metrics.total_tasks, 2)
        self.assertAlmostEqual(metrics.language_compliance_rate, 0.5)
        self.assertEqual(metrics.error_distribution.get("OllamaClientError"), 1)

    def test_calculate_maria_metrics_includes_avg_tokens_per_second(self):
        results = [
            MariaTaskResult(
                task_id=1,
                task_name="Teste 1",
                category="categoria",
                model="maria",
                tool_detected="criar_planilha",
                tool_correct=True,
                confirmation_completed=True,
                keyword_match=True,
                runtime_ok=True,
                final_message="Tudo certo.",
                latency_ms=100.0,
                errors=[],
                raw_tool_args={},
                language_ok=True,
                tokens_gerados=120,
                tokens_por_segundo=20.0,
            ),
            MariaTaskResult(
                task_id=2,
                task_name="Teste 2",
                category="categoria",
                model="maria",
                tool_detected="criar_planilha",
                tool_correct=False,
                confirmation_completed=False,
                keyword_match=False,
                runtime_ok=False,
                final_message="Erro.",
                latency_ms=200.0,
                errors=[{"kind": "OllamaClientError", "message": "Falha"}],
                raw_tool_args={},
                language_ok=False,
                tokens_gerados=80,
                tokens_por_segundo=10.0,
            ),
        ]

        metrics = calculate_maria_metrics(results)
        self.assertAlmostEqual(metrics.avg_tokens_por_segundo, 15.0)

    def test_chat_com_tools_stream_com_metricas_acumula_tokens(self):
        class FakeResponse:
            def __init__(self, payloads):
                self.payloads = payloads

            def iter_lines(self):
                for payload in self.payloads:
                    time.sleep(0.03)
                    yield payload

        client = OllamaClient(timeout=10)
        client._make_request = lambda payload, stream=False: FakeResponse([
            json.dumps({"message": {"content": "Olá "}}).encode("utf-8"),
            json.dumps({"message": {"content": "mundo"}, "done": True, "eval_count": 15}).encode("utf-8"),
        ])

        texto, tool_call, tokens_gerados, tokens_por_segundo, ttft_ms = client.chat_com_tools_stream_com_metricas(
            "teste",
            historico=None,
            tools=None,
        )

        self.assertEqual(texto, "Olá mundo")
        self.assertEqual(tokens_gerados, 15)
        self.assertGreater(tokens_por_segundo, 0)
        self.assertIsNotNone(ttft_ms)
        self.assertGreaterEqual(ttft_ms, 0)
        self.assertIsNone(tool_call)

    def test_chat_com_tools_stream_com_metricas_guarda_contra_duracao_irreal(self):
        """Reproduz o padrão observado em produção (eval_count alto, duração
        quase nula) e garante que tokens_por_segundo não retorna um valor
        fisicamente implausível."""
        class FakeResponse:
            def __init__(self, payloads):
                self.payloads = payloads

            def iter_lines(self):
                yield from self.payloads

        client = OllamaClient(timeout=10)
        client._make_request = lambda payload, stream=False: FakeResponse([
            json.dumps({
                "message": {"content": "resposta completa em um único chunk"},
                "done": True,
                "eval_count": 400,
            }).encode("utf-8"),
        ])

        _, _, tokens_gerados, tokens_por_segundo, ttft_ms = client.chat_com_tools_stream_com_metricas(
            "teste", historico=None, tools=None,
        )

        self.assertEqual(tokens_gerados, 400)
        self.assertEqual(tokens_por_segundo, 0.0)
        self.assertIsNotNone(ttft_ms)

    def test_diagnostico_falha_sem_erro_detecta_tool_incorreto(self):
        result = MariaTaskResult(
            task_id=3,
            task_name="Teste 3",
            category="categoria",
            model="maria",
            tool_detected="editar_planilha",
            tool_correct=False,
            confirmation_completed=True,
            keyword_match=True,
            runtime_ok=True,
            final_message="Ferramenta incorreta.",
            latency_ms=150.0,
            errors=[],
            raw_tool_args={},
            language_ok=True,
        )
        from benchmark.analysis.report import _diagnosticar_falha
        self.assertEqual(_diagnosticar_falha(result), "Tool call incorreto ou ferramenta inesperada")

    def test_diagnostico_falha_por_idioma_incorreto(self):
        result = MariaTaskResult(
            task_id=4,
            task_name="Teste 4",
            category="categoria",
            model="maria",
            tool_detected="criar_documento",
            tool_correct=True,
            confirmation_completed=True,
            keyword_match=True,
            runtime_ok=True,
            final_message="This is a response in English.",
            latency_ms=120.0,
            errors=[],
            raw_tool_args={},
            language_ok=False,
        )
        from benchmark.analysis.report import _diagnosticar_falha
        self.assertEqual(_diagnosticar_falha(result), "Resposta em idioma incorreto")

    def test_editar_planilha_real_arquivo_inexistente_levanta_value_error(self):
        """Testa erro ao editar uma planilha inexistente."""
        with self.assertRaises(ValueError):
            editar_planilha_real("planilha_que_nao_existe", colunas=["A", "B"])


class TestValidacaoArgumentos(unittest.TestCase):
    """Testes para validação de campos obrigatórios em ferramentas."""

    def test_validar_argumentos_obrigatorios_ausente_levanta_value_error(self):
        """Campo obrigatório ausente deve ser rejeitado antes da execução."""
        with self.assertRaisesRegex(ValueError, "colunas"):
            validar_argumentos_obrigatorios(
                "criar_planilha",
                {"nome_arquivo": "teste"}
            )

    def test_validar_argumentos_obrigatorios_vazio_levanta_value_error(self):
        """String vazia deve ser tratada como campo obrigatório ausente."""
        with self.assertRaisesRegex(ValueError, "titulo"):
            validar_argumentos_obrigatorios(
                "criar_documento",
                {"nome_arquivo": "x", "titulo": "   ", "conteudo": "y"}
            )


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
    
    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_tool_calls_malformado(self, mock_session_class):
        """Testa que chat_com_tools não quebra com tool_calls malformado."""
        from core.ollama_client import OllamaClient
        
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
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )
        
        cliente = OllamaClient()
        conteudo, tool_call = cliente.chat_com_tools(
            mensagem_usuario="teste",
            historico=[{"role": "user", "content": "teste"}],
            tools=[FERRAMENTA_CRIAR_PLANILHA]
        )
        
        self.assertEqual(conteudo, "Resposta do modelo")
        self.assertIsNone(tool_call)
    
    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_tool_calls_sem_function(self, mock_session_class):
        """Testa que chat_com_tools lida com tool_call sem 'function'."""
        from core.ollama_client import OllamaClient
        
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
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )
        
        cliente = OllamaClient()
        conteudo, tool_call = cliente.chat_com_tools(
            mensagem_usuario="teste",
            historico=[{"role": "user", "content": "teste"}],
            tools=[FERRAMENTA_CRIAR_PLANILHA]
        )
        
        self.assertEqual(conteudo, "Resposta do modelo")
        self.assertIsNone(tool_call)
    
    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_tool_calls_sem_name(self, mock_session_class):
        """Testa que chat_com_tools lida com tool_call sem 'name'."""
        from core.ollama_client import OllamaClient
        
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
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )
        
        cliente = OllamaClient()
        conteudo, tool_call = cliente.chat_com_tools(
            mensagem_usuario="teste",
            historico=[{"role": "user", "content": "teste"}],
            tools=[FERRAMENTA_CRIAR_PLANILHA]
        )
        
        self.assertEqual(conteudo, "Resposta do modelo")
        self.assertIsNone(tool_call)

    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_stream_tool_calls_vazio_nao_quebra(self, mock_session_class):
        """Testa streaming com tool_calls vazio."""
        from core.ollama_client import OllamaClient

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
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )

        chunks = list(OllamaClient(model="qwen3.5:4b").chat_com_tools_stream(
            mensagem_usuario="oi",
            historico=[],
            tools=[FERRAMENTA_CRIAR_PLANILHA]
        ))

        self.assertEqual("".join(chunk for chunk, _ in chunks if chunk), "Olá!")
        self.assertIsNone(chunks[-1][1])

    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_stream_tool_call_vazada_como_texto(self, mock_session_class):
        """Testa que uma tool call vazada como texto no content é detectada via fallback."""
        from core.ollama_client import OllamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        conteudo_vazado = (
            'brtc\n{"name": "editar_planilha", "arguments": '
            '{"nome_arquivo": "estoque", "colunas": ["Produto", "Quantidade"]}}\n</tool_call>'
        )
        linhas_stream = [
            json.dumps({"message": {"content": conteudo_vazado, "tool_calls": []}, "done": True}).encode("utf-8"),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas_stream)
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )

        chunks = list(OllamaClient(model="qwen3.5:4b").chat_com_tools_stream(
            mensagem_usuario="edite a planilha",
            historico=[],
            tools=[FERRAMENTA_EDITAR_PLANILHA]
        ))

        tool_call_final = chunks[-1][1]
        self.assertIsNotNone(tool_call_final)
        self.assertEqual(tool_call_final["name"], "editar_planilha")
        self.assertEqual(tool_call_final["arguments"]["nome_arquivo"], "estoque")

    def test_timeout_de_streaming_nao_faz_retry(self):
        """Testa que timeout de geração é propagado sem nova tentativa."""
        from benchmark.runners.maria_runner import MariaRunner
        from benchmark.tasks.task_schema import MariaTask
        from core.ollama_client import OllamaClient, OllamaTimeoutError

        class ClienteComTimeout(OllamaClient):
            def __init__(self):
                self.model = "qwen3.5:4b"
                self.chamadas = 0

            def chat_com_tools_stream(self, **kwargs):
                self.chamadas += 1
                raise OllamaTimeoutError("timeout de teste")

            def chat_com_tools_stream_com_metricas(self, **kwargs):
                self.chamadas += 1
                raise OllamaTimeoutError("timeout de teste")

        cliente = ClienteComTimeout()
        runner = MariaRunner(cliente=cliente)
        task = MariaTask(999, "Timeout", "Teste", "Olá")

        with self.assertRaises(OllamaTimeoutError):
            runner._enviar_com_retry(ChatSession(), task)

        self.assertEqual(cliente.chamadas, 1)

    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_stream_recupera_tool_call_do_campo_thinking(self, mock_session_class):
        """Tool call presa em 'thinking' (bug do Qwen3.5) deve ser recuperada mesmo com content vazio."""
        from core.ollama_client import OllamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        thinking_com_tool_call = (
            'Vou criar a planilha.\n<tool_call>\n'
            '{"name": "criar_planilha", "arguments": '
            '{"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}}\n'
            '</tool_call>'
        )
        linhas_stream = [
            json.dumps({
                "message": {"content": "", "thinking": thinking_com_tool_call, "tool_calls": []},
                "done": True,
            }).encode("utf-8"),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas_stream)
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )

        cliente = OllamaClient(model="qwen3.5:4b")
        chunks = list(cliente.chat_com_tools_stream(
            mensagem_usuario="crie uma planilha de gastos",
            historico=[],
            tools=[FERRAMENTA_CRIAR_PLANILHA],
        ))

        tool_call_final = chunks[-1][1]
        self.assertIsNotNone(tool_call_final)
        self.assertEqual(tool_call_final["name"], "criar_planilha")
        self.assertEqual(tool_call_final["arguments"]["nome_arquivo"], "gastos")

    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_stream_com_metricas_recupera_tool_call_vazada_como_texto(self, mock_session_class):
        """chat_com_tools_stream_com_metricas hoje não tem fallback textual — este teste cobre o gap."""
        from core.ollama_client import OllamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        conteudo_vazado = (
            '{"name": "criar_planilha", "arguments": '
            '{"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}}'
        )
        linhas_stream = [
            json.dumps({
                "message": {"content": conteudo_vazado, "tool_calls": []},
                "done": True,
                "eval_count": 40,
            }).encode("utf-8"),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas_stream)
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )

        cliente = OllamaClient(model="qwen3.5:4b")
        texto, tool_call, tokens_gerados, tokens_por_segundo, ttft_ms = cliente.chat_com_tools_stream_com_metricas(
            "crie uma planilha de gastos",
            historico=[],
            tools=[FERRAMENTA_CRIAR_PLANILHA],
        )

        self.assertIsNotNone(tool_call)
        self.assertEqual(tool_call["name"], "criar_planilha")
        self.assertEqual(tool_call["arguments"]["nome_arquivo"], "gastos")
        self.assertEqual(tokens_gerados, 40)

    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_stream_com_metricas_recupera_tool_call_do_campo_thinking(self, mock_session_class):
        """Combina os dois gaps: campo 'thinking' + método de métricas do benchmark."""
        from core.ollama_client import OllamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        thinking_com_tool_call = (
            '<tool_call>\n{"name": "editar_planilha", "arguments": '
            '{"nome_arquivo": "estoque", "colunas": ["Produto", "Quantidade"]}}\n</tool_call>'
        )
        linhas_stream = [
            json.dumps({
                "message": {"content": "", "thinking": thinking_com_tool_call, "tool_calls": []},
                "done": True,
                "eval_count": 55,
            }).encode("utf-8"),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas_stream)
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )

        cliente = OllamaClient(model="qwen3.5:4b")
        texto, tool_call, tokens_gerados, tokens_por_segundo, ttft_ms = cliente.chat_com_tools_stream_com_metricas(
            "atualize a planilha estoque",
            historico=[],
            tools=[FERRAMENTA_EDITAR_PLANILHA],
        )

        self.assertIsNotNone(tool_call)
        self.assertEqual(tool_call["name"], "editar_planilha")
        self.assertEqual(tokens_gerados, 55)

    @patch('core.ollama_client.requests.Session')
    def test_continuar_com_resultado_ferramenta_stream_recupera_tool_call_do_campo_thinking(self, mock_session_class):
        """Mesma cobertura de 'thinking' para o método de continuação (após leitura de arquivo)."""
        from core.ollama_client import OllamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        thinking_com_tool_call = (
            '<tool_call>\n{"name": "criar_planilha", "arguments": '
            '{"nome_arquivo": "novo", "colunas": ["A", "B"]}}\n</tool_call>'
        )
        linhas_stream = [
            json.dumps({
                "message": {"content": "", "thinking": thinking_com_tool_call, "tool_calls": []},
                "done": True,
            }).encode("utf-8"),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas_stream)
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )

        cliente = OllamaClient(model="qwen3.5:4b")
        chunks = list(cliente.continuar_com_resultado_ferramenta_stream(
            historico=[{"role": "system", "content": "sistema"}],
            tool_call={"name": "listar_arquivos", "arguments": {}},
            resultado="A pasta está vazia.",
            tools=[FERRAMENTA_CRIAR_PLANILHA],
        ))

        tool_call_final = chunks[-1][1]
        self.assertIsNotNone(tool_call_final)
        self.assertEqual(tool_call_final["name"], "criar_planilha")
    
    def test_montar_mensagens_com_reforco_mescla_system_existente(self):


        historico = [
            {"role": "system", "content": "PROMPT LONGO ORIGINAL"},
            {"role": "user", "content": "mensagem anterior"},
            {"role": "assistant", "content": "resposta anterior"},
        ]
        mensagens = _montar_mensagens_com_reforco(historico, "nova mensagem")

        systems = [m for m in mensagens if m["role"] == "system"]
        self.assertEqual(len(systems), 1)
        self.assertIn("PROMPT LONGO ORIGINAL", systems[0]["content"])
        self.assertIn("IMPORTANTE: Você DEVE usar as ferramentas disponíveis", systems[0]["content"])
        self.assertEqual(mensagens[-1], {"role": "user", "content": "nova mensagem"})
        self.assertEqual(historico[0]["content"], "PROMPT LONGO ORIGINAL")  # historico não mutado

    def test_montar_mensagens_com_reforco_sem_system_previo(self):
        from core.ollama_client import _montar_mensagens_com_reforco
        mensagens = _montar_mensagens_com_reforco(None, "mensagem")

        systems = [m for m in mensagens if m["role"] == "system"]
        self.assertEqual(len(systems), 1)
        self.assertIn("IMPORTANTE: Você DEVE usar as ferramentas disponíveis", systems[0]["content"])

    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_envia_uma_unica_mensagem_system(self, mock_session_class):
        from core.ollama_client import OllamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"message": {"content": "ok", "tool_calls": []}}
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )

        cliente = OllamaClient(model="qwen3.5:4b")
        historico = [{"role": "system", "content": "PROMPT LONGO DA SESSAO"}]
        cliente.chat_com_tools(
            mensagem_usuario="crie uma planilha", historico=historico, tools=[FERRAMENTA_CRIAR_PLANILHA],
        )

        payload_enviado = mock_session.post.call_args.kwargs["json"]
        mensagens_system = [m for m in payload_enviado["messages"] if m["role"] == "system"]
        self.assertEqual(len(mensagens_system), 1)
        self.assertIn("PROMPT LONGO DA SESSAO", mensagens_system[0]["content"])

    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_stream_envia_uma_unica_mensagem_system(self, mock_session_class):
        from core.ollama_client import OllamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        linhas_stream = [
            json.dumps({"message": {"content": "ok", "tool_calls": []}, "done": True}).encode("utf-8"),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas_stream)
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )

        cliente = OllamaClient(model="qwen3.5:4b")
        historico = [{"role": "system", "content": "PROMPT LONGO DA SESSAO"}]
        list(cliente.chat_com_tools_stream(
            mensagem_usuario="crie uma planilha", historico=historico, tools=[FERRAMENTA_CRIAR_PLANILHA],
        ))

        payload_enviado = mock_session.post.call_args.kwargs["json"]
        mensagens_system = [m for m in payload_enviado["messages"] if m["role"] == "system"]
        self.assertEqual(len(mensagens_system), 1)
        self.assertIn("PROMPT LONGO DA SESSAO", mensagens_system[0]["content"])

    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_stream_com_metricas_envia_uma_unica_mensagem_system(self, mock_session_class):
        from core.ollama_client import OllamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        linhas_stream = [
            json.dumps({"message": {"content": "ok"}, "done": True, "eval_count": 1}).encode("utf-8"),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas_stream)
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "qwen3.5:4b"}]}
        )

        cliente = OllamaClient(model="qwen3.5:4b")
        historico = [{"role": "system", "content": "PROMPT LONGO DA SESSAO"}]
        cliente.chat_com_tools_stream_com_metricas(
            "crie uma planilha", historico=historico, tools=[FERRAMENTA_CRIAR_PLANILHA],
        )

        payload_enviado = mock_session.post.call_args.kwargs["json"]
        mensagens_system = [m for m in payload_enviado["messages"] if m["role"] == "system"]
        self.assertEqual(len(mensagens_system), 1)
        self.assertIn("PROMPT LONGO DA SESSAO", mensagens_system[0]["content"])






class TestSessionStorage(unittest.TestCase):
    """Testes para persistência de sessões em disco."""

    def setUp(self):
        """Configura pasta temporária isolada para testes."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_pasta = os.environ.get("PASTA_SESSOES")
        os.environ["PASTA_SESSOES"] = self.temp_dir.name

    def tearDown(self):
        """Limpa pasta temporária e restaura variável de ambiente."""
        self.temp_dir.cleanup()
        if self.original_pasta:
            os.environ["PASTA_SESSOES"] = self.original_pasta
        else:
            os.environ.pop("PASTA_SESSOES", None)

    def test_salvar_e_carregar_sessao(self):
        """Testa que uma sessão salva pode ser recarregada com o mesmo histórico."""
        sessao = ChatSession()
        sessao.adicionar_mensagem("user", "Olá")
        sessao.adicionar_mensagem("assistant", "Oi! Como posso ajudar?")

        caminho = salvar_sessao(sessao.to_dict(), "sessao_20260101_120000.json")
        self.assertTrue(os.path.exists(caminho))

        dados_carregados = carregar_sessao(caminho)
        sessao_restaurada = ChatSession.from_dict(dados_carregados)

        self.assertEqual(sessao_restaurada.contar_mensagens(), 2)
        self.assertEqual(sessao_restaurada.get_ultima_mensagem_usuario(), "Olá")

    def test_listar_sessoes_ordena_mais_recentes_primeiro(self):
        """Testa que listar_sessoes_salvas ordena por nome (timestamp) decrescente."""
        sessao = ChatSession()
        sessao.adicionar_mensagem("user", "teste")

        salvar_sessao(sessao.to_dict(), "sessao_20260101_100000.json")
        salvar_sessao(sessao.to_dict(), "sessao_20260102_100000.json")

        sessoes = listar_sessoes_salvas()

        self.assertEqual(len(sessoes), 2)
        self.assertEqual(sessoes[0]["nome_arquivo"], "sessao_20260102_100000.json")
        self.assertEqual(sessoes[1]["nome_arquivo"], "sessao_20260101_100000.json")
        self.assertEqual(sessoes[0]["qtd_mensagens"], 1)

    def test_listar_sessoes_ignora_arquivo_corrompido(self):
        """Testa que um arquivo de sessão corrompido é ignorado, não levanta exceção."""
        pasta = os.environ["PASTA_SESSOES"]
        os.makedirs(pasta, exist_ok=True)
        caminho_corrompido = os.path.join(pasta, "sessao_20260103_100000.json")
        with open(caminho_corrompido, "w", encoding="utf-8") as arquivo:
            arquivo.write("{ json inválido")

        sessoes = listar_sessoes_salvas()

        self.assertEqual(sessoes, [])

    def test_carregar_sessao_inexistente_levanta_value_error(self):
        """Testa que carregar uma sessão inexistente levanta ValueError."""
        with self.assertRaises(ValueError):
            carregar_sessao(os.path.join(os.environ["PASTA_SESSOES"], "nao_existe.json"))


class TestOllamaClientErrorModeloNaoInstalado(unittest.TestCase):
    """Testes para erro claro quando modelo não está instalado."""
    
    @patch('core.ollama_client.requests.Session')
    def test_modelo_nao_instalado_levanta_erro_claro(self, mock_session_class):
        """Testa que OllamaClientError é levantado com mensagem clara quando modelo não existe."""
        from core.ollama_client import OllamaClient, OllamaClientError
        
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
        
        cliente = OllamaClient(model="qwen3.5:4b")
        
        with self.assertRaises(OllamaClientError) as context:
            cliente._check_connection()
        
        # Verificar mensagem de erro clara
        erro_msg = str(context.exception)
        self.assertIn("não está instalado", erro_msg)
        self.assertIn("qwen3.5:4b", erro_msg)
        self.assertIn("ollama pull", erro_msg)


class TestAcessoLeitura(unittest.TestCase):
    """Testes para as ferramentas de leitura (listar_arquivos, ler_documento)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_pastas = os.environ.get("PASTAS_PERMITIDAS")
        os.environ["PASTAS_PERMITIDAS"] = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()
        if self.original_pastas:
            os.environ["PASTAS_PERMITIDAS"] = self.original_pastas
        else:
            os.environ.pop("PASTAS_PERMITIDAS", None)

    def test_traversal_negado(self):
        """Testa que um caminho fora das pastas permitidas é rejeitado."""
        with self.assertRaises(ValueError):
            resolver_caminho_permitido("../../etc/passwd")

    def test_listar_pasta_temporaria(self):
        """Testa listagem de arquivos em uma pasta permitida."""
        caminho_arquivo = os.path.join(self.temp_dir.name, "nota.txt")
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write("conteúdo de teste")

        itens = listar_arquivos()

        nomes = [item["nome"] for item in itens]
        self.assertIn("nota.txt", nomes)

    def test_listar_pasta_vazia(self):
        """Testa que uma pasta permitida vazia retorna lista vazia."""
        self.assertEqual(listar_arquivos(), [])

    def test_listar_pasta_padrao_ausente_nao_gera_caminho_duplicado(self):
        """Testa que listar_arquivos() sem pasta explícita não duplica o
        caminho e cria a pasta padrão automaticamente se ainda não existir."""
        pasta_inexistente = os.path.join(self.temp_dir.name, "ainda_nao_criada")
        os.environ["PASTAS_PERMITIDAS"] = pasta_inexistente

        self.assertFalse(os.path.isdir(pasta_inexistente))

        itens = listar_arquivos()

        self.assertEqual(itens, [])
        self.assertTrue(os.path.isdir(pasta_inexistente))

    def test_leitura_truncada(self):
        """Testa que um arquivo maior que max_chars é truncado corretamente."""
        caminho_arquivo = os.path.join(self.temp_dir.name, "grande.txt")
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write("a" * 100)

        doc = ler_documento("grande.txt", max_chars=10)

        self.assertTrue(doc["truncado"])
        self.assertEqual(len(doc["texto"]), 10)
        self.assertEqual(doc["total_chars"], 100)

    def test_leitura_nao_truncada(self):
        """Testa que um arquivo menor que max_chars não é marcado como truncado."""
        caminho_arquivo = os.path.join(self.temp_dir.name, "pequeno.txt")
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write("texto curto")

        doc = ler_documento("pequeno.txt")

        self.assertFalse(doc["truncado"])
        self.assertEqual(doc["texto"], "texto curto")

    def test_extensao_nao_suportada(self):
        """Testa que uma extensão fora da lista permitida levanta ValueError."""
        caminho_arquivo = os.path.join(self.temp_dir.name, "programa.exe")
        with open(caminho_arquivo, "wb") as f:
            f.write(b"binario")

        with self.assertRaises(ValueError):
            ler_documento("programa.exe")

    def test_arquivo_inexistente_levanta_value_error(self):
        """Testa que ler um arquivo inexistente levanta ValueError."""
        with self.assertRaises(ValueError):
            ler_documento("nao_existe.txt")


class TestFerramentasLeitura(unittest.TestCase):
    """Testes para o executor de ferramentas de leitura (tools_schema)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_pastas = os.environ.get("PASTAS_PERMITIDAS")
        os.environ["PASTAS_PERMITIDAS"] = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()
        if self.original_pastas:
            os.environ["PASTAS_PERMITIDAS"] = self.original_pastas
        else:
            os.environ.pop("PASTAS_PERMITIDAS", None)

    def test_executar_listar_arquivos_pasta_vazia(self):
        resultado = executar_ferramenta_leitura("listar_arquivos", {})
        self.assertIn("vazia", resultado.lower())

    def test_executar_resumir_documento(self):
        caminho_arquivo = os.path.join(self.temp_dir.name, "notas.txt")
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write("Reunião marcada para sexta-feira.")

        resultado = executar_ferramenta_leitura(
            "resumir_documento", {"nome_arquivo": "notas.txt"}
        )

        self.assertIn("Reunião marcada para sexta-feira.", resultado)

    def test_executar_ferramenta_desconhecida(self):
        with self.assertRaises(ValueError):
            executar_ferramenta_leitura("apagar_tudo", {})


class TestSelecaoModeloCLI(unittest.TestCase):
    """Testes para a seleção de modelo via argumento -m/--modelo (main.py)."""

    def test_controller_usa_modelo_informado(self):
        from main import MariaController
        controller = MariaController(modelo="qwen3:8b")
        controller.inicializar()
        self.assertEqual(controller.cliente.model, "qwen3:8b")

    def test_controller_usa_modelo_padrao_quando_nao_informado(self):
        from main import MariaController
        from core.config import OLLAMA_MODEL
        controller = MariaController()
        controller.inicializar()
        self.assertEqual(controller.cliente.model, OLLAMA_MODEL)


class TestAquecimentoModelo(unittest.TestCase):
    """Testes para o warmup do modelo na inicialização interativa (main.py)."""

    def test_aquecer_modelo_chama_enviar_mensagem(self):
        from main import MariaController
        controller = MariaController()
        controller.inicializar()
        controller.cliente.enviar_mensagem = MagicMock(return_value="ok")

        controller.aquecer_modelo()

        controller.cliente.enviar_mensagem.assert_called_once()

    def test_aquecer_modelo_nao_propaga_excecao(self):
        from main import MariaController
        from core.ollama_client import OllamaClientError
        controller = MariaController()
        controller.inicializar()
        controller.cliente.enviar_mensagem = MagicMock(side_effect=OllamaClientError("falha"))

        controller.aquecer_modelo()  # não deve levantar exceção


class TestAcuraciaDeArgumentos(unittest.TestCase):
    """Testes para a comparação de argumentos do benchmark (MariaRunner)."""

    def test_argumentos_compativeis_sem_criterio_retorna_true(self):
        from benchmark.runners.maria_runner import MariaRunner
        self.assertTrue(MariaRunner._argumentos_compativeis({"a": 1}, None))

    def test_argumentos_compativeis_subconjunto_correto(self):
        from benchmark.runners.maria_runner import MariaRunner
        obtidos = {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"], "descricao": "extra"}
        esperados = {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}
        self.assertTrue(MariaRunner._argumentos_compativeis(obtidos, esperados))

    def test_argumentos_incompativeis_detecta_divergencia(self):
        from benchmark.runners.maria_runner import MariaRunner
        obtidos = {"nome_arquivo": "gastos_errado", "colunas": ["Data", "Valor"]}
        esperados = {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}
        self.assertFalse(MariaRunner._argumentos_compativeis(obtidos, esperados))


class TestSystemPromptExcecaoArquivoInexistente(unittest.TestCase):
    """Testa que o SYSTEM_PROMPT distingue arquivo incerto de arquivo
    declaradamente inexistente (Fix D)."""

    def test_system_prompt_contem_excecao_para_arquivo_ficticio(self):
        self.assertIn("SEM chamar listar_arquivos", ChatSession.SYSTEM_PROMPT)


class TestReforcoComposicaoDocumento(unittest.TestCase):
    """Testa que o reforço instrui a redigir documentos sem pedir mais
    detalhes ao usuário (Fix B)."""

    def test_reforco_instrui_composicao_de_documento_sem_conteudo_literal(self):
        mensagens = _montar_mensagens_com_reforco(None, "mensagem")
        texto_system = mensagens[0]["content"]
        self.assertIn("REDIGIR um conteúdo completo", texto_system)


class TestToolChaining(unittest.TestCase):
    """Testes para o módulo compartilhado core/tool_chaining.py."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_pastas = os.environ.get("PASTAS_PERMITIDAS")
        os.environ["PASTAS_PERMITIDAS"] = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()
        if self.original_pastas:
            os.environ["PASTAS_PERMITIDAS"] = self.original_pastas
        else:
            os.environ.pop("PASTAS_PERMITIDAS", None)

    def test_encadear_leitura_stream_avanca_ate_ferramenta_de_escrita(self):
        from core.tool_chaining import encadear_leitura_stream

        class ClienteFalso:
            def continuar_com_resultado_ferramenta_stream(self, **kwargs):
                yield None, {"name": "editar_planilha", "arguments": {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}}

        resultado = list(encadear_leitura_stream(
            ClienteFalso(),
            historico_com_system=[{"role": "system", "content": "sistema"}],
            tool_call_inicial={"name": "listar_arquivos", "arguments": {}},
            tools=[],
        ))

        tool_call_final = resultado[-1][1]
        self.assertEqual(tool_call_final["name"], "editar_planilha")

    def test_encadear_leitura_stream_respeita_limite_de_passos(self):
        from core.tool_chaining import encadear_leitura_stream

        class ClienteQueSempreLista:
            def continuar_com_resultado_ferramenta_stream(self, **kwargs):
                yield None, {"name": "listar_arquivos", "arguments": {}}

        resultado = list(encadear_leitura_stream(
            ClienteQueSempreLista(),
            historico_com_system=[{"role": "system", "content": "sistema"}],
            tool_call_inicial={"name": "listar_arquivos", "arguments": {}},
            tools=[],
        ))

        tool_call_final = resultado[-1][1]
        self.assertIsNone(tool_call_final)
        textos = "".join(chunk for chunk, _ in resultado if chunk)
        self.assertIn("Não consegui concluir", textos)

    def test_encadear_leitura_stream_propaga_timeout_por_chamada(self):
        from core.tool_chaining import encadear_leitura_stream

        class ClienteFalso:
            def continuar_com_resultado_ferramenta_stream(self, **kwargs):
                yield None, {"name": "editar_planilha", "arguments": {}}

        def callback_que_estoura(duracao):
            raise TimeoutError("timeout de teste")

        with self.assertRaises(TimeoutError):
            list(encadear_leitura_stream(
                ClienteFalso(),
                historico_com_system=[{"role": "system", "content": "sistema"}],
                tool_call_inicial={"name": "listar_arquivos", "arguments": {}},
                tools=[],
                apos_cada_chamada=callback_que_estoura,
            ))


class TestMariaRunnerEncadeamento(unittest.TestCase):
    """Testa que o MariaRunner encadeia leitura -> escrita (Fix A)."""

    def test_runner_encadeia_listar_arquivos_ate_editar_planilha(self):
        from benchmark.runners.maria_runner import MariaRunner
        from benchmark.tasks.task_schema import MariaTask, MariaTaskCategory

        class ClienteFalso:
            model = "modelo-teste"

            def chat_com_tools_stream_com_metricas(self, **kwargs):
                return ("", {"name": "listar_arquivos", "arguments": {}}, 10, 5.0, 1.0)

            def continuar_com_resultado_ferramenta_stream(self, **kwargs):
                yield None, {
                    "name": "editar_planilha",
                    "arguments": {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]},
                }

        task = MariaTask(
            9001, "Teste encadeamento", "desc", "edite a planilha gastos",
            expected_tool="editar_planilha", confirm_sequence=[],
            category=MariaTaskCategory.EDITAR_PLANILHA,
        )

        runner = MariaRunner(cliente=ClienteFalso())
        resultado = runner.run(task)

        self.assertEqual(resultado.tool_detected, "editar_planilha")
        self.assertTrue(resultado.tool_correct)


if __name__ == "__main__":
    unittest.main()
