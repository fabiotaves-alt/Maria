"""Geração de relatório Markdown e log JSON do benchmark MARIA."""
import json
import os
from dataclasses import asdict
from datetime import datetime

from backend.core.config import LLAMA_NUM_CTX

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
    modelo_configurado: str | None = None,
    modelo_carregado: str | None = None,
    metadados_modelo: dict | None = None,
    log_final: dict | None = None,
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

    modelo_cfg = modelo_configurado or "—"
    modelo_ld = modelo_carregado or "—"
    meta = metadados_modelo or {}

    # Monta a seção Modelo enriquecida
    linhas_modelo = [
        "## Modelo",
        "",
        "| Origem | Nome |",
        "|---|---:|",
        f"| Configurado (`LLAMA_MODEL`) | {modelo_cfg} |",
        f"| Carregado (`/v1/models`) | {meta.get('id_exibicao') or modelo_ld} |",
    ]

    # Linha de modelo derivado (quando id é blob)
    rotulo = meta.get("rotulo_tamanho", "")
    if rotulo and meta.get("id") and meta.get("id") != meta.get("id_exibicao"):
        linhas_modelo.append(f"| Modelo (derivado) | {rotulo} |")

    # Quantização
    quantizacao = meta.get("quantizacao", "")
    if quantizacao:
        linhas_modelo.append(f"| Quantização | {quantizacao} |")

    # Parâmetros
    n_params = meta.get("n_params")
    if n_params:
        bilhoes = n_params / 1e9
        linhas_modelo.append(f"| Parâmetros | {bilhoes:.2f}B ({n_params:,}) |")

    # n_ctx
    n_ctx = meta.get("n_ctx")
    n_ctx_train = meta.get("n_ctx_train")
    if n_ctx is not None or n_ctx_train is not None:
        ctx_str = str(n_ctx) if n_ctx is not None else "—"
        ctx_train_str = str(n_ctx_train) if n_ctx_train is not None else "—"
        linhas_modelo.append(f"| n_ctx (servidor / treino) | {ctx_str} / {ctx_train_str} |")

    # Tamanho
    tamanho_legivel = meta.get("tamanho_legivel", "")
    if tamanho_legivel:
        linhas_modelo.append(f"| Tamanho | {tamanho_legivel} |")

    # Alerta de divergência (só quando relevante)
    alerta_modelo = ""
    if modelo_configurado and modelo_carregado and modelo_configurado != modelo_carregado:
        eh_local = (os.sep in modelo_carregado or "/" in modelo_carregado
                    or modelo_carregado.lower().endswith(".gguf")
                    or modelo_carregado.startswith("sha256-"))
        if not eh_local or not rotulo:
            alerta_modelo = (
                f"\n> ⚠️ **Atenção:** `LLAMA_MODEL` ({modelo_configurado}) diverge do modelo "
                f"efetivamente carregado no llama-server ({meta.get('id_exibicao') or modelo_carregado}). "
                f"As execuções podem não estar usando o modelo desejado.\n"
            )

    # Aviso de n_ctx (config > servidor)
    aviso_n_ctx = ""
    if n_ctx is not None:
        try:
            if int(LLAMA_NUM_CTX) > int(n_ctx):
                aviso_n_ctx = (
                    f"\n> ℹ️ `LLAMA_NUM_CTX` ({LLAMA_NUM_CTX}) é maior que o n_ctx real do "
                    f"servidor ({n_ctx}). O contexto efetivo das execuções é {n_ctx}.\n"
                )
        except (TypeError, ValueError, NameError):
            pass

    secao_modelo = "\n".join(linhas_modelo) + alerta_modelo + aviso_n_ctx

    report = f"""# Relatório do Benchmark MARIA

Gerado em: {generated_at}

{secao_modelo}
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
        if log_final is not None:
            json.dump(log_final, log_file, ensure_ascii=False, indent=2)
        else:
            json.dump([asdict(result) for result in results], log_file, ensure_ascii=False, indent=2)

    return report_path
