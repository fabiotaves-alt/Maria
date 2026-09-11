"""Testes das configurações centralizadas (backend/config.py)."""
from backend import config


def test_llama_timeout_padrao_300_segundos():
    """Timeout padrão deve estar alinhado ao bridge Rust (300s)."""
    assert config.LLAMA_TIMEOUT == 300
