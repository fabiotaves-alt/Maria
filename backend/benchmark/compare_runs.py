"""Compara duas execuções do benchmark MARIA."""
import argparse
import json
import os

from .analysis.metrics import calculate_maria_metrics
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


def _load_metrics(run_dir: str):
    with open(os.path.join(run_dir, "log.json"), encoding="utf-8") as log_file:
        dados = json.load(log_file)
    # Suporta ambos os formatos: novo (dict com "individual") e antigo (lista plana)
    if isinstance(dados, dict):
        resultados_raw = dados.get("individual", [])
    else:
        resultados_raw = dados
    results = [MariaTaskResult(**item) for item in resultados_raw]
    return calculate_maria_metrics(results)


def generate_comparison(before_dir: str, after_dir: str) -> str:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Compara dois runs do benchmark MARIA")
    parser.add_argument("--before", required=True, help="Diretório do run anterior")
    parser.add_argument("--after", required=True, help="Diretório do run posterior")
    args = parser.parse_args()
    print(generate_comparison(args.before, args.after))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
