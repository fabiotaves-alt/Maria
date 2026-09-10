"""Verifica se a resposta final está em português, detectando vazamento para inglês."""
import re

# Palavras funcionais comuns em inglês que não aparecem em português nesse contexto
_PALAVRAS_INGLES = {
    "the", "please", "could", "provide", "would", "should", "sure",
    "here", "your", "what", "when", "with", "this", "that", "and",
}


def resposta_em_portugues(texto: str) -> bool:
    """Retorna False se a resposta contiver vazamento significativo de inglês."""
    if not texto or not texto.strip():
        return True  # resposta vazia não é considerada vazamento de idioma

    palavras = re.findall(r"[a-zA-ZÀ-ÿ]+", texto.lower())
    if not palavras:
        return True

    ocorrencias_ingles = sum(1 for p in palavras if p in _PALAVRAS_INGLES)
    proporcao = ocorrencias_ingles / len(palavras)

    # Limiar: mais de 3% de palavras de função em inglês indica vazamento
    return proporcao <= 0.03
