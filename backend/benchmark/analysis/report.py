"""Geração de relatório Markdown do benchmark MARIA."""
import json
import os
from datetime import datetime

from backend.core.config import LLAMA_NUM_CTX

from .metrics import MariaBenchmarkMetrics
from ..tasks.task_schema import MariaTaskResult


# Ordem de exibição dos parâmetros de sampler no relatório (mesma ordem da
# documentação do llama.cpp / lista apresentada na especificação da tarefa).
_ORDEM_SAMPLER = (
    "repeat_last_n",
    "repeat_penalty",
    "frequency_penalty",
    "presence_penalty",
    "dry_multiplier",
    "dry_base",
    "dry_allowed_length",
    "dry_penalty_last_n",
    "top_k",
    "top_p",
    "min_p",
    "xtc_probability",
    "xtc_threshold",
    "typical_p",
    "top_n_sigma",
    "temperature",
)


def _formatar_sampler_valor(valor) -> str:
    """Formata valores de sampler: floats com 3 casas, demais como inteiro/str."""
    if isinstance(valor, float):
        return f"{valor:.3f}"
    return str(valor)


def _montar_secacao_sampler(sampler_params: dict | None) -> str:
    """Renderiza a tabela de parâmetros de sampler usados no benchmark."""
    if not sampler_params:
        return ""
    linhas = ["## Parâmetros do sampler", "", "| Parâmetro | Valor |", "|---|---:|"]
    for chave in _ORDEM_SAMPLER:
        valor = sampler_params.get(chave)
        if valor is not None:
            linhas.append(f"| {chave} | {_formatar_sampler_valor(valor)} |")
    return "\n".join(linhas) + "\n"


def extrair_texto_system(mensagens: list[dict] | None) -> str | None:
    """Retorna o content da primeira mensagem role='system' encontrada em
    `mensagens`, ou None se não houver mensagem system ou a lista for vazia/None."""
    if not mensagens:
        return None
    for mensagem in mensagens:
        if mensagem.get("role") == "system":
            return mensagem.get("content")
    return None


def mascarar_system_prompt(mensagens: list[dict]) -> list[dict]:
    """Retorna uma CÓPIA da lista de mensagens onde o content da mensagem
    role='system' foi substituído pelo marcador 'prompt do system injetado'.
    Não muta `mensagens` nem os dicts originais (necessário porque
    result.prompt_enviado também é usado para gravação bruta em log.json)."""
    if not mensagens:
        return []
    resultado = []
    for mensagem in mensagens:
        if mensagem.get("role") == "system":
            nova = dict(mensagem)
            nova["content"] = "prompt do system injetado"
            resultado.append(nova)
        else:
            resultado.append(mensagem)
    return resultado


def _montar_detalhes_execucao(results: list[MariaTaskResult]) -> str:
    """Renderiza, por execução, o prompt enviado e a resposta bruta do modelo.

    O texto do prompt de sistema é impresso UMA ÚNICA VEZ no topo desta seção
    (extraído da primeira execução que o contiver). Em cada bloco de execução
    individual, a mensagem role='system' é substituída pelo marcador
    'prompt do system injetado' para evitar repetição do texto completo.
    """
    if not results:
        return ""
    tem_conteudo = any(r.prompt_enviado or r.resposta_bruta_modelo for r in results)
    if not tem_conteudo:
        return ""

    linhas = ["## Detalhes por execução", ""]

    system_prompt_texto = None
    for result in results:
        texto = extrair_texto_system(result.prompt_enviado)
        if texto:
            system_prompt_texto = texto
            break

    if system_prompt_texto:
        linhas.append("**Prompt do system (injetado em todas as execuções abaixo):**")
        linhas.append("")
        linhas.append("```text")
        linhas.append(system_prompt_texto)
        linhas.append("```")
        linhas.append("")

    for idx, result in enumerate(results, start=1):
        linhas.append(
            f"### Execução {idx} — Tarefa {result.task_id}: {result.task_name} "
            f"({result.category})"
        )
        linhas.append("")
        if result.prompt_enviado:
            linhas.append("**Prompt enviado (mensagens):**")
            linhas.append("")
            linhas.append("```json")
            linhas.append(json.dumps(
                mascarar_system_prompt(result.prompt_enviado),
                ensure_ascii=False,
                indent=2,
            ))
            linhas.append("```")
        else:
            linhas.append("**Prompt enviado:** *(não capturado)*")
        linhas.append("")
        if result.resposta_bruta_modelo:
            linhas.append("**Resposta bruta do modelo:**")
            linhas.append("")
            linhas.append("```text")
            linhas.append(result.resposta_bruta_modelo)
            linhas.append("```")
        else:
            linhas.append("**Resposta bruta do modelo:** *(vazia)*")
        linhas.append("")
        if result.final_message and result.final_message != result.resposta_bruta_modelo:
            linhas.append("**Mensagem final (pós-ferramenta/confirmação):**")
            linhas.append("")
            linhas.append("```text")
            linhas.append(result.final_message)
            linhas.append("```")
            linhas.append("")
    return "\n".join(linhas) + "\n"


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
    metadados_modelo: dict | None = None,
    sampler_params: dict | None = None,
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

    # Monta a seção Modelo — APENAS dados reais (fonte: /v1/models).
    # Nenhuma coluna "Configurado"/fake é exibida.
    meta = metadados_modelo or {}
    if metadados_modelo:
        modelo_nome = (
            meta.get("nome_exibicao") or meta.get("id_exibicao") or "Desconhecido"
        )
        modelo_id = meta.get("id") or "N/A"
        modelo_qtz = meta.get("quantizacao") or "N/A"
        linhas_modelo = [
            "## Modelo",
            "",
            "| Propriedade | Valor |",
            "|---|---:|",
            f"| Nome | {modelo_nome} |",
            f"| Quantização | {modelo_qtz} |",
            f"| ID real | {modelo_id} |",
        ]

        # Parâmetros (reais, via /v1/models)
        n_params = meta.get("n_params")
        if n_params:
            bilhoes = n_params / 1e9
            linhas_modelo.append(f"| Parâmetros | {bilhoes:.2f}B ({n_params:,}) |")

        # n_ctx (reais, via /v1/models)
        n_ctx = meta.get("n_ctx")
        n_ctx_train = meta.get("n_ctx_train")
        if n_ctx is not None or n_ctx_train is not None:
            ctx_str = str(n_ctx) if n_ctx is not None else "—"
            ctx_train_str = str(n_ctx_train) if n_ctx_train is not None else "—"
            linhas_modelo.append(f"| n_ctx (servidor / treino) | {ctx_str} / {ctx_train_str} |")

        # Tamanho (real, via /v1/models)
        tamanho_legivel = meta.get("tamanho_legivel")
        if tamanho_legivel:
            linhas_modelo.append(f"| Tamanho | {tamanho_legivel} |")

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

        secao_modelo = "\n".join(linhas_modelo) + aviso_n_ctx
    else:
        secao_modelo = (
            "## Modelo\n"
            "\n"
            "| Propriedade | Valor |\n"
            "|---|---:|\n"
            "| Nome | Não detectado |\n"
            "\n"
            "> ERRO: Não foi possível obter metadados do modelo via /v1/models."
        )

    secao_sampler = _montar_secacao_sampler(sampler_params)
    secao_detalhes = _montar_detalhes_execucao(results)

    report = f"""# Relatório do Benchmark MARIA

Gerado em: {generated_at}

{secao_modelo}
{secao_sampler}
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
| Contexto OK | {metrics.contexto_ok_rate * 100:.1f}% |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
"""
    for category, values in sorted(metrics.by_category.items()):
        report += f"| {category} | {int(values['total'])} | {values['tool_accuracy'] * 100:.1f}% |\n"

    report += "\n## Distribuição de erros\n\n" + _format_errors(metrics.error_distribution)
    if secao_detalhes:
        report += "\n\n" + secao_detalhes
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

    return report_path
