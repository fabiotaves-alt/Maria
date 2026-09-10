"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.chat_session esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.domain.chat_session import *
