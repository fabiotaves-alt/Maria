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


def _extrair_lista_balanceada(texto: str, inicio: int) -> str | None:
    """Extrai a substring da lista que começa em texto[inicio] == '['.

    Percorre o texto contando profundidade de colchetes, ignorando os que
    estiverem dentro de strings (aspas duplas/simples). Retorna None se o
    fechamento não for encontrado (lista truncada por max_tokens, por ex.).
    """
    profundidade = 0
    aspa: str | None = None
    for i in range(inicio, len(texto)):
        char = texto[i]
        if aspa is not None:
            if char == aspa:
                aspa = None
            continue
        if char in ("\"", "'"):
            aspa = char
        elif char == "[":
            profundidade += 1
        elif char == "]":
            profundidade -= 1
            if profundidade == 0:
                return texto[inicio:i + 1]
    return None


def _reparar_lista_truncada(args_str: str) -> str | None:
    """Tenta fechar uma lista cortada por max_tokens para torná-la parseável.

    Estratégia conservadora: descarta o último item quando ele está incompleto
    (string sem aspas de fechamento fora do início da lista) e adiciona as
    aspas/colchetes pendentes. Retorna None quando o reparo não é possível.
    """
    texto = args_str.rstrip()
    if not texto.startswith("["):
        return None
    profundidade = 0
    aspa: str | None = None
    for char in texto:
        if aspa is not None:
            if char == aspa:
                aspa = None
            continue
        if char in ("\"", "'"):
            aspa = char
        elif char == "[":
            profundidade += 1
        elif char == "]":
            profundidade -= 1
    if aspa is not None and texto.rstrip().rstrip(",").endswith(aspa):
        # String aberta sem conteúdo após a aspa inicial: item vazio; descarta.
        texto = texto[:texto.rindex(aspa)].rstrip().rstrip(",")
        aspa = None
    elif aspa is not None:
        # Fecha a string aberta e aceita o conteúdo parcial do último item.
        texto += aspa
    if profundidade <= 0:
        return None
    return texto + "]" * profundidade


def _normalizar_argumentos(nome: str, args_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza os argumentos posicionais mapeados.

    - Se o modelo achatou as colunas (criar_planilha: ["gastos", "Data", "Valor"]),
      os itens extras são agrupados na lista 'colunas'.
    - Se 'colunas' veio como string única ("Dia, Compromisso"), vira lista
      (split por vírgula, itens aparados).
    """
    param_names = POSITIONAL_MAP.get(nome, [])
    if "colunas" in param_names:
        extras = args_dict.pop("_extras", [])
        colunas = args_dict.get("colunas")
        if extras:
            lista = list(colunas) if isinstance(colunas, list) else ([colunas] if colunas is not None else [])
            lista.extend(extras)
            args_dict["colunas"] = lista
        elif isinstance(colunas, str):
            args_dict["colunas"] = [item.strip() for item in colunas.split(",") if item.strip()]
    else:
        args_dict.pop("_extras", None)
    return args_dict


def extrair_tool_call_textual(conteudo: str) -> Optional[Dict[str, Any]]:
    """
    Extrai chamada de ferramenta no formato textual:
        nome_da_ferramenta: [arg1, arg2, ...]
    ou
        nome_da_ferramenta(["arg1", "arg2"])

    Retorna {"name": str, "arguments": dict} ou None.

    Tolerante às variações observadas em produção (log do benchmark):
    - texto explicativo antes/depois da chamada (a PRIMEIRA ocorrência de
      ferramenta conhecida vence; o restante é ignorado);
    - pontuação final após a lista (';' ou '.');
    - lista truncada por max_tokens (reparada de forma conservadora);
    - colunas achatadas ou como string única (normalizadas para lista).
    """
    if not conteudo:
        return None

    # Localiza a primeira ocorrência de uma ferramenta CONHECIDA seguida de
    # ':' ou '('. Nomes desconhecidos (ex.: pseudo-chamadas como
    # "Listar arquivos:" com espaço/capitalização livre) não casam.
    for match in re.finditer(r"\b([a-z_][a-z0-9_]*)\s*[:(]", conteudo):
        nome = match.group(1)
        if nome not in POSITIONAL_MAP:
            continue
        idx_lista = conteudo.find("[", match.end())
        if idx_lista == -1:
            return None
        args_str = _extrair_lista_balanceada(conteudo, idx_lista)
        if args_str is None:
            args_str = _reparar_lista_truncada(conteudo[idx_lista:])
        if args_str is None:
            return None
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

    # Mapeia posição para nome do parâmetro (nomes desconhecidos são
    # rejeitados antes, em extrair_tool_call_textual — whitelist).
    param_names = POSITIONAL_MAP[nome]

    # Monta dict com os nomes esperados; itens além do último parâmetro
    # viram "_extras" para _normalizar_argumentos (colunas achatadas).
    args_dict = {}
    for i, param in enumerate(param_names):
        if i < len(args_list):
            args_dict[param] = args_list[i]
        else:
            args_dict[param] = None  # campo obrigatório ausente
    if len(args_list) > len(param_names):
        args_dict["_extras"] = args_list[len(param_names):]

    return {"name": nome, "arguments": _normalizar_argumentos(nome, args_dict)}