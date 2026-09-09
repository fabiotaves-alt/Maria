"""
Módulo cliente para comunicação com o llama-server (llama.cpp).
Compatível com a API OpenAI (/v1/chat/completions).
Suporta entradas multimodais: texto, imagem (base64) e áudio (.wav).
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
from backend.infrastructure.tools.tool_call_json_parser import extrair_tool_call_json
from backend.domain.validacao_tool_call import validar_tool_call_determinístico

logger = logging.getLogger(__name__)


class LlamaClientError(Exception):
    """Exceção personalizada para erros do cliente llama-server."""
    pass


class LlamaTimeoutError(LlamaClientError):
    """Indica que uma requisição excedeu o timeout configurado."""
    pass


_PALAVRAS_COMPOSICAO_DOCUMENTO = {
    "carta", "relatório", "relatorio", "ata", "comunicado", "memorando", "memorial",
}


def _sugere_composicao_de_documento(mensagem_usuario: str) -> bool:
    texto = mensagem_usuario.lower()
    return any(palavra in texto for palavra in _PALAVRAS_COMPOSICAO_DOCUMENTO)


def _detectar_degeneracao(texto: str, minimo: int = 100, tamanho_bloco_max: int = 8) -> bool:
    if len(texto) < minimo:
        return False

    cauda = texto[-minimo:]
    for tamanho in range(1, tamanho_bloco_max + 1):
        bloco = cauda[:tamanho]
        repeticoes = len(cauda) // tamanho
        if repeticoes >= 2 and cauda.startswith(bloco * repeticoes):
            return True

    return False


def montar_mensagens_com_reforco(historico: list[dict] | None, mensagem_usuario: str) -> list[dict]:
    mensagens = list(historico or [])
    if not mensagens or mensagens[0].get("role") != "system":
        from backend.core.config import MARIA_SYSTEM_PROMPT
        mensagens.insert(0, {"role": "system", "content": MARIA_SYSTEM_PROMPT})

    mensagens.append({"role": "user", "content": mensagem_usuario})
    return mensagens


# Alias privado para compatibilidade temporária durante migração
_montar_mensagens_com_reforco = montar_mensagens_com_reforco


def _montar_conteudo_multimodal(
    texto: str,
    image_path: str | None = None,
    audio_path: str | None = None,
) -> str | list:
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
    def __init__(
        self,
        base_url: str = LLAMA_BASE_URL,
        model: str = LLAMA_MODEL,
        timeout: int = LLAMA_TIMEOUT,
        num_predict: int | None = None,
        temperature: float | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.num_predict = num_predict
        self.temperature = temperature
        self._session = requests.Session()
        self._connection_checked = False
        self._num_ctx_respeitado: bool | None = None

    def _check_connection(self) -> bool:
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
        temperatura_override: float | None = None,
    ) -> dict:
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
            payload.update(montar_sampler_params())
            if temperatura_override is not None:
                payload["temperature"] = temperatura_override
            elif self.temperature is not None:
                payload["temperature"] = self.temperature
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    def _make_request(self, payload: dict, stream: bool = False) -> requests.Response:
        if not self._check_connection():
            raise LlamaClientError(
                "Não foi possível conectar ao llama-server. "
                f"Verifique se o servidor está rodando em {self.base_url}."
            )
        if self._num_ctx_respeitado is False:
            payload.pop("num_ctx", None)
        try:
            response = self._session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout,
                stream=stream,
            )
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
            raise LlamaClientError("Perda de conexão com o llama-server.")
        except requests.exceptions.Timeout:
            raise LlamaTimeoutError("Tempo limite excedido ao aguardar resposta do llama-server.")

    def _extrair_tool_call_da_resposta(self, message: dict, content: str) -> dict | None:
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

            tc_raw = {"name": nome, "arguments": argumentos if isinstance(argumentos, dict) else {}}
            res_val = validar_tool_call_determinístico(tc_raw)
            logger.debug("Tool call detectada via delta/nativo: %s(%s)", nome, res_val["tool_call"]["arguments"])
            return res_val["tool_call"]

        if LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL and content:
            tool_call_json = extrair_tool_call_json(content)
            if tool_call_json:
                logger.info("Tool call extraída via JSON parser: %s", tool_call_json["name"])
                res_val = validar_tool_call_determinístico(tool_call_json)
                return res_val["tool_call"]

        return None

    def _resolver_tool_call_final(
        self,
        tc_detectada_via_delta: bool,
        tc_nome_acumulado: str,
        tc_args_acumulado: str,
        conteudo_acumulado: str,
        contexto_log: str = "",
    ):
        if tc_detectada_via_delta and tc_nome_acumulado:
            try:
                argumentos = json.loads(tc_args_acumulado) if tc_args_acumulado else {}
            except json.JSONDecodeError:
                argumentos = {}
            tc_raw = {"name": tc_nome_acumulado, "arguments": argumentos}
            res_val = validar_tool_call_determinístico(tc_raw)
            fallbacks = [r["tipo"] for r in res_val.get("reparos", [])]
            logger.debug("Tool call via delta%s: %s(%s)", contexto_log, tc_nome_acumulado, res_val["tool_call"]["arguments"])
            return res_val["tool_call"], "delta", None, fallbacks

        if LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL and conteudo_acumulado:
            tc_json = extrair_tool_call_json(conteudo_acumulado)
            if tc_json:
                reparado_json = tc_json.pop("_reparado", False)
                tc_json.pop("_fonte", None)
                res_val = validar_tool_call_determinístico(tc_json)
                fallbacks = []
                if reparado_json:
                    fallbacks.append("json_reparado")
                for r in res_val.get("reparos", []):
                    fallbacks.append(r["tipo"])
                logger.info("Tool call detectada via JSON parser%s: %s", contexto_log, res_val["tool_call"]["name"])
                return res_val["tool_call"], "json", None, fallbacks

        return None, None, None, []

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        image_path: str | None = None,
        audio_path: str | None = None,
        metricas_saida: dict | None = None,
    ) -> tuple[str | None, dict | None]:
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
        eval_count = 0
        t_primeiro_token: float | None = None
        degeneracao_detectada = False
        finish_reason_final: str | None = None

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
                if finish_reason:
                    finish_reason_final = finish_reason

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
                    if _detectar_degeneracao(conteudo_acumulado):
                        logger.warning(
                            "Geração degenerada detectada (repetição de %r): stream interrompido.",
                            conteudo_acumulado[-1],
                        )
                        degeneracao_detectada = True
                        finish_reason_final = "degenerate"
                        break
                    yield chunk, None

                usage = data.get("usage")
                if usage:
                    eval_count = usage.get("completion_tokens", eval_count)

                if finish_reason in ("stop", "tool_calls", "length"):
                    break

        except requests.exceptions.ConnectionError:
            raise LlamaClientError("Perda de conexão com o llama-server durante o streaming.")
        except requests.exceptions.Timeout:
            raise LlamaTimeoutError("Tempo limite excedido durante o streaming da resposta.")

        if degeneracao_detectada:
            tool_call_final = None
            tool_call_fonte = None
            tool_nome_bruto = None
            tool_fallbacks = []
        else:
            tool_call_final, tool_call_fonte, tool_nome_bruto, tool_fallbacks = self._resolver_tool_call_final(
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
            metricas_saida["finish_reason"] = finish_reason_final
            metricas_saida["degeneracao_detectada"] = degeneracao_detectada
            metricas_saida["tool_call_fonte"] = tool_call_fonte
            metricas_saida["tool_nome_bruto"] = tool_nome_bruto
            metricas_saida["fallbacks"] = tool_fallbacks

        yield None, tool_call_final

    def enviar_mensagem(
        self,
        mensagens: list[dict],
        tools: list[dict] | None = None,
        stream: bool = False,
    ) -> str:
        content, _ = self.chat(mensagens, tools=tools)
        return content or ""

    def chat_com_tools_stream(
        self,
        mensagem_usuario: str,
        historico: list[dict] | None = None,
        tools: list[dict] | None = None,
    ) -> Generator[tuple[str | None, dict | None], None, None]:
        mensagens = montar_mensagens_com_reforco(historico, mensagem_usuario)
        yield from self.chat_stream(mensagens, tools=tools)

    def chat_com_tools_stream_com_metricas(
        self,
        mensagem_usuario: str,
        historico: list[dict[str, str]] | None = None,
        tools: list[dict] | None = None,
        extras_saida: dict | None = None,
    ) -> tuple[str, dict | None, int, float, float | None]:
        mensagens = montar_mensagens_com_reforco(historico, mensagem_usuario)
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

        if extras_saida is not None:
            extras_saida["finish_reason"] = metricas.get("finish_reason")
            extras_saida["degeneracao_detectada"] = metricas.get("degeneracao_detectada", False)
            extras_saida["tool_call_fonte"] = metricas.get("tool_call_fonte")
            extras_saida["tool_nome_bruto"] = metricas.get("tool_nome_bruto")
            extras_saida["fallbacks"] = metricas.get("fallbacks", [])

        return texto_final, tool_call_final, tokens_gerados, tokens_por_segundo, ttft_ms

    def continuar_com_resultado_ferramenta_stream(
        self,
        historico: list[dict],
        tool_call: dict,
        resultado: str,
        tools: list[dict] | None = None,
        metricas_saida: dict | None = None,
        temperatura_override: float | None = None,
    ) -> Generator[tuple[str | None, dict | None], None, None]:
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
            temperatura_override=temperatura_override,
        )
        inicio = time.monotonic()
        response = self._make_request(payload, stream=True)

        conteudo_acumulado = ""
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
            raise LlamaClientError("Perda de conexão com o llama-server durante o streaming de continuação.")
        except requests.exceptions.Timeout:
            raise LlamaTimeoutError("Tempo limite excedido durante o streaming de continuação.")

        tool_call_final, tool_call_fonte, tool_nome_bruto, tool_fallbacks = self._resolver_tool_call_final(
            tc_detectada_via_delta,
            tc_nome_acumulado,
            tc_args_acumulado,
            conteudo_acumulado,
            contexto_log=" (continuação)",
        )

        if metricas_saida is not None:
            metricas_saida["tokens_gerados"] = eval_count
            metricas_saida["tool_call_fonte"] = tool_call_fonte
            metricas_saida["tool_nome_bruto"] = tool_nome_bruto
            metricas_saida["fallbacks"] = tool_fallbacks

        yield None, tool_call_final


def _ultima_mensagem_usuario(mensagens: list[dict]) -> str | None:
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
    for parte in partes:
        if isinstance(parte, dict) and parte.get("type") == "text":
            return parte.get("text", "")
    return ""
