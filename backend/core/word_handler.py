"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.word_handler esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.infrastructure.tools.word_handler import *
