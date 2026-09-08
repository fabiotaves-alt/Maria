"""
Módulo para persistência de sessões de chat em disco no projeto MARIA.
"""

import os
import json
import glob
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _pasta_sessoes() -> str:
    """Lê a pasta de sessões no momento da chamada, inclusive em testes."""
    return os.getenv("PASTA_SESSOES", "sessoes_salvas")


def garantir_pasta_sessoes() -> str:
    pasta = _pasta_sessoes()
    os.makedirs(pasta, exist_ok=True)
    logger.debug(f"Pasta '{pasta}' garantida.")
    return os.path.abspath(pasta)


def salvar_sessao(sessao_dict: dict, nome_arquivo: str) -> str:
    pasta_absoluta = garantir_pasta_sessoes()
    caminho_completo = os.path.join(pasta_absoluta, nome_arquivo)

    try:
        with open(caminho_completo, "w", encoding="utf-8") as arquivo:
            json.dump(sessao_dict, arquivo, ensure_ascii=False, indent=2)
        logger.debug(f"Sessão salva: {caminho_completo}")
        return caminho_completo
    except PermissionError as error:
        logger.error(f"Permissão negada ao salvar sessão: {error}")
        raise PermissionError(
            f"Não foi possível salvar a sessão. Verifique as permissões da pasta '{_pasta_sessoes()}'."
        ) from error
    except OSError as error:
        logger.error(f"Erro de disco ao salvar sessão: {error}")
        raise OSError(
            "Não foi possível salvar a sessão. Verifique se há espaço em disco disponível."
        ) from error


def listar_sessoes_salvas() -> list[dict]:
    pasta_absoluta = garantir_pasta_sessoes()
    padrao = os.path.join(pasta_absoluta, "sessao_*.json")
    arquivos = sorted(glob.glob(padrao), reverse=True)

    sessoes = []
    for caminho in arquivos:
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            sessoes.append({
                "nome_arquivo": os.path.basename(caminho),
                "caminho": caminho,
                "qtd_mensagens": len(dados.get("historico", [])),
            })
        except (json.JSONDecodeError, OSError) as error:
            logger.debug(f"Sessão ilegível ignorada: {caminho} ({error})")
            continue

    return sessoes


def carregar_sessao(caminho: str) -> dict:
    if not os.path.exists(caminho):
        raise ValueError(f"Arquivo de sessão não encontrado: '{caminho}'.")

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except json.JSONDecodeError as error:
        raise ValueError(f"Sessão corrompida ou em formato inválido: '{caminho}'.") from error


def exportar_sessao(sessao, formato: str = "txt") -> str:
    dados = sessao.to_dict() if hasattr(sessao, "to_dict") else sessao
    historico = dados.get("historico", []) if isinstance(dados, dict) else []

    pasta = garantir_pasta_sessoes()
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")

    if formato == "json":
        caminho = os.path.join(pasta, f"export_{carimbo}.json")
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        return caminho

    rotulos = {"user": "Usuário", "assistant": "MARIA", "system": "Sistema"}
    linhas = []
    for msg in historico:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "?")
        content = msg.get("content", msg.get("conteudo", ""))
        linhas.append(f"[{rotulos.get(role, role)}]\n{content}\n")

    caminho = os.path.join(pasta, f"export_{carimbo}.txt")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))
    return caminho
