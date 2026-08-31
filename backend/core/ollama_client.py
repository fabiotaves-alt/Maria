"""
Módulo cliente para comunicação com a API local do Ollama.
Responsável por enviar mensagens ao modelo Qwen3.5-4B e receber respostas.

Requisitos:
- Comunicação apenas via localhost (sem dependência de internet)
- Tratamento de erros claro para o usuário
- Suporte opcional a streaming
"""

import logging
import re
import time
import requests
import json
from collections.abc import Generator
from backend.core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_NUM_CTX,
    OLLAMA_NUM_PREDICT,
    OLLAMA_NUM_THREAD,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_ENVIAR_THINK_PARAM,
    OLLAMA_THINK_HABILITADO,
    OLLAMA_TEMPERATURE_TOOLS,
    OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL,
    OLLAMA_NUM_PREDICT_DOCUMENTO,
    OLLAMA_NUM_PREDICT_CONTINUACAO,
)


# Configurar logger do módulo
logger = logging.getLogger(__name__)


class OllamaClientError(Exception):
    """Exceção personalizada para erros do cliente Ollama."""
    pass


class OllamaTimeoutError(OllamaClientError):
    """Indica que uma requisição excedeu o timeout configurado."""
    pass


def _tentar_extrair_tool_call_textual(conteudo: str) -> dict | None:
    """
    Fallback: alguns modelos, em vez de preencher o campo estruturado
    'tool_calls' da API do Ollama, vazam a chamada de ferramenta como
    texto no campo 'content', geralmente terminando com a tag literal
    '</tool_call>'. Esta função tenta detectar e extrair esse padrão.

    Args:
        conteudo: texto acumulado de 'content' de uma resposta (streaming
            ou não).

    Returns:
        {"name": str, "arguments": dict} se um padrão válido de tool call
        for encontrado no texto, None caso contrário.
    """
    if '"name"' not in conteudo or '"arguments"' not in conteudo:
        return None

    match = re.search(r'\{.*"name"\s*:\s*"[^"]+".*"arguments"\s*:\s*\{.*?\}\s*\}', conteudo, re.DOTALL)
    if not match:
        return None

    try:
        dados = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    nome = dados.get("name")
    argumentos = dados.get("arguments", {})
    if not isinstance(nome, str) or not nome:
        return None
    if not isinstance(argumentos, dict):
        return None

    return {"name": nome, "arguments": argumentos}


_PALAVRAS_COMPOSICAO_DOCUMENTO = {
    "carta", "relatório", "relatorio", "ata", "comunicado", "memorando", "memorial",
}


def _sugere_composicao_de_documento(mensagem_usuario: str) -> bool:
    """Heurística simples: retorna True se a mensagem do usuário sugere a
    composição de um documento narrativo (carta, relatório, ata, comunicado),
    caso em que um orçamento maior de tokens (OLLAMA_NUM_PREDICT_DOCUMENTO)
    é aplicado em vez do padrão, já que o modelo precisa redigir o texto
    inteiro antes de emitir a tool call."""
    texto = mensagem_usuario.lower()
    return any(palavra in texto for palavra in _PALAVRAS_COMPOSICAO_DOCUMENTO)


def _montar_mensagens_com_reforco(historico: list[dict] | None, mensagem_usuario: str) -> list[dict]:
    """
    Monta a lista de mensagens para o Ollama garantindo uma ÚNICA mensagem
    role="system" no payload.

    Se `historico` já começar com uma mensagem system (ex.: injetada por
    ChatSession.get_historico_com_system()), o reforço de uso de ferramentas
    é mesclado ao final dela. Caso contrário, cria uma nova mensagem system
    só com o reforço. Isso evita mandar duas mensagens system consecutivas
    ao Ollama — comportamento que, com Qwen3.5, gera tool calls com
    argumentos incompletos (ex.: 'nome_arquivo' ausente em criar_documento).

    Não muta `historico` nem os dicts originais (retorna uma lista nova).
    """
    # Reforço específico e direto para tool calling
    reforco = """IMPORTANTE: Você DEVE usar as ferramentas disponíveis quando o usuário pedir para:
- Criar planilhas: use SEMPRE a ferramenta "criar_planilha"
- Criar documentos Word: use SEMPRE a ferramenta "criar_documento"  
- Editar planilhas existentes: use SEMPRE a ferramenta "editar_planilha"

Não responda apenas com texto - chame a ferramenta apropriada preenchendo TODOS os campos obrigatórios.

Se o usuário pedir um documento narrativo (carta, relatório, ata, comunicado) SEM fornecer o texto pronto, você mesmo deve REDIGIR um conteúdo completo e coerente com base no que foi pedido e chamar "criar_documento" imediatamente. NUNCA responda apenas com perguntas pedindo mais detalhes antes de tentar compor o documento - use um conteúdo razoável e genérico quando faltar informação específica. Mantenha o conteúdo OBJETIVO: no máximo 3 a 5 parágrafos curtos, sem repetições ou seções desnecessárias.

Se o usuário pedir um documento oficial (ofício, aviso, memorando, exposição de motivos, mensagem ao Congresso, e-mail institucional), chame "consultar_manual_redacao" com o tipo_documento apropriado ANTES de chamar "criar_documento", e preencha "tipo_documento_oficial" no criar_documento.

Responda sempre em português do Brasil."""

    mensagens = list(historico or [])

    if mensagens and mensagens[0].get("role") == "system":
        # Mesclar reforço ao system prompt existente
        mensagens[0] = {
            "role": "system",
            "content": mensagens[0]["content"].rstrip() + "\n\n" + reforco,
        }
    else:
        # Criar novo system prompt apenas com o reforço
        mensagens.insert(0, {"role": "system", "content": reforco})

    mensagens.append({"role": "user", "content": mensagem_usuario})
    return mensagens


class OllamaClient:
    """
    Cliente para comunicação com a API do Ollama rodando localmente.

    Atributos:
        base_url (str): URL base da API do Ollama
        model (str): Nome do modelo a ser usado
        timeout (int): Timeout em segundos para as requisições
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout: int = OLLAMA_TIMEOUT,
        num_predict: int | None = None,
    ):
        """
        Inicializa o cliente Ollama.

        Args:
            base_url: URL da API do Ollama (padrão: localhost:11434)
            model: Nome do modelo a usar (padrão: qwen3.5:4b)
            timeout: Timeout para requisições em segundos (padrão: 120)
            num_predict: Override do número de tokens previstos pelo modelo.
                Quando None, usa OLLAMA_NUM_PREDICT da configuração.
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.num_predict = num_predict
        self._session = requests.Session()
        self._connection_checked = False

    def _check_connection(self) -> bool:
        """
        Verifica se o Ollama está acessível e se o modelo está instalado.
        Verificação é feita apenas uma vez por sessão para otimização.

        Returns:
            True se conectado e modelo instalado, False caso contrário

        Raises:
            OllamaClientError: Se o modelo não estiver instalado
        """
        if not hasattr(self, "_connection_checked"):
            self._connection_checked = False
        if self._connection_checked:
            return True
        if not hasattr(self, "_session"):
            self._session = requests.Session()
        if not hasattr(self, "base_url"):
            self.base_url = OLLAMA_BASE_URL.rstrip('/')
        if not hasattr(self, "model"):
            self.model = OLLAMA_MODEL

        try:
            response = self._session.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])

                # Verificar se o modelo especificado está na lista
                model_names = [m.get("name", "") for m in models]
                # Normalizar nomes para comparação (remover tags como :latest)
                model_names_normalized = [m.split(":")[0] if ":" in m else m for m in model_names]

                # Verificar se o modelo está instalado (comparação exata ou parcial)
                model_existe = self.model in model_names or self.model.split(":")[0] in model_names_normalized

                if not model_existe:
                    raise OllamaClientError(
                        f"Modelo '{self.model}' não está instalado no Ollama.\n"
                        f"Modelos disponíveis: {', '.join(model_names) if model_names else 'nenhum'}\n\n"
                        f"Para instalar o modelo, execute: ollama pull {self.model}"
                    )

                self._connection_checked = True
                return True
            return False
        except requests.exceptions.ConnectionError:
            return False
        except requests.exceptions.Timeout:
            return False

    def _montar_options(self, num_predict_override: int | None = None, incluir_temperatura: bool = False) -> dict:
        """Monta o dicionário 'options' do payload do Ollama, centralizando
        os parâmetros de geração (num_ctx, num_predict, num_thread e,
        quando aplicável, temperature) em um único lugar."""
        options = {
            "num_ctx": OLLAMA_NUM_CTX,
            "num_predict": (
                num_predict_override if num_predict_override is not None
                else (self.num_predict if self.num_predict is not None else OLLAMA_NUM_PREDICT)
            ),
            "num_thread": OLLAMA_NUM_THREAD,
        }
        if incluir_temperatura:
            options["temperature"] = OLLAMA_TEMPERATURE_TOOLS
        return options

    def _montar_payload(
        self,
        mensagens: list[dict],
        tools: list[dict] | None,
        stream: bool,
        incluir_temperatura: bool = False,
        num_predict_override: int | None = None,
    ) -> dict:
        """Monta o payload base enviado ao Ollama, centralizando campos que
        dependem do modelo (ex.: 'think') em core/config.py. Se
        OLLAMA_ENVIAR_THINK_PARAM for False, o campo 'think' é omitido do
        payload inteiramente (para modelos que não o suportam)."""
        payload = {
            "model": self.model,
            "messages": mensagens,
            "stream": stream,
            "options": self._montar_options(num_predict_override, incluir_temperatura),
            "keep_alive": OLLAMA_KEEP_ALIVE,
        }
        if OLLAMA_ENVIAR_THINK_PARAM:
            payload["think"] = OLLAMA_THINK_HABILITADO
        if tools:
            payload["tools"] = tools
        return payload

    def _make_request(
        self,
        payload: dict,
        stream: bool = False
    ) -> requests.Response:
        """
        Faz a requisição HTTP para a API do Ollama.
        Método centralizado para evitar duplicação de código.

        Args:
            payload: Dicionário com os dados da requisição
            stream: Se True, habilita streaming na requisição

        Returns:
            Objeto Response da requisição

        Raises:
            OllamaClientError: Se houver erro de conexão ou HTTP
        """
        # Verificar conexão apenas na primeira chamada
        if not self._check_connection():
            raise OllamaClientError(
                "Não foi possível conectar ao Ollama. "
                f"Verifique se o Ollama está rodando em {self.base_url} "
                f"e se o modelo '{self.model}' está instalado.\n"
                "\nPara iniciar o Ollama, execute: ollama serve\n"
                f"Para instalar o modelo, execute: ollama pull {self.model}"
            )

        if not hasattr(self, "_session"):
            self._session = requests.Session()
        if not hasattr(self, "base_url"):
            self.base_url = OLLAMA_BASE_URL.rstrip('/')
        if not hasattr(self, "timeout"):
            self.timeout = OLLAMA_TIMEOUT

        try:
            response = self._session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
                stream=stream
            )

            if response.status_code != 200:
                raise OllamaClientError(
                    f"Erro na API do Ollama: status {response.status_code}\n"
                    f"Detalhes: {response.text}"
                )

            return response

        except requests.exceptions.ConnectionError:
            raise OllamaClientError(
                "Perda de conexão com o Ollama durante a requisição. "
                "Verifique se o serviço continua rodando."
            )
        except requests.exceptions.Timeout:
            raise OllamaTimeoutError(
                "Tempo limite excedido ao aguardar resposta do modelo. "
                "O modelo pode estar processando uma requisição complexa."
            )

    def enviar_mensagem(
        self,
        mensagens: list[dict[str, str]],
        tools: list[dict] | None = None,
        stream: bool = False
    ) -> Generator[str, None, None] | str:
        """
        Envia uma conversa (histórico de mensagens) para o modelo.

        Args:
            mensagens: Lista de dicionários com as mensagens no formato
                      [{"role": "user|assistant|system", "content": "..."}]
            tools: Lista de ferramentas (function calling) opcionais
            stream: Se True, retorna um generator para streaming

        Returns:
            Se stream=False: string com a resposta completa
            Se stream=True: generator que yielda chunks da resposta

        Raises:
            OllamaClientError: Se houver erro de conexão ou resposta inválida
        """
        # Preparar payload da requisição com parâmetros de otimização
        payload = self._montar_payload(mensagens, tools, stream=stream)

        response = self._make_request(payload, stream=stream)

        if stream:
            return self._process_stream(response)
        else:
            return self._process_response(response)

    def _process_response(self, response: requests.Response) -> str:
        """
        Processa uma resposta não-streaming da API.

        Args:
            response: Objeto Response do requests

        Returns:
            Conteúdo da mensagem do assistente
        """
        data = response.json()
        return data.get("message", {}).get("content", "")

    def _process_stream(self, response: requests.Response) -> Generator[str, None, None]:
        """
        Processa uma resposta em streaming da API.
        Inclui tratamento de erro durante a iteração do generator.

        Args:
            response: Objeto Response do requests em modo stream

        Yields:
            Chunks de texto da resposta

        Raises:
            OllamaClientError: Se houver erro de conexão durante o streaming
        """
        try:
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Erro de conexão durante streaming: {e}")
            raise OllamaClientError(
                "Perda de conexão com o Ollama durante o streaming. "
                "Verifique se o serviço continua rodando."
            )
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout durante streaming: {e}")
            raise OllamaTimeoutError(
                "Tempo limite excedido durante o streaming da resposta."
            )

    def chat_com_tools(
        self,
        mensagem_usuario: str,
        historico: list[dict[str, str]] | None = None,
        tools: list[dict] | None = None
    ) -> tuple[str, dict | None]:
        """
        Envia mensagem com suporte a function calling e extrai tool calls.
        Reutiliza a lógica de _make_request para evitar duplicação de código.

        Args:
            mensagem_usuario: Texto da mensagem do usuário
            historico: Histórico opcional de mensagens anteriores
            tools: Ferramentas para function calling

        Returns:
            Tupla (resposta_texto, tool_call_info) onde:
            - resposta_texto: String com a resposta do modelo
            - tool_call_info: Dict {"name": str, "arguments": dict} se houver call, None caso contrário
        """
        mensagens = _montar_mensagens_com_reforco(historico, mensagem_usuario)

        if not tools:
            # Sem tools, comportamento normal
            resposta = self.enviar_mensagem(mensagens, tools=None, stream=False)
            return resposta, None

        # Com tools, preparar payload completo com parâmetros de otimização
        num_predict_override = (
            OLLAMA_NUM_PREDICT_DOCUMENTO if _sugere_composicao_de_documento(mensagem_usuario) else None
        )
        payload = self._montar_payload(
            mensagens, tools, stream=False, incluir_temperatura=True,
            num_predict_override=num_predict_override,
        )

        # Reutilizar _make_request para fazer a chamada HTTP
        response = self._make_request(payload, stream=False)

        data = response.json()
        message = data.get("message", {})
        content = message.get("content", "")

        # Verificar se há tool_calls na resposta (formato padrão Ollama)
        tool_calls = message.get("tool_calls", [])

        if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
            # Validar estrutura da tool call antes de acessar
            tc = tool_calls[0]
            if not isinstance(tc, dict):
                logger.warning(f"Tool call malformada: esperado dict, obtido {type(tc)}")
                return content, None

            funcao = tc.get("function")
            if not isinstance(funcao, dict):
                logger.warning(f"Tool call malformada: 'function' não é um dict: {funcao}")
                return content, None

            nome = funcao.get("name")
            if not nome or not isinstance(nome, str):
                logger.warning(f"Tool call malformada: 'name' ausente ou inválido: {nome}")
                return content, None

            argumentos_str = funcao.get("arguments", "{}")

            try:
                argumentos = json.loads(argumentos_str) if isinstance(argumentos_str, str) else argumentos_str
            except json.JSONDecodeError:
                logger.warning(f"Falha ao parsear argumentos da tool call: {argumentos_str}")
                argumentos = {}

            tool_call_info = {
                "name": nome,
                "arguments": argumentos
            }

            logger.debug(f"Tool call detectada: {nome}({argumentos})")
            return content, tool_call_info

        # Fallback: tentar extrair tool call do conteúdo textual (comportamento
        # específico de modelos como o Qwen3.5; desativável via
        # OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL para outros modelos)
        if OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL:
            tool_call_textual = _tentar_extrair_tool_call_textual(content)
            if tool_call_textual:
                logger.info(f"Tool call extraída via fallback textual: {tool_call_textual['name']}")
                return content, tool_call_textual

        return content, None

    def chat_com_tools_stream_com_metricas(
        self,
        mensagem_usuario: str,
        historico: list[dict[str, str]] | None = None,
        tools: list[dict] | None = None,
    ) -> tuple[str, dict | None, int, float, float | None]:
        """Envia uma mensagem em streaming e retorna texto, tool call e
        métricas de tokens, incluindo TTFT (tempo até o primeiro token)
        separado da velocidade de decodificação."""
        mensagens = _montar_mensagens_com_reforco(historico, mensagem_usuario)

        num_predict_override = (
            OLLAMA_NUM_PREDICT_DOCUMENTO if _sugere_composicao_de_documento(mensagem_usuario) else None
        )
        payload = self._montar_payload(
            mensagens, tools, stream=True, incluir_temperatura=True,
            num_predict_override=num_predict_override,
        )

        response = self._make_request(payload, stream=True)
        tool_call_final = None
        partes_texto: list[str] = []
        partes_thinking: list[str] = []
        eval_count = 0
        inicio = time.monotonic()
        t_primeiro_token: float | None = None

        try:
            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    data = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue

                message = data.get("message", {})
                content = message.get("content", "")
                if content:
                    if t_primeiro_token is None:
                        t_primeiro_token = time.monotonic()
                    partes_texto.append(content)

                thinking = message.get("thinking", "")
                if thinking:
                    partes_thinking.append(thinking)

                if data.get("done") is True:
                    eval_count = int(data.get("eval_count") or 0)

                tool_calls = message.get("tool_calls")
                if not isinstance(tool_calls, list) or not tool_calls:
                    continue

                tool_call = tool_calls[0]
                if not isinstance(tool_call, dict):
                    logger.warning("Tool call malformada no stream com métricas: esperado dict")
                    continue

                function = tool_call.get("function")
                if not isinstance(function, dict):
                    logger.warning("Tool call malformada no stream com métricas: function inválida")
                    continue

                name = function.get("name")
                if not isinstance(name, str) or not name:
                    logger.warning("Tool call malformada no stream com métricas: name inválido")
                    continue

                arguments_raw = function.get("arguments", "{}")
                try:
                    arguments = json.loads(arguments_raw) if isinstance(arguments_raw, str) else arguments_raw
                except json.JSONDecodeError:
                    logger.warning("Falha ao parsear argumentos da tool call no stream com métricas")
                    arguments = {}

                tool_call_final = {"name": name, "arguments": arguments}

        except requests.exceptions.ConnectionError as error:
            logger.error(f"Erro de conexão durante streaming com métricas: {error}")
            raise OllamaClientError(
                "Perda de conexão com o Ollama durante o streaming. "
                "Verifique se o serviço continua rodando."
            ) from error
        except requests.exceptions.Timeout as error:
            logger.error(f"Timeout durante streaming com métricas: {error}")
            raise OllamaTimeoutError(
                "Tempo limite excedido durante o streaming da resposta."
            ) from error

        conteudo_final = "".join(partes_texto)

        if (
            OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL
            and tool_call_final is None
            and (partes_texto or partes_thinking)
        ):
            texto_busca = conteudo_final + "\n" + "".join(partes_thinking)
            tool_call_textual = _tentar_extrair_tool_call_textual(texto_busca)
            if tool_call_textual is not None:
                origem = "thinking" if not conteudo_final.strip() and partes_thinking else "content"
                logger.warning(
                    "Tool call detectada via fallback textual no stream com métricas (origem=%s): %s",
                    origem, tool_call_textual["name"],
                )
                tool_call_final = tool_call_textual

        fim = time.monotonic()
        ttft_ms = ((t_primeiro_token - inicio) * 1000) if t_primeiro_token is not None else None

        LIMIAR_MIN_DECODE_S = 0.01  # abaixo disso, a medição não é confiável
        duracao_decode = (fim - t_primeiro_token) if t_primeiro_token is not None else (fim - inicio)

        if eval_count and duracao_decode >= LIMIAR_MIN_DECODE_S:
            tokens_por_segundo = eval_count / duracao_decode
        else:
            tokens_por_segundo = 0.0

        return conteudo_final, tool_call_final, eval_count, tokens_por_segundo, ttft_ms

    def chat_com_tools_stream(
        self,
        mensagem_usuario: str,
        historico: list[dict[str, str]] | None = None,
        tools: list[dict] | None = None
    ) -> Generator[tuple[str | None, dict | None], None, None]:
        """Envia uma mensagem com function calling e retorna a resposta em chunks."""
        mensagens = _montar_mensagens_com_reforco(historico, mensagem_usuario)

        num_predict_override = (
            OLLAMA_NUM_PREDICT_DOCUMENTO if _sugere_composicao_de_documento(mensagem_usuario) else None
        )
        payload = self._montar_payload(
            mensagens, tools, stream=True, incluir_temperatura=True,
            num_predict_override=num_predict_override,
        )

        response = self._make_request(payload, stream=True)
        tool_call_final = None
        houve_conteudo = False
        conteudo_acumulado = ""
        thinking_acumulado = ""

        try:
            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    data = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue

                message = data.get("message", {})
                content = message.get("content", "")
                if content:
                    houve_conteudo = True
                    conteudo_acumulado += content
                    yield content, None

                thinking = message.get("thinking", "")
                if thinking:
                    thinking_acumulado += thinking

                tool_calls = message.get("tool_calls")
                if not isinstance(tool_calls, list) or not tool_calls:
                    continue

                tool_call = tool_calls[0]
                if not isinstance(tool_call, dict):
                    logger.warning("Tool call malformada no stream: esperado dict")
                    continue

                function = tool_call.get("function")
                if not isinstance(function, dict):
                    logger.warning("Tool call malformada no stream: function inválida")
                    continue

                name = function.get("name")
                if not isinstance(name, str) or not name:
                    logger.warning("Tool call malformada no stream: name inválido")
                    continue

                arguments_raw = function.get("arguments", "{}")
                try:
                    arguments = (
                        json.loads(arguments_raw)
                        if isinstance(arguments_raw, str)
                        else arguments_raw
                    )
                except json.JSONDecodeError:
                    logger.warning("Falha ao parsear argumentos da tool call no stream")
                    arguments = {}

                tool_call_final = {"name": name, "arguments": arguments}

        except requests.exceptions.ConnectionError as error:
            logger.error(f"Erro de conexão durante streaming: {error}")
            raise OllamaClientError(
                "Perda de conexão com o Ollama durante o streaming. "
                "Verifique se o serviço continua rodando."
            ) from error
        except requests.exceptions.Timeout as error:
            logger.error(f"Timeout durante streaming: {error}")
            raise OllamaTimeoutError(
                "Tempo limite excedido durante o streaming da resposta."
            ) from error

        if (
            OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL
            and tool_call_final is None
            and (conteudo_acumulado or thinking_acumulado)
        ):
            texto_busca = conteudo_acumulado + "\n" + thinking_acumulado
            tool_call_textual = _tentar_extrair_tool_call_textual(texto_busca)
            if tool_call_textual is not None:
                origem = "thinking" if not conteudo_acumulado.strip() and thinking_acumulado.strip() else "content"
                logger.warning(
                    "Tool call detectada via fallback textual (origem=%s): %s",
                    origem, tool_call_textual["name"],
                )
                tool_call_final = tool_call_textual

        if tool_call_final is None and not houve_conteudo and not thinking_acumulado:
            logger.debug(
                "Resposta do Ollama sem tool call e sem conteúdo textual "
                "para o modelo '%s'.", self.model
            )

        yield None, tool_call_final

    def continuar_com_resultado_ferramenta_stream(
        self,
        historico: list[dict[str, str]],
        tool_call: dict,
        resultado: str,
        tools: list[dict] | None = None,
        metricas_saida: dict | None = None,
    ) -> Generator[tuple[str | None, dict | None], None, None]:
        """
        Reenvia a conversa incluindo o resultado de uma ferramenta de leitura
        (role="tool") e transmite a nova resposta do modelo em streaming.

        Args:
            historico: histórico já contendo system prompt + mensagem do usuário
                (NÃO deve incluir a chamada de ferramenta nem o resultado; ambos
                são montados aqui).
            tool_call: {"name": str, "arguments": dict} da ferramenta já executada.
            resultado: texto com o resultado real da execução da ferramenta.
            tools: schema de ferramentas, para permitir encadeamento (ex.: nova leitura).
        """
        mensagens = list(historico)
        mensagens.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {
                "name": tool_call.get("name", ""),
                "arguments": tool_call.get("arguments", {}),
            }}],
        })
        mensagens.append({"role": "tool", "content": resultado})

        payload = self._montar_payload(
            mensagens, tools, stream=True, incluir_temperatura=True,
            num_predict_override=OLLAMA_NUM_PREDICT_CONTINUACAO,
        )

        response = self._make_request(payload, stream=True)
        tool_call_final = None
        houve_conteudo = False
        conteudo_acumulado = ""
        thinking_acumulado = ""
        eval_count = 0

        try:
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue

                message = data.get("message", {})
                content = message.get("content", "")
                if content:
                    houve_conteudo = True
                    conteudo_acumulado += content
                    yield content, None

                thinking = message.get("thinking", "")
                if thinking:
                    thinking_acumulado += thinking

                if data.get("done") is True:
                    eval_count = int(data.get("eval_count") or 0)

                tool_calls = message.get("tool_calls")
                if not isinstance(tool_calls, list) or not tool_calls:
                    continue

                tc = tool_calls[0]
                if not isinstance(tc, dict):
                    logger.warning("Tool call malformada no stream de continuação")
                    continue
                function = tc.get("function")
                if not isinstance(function, dict):
                    logger.warning("Tool call malformada no stream de continuação: function inválida")
                    continue
                name = function.get("name")
                if not isinstance(name, str) or not name:
                    logger.warning("Tool call malformada no stream de continuação: name inválido")
                    continue
                arguments_raw = function.get("arguments", "{}")
                try:
                    arguments = (
                        json.loads(arguments_raw)
                        if isinstance(arguments_raw, str)
                        else arguments_raw
                    )
                except json.JSONDecodeError:
                    logger.warning("Falha ao parsear argumentos no stream de continuação")
                    arguments = {}
                tool_call_final = {"name": name, "arguments": arguments}

        except requests.exceptions.ConnectionError as error:
            logger.error(f"Erro de conexão durante streaming de continuação: {error}")
            raise OllamaClientError(
                "Perda de conexão com o Ollama durante o streaming. "
                "Verifique se o serviço continua rodando."
            ) from error
        except requests.exceptions.Timeout as error:
            logger.error(f"Timeout durante streaming de continuação: {error}")
            raise OllamaTimeoutError(
                "Tempo limite excedido durante o streaming da resposta."
            ) from error

        if (
            OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL
            and tool_call_final is None
            and (conteudo_acumulado or thinking_acumulado)
        ):
            texto_busca = conteudo_acumulado + "\n" + thinking_acumulado
            tool_call_textual = _tentar_extrair_tool_call_textual(texto_busca)
            if tool_call_textual is not None:
                origem = "thinking" if not conteudo_acumulado.strip() and thinking_acumulado.strip() else "content"
                logger.warning(
                    "Tool call detectada via fallback textual na continuação (origem=%s): %s",
                    origem, tool_call_textual["name"],
                )
                tool_call_final = tool_call_textual

        if tool_call_final is None and not houve_conteudo and not thinking_acumulado:
            logger.debug("Resposta de continuação sem tool call e sem conteúdo textual.")

        if metricas_saida is not None:
            metricas_saida["tokens_gerados"] = eval_count

        yield None, tool_call_final
