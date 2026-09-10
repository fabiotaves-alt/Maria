"""Re-export de compatibilidade temporaria (DEPRECATED).

Este modulo sera removido em uma versao futura. Use `backend.config`
diretamente. Ver docs/PROGRESSO_DESENVOLVIMENTO.md (fase B7) para o
cronograma de remocao.
"""
import warnings

warnings.warn(
    "backend.core.config esta deprecated; use backend.config diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.config import *  # noqa: F401,F403
# `import *` nao exporta nomes com underscore (ex.: __version__), que o
# bridge ainda consome durante a transicao.
from backend.config import __version__  # noqa: F401
