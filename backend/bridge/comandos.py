"""Protocolo de comandos do bridge — compartilhado entre o loop stdin/stdout
(`_modo_bridge`) e o servidor HTTP (`_criar_app_http`).

Funções movidas integralmente de `backend/main.py` na divisão de módulos —
sem alterações de lógica.
"""

import json
import logging
import os
import platform
import re
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

from backend.core.config import LLAMA_MODEL
from backend.core.paths import RAIZ_MONOREPO
from backend.database.connection import get_connection

logger = logging.getLogger(__name__)


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


def _cmd_ping(controller, payload):
    return "ok", "pong", None


def _cmd_status(controller, payload):
    dados_status = _get_system_status()
    dados_status["modelo"] = controller.modelo or LLAMA_MODEL
    return "ok", dados_status, None


def _cmd_analisar_arquivo(controller, payload):
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


def _cmd_analisar_dados(controller, payload):
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

def _cmd_upload_arquivo(controller, payload):
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


def _cmd_transcrever_audio(controller, payload):
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
            str(Path(RAIZ_MONOREPO) / "bin"),
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

def _cmd_chat(controller, payload):
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


def _cmd_encerrar(controller, payload):
    return "ok", "encerrando", None


def _cmd_limpar_conversa(controller, payload):
    controller.sessao.limpar_historico()
    return "ok", "conversa limpa", None


def _cmd_exportar_conversa(controller, payload):
    formato = payload.get("formato", "txt")
    from backend.core.session_storage import exportar_sessao
    try:
        arquivo_saida = exportar_sessao(controller.sessao, formato=formato)
        return "ok", f"Exportado: {arquivo_saida}", None
    except Exception as error:
        logger.error(f"Erro ao exportar conversa: {error}")
        return "erro", None, str(error)


def _cmd_listar_sessoes(controller, payload):
    from backend.core.session_storage import listar_sessoes_salvas
    return "ok", listar_sessoes_salvas(), None


def _cmd_carregar_sessao(controller, payload):
    nome = payload.get("nome", "")
    if not nome:
        return "erro", None, "Campo 'nome' vazio."
    from backend.core.session_storage import carregar_sessao, listar_sessoes_salvas
    try:
        # Aceita nome_arquivo (ex.: 'sessao_....json') ou caminho completo.
        caminho = nome
        if not os.path.isabs(caminho) and not Path(caminho).exists():
            for info in listar_sessoes_salvas():
                if info["nome_arquivo"] == nome:
                    caminho = info["caminho"]
                    break

        dados = carregar_sessao(caminho)
        historico = dados.get("historico", []) if isinstance(dados, dict) else []
        mensagens = [
            {"role": m.get("role"), "conteudo": m.get("content", m.get("conteudo", ""))}
            for m in historico
        ]
        return "ok", mensagens, None
    except Exception as error:
        logger.error(f"Erro ao carregar sessão: {error}")
        return "erro", None, str(error)

def _cmd_salvar_memoria(controller, payload):
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


def _cmd_listar_memoria(controller, payload):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, fato, categoria, relevancia FROM memoria ORDER BY criado_em DESC")
        rows = cursor.fetchall()
        memorias = [
            {"id": row["id"], "fato": row["fato"], "categoria": row["categoria"], "relevancia": row["relevancia"]}
            for row in rows
        ]
        return "ok", memorias, None
    except Exception as error:
        logger.error(f"Erro ao listar memória: {error}")
        return "erro", None, str(error)


def _cmd_deletar_memoria(controller, payload):
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


def _cmd_limpar_memorias(controller, payload):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memoria")
        conn.commit()
        return "ok", "memórias limpas", None
    except Exception as error:
        logger.error(f"Erro ao limpar memórias: {error}")
        return "erro", None, str(error)

def _cmd_criar_automacao(controller, payload):
    nome = payload.get("nome", "")
    descricao = payload.get("descricao", "")
    passos = payload.get("passos", [])
    gatilho = payload.get("gatilho", "")
    acao = payload.get("acao", "")  # schema exige NOT NULL; pode evoluir para derivar de 'passos'
    if not nome:
        return "erro", None, "Campo 'nome' vazio."
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO automacoes (nome, descricao, gatilho, acao, passos_json) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, gatilho, acao, json.dumps(passos)),
        )
        conn.commit()
        return "ok", "automação criada", None
    except Exception as error:
        logger.error(f"Erro ao criar automação: {error}")
        return "erro", None, str(error)


def _cmd_listar_automacoes(controller, payload):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, descricao, passos_json, gatilho, ativo, criado_em FROM automacoes ORDER BY criado_em DESC"
        )
        colunas = ["id", "nome", "descricao", "passos", "gatilho", "ativa", "criado_em"]
        automacoes = [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
        return "ok", automacoes, None
    except Exception as error:
        logger.error(f"Erro ao listar automações: {error}")
        return "erro", None, str(error)


def _cmd_deletar_automacao(controller, payload):
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


def _cmd_toggle_automacao(controller, payload):
    automacao_id = payload.get("id")
    if automacao_id is None:
        return "erro", None, "Campo 'id' vazio."
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE automacoes SET ativo = NOT ativo WHERE id = ?", (automacao_id,))
        conn.commit()
        cursor.execute("SELECT ativo FROM automacoes WHERE id = ?", (automacao_id,))
        resultado = cursor.fetchone()
        return "ok", {"ativa": bool(resultado[0]) if resultado else False}, None
    except Exception as error:
        logger.error(f"Erro ao toggle automação: {error}")
        return "erro", None, str(error)


_COMANDOS = {
    "ping": _cmd_ping,
    "status": _cmd_status,
    "analisar_arquivo": _cmd_analisar_arquivo,
    "analisar_dados": _cmd_analisar_dados,
    "upload_arquivo": _cmd_upload_arquivo,
    "transcrever_audio": _cmd_transcrever_audio,
    "chat": _cmd_chat,
    "encerrar": _cmd_encerrar,
    "limpar_conversa": _cmd_limpar_conversa,
    "exportar_conversa": _cmd_exportar_conversa,
    "listar_sessoes": _cmd_listar_sessoes,
    "carregar_sessao": _cmd_carregar_sessao,
    "salvar_memoria": _cmd_salvar_memoria,
    "listar_memoria": _cmd_listar_memoria,
    "deletar_memoria": _cmd_deletar_memoria,
    "limpar_memorias": _cmd_limpar_memorias,
    "criar_automacao": _cmd_criar_automacao,
    "listar_automacoes": _cmd_listar_automacoes,
    "deletar_automacao": _cmd_deletar_automacao,
    "toggle_automacao": _cmd_toggle_automacao,
}


def _despachar_comando(controller: "MariaController", comando: str, payload: dict) -> tuple[str, object, str | None]:
    """
    Executa um comando do protocolo bridge e retorna (status, dados, mensagem_erro).
    Compartilhado entre o loop stdin/stdout (_modo_bridge) e o servidor HTTP (_criar_app_http).
    O comando "encerrar" NÃO decide aqui se o processo deve parar — quem chama trata isso.
    """
    handler = _COMANDOS.get(comando)
    if handler is None:
        return "erro", None, f"Comando desconhecido: {comando}"
    return handler(controller, payload)
