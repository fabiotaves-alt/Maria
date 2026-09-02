"""CLI para executar o benchmark live da MARIA."""
import argparse
import os
import sys
import time
from datetime import datetime

from .analysis.metrics import calculate_maria_metrics, aggregate_by_task
from .analysis.report import generate_report
from .benchmark_config import BENCHMARK_RESULTS_DIR, BENCHMARK_WARMUP_TIMEOUT, BENCHMARK_REPETICOES
from .runners.maria_runner import MariaRunner
from .tasks import load_all_maria_tasks

# llama_client é um módulo local da raiz do projeto, não um pacote instalado.
MARIA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if MARIA_ROOT not in sys.path:
    sys.path.insert(0, MARIA_ROOT)

import re
import requests

# Alias no módulo: permite patch consistente via unittest.mock e evita
# import local dentro de funções.
_requests = requests

from backend.core.config import LLAMA_BASE_URL, LLAMA_MODEL, LLAMA_NUM_CTX
from core.llama_client import (
    LlamaClient as OllamaClient,
    LlamaClientError as OllamaClientError,
    montar_sampler_params,
)  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark live do tool calling da MARIA")
    parser.add_argument("--task-ids", type=int, nargs="+", help="IDs específicos de tarefas")
    parser.add_argument("--tasks", type=int, default=None, help="Número inicial de tarefas")
    parser.add_argument("--category", type=str, help="Categoria exata, por exemplo criar_planilha")
    parser.add_argument("--output-dir", default=BENCHMARK_RESULTS_DIR, help="Diretório base dos resultados")
    parser.add_argument("--delay", type=float, default=0.0, help="Espera entre tarefas em segundos")
    parser.add_argument("--repeticoes", type=int, default=BENCHMARK_REPETICOES,
                        help="Número de repetições por tarefa (padrão: BENCHMARK_REPETICOES)")
    parser.add_argument("--num-predict", type=int, default=None,
                        help="Override do número de tokens previstos pelo modelo no benchmark")
    return parser.parse_args()


def _select_tasks(tasks, args):
    if args.task_ids:
        requested = set(args.task_ids)
        selected = [task for task in tasks if task.id in requested]
        missing = sorted(requested - {task.id for task in selected})
        if missing:
            print(f"Aviso: IDs não encontrados: {missing}")
        return selected
    if args.category:
        return [task for task in tasks if task.category.value == args.category]
    if args.tasks is not None:
        return tasks[:max(args.tasks, 0)]
    return tasks


def _parece_caminho_local(id_modelo: str) -> bool:
    """Retorna True quando o id do modelo parece um caminho de arquivo local
    (blob do Ollama, caminho com separadores, ou extensão .gguf)."""
    if not id_modelo:
        return False
    return (
        os.sep in id_modelo
        or "/" in id_modelo
        or id_modelo.lower().endswith(".gguf")
        or re.match(r"^[0-9a-f]{64}$", id_modelo) is not None
        or id_modelo.startswith("sha256-")
    )


def _derivar_rotulo_modelo(n_params: int | float, n_vocab: int) -> str:
    """Deriva um rótulo legível (ex.: 'Qwen2.5 3B') a partir da contagem de
    parâmetros e do tamanho do vocabulário.

    Mapeia n_params para o tamanho conhecido da família Qwen2.5 mais próximo
    e usa n_vocab == 151936 como sinal de família Qwen2.5.
    """
    if not n_params:
        return ""

    # Tamanhos conhecidos da família Qwen2.5 (em bilhões)
    tamanhos_qwen25 = (0.5, 1.5, 3, 7, 14, 32, 72)
    bilhoes = n_params / 1e9
    tamanho = min(tamanhos_qwen25, key=lambda t: abs(t - bilhoes))

    if tamanho == int(tamanho):
        rotulo = f"{int(tamanho)}B"
    else:
        rotulo = f"{tamanho}B"

    if n_vocab in (151936, 152064, 152128):
        return f"Qwen2.5 {rotulo}"
    return rotulo


_FTYPE_PARA_NOME: dict[int, str] = {
    0: "F32",
    1: "F16",
    2: "Q4_0",
    3: "Q4_1",
    6: "Q5_0",
    7: "Q5_1",
    8: "Q8_0",
    9: "Q2_K",
    10: "Q3_K_S",
    11: "Q3_K_M",
    12: "Q3_K_L",
    13: "Q4_K_S",
    14: "Q4_K_M",
    15: "Q5_K_S",
    16: "Q5_K_M",
    17: "Q6_K",
    18: "Q8_K",
    30: "IQ2_XXS",
    31: "IQ2_XS",
    32: "IQ2_S",
    33: "IQ2_M",
    34: "IQ1_S",
    35: "IQ1_M",
    36: "Q4_0_4_4",
    37: "Q4_0_4_8",
    38: "Q4_0_8_8",
    39: "TQ1_0",
    40: "TQ2_0",
}


def _ftype_para_nome(ftype: int | str | None) -> str:
    """Converte o campo ftype (enum GGML ou string) para nome legível."""
    if ftype is None:
        return ""
    if isinstance(ftype, str):
        return ftype
    return _FTYPE_PARA_NOME.get(ftype, f"tipo-{ftype}")


def _formatar_tamanho(tamanho_bytes: int | None) -> str:
    """Formata bytes como string legível (ex.: 2098976768 -> '1.95 GiB')."""
    if not tamanho_bytes:
        return ""
    gib = tamanho_bytes / (1024 ** 3)
    if gib >= 1:
        return f"{gib:.2f} GiB"
    return f"{tamanho_bytes / (1024 ** 2):.1f} MiB"


def _obter_metadados_modelo() -> dict | None:
    """Consulta GET {LLAMA_BASE_URL}/v1/models e retorna metadados do primeiro
    modelo carregado no llama-server, ou None se não for possível obter.

    O dicionário retornado contém:
        id, id_exibicao, quantizacao, n_params, n_vocab, n_ctx, n_ctx_train,
        tamanho_bytes, rotulo_tamanho, tamanho_legivel
    """
    try:
        resp = _requests.get(f"{LLAMA_BASE_URL}/v1/models", timeout=5)
        if resp.status_code != 200:
            return None
        modelos = resp.json().get("data", [])
        if not modelos:
            return None
        primeiro = modelos[0]
        meta = primeiro.get("meta", {}) or {}
        id_modelo = primeiro.get("id", "") or ""
    except (_requests.exceptions.RequestException, ValueError, KeyError):
        return None

    n_params = meta.get("n_params")
    n_vocab = meta.get("n_vocab") or 0
    n_ctx = meta.get("n_ctx")
    n_ctx_train = meta.get("n_ctx_train")
    tamanho_bytes = meta.get("size")
    ftype_raw = meta.get("ftype")

    quantizacao = _ftype_para_nome(ftype_raw)
    rotulo = _derivar_rotulo_modelo(n_params, n_vocab) if n_params else ""
    tamanho_legivel = _formatar_tamanho(tamanho_bytes)

    # Se o id é um caminho local/blob, usa o rótulo derivado como exibição
    id_exibicao = rotulo if (_parece_caminho_local(id_modelo) and rotulo) else id_modelo

    return {
        "id": id_modelo,
        "id_exibicao": id_exibicao,
        "quantizacao": quantizacao,
        "n_params": n_params,
        "n_vocab": n_vocab,
        "n_ctx": n_ctx,
        "n_ctx_train": n_ctx_train,
        "tamanho_bytes": tamanho_bytes,
        "rotulo_tamanho": rotulo,
        "tamanho_legivel": tamanho_legivel,
    }


def _warmup_model() -> tuple[str | None, dict | None]:
    """Aquece o modelo uma vez antes de iniciar as tarefas do benchmark.

    Retorna (nome_do_modelo_carregado, metadados_do_modelo).
    Alerta no console quando o id reportado diverge de LLAMA_MODEL de forma
    relevante (não apenas por ser caminho de blob do mesmo modelo).
    """
    print(f"Aquecendo o modelo (timeout de warmup: {BENCHMARK_WARMUP_TIMEOUT}s)...")
    inicio = time.monotonic()

    metadados_modelo = _obter_metadados_modelo()
    modelo_carregado = (metadados_modelo or {}).get("id")
    id_exibicao = (metadados_modelo or {}).get("id_exibicao") or modelo_carregado

    if modelo_carregado and modelo_carregado != LLAMA_MODEL:
        eh_local = _parece_caminho_local(modelo_carregado)
        rotulo = (metadados_modelo or {}).get("rotulo_tamanho", "")
        if not eh_local or not rotulo:
            print(
                f"[AVISO] LLAMA_MODEL configurado = '{LLAMA_MODEL}', mas o modelo "
                f"carregado no llama-server (/v1/models) = '{id_exibicao}'.\n"
                "As execuções podem não estar usando o modelo desejado."
            )
        elif rotulo and LLAMA_MODEL and rotulo.split()[-1].lower() not in LLAMA_MODEL.lower():
            print(
                f"[AVISO] LLAMA_MODEL configurado = '{LLAMA_MODEL}', mas o modelo "
                f"carregado no llama-server parece ser '{rotulo}'.\n"
                "As execuções podem não estar usando o modelo desejado."
            )

    try:
        cliente_warmup = OllamaClient(timeout=BENCHMARK_WARMUP_TIMEOUT)
        resposta = cliente_warmup.enviar_mensagem(
            mensagens=[{"role": "user", "content": "Responda apenas com a palavra ok."}],
            tools=None,
            stream=False,
        )
    except OllamaClientError as error:
        raise SystemExit(
            "Falha no warmup do modelo: não foi possível obter resposta do llama-server.\n"
            f"Detalhes: {error}\n"
            "Verifique se o llama-server está rodando (`llama-server -m <modelo.gguf> --port 8080`) "
            f"e o modelo {LLAMA_MODEL} está carregado antes de rodar o benchmark."
        ) from error

    duracao_s = time.monotonic() - inicio
    print(f"Modelo aquecido em {duracao_s:.1f}s. Resposta de teste: {resposta.strip()!r}")
    print(f"Modelo carregado: {id_exibicao or 'N/D'}")

    return modelo_carregado, metadados_modelo


def main() -> int:
    args = _parse_args()
    tasks = _select_tasks(load_all_maria_tasks(), args)
    if not tasks:
        raise SystemExit("Nenhuma tarefa selecionada.")

    modelo_carregado, metadados_modelo = _warmup_model()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(args.output_dir, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"Executando {len(tasks)} tarefa(s) em sequência. Resultados: {run_dir}")

    # Um único runner reduz reconexões; a execução sequencial evita sobrecarga da GPU.
    runner = MariaRunner(num_predict=args.num_predict, modelo_carregado=modelo_carregado)
    resultados_individuais_todas_tarefas = []
    agregados_todas_tarefas = []

    for index, task in enumerate(tasks, start=1):
        print(f"[{index}/{len(tasks)}] Tarefa {task.id}: {task.name} ({BENCHMARK_REPETICOES}x)")

        def _mostrar_resultado_individual(indice_execucao, resultado, task=task):
            status = "✓" if resultado.tool_correct else "✗"
            esperado = (
                f" (esperado: {task.expected_tool})"
                if not resultado.tool_correct and task.expected_tool
                else ""
            )
            print(
                f"    rep {indice_execucao}/{BENCHMARK_REPETICOES}: {status} "
                f"tool={resultado.tool_detected or '—'}{esperado} "
                f"args={'OK' if resultado.args_correct else 'DIVERGENTE'} "
                f"latência={resultado.latency_ms / 1000:.1f}s tokens={resultado.tokens_gerados}"
            )

        resultados_task = runner.run_repeated(
            task, BENCHMARK_REPETICOES, apos_cada_execucao=_mostrar_resultado_individual
        )
        resultados_individuais_todas_tarefas.extend(resultados_task)
        agregados_todas_tarefas.append(aggregate_by_task(resultados_task))

        metricas_parciais = calculate_maria_metrics(resultados_individuais_todas_tarefas)
        print(
            f"    → acumulado: tool_accuracy={metricas_parciais.tool_accuracy * 100:.1f}% "
            f"confirmação={metricas_parciais.confirmation_success_rate * 100:.1f}% "
            f"latência média={metricas_parciais.avg_latency_ms / 1000:.1f}s"
        )

    # log.json final com estrutura individual + agregado_por_tarefa + meta
    log_final = {
        "meta": {
            "modelo_configurado": LLAMA_MODEL,
            "modelo_carregado": modelo_carregado,
            "metadados_modelo": metadados_modelo,
            "llama_num_ctx_config": LLAMA_NUM_CTX,
            "sampler_params": montar_sampler_params(),
        },
        "individual": [r.__dict__ for r in resultados_individuais_todas_tarefas],
        "agregado_por_tarefa": [a.__dict__ for a in agregados_todas_tarefas],
    }
    log_path = os.path.join(run_dir, "log.json")
    with open(log_path, "w", encoding="utf-8") as log_file:
        import json
        json.dump(log_final, log_file, ensure_ascii=False, indent=2)

    generate_report(resultados_individuais_todas_tarefas,
                    calculate_maria_metrics(resultados_individuais_todas_tarefas),
                    run_dir,
                    modelo_configurado=LLAMA_MODEL,
                    modelo_carregado=modelo_carregado,
                    metadados_modelo=metadados_modelo,
                    sampler_params=montar_sampler_params(),
                    log_final=log_final)

    print("\nResumo")
    print(f"Tarefas: {calculate_maria_metrics(resultados_individuais_todas_tarefas).total_tasks}")
    print(f"Tool accuracy: {calculate_maria_metrics(resultados_individuais_todas_tarefas).tool_accuracy * 100:.1f}%")
    print(f"Confirmação: {calculate_maria_metrics(resultados_individuais_todas_tarefas).confirmation_success_rate * 100:.1f}%")
    print(f"Runtime: {calculate_maria_metrics(resultados_individuais_todas_tarefas).runtime_success_rate * 100:.1f}%")
    print(f"Latência média: {calculate_maria_metrics(resultados_individuais_todas_tarefas).avg_latency_ms:.1f} ms")
    print(f"Relatório: {os.path.join(run_dir, 'report.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())