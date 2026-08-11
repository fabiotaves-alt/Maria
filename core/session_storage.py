"""
Módulo para persistência de sessões de chat em disco no projeto MARIA.
Cada execução gera um arquivo de sessão próprio (sessao_<timestamp>.json).
Sessões salvas podem ser listadas e retomadas via o comando 'retomar' em main.py.
"""

import os
import json
import glob
import logging

logger = logging.getLogger(__name__)


def _pasta_sessoes() -> str:
    """Lê a pasta de sessões no momento da chamada, inclusive em testes."""
    return os.getenv("PASTA_SESSOES", "sessoes_salvas")


def garantir_pasta_sessoes() -> str:
    """
    Garante que a pasta de sessões salvas existe.

    Returns:
        Caminho absoluto da pasta de sessões salvas.
    """
    pasta = _pasta_sessoes()
    if not os.path.exists(pasta):
        os.makedirs(pasta)
        logger.debug(f"Pasta '{pasta}' criada.")
    return os.path.abspath(pasta)


def salvar_sessao(sessao_dict: dict, nome_arquivo: str) -> str:
    """
    Salva (sobrescrevendo) o estado de uma sessão em um arquivo JSON.

    Args:
        sessao_dict: Resultado de ChatSession.to_dict().
        nome_arquivo: Nome do arquivo, sem caminho, com extensão .json
                      (ex: 'sessao_20260811_143000.json').

    Returns:
        Caminho absoluto do arquivo salvo.

    Raises:
        PermissionError: Se não houver permissão de escrita.
        OSError: Se houver erro de disco.
    """
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
    """
    Lista as sessões salvas, mais recentes primeiro (ordenação lexicográfica
    do nome do arquivo, que embute o timestamp).

    Returns:
        Lista de dicionários com 'nome_arquivo', 'caminho' e 'qtd_mensagens'.
        Arquivos corrompidos ou ilegíveis são ignorados (logados em debug).
    """
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
    """
    Carrega o dicionário de uma sessão salva a partir do caminho completo.

    Args:
        caminho: Caminho absoluto ou relativo do arquivo de sessão.

    Returns:
        Dicionário no formato aceito por ChatSession.from_dict().

    Raises:
        ValueError: Se o arquivo não existir ou o JSON for inválido.
    """
    if not os.path.exists(caminho):
        raise ValueError(f"Arquivo de sessão não encontrado: '{caminho}'.")

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except json.JSONDecodeError as error:
        raise ValueError(f"Sessão corrompida ou em formato inválido: '{caminho}'.") from error