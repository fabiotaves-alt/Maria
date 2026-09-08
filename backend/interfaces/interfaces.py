"""Interfaces abstratas (``typing.Protocol``) da camada interfaces da MARIA."""

from typing import Protocol

from backend.interfaces.client_protocol import LLMClientProtocol


class SessionStorageProtocol(Protocol):
    """Persistência de sessões de conversa (injetável no controller)."""

    def salvar(self, dados: dict, nome: str) -> None: ...

    def carregar(self, caminho: str) -> dict: ...

    def listar(self) -> list[dict]: ...


class ToolExecutorProtocol(Protocol):
    """
    Execução de ferramentas de escrita/leitura.
    """

    def executar_real(self, nome: str, args: dict) -> str: ...

    def executar_leitura(self, nome: str, args: dict) -> str: ...
