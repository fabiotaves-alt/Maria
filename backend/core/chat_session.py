"""
Módulo que gerencia a sessão de chat com histórico de contexto.
Responsável por manter o histórico da conversa e limitar o número de mensagens
para evitar degradação de performance.
"""

from backend.core.config import MARIA_SYSTEM_PROMPT
from backend.core.confirmacao import ConfirmacaoAcao, interpretar_confirmacao


class ChatSession:
    """
    Gerencia uma sessão de chat com histórico de mensagens.
    
    Atributos:
        historico (list[dict]): Lista de mensagens no formato {"role": str, "content": str}
        max_mensagens (int): Número máximo de mensagens no histórico
        system_prompt (str): Prompt de sistema que define a identidade da MARIA
    """
    
    # System prompt da MARIA carregado do ARQUIVO EXTERNO
    # backend/core/system_prompt.txt (via backend.core.config.MARIA_SYSTEM_PROMPT).
    # Alias mantido por compatibilidade com código legado; o prompt é injetado
    # dinamicamente por get_historico_com_system(), nunca armazenado no histórico.
    SYSTEM_PROMPT: str = MARIA_SYSTEM_PROMPT

    def __init__(self, max_mensagens: int = None):
        """
        Inicializa uma nova sessão de chat.
        
        Args:
            max_mensagens: Número máximo de mensagens no histórico.
                          Se None, usa o valor de MAX_MENSAGENS_HISTORICO do config.py
        """
        from backend.core.config import MAX_MENSAGENS_HISTORICO
        self.max_mensagens = max_mensagens if max_mensagens is not None else MAX_MENSAGENS_HISTORICO
        self.historico: list[dict[str, str]] = []
        self._confirmacao = ConfirmacaoAcao()
    
    @property
    def acao_pendente(self) -> dict | None:
        """Ação pendente aguardando confirmação (compatibilidade)."""
        return self._confirmacao.tool_call

    @property
    def tentativas_confirmacao_ambigua(self) -> int:
        """Contador de respostas ambíguas consecutivas (compatibilidade)."""
        return self._confirmacao.tentativas_ambiguas

    @tentativas_confirmacao_ambigua.setter
    def tentativas_confirmacao_ambigua(self, valor: int) -> None:
        self._confirmacao.tentativas_ambiguas = valor

    def definir_acao_pendente(self, tool_call: dict) -> None:
        """
        Armazena uma ação pendente aguardando confirmação do usuário.
        
        Args:
            tool_call: Dicionário com 'name' e 'arguments' da tool call
        """
        self._confirmacao.definir(tool_call)
    
    def limpar_acao_pendente(self) -> None:
        """Limpa a ação pendente e zera o contador de ambiguidade."""
        self._confirmacao.limpar()
    
    def tem_acao_pendente(self) -> bool:
        """
        Verifica se há uma ação pendente aguardando confirmação.
        
        Returns:
            True se houver ação pendente, False caso contrário
        """
        return self._confirmacao.tem()
    
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
