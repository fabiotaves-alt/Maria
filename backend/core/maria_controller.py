"""
Controller — lógica de negócio da MARIA.

Classe `MariaController` (e dependências) movida integralmente de
`backend/main.py` na divisão de módulos — sem alterações de lógica.
"""

import logging
from datetime import datetime

from backend.core.config import MAX_MENSAGENS_HISTORICO
from backend.core.llama_client import LlamaClient as OllamaClient
from backend.core.chat_session import ChatSession, interpretar_confirmacao
from backend.core.tools_schema import TOOLS_SCHEMA, executar_ferramenta_real
from backend.core.session_storage import salvar_sessao, listar_sessoes_salvas, carregar_sessao
from backend.core.tool_chaining import encadear_leitura_stream

logger = logging.getLogger(__name__)


class MariaController:
    """
    Encapsula toda a lógica de negócio da MARIA:
    conexão com Ollama, sessão de chat, ferramentas e persistência.
    """

    def __init__(self, modelo: str | None = None):
        self.cliente: OllamaClient | None = None  # type: ignore[valid-type]
        self.sessao: ChatSession | None = None
        self.nome_sessao: str = ""
        self._tool_call_final = None
        self._resposta_textual = ""
        self.modelo = modelo

    # ── Ciclo de vida ─────────────────────────────────────────

    def inicializar(self):
        """Cria cliente, sessão e define nome do arquivo de persistência."""
        self.cliente = OllamaClient(model=self.modelo) if self.modelo else OllamaClient()  # LlamaClient
        self.sessao = ChatSession(max_mensagens=MAX_MENSAGENS_HISTORICO)
        self.nome_sessao = self._gerar_nome_sessao()
        self._tool_call_final = None
        self._resposta_textual = ""

    def aquecer_modelo(self) -> None:
        """
        Envia uma mensagem mínima ao modelo para forçar o carregamento em
        memória antes da primeira interação real do usuário. Best-effort:
        falhas aqui não interrompem a aplicação, pois o mesmo erro será
        reportado de forma amigável na primeira mensagem real, se persistir.
        """
        try:
            self.cliente.enviar_mensagem(
                mensagens=[{"role": "user", "content": "Responda apenas com a palavra ok."}],
                tools=None,
                stream=False,
            )
        except Exception as error:
            logger.warning(f"Aquecimento do modelo falhou (não crítico): {error}")

    def finalizar(self):
        """Cleanup opcional ao encerrar."""
        pass

    # ── Sessão e persistência ─────────────────────────────────

    @staticmethod
    def _gerar_nome_sessao() -> str:
        return f"sessao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    def _salvar_silenciosamente(self):
        try:
            salvar_sessao(self.sessao.to_dict(), self.nome_sessao)
        except (PermissionError, OSError) as error:
            logger.warning(f"Falha ao salvar sessão automaticamente: {error}")
            print(f"\n[AVISO] Não foi possível salvar a sessão automaticamente: {error}")

    def listar_sessoes(self):
        """Retorna lista de sessões salvas (mais recentes primeiro)."""
        return listar_sessoes_salvas()

    def retomar_sessao(self, indice: int) -> tuple[bool, str]:
        """
        Retoma uma sessão salva pelo índice (1-based).
        Retorna (sucesso, mensagem).
        """
        sessoes = listar_sessoes_salvas()
        if not sessoes:
            return False, "Nenhuma sessão salva encontrada."

        try:
            info = sessoes[indice - 1]
        except IndexError:
            return False, "Índice inválido."

        try:
            dados = carregar_sessao(info["caminho"])
            self.sessao = ChatSession.from_dict(dados)
            self.nome_sessao = info["nome_arquivo"]
            return (
                True,
                f"Sessão '{info['nome_arquivo']}' retomada com "
                f"{self.sessao.contar_mensagens()} mensagem(ns)."
            )
        except ValueError as error:
            return False, f"[ERRO] Não foi possível retomar a sessão: {error}"

    # ── Estado da conversa ────────────────────────────────────

    def tem_acao_pendente(self) -> bool:
        return self.sessao.tem_acao_pendente()

    def limpar_acao_pendente(self):
        self.sessao.limpar_acao_pendente()
        self.sessao.tentativas_confirmacao_ambigua = 0

    def limpar_historico(self):
        self.sessao.limpar_historico()
        self.sessao.limpar_acao_pendente()

    # ── Envio de mensagens ────────────────────────────────────

    def enviar_mensagem(self, entrada: str):
        """
        Prepara o envio da mensagem ao modelo, encadeando automaticamente
        ferramentas de LEITURA (sem confirmação) até MAX_PASSOS_LEITURA vezes.
        Retorna um generator que yield pares (chunk_texto, tool_chunk); o
        tool_chunk só vem preenchido no último item — com uma ferramenta de
        ESCRITA pendente (se houver) ou None.
        """
        historico_atual = self.sessao.get_historico_com_system()
        self.sessao.adicionar_mensagem("user", entrada)
        self._tool_call_final = None
        self._resposta_textual = ""

        return self._gerar_resposta_com_encadeamento(entrada, historico_atual)

    def _gerar_resposta_com_encadeamento(self, entrada: str, historico_atual: list[dict]):
        """
        Generator interno: chama o modelo e delega o encadeamento de leitura
        (listar_arquivos/resumir_documento) ao módulo compartilhado
        core.tool_chaining.encadear_leitura_stream, usado também pelo
        benchmark (MariaRunner) para garantir comportamento idêntico.
        """
        tool_call_atual = None

        for chunk, tool_chunk in self.cliente.chat_com_tools_stream(
            mensagem_usuario=entrada,
            historico=historico_atual,
            tools=TOOLS_SCHEMA
        ):
            if chunk is not None:
                yield chunk, None
            if tool_chunk is not None:
                tool_call_atual = tool_chunk

        historico_continuacao = self.sessao.get_historico_com_system()
        yield from encadear_leitura_stream(
            self.cliente, historico_continuacao, tool_call_atual, TOOLS_SCHEMA
        )

    def processar_chunk(self, chunk, tool_chunk):
        """Acumula chunks durante o streaming."""
        if chunk is not None:
            self._resposta_textual += chunk
        if tool_chunk is not None:
            self._tool_call_final = tool_chunk

    def finalizar_mensagem(self) -> tuple[bool, dict | None]:
        """
        Finaliza o processamento após o streaming.
        Registra no histórico, salva sessão e retorna se há tool call pendente.
        """
        if self._tool_call_final:
            self.sessao.definir_acao_pendente(self._tool_call_final)
            if self._resposta_textual.strip():
                self.sessao.adicionar_mensagem("assistant", self._resposta_textual)
            self._salvar_silenciosamente()
            return True, self._tool_call_final

        if self._resposta_textual.strip():
            self.sessao.adicionar_mensagem("assistant", self._resposta_textual)
        self._salvar_silenciosamente()
        return False, None

    # ── Confirmação de ações ──────────────────────────────────

    def get_mensagem_confirmacao(self) -> str:
        """Gera mensagem amigável de confirmação para o usuário."""
        acao = self.sessao.acao_pendente
        nome = acao.get("name", "")
        args = acao.get("arguments", {})

        if nome == "criar_planilha":
            nome_arquivo = args.get("nome_arquivo", "planilha")
            colunas = args.get("colunas", [])
            lista = ", ".join(colunas) if colunas else "sem colunas definidas"
            return (
                f'Entendi! Vou criar uma planilha chamada "{nome_arquivo}" '
                f'com as colunas: {lista}.\n'
                f'Posso seguir com a criação? (responda sim ou não)'
            )

        if nome == "criar_documento":
            nome_arquivo = args.get("nome_arquivo", "documento")
            titulo = args.get("titulo", "Sem título")
            conteudo = args.get("conteudo", "")
            preview = conteudo[:80].strip()
            if len(conteudo) > 80:
                preview += "..."
            preview_texto = f'\nInício do conteúdo: "{preview}"' if preview else ""
            return (
                f'Entendi! Vou criar um documento chamado "{nome_arquivo}" '
                f'com o título "{titulo}".{preview_texto}\n'
                f'Posso seguir com a criação? (responda sim ou não)'
            )

        if nome == "editar_planilha":
            nome_arquivo = args.get("nome_arquivo", "planilha")
            colunas = args.get("colunas", [])
            lista = ", ".join(colunas) if colunas else "sem colunas definidas"
            qtd = len(args.get("linhas") or [])
            return (
                f'Entendi! Vou SOBRESCREVER a planilha "{nome_arquivo}" '
                f'com as colunas: {lista} ({qtd} linha(s) de dados).\n'
                f'Esta ação substitui o conteúdo atual do arquivo. Posso seguir? (responda sim ou não)'
            )

        return f'Vou executar a ação "{nome}". Posso prosseguir? (responda sim ou não)'

    def processar_confirmacao(self, entrada: str) -> tuple[bool | None, str]:
        """
        Processa a resposta de confirmação do usuário.
        Retorna (status, mensagem):
            status=True  → confirmado e executado
            status=False → negado ou cancelado
            status=None  → ambíguo (perguntar novamente)
        """
        resultado = interpretar_confirmacao(entrada)

        if resultado is True:
            try:
                nome_acao = self.sessao.acao_pendente["name"]
                argumentos = self.sessao.acao_pendente["arguments"]
                caminho = executar_ferramenta_real(nome_acao, argumentos)
                self.sessao.adicionar_mensagem("assistant", caminho)
                self.sessao.limpar_acao_pendente()
                self._salvar_silenciosamente()
                return True, caminho
            except (PermissionError, OSError, ValueError) as e:
                logger.error(f"Erro ao executar ferramenta: {e}")
                self.sessao.limpar_acao_pendente()
                return False, f"[ERRO] Não foi possível criar o arquivo: {e}"
            except Exception as e:
                logger.error(f"Erro inesperado ao executar ferramenta: {e}")
                self.sessao.limpar_acao_pendente()
                return False, f"[ERRO] Ocorreu um erro inesperado: {e}"

        if resultado is False:
            self.sessao.limpar_acao_pendente()
            return False, "Ação cancelada."

        # Ambíguo
        self.sessao.tentativas_confirmacao_ambigua += 1
        if self.sessao.tentativas_confirmacao_ambigua >= 2:
            self.sessao.limpar_acao_pendente()
            return False, "Não consegui confirmar, cancelando a ação por segurança."
        return None, "Não entendi. Você confirma a criação? Responda sim ou não."
