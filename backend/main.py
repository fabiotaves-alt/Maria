"""
Script principal da MARIA - Assistente de IA de Escritório.

Responsabilidades:
    - Inicializar o controller (lógica de negócio)
    - Delegar toda a interface para ui_terminal.InterfaceTerminal
    - Encapsular: LlamaClient, ChatSession, ferramentas, persistência

Uso:
    python main.py
"""

import sys
import json
import argparse
import logging
import os
import platform
import re
import secrets
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
    LLAMA_MODEL,
    MARIA_ENV,
)
from backend.core.llama_client import LlamaClient as OllamaClient
from backend.core.chat_session import ChatSession, interpretar_confirmacao
from backend.core.tools_schema import (
    TOOLS_SCHEMA,
    executar_ferramenta_real,
)
from backend.database.connection import get_connection
from backend.core.session_storage import salvar_sessao, listar_sessoes_salvas, carregar_sessao
from backend.core.tool_chaining import encadear_leitura_stream

from backend.ui_terminal import InterfaceTerminal


# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════
# Controller — lógica de negócio
# ═════════════════════════════════════════════════════════════

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


# ═════════════════════════════════════════════════════════════
# Modo bridge (integração JavaFX ↔ Python)
# ═════════════════════════════════════════════════════════════

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

    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        ram_percent = psutil.virtual_memory().percent
    except Exception as e:
        logger.warning(f"Erro ao obter recursos: {e}")
        cpu_percent = 0.0
        ram_percent = 0.0

    # GPU é opcional — tentar via pynvml se disponível (NVIDIA)
    gpu_percent = 0.0
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_percent = float(pynvml.nvmlDeviceGetUtilizationRates(handle).gpu)
        pynvml.nvmlShutdown()
    except Exception:
        pass

    return {
        "cpu": round(cpu_percent, 1),
        "ram": round(ram_percent, 1),
        "gpu": round(gpu_percent, 1),
        "plataforma": platform.system()
    }


def _despachar_comando(controller: "MariaController", comando: str, payload: dict) -> tuple[str, object, str | None]:
    """
    Executa um comando do protocolo bridge e retorna (status, dados, mensagem_erro).
    Compartilhado entre o loop stdin/stdout (_modo_bridge) e o servidor HTTP (_criar_app_http).
    O comando "encerrar" NÃO decide aqui se o processo deve parar — quem chama trata isso.
    """
    if comando == "ping":
        return "ok", "pong", None

    elif comando == "status":
        dados_status = _get_system_status()
        dados_status["modelo"] = controller.modelo or LLAMA_MODEL
        return "ok", dados_status, None

    elif comando == "analisar_arquivo":
        caminho = payload.get("caminho", "")
        if not caminho:
            return "erro", None, "Campo 'caminho' vazio."
        try:
            from backend.core.file_utils import ler_documento
            from backend.core.excel_handler import ler_planilha_resumo

            caminho_lower = caminho.lower()
            if caminho_lower.endswith(('.docx', '.txt', '.md', '.csv', '.log')):
                doc = ler_documento(caminho)
                resultado = f"Arquivo: {doc['nome']}\nConteúdo (parcial):\n{doc['texto'][:500]}"
                if doc['truncado']:
                    resultado += f"\n[Conteúdo truncado em {doc['total_chars']} caracteres]"
            elif caminho_lower.endswith(('.xlsx', '.xls')):
                resumo = ler_planilha_resumo(caminho)
                resultado = f"Planilha: {caminho}\n{resumo}"
            else:
                resultado = f"Tipo de arquivo não suportado: {caminho}"
            return "ok", resultado, None
        except Exception as error:
            logger.error(f"Erro ao analisar arquivo: {error}")
            return "erro", None, str(error)

    elif comando == "analisar_dados":
        caminho = payload.get("caminho", "")
        if not caminho:
            return "erro", None, "Campo 'caminho' vazio."
        try:
            from backend.core.excel_handler import ler_planilha_resumo
            resumo = ler_planilha_resumo(caminho)
            return "ok", resumo, None
        except Exception as error:
            logger.error(f"Erro ao analisar dados: {error}")
            return "erro", None, str(error)

    elif comando == "upload_arquivo":
        caminho = payload.get("caminho", "")
        if not caminho:
            return "erro", None, "Campo 'caminho' vazio."
        try:
            import shutil
            from pathlib import Path
            from backend.core.file_utils import garantir_pasta_arquivos

            origem = Path(caminho)
            if not origem.is_file():
                raise ValueError(f"Arquivo não encontrado ou caminho inválido: {caminho}")

            # Segurança: limite de tamanho para evitar cópias gigantes
            TAMANHO_MAXIMO = 100 * 1024 * 1024  # 100 MB
            if origem.stat().st_size > TAMANHO_MAXIMO:
                raise ValueError("Arquivo excede o tamanho máximo de 100 MB.")

            pasta_destino = Path(garantir_pasta_arquivos())
            nome_destino = pasta_destino / origem.name
            contador = 1
            while nome_destino.exists():
                nome_destino = pasta_destino / f"{origem.stem}_{contador}{origem.suffix}"
                contador += 1

            shutil.copy2(origem, nome_destino)
            logger.info("upload_arquivo: '%s' -> '%s'", origem, nome_destino)
            return "ok", f"Arquivo copiado para: {nome_destino}", None
        except Exception as error:
            logger.error(f"Erro ao fazer upload: {error}")
            return "erro", None, str(error)

    elif comando == "transcrever_audio":
        caminho = payload.get("caminho", "")
        if not caminho:
            return "erro", None, "Campo 'caminho' vazio."
        try:
            import shutil
            import subprocess
            from pathlib import Path
            from backend.core.file_utils import (
                garantir_pasta_arquivos,
                resolver_caminho_permitido,
            )

            audio_path = Path(caminho)
            if not audio_path.is_file():
                raise ValueError(f"Arquivo de áudio não encontrado: {caminho}")

            # Segurança: o áudio deve estar dentro das pastas permitidas.
            audio_path = resolver_caminho_permitido(str(audio_path))

            # Segurança: binário restrito a nome simples (sem caminho/argumentos).
            whisper_bin_nome = os.getenv("WHISPER_BIN", "whisper-main")
            if not re.fullmatch(r"[\w.-]+(\.exe)?", whisper_bin_nome):
                raise ValueError(
                    "WHISPER_BIN inválido: use apenas o nome do binário "
                    "(sem caminho ou argumentos)."
                )

            # Segurança: resolve via PATH mas EXIGE que o caminho resolvido
            # esteja dentro de um diretório explicitamente permitido,
            # rejeitando binários encontrados em diretórios genéricos do
            # PATH do usuário/sistema (mitiga PATH hijacking).
            caminho_resolvido = shutil.which(whisper_bin_nome)
            if not caminho_resolvido:
                raise ValueError(
                    f"Binário '{whisper_bin_nome}' não encontrado. "
                    "Instale whisper.cpp ou configure WHISPER_BIN."
                )

            dir_permitido_whisper = os.getenv(
                "WHISPER_ALLOWED_DIR",
                str(Path(_RAIZ_MONOREPO) / "bin"),
            )
            caminho_resolvido_abs = Path(caminho_resolvido).resolve()
            dir_permitido_abs = Path(dir_permitido_whisper).resolve()
            if not (
                caminho_resolvido_abs == dir_permitido_abs
                or caminho_resolvido_abs.is_relative_to(dir_permitido_abs)
            ):
                raise ValueError(
                    f"Binário resolvido fora do diretório permitido: "
                    f"{caminho_resolvido_abs}. Configure WHISPER_ALLOWED_DIR "
                    "ou instale o binário no diretório esperado do app."
                )
            whisper_bin = str(caminho_resolvido_abs)

            # Arquivos temporários de saída na pasta gerenciada
            saida_base = Path(garantir_pasta_arquivos()) / "temp_whisper"
            try:
                resultado = subprocess.run(
                    [whisper_bin, "-f", str(audio_path), "-otxt", "-of", str(saida_base)],
                    capture_output=True, text=True, timeout=60,
                )
                output_file = saida_base.with_suffix(".txt")
                if output_file.exists():
                    transcricao = output_file.read_text(encoding="utf-8")
                    output_file.unlink()
                else:
                    logger.warning(
                        "whisper.cpp não gerou saída (returncode=%s): %s",
                        resultado.returncode, resultado.stderr.strip()[:500],
                    )
                    transcricao = "[Transcrição não gerada - verificar whisper.cpp]"
                audio_path.unlink(missing_ok=True)
            except FileNotFoundError:
                transcricao = f"[Whisper.cpp não encontrado. Instale whisper.cpp ou use o áudio: {audio_path.name}]"
                logger.warning(f"whisper.cpp não encontrado. Arquivo mantido: {audio_path}")
            return "ok", transcricao, None
        except subprocess.TimeoutExpired:
            return "erro", None, "Tempo esgotado na transcrição"
        except Exception as error:
            logger.error(f"Erro ao transcrever áudio: {error}")
            return "erro", None, str(error)

    elif comando == "chat":
        mensagem = payload.get("mensagem", "")
        if not mensagem:
            return "erro", None, "Campo 'mensagem' vazio."
        try:
            stream = controller.enviar_mensagem(mensagem)
            texto_final = ""
            for chunk, tool_chunk in stream:
                if chunk is not None:
                    texto_final += chunk
                controller.processar_chunk(chunk, tool_chunk)

            tem_tool, info = controller.finalizar_mensagem()
            if tem_tool:
                texto_final += "\n\n" + controller.get_mensagem_confirmacao()
            return "ok", texto_final, None
        except Exception as error:
            logger.error(f"Erro no comando chat: {error}")
            return "erro", None, str(error)

    elif comando == "encerrar":
        return "ok", "encerrando", None

    elif comando == "limpar_conversa":
        controller.sessao.limpar_historico()
        return "ok", "conversa limpa", None

    elif comando == "exportar_conversa":
        formato = payload.get("formato", "txt")
        from backend.core.session_storage import exportar_sessao
        try:
            arquivo_saida = exportar_sessao(controller.sessao, formato=formato)
            return "ok", f"Exportado: {arquivo_saida}", None
        except Exception as error:
            logger.error(f"Erro ao exportar conversa: {error}")
            return "erro", None, str(error)

    elif comando == "listar_sessoes":
        from backend.core.session_storage import listar_sessoes_salvas
        return "ok", listar_sessoes_salvas(), None

    elif comando == "carregar_sessao":
        nome = payload.get("nome", "")
        from backend.core.session_storage import carregar_sessao
        try:
            sessao = carregar_sessao(nome)
            mensagens = [{"role": m["role"], "conteudo": m["content"]} for m in sessao.historico]
            return "ok", mensagens, None
        except Exception as error:
            logger.error(f"Erro ao carregar sessão: {error}")
            return "erro", None, str(error)

    elif comando == "salvar_memoria":
        fato = payload.get("fato", "")
        categoria = payload.get("categoria", "geral")
        relevancia = payload.get("relevancia", 1.0)
        if not fato:
            return "erro", None, "Campo 'fato' vazio."
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO memoria (fato, categoria, relevancia) VALUES (?, ?, ?)",
                (fato, categoria, relevancia),
            )
            conn.commit()
            return "ok", "memória salva", None
        except Exception as error:
            logger.error(f"Erro ao salvar memória: {error}")
            return "erro", None, str(error)

    elif comando == "listar_memoria":
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT fato, categoria, relevancia FROM memoria ORDER BY criado_em DESC")
            rows = cursor.fetchall()
            memorias = [
                {"fato": row["fato"], "categoria": row["categoria"], "relevancia": row["relevancia"]}
                for row in rows
            ]
            return "ok", memorias, None
        except Exception as error:
            logger.error(f"Erro ao listar memória: {error}")
            return "erro", None, str(error)

    elif comando == "deletar_memoria":
        memoria_id = payload.get("id")
        if memoria_id is None:
            return "erro", None, "Campo 'id' vazio."
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memoria WHERE id = ?", (memoria_id,))
            conn.commit()
            return "ok", "memória deletada", None
        except Exception as error:
            logger.error(f"Erro ao deletar memória: {error}")
            return "erro", None, str(error)

    elif comando == "limpar_memorias":
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memoria")
            conn.commit()
            return "ok", "memórias limpas", None
        except Exception as error:
            logger.error(f"Erro ao limpar memórias: {error}")
            return "erro", None, str(error)

    elif comando == "criar_automacao":
        nome = payload.get("nome", "")
        descricao = payload.get("descricao", "")
        passos = payload.get("passos", [])
        gatilho = payload.get("gatilho", "")
        if not nome:
            return "erro", None, "Campo 'nome' vazio."
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO automacoes (nome, descricao, passos_json, gatilho) VALUES (?, ?, ?, ?)",
                (nome, descricao, json.dumps(passos), gatilho),
            )
            conn.commit()
            return "ok", "automação criada", None
        except Exception as error:
            logger.error(f"Erro ao criar automação: {error}")
            return "erro", None, str(error)

    elif comando == "listar_automacoes":
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, descricao, passos_json, gatilho, ativa, criado_em FROM automacoes ORDER BY criado_em DESC"
            )
            colunas = ["id", "nome", "descricao", "passos", "gatilho", "ativa", "criado_em"]
            automacoes = [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
            return "ok", automacoes, None
        except Exception as error:
            logger.error(f"Erro ao listar automações: {error}")
            return "erro", None, str(error)

    elif comando == "deletar_automacao":
        automacao_id = payload.get("id")
        if automacao_id is None:
            return "erro", None, "Campo 'id' vazio."
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM automacoes WHERE id = ?", (automacao_id,))
            conn.commit()
            return "ok", "automação deletada", None
        except Exception as error:
            logger.error(f"Erro ao deletar automação: {error}")
            return "erro", None, str(error)

    elif comando == "toggle_automacao":
        automacao_id = payload.get("id")
        if automacao_id is None:
            return "erro", None, "Campo 'id' vazio."
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE automacoes SET ativa = NOT ativa WHERE id = ?", (automacao_id,))
            conn.commit()
            cursor.execute("SELECT ativa FROM automacoes WHERE id = ?", (automacao_id,))
            resultado = cursor.fetchone()
            return "ok", {"ativa": bool(resultado[0]) if resultado else False}, None
        except Exception as error:
            logger.error(f"Erro ao toggle automação: {error}")
            return "erro", None, str(error)

    else:
        return "erro", None, f"Comando desconhecido: {comando}"


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
    # Inicializar banco de dados
    from backend.database.schema import init_db

    try:
        init_db()
        logger.info("Banco de dados inicializado")
    except Exception as e:
        logger.warning(f"Falha ao inicializar DB: {e}")

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

        status, dados, mensagem_erro = _despachar_comando(controller, comando, payload)
        _responder_bridge(identificador, status, dados=dados, mensagem_erro=mensagem_erro)

        if comando == "encerrar":
            break


def _carregar_token_api() -> str:
    """
    Gera o token da API bridge HTTP e o persiste atomicamente em
    `shared/.bridge_token`, restringindo a permissão de leitura ao
    usuário atual (POSIX). O frontend Tauri relê este arquivo a cada
    chamada (ver `call_python_backend` em main.rs), portanto não é
    necessário nenhum mecanismo adicional de sincronização.
    """
    caminho = Path(_RAIZ_MONOREPO) / "frontend-tauri" / "shared" / ".bridge_token"
    token = secrets.token_hex(32)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    arquivo_temp = caminho.with_suffix(".tmp")
    try:
        arquivo_temp.write_text(token, encoding="utf-8")
        os.replace(arquivo_temp, caminho)  # rename atômico no mesmo filesystem
        if os.name == "posix":
            os.chmod(caminho, 0o600)
    finally:
        arquivo_temp.unlink(missing_ok=True)

    logger.info("Token da API bridge HTTP regenerado")
    return token


def _criar_app_http(controller: "MariaController", token: str):
    """
    App Flask que expõe o protocolo bridge via HTTP. Único endpoint POST /chat,
    aceitando {"id","comando","dados"} e respondendo {"id","status","dados","mensagemErro"}.
    Contrato consumido por frontend-tauri/src-tauri/src/main.rs (PythonRequest/PythonResponse).

    Segurança:
        - Autenticação obrigatória via header `Authorization: Bearer <token>`
          (/ping permanece aberto como health check, sem dados sensíveis).
        - CORS restrito às origens do frontend Tauri (dev e produção).
    """
    from flask import Flask, request, jsonify
    from flask_cors import CORS

    app = Flask(__name__)
    _ORIGENS_BASE = ["tauri://localhost", "http://tauri.localhost"]
    _ORIGENS_DEV_EXTRA = ["http://localhost:5173"]  # Vite dev server

    origens_cors = _ORIGENS_BASE + (_ORIGENS_DEV_EXTRA if MARIA_ENV == "development" else [])
    if MARIA_ENV != "development":
        logger.info("MARIA_ENV=%s: CORS restrito às origens de produção do Tauri.", MARIA_ENV)

    CORS(
        app,
        origins=origens_cors,
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.before_request
    def _exigir_autenticacao():
        """Rejeita requisições sem token válido (exceto /ping)."""
        if request.path == "/ping":
            return None
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or not secrets.compare_digest(auth[7:], token):
            logger.warning("Requisição sem token válido rejeitada (rota: %s)", request.path)
            return jsonify({"id": "", "status": "erro", "dados": None,
                            "mensagemErro": "Não autorizado: token inválido ou ausente."}), 401
        return None

    @app.route("/chat", methods=["POST"])
    def _rota_unica():
        corpo = request.get_json(silent=True) or {}
        identificador = corpo.get("id", "")
        comando = corpo.get("comando", "")
        payload = corpo.get("dados") or {}

        if not comando:
            return jsonify({"id": identificador, "status": "erro", "dados": None,
                             "mensagemErro": "Campo 'comando' vazio."}), 400

        status, dados, mensagem_erro = _despachar_comando(controller, comando, payload)
        return jsonify({"id": identificador, "status": status, "dados": dados,
                         "mensagemErro": mensagem_erro})

    @app.route("/ping", methods=["GET"])
    def _health_check():
        return jsonify({"status": "ok", "dados": "pong"})

    return app


def _modo_bridge_http(modelo: str | None = None, porta: int = 8081):
    from backend.database.schema import init_db
    try:
        init_db()
        logger.info("Banco de dados inicializado")
    except Exception as e:
        logger.warning(f"Falha ao inicializar DB: {e}")

    controller = MariaController(modelo=modelo)
    try:
        controller.inicializar()
    except Exception as error:
        logger.error(f"Falha ao inicializar controller: {error}")
        raise SystemExit(f"Falha ao inicializar: {error}")

    app = _criar_app_http(controller, _carregar_token_api())
    logger.info(f"Servidor HTTP bridge iniciado em http://127.0.0.1:{porta}")
    app.run(host="127.0.0.1", port=porta, debug=False, use_reloader=False)


# ═════════════════════════════════════════════════════════════
# Ponto de entrada
# ═════════════════════════════════════════════════════════════

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
    parser.add_argument(
        "--bridge-http",
        action="store_true",
        help="Executa em modo bridge HTTP (REST) para o frontend Tauri."
    )
    parser.add_argument(
        "--porta",
        type=int,
        default=8081,
        help="Porta do servidor HTTP quando --bridge-http é usado (padrão: 8081)."
    )
    args = parser.parse_args()

    # Verificar dependências
    try:
        import requests  # noqa: F401
    except ImportError:
        print("\n[ERRO] A biblioteca 'requests' não está instalada.")
        print("Instale com: pip install requests\n")
        sys.exit(1)

    # Modo bridge HTTP (frontend Tauri)
    if args.bridge_http:
        try:
            import flask  # noqa: F401
            import flask_cors  # noqa: F401
        except ImportError as e:
            print(f"\n[ERRO] Biblioteca faltando: {e}")
            print("Instale com: pip install flask flask-cors\n")
            sys.exit(1)
        _modo_bridge_http(modelo=args.modelo, porta=args.porta)
        return

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
