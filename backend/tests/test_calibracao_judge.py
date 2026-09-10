"""
Testes unitários do harness de calibração do LLM-as-judge (fase B6).

Executar:
    python -m unittest test_calibracao_judge.py
"""

import unittest


class TestCalibracaoJudge(unittest.TestCase):
    def test_concordancia_100_por_cento(self):
        from backend.benchmarks.maria_bench.analysis.calibracao_judge import calcular_concordancia
        rotulos = [{"task_id": 1, "rep": 1, "eixo": "tool_correta", "veredito_humano": "ok"}]
        vereditos = {(1, 1): {"tool_correta": "ok"}}
        resultado = calcular_concordancia(rotulos, vereditos)
        self.assertEqual(resultado["concordancia_geral"], 1.0)

    def test_concordancia_zero_por_cento(self):
        from backend.benchmarks.maria_bench.analysis.calibracao_judge import calcular_concordancia
        rotulos = [{"task_id": 1, "rep": 1, "eixo": "tool_correta", "veredito_humano": "ok"}]
        vereditos = {(1, 1): {"tool_correta": "falha"}}
        resultado = calcular_concordancia(rotulos, vereditos)
        self.assertEqual(resultado["concordancia_geral"], 0.0)

    def test_sem_comparacoes_retorna_zero_sem_excecao(self):
        from backend.benchmarks.maria_bench.analysis.calibracao_judge import calcular_concordancia
        resultado = calcular_concordancia([], {})
        self.assertEqual(resultado["n_comparacoes"], 0)
        self.assertEqual(resultado["concordancia_geral"], 0.0)


if __name__ == "__main__":
    unittest.main()
