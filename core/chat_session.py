"""
Módulo que gerencia a sessão de chat com histórico de contexto.
Responsável por manter o histórico da conversa e limitar o número de mensagens
para evitar degradação de performance.
"""

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


class ChatSession:
    """
    Gerencia uma sessão de chat com histórico de mensagens.
    
    Atributos:
        historico (list[dict]): Lista de mensagens no formato {"role": str, "content": str}
        max_mensagens (int): Número máximo de mensagens no histórico
        system_prompt (str): Prompt de sistema que define a identidade da MARIA
    """
    
    # Prompt de sistema fixo em português do Brasil
    SYSTEM_PROMPT = """Você é a MARIA, uma assistente de IA de escritório que roda 100% localmente no computador do usuário, sem depender de internet.

Suas características:
- Você responde SEMPRE em português do Brasil, mesmo ao pedir esclarecimentos, fazer perguntas ou lidar com incerteza. Nunca responda em inglês ou qualquer outro idioma, em nenhuma circunstância.
- Você é objetiva e focada em produtividade de escritório
- Você ajuda com tarefas administrativas, organização, redação e análise de dados
- Você mantém um tom profissional mas amigável
- Nunca invente informações sobre o usuário, como nome, preferências ou fatos que não tenham sido explicitamente informados nesta conversa. Se você não tiver certeza de algo mencionado anteriormente, diga claramente que não possui essa informação, em vez de supor ou inventar uma resposta.

Ferramentas disponíveis:
- Use criar_planilha para planilhas novas e editar_planilha para substituir uma planilha existente.
- Use criar_documento para documentos Word narrativos, sempre fornecendo título e conteúdo completo.
- Use listar_arquivos para ver o que existe em uma pasta permitida, e resumir_documento para ler e resumir um documento de texto já existente (.txt, .md, .csv, .log, .docx). Essas duas ferramentas são somente leitura e não pedem confirmação.
- Nunca invente o conteúdo de um arquivo ou uma lista de arquivos: use listar_arquivos e resumir_documento para verificar o que realmente existe antes de responder.
- Se um documento lido estiver marcado como truncado, avise o usuário que a análise considera apenas a parte inicial do arquivo.
- Você não tem acesso à internet, então não pode buscar informações online ou em tempo real

Seu objetivo é ser útil dentro das suas capacidades atuais, sempre comunicando de forma clara o que você pode e não pode fazer neste momento."""

    def __init__(self, max_mensagens: int = None):
        """
        Inicializa uma nova sessão de chat.
        
        Args:
            max_mensagens: Número máximo de mensagens no histórico.
                          Se None, usa o valor de MAX_MENSAGENS_HISTORICO do config.py
        """
        from core.config import MAX_MENSAGENS_HISTORICO
        self.max_mensagens = max_mensagens if max_mensagens is not None else MAX_MENSAGENS_HISTORICO
        self.historico: list[dict[str, str]] = []
        self.acao_pendente: dict | None = None
        self.tentativas_confirmacao_ambigua: int = 0
    
    def definir_acao_pendente(self, tool_call: dict) -> None:
        """
        Armazena uma ação pendente aguardando confirmação do usuário.
        
        Args:
            tool_call: Dicionário com 'name' e 'arguments' da tool call
        """
        self.acao_pendente = {
            "name": tool_call.get("name"),
            "arguments": tool_call.get("arguments", {})
        }
        self.tentativas_confirmacao_ambigua = 0
    
    def limpar_acao_pendente(self) -> None:
        """Limpa a ação pendente e zera o contador de ambiguidade."""
        self.acao_pendente = None
        self.tentativas_confirmacao_ambigua = 0
    
    def tem_acao_pendente(self) -> bool:
        """
        Verifica se há uma ação pendente aguardando confirmação.
        
        Returns:
            True se houver ação pendente, False caso contrário
        """
        return self.acao_pendente is not None
    
    def adicionar_mensagem(self, role: str, content: str) -> None:
        """
        Adiciona uma mensagem ao histórico.
        
        Args:
            role: Papel da mensagem ("user" ou "assistant")
            content: Conteúdo da mensagem
            
        Raises:
            ValueError: Se o role não for "user" ou "assistant"
        """
        if role not in ["user", "assistant"]:
            raise ValueError(f"Role inválido: {role}. Use apenas 'user' ou 'assistant'.")
        
        self.historico.append({"role": role, "content": content})
        
        # Manter histórico dentro do limite
        self._limitar_historico()
    
    def _limitar_historico(self) -> None:
        """
        Remove mensagens antigas se o histórico exceder o limite.
        O histórico interno contém apenas mensagens user/assistant.
        """
        if len(self.historico) > self.max_mensagens:
            # Remover mensagens mais antigas (FIFO)
            self.historico = self.historico[-self.max_mensagens:]
    
    def get_historico_com_system(self) -> list[dict[str, str]]:
        """
        Retorna o histórico completo incluindo o system prompt.
        O system prompt é sempre injetado como primeira mensagem.
        
        Returns:
            Lista de mensagens com system prompt como primeira mensagem
        """
        # Sempre injetar system prompt no início
        return [{"role": "system", "content": self.SYSTEM_PROMPT}] + self.historico
    
    def get_historico_sem_system(self) -> list[dict[str, str]]:
        """
        Retorna apenas as mensagens da conversa (sem system prompt).
        Como o histórico interno nunca contém role="system", basta retornar uma cópia.
        
        Returns:
            Lista de mensagens user/assistant
        """
        return self.historico.copy()
    
    def limpar_historico(self) -> None:
        """
        Limpa o histórico da conversa.
        O system prompt continua sendo injetado dinamicamente por
        get_historico_com_system.
        """
        self.historico = []
    
    def get_ultima_mensagem_usuario(self) -> str | None:
        """
        Retorna a última mensagem do usuário.
        
        Returns:
            Conteúdo da última mensagem do usuário, ou None se não houver
        """
        for msg in reversed(self.historico):
            if msg["role"] == "user":
                return msg["content"]
        return None
    
    def contar_mensagens(self) -> int:
        """
        Conta o número de mensagens no histórico.
        Como o histórico interno só contém user/assistant, retorna len(historico).
        
        Returns:
            Número de mensagens user/assistant
        """
        return len(self.historico)
    
    def to_dict(self) -> dict:
        """
        Serializa a sessão para um dicionário.
        
        Returns:
            Dicionário com os dados da sessão
        """
        return {
            "max_mensagens": self.max_mensagens,
            "historico": self.historico,
            "system_prompt": self.SYSTEM_PROMPT
        }
    
    @classmethod
    def from_dict(cls, dados: dict) -> 'ChatSession':
        """
        Cria uma sessão a partir de um dicionário serializado.
        
        Args:
            dados: Dicionário com dados da sessão
            
        Returns:
            Nova instância de ChatSession
        """
        sessao = cls(max_mensagens=dados.get("max_mensagens"))
        sessao.historico = dados.get("historico", [])
        return sessao
