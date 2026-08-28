"""
Router para seleção dinâmica de modelos LLM baseado na complexidade da tarefa.

Implementa arquitetura MoE (Mixture of Experts) local:
- Tarefas simples (conversa, resumo curto) → Qwen 2.5 Omni 3B (rápido)
- Tarefas complexas (relatórios, análise profunda, código) → Llama 3.2 8B (potente)
- Visão/áudio → Qwen 2.5 Omni 3B (multimodal)
"""

import re
from typing import Literal


class ModelRouter:
    """
    Roteador inteligente que seleciona o modelo LLM apropriado
    baseado no conteúdo e complexidade da mensagem.
    """

    # Palavras-chave que indicam tarefas complexas
    COMPLEX_KEYWORDS = [
        'relatório', 'relatorio', 'análise profunda', 'analise profunda',
        'código', 'codigo', 'script', 'programa', 'desenvolver',
        'documento extenso', 'texto longo', 'artigo',
        'compare', 'contraste', 'comparar', 'contrastar', 'comparação', 'comparacao',
        'síntese', 'sintese', 'técnico', 'tecnico',
        'jurídico', 'juridico', 'legal', 'lei', 'processo',
        'planilha', 'excel', 'dados estruturados',
        'múltiplas', 'multiplas', 'vários', 'varios',
        'detalhado', 'detalhadamente', 'completo',
        'pesquisa', 'investigar', 'investigação', 'investigacao',
        'financeiro', 'contábil', 'contabil', 'imposto',
        'contrato', 'cláusula', 'clausula', 'termo',
        'implementação', 'implementacao', 'arquitetura', 'sistema distribuído',
    ]

    # Palavras-chave que indicam tarefas simples
    SIMPLE_KEYWORDS = [
        'oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite',
        'tudo bem', 'como vai', 'obrigado', 'obrigada',
        'ajuda', 'help', 'socorro',
        'resumo', 'resumir', 'explique', 'explicar',
        'traduzir', 'tradução', 'traducao',
        'corrigir', 'correção', 'correcao', 'gramática', 'gramatica',
        'pergunta', 'questão', 'questao',
    ]

    def __init__(self):
        self.default_model: Literal['qwen3b', 'llama8b'] = 'qwen3b'

    def _calculate_complexity_score(self, message: str) -> float:
        """
        Calcula um score de complexidade baseado em:
        - Tamanho da mensagem
        - Presença de palavras-chave complexas
        - Estrutura da mensagem (listas, múltiplas perguntas)
        """
        msg_lower = message.lower()
        score = 0.0

        # Score base pelo tamanho (mensagens longas tendem a ser mais complexas)
        word_count = len(message.split())
        if word_count > 50:
            score += 0.3
        if word_count > 100:
            score += 0.3
        if word_count > 200:
            score += 0.4

        # Score por palavras-chave complexas
        complex_matches = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in msg_lower)
        score += min(complex_matches * 0.15, 0.6)  # Máximo 0.6 de score por keywords

        # Score por palavras-chave simples (reduz complexidade)
        simple_matches = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in msg_lower)
        score -= min(simple_matches * 0.1, 0.3)  # Reduz até 0.3

        # Score por estrutura (múltiplas perguntas, listas)
        if '?' in message and message.count('?') > 1:
            score += 0.2
        if message.count('•') > 2 or message.count('-') > 2:
            score += 0.1
        if re.search(r'\d+\.', message):  # Listas numeradas
            score += 0.1

        return min(max(score, 0.0), 1.0)  # Normaliza entre 0 e 1

    def route(
        self,
        message: str,
        has_image: bool = False,
        has_audio: bool = False
    ) -> Literal['qwen3b', 'llama8b']:
        """
        Decide qual modelo usar baseado na mensagem.

        Args:
            message: Texto da mensagem do usuário
            has_image: True se a mensagem inclui imagem/anexo visual
            has_audio: True se a mensagem inclui áudio

        Returns:
            'qwen3b' para tarefas leves, 'llama8b' para tarefas complexas
        """
        # Visão e áudio sempre usam Qwen (único multimodal)
        if has_image or has_audio:
            return 'qwen3b'

        # Calcula score de complexidade
        complexity = self._calculate_complexity_score(message)

        # Threshold: acima de 0.4 usa modelo pesado
        if complexity > 0.4:
            return 'llama8b'

        return 'qwen3b'

    def get_model_info(self, model: Literal['qwen3b', 'llama8b']) -> dict:
        """Retorna informações sobre o modelo."""
        models = {
            'qwen3b': {
                'name': 'Qwen 2.5 Omni 3B',
                'description': 'Modelo leve e rápido para tarefas cotidianas',
                'use_cases': ['Conversa', 'Resumos curtos', 'Visão', 'Áudio', 'Tradução'],
                'avg_response_time': '1-3s',
            },
            'llama8b': {
                'name': 'Llama 3.2 8B',
                'description': 'Modelo potente para raciocínio complexo',
                'use_cases': ['Relatórios', 'Análise profunda', 'Código', 'Jurídico'],
                'avg_response_time': '5-15s',
            }
        }
        return models.get(model, models['qwen3b'])


# Instância singleton para uso global
_router_instance: ModelRouter | None = None


def get_router() -> ModelRouter:
    """Retorna instância singleton do router."""
    global _router_instance
    if _router_instance is None:
        _router_instance = ModelRouter()
    return _router_instance


def route_message(message: str, has_image: bool = False, has_audio: bool = False) -> Literal['qwen3b', 'llama8b']:
    """
    Função utilitária para roteamento rápido.

    Exemplo:
        model = route_message("Preciso de um relatório jurídico detalhado")
        # Retorna: 'llama8b'
    """
    return get_router().route(message, has_image, has_audio)


if __name__ == '__main__':
    # Testes rápidos
    router = ModelRouter()

    test_cases = [
        ("Oi, tudo bem?", 'qwen3b'),
        ("Preciso analisar este documento financeiro", 'qwen3b'),
        ("Gere um relatório jurídico completo de 10 páginas com análise detalhada de todas as cláusulas contratuais", 'llama8b'),
        ("Crie um script Python para automatizar planilhas Excel", 'llama8b'),
        ("Traduza este texto para inglês", 'qwen3b'),
        ("Compare os prós e contras de diferentes abordagens técnicas para implementação de sistema distribuído", 'llama8b'),
    ]

    print("Testes do ModelRouter:")
    print("-" * 60)
    for message, expected in test_cases:
        result = router.route(message)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{message[:50]}...' → {result} (esperado: {expected})")
