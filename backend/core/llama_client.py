"""
Módulo cliente para comunicação com o llama-server (llama.cpp).
Compatível com a API OpenAI (/v1/chat/completions).
Suporta entradas multimodais: texto, imagem (base64) e áudio (.wav).

Requisitos:
- Comunicação apenas via localhost (sem dependência de internet)
- Interface pública idêntica ao OllamaClient (chat, chat_stream)
- Suporte a streaming, tool calling e fallback textual
"""

import base64
import json
import logging
import re
import time
import uuid
from collections.abc import Generator
from pathlib import Path

import requests

from backend.core.config import (
    LLAMA_BASE_URL,
    LLAMA_MODEL,
    LLAMA_TIMEOUT,
    LLAMA_NUM_CTX,
    LLAMA_NUM_PREDICT,
    LLAMA_TEMPERATURE_TOOLS,
    LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL,
    LLAMA_NUM_PREDICT_DOCUMENTO,
    LLAMA_NUM_PREDICT_CONTINUACAO,
    LLAMA_REPEAT_LAST_N,
    LLAMA_REPEAT_PENALTY,
    LLAMA_FREQUENCY_PENALTY,
    LLAMA_PRESENCE_PENALTY,
    LLAMA_DRY_MULTIPLIER,
    LLAMA_DRY_BASE,
    LLAMA_DRY_ALLOWED_LENGTH,
    LLAMA_DRY_PENALTY_LAST_N,
    LLAMA_TOP_K,
    LLAMA_TOP_P,
    LLAMA_MIN_P,
    LLAMA_XTC_PROBABILITY,
    LLAMA_XTC_THRESHOLD,
    LLAMA_TYPICAL_P,
    LLAMA_TOP_N_SIGMA,
)

logger = logging.getLogger(__name__)


# Importa parser para formato textual usado pelo Qwen2.5-Omni-3B
from backend.core.tool_call_textual_parser import extrair_tool_call_textual


class LlamaClientError(Exception):
    """Exceção personalizada para erros do cliente llama-server."""
    pass


class LlamaTimeoutError(LlamaClientError):
    """Indica que uma requisição excedeu o timeout configurado."""
    pass


def _tentar_extrair_tool_call_textual(conteudo: str) -> dict | None:
    """
    Fallback: alguns modelos vazam a chamada de ferramenta como texto no
    campo 'content'. Esta função tenta detectar e extrair esse padrão.

    Returns:
        {"name": str, "arguments": dict} se encontrado, None caso contrário.

    NOTA: Este fallback cobre o formato JSON nativo no content.
    Para o formato array posicional do Qwen2.5-Omni-3B
    (ex: criar_planilha: ["gastos", "data", "valor"]), veja extrair_tool_call_textual.
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

    # NORMALIZACAO DE CHAVES: garante minusculas para evitar
    # falsos negativos quando o modelo gera 'Conteudo', 'Nome_arquivo', etc.
    argumentos = {k.lower(): v for k, v in argumentos.items()}

    return {"name": nome, "arguments": argumentos}


_PALAVRAS_COMPOSICAO_DOCUMENTO = {
    "carta", "relatório", "relatorio", "ata", "comunicado", "memorando", "memorial",
}


def _sugere_composicao_de_documento(mensagem_usuario: str) -> bool:
    """Heurística: retorna True se a mensagem sugere composição de documento narrativo."""
    texto = mensagem_usuario.lower()
    return any(palavra in texto for palavra in _PALAVRAS_COMPOSICAO_DOCUMENTO)


def _montar_mensagens_com_reforco(historico: list[dict] | None, mensagem_usuario: str) -> list[dict]:
    """
    Monta a lista de mensagens garantindo uma ÚNICA mensagem role="system".
    Não muta `historico` nem os dicts originais.
    O system prompt é carregado do arquivo system_prompt.txt pelo ChatSession.
    Esta função apenas garante que o system prompt esteja presente e adiciona a mensagem do usuário.
    """
    mensagens = list(historico or [])

    # Garante que há exatamente uma mensagem system no início
    # (o ChatSession já deve ter carregado o prompt do arquivo)
    if not mensagens or mensagens[0].get("role") != "system":
        # Fallback: se o ChatSession não carregou, lemos do arquivo aqui
        from backend.core.config import MARIA_SYSTEM_PROMPT
        mensagens.insert(0, {"role": "system", "content": MARIA_SYSTEM_PROMPT})

    mensagens.append({"role": "user", "content": mensagem_usuario})
    return mensagens


def _montar_conteudo_multimodal(
    texto: str,
    image_path: str | None = None,
    audio_path: str | None = None,
) -> str | list:
    """
    Monta o campo 'content' da última mensagem do usuário.
    Se não houver mídia, retorna string simples.
    Se houver imagem ou áudio, retorna lista de partes no formato OpenAI multimodal.
    """
    if not image_path and not audio_path:
        return texto

    partes: list[dict] = [{"type": "text", "text": texto}]

    if image_path:
        caminho = Path(image_path)
        sufixo = caminho.suffix.lower().lstrip(".")
        mime = f"image/{sufixo}" if sufixo in {"jpg", "jpeg", "png", "gif", "webp"} else "image/jpeg"
        if sufixo == "jpg":
            mime = "image/jpeg"
        dados_b64 = base64.b64encode(caminho.read_bytes()).decode("utf-8")
        partes.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{dados_b64}"},
        })

    if audio_path:
        caminho_audio = Path(audio_path)
        dados_b64 = base64.b64encode(caminho_audio.read_bytes()).decode("utf-8")
        partes.append({
            "type": "input_audio",
            "input_audio": {"data": dados_b64, "format": "wav"},
        })

    return partes


def montar_sampler_params() -> dict:
    """Snapshot dos parâmetros de sampler efetivos (config atual).

    Fonte única da verdade: usada tanto para montar o payload enviado ao
    llama-server quanto para registrar no log do benchmark quais parâmetros
    foram usados em cada execução. Os defaults espelham os do llama-server.
    """
    return {
        "temperature": LLAMA_TEMPERATURE_TOOLS,
        "repeat_last_n": LLAMA_REPEAT_LAST_N,
        "repeat_penalty": LLAMA_REPEAT_PENALTY,
        "frequency_penalty": LLAMA_FREQUENCY_PENALTY,
        "presence_penalty": LLAMA_PRESENCE_PENALTY,
        "dry_multiplier": LLAMA_DRY_MULTIPLIER,
        "dry_base": LLAMA_DRY_BASE,
        "dry_allowed_length": LLAMA_DRY_ALLOWED_LENGTH,
        "dry_penalty_last_n": LLAMA_DRY_PENALTY_LAST_N,
        "top_k": LLAMA_TOP_K,
        "top_p": LLAMA_TOP_P,
        "min_p": LLAMA_MIN_P,
        "xtc_probability": LLAMA_XTC_PROBABILITY,
        "xtc_threshold": LLAMA_XTC_THRESHOLD,
        "typical_p": LLAMA_TYPICAL_P,
        "top_n_sigma": LLAMA_TOP_N_SIGMA,
    }


class LlamaClient:
    """
    Cliente para comunicação com o llama-server (llama.cpp) via API OpenAI-compatible.

    Expõe a mesma interface pública que OllamaClient:
        chat()        — síncrono, retorna (texto, tool_call)
        chat_stream() — generator, yielda (chunk_texto, tool_call)
    """

    def __init__(
        self,
        base_url: str = LLAMA_BASE_URL,
        model: str = LLAMA_MODEL,
        timeout: int = LLAMA_TIMEOUT,
        num_predict: int | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.num_predict = num_predict
        self._session = requests.Session()
        self._connection_checked = False
        # None = nao testado; False = servidor rejeitou num_ctx (HTTP 400);
        # True = servidor aceitou. Cacheado por instancia.
        self._num_ctx_respeitado: bool | None = None

    def _check_connection(self) -> bool:
        """
        Verifica se o llama-server está acessível via GET /v1/models.
        Verificação feita apenas uma vez por instância.
        """
        if self._connection_checked:
            return True
        try:
            response = self._session.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                self._connection_checked = True
                return True
            return False
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return False

    def _montar_payload(
        self,
        mensagens: list[dict],
        tools: list[dict] | None,
        stream: bool,
        incluir_temperatura: bool = False,
        num_predict_override: int | None = None,
    ) -> dict:
        """Monta o payload para POST /v1/chat/completions."""
        max_tokens = (
            num_predict_override
            if num_predict_override is not None
            else (self.num_predict if self.num_predict is not None else LLAMA_NUM_PREDICT)
        )
        payload: dict = {
            "model": self.model,
            "messages": mensagens,
            "stream": stream,
            "max_tokens": max_tokens,
            "num_ctx": LLAMA_NUM_CTX,
        }
        if incluir_temperatura:
            # Envia explicitamente TODOS os parâmetros de sampler (mesmos
            # defaults do llama-server) para deixá-los configuráveis via ENV e
            # auditáveis no benchmark. O servidor ignora campos desconhecidos.
            payload.update(montar_sampler_params())
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    def _make_request(self, payload: dict, stream: bool = False) -> requests.Response:
        """
        Faz a requisição HTTP para o llama-server.

        Raises:
            LlamaClientError: erro de conexão ou HTTP inválido.
            LlamaTimeoutError: timeout excedido.
        """
        if not self._check_connection():
            raise LlamaClientError(
                "Não foi possível conectar ao llama-server. "
                f"Verifique se o servidor está rodando em {self.base_url}.\n"
                "Para iniciar: ./build/bin/llama-server -m <modelo.gguf> --port 8080"
            )
        # Servidores que já rejeitaram 'num_ctx' (HTTP 400) recebem o payload
        # sem o campo a partir da próxima chamada (flag cacheada por instância).
        if self._num_ctx_respeitado is False:
            payload.pop("num_ctx", None)
        try:
            response = self._session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout,
                stream=stream,
            )
            # Adaptativo: se o servidor rejeitar 'num_ctx' (HTTP 400), remove o
            # campo e refaz a requisição uma única vez — evita erro 400 desnecessário
            # sem custar uma requisição de sonda nas chamadas normais.
            if (
                response.status_code == 400
                and "num_ctx" in payload
                and self._num_ctx_respeitado is not False
            ):
                self._num_ctx_respeitado = False
                payload.pop("num_ctx", None)
                logger.warning(
                    "llama-server rejeitou 'num_ctx' (HTTP 400); reenviando sem o campo."
                )
                response = self._session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.timeout,
                    stream=stream,
                )
            if response.status_code != 200:
                raise LlamaClientError(
                    f"Erro na API do llama-server: status {response.status_code}\n"
                    f"Detalhes: {response.text}"
                )
            return response
        except requests.exceptions.ConnectionError:
            raise LlamaClientError(
                "Perda de conexão com o llama-server durante a requisição. "
                "Verifique se o serviço continua rodando."
            )
        except requests.exceptions.Timeout:
            raise LlamaTimeoutError(
                "Tempo limite excedido ao aguardar resposta do llama-server. "
                "O modelo pode estar processando uma requisição complexa."
            )

    def _extrair_tool_call_da_resposta(self, message: dict, content: str) -> dict | None:
        """
        Extrai tool call da mensagem de resposta (formato OpenAI).
        Tenta campo estruturado 'tool_calls' primeiro; depois fallback textual.
        """
        tool_calls = message.get("tool_calls") or []
        if tool_calls and isinstance(tool_calls, list):
            tc = tool_calls[0]
            if not isinstance(tc, dict):
                logger.warning("Tool call malformada: esperado dict, obtido %s", type(tc))
                return None
            funcao = tc.get("function")
            if not isinstance(funcao, dict):
                logger.warning("Tool call malformada: 'function' não é dict: %s", funcao)
                return None
            nome = funcao.get("name")
            if not nome or not isinstance(nome, str):
                logger.warning("Tool call malformada: 'name' ausente ou inválido: %s", nome)
                return None
            argumentos_raw = funcao.get("arguments", "{}")
            try:
                argumentos = json.loads(argumentos_raw) if isinstance(argumentos_raw, str) else argumentos_raw
            except json.JSONDecodeError:
                logger.warning("Falha ao parsear argumentos da tool call: %s", argumentos_raw)
                argumentos = {}

            # NORMALIZACAO DE CHAVES: garante minusculas para evitar
            # falsos negativos quando o modelo gera 'Conteudo', 'Nome_arquivo', etc.
            if isinstance(argumentos, dict):
                argumentos = {k.lower(): v for k, v in argumentos.items()}

            logger.debug("Tool call detectada: %s(%s)", nome, argumentos)
            return {"name": nome, "arguments": argumentos}

        if LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL and content:
            tool_call_textual = _tentar_extrair_tool_call_textual(content)
            if tool_call_textual:
                logger.info("Tool call extraída via fallback textual: %s", tool_call_textual["name"])
                return tool_call_textual

        # --- Fallback 3: formato array posicional (Qwen2.5-Omni-3B) ---
        # O modelo gera texto como: criar_planilha: ["gastos", "data", "valor"]
        # ou criar_documento(["pauta", "Titulo", "conteudo"])
        tool_call_array = extrair_tool_call_textual(content)
        if tool_call_array:
            logger.info("Tool call extraída via parser array posicional: %s", tool_call_array["name"])
            return tool_call_array

        return None

    def _resolver_tool_call_final(
        self,
        tc_detectada_via_delta: bool,
        tc_nome_acumulado: str,
        tc_args_acumulado: str,
        conteudo_acumulado: str,
        contexto_log: str = "",
    ) -> dict | None:
        """Monta o dict final da tool call a partir dos acumuladores do streaming.

        Elimina duplicação entre chat_stream e continuar_com_resultado_ferramenta_stream.
        """
        if tc_detectada_via_delta and tc_nome_acumulado:
            try:
                argumentos = json.loads(tc_args_acumulado) if tc_args_acumulado else {}
            except json.JSONDecodeError:
                argumentos = {}
            logger.debug("Tool call via delta%s: %s(%s)", contexto_log, tc_nome_acumulado, argumentos)
            return {"name": tc_nome_acumulado, "arguments": argumentos}

        if LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL and conteudo_acumulado:
            tool_call_textual = _tentar_extrair_tool_call_textual(conteudo_acumulado)
            if tool_call_textual:
                logger.info("Tool call detectada via fallback textual%s: %s", contexto_log, tool_call_textual["name"])
                return tool_call_textual

        return None

    # ------------------------------------------------------------------
    # Interface pública principal
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        image_path: str | None = None,
        audio_path: str | None = None,
        metricas_saida: dict | None = None,
    ) -> tuple[str | None, dict | None]:
        """
        Envia mensagens ao llama-server e retorna (texto, tool_call).

        Args:
            messages: Histórico de mensagens já montado (inclui system + user).
            tools: Ferramentas para function calling.
            image_path: Caminho para imagem a incluir na última mensagem do usuário.
            audio_path: Caminho para arquivo .wav a incluir na última mensagem do usuário.
            metricas_saida: Dict mutável para receber métricas (tokens_gerados).

        Returns:
            (texto_resposta, tool_call_info) onde tool_call_info é
            {"name": str, "arguments": dict} ou None.
        """
        mensagens = _aplicar_midia_na_ultima_mensagem(messages, image_path, audio_path)

        num_predict_override = None
        ultima_user = _ultima_mensagem_usuario(mensagens)
        if ultima_user and _sugere_composicao_de_documento(ultima_user):
            num_predict_override = LLAMA_NUM_PREDICT_DOCUMENTO

        payload = self._montar_payload(
            mensagens, tools, stream=False,
            incluir_temperatura=bool(tools),
            num_predict_override=num_predict_override,
        )
        response = self._make_request(payload, stream=False)
        data = response.json()

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message", {})
        content = message.get("content") or ""

        if metricas_saida is not None:
            usage = data.get("usage", {})
            metricas_saida["tokens_gerados"] = usage.get("completion_tokens", 0)

        tool_call = self._extrair_tool_call_da_resposta(message, content)
        return content, tool_call

    def chat_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        image_path: str | None = None,
        audio_path: str | None = None,
        metricas_saida: dict | None = None,
    ) -> Generator[tuple[str | None, dict | None], None, None]:
        """
        Envia mensagens ao llama-server em modo streaming.

        Yields:
            (chunk_texto, None) durante o streaming de texto.
            (None, tool_call_info) como último item quando há tool call.
            (None, None) como último item quando não há tool call.
        """
        mensagens = _aplicar_midia_na_ultima_mensagem(messages, image_path, audio_path)

        num_predict_override = None
        ultima_user = _ultima_mensagem_usuario(mensagens)
        if ultima_user and _sugere_composicao_de_documento(ultima_user):
            num_predict_override = LLAMA_NUM_PREDICT_DOCUMENTO

        payload = self._montar_payload(
            mensagens, tools, stream=True,
            incluir_temperatura=bool(tools),
            num_predict_override=num_predict_override,
        )
        inicio = time.monotonic()
        response = self._make_request(payload, stream=True)

        conteudo_acumulado = ""
        tool_call_final: dict | None = None
        eval_count = 0
        t_primeiro_token: float | None = None

        # Acumuladores para tool call em streaming (delta)
        tc_nome_acumulado = ""
        tc_args_acumulado = ""
        tc_detectada_via_delta = False

        try:
            for line in response.iter_lines():
                if not line:
                    continue
                linha = line.decode("utf-8") if isinstance(line, bytes) else line
                if linha.startswith("data:"):
                    linha = linha[5:].strip()
                if linha == "[DONE]":
                    break
                try:
                    data = json.loads(linha)
                except json.JSONDecodeError:
                    continue

                choice = (data.get("choices") or [{}])[0]
                delta = choice.get("delta", {})
                finish_reason = choice.get("finish_reason")

                # Acumular tool call via delta (formato OpenAI streaming)
                delta_tool_calls = delta.get("tool_calls") or []
                if delta_tool_calls:
                    tc_detectada_via_delta = True
                    tc0 = delta_tool_calls[0]
                    funcao_delta = tc0.get("function", {})
                    tc_nome_acumulado += funcao_delta.get("name") or ""
                    tc_args_acumulado += funcao_delta.get("arguments") or ""

                chunk = delta.get("content") or ""
                if chunk:
                    if t_primeiro_token is None:
                        t_primeiro_token = time.monotonic() - inicio
                    conteudo_acumulado += chunk
                    eval_count += 1
                    yield chunk, None

                # Métricas via usage (último chunk)
                usage = data.get("usage")
                if usage:
                    eval_count = usage.get("completion_tokens", eval_count)

                if finish_reason in ("stop", "tool_calls", "length"):
                    break

        except requests.exceptions.ConnectionError:
            raise LlamaClientError(
                "Perda de conexão com o llama-server durante o streaming."
            )
        except requests.exceptions.Timeout:
            raise LlamaTimeoutError(
                "Tempo limite excedido durante o streaming da resposta."
            )

        tool_call_final = self._resolver_tool_call_final(
            tc_detectada_via_delta,
            tc_nome_acumulado,
            tc_args_acumulado,
            conteudo_acumulado,
            contexto_log=" streaming",
        )

        if metricas_saida is not None:
            duracao = time.monotonic() - inicio
            metricas_saida["tokens_gerados"] = eval_count
            metricas_saida["ttft"] = round(t_primeiro_token, 3) if t_primeiro_token is not None else None
            metricas_saida["tokens_por_segundo"] = round(eval_count / duracao, 1) if duracao > 0 else 0.0

        yield None, tool_call_final

    # ------------------------------------------------------------------
    # Métodos de compatibilidade com a interface do OllamaClient
    # (usados por main.py, tool_chaining.py e benchmark)
    # ------------------------------------------------------------------

    def enviar_mensagem(
        self,
        mensagens: list[dict],
        tools: list[dict] | None = None,
        stream: bool = False,
    ) -> str:
        """Compatibilidade com OllamaClient.enviar_mensagem (usado em aquecer_modelo)."""
        content, _ = self.chat(mensagens, tools=tools)
        return content or ""

    def chat_com_tools_stream(
        self,
        mensagem_usuario: str,
        historico: list[dict] | None = None,
        tools: list[dict] | None = None,
    ) -> Generator[tuple[str | None, dict | None], None, None]:
        """
        Compatibilidade com OllamaClient.chat_com_tools_stream.
        Monta as mensagens com reforço e delega ao chat_stream.
        """
        mensagens = _montar_mensagens_com_reforco(historico, mensagem_usuario)
        yield from self.chat_stream(mensagens, tools=tools)

    def chat_com_tools_stream_com_metricas(
        self,
        mensagem_usuario: str,
        historico: list[dict[str, str]] | None = None,
        tools: list[dict] | None = None,
    ) -> tuple[str, dict | None, int, float, float | None]:
        """
        Envia uma mensagem em streaming e retorna (texto, tool_call,
        tokens_gerados, tokens_por_segundo, ttft_ms). ttft_ms é o tempo até o
        primeiro token em MILISSEGUNDOS (chat_stream usa segundos internamente
        em metricas_saida["ttft"] — converter aqui).
        """
        mensagens = _montar_mensagens_com_reforco(historico, mensagem_usuario)
        metricas: dict = {}
        partes_texto: list[str] = []
        tool_call_final: dict | None = None

        for chunk, tool_chunk in self.chat_stream(mensagens, tools=tools, metricas_saida=metricas):
            if chunk is not None:
                partes_texto.append(chunk)
            if tool_chunk is not None:
                tool_call_final = tool_chunk

        texto_final = "".join(partes_texto)
        tokens_gerados = metricas.get("tokens_gerados", 0)
        tokens_por_segundo = metricas.get("tokens_por_segundo", 0.0)
        ttft_s = metricas.get("ttft")
        ttft_ms = round(ttft_s * 1000, 1) if ttft_s is not None else None

        return texto_final, tool_call_final, tokens_gerados, tokens_por_segundo, ttft_ms

    def continuar_com_resultado_ferramenta_stream(
        self,
        historico: list[dict],
        tool_call: dict,
        resultado: str,
        tools: list[dict] | None = None,
        metricas_saida: dict | None = None,
    ) -> Generator[tuple[str | None, dict | None], None, None]:
        """
        Reenvia o histórico (incluindo role="tool") ao llama-server e continua
        a geração em streaming. Usado após executar uma ferramenta.

        Yields:
            (chunk_texto, None) durante o streaming.
            (None, tool_call_info) como último item.
        """
        mensagens = list(historico)
        tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
        mensagens.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": tool_call_id,
                "type": "function",
                "function": {
                    "name": tool_call.get("name", ""),
                    "arguments": json.dumps(tool_call.get("arguments", {}), ensure_ascii=False),
                },
            }],
        })
        mensagens.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": resultado,
        })

        payload = self._montar_payload(
            mensagens, tools, stream=True,
            incluir_temperatura=bool(tools),
            num_predict_override=LLAMA_NUM_PREDICT_CONTINUACAO,
        )
        inicio = time.monotonic()
        response = self._make_request(payload, stream=True)

        conteudo_acumulado = ""
        tool_call_final: dict | None = None
        eval_count = 0
        t_primeiro_token: float | None = None

        tc_nome_acumulado = ""
        tc_args_acumulado = ""
        tc_detectada_via_delta = False

        try:
            for line in response.iter_lines():
                if not line:
                    continue
                linha = line.decode("utf-8") if isinstance(line, bytes) else line
                if linha.startswith("data:"):
                    linha = linha[5:].strip()
                if linha == "[DONE]":
                    break
                try:
                    data = json.loads(linha)
                except json.JSONDecodeError:
                    continue

                choice = (data.get("choices") or [{}])[0]
                delta = choice.get("delta", {})
                finish_reason = choice.get("finish_reason")

                delta_tool_calls = delta.get("tool_calls") or []
                if delta_tool_calls:
                    tc_detectada_via_delta = True
                    tc0 = delta_tool_calls[0]
                    funcao_delta = tc0.get("function", {})
                    tc_nome_acumulado += funcao_delta.get("name") or ""
                    tc_args_acumulado += funcao_delta.get("arguments") or ""

                chunk = delta.get("content") or ""
                if chunk:
                    if t_primeiro_token is None:
                        t_primeiro_token = time.monotonic() - inicio
                    conteudo_acumulado += chunk
                    eval_count += 1
                    yield chunk, None

                usage = data.get("usage")
                if usage:
                    eval_count = usage.get("completion_tokens", eval_count)

                if finish_reason in ("stop", "tool_calls", "length"):
                    break

        except requests.exceptions.ConnectionError:
            raise LlamaClientError(
                "Perda de conexão com o llama-server durante o streaming de continuação."
            )
        except requests.exceptions.Timeout:
            raise LlamaTimeoutError(
                "Tempo limite excedido durante o streaming de continuação."
            )

        tool_call_final = self._resolver_tool_call_final(
            tc_detectada_via_delta,
            tc_nome_acumulado,
            tc_args_acumulado,
            conteudo_acumulado,
            contexto_log=" (continuação)",
        )

        if metricas_saida is not None:
            metricas_saida["tokens_gerados"] = eval_count

        yield None, tool_call_final


# ------------------------------------------------------------------
# Helpers de módulo
# ------------------------------------------------------------------

def _ultima_mensagem_usuario(mensagens: list[dict]) -> str | None:
    """Retorna o texto da última mensagem com role='user', ou None."""
    for msg in reversed(mensagens):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                for parte in content:
                    if isinstance(parte, dict) and parte.get("type") == "text":
                        return parte.get("text", "")
    return None


def _aplicar_midia_na_ultima_mensagem(
    mensagens: list[dict],
    image_path: str | None,
    audio_path: str | None,
) -> list[dict]:
    """
    Retorna uma cópia da lista de mensagens onde a última mensagem com
    role='user' tem seu 'content' substituído pelo conteúdo multimodal,
    caso image_path ou audio_path sejam fornecidos.
    """
    if not image_path and not audio_path:
        return mensagens

    resultado = list(mensagens)
    for i in range(len(resultado) - 1, -1, -1):
        if resultado[i].get("role") == "user":
            content_atual = resultado[i].get("content", "")
            texto = content_atual if isinstance(content_atual, str) else _extrair_texto_de_partes(content_atual)
            novo_content = _montar_conteudo_multimodal(texto, image_path, audio_path)
            resultado[i] = {**resultado[i], "content": novo_content}
            break
    return resultado


def _extrair_texto_de_partes(partes: list) -> str:
    """Extrai texto de uma lista de partes multimodais."""
    for parte in partes:
        if isinstance(parte, dict) and parte.get("type") == "text":
            return parte.get("text", "")
    return ""
