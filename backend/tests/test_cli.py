"""Testes da CLI unificada do benchmark (fase B5) — cli.py.

Isolados em arquivo próprio (em vez de test_maria.py) porque cobrem apenas o
parser de subcomandos e o despacho para as funções existentes — NÃO repetem a
lógica de run_benchmark/compare_runs/report (já coberta em test_maria.py).

Decisão B5: `report` opera sobre diretório run_* (posicional), não sobre
run_id SQLite — ver relatório de fechamento da B5.
"""
import sys
import unittest
from unittest.mock import patch

from backend.benchmarks.maria_bench.cli import construir_parser, main


class TestCliBenchmark(unittest.TestCase):
    def test_parser_aceita_subcomando_run(self):
        args = construir_parser().parse_args(["run", "--tasks", "3"])
        self.assertEqual(args.comando, "run")
        self.assertEqual(args.tasks, 3)

    def test_parser_aceita_subcomando_compare(self):
        args = construir_parser().parse_args(["compare", "1", "2"])
        self.assertEqual(args.comando, "compare")
        self.assertEqual(args.run_a, "1")
        self.assertEqual(args.run_b, "2")

    def test_parser_aceita_subcomando_report_com_run_dir(self):
        args = construir_parser().parse_args(
            ["report", "results/run_20260909_120000", "--detail"]
        )
        self.assertEqual(args.comando, "report")
        self.assertEqual(args.run_dir, "results/run_20260909_120000")
        self.assertTrue(args.detail)

    def test_parser_exige_subcomando(self):
        with self.assertRaises(SystemExit):
            construir_parser().parse_args([])

    def test_run_despacha_para_run_benchmark_main(self):
        argv_antes = list(sys.argv)
        with patch("backend.benchmarks.maria_bench.run_benchmark.main", return_value=0) as mock_main:
            ret = main(["run", "--tasks", "2", "--temperature", "0.5"])
        self.assertEqual(ret, 0)
        mock_main.assert_called_once_with()
        self.assertEqual(sys.argv, argv_antes)

    def test_compare_despacha_para_generate_comparison(self):
        with patch(
            "backend.benchmarks.maria_bench.compare_runs.generate_comparison",
            return_value="# comparacao",
        ) as mock_compare:
            ret = main(["compare", "3", "4"])
        self.assertEqual(ret, 0)
        mock_compare.assert_called_once_with("3", "4")


if __name__ == "__main__":
    unittest.main()
