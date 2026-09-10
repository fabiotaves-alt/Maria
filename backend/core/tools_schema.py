"""Re-export para compatibilidade temporária."""
import warnings

warnings.warn(
    "backend.core.tools_schema esta deprecated; use a camada real diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.infrastructure.tools.tools_schema import *
from backend.infrastructure.tools.tools_schema import _sanitizar_nome_seguro