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
}


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
        multiplier = 100 if field_name != "avg_latency_ms" else 1
        suffix = " pp" if field_name != "avg_latency_ms" else " ms"
        difference = (after_value - before_value) * multiplier
        lines.append(
            f"| {label} | {before_value * multiplier:.1f}{suffix} | "
            f"{after_value * multiplier:.1f}{suffix} | {difference:+.1f}{suffix} |"
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
