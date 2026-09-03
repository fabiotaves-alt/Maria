"""
Parser de tool calls textuais para o formato nativo do llama-server.

O Qwen2.5-Omni-3B não emite tool_calls estruturadas via API OpenAI.
Ele gera texto plano no formato ensinado pelo system prompt.
Este parser converte esse texto para {"name": ..., "arguments": {...}}.

Formatos suportados:
    criar_planilha: ["gastos", "data", "valor"]
    criar_documento(["pauta_reuniao", "Pauta", "conteudo..."])
    editar_planilha: ["nome", "colunas"]
"""

import json
import re

# Mapeamento posicional: nome da ferramenta -> lista de chaves dos argumentos
_MAPEAMENTO_POSICIONAL = {
    "criar_planilha": ["nome_arquivo", "colunas"],
    "criar_documento": ["nome_arquivo", "titulo", "conteudo"],
    "editar_planilha": ["nome_arquivo", "colunas"],
    "listar_arquivos": [],
    "resumir_documento": ["nome_arquivo"],
    "consultar_manual_redacao": ["tipo_documento"],
}

# Regex para capturar os 3 formatos textuais
_RE_FORMATO_1 = re.compile(
    r"^\s*([a-z_]+)\s*:\s*\[(.*)\]\s*$",
    re.DOTALL | re.IGNORECASE,
)
_RE_FORMATO_2 = re.compile(
    r"^\s*([a-z_]+)\s*\(\s*\[(.*)\]\s*\)\s*$",
    re.DOTALL | re.IGNORECASE,
)
_RE_FORMATO_3 = re.compile(
    r"^\s*([a-z_]+)\s*\(\s*(.*)\s*\)\s*$",
    re.DOTALL | re.IGNORECASE,
)


def _parse_valor_bruto(valor_str: str):
    """Tenta parsear um valor bruto como JSON (lista, dict, bool, null, int, float).
    Se falhar, retorna a string limpa."""
    valor_str = valor_str.strip()
    if not valor_str:
        return ""
    # Tenta JSON primeiro
    try:
        return json.loads(valor_str)
    except json.JSONDecodeError:
        pass
    # Tenta detectar booleanos
    if valor_str.lower() == "true":
        return True
    if valor_str.lower() == "false":
        return False
    if valor_str.lower() in ("null", "none"):
        return None
    # Remove aspas externas se houver
    if (valor_str.startswith('"') and valor_str.endswith('"')) or \
       (valor_str.startswith("'") and valor_str.endswith("'")):
        return valor_str[1:-1]
    return valor_str


def _split_args_respeitando_listas(texto: str) -> list[str]:
    """Split por vírgula, mas respeita listas aninhadas [ ... ], dicts { ... } e strings \" ... \"."""
    partes = []
    atual = []
    profundidade_lista = 0
    profundidade_dict = 0
    dentro_string = False
    char_string = None
    i = 0
    while i < len(texto):
        c = texto[i]
        if not dentro_string and c in ('"', "'"):
            dentro_string = True
            char_string = c
            atual.append(c)
        elif dentro_string and c == char_string:
            # Verifica escape
            if i > 0 and texto[i - 1] == "\\":
                atual.append(c)
            else:
                dentro_string = False
                char_string = None
                atual.append(c)
        elif not dentro_string:
            if c == "[":
                profundidade_lista += 1
                atual.append(c)
            elif c == "]":
                profundidade_lista -= 1
                atual.append(c)
            elif c == "{":
                profundidade_dict += 1
                atual.append(c)
            elif c == "}":
                profundidade_dict -= 1
                atual.append(c)
            elif c == "," and profundidade_lista == 0 and profundidade_dict == 0:
                partes.append("".join(atual).strip())
                atual = []
            else:
                atual.append(c)
        else:
            atual.append(c)
        i += 1
    if atual:
        partes.append("".join(atual).strip())
    return [p for p in partes if p]


def _normalizar_quebras_em_arrays(conteudo: str) -> str:
    """Remove quebras de linha e espaços excedentes DENTRO de [ ] e ( ).
    
    Preserva o conteúdo mas deixa tudo em uma linha dentro dos delimitadores.
    """
    resultado = []
    profundidade_lista = 0
    profundidade_paren = 0
    i = 0
    
    while i < len(conteudo):
        c = conteudo[i]
        
        if c == "[":
            profundidade_lista += 1
            resultado.append(c)
        elif c == "]":
            profundidade_lista -= 1
            resultado.append(c)
        elif c == "(":
            profundidade_paren += 1
            resultado.append(c)
        elif c == ")":
            profundidade_paren -= 1
            resultado.append(c)
        elif c in ("\n", "\r") and (profundidade_lista > 0 or profundidade_paren > 0):
            # Dentro de array/parênteses: troca quebra por espaço
            resultado.append(" ")
        elif c == " " and (profundidade_lista > 0 or profundidade_paren > 0):
            # Dentro de array/parênteses: compacta espaços múltiplos
            if resultado and resultado[-1] != " ":
                resultado.append(c)
        else:
            resultado.append(c)
        
        i += 1
    
    return "".join(resultado)


def extrair_tool_call_textual(conteudo: str) -> dict | None:
    """Extrai tool call do formato textual gerado pelo modelo.

    Retorna {"name": str, "arguments": dict} ou None.
    """
    if not conteudo or not conteudo.strip():
        return None

    # Normaliza quebras dentro de arrays/parênteses
    conteudo_normalizado = _normalizar_quebras_em_arrays(conteudo)
    
    # Procura linha a linha (o modelo pode ter texto antes/depois)
    for linha in conteudo_normalizado.split("\n"):
        linha = linha.strip()
        if not linha:
            continue

        match = None
        for regex in (_RE_FORMATO_1, _RE_FORMATO_2, _RE_FORMATO_3):
            m = regex.match(linha)
            if m:
                match = m
                break

        if not match:
            continue

        nome = match.group(1).strip().lower()
        raw_args = match.group(2).strip()

        chaves = _MAPEAMENTO_POSICIONAL.get(nome)
        if chaves is None:
            continue  # ferramenta desconhecida

        argumentos = {}
        if chaves:
            partes = _split_args_respeitando_listas(raw_args)
            for i, chave in enumerate(chaves):
                if i < len(partes):
                    argumentos[chave] = _parse_valor_bruto(partes[i])
                else:
                    argumentos[chave] = None

        # Normalizacao de chaves para minusculas (defesa)
        argumentos = {k.lower(): v for k, v in argumentos.items()}

        return {"name": nome, "arguments": argumentos}

    return None
