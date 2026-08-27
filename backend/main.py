"""
Script principal da MARIA - Assistente de IA de Escritório.

Responsabilidades:
    - Inicializar o controller (lógica de negócio)
    - Delegar toda a interface para ui_terminal.InterfaceTerminal
    - Encapsular: OllamaClient, ChatSession, ferramentas, persistência

Uso:
    python main.py
"""

import sys
import json
import argparse
import logging
import os
import platform
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None


# Garantir que a raiz do monorepo esteja no sys.path quando o script é
# executado diretamente (ex.: python backend/main.py --bridge), permitindo
# imports como `from backend.core.config import ...` sejam resolvidos.
_RAIZ_MONOREPO = str(Path(__file__).resolve().parent.parent)
if _RAIZ_MONOREPO not in sys.path:
    sys.path.insert(0, _RAIZ_MONOREPO)


from backend.core.config import (
    LOG_LEVEL,
    MAX_MENSAGENS_HISTORICO,
)
from backend.core.ollama_client import OllamaClient
from backend.core.chat_session import ChatSession, interpretar_confirmacao
from backend.core.tools_schema import (
    TOOLS_SCHEMA,
    executar_ferramenta_real,
)
from backend.core.session_storage import salvar_sessao, listar_sessoes_salvas, carregar_sessao
from backend.core.tool_chaining import encadear_leitura_stream

from backend.ui_terminal import InterfaceTerminal


# ───────────────────────────────────────────────────────────────
# Logging
# ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Controller — lógica de negócio
# ═══════════════════════════════════════════════════════════════

class MariaController:
    """
    Encapsula toda a lógica de negócio da MARIA:
    conexão com Ollama, sessão de chat, ferramentas e persistência.
    """

    def __init__(self, modelo: str | None = None):
        self.cliente: OllamaClient | None = None
        self.sessao: ChatSession | None = None
        self.nome_sessao: str = ""
        self._tool_call_final = None
        self._resposta_textual = ""
        self.modelo = modelo

    # ── Ciclo de vida ─────────────────────────────────────────

    def inicializar(self):
        """Cria cliente, sessão e define nome do arquivo de persistência."""
        self.cliente = OllamaClient(model=self.modelo) if self.modelo else OllamaClient()
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


# ═══════════════════════════════════════════════════════════════
# Modo bridge (integração JavaFX ↔ Python)
# ═══════════════════════════════════════════════════════════════

def _responder_bridge(identificador: str, status: str, dados=None, mensagem_erro: str | None = None):
    """Envia uma resposta JSON por linha no stdout."""
    resposta = {
        "id": identificador,
        "status": status,
        "dados": dados,
        "mensagemErro": mensagem_erro,
    }
    print(json.dumps(resposta, ensure_ascii=False), flush=True)


def _get_system_status():
    """Obtém métricas reais de CPU, RAM e GPU do sistema."""
    if psutil is None:
        return {
            "cpu": 0.0,
            "ram": 0.0,
            "gpu": 0.0,
            "plataforma": platform.system(),
            "aviso": "psutil não instalado"
        }
    
    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram_percent = psutil.virtual_memory().percent
    
    # GPU é opcional — tentar via pynvml se disponível (NVIDIA)
    gpu_percent = 0.0
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_percent = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
        pynvml.nvmlShutdown()
    except Exception:
        pass  # Sem GPU NVIDIA ou pynvml não instalado
    
    return {
        "cpu": cpu_percent,
        "ram": ram_percent,
        "gpu": gpu_percent,
        "plataforma": platform.system()
    }


def _modo_bridge(modelo: str | None = None):
    """
    Modo de integração com o frontend JavaFX.

    Lê requisições JSON por linha do stdin no formato:
        {"id": "...", "comando": "...", "payload": {...}}

    Comandos suportados:
        ping       → responde {"status": "ok", "dados": "pong"}
        chat       → envia mensagem ao modelo e responde com o texto final
        encerrar   → encerra o processo

    Responde JSON por linha no stdout no formato:
        {"id": "...", "status": "ok|erro", "dados": ..., "mensagemErro": ...}
    """
    controller = MariaController(modelo=modelo)
    try:
        controller.inicializar()
    except Exception as error:
        _responder_bridge("", "erro", mensagem_erro=f"Falha ao inicializar: {error}")
        return

    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue

        try:
            requisicao = json.loads(linha)
        except json.JSONDecodeError as error:
            _responder_bridge("", "erro", mensagem_erro=f"JSON inválido: {error}")
            continue

        identificador = requisicao.get("id", "")
        comando = requisicao.get("comando", "")
        payload = requisicao.get("payload") or {}

        if comando == "ping":
            _responder_bridge(identificador, "ok", dados="pong")

        elif comando == "status":
            # Retorna métricas reais de CPU/RAM/GPU
            dados_status = _get_system_status()
            # Adicionar modelo atual ao status
            dados_status["modelo"] = controller.modelo or OLLAMA_MODEL
            _responder_bridge(identificador, "ok", dados=dados_status)

        elif comando == "analisar_arquivo":
            # Handler para analisar arquivo (docx, xlsx, pdf, txt)
            caminho = payload.get("caminho", "")
            if not caminho:
                _responder_bridge(identificador, "erro", mensagem_erro="Campo 'caminho' vazio.")
                continue
            
            try:
                from backend.core.file_utils import ler_documento
                from backend.core.excel_handler import ler_planilha_resumo
                
                caminho_lower = caminho.lower()
                if caminho_lower.endswith(('.docx', '.txt', '.md', '.csv', '.log')):
                    doc = ler_documento(caminho)
                    resultado = f"Arquivo: {doc['nome']}\\nConteúdo (parcial):\\n{doc['texto'][:500]}"
                    if doc['truncado']:
                        resultado += f"\\n[Conteúdo truncado em {doc['total_chars']} caracteres]"
                elif caminho_lower.endswith(('.xlsx', '.xls')):
                    resumo = ler_planilha_resumo(caminho)
                    resultado = f"Planilha: {caminho}\\n{resumo}"
                else:
                    resultado = f"Tipo de arquivo não suportado: {caminho}"
                
                _responder_bridge(identificador, "ok", dados=resultado)
            except Exception as error:
                logger.error(f"Erro ao analisar arquivo: {error}")
                _responder_bridge(identificador, "erro", mensagem_erro=str(error))

        elif comando == "analisar_dados":
            # Handler para analisar dados de planilha
            caminho = payload.get("caminho", "")
            if not caminho:
                _responder_bridge(identificador, "erro", mensagem_erro="Campo 'caminho' vazio.")
                continue
            
            try:
                from backend.core.excel_handler import ler_planilha_resumo
                resumo = ler_planilha_resumo(caminho)
                _responder_bridge(identificador, "ok", dados=resumo)
            except Exception as error:
                logger.error(f"Erro ao analisar dados: {error}")
                _responder_bridge(identificador, "erro", mensagem_erro=str(error))

        elif comando == "upload_arquivo":
            # Handler para upload de arquivo (copia para pasta de arquivos gerados)
            caminho = payload.get("caminho", "")
            if not caminho:
                _responder_bridge(identificador, "erro", mensagem_erro="Campo 'caminho' vazio.")
                continue
            
            try:
                import shutil
                from pathlib import Path
                from backend.core.file_utils import garantir_pasta_arquivos
                
                origem = Path(caminho)
                if not origem.exists():
                    raise ValueError(f"Arquivo não encontrado: {caminho}")
                
                pasta_destino = Path(garantir_pasta_arquivos())
                nome_destino = pasta_destino / origem.name
                
                # Gerar nome único se já existir
                contador = 1
                while nome_destino.exists():
                    nome_destino = pasta_destino / f"{origem.stem}_{contador}{origem.suffix}"
                    contador += 1
                
                shutil.copy2(origem, nome_destino)
                _responder_bridge(identificador, "ok", dados=f"Arquivo copiado para: {nome_destino}")
            except Exception as error:
                logger.error(f"Erro ao fazer upload: {error}")
                _responder_bridge(identificador, "erro", mensagem_erro=str(error))

        elif comando == "transcrever_audio":
            # Handler para transcrever áudio usando whisper.cpp (binário externo)
            caminho = payload.get("caminho", "")
            if not caminho:
                _responder_bridge(identificador, "erro", mensagem_erro="Campo 'caminho' vazio.")
                continue
            
            try:
                import subprocess
                from pathlib import Path
                
                audio_path = Path(caminho)
                if not audio_path.exists():
                    raise ValueError(f"Arquivo de áudio não encontrado: {caminho}")
                
                # Tentar usar whisper.cpp como binário externo (mais leve que openai-whisper)
                # O usuário deve ter whisper.cpp instalado e no PATH
                whisper_bin = os.getenv("WHISPER_BIN", "whisper-main")
                
                try:
                    # whisper.cpp: whisper-main -f audio.wav -otxt -of output.txt
                    resultado = subprocess.run(
                        [whisper_bin, "-f", str(audio_path), "-otxt", "-of", "temp_whisper"],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    # Ler arquivo de saída do whisper.cpp
                    output_file = Path("temp_whisper.txt")
                    if output_file.exists():
                        transcricao = output_file.read_text(encoding="utf-8")
                        output_file.unlink()  # Remover arquivo temporário
                    else:
                        transcricao = "[Transcrição não gerada - verificar whisper.cpp]"
                    
                    # Limpar arquivo de áudio temporário
                    audio_path.unlink(missing_ok=True)
                    
                except FileNotFoundError:
                    # Fallback: mensagem informativa se whisper.cpp não estiver disponível
                    transcricao = f"[Whisper.cpp não encontrado. Instale whisper.cpp ou use o áudio: {audio_path.name}]"
                    # Manter arquivo para debug
                    logger.warning(f"whisper.cpp não encontrado. Arquivo mantido: {audio_path}")
                
                _responder_bridge(identificador, "ok", dados=transcricao)
            except subprocess.TimeoutExpired:
                _responder_bridge(identificador, "erro", mensagem_erro="Tempo esgotado na transcrição")
            except Exception as error:
                logger.error(f"Erro ao transcrever áudio: {error}")
                _responder_bridge(identificador, "erro", mensagem_erro=str(error))

        elif comando == "chat":
            mensagem = payload.get("mensagem", "")
            if not mensagem:
                _responder_bridge(identificador, "erro", mensagem_erro="Campo 'mensagem' vazio.")
                continue

            try:
                stream = controller.enviar_mensagem(mensagem)
                texto_final = ""
                tool_call_final = None
                for chunk, tool_chunk in stream:
                    if chunk is not None:
                        texto_final += chunk
                    if tool_chunk is not None:
                        tool_call_final = tool_chunk
                    controller.processar_chunk(chunk, tool_chunk)

                tem_tool, info = controller.finalizar_mensagem()
                if tem_tool:
                    texto_final += "\n\n" + controller.get_mensagem_confirmacao()

                _responder_bridge(identificador, "ok", dados=texto_final)
            except Exception as error:
                logger.error(f"Erro no modo bridge (chat): {error}")
                _responder_bridge(identificador, "erro", mensagem_erro=str(error))

        elif comando == "encerrar":
            _responder_bridge(identificador, "ok", dados="encerrando")
            break

        else:
            _responder_bridge(identificador, "erro", mensagem_erro=f"Comando desconhecido: {comando}")


# ═══════════════════════════════════════════════════════════════
# Ponto de entrada
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="MARIA - Assistente de IA de Escritório")
    parser.add_argument(
        "-m", "--modelo",
        dest="modelo",
        default=None,
        help="Nome do modelo Ollama a usar nesta execução (ex: qwen3:8b). "
             "Se omitido, usa OLLAMA_MODEL do ambiente/config.py."
    )
    parser.add_argument(
        "--bridge",
        action="store_true",
        help="Executa em modo bridge (JSON por linha no stdin/stdout) para integração com o frontend JavaFX."
    )
    args = parser.parse_args()

    # Verificar dependências
    try:
        import requests  # noqa: F401
    except ImportError:
        print("\n[ERRO] A biblioteca 'requests' não está instalada.")
        print("Instale com: pip install requests\n")
        sys.exit(1)

    # Modo bridge (frontend JavaFX)
    if args.bridge:
        _modo_bridge(modelo=args.modelo)
        return

    # Criar controller e interface
    controller = MariaController(modelo=args.modelo)
    interface = InterfaceTerminal(controller, imagem_banner="maria_opening.png")

    # Delegar totalmente para a interface
    interface.iniciar()


if __name__ == "__main__":
    main()