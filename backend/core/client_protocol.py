"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.client_protocol esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.interfaces.client_protocol import *
