"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.confirmacao esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.domain.confirmacao import *
