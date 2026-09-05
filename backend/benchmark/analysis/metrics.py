"""Métricas agregadas do benchmark MARIA."""
import statistics
from collections import defaultdict
from dataclasses import dataclass, field

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
    avg_tokens_por_segundo: float = 0.0
    args_accuracy: float = 1.0
    avg_ttft_ms: float | None = None
    p50_latency_ms: float = 0.0
    p90_latency_ms: float = 0.0
    # Taxa de tarefas sem erro de contexto (prompt > ctx_size do servidor).
    contexto_ok_rate: float = 1.0
    # Taxa de confirmação calculada SOMENTE sobre tarefas elegíveis
    # (confirmacao_elegivel=True). None quando não há tarefa elegível no run.
    # Elimina o efeito cascata de falhas de parser/timeout, que impedem a
    # confirmação de ser sequer oferecida ao usuário simulado.
    confirmation_success_rate_elegiveis: float | None = None
    # Nº de execuções sem tool call detectada MAS com padrão de chamada na
    # resposta bruta — separa "modelo não chamou" de "parser falhou".
    parse_suspeito_count: int = 0
    # Proporção de execuções SEM erro semântico (heurística de qualidade de
    # conteúdo: título/conteúdo invertidos, placeholders, conteúdo curto,
    # nome com extensão). Complementa args_accuracy (que é estrutural).
    semantic_quality_rate: float = 1.0
    # Contagem de erros semânticos por tipo (chaves: titulo_conteudo_invertido,
    # placeholder_detectado, conteudo_curto, nome_com_extensao).
    semantic_errors_by_type: dict[str, int] = field(default_factory=dict)
    # Total de correções automáticas aplicadas (ex.: sanitização de nome).
    correcoes_count: int = 0


def calculate_maria_metrics(results: list[MariaTaskResult]) -> MariaBenchmarkMetrics:
    total = len(results)
    if not total:
        return MariaBenchmarkMetrics(
            total_tasks=0,
            tool_accuracy=0.0,
            confirmation_success_rate=0.0,
            keyword_match_rate=0.0,
            runtime_success_rate=0.0,
            avg_latency_ms=0.0,
            error_distribution={},
            by_category={},
        )

    error_distribution = defaultdict(int)
    by_category = defaultdict(lambda: {"total": 0, "tool_correct": 0})
    language_ok_count = 0
    contexto_ok_count = 0
    for result in results:
        for error in result.errors:
            error_distribution[error.get("kind", "Unknown")] += 1
        by_category[result.category]["total"] += 1
        by_category[result.category]["tool_correct"] += int(result.tool_correct)
        if result.language_ok:
            language_ok_count += 1
        if result.contexto_ok:
            contexto_ok_count += 1

    category_metrics = {
        category: {
            "total": values["total"],
            "tool_accuracy": values["tool_correct"] / values["total"],
        }
        for category, values in by_category.items()
    }

    _SEMANTIC_FLAGS = (
        "titulo_conteudo_invertido",
        "placeholder_detectado",
        "conteudo_curto",
        "nome_com_extensao",
    )
    semantic_errors = defaultdict(int)
    semantic_ok_count = 0
    correcoes_total = 0
    for result in results:
        tem_erro = False
        for flag in _SEMANTIC_FLAGS:
            if getattr(result, flag, False):
                semantic_errors[flag] += 1
                tem_erro = True
        if not tem_erro:
            semantic_ok_count += 1
        correcoes_total += len(result.correcoes)

    tokens_medidos = [r.tokens_por_segundo for r in results if r.tokens_por_segundo > 0]
    avg_tokens_por_segundo = sum(tokens_medidos) / len(tokens_medidos) if tokens_medidos else 0.0

    ttft_medidos = [r.ttft_ms for r in results if r.ttft_ms is not None]
    avg_ttft_ms = sum(ttft_medidos) / len(ttft_medidos) if ttft_medidos else None

    latencias = sorted(r.latency_ms for r in results)
    p50_latency_ms = statistics.median(latencias)
    p90_latency_ms = (
        statistics.quantiles(latencias, n=10)[8] if len(latencias) >= 2 else latencias[0]
    )

    elegiveis = [r for r in results if r.confirmacao_elegivel]
    confirmation_elegiveis = (
        sum(1 for r in elegiveis if r.confirmation_completed) / len(elegiveis)
        if elegiveis else None
    )

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
        avg_tokens_por_segundo=avg_tokens_por_segundo,
        args_accuracy=sum(result.args_correct for result in results) / total,
        avg_ttft_ms=avg_ttft_ms,
        p50_latency_ms=p50_latency_ms,
        p90_latency_ms=p90_latency_ms,
        contexto_ok_rate=contexto_ok_count / total,
        confirmation_success_rate_elegiveis=confirmation_elegiveis,
        parse_suspeito_count=sum(1 for r in results if r.parse_suspeito),
        semantic_quality_rate=semantic_ok_count / total,
        semantic_errors_by_type=dict(semantic_errors),
        correcoes_count=correcoes_total,
    )


def aggregate_by_task(resultados: list["MariaTaskResult"]) -> MariaTaskAggregateResult:
    """Agrega N execuções da MESMA tarefa (mesmo task_id) em um único resumo."""
    if not resultados:
        raise ValueError("Lista de resultados vazia para agregação.")

    n = len(resultados)
    latencias = [r.latency_ms for r in resultados]

    tokens_medidos = [r.tokens_por_segundo for r in resultados if r.tokens_por_segundo > 0]
    tokens_gerados = [r.tokens_gerados for r in resultados]

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
        avg_tokens_por_segundo=sum(tokens_medidos) / len(tokens_medidos) if tokens_medidos else 0.0,
        avg_tokens_gerados=sum(tokens_gerados) / n,
    )