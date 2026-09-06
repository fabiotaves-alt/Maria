"""Interfaces abstratas (``typing.Protocol``) da camada core da MARIA.

Reúne os contratos estruturais consumidos por `MariaController` e pelo
encadeamento de ferramentas. ``LLMClientProtocol`` **não** é redefinido aqui —
é importado de ``backend/core/client_protocol.py`` (fonte única), onde já é
usado pelo benchmark (``MariaRunner``) e pelo ``tool_chaining``.
"""

from typing import Protocol

from backend.core.client_protocol import LLMClientProtocol


class SessionStorageProtocol(Protocol):
    """Persistência de sessões de conversa (injetável no controller)."""

    def salvar(self, dados: dict, nome: str) -> None: ...

    def carregar(self, caminho: str) -> dict: ...

    def listar(self) -> list[dict]: ...


class ToolExecutorProtocol(Protocol):
    """
    Execução de ferramentas de escrita/leitura.

    Permite injetar um executor fake em testes (sem ``@patch`` de módulos
    concretos) e prepara a Fase 4 (arquitetura hexagonal): o controller e o
    ``tool_chaining`` passam a depender desta interface, não das funções
    globais de ``tools_schema``.
    """

    def executar_real(self, nome: str, args: dict) -> str: ...

    def executar_leitura(self, nome: str, args: dict) -> str: ...
