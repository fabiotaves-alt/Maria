"""Utilitários compartilhados do benchmark da MARIA.

Contém a estimativa de tokens usada pelo warmup (`run_benchmark.py`) e pelo
pre-check de contexto do runner (`runners/maria_runner.py`). Módulo separado
para evitar import circular (run_benchmark importa MariaRunner).
"""

# Tokens reservados no warmup para histórico + resposta do modelo.
MARGEM_SEGURANCA_SYSTEM = 512

# Fração do contexto reservada à resposta do modelo no pre-check por tarefa.
MARGEM_RESERVA_RESPOSTA = 0.30

# Fator de calibração medido no warmup: tokens reais (via /tokenize) divididos
# pela estimativa por caracteres do system prompt. Captura o efeito dos JSONs
# de tool schema (muito mais densos em tokens que prosa). 1.0 = sem calibração.
_fator_calibracao: float = 1.0


def estimar_tokens(texto: str) -> int:
    """Estimativa rápida de tokens: ~4 caracteres por token (regra do polegar).

    Não é precisa (tokenização BPE varia por tipo de conteúdo), mas serve para
    detectar estouro GROSSO de contexto. Retorna 0 para texto vazio e no
    mínimo 1 para texto não vazio.
    """
    if not texto:
        return 0
    return max(1, len(texto) // 4)


def definir_fator_calibracao(tokens_reais: int, texto: str) -> float:
    """Define o fator de calibração a partir de uma contagem exata de tokens.

    `tokens_reais` deve vir de POST /tokenize do llama-server sobre o mesmo
    `texto`. Se a estimativa do texto for zero (texto vazio), o fator não é
    alterado. Retorna o fator vigente após a operação.
    """
    global _fator_calibracao
    estimativa = estimar_tokens(texto)
    if estimativa > 0 and tokens_reais > 0:
        _fator_calibracao = tokens_reais / estimativa
    return _fator_calibracao


def obter_fator_calibracao() -> float:
    """Retorna o fator de calibração vigente."""
    return _fator_calibracao


def estimar_tokens_calibrado(texto: str) -> int:
    """Estimativa de tokens ajustada pelo fator medido no warmup.

    Com calibração ativa, o erro cai de ~±50% (chars/4 puro) para ~±10%,
    sem nenhuma chamada HTTP extra por tarefa.
    """
    if not texto:
        return 0
    return max(1, int(estimar_tokens(texto) * _fator_calibracao))