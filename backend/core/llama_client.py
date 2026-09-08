"""Re-export de compatibilidade temporaria."""
from backend.infrastructure.llm.llama_client import *
from backend.infrastructure.llm.llama_client import (
    _detectar_degeneracao,
    _montar_mensagens_com_reforco,
    _sugere_composicao_de_documento,
)