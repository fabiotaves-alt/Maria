"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.paths esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.infrastructure.paths import *
