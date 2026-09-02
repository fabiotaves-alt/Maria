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
from backend.core.chat_session import ChatSession, interpretar_confirmacao
from backend.core.ollama_client import _montar_mensagens_com_reforco
from backend.core.tools_schema import (
    simular_execucao_ferramenta,
    executar_ferramenta_real,
    validar_argumentos_obrigatorios,
    FERRAMENTA_CRIAR_PLANILHA,
    FERRAMENTA_CRIAR_DOCUMENTO,
    FERRAMENTA_EDITAR_PLANILHA,
    executar_ferramenta_leitura,
    FERRAMENTAS_LEITURA,
)
from backend.core.excel_handler import criar_planilha_real, editar_planilha_real
from backend.core.file_utils import (
    gerar_nome_unico,
    garantir_pasta_arquivos,
    resolver_caminho_permitido,
    listar_arquivos,
    ler_documento,
)
from backend.core.session_storage import salvar_sessao, listar_sessoes_salvas, carregar_sessao
from backend.benchmark.analysis.language_check import resposta_em_portugues
from backend.benchmark.analysis.metrics import calculate_maria_metrics
from backend.benchmark.tasks.task_schema import MariaTaskResult
from backend.core.ollama_client import OllamaClient


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
        """Testa que o prompt exige português do Brasil em qualquer resposta."""
        self.assertIn("portugues do Brasil", ChatSession.SYSTEM_PROMPT)
    
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
        from backend.benchmark.analysis.report import _diagnosticar_falha
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
        from backend.benchmark.analysis.report import _diagnosticar_falha
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
        from backend.core.ollama_client import OllamaClient
        
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
        from backend.core.ollama_client import OllamaClient
        
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
        from backend.core.ollama_client import OllamaClient
        
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
        from backend.core.ollama_client import OllamaClient

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
        from backend.core.ollama_client import OllamaClient

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
        from backend.benchmark.runners.maria_runner import MariaRunner
        from backend.benchmark.tasks.task_schema import MariaTask
        from backend.core.ollama_client import OllamaClient, OllamaTimeoutError

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
        from backend.core.ollama_client import OllamaClient

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
        from backend.core.ollama_client import OllamaClient

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
        from backend.core.ollama_client import OllamaClient

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
        from backend.core.ollama_client import OllamaClient

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
        from backend.core.ollama_client import _montar_mensagens_com_reforco
        mensagens = _montar_mensagens_com_reforco(None, "mensagem")

        systems = [m for m in mensagens if m["role"] == "system"]
        self.assertEqual(len(systems), 1)
        self.assertIn("IMPORTANTE: Você DEVE usar as ferramentas disponíveis", systems[0]["content"])

    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_envia_uma_unica_mensagem_system(self, mock_session_class):
        from backend.core.ollama_client import OllamaClient

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
        from backend.core.ollama_client import OllamaClient

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
        from backend.core.ollama_client import OllamaClient

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
        from backend.core.ollama_client import OllamaClient, OllamaClientError
        
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
        from backend.main import MariaController
        controller = MariaController(modelo="qwen3:8b")
        controller.inicializar()
        self.assertEqual(controller.cliente.model, "qwen3:8b")

    def test_controller_usa_modelo_padrao_quando_nao_informado(self):
        from backend.main import MariaController
        from backend.core.config import LLAMA_MODEL
        controller = MariaController()
        controller.inicializar()
        self.assertEqual(controller.cliente.model, LLAMA_MODEL)


class TestAquecimentoModelo(unittest.TestCase):
    """Testes para o warmup do modelo na inicialização interativa (main.py)."""

    def test_aquecer_modelo_chama_enviar_mensagem(self):
        from backend.main import MariaController
        controller = MariaController()
        controller.inicializar()
        controller.cliente.enviar_mensagem = MagicMock(return_value="ok")

        controller.aquecer_modelo()

        controller.cliente.enviar_mensagem.assert_called_once()

    def test_aquecer_modelo_nao_propaga_excecao(self):
        from backend.main import MariaController
        from backend.core.ollama_client import OllamaClientError
        controller = MariaController()
        controller.inicializar()
        controller.cliente.enviar_mensagem = MagicMock(side_effect=OllamaClientError("falha"))

        controller.aquecer_modelo()  # não deve levantar exceção


class TestAcuraciaDeArgumentos(unittest.TestCase):
    """Testes para a comparação de argumentos do benchmark (MariaRunner)."""

    def test_argumentos_compativeis_sem_criterio_retorna_true(self):
        from backend.benchmark.runners.maria_runner import MariaRunner
        self.assertTrue(MariaRunner._argumentos_compativeis({"a": 1}, None))

    def test_argumentos_compativeis_subconjunto_correto(self):
        from backend.benchmark.runners.maria_runner import MariaRunner
        obtidos = {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"], "descricao": "extra"}
        esperados = {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}
        self.assertTrue(MariaRunner._argumentos_compativeis(obtidos, esperados))

    def test_argumentos_incompativeis_detecta_divergencia(self):
        from backend.benchmark.runners.maria_runner import MariaRunner
        obtidos = {"nome_arquivo": "gastos_errado", "colunas": ["Data", "Valor"]}
        esperados = {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}
        self.assertFalse(MariaRunner._argumentos_compativeis(obtidos, esperados))


class TestSystemPromptExcecaoArquivoInexistente(unittest.TestCase):
    """Testa que o SYSTEM_PROMPT distingue arquivo incerto de arquivo
    declaradamente inexistente (Fix D)."""

    def test_system_prompt_contem_excecao_para_arquivo_ficticio(self):
        self.assertIn("arquivo nao foi encontrado", ChatSession.SYSTEM_PROMPT)


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
        from backend.core.tool_chaining import encadear_leitura_stream

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
        from backend.core.tool_chaining import encadear_leitura_stream

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
        from backend.core.tool_chaining import encadear_leitura_stream

        class ClienteFalso:
            def continuar_com_resultado_ferramenta_stream(self, **kwargs):
                yield None, {"name": "editar_planilha", "arguments": {}}

        def callback_que_estoura(duracao, tokens):
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
        from backend.benchmark.runners.maria_runner import MariaRunner
        from backend.benchmark.tasks.task_schema import MariaTask, MariaTaskCategory

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


class TestConfiguracaoDeModeloCentralizada(unittest.TestCase):
    """Testes para a centralização de configuração de modelo (Item 1)."""

    def test_montar_payload_inclui_think_quando_habilitado(self):
        from backend.core.ollama_client import OllamaClient
        cliente = OllamaClient(model="modelo-teste")
        payload = cliente._montar_payload([{"role": "user", "content": "oi"}], tools=None, stream=False)
        self.assertIn("think", payload)

    @patch('backend.core.ollama_client.OLLAMA_ENVIAR_THINK_PARAM', False)
    def test_montar_payload_omite_think_quando_desabilitado(self):
        from backend.core.ollama_client import OllamaClient
        cliente = OllamaClient(model="modelo-teste")
        payload = cliente._montar_payload([{"role": "user", "content": "oi"}], tools=None, stream=False)
        self.assertNotIn("think", payload)

    def test_montar_payload_inclui_temperatura_apenas_quando_solicitado(self):
        from backend.core.ollama_client import OllamaClient
        cliente = OllamaClient(model="modelo-teste")
        sem_temp = cliente._montar_payload([{"role": "user", "content": "oi"}], tools=None, stream=False)
        com_temp = cliente._montar_payload(
            [{"role": "user", "content": "oi"}], tools=None, stream=False, incluir_temperatura=True
        )
        self.assertNotIn("temperature", sem_temp["options"])
        self.assertIn("temperature", com_temp["options"])

    @patch('core.ollama_client.requests.Session')
    def test_mensagem_de_erro_de_conexao_usa_model_e_base_url_dinamicos(self, mock_session_class):
        import requests as requests_module
        from backend.core.ollama_client import OllamaClient, OllamaClientError

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = requests_module.exceptions.ConnectionError()

        cliente = OllamaClient(model="outro-modelo", base_url="http://exemplo:9999")

        with self.assertRaises(OllamaClientError) as contexto:
            cliente._make_request({"model": "outro-modelo", "messages": []})

        mensagem = str(contexto.exception)
        self.assertIn("outro-modelo", mensagem)
        self.assertIn("http://exemplo:9999", mensagem)


class TestFallbackTextualDesativavel(unittest.TestCase):
    """Testa que o fallback de tool call vazada como texto respeita
    OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL (Item 3)."""

    @patch('backend.core.ollama_client.OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL', False)
    @patch('backend.core.ollama_client.requests.Session')
    def test_fallback_desativado_nao_extrai_tool_call(self, mock_session_class):
        from backend.core.ollama_client import OllamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        conteudo_vazado = '{"name": "criar_planilha", "arguments": {"nome_arquivo": "x", "colunas": ["A"]}}'
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"message": {"content": conteudo_vazado, "tool_calls": []}}
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "modelo-teste"}]}
        )

        cliente = OllamaClient(model="modelo-teste")
        _, tool_call = cliente.chat_com_tools(
            mensagem_usuario="crie uma planilha", historico=[], tools=[FERRAMENTA_CRIAR_PLANILHA]
        )

        self.assertIsNone(tool_call)


class TestOrcamentoDeTokensParaDocumento(unittest.TestCase):
    """Testa a heurística de orçamento maior de tokens para composição de
    documentos narrativos (Item A)."""

    def test_sugere_composicao_de_documento_detecta_palavras_chave(self):
        from backend.core.ollama_client import _sugere_composicao_de_documento
        self.assertTrue(_sugere_composicao_de_documento("Crie uma carta de apresentação formal"))
        self.assertTrue(_sugere_composicao_de_documento("Escreva um relatório da reunião"))
        self.assertFalse(_sugere_composicao_de_documento("Crie uma planilha de gastos"))

    @patch('core.ollama_client.requests.Session')
    def test_chat_com_tools_usa_num_predict_documento_para_carta(self, mock_session_class):
        from backend.core.ollama_client import OllamaClient
        from backend.core.config import OLLAMA_NUM_PREDICT_DOCUMENTO

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"message": {"content": "ok", "tool_calls": []}}
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "modelo-teste"}]}
        )

        cliente = OllamaClient(model="modelo-teste")
        cliente.chat_com_tools(
            mensagem_usuario="Crie uma carta de demissão formal",
            historico=[], tools=[FERRAMENTA_CRIAR_DOCUMENTO],
        )

        payload_enviado = mock_session.post.call_args.kwargs["json"]
        self.assertEqual(payload_enviado["options"]["num_predict"], OLLAMA_NUM_PREDICT_DOCUMENTO)


class TestInstrumentacaoDaContinuacao(unittest.TestCase):
    """Testa que a chamada de continuação usa orçamento reduzido de tokens
    e expõe tokens_gerados via metricas_saida (Item B)."""

    @patch('core.ollama_client.requests.Session')
    def test_continuar_usa_num_predict_continuacao(self, mock_session_class):
        from backend.core.ollama_client import OllamaClient
        from backend.core.config import OLLAMA_NUM_PREDICT_CONTINUACAO

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        linhas_stream = [
            json.dumps({"message": {"content": "ok"}, "done": True, "eval_count": 12}).encode("utf-8"),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas_stream)
        mock_session.post.return_value = mock_response
        mock_session.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "modelo-teste"}]}
        )

        cliente = OllamaClient(model="modelo-teste")
        metricas = {}
        list(cliente.continuar_com_resultado_ferramenta_stream(
            historico=[{"role": "system", "content": "sistema"}],
            tool_call={"name": "listar_arquivos", "arguments": {}},
            resultado="A pasta está vazia.",
            tools=[FERRAMENTA_EDITAR_PLANILHA],
            metricas_saida=metricas,
        ))

        payload_enviado = mock_session.post.call_args.kwargs["json"]
        self.assertEqual(payload_enviado["options"]["num_predict"], OLLAMA_NUM_PREDICT_CONTINUACAO)
        self.assertEqual(metricas["tokens_gerados"], 12)


class TestEncadeamentoPropagaTokens(unittest.TestCase):
    """Testa que core/tool_chaining.py repassa tokens_gerados da chamada de
    continuação para o callback apos_cada_chamada (Item B)."""

    def test_apos_cada_chamada_recebe_tokens_gerados(self):
        from backend.core.tool_chaining import encadear_leitura_stream

        class ClienteFalso:
            def continuar_com_resultado_ferramenta_stream(self, metricas_saida=None, **kwargs):
                if metricas_saida is not None:
                    metricas_saida["tokens_gerados"] = 42
                yield None, {"name": "editar_planilha", "arguments": {}}

        chamadas = []
        list(encadear_leitura_stream(
            ClienteFalso(),
            historico_com_system=[{"role": "system", "content": "sistema"}],
            tool_call_inicial={"name": "listar_arquivos", "arguments": {}},
            tools=[],
            apos_cada_chamada=lambda duracao, tokens: chamadas.append(tokens),
        ))

        self.assertEqual(chamadas, [42])


class TestMariaRunnerSomaTokensDaContinuacao(unittest.TestCase):
    """Testa que MariaRunner soma tokens_gerados da chamada de continuação
    ao total reportado (Item B)."""

    def test_tokens_gerados_inclui_continuacao(self):
        from backend.benchmark.runners.maria_runner import MariaRunner
        from backend.benchmark.tasks.task_schema import MariaTask, MariaTaskCategory

        class ClienteFalso:
            model = "modelo-teste"

            def chat_com_tools_stream_com_metricas(self, **kwargs):
                return ("", {"name": "listar_arquivos", "arguments": {}}, 10, 5.0, 1.0)

            def continuar_com_resultado_ferramenta_stream(self, metricas_saida=None, **kwargs):
                if metricas_saida is not None:
                    metricas_saida["tokens_gerados"] = 15
                yield None, {
                    "name": "editar_planilha",
                    "arguments": {"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]},
                }

        task = MariaTask(
            9002, "Teste soma tokens", "desc", "edite a planilha gastos",
            expected_tool="editar_planilha", confirm_sequence=[],
            category=MariaTaskCategory.EDITAR_PLANILHA,
        )

        runner = MariaRunner(cliente=ClienteFalso())
        resultado = runner.run(task)

        self.assertEqual(resultado.tokens_gerados, 25)  # 10 (inicial) + 15 (continuação)


class TestRunRepeatedComCallback(unittest.TestCase):
    """Testa que MariaRunner.run_repeated invoca o callback de progresso
    após cada execução individual (Item C)."""

    def test_apos_cada_execucao_e_chamado_para_cada_repeticao(self):
        from backend.benchmark.runners.maria_runner import MariaRunner
        from backend.benchmark.tasks.task_schema import MariaTask, MariaTaskCategory

        class ClienteFalso:
            model = "modelo-teste"

            def chat_com_tools_stream_com_metricas(self, **kwargs):
                return ("Olá!", None, 5, 10.0, 0.5)

        task = MariaTask(9003, "Teste callback", "desc", "olá", category=MariaTaskCategory.CONVERSA)
        runner = MariaRunner(cliente=ClienteFalso())

        chamadas = []
        runner.run_repeated(task, 3, apos_cada_execucao=lambda i, r: chamadas.append(i))

        self.assertEqual(chamadas, [1, 2, 3])


class TestMariaRunnerNegaEAmbiguidade(unittest.TestCase):
    """Tarefa 4: em negação ou ambiguidade, a ferramenta não é executada e
    tool_call_final passa a ser None (tool_correct=True quando
    expected_tool=None)."""

    def _falso_cliente_com_tool(self, nome_tool: str):
        class ClienteFalso:
            model = "modelo-teste"

            def chat_com_tools_stream_com_metricas(self, **kwargs):
                return ("", {"name": nome_tool, "arguments": {}}, 5, 2.0, 0.5)

        return ClienteFalso()

    def test_negacao_anula_tool_call(self):
        from backend.benchmark.runners.maria_runner import MariaRunner
        from backend.benchmark.tasks.task_schema import MariaTask, MariaTaskCategory

        task = MariaTask(
            9004, "Negação teste", "desc",
            "Crie uma planilha simples de tarefas.",
            expected_tool=None, expected_keywords=["cancelada"],
            confirm_sequence=["não"], expected_final_message="cancelada",
            category=MariaTaskCategory.CANCELAMENTO,
        )
        runner = MariaRunner(cliente=self._falso_cliente_com_tool("criar_planilha"))
        resultado = runner.run(task)

        self.assertIsNone(resultado.tool_detected)
        self.assertTrue(resultado.tool_correct)
        self.assertTrue(resultado.confirmation_completed)
        self.assertEqual(resultado.final_message, "Ação cancelada.")

    def test_ambiguidade_anula_tool_call(self):
        from backend.benchmark.runners.maria_runner import MariaRunner
        from backend.benchmark.tasks.task_schema import MariaTask, MariaTaskCategory

        task = MariaTask(
            9005, "Ambiguidade teste", "desc",
            "Crie uma planilha de projetos com Projeto e Status.",
            expected_tool=None, expected_keywords=["cancelada"],
            confirm_sequence=["talvez", "hummm"], expected_final_message="cancelada",
            category=MariaTaskCategory.AMBIGUIDADE,
        )
        runner = MariaRunner(cliente=self._falso_cliente_com_tool("criar_planilha"))
        resultado = runner.run(task)

        self.assertIsNone(resultado.tool_detected)
        self.assertTrue(resultado.tool_correct)
        self.assertTrue(resultado.confirmation_completed)
        self.assertEqual(resultado.final_message, "Ação cancelada por ambiguidade.")


class TestMariaRunnerMensagemDeErro(unittest.TestCase):
    """Tarefa 5: erro ao executar ferramenta preenche final_message
    com a mensagem do erro em vez de deixar vazia."""

    def test_value_error_edicao_inexistente_preenche_final_message(self):
        from backend.benchmark.runners.maria_runner import MariaRunner
        from backend.benchmark.tasks.task_schema import MariaTask, MariaTaskCategory

        class ClienteFalso:
            model = "modelo-teste"

            def chat_com_tools_stream_com_metricas(self, **kwargs):
                return ("", {
                    "name": "editar_planilha",
                    "arguments": {"nome_arquivo": "arquivo_ausente_a", "colunas": ["A"]},
                }, 5, 2.0, 0.5)

        task = MariaTask(
            9006, "Edição inexistente teste", "desc",
            "Edite a planilha arquivo_ausente_a com a coluna A.",
            expected_tool=None, expected_keywords=["exist"],
            confirm_sequence=["sim"], category=MariaTaskCategory.EDITAR_PLANILHA,
        )
        runner = MariaRunner(cliente=ClienteFalso())
        resultado = runner.run(task)

        self.assertFalse(resultado.runtime_ok)
        self.assertTrue(resultado.errors)
        self.assertIn("ValueError", resultado.errors[0]["kind"])
        self.assertIn("não encontrado", resultado.final_message)


# ═══════════════════════════════════════════════════════════════
# Testes do LlamaClient (llama-server / API OpenAI-compatible)
# ═══════════════════════════════════════════════════════════════

class TestLlamaClientChatTexto(unittest.TestCase):
    """Testa chat síncrono básico do LlamaClient."""

    @patch('backend.core.llama_client.requests.Session')
    def test_chat_retorna_texto(self, mock_session_class):
        from backend.core.llama_client import LlamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MagicMock(status_code=200)
        mock_session.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [{"message": {"content": "Olá!", "tool_calls": None}}],
                "usage": {"completion_tokens": 5},
            },
        )

        cliente = LlamaClient()
        texto, tool_call = cliente.chat([{"role": "user", "content": "Oi"}])

        self.assertEqual(texto, "Olá!")
        self.assertIsNone(tool_call)

    @patch('backend.core.llama_client.requests.Session')
    def test_chat_preenche_metricas(self, mock_session_class):
        from backend.core.llama_client import LlamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MagicMock(status_code=200)
        mock_session.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [{"message": {"content": "ok", "tool_calls": None}}],
                "usage": {"completion_tokens": 7},
            },
        )

        cliente = LlamaClient()
        metricas = {}
        cliente.chat([{"role": "user", "content": "teste"}], metricas_saida=metricas)

        self.assertEqual(metricas["tokens_gerados"], 7)


class TestLlamaClientToolCalling(unittest.TestCase):
    """Testa tool calling estruturado e fallback textual."""

    @patch('backend.core.llama_client.requests.Session')
    def test_tool_call_estruturada(self, mock_session_class):
        from backend.core.llama_client import LlamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MagicMock(status_code=200)
        mock_session.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [{
                    "message": {
                        "content": "",
                        "tool_calls": [{
                            "function": {
                                "name": "criar_planilha",
                                "arguments": '{"nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}',
                            }
                        }],
                    }
                }],
                "usage": {"completion_tokens": 20},
            },
        )

        cliente = LlamaClient()
        _, tool_call = cliente.chat([{"role": "user", "content": "crie planilha"}], tools=[{}])

        self.assertIsNotNone(tool_call)
        self.assertEqual(tool_call["name"], "criar_planilha")
        self.assertEqual(tool_call["arguments"]["nome_arquivo"], "gastos")

    @patch('backend.core.llama_client.requests.Session')
    def test_fallback_textual_extrai_tool_call(self, mock_session_class):
        from backend.core.llama_client import LlamaClient

        conteudo_com_tool_call = '{"name": "criar_planilha", "arguments": {"nome_arquivo": "test"}}'
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MagicMock(status_code=200)
        mock_session.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [{"message": {"content": conteudo_com_tool_call, "tool_calls": None}}],
                "usage": {"completion_tokens": 15},
            },
        )

        cliente = LlamaClient()
        _, tool_call = cliente.chat([{"role": "user", "content": "crie planilha"}], tools=[{}])

        self.assertIsNotNone(tool_call)
        self.assertEqual(tool_call["name"], "criar_planilha")


class TestLlamaClientStreaming(unittest.TestCase):
    """Testa streaming do LlamaClient."""

    @patch('backend.core.llama_client.requests.Session')
    def test_chat_stream_yields_chunks(self, mock_session_class):
        from backend.core.llama_client import LlamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MagicMock(status_code=200)

        linhas = [
            b'data: ' + json.dumps({"choices": [{"delta": {"content": "Olá"}, "finish_reason": None}]}).encode(),
            b'data: ' + json.dumps({"choices": [{"delta": {"content": " mundo"}, "finish_reason": None}]}).encode(),
            b'data: ' + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": {"completion_tokens": 2}}).encode(),
            b'data: [DONE]',
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas)
        mock_session.post.return_value = mock_response

        cliente = LlamaClient()
        chunks = list(cliente.chat_stream([{"role": "user", "content": "oi"}]))

        textos = [c for c, _ in chunks if c is not None]
        self.assertIn("Olá", textos)
        self.assertIn(" mundo", textos)
        # Último item deve ser (None, None) ou (None, tool_call)
        ultimo_chunk, ultimo_tool = chunks[-1]
        self.assertIsNone(ultimo_chunk)

    @patch('backend.core.llama_client.requests.Session')
    def test_chat_stream_metricas(self, mock_session_class):
        from backend.core.llama_client import LlamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MagicMock(status_code=200)

        linhas = [
            b'data: ' + json.dumps({"choices": [{"delta": {"content": "ok"}, "finish_reason": None}]}).encode(),
            b'data: ' + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": {"completion_tokens": 3}}).encode(),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas)
        mock_session.post.return_value = mock_response

        cliente = LlamaClient()
        metricas = {}
        list(cliente.chat_stream([{"role": "user", "content": "oi"}], metricas_saida=metricas))

        self.assertEqual(metricas["tokens_gerados"], 3)
        self.assertIn("ttft", metricas)

    @patch('backend.core.llama_client.requests.Session')
    def test_chat_com_tools_stream_com_metricas_retorna_metricas(self, mock_session_class):
        from backend.core.llama_client import LlamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MagicMock(status_code=200)

        linhas = [
            b'data: ' + json.dumps({"choices": [{"delta": {"content": "R"}, "finish_reason": None}]}).encode(),
            b'data: ' + json.dumps({"choices": [{"delta": {"content": "esposta"}, "finish_reason": None}]}).encode(),
            b'data: ' + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": {"completion_tokens": 2}}).encode(),
            b'data: [DONE]',
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas)
        mock_session.post.return_value = mock_response

        cliente = LlamaClient()
        self.assertTrue(hasattr(cliente, "chat_com_tools_stream_com_metricas"))

        texto, tool_call, tokens_gerados, tokens_por_segundo, ttft_ms = (
            cliente.chat_com_tools_stream_com_metricas(
                mensagem_usuario="olá",
                historico=[],
                tools=None,
            )
        )
        self.assertEqual(texto, "Resposta")
        self.assertIsNone(tool_call)
        self.assertGreater(tokens_gerados, 0)
        self.assertGreater(tokens_por_segundo, 0)
        self.assertIsNotNone(ttft_ms)


class TestLlamaClientErros(unittest.TestCase):
    """Testa tratamento de erros de conexão e timeout."""

    @patch('backend.core.llama_client.requests.Session')
    def test_erro_conexao_levanta_llama_client_error(self, mock_session_class):
        import requests as req
        from backend.core.llama_client import LlamaClient, LlamaClientError

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = req.exceptions.ConnectionError("offline")

        cliente = LlamaClient()
        with self.assertRaises(LlamaClientError):
            cliente.chat([{"role": "user", "content": "oi"}])

    @patch('backend.core.llama_client.requests.Session')
    def test_timeout_levanta_llama_timeout_error(self, mock_session_class):
        import requests as req
        from backend.core.llama_client import LlamaClient, LlamaTimeoutError

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MagicMock(status_code=200)
        mock_session.post.side_effect = req.exceptions.Timeout("timeout")

        cliente = LlamaClient()
        with self.assertRaises(LlamaTimeoutError):
            cliente.chat([{"role": "user", "content": "oi"}])


class TestLlamaClientCompatibilidade(unittest.TestCase):
    """Testa métodos de compatibilidade com OllamaClient."""

    @patch('backend.core.llama_client.requests.Session')
    def test_chat_com_tools_stream_compativel(self, mock_session_class):
        from backend.core.llama_client import LlamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MagicMock(status_code=200)

        linhas = [
            b'data: ' + json.dumps({"choices": [{"delta": {"content": "Resposta"}, "finish_reason": None}]}).encode(),
            b'data: ' + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}]}).encode(),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas)
        mock_session.post.return_value = mock_response

        cliente = LlamaClient()
        chunks = list(cliente.chat_com_tools_stream(
            mensagem_usuario="olá",
            historico=[],
            tools=None,
        ))
        textos = [c for c, _ in chunks if c is not None]
        self.assertIn("Resposta", textos)

    @patch('backend.core.llama_client.requests.Session')
    def test_continuar_com_resultado_ferramenta_stream(self, mock_session_class):
        from backend.core.llama_client import LlamaClient

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MagicMock(status_code=200)

        linhas = [
            b'data: ' + json.dumps({"choices": [{"delta": {"content": "Feito"}, "finish_reason": None}]}).encode(),
            b'data: ' + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}]}).encode(),
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = iter(linhas)
        mock_session.post.return_value = mock_response

        cliente = LlamaClient()
        metricas = {}
        chunks = list(cliente.continuar_com_resultado_ferramenta_stream(
            historico=[{"role": "system", "content": "sistema"}],
            tool_call={"name": "listar_arquivos", "arguments": {}},
            resultado="pasta vazia",
            tools=None,
            metricas_saida=metricas,
        ))
        textos = [c for c, _ in chunks if c is not None]
        self.assertIn("Feito", textos)
        # Verifica que o payload inclui mensagem role=tool
        payload_enviado = mock_session.post.call_args.kwargs["json"]
        mensagens = payload_enviado["messages"]
        roles = [m["role"] for m in mensagens]
        self.assertIn("tool", roles)

        # Verifica formato correto de tool calling (id, type e tool_call_id)
        msg_assistant = next(m for m in mensagens if m["role"] == "assistant")
        tool_call_payload = msg_assistant["tool_calls"][0]
        self.assertIn("id", tool_call_payload)
        self.assertTrue(tool_call_payload["id"])
        self.assertEqual(tool_call_payload["type"], "function")
        self.assertEqual(
            tool_call_payload["function"]["name"], "listar_arquivos"
        )
        self.assertEqual(
            tool_call_payload["function"]["arguments"],
            json.dumps({}, ensure_ascii=False),
        )
        msg_tool = next(m for m in mensagens if m["role"] == "tool")
        self.assertEqual(msg_tool["tool_call_id"], tool_call_payload["id"])


class TestSegurancaComandosBridge(unittest.TestCase):
    """Testes de segurança para upload_arquivo e transcrever_audio (P0)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_fora = tempfile.TemporaryDirectory()
        self.original_pastas = os.environ.get("PASTAS_PERMITIDAS")
        os.environ["PASTAS_PERMITIDAS"] = self.temp_dir.name
        self.pasta_gerados = os.path.join(self.temp_dir.name, "arquivos_gerados")
        self.original_gerados = os.environ.get("PASTA_ARQUIVOS_GERADOS")
        os.environ["PASTA_ARQUIVOS_GERADOS"] = self.pasta_gerados

    def tearDown(self):
        self.temp_dir.cleanup()
        self.temp_fora.cleanup()
        if self.original_pastas:
            os.environ["PASTAS_PERMITIDAS"] = self.original_pastas
        else:
            os.environ.pop("PASTAS_PERMITIDAS", None)
        if self.original_gerados:
            os.environ["PASTA_ARQUIVOS_GERADOS"] = self.original_gerados
        else:
            os.environ.pop("PASTA_ARQUIVOS_GERADOS", None)
        os.environ.pop("WHISPER_BIN", None)

    def _despachar(self, comando, payload):
        from backend.main import _despachar_comando
        return _despachar_comando(None, comando, payload)

    def test_upload_rejeita_diretorio(self):
        """upload_arquivo deve rejeitar pastas (apenas arquivos)."""
        status, dados, erro = self._despachar(
            "upload_arquivo", {"caminho": self.temp_fora.name}
        )
        self.assertEqual(status, "erro")
        self.assertIn("inválido", erro)

    def test_upload_arquivo_valido_copia_para_pasta_gerenciada(self):
        """upload_arquivo copia um arquivo válido para a pasta permitida."""
        origem = os.path.join(self.temp_fora.name, "doc.txt")
        with open(origem, "w", encoding="utf-8") as f:
            f.write("conteúdo")

        status, dados, erro = self._despachar("upload_arquivo", {"caminho": origem})

        self.assertEqual(status, "ok", erro)
        self.assertTrue(
            os.path.isfile(os.path.join(self.pasta_gerados, "doc.txt")),
            f"Arquivo deveria estar em {self.pasta_gerados}: {dados}",
        )

    def test_transcrever_audio_rejeita_caminho_fora_das_pastas_permitidas(self):
        """transcrever_audio não pode ler/deletar arquivos fora das pastas
        permitidas (corrige deleção arbitrária via unlink)."""
        audio_fora = os.path.join(self.temp_fora.name, "audio.wav")
        with open(audio_fora, "wb") as f:
            f.write(b"RIFF....")

        status, dados, erro = self._despachar(
            "transcrever_audio", {"caminho": audio_fora}
        )

        self.assertEqual(status, "erro")
        # O arquivo fora da pasta permitida NÃO pode ser deletado
        self.assertTrue(os.path.exists(audio_fora))

    def test_transcrever_audio_rejeita_whisper_bin_invalido(self):
        """WHISPER_BIN com caminho/espaços deve ser rejeitado (evita
        execução de binário arbitrário)."""
        audio = os.path.join(self.temp_dir.name, "audio.wav")
        with open(audio, "wb") as f:
            f.write(b"RIFF....")
        os.environ["WHISPER_BIN"] = "C:/evil/dir/whisper-main.exe"

        status, dados, erro = self._despachar(
            "transcrever_audio", {"caminho": audio}
        )

        self.assertEqual(status, "erro")
        self.assertIn("WHISPER_BIN", erro)


class TestSegurancaApiHttp(unittest.TestCase):
    """Testes de autenticação da API bridge HTTP (P1)."""

    def setUp(self):
        from backend.main import _criar_app_http, _carregar_token_api
        self.token = _carregar_token_api()
        self.app = _criar_app_http(None, self.token)
        self.client = self.app.test_client()

    def test_chat_sem_token_rejeitado(self):
        resp = self.client.post("/chat", json={"id": "1", "comando": "status", "dados": {}})
        self.assertEqual(resp.status_code, 401)

    def test_chat_token_invalido_rejeitado(self):
        resp = self.client.post(
            "/chat",
            json={"id": "1", "comando": "status", "dados": {}},
            headers={"Authorization": "Bearer token-falso"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_ping_fica_aberto_para_health_check(self):
        resp = self.client.get("/ping")
        self.assertEqual(resp.status_code, 200)

    def test_cors_origem_maliciosa_nao_autorizada(self):
        resp = self.client.options(
            "/chat",
            headers={
                "Origin": "https://site-malicioso.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertNotEqual(
            resp.headers.get("Access-Control-Allow-Origin", ""), "*"
        )

    def test_cors_origem_tauri_autorizada(self):
        resp = self.client.options(
            "/chat",
            headers={
                "Origin": "http://tauri.localhost",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        self.assertEqual(
            resp.headers.get("Access-Control-Allow-Origin"), "http://tauri.localhost"
        )


def _fts5_disponivel() -> bool:
    """Verifica em tempo de execução se o SQLite local suporta FTS5."""
    import sqlite3
    try:
        conexao_teste = sqlite3.connect(":memory:")
        conexao_teste.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        conexao_teste.close()
        return True
    except sqlite3.OperationalError:
        return False


class TestManualRedacaoIngestao(unittest.TestCase):
    """Testes para o parser/chunker do Manual de Redação (ingest_manual_redacao.py)."""

    def test_extrair_chunks_classifica_secao_oficio(self):
        from backend.database.ingest_manual_redacao import extrair_chunks
        texto = (
            "#### **5 O padrão ofício**\n"
            "Texto introdutório do padrão ofício.\n"
            "##### 5.1.7 Fechos para comunicações\n"
            "Conteúdo bastante longo sobre os fechos oficiais utilizados em comunicações formais do governo federal.\n"
            "##### 5.1.8 Identificação do signatário\n"
            "Conteúdo sobre como identificar corretamente o signatário do documento oficial em questão.\n"
        )
        chunks = extrair_chunks(texto)
        secoes = {c["secao"]: c["tipo_documento"] for c in chunks}
        self.assertIn("5.1.7 Fechos para comunicações", secoes)
        self.assertEqual(secoes["5.1.7 Fechos para comunicações"], "oficio")

    def test_extrair_chunks_descarta_secoes_vazias(self):
        from backend.database.ingest_manual_redacao import extrair_chunks
        texto = "# **Capítulo I**\n\n#### **1 Panorama**\num\n"
        chunks = extrair_chunks(texto)
        self.assertEqual(chunks, [])

    def test_classificar_tipo_documento_mapeia_exposicao_e_mensagem(self):
        from backend.database.ingest_manual_redacao import _classificar_tipo_documento
        self.assertEqual(_classificar_tipo_documento("6.2.1 Definição e finalidade"), "exposicao_motivos")
        self.assertEqual(_classificar_tipo_documento("6.3.2 Forma e estrutura"), "mensagem")
        self.assertEqual(_classificar_tipo_documento("6.4.1 Definição e finalidade"), "email")
        self.assertEqual(_classificar_tipo_documento("Prefácio"), "geral")


@unittest.skipUnless(_fts5_disponivel(), "SQLite local sem suporte a FTS5")
class TestManualRedacaoConsulta(unittest.TestCase):
    """Testes para o módulo de consulta RAG (core/manual_redacao.py)."""

    def setUp(self):
        import backend.database.connection as connection_module
        connection_module._CONNECTION = None
        self.temp_dir = tempfile.TemporaryDirectory()
        connection_module.init_db(f"{self.temp_dir.name}/teste_manual.db")
        from backend.database.schema import init_db
        init_db()
        conn = connection_module.get_connection()
        conn.executemany(
            "INSERT INTO manual_redacao_fts (tipo_documento, secao, conteudo) VALUES (?, ?, ?)",
            [
                ("oficio", "5.1.7 Fechos para comunicações",
                 "O fecho das comunicações oficiais objetiva saudar o destinatário com respeitosamente ou atenciosamente."),
                ("oficio", "4.4 Vocativo",
                 "O vocativo a ser empregado em comunicações dirigidas aos chefes de poder é Senhor mais o cargo."),
                ("mensagem", "6.3.2 Forma e estrutura",
                 "A mensagem não obedece a um único e rígido modelo, mas apresenta a mesma estrutura do padrão ofício."),
            ],
        )
        conn.commit()

    def tearDown(self):
        import backend.database.connection as connection_module
        connection_module.close_connection()
        connection_module._DB_PATH = None  # evita que _DB_PATH aponte para o temp_dir já removido
        self.temp_dir.cleanup()

    def test_consulta_com_tipo_e_termo_busca(self):
        from backend.core.manual_redacao import consultar_manual
        resultado = consultar_manual(tipo_documento="oficio", termo_busca="vocativo")
        self.assertIn("Vocativo", resultado)
        self.assertNotIn("6.3.2", resultado)

    def test_consulta_sem_termo_busca_filtra_apenas_por_tipo(self):
        from backend.core.manual_redacao import consultar_manual
        resultado = consultar_manual(tipo_documento="mensagem")
        self.assertIn("6.3.2 Forma e estrutura", resultado)

    def test_consulta_sem_resultados_retorna_mensagem_amigavel(self):
        from backend.core.manual_redacao import consultar_manual
        resultado = consultar_manual(tipo_documento="email", termo_busca="anexo")
        self.assertIn("Nenhum trecho", resultado)

    def test_consulta_tipo_invalido_e_ignorado_sem_erro(self):
        from backend.core.manual_redacao import consultar_manual
        resultado = consultar_manual(tipo_documento="tipo_que_nao_existe", termo_busca="fecho")
        self.assertIn("Fechos", resultado)

    def test_consulta_trunca_trechos_muito_longos(self):
        """Cobre a correção da Tarefa 3: trechos maiores que
        MANUAL_REDACAO_MAX_CHARS_POR_TRECHO devem ser truncados com
        marcador '[...]' para não estourar o contexto do modelo."""
        from backend.core.manual_redacao import consultar_manual
        import backend.database.connection as connection_module

        conn = connection_module.get_connection()
        conteudo_longo = "palavra " * 500  # muito acima do limite padrão (800 caracteres)
        conn.execute(
            "INSERT INTO manual_redacao_fts (tipo_documento, secao, conteudo) VALUES (?, ?, ?)",
            ("geral", "99.9 Seção de teste longa", conteudo_longo),
        )
        conn.commit()

        resultado = consultar_manual(tipo_documento="geral", termo_busca="palavra")
        self.assertIn("[...]", resultado)


class TestFerramentaConsultarManualRedacao(unittest.TestCase):
    """Testes para a integração da ferramenta em tools_schema.py."""

    def test_consultar_manual_redacao_esta_em_ferramentas_leitura(self):
        self.assertIn("consultar_manual_redacao", FERRAMENTAS_LEITURA)

    def test_ferramenta_criar_documento_nao_menciona_memorandos(self):
        """Cobre a correção de consistência da Tarefa 4.5: 'memorando' foi
        unificado sob 'ofício' no Manual, então criar_documento não deve
        mais listá-lo como exemplo de uso direto."""
        descricao = FERRAMENTA_CRIAR_DOCUMENTO["function"]["description"]
        self.assertNotIn("memorandos", descricao)

    def test_executar_ferramenta_leitura_ferramenta_desconhecida_ainda_falha(self):
        with self.assertRaises(ValueError):
            executar_ferramenta_leitura("ferramenta_inexistente", {})

class TestObterMetadadosModelo(unittest.TestCase):
    """Testa a extração de metadados do llama-server via /v1/models (mock, sem servidor)."""

    def test_obter_metadados_resposta_valida(self):
        from backend.benchmark.run_benchmark import _obter_metadados_modelo
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {
            "data": [{
                "id": "C:\\blob\\sha256-2bada8a",
                "meta": {"n_params": 3397103616, "n_vocab": 151936,
                         "n_ctx": 8192, "n_ctx_train": 131072,
                         "size": 2098976768, "ftype": 14},
            }]
        }
        with patch("backend.benchmark.run_benchmark._requests.get", return_value=mock_response):
            m = _obter_metadados_modelo()
        self.assertIsNotNone(m)
        self.assertEqual(m["quantizacao"], "Q4_K_M")
        self.assertEqual(m["rotulo_tamanho"], "Qwen2.5 3B")
        self.assertEqual(m["id_exibicao"], "Qwen2.5 3B")

    def test_obter_metadados_servidor_offline(self):
        import requests as req
        from backend.benchmark.run_benchmark import _obter_metadados_modelo

        with patch("backend.benchmark.run_benchmark._requests.get",
                   side_effect=req.exceptions.ConnectionError()):
            self.assertIsNone(_obter_metadados_modelo())

    def test_obter_metadados_status_500(self):
        from backend.benchmark.run_benchmark import _obter_metadados_modelo

        mock_response = MagicMock(status_code=500)
        with patch("backend.benchmark.run_benchmark._requests.get", return_value=mock_response):
            self.assertIsNone(_obter_metadados_modelo())


class TestDerivarRotuloModelo(unittest.TestCase):
    """Testa a derivação de rótulo legível a partir de n_params e n_vocab."""

    def test_qwen25_3b(self):
        from backend.benchmark.run_benchmark import _derivar_rotulo_modelo
        self.assertEqual(_derivar_rotulo_modelo(3397103616, 151936), "Qwen2.5 3B")

    def test_qwen25_7b(self):
        from backend.benchmark.run_benchmark import _derivar_rotulo_modelo
        self.assertEqual(_derivar_rotulo_modelo(7615616512, 151936), "Qwen2.5 7B")

    def test_qwen25_14b(self):
        from backend.benchmark.run_benchmark import _derivar_rotulo_modelo
        self.assertEqual(_derivar_rotulo_modelo(14771111936, 151936), "Qwen2.5 14B")

    def test_vocab_desconhecido(self):
        from backend.benchmark.run_benchmark import _derivar_rotulo_modelo
        self.assertEqual(_derivar_rotulo_modelo(3397103616, 99999), "3B")

    def test_sem_params(self):
        from backend.benchmark.run_benchmark import _derivar_rotulo_modelo
        self.assertEqual(_derivar_rotulo_modelo(0, 151936), "")


class TestPareceCaminhoLocal(unittest.TestCase):
    """Testa a detecção de caminhos locais/blobs."""

    def test_blob_ollama(self):
        from backend.benchmark.run_benchmark import _parece_caminho_local
        self.assertTrue(_parece_caminho_local("C:\\blob\\sha256-2bada8a"))

    def test_hash_puro(self):
        from backend.benchmark.run_benchmark import _parece_caminho_local
        self.assertTrue(_parece_caminho_local("2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730"))

    def test_gguf(self):
        from backend.benchmark.run_benchmark import _parece_caminho_local
        self.assertTrue(_parece_caminho_local("models/qwen2.gguf"))

    def test_nome_simples(self):
        from backend.benchmark.run_benchmark import _parece_caminho_local
        self.assertFalse(_parece_caminho_local("qwen2.5-omni-3b"))

    def test_vazio(self):
        from backend.benchmark.run_benchmark import _parece_caminho_local
        self.assertFalse(_parece_caminho_local(""))
        self.assertFalse(_parece_caminho_local(None))


class TestAlertaNaoDisparaParaBlob(unittest.TestCase):
    """Testa que o alerta de divergência NÃO dispara quando o id é blob
    do mesmo modelo configurado."""

    def test_sem_alerta_para_blob_mesmo_modelo(self):
        import io
        from contextlib import redirect_stdout
        from backend.benchmark.run_benchmark import _warmup_model

        metadados = {
            "id": "C:\\blob\\sha256-2bada8a",
            "id_exibicao": "Qwen2.5 3B",
            "rotulo_tamanho": "Qwen2.5 3B",
        }

        class FakeClient:
            def enviar_mensagem(self, *a, **kw):
                return "ok"

        buf = io.StringIO()
        with patch("backend.benchmark.run_benchmark._obter_metadados_modelo", return_value=metadados), \
             patch("backend.benchmark.run_benchmark.OllamaClient", return_value=FakeClient()):
            with redirect_stdout(buf):
                modelo, meta = _warmup_model()

        # "3b" está contido em "qwen2.5-omni-3b" -> NÃO deve gerar alerta
        self.assertNotIn("[AVISO]", buf.getvalue())


class TestAvisoNctx(unittest.TestCase):
    """Testa o aviso de n_ctx quando config > servidor."""

    def test_relatorio_contem_aviso_nctx(self):
        import tempfile
        from unittest.mock import patch as _patch
        from backend.benchmark.analysis.report import generate_report
        from backend.benchmark.tasks.task_schema import MariaTaskResult

        results = [
            MariaTaskResult(
                task_id=1, task_name="T1", category="conversa", model="m",
                tool_detected=None, tool_correct=True, confirmation_completed=True,
                keyword_match=True, runtime_ok=True, final_message="ok",
                latency_ms=100.0, errors=[], raw_tool_args={},
            ),
        ]

        metadados = {
            "id": "modelo.gguf", "id_exibicao": "modelo.gguf",
            "n_ctx": 4096, "n_ctx_train": 131072,
            "quantizacao": "Q4_K_M", "n_params": 3397103616,
            "tamanho_legivel": "1.95 GiB",
        }

        with _patch("backend.benchmark.analysis.report.LLAMA_NUM_CTX", 8192):
            with tempfile.TemporaryDirectory() as tmpdir:
                generate_report(
                    results,
                    MagicMock(
                        total_tasks=1, tool_accuracy=1.0, confirmation_success_rate=1.0,
                        keyword_match_rate=1.0, runtime_success_rate=1.0,
                        language_compliance_rate=1.0, args_accuracy=1.0,
                        avg_tokens_por_segundo=0.0, avg_ttft_ms=None,
                        p50_latency_ms=100.0, p90_latency_ms=100.0,
                        avg_latency_ms=100.0, error_distribution={}, by_category={},
                    ),
                    tmpdir,
                    modelo_configurado="qwen2.5-omni-3b",
                    modelo_carregado="modelo.gguf",
                    metadados_modelo=metadados,
                )
                with open(os.path.join(tmpdir, "report.md"), encoding="utf-8") as f:
                    report = f.read()

        self.assertIn("4096", report)
        self.assertIn("n_ctx", report)


class TestFtypeParaNome(unittest.TestCase):
    """Testa a conversão de ftype (enum GGML) para nome legível."""

    def test_q4_k_m(self):
        from backend.benchmark.run_benchmark import _ftype_para_nome
        self.assertEqual(_ftype_para_nome(14), "Q4_K_M")

    def test_string_passa_direto(self):
        from backend.benchmark.run_benchmark import _ftype_para_nome
        self.assertEqual(_ftype_para_nome("Q8_0"), "Q8_0")

    def test_none(self):
        from backend.benchmark.run_benchmark import _ftype_para_nome
        self.assertEqual(_ftype_para_nome(None), "")


class TestSamplerParamsBenchmark(unittest.TestCase):
    """Testa os parâmetros de sampler configuráveis e sua exposição no benchmark."""

    def test_config_defaults_dos_sampler_params(self):
        from backend.core.config import (
            LLAMA_DRY_ALLOWED_LENGTH, LLAMA_DRY_BASE, LLAMA_DRY_MULTIPLIER,
            LLAMA_DRY_PENALTY_LAST_N, LLAMA_FREQUENCY_PENALTY, LLAMA_MIN_P,
            LLAMA_PRESENCE_PENALTY, LLAMA_REPEAT_LAST_N, LLAMA_REPEAT_PENALTY,
            LLAMA_TOP_K, LLAMA_TOP_N_SIGMA, LLAMA_TOP_P, LLAMA_TYPICAL_P,
            LLAMA_XTC_PROBABILITY, LLAMA_XTC_THRESHOLD,
        )
        self.assertEqual(LLAMA_REPEAT_LAST_N, 64)
        self.assertEqual(LLAMA_REPEAT_PENALTY, 1.0)
        self.assertEqual(LLAMA_FREQUENCY_PENALTY, 0.0)
        self.assertEqual(LLAMA_PRESENCE_PENALTY, 0.0)
        self.assertEqual(LLAMA_DRY_MULTIPLIER, 0.0)
        self.assertEqual(LLAMA_DRY_BASE, 1.75)
        self.assertEqual(LLAMA_DRY_ALLOWED_LENGTH, 2)
        self.assertEqual(LLAMA_DRY_PENALTY_LAST_N, 64)
        self.assertEqual(LLAMA_TOP_K, 40)
        self.assertEqual(LLAMA_TOP_P, 0.95)
        self.assertEqual(LLAMA_MIN_P, 0.05)
        self.assertEqual(LLAMA_XTC_PROBABILITY, 0.0)
        self.assertEqual(LLAMA_XTC_THRESHOLD, 0.1)
        self.assertEqual(LLAMA_TYPICAL_P, 1.0)
        self.assertEqual(LLAMA_TOP_N_SIGMA, -1.0)

    def test_montar_sampler_params_contem_todos_os_campos(self):
        from backend.core.llama_client import montar_sampler_params
        params = montar_sampler_params()
        esperados = {
            "temperature", "repeat_last_n", "repeat_penalty",
            "frequency_penalty", "presence_penalty", "dry_multiplier",
            "dry_base", "dry_allowed_length", "dry_penalty_last_n",
            "top_k", "top_p", "min_p", "xtc_probability",
            "xtc_threshold", "typical_p", "top_n_sigma",
        }
        self.assertEqual(set(params), esperados)
        self.assertEqual(params["top_k"], 40)
        self.assertEqual(params["top_p"], 0.95)
        self.assertEqual(params["temperature"], 0.1)

    def test_montar_payload_inclui_sampler_params_com_tools(self):
        from backend.core.llama_client import LlamaClient
        cliente = LlamaClient(model="modelo-teste")
        payload = cliente._montar_payload(
            [{"role": "user", "content": "oi"}], tools=[{}], stream=False,
            incluir_temperatura=True,
        )
        for chave in ("temperature", "top_k", "top_p", "min_p",
                      "repeat_last_n", "repeat_penalty", "dry_base",
                      "xtc_probability", "typical_p", "top_n_sigma"):
            self.assertIn(chave, payload)
        self.assertEqual(payload["top_k"], 40)
        self.assertEqual(payload["temperature"], 0.1)

    def test_montar_payload_omite_sampler_sem_tools(self):
        from backend.core.llama_client import LlamaClient
        cliente = LlamaClient(model="modelo-teste")
        payload = cliente._montar_payload(
            [{"role": "user", "content": "oi"}], tools=None, stream=False,
        )
        self.assertNotIn("top_k", payload)
        self.assertNotIn("temperature", payload)

    def test_maria_task_result_campos_novos_com_default(self):
        from backend.benchmark.tasks.task_schema import MariaTaskResult
        result = MariaTaskResult(
            task_id=1, task_name="T", category="conversa", model="m",
            tool_detected=None, tool_correct=True, confirmation_completed=True,
            keyword_match=True, runtime_ok=True, final_message="ok",
            latency_ms=100.0, errors=[], raw_tool_args={},
        )
        self.assertEqual(result.prompt_enviado, [])
        self.assertEqual(result.resposta_bruta_modelo, "")
        self.assertEqual(result.sampler_params, {})

    def test_runner_preenche_prompt_e_resposta_bruta(self):
        from backend.benchmark.runners.maria_runner import MariaRunner
        from backend.benchmark.tasks.task_schema import MariaTask, MariaTaskCategory

        class ClienteFalso:
            model = "modelo-teste"

            def chat_com_tools_stream_com_metricas(self, **kwargs):
                return (
                    "Vou criar a planilha.",
                    {"name": "criar_planilha", "arguments": {
                        "nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}},
                    8, 5.0, 1.0,
                )

        task = MariaTask(
            9101, "Prompt/resposta", "desc", "Crie uma planilha de gastos.",
            expected_tool="criar_planilha", confirm_sequence=["sim"],
            category=MariaTaskCategory.CRIAR_PLANILHA,
        )
        runner = MariaRunner(cliente=ClienteFalso())
        resultado = runner.run(task)

        # Prompt enviado contém system (reforço) e a mensagem do usuário.
        self.assertTrue(any(m["role"] == "system" for m in resultado.prompt_enviado))
        self.assertEqual(resultado.prompt_enviado[-1]["role"], "user")
        self.assertIn("Crie uma planilha de gastos.", resultado.prompt_enviado[-1]["content"])
        # Resposta bruta preserva o que o modelo gerou ANTES da confirmação.
        self.assertEqual(resultado.resposta_bruta_modelo, "Vou criar a planilha.")
        self.assertNotEqual(resultado.final_message, resultado.resposta_bruta_modelo)
        self.assertTrue(resultado.sampler_params)
        self.assertIn("top_k", resultado.sampler_params)

    def test_report_contem_parametros_e_detalhes_por_execucao(self):
        import tempfile
        from unittest.mock import MagicMock
        from backend.benchmark.analysis.report import generate_report
        from backend.core.llama_client import montar_sampler_params
        from backend.benchmark.tasks.task_schema import MariaTaskResult

        results = [
            MariaTaskResult(
                task_id=3, task_name="Planilha básica", category="criar_planilha",
                model="m", tool_detected="criar_planilha", tool_correct=True,
                confirmation_completed=True, keyword_match=True, runtime_ok=True,
                final_message="Planilha criada com sucesso: ...",
                latency_ms=100.0, errors=[], raw_tool_args={},
                prompt_enviado=[
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": "Crie uma planilha de gastos"},
                ],
                resposta_bruta_modelo="Vou criar a planilha.",
                sampler_params=montar_sampler_params(),
            ),
        ]
        metrics = MagicMock(
            total_tasks=1, tool_accuracy=1.0, confirmation_success_rate=1.0,
            keyword_match_rate=1.0, runtime_success_rate=1.0,
            language_compliance_rate=1.0, args_accuracy=1.0,
            avg_tokens_por_segundo=0.0, avg_ttft_ms=None,
            p50_latency_ms=100.0, p90_latency_ms=100.0,
            avg_latency_ms=100.0, error_distribution={}, by_category={},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_report(
                results, metrics, tmpdir, sampler_params=montar_sampler_params(),
            )
            with open(os.path.join(tmpdir, "report.md"), encoding="utf-8") as f:
                report = f.read()

        self.assertIn("## Parâmetros do sampler", report)
        self.assertIn("| top_k | 40 |", report)
        self.assertIn("| temperature | 0.100 |", report)
        self.assertIn("## Detalhes por execução", report)
        self.assertIn("Crie uma planilha de gastos", report)
        self.assertIn("Vou criar a planilha.", report)


if __name__ == "__main__":
    unittest.main()
