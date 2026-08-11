"""Cálculo de métricas do benchmark."""
from typing import List, Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class TaskResult:
    task_id: int
    surface: str  # "lia" ou "python"
    model: str
    parse_ok: bool
    type_ok: bool
    runtime_ok: bool
    output_match: bool
    errors: List[Dict] = field(default_factory=list)
    tokens_prompt: int = 0
    tokens_completion: int = 0
    latency_ms: float = 0.0
    iterations: int = 1  # número de tentativas até sucesso
    source: str = ""  # código gerado pelo LLM


@dataclass
class BenchmarkMetrics:
    total_tasks: int
    parse_success_rate: float
    type_success_rate: float
    runtime_success_rate: float
    output_match_rate: float
    avg_tokens: float
    avg_latency_ms: float
    error_distribution: Dict[str, int]
    by_category: Dict[str, Dict[str, float]]
    by_difficulty: Dict[int, Dict[str, float]]


def calculate_metrics(results: List[TaskResult]) -> BenchmarkMetrics:
    """Calcula métricas agregadas de uma lista de resultados."""
    total = len(results)
    if total == 0:
        return BenchmarkMetrics(0, 0, 0, 0, 0, 0, 0, {}, {}, {})
    
    parse_ok = sum(1 for r in results if r.parse_ok)
    type_ok = sum(1 for r in results if r.type_ok)
    runtime_ok = sum(1 for r in results if r.runtime_ok)
    output_match = sum(1 for r in results if r.output_match)
    
    avg_tokens = sum(r.tokens_prompt + r.tokens_completion for r in results) / total
    avg_latency = sum(r.latency_ms for r in results) / total
    
    # Distribuição de erros
    error_dist = defaultdict(int)
    for r in results:
        for err in r.errors:
            error_dist[err.get("kind", "Unknown")] += 1
    
    # Por categoria (requer task_id -> category mapping)
    by_category = defaultdict(lambda: {"total": 0, "runtime_ok": 0})
    by_difficulty = defaultdict(lambda: {"total": 0, "runtime_ok": 0})
    
    return BenchmarkMetrics(
        total_tasks=total,
        parse_success_rate=parse_ok / total,
        type_success_rate=type_ok / total,
        runtime_success_rate=runtime_ok / total,
        output_match_rate=output_match / total,
        avg_tokens=avg_tokens,
        avg_latency_ms=avg_latency,
        error_distribution=dict(error_dist),
        by_category=dict(by_category),
        by_difficulty=dict(by_difficulty)
    )


def compare_metrics(lia: BenchmarkMetrics, python: BenchmarkMetrics) -> Dict[str, Any]:
    """Compara métricas entre Lia e Python."""
    lia_runtime = lia.runtime_success_rate * 100
    python_runtime = python.runtime_success_rate * 100
    runtime_diff = lia_runtime - python_runtime
    
    return {
        "parse_diff": (lia.parse_success_rate - python.parse_success_rate) * 100,
        "type_diff": (lia.type_success_rate - python.type_success_rate) * 100,
        "runtime_diff": runtime_diff,
        "output_diff": (lia.output_match_rate - python.output_match_rate) * 100,
        "tokens_diff": lia.avg_tokens - python.avg_tokens,
        "latency_diff": lia.avg_latency_ms - python.avg_latency_ms,
        "conclusion": _interpret_results(lia, python)
    }


def _interpret_results(lia: BenchmarkMetrics, python: BenchmarkMetrics) -> str:
    """Interpreta os resultados e gera conclusão."""
    runtime_diff = (lia.runtime_success_rate - python.runtime_success_rate) * 100
    
    if runtime_diff >= 15:
        return f"✅ Lia supera Python em {runtime_diff:.1f}pp. Hipótese validada."
    elif runtime_diff >= 5:
        return f"⚠️ Lia supera Python em {runtime_diff:.1f}pp. Vantagem marginal."
    elif runtime_diff >= -5:
        return f"⚠️ Paridade estatística ({runtime_diff:.1f}pp). Considerar pivot."
    else:
        return f"❌ Python supera Lia em {-runtime_diff:.1f}pp. Reavaliar projeto."
