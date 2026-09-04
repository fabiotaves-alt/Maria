"""Fluxo de confirmação de ações pendentes (escrita em disco)."""

import unicodedata


def interpretar_confirmacao(texto: str) -> bool | None:
    """
    Interpreta a resposta do usuário a um pedido de confirmação.

    Args:
        texto: Texto da resposta do usuário

    Returns:
        True se afirmativa (ex: "sim", "pode", "confirmo", "ok", "vai", "isso")
        False se negativa (ex: "não", "nao", "cancela", "para", "esquece")
        None se ambígua/não reconhecida
    """
    # Normalizar texto: lowercase, remover acentos e pontuação
    texto_normalizado = texto.lower().strip()

    # Remover acentos
    texto_normalizado = unicodedata.normalize('NFD', texto_normalizado)
    texto_normalizado = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')

    # Remover pontuação
    texto_normalizado = ''.join(c for c in texto_normalizado if c.isalnum() or c.isspace())

    # Frases completas que devem ser verificadas primeiro (antes de palavras soltas)
    frases_afirmativas = {"com certeza", "pois nao", "pode ser"}
    frases_negativas = {"de jeito nenhum", "nem pensar"}

    # Verificar frases completas primeiro
    if texto_normalizado in frases_afirmativas:
        return True
    if texto_normalizado in frases_negativas:
        return False

    # Palavras-chave afirmativas (palavras únicas)
    afirmativas = {"sim", "pode", "confirmo", "ok", "vale", "bora", "vai", "isso",
                   "claro", "certeza", "pois", "ser"}

    # Palavras-chave negativas (palavras únicas)
    negativas = {"nao", "cancela", "para", "esquece", "jamais", "aborta", "desiste"}

    # Dividir em palavras
    palavras = texto_normalizado.split()

    # Para frases com múltiplas palavras que não são frases conhecidas,
    # verificar se contém palavras-chave fortes
    if len(palavras) > 1:
        # Verificar se é uma frase ambígua comum
        if "acho" in palavras or "quero" in palavras or "ver" in palavras or "depois" in palavras:
            return None
        # Verificar se contém "sim" ou "nao/não" como palavra forte
        if "sim" in palavras:
            return True
        if "nao" in palavras:
            return False
        # Caso contrário, é ambíguo
        return None

    # Para palavras únicas, verificar diretamente
    if len(palavras) == 1:
        palavra = palavras[0]
        if palavra in afirmativas:
            return True
        if palavra in negativas:
            return False

    # Ambíguo/não reconhecido
    return None


class ConfirmacaoAcao:
    """Estado de uma ação pendente aguardando confirmação do usuário."""

    MAX_TENTATIVAS_AMBIGUAS = 2

    def __init__(self):
        self.tool_call: dict | None = None
        self.tentativas_ambiguas: int = 0

    def definir(self, tool_call: dict) -> None:
        self.tool_call = {
            "name": tool_call.get("name"),
            "arguments": tool_call.get("arguments", {}),
        }
        self.tentativas_ambiguas = 0

    def limpar(self) -> None:
        self.tool_call = None
        self.tentativas_ambiguas = 0

    def tem(self) -> bool:
        return self.tool_call is not None
