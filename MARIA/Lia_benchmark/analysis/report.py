"""Geração de relatório do benchmark."""
import json
import os
from datetime import datetime
from typing import List, Dict, Any

from .metrics import BenchmarkMetrics, compare_metrics


def generate_report(
    lia_results: List[Dict],
    python_results: List[Dict],
    lia_metrics: BenchmarkMetrics,
    python_metrics: BenchmarkMetrics,
    output_dir: str
) -> str:
    """Gera um relatório em Markdown com os resultados do benchmark."""
    
    comparison = compare_metrics(lia_metrics, python_metrics)
    
    report = f"""# Relatório do Benchmark Lia vs Python

Gerado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Resumo Executivo

{comparison['conclusion']}

## Métricas Comparativas

| Métrica | Lia | Python | Diferença (pp) |
|---------|-----|--------|----------------|
| Parse Success | {lia_metrics.parse_success_rate*100:.1f}% | {python_metrics.parse_success_rate*100:.1f}% | {comparison['parse_diff']:+.1f} |
| Type Check Success | {lia_metrics.type_success_rate*100:.1f}% | {python_metrics.type_success_rate*100:.1f}% | {comparison['type_diff']:+.1f} |
| Runtime Success | {lia_metrics.runtime_success_rate*100:.1f}% | {python_metrics.runtime_success_rate*100:.1f}% | {comparison['runtime_diff']:+.1f} |
| Output Match | {lia_metrics.output_match_rate*100:.1f}% | {python_metrics.output_match_rate*100:.1f}% | {comparison['output_diff']:+.1f} |
| Tokens Médios | {lia_metrics.avg_tokens:.1f} | {python_metrics.avg_tokens:.1f} | {comparison['tokens_diff']:+.1f} |
| Latência Média (ms) | {lia_metrics.avg_latency_ms:.1f} | {python_metrics.avg_latency_ms:.1f} | {comparison['latency_diff']:+.1f} |

## Critérios de Decisão

| Critério | Meta | Resultado | Status |
|----------|------|-----------|--------|
| Runtime Success (Lia) | ≥ 90% | {lia_metrics.runtime_success_rate*100:.1f}% | {'✅' if lia_metrics.runtime_success_rate >= 0.9 else '❌'} |
| Vantagem sobre Python | ≥ 15pp | {comparison['runtime_diff']:+.1f}pp | {'✅' if comparison['runtime_diff'] >= 15 else '❌'} |
| Type Check (Lia) | ≥ 93% | {lia_metrics.type_success_rate*100:.1f}% | {'✅' if lia_metrics.type_success_rate >= 0.93 else '❌'} |
| Output Match | ≥ 75% | {lia_metrics.output_match_rate*100:.1f}% | {'✅' if lia_metrics.output_match_rate >= 0.75 else '❌'} |

## Distribuição de Erros

### Lia
{format_error_dist(lia_metrics.error_distribution)}

### Python
{format_error_dist(python_metrics.error_distribution)}

## Conclusão e Próximos Passos

Com base nos resultados acima:

- **Se a vantagem for ≥ 15pp**: Avançar para implementação de ADTs + Pattern Matching (Fase 4)
- **Se a vantagem for 5-15pp**: Considerar redução de escopo para DSL de nicho
- **Se houver paridade (±5pp)**: Avaliar pivot para ferramenta de reparo
- **Se Python for superior**: Reavaliar fundamentos do projeto ou abandonar

---

*Relatório gerado automaticamente pelo benchmark harness da linguagem Lia.*
"""
    
    # Salva o relatório
    report_path = os.path.join(output_dir, "benchmark_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    # Salva os dados brutos em JSON
    data_path = os.path.join(output_dir, "benchmark_data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "lia_results": lia_results,
            "python_results": python_results,
            "lia_metrics": {
                "total_tasks": lia_metrics.total_tasks,
                "parse_success_rate": lia_metrics.parse_success_rate,
                "type_success_rate": lia_metrics.type_success_rate,
                "runtime_success_rate": lia_metrics.runtime_success_rate,
                "output_match_rate": lia_metrics.output_match_rate,
                "avg_tokens": lia_metrics.avg_tokens,
                "avg_latency_ms": lia_metrics.avg_latency_ms,
                "error_distribution": lia_metrics.error_distribution,
            },
            "python_metrics": {
                "total_tasks": python_metrics.total_tasks,
                "parse_success_rate": python_metrics.parse_success_rate,
                "type_success_rate": python_metrics.type_success_rate,
                "runtime_success_rate": python_metrics.runtime_success_rate,
                "output_match_rate": python_metrics.output_match_rate,
                "avg_tokens": python_metrics.avg_tokens,
                "avg_latency_ms": python_metrics.avg_latency_ms,
                "error_distribution": python_metrics.error_distribution,
            },
            "comparison": comparison,
        }, f, indent=2)
    
    return report


def format_error_dist(error_dist: Dict[str, int]) -> str:
    """Formata distribuição de erros como tabela Markdown."""
    if not error_dist:
        return "*Nenhum erro*"
    
    lines = ["| Tipo de Erro | Ocorrências |", "|--------------|-------------|"]
    for kind, count in sorted(error_dist.items(), key=lambda x: -x[1]):
        lines.append(f"| {kind} | {count} |")
    return "\n".join(lines)
