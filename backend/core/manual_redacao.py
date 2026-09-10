"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.manual_redacao esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.application.manual_redacao import *