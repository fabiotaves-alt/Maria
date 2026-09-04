"""Contrato estrutural de cliente LLM (``typing.Protocol``).

Define a interface que o benchmark (``MariaRunner``) e o encadeamento de
ferramentas (``tool_chaining``) esperam de um cliente. ``LlamaClient`` satisfaz
este protocolo sem herança (duck typing estrutural), e fakes/test doubles podem
implementá-lo para substituir o cliente real — garantindo a substituibilidade
(princípio de Liskov) sem acoplamento a uma classe concreta.
"""
from collections.abc import Generator
from typing import Protocol


class LLMClientProtocol(Protocol):
    """Interface estrutural de um cliente LLM consumido pelo benchmark."""

    model: str

    def enviar_mensagem(
        self,
        mensagens: list[dict],
        tools: list[dict] | None = None,
        stream: bool = False,
    ) -> str: ...

    def chat_com_tools_stream(
        self,
        mensagem_usuario: str,
        historico: list[dict] | None = None,
        tools: list[dict] | None = None,
    ) -> Generator[tuple[str | None, dict | None], None, None]: ...

    def chat_com_tools_stream_com_metricas(
        self,
        mensagem_usuario: str,
        historico: list[dict[str, str]] | None = None,
        tools: list[dict] | None = None,
    ) -> tuple[str, dict | None, int, float, float | None]: ...

    def continuar_com_resultado_ferramenta_stream(
        self,
        historico: list[dict],
        tool_call: dict,
        resultado: str,
        tools: list[dict] | None = None,
        metricas_saida: dict | None = None,
        temperatura_override: float | None = None,
    ) -> Generator[tuple[str | None, dict | None], None, None]: ...
