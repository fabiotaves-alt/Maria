"""CLI para executar o benchmark live da MARIA."""
import argparse
import os
import sys
import time
from datetime import datetime

from .analysis.metrics import calculate_maria_metrics
from .analysis.report import generate_report
from .benchmark_config import BENCHMARK_RESULTS_DIR, BENCHMARK_WARMUP_TIMEOUT
from .runners.maria_runner import MariaRunner
from .tasks import load_all_maria_tasks

# ollama_client é um módulo local da raiz do projeto, não um pacote instalado.
MARIA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if MARIA_ROOT not in sys.path:
    sys.path.insert(0, MARIA_ROOT)

from core.ollama_client import OllamaClient, OllamaClientError  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark live do tool calling da MARIA")
    parser.add_argument("--task-ids", type=int, nargs="+", help="IDs específicos de tarefas")
    parser.add_argument("--tasks", type=int, default=None, help="Número inicial de tarefas")
    parser.add_argument("--category", type=str, help="Categoria exata, por exemplo criar_planilha")
    parser.add_argument("--output-dir", default=BENCHMARK_RESULTS_DIR, help="Diretório base dos resultados")
    parser.add_argument("--delay", type=float, default=0.0, help="Espera entre tarefas em segundos")
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


def _warmup_model() -> None:
    """Aquece o modelo uma vez antes de iniciar as tarefas do benchmark."""
    print(f"Aquecendo o modelo (timeout de warmup: {BENCHMARK_WARMUP_TIMEOUT}s)...")
    inicio = time.monotonic()

    try:
        cliente_warmup = OllamaClient(timeout=BENCHMARK_WARMUP_TIMEOUT)
        resposta = cliente_warmup.enviar_mensagem(
            mensagens=[{"role": "user", "content": "Responda apenas com a palavra ok."}],
            tools=None,
            stream=False,
        )
    except OllamaClientError as error:
        raise SystemExit(
            "Falha no warmup do modelo: não foi possível obter resposta do Ollama.\n"
            f"Detalhes: {error}\n"
            "Verifique se o Ollama está rodando (`ollama serve`) e se o modelo "
            "está instalado (`ollama pull <modelo>`) antes de rodar o benchmark."
        ) from error

    duracao_s = time.monotonic() - inicio
    print(f"Modelo aquecido em {duracao_s:.1f}s. Resposta de teste: {resposta.strip()!r}")


def main() -> int:
    args = _parse_args()
    tasks = _select_tasks(load_all_maria_tasks(), args)
    if not tasks:
        raise SystemExit("Nenhuma tarefa selecionada.")

    _warmup_model()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(args.output_dir, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"Executando {len(tasks)} tarefa(s) em sequência. Resultados: {run_dir}")

    # Um único runner reduz reconexões; a execução sequencial evita sobrecarga da GPU.
    runner = MariaRunner()
    results = []
    for index, task in enumerate(tasks, start=1):
        print(f"[{index}/{len(tasks)}] Tarefa {task.id}: {task.name}")
        result = runner.run(task)
        results.append(result)
        status = "OK" if result.runtime_ok and result.tool_correct else "FALHA"
        print(
            f"  {status} tool={result.tool_detected or '-'} "
            f"runtime={result.runtime_ok} lat={result.latency_ms:.0f}ms"
        )
        if args.delay and index < len(tasks):
            time.sleep(args.delay)

    metrics = calculate_maria_metrics(results)
    generate_report(results, metrics, run_dir)
    print("\nResumo")
    print(f"Tarefas: {metrics.total_tasks}")
    print(f"Tool accuracy: {metrics.tool_accuracy * 100:.1f}%")
    print(f"Confirmação: {metrics.confirmation_success_rate * 100:.1f}%")
    print(f"Runtime: {metrics.runtime_success_rate * 100:.1f}%")
    print(f"Latência média: {metrics.avg_latency_ms:.1f} ms")
    print(f"Relatório: {os.path.join(run_dir, 'report.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
