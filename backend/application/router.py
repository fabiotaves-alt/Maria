"""
Router para seleção dinâmica de modelos LLM baseado na complexidade da tarefa.
"""

import re
from typing import Literal


class ModelRouter:
    """
    Router para seleção dinâmica de modelos baseado em heurísticas de complexidade.
    """

    MODEL_3B = "qwen2.5-omni-3b"
    MODEL_7B = "qwen2.5-omni-7b"

    COMPLEXITY_KEYWORDS = {
        "pesado": [
            "relatório", "relatorio", "análise", "analise", "comparativo",
            "código", "codigo", "script", "automação", "automacao",
            "detalhado", "extenso", "completo", "profundo",
            "resuma", "resumo", "sintetize", "extraia", "extrair",
            "ofício", "oficio", "memorando", "portaria", "decreto",
        ],
        "leitura_complexa": [
            "conteúdo de", "conteudo de", "analise o arquivo",
            "leia o documento", "resuma o documento",
        ],
    }

    def __init__(self, default_model: str = MODEL_3B):
        self.default_model = default_model

    def route(
        self,
        mensagem: str,
        tem_imagem: bool = False,
        tem_audio: bool = False,
        tem_ferramentas: bool = True,
    ) -> str:
        if tem_imagem or tem_audio:
            return self.MODEL_3B

        score = self._calculate_complexity_score(mensagem)

        if score >= 3:
            return self.MODEL_7B
        else:
            return self.MODEL_3B

    def _calculate_complexity_score(self, mensagem: str) -> int:
        texto = mensagem.lower()
        score = 0

        num_palavras = len(texto.split())
        if num_palavras > 30:
            score += 2
        elif num_palavras > 15:
            score += 1

        for kw in self.COMPLEXITY_KEYWORDS["pesado"]:
            if re.search(rf"\b{re.escape(kw)}\b", texto):
                score += 1

        for kw in self.COMPLEXITY_KEYWORDS["leitura_complexa"]:
            if kw in texto:
                score += 2

        if texto.count("?") > 1 or texto.count(".") > 3:
            score += 1

        return score

    def get_model_info(self, model_name: str) -> dict:
        if model_name == self.MODEL_7B:
            return {
                "name": self.MODEL_7B,
                "type": "heavy",
                "ctx_size": 4096,
                "description": "Modelo 7B — alta capacidade para tarefas complexas",
            }
        return {
            "name": self.MODEL_3B,
            "type": "light",
            "ctx_size": 2048,
            "description": "Modelo 3B — rápido para tarefas simples e multimodal",
        }


_router_instance: ModelRouter | None = None


def get_router() -> ModelRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = ModelRouter()
    return _router_instance


def route_message(mensagem: str, **kwargs) -> str:
    return get_router().route(mensagem, **kwargs)
