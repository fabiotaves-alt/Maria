"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.excel_handler esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.infrastructure.tools.excel_handler import *
