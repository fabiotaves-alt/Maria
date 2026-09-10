"""Re-export de compatibilidade temporaria."""
import warnings

warnings.warn(
    "backend.core.llama_client esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.infrastructure.llm.llama_client import *
from backend.infrastructure.llm.llama_client import (
    _detectar_degeneracao,
    _montar_mensagens_com_reforco,
    _sugere_composicao_de_documento,
)