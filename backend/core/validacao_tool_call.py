"""
Camada de validação determinística pós-parser para tool calls.
Executa verificações estruturais e correções case-insensitive sem chamadas ao LLM.
"""
import copy
import logging
from typing import Any

from backend.core.config import get_max_linhas_por_chamada
from backend.core.tools_schema import CAMPOS_OBRIGATORIOS

logger = logging.getLogger(__name__)


def validar_tool_call_determinístico(tool_call: dict[str, Any]) -> dict[str, Any]:
    """
    Valida e sanitiza deterministicamente uma tool call antes da execução.

    Args:
        tool_call: dict no formato {"name": str, "arguments": dict, ...}

    Returns:
        dict {
            "tool_call": dict,
            "erros": list[str],
            "reparos": list[dict],
            "bloqueante": bool
        }
    """
    if not tool_call or not isinstance(tool_call, dict):
        return {
            "tool_call": tool_call,
            "erros": ["Tool call nula ou inválida"],
            "reparos": [],
            "bloqueante": True,
        }

    tc = copy.deepcopy(tool_call)
    nome = tc.get("name", "")
    args = tc.get("arguments", {})
    if not isinstance(args, dict):
        args = {}
        tc["arguments"] = args

    erros = []
    reparos = []

    # V1: Campos obrigatórios
    campos_req = CAMPOS_OBRIGATORIOS.get(nome, [])
    for campo in campos_req:
        if campo not in args or args[campo] is None or (isinstance(args[campo], (str, list)) and len(args[campo]) == 0):
            # Exceção V5: 'colunas' pode ser derivada se 'linhas' estiver presente
            if campo == "colunas" and "linhas" in args and isinstance(args["linhas"], list) and len(args["linhas"]) > 0:
                pass
            else:
                erros.append(f"Campo obrigatório '{campo}' ausente ou vazio para ferramenta '{nome}'.")

    # V5: Derivar 'colunas' a partir das chaves de 'linhas' se colunas estiver ausente ou vazia
    if nome in ("criar_planilha", "editar_planilha"):
        colunas = args.get("colunas")
        linhas = args.get("linhas")

        if (not colunas or not isinstance(colunas, list)) and isinstance(linhas, list) and len(linhas) > 0 and isinstance(linhas[0], dict):
            colunas_derivadas = list(linhas[0].keys())
            args["colunas"] = colunas_derivadas
            reparos.append({"tipo": "colunas_derivadas", "colunas": colunas_derivadas})
            logger.info("Validação V5: 'colunas' derivada das chaves de 'linhas': %s", colunas_derivadas)

    # V2, V3, V4, V7: Validações sobre 'linhas' (se presente)
    if "linhas" in args and args["linhas"] is not None:
        linhas = args["linhas"]
        if not isinstance(linhas, list):
            erros.append("O parâmetro 'linhas' deve ser uma lista de objetos (dicts).")
        else:
            colunas = args.get("colunas", [])
            if isinstance(colunas, list):
                # Mapa case-insensitive para colunas
                mapa_colunas_lower = {str(c).strip().lower(): str(c) for c in colunas}

                linhas_corrigidas = []
                houve_renomeacao = False

                for item in linhas:
                    if not isinstance(item, dict):
                        erros.append("Item em 'linhas' não é um dict válido.")
                        continue

                    novo_item = {}
                    for k, v in item.items():
                        k_str = str(k).strip()
                        k_lower = k_str.lower()

                        # V3: Match case-insensitive contra colunas
                        if k_lower in mapa_colunas_lower:
                            col_canonica = mapa_colunas_lower[k_lower]
                            novo_item[col_canonica] = v
                            if col_canonica != k_str:
                                houve_renomeacao = True
                        else:
                            # V4: Chave sem match direto
                            novo_item[k_str] = v

                    linhas_corrigidas.append(novo_item)

                args["linhas"] = linhas_corrigidas
                if houve_renomeacao:
                    reparos.append({"tipo": "chaves_normalizadas", "detalhe": "Chaves de linhas normalizadas case-insensitive."})

            # V7: Limite de linhas
            limite = get_max_linhas_por_chamada()
            if len(linhas) > limite:
                args["linhas"] = linhas[:limite]
                reparos.append({"tipo": "linhas_truncadas_limite", "original": len(linhas), "limite": limite})

    bloqueante = len(erros) > 0
    return {
        "tool_call": tc,
        "erros": erros,
        "reparos": reparos,
        "bloqueante": bloqueante,
    }

