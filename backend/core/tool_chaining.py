"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.tool_chaining esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.application.tool_chaining import *