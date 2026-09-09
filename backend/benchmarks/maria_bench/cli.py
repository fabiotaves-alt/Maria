"""CLI unificada do benchmark MARIA (fase B5).

Wrapper fino sobre run_benchmark.py, compare_runs.py e analysis/report.py —
nao reimplementa logica, apenas oferece subcomandos.

Uso:
    python -m backend.benchmarks.maria_bench.cli run --tasks 5
    python -m backend.benchmarks.maria_bench.cli compare <run_a> <run_b>
    python -m backend.benchmarks.maria_bench.cli report <run_dir> --detail

Escopo adiado (ver PROGRESSO_DESENVOLVIMENTO.md): --ctx-size, --system-prompt,
empacotamento e subcomando `judge` (B6). `report` opera sobre run_* (log.json).
"""
import argparse
import sys


def _cmd_run(args: argparse.Namespace) -> int:
    from . import run_benchmark

    # run_benchmark.main() le sys.argv via _parse_args() (diagnostico T0 da B5):
    # monta argv sintetico e delega — sem duplicar selecao/execucao/report.
    argv = ["maria-bench run"]
    if args.task_ids:
        argv += ["--task-ids"] + [str(i) for i in args.task_ids]
    if args.tasks is not None:
        argv += ["--tasks", str(args.tasks)]
    if args.category is not None:
        argv += ["--category", args.category]
    if args.repeticoes is not None:
        argv += ["--repeticoes", str(args.repeticoes)]
    if args.num_predict is not None:
        argv += ["--num-predict", str(args.num_predict)]
    if args.temperature is not None:
        argv += ["--temperature", str(args.temperature)]
    if args.detail:
        argv += ["--detail"]

    argv_original = sys.argv
    sys.argv = argv
    try:
        return run_benchmark.main()
    finally:
        sys.argv = argv_original


def _cmd_compare(args: argparse.Namespace) -> int:
    from .compare_runs import generate_comparison

    print(generate_comparison(args.run_a, args.run_b))
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    import json
    import os

    from .analysis.metrics import calculate_maria_metrics
    from .analysis.report import generate_report
    from .compare_runs import carregar_resultados_de_log

    log_path = os.path.join(args.run_dir, "log.json")
    if not os.path.isfile(log_path):
        raise SystemExit(f"log.json não encontrado em {args.run_dir}")
    with open(log_path, encoding="utf-8") as log_file:
        log_final = json.load(log_file)
    if not isinstance(log_final, dict) or "individual" not in log_final:
        raise SystemExit(
            f"log.json em formato inesperado em {log_path} "
            "(esperado dict com 'meta'/'individual')."
        )

    meta = log_final.get("meta", {}) or {}
    resultados = carregar_resultados_de_log(args.run_dir)
    metricas = calculate_maria_metrics(resultados)

    # Regenera report.md no PROPRIO diretorio (sobrescreve). metadados_modelo
    # remontado do subconjunto preservado no meta do log.json.
    generate_report(
        resultados,
        metricas,
        args.run_dir,
        metadados_modelo={
            "id": meta.get("id_modelo"),
            "quantizacao": meta.get("modelo_quantizacao"),
            "n_ctx": meta.get("ctx_size_detectado"),
        },
        sampler_params=meta.get("sampler_params"),
        log_final=log_final,
        metricas_sistema=meta.get("metricas_sistema"),
        warmup_duracao_s=meta.get("warmup_duracao_s"),
        detail=args.detail,
    )
    print(f"report.md regenerado em {os.path.join(args.run_dir, 'report.md')}")
    return 0


def _adicionar_args_run(p_run):
    p_run.add_argument("--tasks", type=int, default=None, help="Número inicial de tarefas")
    p_run.add_argument("--task-ids", type=int, nargs="+", default=None, help="IDs específicos")
    p_run.add_argument("--category", type=str, default=None, help="Categoria exata")
    p_run.add_argument("--repeticoes", type=int, default=None, help="Repetições por tarefa")
    p_run.add_argument("--num-predict", type=int, default=None, help="Override de max_tokens")
    p_run.add_argument("--temperature", type=float, default=None, help="Override de temperatura")
    p_run.add_argument("--detail", action="store_true", help="Report detalhado")


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maria-bench",
        description="CLI unificada do benchmark MARIA (run / report / compare).",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_run = subparsers.add_parser("run", help="Executa o benchmark.")
    _adicionar_args_run(p_run)
    p_run.set_defaults(func=_cmd_run)

    p_compare = subparsers.add_parser("compare", help="Compara dois runs.")
    p_compare.add_argument("run_a", help="run_* (log.json) ou run_id SQLite")
    p_compare.add_argument("run_b", help="run_* (log.json) ou run_id SQLite")
    p_compare.set_defaults(func=_cmd_compare)

    p_report = subparsers.add_parser("report", help="Regenera o report.md de um run.")
    p_report.add_argument("run_dir", help="Diretório do run (ex.: run_20260909_120000)")
    p_report.add_argument("--detail", action="store_true", help="Report detalhado")
    p_report.set_defaults(func=_cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
