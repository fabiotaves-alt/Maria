import ast
import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Mapeamento de ordem posicional para nomes de parâmetros por ferramenta
POSITIONAL_MAP = {
    "criar_planilha": ["nome_arquivo", "colunas"],
    "criar_documento": ["nome_arquivo", "titulo", "conteudo"],
    "editar_planilha": ["nome_arquivo", "colunas"],
    "listar_arquivos": ["pasta"],
    "resumir_documento": ["nome_arquivo"],
    "consultar_manual_redacao": ["tipo_documento"],
}


def extrair_tool_call_textual(conteudo: str) -> Optional[Dict[str, Any]]:
    """
    Extrai chamada de ferramenta no formato textual:
        nome_da_ferramenta: [arg1, arg2, ...]
    ou
        nome_da_ferramenta(["arg1", "arg2"])

    Retorna {"name": str, "arguments": dict} ou None.
    """
    if not conteudo:
        return None

    # Remove quebras de linha e espaços extras
    texto = " ".join(conteudo.strip().splitlines()).strip()

    # Padrão 1: nome: [ ... ]
    # Ex: criar_planilha: ["gastos", ["Data", "Valor"]]
    match = re.match(r"^\s*([a-zA-Z_]\w*)\s*:\s*(\[.*\])\s*$", texto, re.DOTALL)
    if match:
        nome = match.group(1)
        args_str = match.group(2)
        return _parse_posicional(nome, args_str)

    # Padrão 2: nome([ ... ])
    match = re.match(r"^\s*([a-zA-Z_]\w*)\s*\(\s*(\[.*\])\s*\)\s*$", texto, re.DOTALL)
    if match:
        nome = match.group(1)
        args_str = match.group(2)
        return _parse_posicional(nome, args_str)

    return None


def _parse_posicional(nome: str, args_str: str) -> Optional[Dict[str, Any]]:
    """
    Converte uma string de argumentos (lista Python literal) em um dicionário
    com os nomes dos parâmetros, usando POSITIONAL_MAP.
    """
    try:
        args_list = ast.literal_eval(args_str)
    except (SyntaxError, ValueError) as e:
        logger.warning("Falha ao parsear argumentos posicionais: %s", e)
        return None

    if not isinstance(args_list, list):
        logger.warning("Argumentos não são uma lista: %s", args_list)
        return None

    # Mapeia posição para nome do parâmetro
    param_names = POSITIONAL_MAP.get(nome, [])
    if not param_names:
        logger.warning("Ferramenta desconhecida para mapeamento posicional: %s", nome)
        # Fallback: usa índices numéricos
        args_dict = {str(i): v for i, v in enumerate(args_list)}
        return {"name": nome, "arguments": args_dict}

    # Monta dict com os nomes esperados
    args_dict = {}
    for i, param in enumerate(param_names):
        if i < len(args_list):
            args_dict[param] = args_list[i]
        else:
            args_dict[param] = None  # campo obrigatório ausente

    # Verifica se todos os obrigatórios foram preenchidos (opcional)
    return {"name": nome, "arguments": args_dict}