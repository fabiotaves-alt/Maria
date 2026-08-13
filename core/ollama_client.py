"""
Módulo cliente para comunicação com a API local do Ollama.
Responsável por enviar mensagens ao modelo Qwen2.5-3B e receber respostas.

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
from core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_NUM_CTX,
    OLLAMA_NUM_PREDICT,
    OLLAMA_NUM_THREAD,
    OLLAMA_KEEP_ALIVE
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
            model: Nome do modelo a usar (padrão: qwen2.5:7b)
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
                "Verifique se o Ollama está rodando em http://localhost:11434 "
                "e se o modelo 'qwen2.5:7b' está instalado.\n"
                "\nPara iniciar o Ollama, execute: ollama serve\n"
                "Para instalar o modelo, execute: ollama pull qwen2.5:7b"
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
        payload = {
            "model": self.model,
            "messages": mensagens,
            "stream": stream,
            "think": False,
            "options": {
                "num_ctx": OLLAMA_NUM_CTX,
                "num_predict": self.num_predict if self.num_predict is not None else OLLAMA_NUM_PREDICT,
                "num_thread": OLLAMA_NUM_THREAD
            },
            "keep_alive": OLLAMA_KEEP_ALIVE
        }
        
        # Adicionar tools se fornecidas
        if tools:
            payload["tools"] = tools
        
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
        mensagens = []
        
        if historico:
            mensagens.extend(historico)
        
        mensagens.append({"role": "user", "content": mensagem_usuario})
        
        if not tools:
            # Sem tools, comportamento normal
            resposta = self.enviar_mensagem(mensagens, tools=None, stream=False)
            return resposta, None
        
        # Com tools, preparar payload completo com parâmetros de otimização
        payload = {
            "model": self.model,
            "messages": mensagens,
            "tools": tools,
            "stream": False,
            "think": False,
            "options": {
                "num_ctx": OLLAMA_NUM_CTX,
                "num_predict": self.num_predict if self.num_predict is not None else OLLAMA_NUM_PREDICT,
                "num_thread": OLLAMA_NUM_THREAD
            },
            "keep_alive": OLLAMA_KEEP_ALIVE
        }
        
        # Reutilizar _make_request para fazer a chamada HTTP
        response = self._make_request(payload, stream=False)
        
        data = response.json()
        message = data.get("message", {})
        content = message.get("content", "")
        
        # Verificar se há tool_calls na resposta
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
        
        return content, None

    def chat_com_tools_stream_com_metricas(
        self,
        mensagem_usuario: str,
        historico: list[dict[str, str]] | None = None,
        tools: list[dict] | None = None,
    ) -> tuple[str, dict | None, int, float]:
        """Envia uma mensagem em streaming e retorna texto, tool call e métricas de tokens."""
        mensagens = list(historico or [])
        mensagens.append({"role": "user", "content": mensagem_usuario})

        num_predict = getattr(self, "num_predict", None)
        payload = {
            "model": self.model,
            "messages": mensagens,
            "tools": tools,
            "stream": True,
            "options": {
                "num_ctx": OLLAMA_NUM_CTX,
                "num_predict": num_predict if num_predict is not None else OLLAMA_NUM_PREDICT,
                "num_thread": OLLAMA_NUM_THREAD
            },
            "keep_alive": OLLAMA_KEEP_ALIVE
        }

        response = self._make_request(payload, stream=True)
        tool_call_final = None
        partes_texto: list[str] = []
        eval_count = 0
        inicio = time.monotonic()

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
                    partes_texto.append(content)

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

        duracao = max(time.monotonic() - inicio, 1e-9)
        tokens_por_segundo = (eval_count / duracao) if eval_count else 0.0
        return "".join(partes_texto), tool_call_final, eval_count, tokens_por_segundo

    def chat_com_tools_stream(
        self,
        mensagem_usuario: str,
        historico: list[dict[str, str]] | None = None,
        tools: list[dict] | None = None
    ) -> Generator[tuple[str | None, dict | None], None, None]:
        """Envia uma mensagem com function calling e retorna a resposta em chunks."""
        mensagens = list(historico or [])
        mensagens.append({"role": "user", "content": mensagem_usuario})

        payload = {
            "model": self.model,
            "messages": mensagens,
            "tools": tools,
            "stream": True,
            "options": {
                "num_ctx": OLLAMA_NUM_CTX,
                "num_predict": self.num_predict if self.num_predict is not None else OLLAMA_NUM_PREDICT,
                "num_thread": OLLAMA_NUM_THREAD
            },
            "keep_alive": OLLAMA_KEEP_ALIVE
        }

        response = self._make_request(payload, stream=True)
        tool_call_final = None
        houve_conteudo = False
        conteudo_acumulado = ""

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

        if tool_call_final is None and conteudo_acumulado:
            tool_call_textual = _tentar_extrair_tool_call_textual(conteudo_acumulado)
            if tool_call_textual is not None:
                logger.warning(
                    "Tool call detectada como texto vazado no content (fallback textual): %s",
                    tool_call_textual["name"],
                )
                tool_call_final = tool_call_textual

        if tool_call_final is None and not houve_conteudo:
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

        payload = {
            "model": self.model,
            "messages": mensagens,
            "tools": tools,
            "stream": True,
            "options": {
                "num_ctx": OLLAMA_NUM_CTX,
                "num_predict": self.num_predict if self.num_predict is not None else OLLAMA_NUM_PREDICT,
                "num_thread": OLLAMA_NUM_THREAD
            },
            "keep_alive": OLLAMA_KEEP_ALIVE
        }

        response = self._make_request(payload, stream=True)
        tool_call_final = None
        houve_conteudo = False
        conteudo_acumulado = ""

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

        if tool_call_final is None and conteudo_acumulado:
            tool_call_textual = _tentar_extrair_tool_call_textual(conteudo_acumulado)
            if tool_call_textual is not None:
                logger.warning(
                    "Tool call detectada como texto vazado no content (fallback textual): %s",
                    tool_call_textual["name"],
                )
                tool_call_final = tool_call_textual

        if tool_call_final is None and not houve_conteudo:
            logger.debug("Resposta de continuação sem tool call e sem conteúdo textual.")

        yield None, tool_call_final
