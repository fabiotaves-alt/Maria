"""Métricas agregadas do benchmark MARIA."""
import statistics
from collections import defaultdict
from dataclasses import dataclass

from ..tasks.task_schema import MariaTaskResult, MariaTaskAggregateResult


@dataclass
class MariaBenchmarkMetrics:
    total_tasks: int
    tool_accuracy: float
    confirmation_success_rate: float
    keyword_match_rate: float
    runtime_success_rate: float
    avg_latency_ms: float
    error_distribution: dict[str, int]
    by_category: dict[str, dict[str, float]]
    language_compliance_rate: float = 0.0


def calculate_maria_metrics(results: list[MariaTaskResult]) -> MariaBenchmarkMetrics:
    total = len(results)
    if not total:
        return MariaBenchmarkMetrics(0, 0, 0, 0, 0, 0, {}, 0.0)

    error_distribution = defaultdict(int)
    by_category = defaultdict(lambda: {"total": 0, "tool_correct": 0})
    language_ok_count = 0
    for result in results:
        for error in result.errors:
            error_distribution[error.get("kind", "Unknown")] += 1
        by_category[result.category]["total"] += 1
        by_category[result.category]["tool_correct"] += int(result.tool_correct)
        if result.language_ok:
            language_ok_count += 1

    category_metrics = {
        category: {
            "total": values["total"],
            "tool_accuracy": values["tool_correct"] / values["total"],
        }
        for category, values in by_category.items()
    }

    return MariaBenchmarkMetrics(
        total_tasks=total,
        tool_accuracy=sum(result.tool_correct for result in results) / total,
        confirmation_success_rate=sum(result.confirmation_completed for result in results) / total,
        keyword_match_rate=sum(result.keyword_match for result in results) / total,
        runtime_success_rate=sum(result.runtime_ok for result in results) / total,
        avg_latency_ms=sum(result.latency_ms for result in results) / total,
        error_distribution=dict(error_distribution),
        by_category=category_metrics,
        language_compliance_rate=language_ok_count / total,
    )


def aggregate_by_task(resultados: list["MariaTaskResult"]) -> MariaTaskAggregateResult:
    """Agrega N execuções da MESMA tarefa (mesmo task_id) em um único resumo."""
    if not resultados:
        raise ValueError("Lista de resultados vazia para agregação.")

    n = len(resultados)
    latencias = [r.latency_ms for r in resultados]

    return MariaTaskAggregateResult(
        task_id=resultados[0].task_id,
        task_name=resultados[0].task_name,
        category=resultados[0].category,
        execucoes=n,
        tool_accuracy=sum(1 for r in resultados if r.tool_correct) / n,
        confirmation_success_rate=sum(1 for r in resultados if r.confirmation_completed) / n,
        keyword_match_rate=sum(1 for r in resultados if r.keyword_match) / n,
        runtime_success_rate=sum(1 for r in resultados if r.runtime_ok) / n,
        avg_latency_ms=sum(latencias) / n,
        stddev_latency_ms=statistics.stdev(latencias) if n > 1 else 0.0,
    )