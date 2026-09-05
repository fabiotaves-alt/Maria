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


def _execucao_falhou(result: MariaTaskResult) -> bool:
    """True se a execução deve ser considerada falha no relatório.

    Usa o mesmo critério da lista `failed` de `generate_report`.
    """
    return (
        not result.tool_correct
        or not result.runtime_ok
        or not result.confirmation_completed
        or not result.language_ok
        or not result.keyword_match
    )


def formatar_avisos(result: MariaTaskResult) -> list[str]:
    """Lista de avisos (⚠️ ...) para exibir em linhas separadas abaixo do `rep X/Y`.

    - Correção automática (sanitização): `⚠️ corrigido campo: "antes" → "depois"`.
    - Ferramenta detectada via parser (não nativo) e, quando houve mapeamento
      de nome (case b), `"bruto" → "canônico"`.
    """
    avisos = []
    for c in result.correcoes or []:
        avisos.append(f'⚠️ corrigido {c.get("campo")}: "{c.get("antes")}" → "{c.get("depois")}"')
    if result.tool_call_fonte == "parser_posicional":
        nome_final = result.tool_nome_final or result.tool_detected
        if result.tool_nome_bruto and result.tool_nome_bruto != nome_final:
            avisos.append(f'⚠️ ferramenta detectada via parser: "{result.tool_nome_bruto}" → "{nome_final}"')
        else:
            avisos.append(f'⚠️ ferramenta detectada via parser: "{nome_final}"')
    return avisos


def _formatar_linha_resumo(result: MariaTaskResult, indice_rep: int, total_rep: int) -> str:
    """Formata a linha de resumo `rep X/Y: ...` exibida em cada execução.

    Se a execução falhou, anexa a descrição do erro.
    """
    status = "✓" if result.tool_correct else "✗"
    linha = (
        f"rep {indice_rep}/{total_rep}: {status} "
        f"tool={result.tool_detected or '—'} "
        f"args={'OK' if result.args_correct else 'DIVERGENTE'} "
        f"latência={result.latency_ms / 1000:.1f}s tokens={result.tokens_gerados}"
    )
    if _execucao_falhou(result):
        linha += f" — erro: {_diagnosticar_falha(result)}"
    return linha


def _montar_detalhes_execucao(results: list[MariaTaskResult]) -> str:
    """Renderiza, por execução, o prompt enviado e a resposta bruta do modelo.

    O texto do prompt de sistema é impresso UMA ÚNICA VEZ no topo desta seção
    (extraído da primeira execução que o contiver). Em cada bloco de execução
    individual, a mensagem role='system' é substituída pelo marcador
    'prompt do system injetado' para evitar repetição do texto completo.

    Cada execução também recebe uma linha de resumo com o status da repetição
    (rep X/Y), ferramenta detectada, validação dos argumentos, latência,
    tokens gerados e, quando aplicável, a descrição do erro.
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

    # Calcula o total de repetições por task_id para formatar "rep X/Y".
    total_por_tarefa: dict[int, int] = {}
    for r in results:
        total_por_tarefa[r.task_id] = total_por_tarefa.get(r.task_id, 0) + 1

    indice_por_tarefa: dict[int, int] = {}
    for idx, result in enumerate(results, start=1):
        linhas.append(
            f"### Execução {idx} — Tarefa {result.task_id}: {result.task_name} "
            f"({result.category})"
        )
        linhas.append("")

        indice_por_tarefa[result.task_id] = indice_por_tarefa.get(result.task_id, 0) + 1
        linhas.append(
            _formatar_linha_resumo(
                result,
                indice_por_tarefa[result.task_id],
                total_por_tarefa[result.task_id],
            )
        )
        for aviso in formatar_avisos(result):
            linhas.append(aviso)
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


def _montar_secao_semantica(metrics: MariaBenchmarkMetrics) -> str:
    """Renderiza a seção '## Qualidade Semântica' do report.md."""
    rotulos = {
        "titulo_conteudo_invertido": "Título/conteúdo invertidos",
        "placeholder_detectado": "Placeholders não preenchidos ([...])",
        "conteudo_curto": "Conteúdo muito curto (<20 chars)",
        "nome_com_extensao": "nome_arquivo com extensão (.xlsx/.docx)",
    }
    erros = metrics.semantic_errors_by_type or {}
    linhas = [
        "## Qualidade Semântica",
        "",
        f"Acurácia semântica (heurística): **{metrics.semantic_quality_rate * 100:.1f}%**",
        "",
        "| Indicador | Ocorrências |",
        "|---|---:|",
    ]
    for chave, rotulo in rotulos.items():
        linhas.append(f"| {rotulo} | {erros.get(chave, 0)} |")
    linhas.append(f"| Correções automáticas (sanitização) | {metrics.correcoes_count} |")
    return "\n".join(linhas) + "\n"


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


def _montar_secao_sistema(metricas_sistema: dict, warmup_duracao_s: float | None) -> str:
    """Monta a seção '## Sistema' do report.md a partir do snapshot coletado."""
    if not metricas_sistema:
        return ""

    linhas = ["## Sistema\n"]
    linhas.append(f"| Campo | Valor |")
    linhas.append(f"|-------|-------|")
    linhas.append(f"| Plataforma | {metricas_sistema.get('plataforma', 'N/D')} |")
    linhas.append(f"| Processador | {metricas_sistema.get('cpu_modelo', 'N/D')} |")
    linhas.append(
        f"| Núcleos físicos / lógicos | "
        f"{metricas_sistema.get('cpu_nucleos_fisicos', 'N/D')} / "
        f"{metricas_sistema.get('cpu_nucleos_logicos', 'N/D')} |"
    )
    freq = metricas_sistema.get("cpu_freq_mhz")
    linhas.append(f"| Frequência CPU | {f'{freq} MHz' if freq else 'N/D'} |")
    linhas.append(f"| Uso CPU (pré-warmup) | {metricas_sistema.get('cpu_uso_percent', 'N/D')}% |")
    linhas.append(f"| RAM total | {metricas_sistema.get('ram_total_gb', 'N/D')} GB |")
    linhas.append(
        f"| RAM disponível (pré-warmup) | "
        f"{metricas_sistema.get('ram_disponivel_gb', 'N/D')} GB |"
    )
    linhas.append(f"| Uso RAM (pré-warmup) | {metricas_sistema.get('ram_uso_percent', 'N/D')}% |")

    gpus = metricas_sistema.get("gpu", [])
    if gpus:
        for i, g in enumerate(gpus):
            prefixo = f"GPU {i}" if len(gpus) > 1 else "GPU"
            linhas.append(f"| {prefixo} | {g.get('nome', 'N/D')} |")
            linhas.append(f"| {prefixo} VRAM total | {g.get('vram_total_gb', 'N/D')} GB |")
            linhas.append(
                f"| {prefixo} VRAM livre (pré-warmup) | "
                f"{g.get('vram_livre_gb', 'N/D')} GB |"
            )
            linhas.append(
                f"| {prefixo} uso (pré-warmup) | "
                f"{g.get('gpu_uso_percent', 'N/D')}% |"
            )
    else:
        linhas.append("| GPU | Não detectada (pynvml indisponível) |")

    if warmup_duracao_s is not None:
        linhas.append(f"| Tempo de warmup | {warmup_duracao_s:.1f}s |")

    return "\n".join(linhas) + "\n"


def generate_report(
    results: list[MariaTaskResult],
    metrics: MariaBenchmarkMetrics,
    output_dir: str,
    metadados_modelo: dict | None = None,
    sampler_params: dict | None = None,
    log_final: dict | None = None,
    metricas_sistema: dict | None = None,
    warmup_duracao_s: float | None = None,
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
        modelo_id = meta.get("id") or "N/A"
        modelo_qtz = meta.get("quantizacao") or "N/A"
        linhas_modelo = [
            "## Modelo",
            "",
            "| Propriedade | Valor |",
            "|---|---:|",
            f"| Quantização | {modelo_qtz} |",
            f"| ID modelo | {modelo_id} |",
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
            "| ID modelo | Não detectado |\n"
            "\n"
            "> ERRO: Não foi possível obter metadados do modelo via /v1/models."
        )

    secao_sampler = _montar_secacao_sampler(sampler_params)
    secao_sistema = _montar_secao_sistema(metricas_sistema, warmup_duracao_s)
    secao_detalhes = _montar_detalhes_execucao(results)
    secao_semantica = _montar_secao_semantica(metrics)

    _taxa_eleg = metrics.confirmation_success_rate_elegiveis
    taxa_elegiveis = (
        f"{_taxa_eleg * 100:.1f}%"
        if isinstance(_taxa_eleg, (int, float))
        else "N/D (sem tarefas elegíveis)"
    )

    report = f"""# Relatório do Benchmark MARIA

Gerado em: {generated_at}

{secao_modelo}
{secao_sistema}
{secao_sampler}
## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | {metrics.total_tasks} |
| Acurácia de tool calling | {metrics.tool_accuracy * 100:.1f}% |
| Taxa de confirmação (todas) | {metrics.confirmation_success_rate * 100:.1f}% |
| Taxa de confirmação (elegíveis) | {taxa_elegiveis} |
| Suspeitas de falha de parser | {metrics.parse_suspeito_count} |
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
| Qualidade semântica | {metrics.semantic_quality_rate * 100:.1f}% |

{secao_semantica}
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
