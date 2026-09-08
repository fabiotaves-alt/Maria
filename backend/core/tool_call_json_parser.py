"""
Parser para tool calls no formato JSON plano {"ferramenta": ...} ou nativo OpenAI {"name": ...}.
"""
import json
import logging
import re
from typing import Any

from backend.core.tools_schema import CAMPOS_OBRIGATORIOS

logger = logging.getLogger(__name__)

# Ferramentas suportadas (whitelist)
FERRAMENTAS_SUPORTADAS = set(CAMPOS_OBRIGATORIOS.keys())

# Chaves de controle conhecidas que devem ser normalizadas para caixa baixa
CHAVES_CONTROLE = {
    "ferramenta",
    "name",
    "arguments",
    "argumentos",
    "nome_arquivo",
    "colunas",
    "linhas",
    "titulo",
    "conteudo",
    "descricao",
    "tipo_documento",
    "pasta",
    "offset",
    "linha_cabecalho",
    "limite_linhas",
}

# Mapeamento de sinonimos/alias de ferramentas
MAPA_ALIASES_FERRAMENTA = {
    "criar planilha": "criar_planilha",
    "criar documento": "criar_documento",
    "editar planilha": "editar_planilha",
    "listar arquivos": "listar_arquivos",
    "resumir documento": "resumir_documento",
    "extrair dados": "extrair_dados_planilha",
    "extrair dados planilha": "extrair_dados_planilha",
    "consultar manual": "consultar_manual_redacao",
}


def _normalizar_chaves_controle(dados: dict[str, Any]) -> dict[str, Any]:
    """Normaliza apenas as chaves de controle de primeiro nível para minusculas."""
    novo_dict = {}
    for k, v in dados.items():
        chave_lower = k.lower()
        if chave_lower in CHAVES_CONTROLE:
            novo_dict[chave_lower] = v
        else:
            novo_dict[k] = v
    return novo_dict


def _tentar_reparar_json(texto: str) -> tuple[dict | None, bool]:
    """
    Tenta fechar aspas, colchetes e chaves pendentes para JSONs truncados por max_tokens.
    Retorna (dict, reparado_com_sucesso).
    """
    texto_limpo = texto.strip()
    if not texto_limpo.startswith("{"):
        return None, False

    # Tentar fechar aspas se houver um número ímpar de aspas não escapadas
    # Contagem simples de aspas
    aspa_aberta = False
    escapado = False
    for char in texto_limpo:
        if char == '\\' and not escapado:
            escapado = True
            continue
        if char == '"' and not escapado:
            aspa_aberta = not aspa_aberta
        escapado = False

    texto_reparado = texto_limpo
    if aspa_aberta:
        texto_reparado += '"'

    # Fechar colchetes e chaves balanceando
    pilha = []
    em_string = False
    escapado = False
    for char in texto_reparado:
        if char == '\\' and not escapado:
            escapado = True
            continue
        if char == '"' and not escapado:
            em_string = not em_string
        elif not em_string:
            if char in ("{", "["):
                pilha.append(char)
            elif char in ("}", "]"):
                if pilha:
                    pilha.pop()
        escapado = False

    while pilha:
        topo = pilha.pop()
        if topo == "{":
            texto_reparado += "}"
        elif topo == "[":
            texto_reparado += "]"

    try:
        dados = json.loads(texto_reparado)
        if isinstance(dados, dict):
            return dados, True
    except json.JSONDecodeError:
        pass

    return None, False


def extrair_tool_call_json(conteudo: str) -> dict[str, Any] | None:
    """
    Extrai tool call no formato JSON do conteúdo retornado pelo modelo.

    Suporta:
    - Objeto plano: {"ferramenta": "criar_planilha", "nome_arquivo": "...", ...}
    - Objeto OpenAI: {"name": "criar_planilha", "arguments": {...}}
    - Bloco de código markdown ```json ... ``` ou JSON embutido em texto.

    Returns:
        dict {"name": str, "arguments": dict, "_fonte": "json", "_reparado": bool}
        ou None se nenhuma tool call válida for encontrada.
    """
    if not conteudo or not isinstance(conteudo, str):
        return None

    texto = conteudo.strip()

    # Stripar cercas de código ```json ... ```
    match_cerca = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', texto, re.DOTALL | re.IGNORECASE)
    if match_cerca:
        texto_bloco = match_cerca.group(1).strip()
    else:
        texto_bloco = texto

    dados_json = None
    reparado = False

    # T1: json.loads direto no texto do bloco ou texto completo
    try:
        dados_json = json.loads(texto_bloco)
    except json.JSONDecodeError:
        pass

    # T2: raw_decode no primeiro '{' encontrado
    if dados_json is None:
        idx_chave = texto.find("{")
        if idx_chave != -1:
            try:
                decoder = json.JSONDecoder()
                dados_json, _ = decoder.raw_decode(texto[idx_chave:])
            except json.JSONDecodeError:
                pass

    # T3: Reparo de truncamento
    if dados_json is None:
        idx_chave = texto.find("{")
        if idx_chave != -1:
            dados_json, reparado = _tentar_reparar_json(texto[idx_chave:])

    if not isinstance(dados_json, dict):
        return None

    # Normalizar chaves de controle
    dados_norm = _normalizar_chaves_controle(dados_json)

    # Identificar formato nativo OpenAI vs formato plano MARIA
    nome_ferramenta = None
    argumentos = {}

    if "name" in dados_norm and isinstance(dados_norm["name"], str):
        nome_ferramenta = dados_norm["name"]
        raw_args = dados_norm.get("arguments", {})
        if isinstance(raw_args, str):
            try:
                argumentos = json.loads(raw_args)
            except json.JSONDecodeError:
                argumentos = {}
        elif isinstance(raw_args, dict):
            argumentos = raw_args
    elif "ferramenta" in dados_norm and isinstance(dados_norm["ferramenta"], str):
        nome_ferramenta = dados_norm["ferramenta"]
        # Argumentos são todas as outras chaves
        argumentos = {k: v for k, v in dados_norm.items() if k != "ferramenta"}
    else:
        return None

    if not nome_ferramenta:
        return None

    # Normalizar nome da ferramenta (caixa/aliases)
    nome_clean = nome_ferramenta.strip().lower().replace("-", "_")
    if nome_clean in MAPA_ALIASES_FERRAMENTA:
        nome_clean = MAPA_ALIASES_FERRAMENTA[nome_clean]
    elif nome_clean.replace("_", " ") in MAPA_ALIASES_FERRAMENTA:
        nome_clean = MAPA_ALIASES_FERRAMENTA[nome_clean.replace("_", " ")]

    if nome_clean not in FERRAMENTAS_SUPORTADAS:
        logger.warning("Tool call ignorada: ferramenta '%s' não está na whitelist.", nome_ferramenta)
        return None

    # Normalizar chaves de primeiro nível dos argumentos (sem tocar em linhas)
    argumentos_norm = {}
    for k, v in argumentos.items():
        k_lower = k.lower()
        if k_lower in CHAVES_CONTROLE:
            argumentos_norm[k_lower] = v
        else:
            argumentos_norm[k] = v

    return {
        "name": nome_clean,
        "arguments": argumentos_norm,
        "_fonte": "json",
        "_reparado": reparado,
    }

