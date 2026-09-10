"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.session_storage esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.interfaces.session_storage import *