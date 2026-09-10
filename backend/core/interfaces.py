"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.interfaces esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.interfaces.interfaces import *
