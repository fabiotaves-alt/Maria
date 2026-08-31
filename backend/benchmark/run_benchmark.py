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

import requests

from backend.core.config import LLAMA_BASE_URL, LLAMA_MODEL
from core.llama_client import LlamaClient as OllamaClient, LlamaClientError as OllamaClientError  # noqa: E402


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


def _consultar_modelo_carregado() -> str | None:
    """Consulta GET {LLAMA_BASE_URL}/v1/models e retorna o id do primeiro
    modelo carregado no llama-server, ou None se não for possível obter."""
    try:
        resp = requests.get(f"{LLAMA_BASE_URL}/v1/models", timeout=5)
        if resp.status_code == 200:
            modelos = [m.get("id", "") for m in resp.json().get("data", [])]
            return modelos[0] if modelos else None
    except requests.exceptions.RequestException:
        pass
    return None


def _warmup_model() -> str | None:
    """Aquece o modelo uma vez antes de iniciar as tarefas do benchmark.

    Retorna o nome do modelo efetivamente carregado (via /v1/models), ou None.
    Também alerta no console quando o id reportado diverge de LLAMA_MODEL.
    """
    print(f"Aquecendo o modelo (timeout de warmup: {BENCHMARK_WARMUP_TIMEOUT}s)...")
    inicio = time.monotonic()

    modelo_carregado = _consultar_modelo_carregado()
    if modelo_carregado and modelo_carregado != LLAMA_MODEL:
        print(
            f"[AVISO] LLAMA_MODEL configurado = '{LLAMA_MODEL}', mas o modelo "
            f"carregado no llama-server (/v1/models) = '{modelo_carregado}'.\n"
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
            "e o modelo qwen2.5-omni-3b está carregado antes de rodar o benchmark."
        ) from error

    duracao_s = time.monotonic() - inicio
    print(f"Modelo aquecido em {duracao_s:.1f}s. Resposta de teste: {resposta.strip()!r}")

    return modelo_carregado


def main() -> int:
    args = _parse_args()
    tasks = _select_tasks(load_all_maria_tasks(), args)
    if not tasks:
        raise SystemExit("Nenhuma tarefa selecionada.")

    modelo_carregado = _warmup_model()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(args.output_dir, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"Executando {len(tasks)} tarefa(s) em sequência. Resultados: {run_dir}")

    # Um único runner reduz reconexões; a execução sequencial evita sobrecarga da GPU.
    runner = MariaRunner(num_predict=args.num_predict)
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

    # log.json final com estrutura individual + agregado_por_tarefa
    log_final = {
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
                    modelo_carregado=modelo_carregado)

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