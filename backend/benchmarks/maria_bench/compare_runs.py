"""Compara duas execuções do benchmark MARIA."""
import argparse
import json
import os

from .analysis.metrics import calculate_maria_metrics
from .benchmark_config import BENCHMARK_RESULTS_DIR
from .tasks.task_schema import MariaTaskResult


METRIC_LABELS = {
    "tool_accuracy": "Tool accuracy",
    "confirmation_success_rate": "Confirmation success rate",
    "keyword_match_rate": "Keyword match rate",
    "runtime_success_rate": "Runtime success rate",
    "avg_latency_ms": "Average latency (ms)",
    "args_accuracy": "Args accuracy",
    "p50_latency_ms": "P50 latency (ms)",
    "p90_latency_ms": "P90 latency (ms)",
    "language_compliance_rate": "Language compliance rate",
    "contexto_ok_rate": "Context OK rate",
    "avg_tokens_por_segundo": "Avg tokens/s",
    "avg_ttft_ms": "Average TTFT (ms)",
}


def _eh_taxa(field_name: str) -> bool:
    return field_name.endswith("_rate") or field_name.endswith("_accuracy")


def _sufixo(field_name: str) -> str:
    if field_name.endswith("_ms"):
        return " ms"
    if _eh_taxa(field_name):
        return " pp"
    if field_name == "avg_tokens_por_segundo":
        return " tok/s"
    return ""


def _multiplicador(field_name: str) -> int:
    return 100 if _eh_taxa(field_name) else 1


def _formatar_valor(field_name: str, value: float | None) -> str:
    if value is None:
        return "N/D"
    return f"{value * _multiplicador(field_name):.1f}{_sufixo(field_name)}"


def _formatar_diferenca(field_name: str, before: float | None, after: float | None) -> str:
    if before is None or after is None:
        return "N/D"
    return f"{(after - before) * _multiplicador(field_name):+.1f}{_sufixo(field_name)}"


def carregar_resultados_de_log(run_dir: str) -> list[MariaTaskResult]:
    """Lê o log.json de um diretório run_* e devolve os resultados individuais.

    Suporta ambos os formatos históricos: novo (dict com "individual") e
    antigo (lista plana). Fonte única de leitura de log.json — reutilizada por
    compare_runs (modo diretório) e pela CLI unificada (`cli report <run_dir>`).
    """
    with open(os.path.join(run_dir, "log.json"), encoding="utf-8") as log_file:
        dados = json.load(log_file)
    if isinstance(dados, dict):
        resultados_raw = dados.get("individual", [])
    else:
        resultados_raw = dados
    return [MariaTaskResult(**item) for item in resultados_raw]


def _load_metrics(run_dir: str):
    return calculate_maria_metrics(carregar_resultados_de_log(run_dir))


def _eh_run_id(valor: str) -> bool:
    """True quando o argumento é um run_id numérico do SQLite (fase B3)."""
    return isinstance(valor, str) and valor.isdigit()


def _generate_comparison_dir(before_dir: str, after_dir: str) -> str:
    """Comparação legada lendo `log.json` de dois diretórios run_*."""
    before = _load_metrics(before_dir)
    after = _load_metrics(after_dir)
    lines = [
        "# Comparação de execuções do benchmark MARIA",
        "",
        f"Antes: `{before_dir}`",
        f"Depois: `{after_dir}`",
        "",
        "| Métrica | Antes | Depois | Diferença |",
        "|---|---:|---:|---:|",
    ]
    for field_name, label in METRIC_LABELS.items():
        before_value = getattr(before, field_name)
        after_value = getattr(after, field_name)
        lines.append(
            f"| {label} | {_formatar_valor(field_name, before_value)} | "
            f"{_formatar_valor(field_name, after_value)} | "
            f"{_formatar_diferenca(field_name, before_value, after_value)} |"
        )
    comparison_path = os.path.join(after_dir, "comparison.md")
    with open(comparison_path, "w", encoding="utf-8") as comparison_file:
        comparison_file.write("\n".join(lines) + "\n")
    return comparison_path


def _generate_comparison_sql(before_id: int, after_id: int) -> str:
    """Comparação via SQL: GROUP BY modelo, task_id, tool_call_fonte (spec B3).

    O3 do spec: a comparação histórica se resolve com agregações da
    tabela `results` em vez de carregar dois log.json gigantes na memória.
    """
    from .storage import agrupar_por_modelo_task_fonte

    antes = agrupar_por_modelo_task_fonte(before_id)
    depois = agrupar_por_modelo_task_fonte(after_id)

    def _tabla(filas: list[dict]) -> str:
        header = [
            "| Modelo | Tarefa | Fonte | Execuções | Acertos | Lat. média (ms) |",
            "|---|---|---:|---:|---:|---:|",
        ]
        filas_md = []
        for row in filas:
            filas_md.append(
                f"| {row['model'] or 'N/D'} | {row['task_id']} "
                f"({row['task_name']}) | {row['tool_call_fonte'] or 'None'} | "
                f"{row['execucoes']} | {row['acertos']} | "
                f"{row['latencia_media_ms']:.0f} |"
            )
        return "\n".join(header + filas_md)

    lines = [
        "# Comparação de execuções do benchmark MARIA (via SQL)",
        "",
        f"Antes: run `{before_id}`",
        f"Depois: run `{after_id}`",
        "",
        "> GROUP BY modelo, task_id, tool_call_fonte sobre `results` (fase B3).",
        "",
        "## Antes",
        "",
        _tabla(antes),
        "",
        "## Depois",
        "",
        _tabla(depois),
        "",
    ]
    comparison_path = os.path.join(
        BENCHMARK_RESULTS_DIR, f"comparison_{before_id}_{after_id}.md"
    )
    with open(comparison_path, "w", encoding="utf-8") as comparison_file:
        comparison_file.write("\n".join(lines) + "\n")
    return comparison_path


def generate_comparison(before: str, after: str) -> str:
    if _eh_run_id(before) and _eh_run_id(after):
        return _generate_comparison_sql(int(before), int(after))
    if not _eh_run_id(before) and not _eh_run_id(after):
        return _generate_comparison_dir(before, after)
    raise SystemExit(
        "Argumentos mistos: `--before`/`--after` devem ser ambos run_id (SQLite) "
        "ou ambos diretórios run_* (log.json)."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Compara dois runs do benchmark MARIA")
    parser.add_argument("--before", required=True,
                        help="Run anterior: diretório run_* (log.json) ou run_id numérico (SQLite, fase B3)")
    parser.add_argument("--after", required=True,
                        help="Run posterior: diretório run_* (log.json) ou run_id numérico (SQLite, fase B3)")
    args = parser.parse_args()
    print(generate_comparison(args.before, args.after))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
