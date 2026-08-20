"""Geração de relatório Markdown e log JSON do benchmark MARIA."""
import json
import os
from dataclasses import asdict
from datetime import datetime

from .metrics import MariaBenchmarkMetrics
from ..tasks.task_schema import MariaTaskResult


def _format_errors(errors: dict[str, int]) -> str:
    if not errors:
        return "| Nenhum erro | 0 |\n|---|---|"
    lines = ["| Tipo | Ocorrências |", "|---|---:|"]
    lines.extend(f"| {kind} | {count} |" for kind, count in sorted(errors.items()))
    return "\n".join(lines)


def _diagnosticar_falha(result: MariaTaskResult) -> str:
    if result.errors:
        first_error = result.errors[0]
        kind = first_error.get("kind", "Erro")
        message = first_error.get("message", "").strip()
        return f"{kind}: {message}" if message else kind

    if not result.runtime_ok:
        return "Falha de execução (runtime)"
    if not result.tool_correct:
        return "Tool call incorreto ou ferramenta inesperada"
    if not result.confirmation_completed:
        return "Confirmação não concluída"
    if not result.language_ok:
        return "Resposta em idioma incorreto"
    if not result.keyword_match:
        return "Palavras-chave esperadas não encontradas"

    return "Falha não identificada"


def generate_report(
    results: list[MariaTaskResult],
    metrics: MariaBenchmarkMetrics,
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    generated_at = datetime.now().isoformat(timespec="seconds")
    failed = [
        result for result in results
        if not result.tool_correct
        or not result.runtime_ok
        or not result.confirmation_completed
        or not result.language_ok
        or not result.keyword_match
    ]

    report = f"""# Relatório do Benchmark MARIA

Gerado em: {generated_at}

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | {metrics.total_tasks} |
| Acurácia de tool calling | {metrics.tool_accuracy * 100:.1f}% |
| Taxa de confirmação | {metrics.confirmation_success_rate * 100:.1f}% |
| Taxa de palavras-chave | {metrics.keyword_match_rate * 100:.1f}% |
| Taxa de execução | {metrics.runtime_success_rate * 100:.1f}% |
| Taxa de conformidade de idioma | {metrics.language_compliance_rate * 100:.1f}% |
| Acurácia de argumentos | {metrics.args_accuracy * 100:.1f}% |
| Tokens por segundo (média) | {metrics.avg_tokens_por_segundo:.1f} tok/s |
| TTFT médio (1º token) | {f"{metrics.avg_ttft_ms:.1f} ms" if metrics.avg_ttft_ms is not None else "N/D"} |
| Latência p50 | {metrics.p50_latency_ms:.1f} ms |
| Latência p90 | {metrics.p90_latency_ms:.1f} ms |
| Latência média | {metrics.avg_latency_ms:.1f} ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
"""
    for category, values in sorted(metrics.by_category.items()):
        report += f"| {category} | {int(values['total'])} | {values['tool_accuracy'] * 100:.1f}% |\n"

    report += "\n## Distribuição de erros\n\n" + _format_errors(metrics.error_distribution)
    report += "\n\n## Tarefas com falha\n\n"
    if failed:
        report += "| ID | Tarefa | Motivo da falha |\n|---:|---|---|\n"
        for result in failed:
            reason = _diagnosticar_falha(result).replace("|", "/")[:200]
            report += f"| {result.task_id} | {result.task_name} | {reason} |\n"
    else:
        report += "Nenhuma tarefa falhou.\n"

    report_path = os.path.join(output_dir, "report.md")
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(report)

    with open(os.path.join(output_dir, "log.json"), "w", encoding="utf-8") as log_file:
        json.dump([asdict(result) for result in results], log_file, ensure_ascii=False, indent=2)

    return report_path
