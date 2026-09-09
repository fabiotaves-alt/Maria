"""Harness de calibracao do LLM-as-judge (fase B6).

Uso: apos rotular manualmente uma amostra de execucoes (>= 30, conforme o
plano), rode este script comparando os veredictos do judge contra os
rotulos humanos. NAO afirme calibracao automaticamente -- este script so
IMPRIME a taxa de concordancia; a decisao de tratar o judge como metrica
oficial e humana, documentada manualmente no CHANGELOG quando acontecer.

Formato esperado do arquivo de rotulos (JSON):
[
  {"task_id": 1, "rep": 1, "eixo": "tool_correta", "veredito_humano": "ok"},
  ...
]
"""
import json
import sys


def calcular_concordancia(rotulos_humanos: list[dict], vereditos_judge: dict[tuple[int, int], dict]) -> dict:
    """Retorna {"concordancia_geral": float, "por_eixo": {eixo: float}, "n_comparacoes": int}."""
    acertos_por_eixo: dict[str, int] = {}
    total_por_eixo: dict[str, int] = {}

    for rotulo in rotulos_humanos:
        chave = (rotulo["task_id"], rotulo["rep"])
        veredito = vereditos_judge.get(chave)
        if veredito is None:
            continue
        eixo = rotulo["eixo"]
        total_por_eixo[eixo] = total_por_eixo.get(eixo, 0) + 1
        if veredito.get(eixo) == rotulo["veredito_humano"]:
            acertos_por_eixo[eixo] = acertos_por_eixo.get(eixo, 0) + 1

    por_eixo = {
        eixo: acertos_por_eixo.get(eixo, 0) / total_por_eixo[eixo]
        for eixo in total_por_eixo
    }
    total_comparacoes = sum(total_por_eixo.values())
    total_acertos = sum(acertos_por_eixo.values())
    concordancia_geral = total_acertos / total_comparacoes if total_comparacoes else 0.0

    return {
        "concordancia_geral": concordancia_geral,
        "por_eixo": por_eixo,
        "n_comparacoes": total_comparacoes,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: python -m backend.benchmarks.maria_bench.analysis.calibracao_judge <rotulos.json> <vereditos.json>")
        return 1

    with open(sys.argv[1], encoding="utf-8") as f:
        rotulos = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        vereditos_raw = json.load(f)

    vereditos = {(v["task_id"], v["rep"]): v["veredito"] for v in vereditos_raw}
    resultado = calcular_concordancia(rotulos, vereditos)

    print(f"Concordancia geral: {resultado['concordancia_geral']:.1%} ({resultado['n_comparacoes']} comparacoes)")
    for eixo, taxa in resultado["por_eixo"].items():
        print(f"  {eixo}: {taxa:.1%}")

    if resultado["concordancia_geral"] < 0.80:
        print("\nAVISO: concordancia abaixo de 80% -- judge NAO deve ser tratado como metrica oficial.")
    else:
        print("\nConcordancia >= 80% atingida. Decisao de promover o judge a metrica oficial e MANUAL (nao automatizada por este script).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
