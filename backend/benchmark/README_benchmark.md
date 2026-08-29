# Benchmark MARIA

O benchmark mede o comportamento real da MARIA usando o llama-server local e o modelo configurado, normalmente `qwen2.5-omni-3b`. Não há modo `--reference-only`: é necessário executar o llama-server e manter o modelo carregado. O relatório inclui agora a taxa de conformidade de idioma (`language_compliance_rate`) nas respostas finais, além das métricas de tool calling, confirmação, execução, erros e latência.

## Executar

A partir da raiz `MARIA/`:

```bash
llama-server -m <caminho/para/qwen2.5-omni-3b.gguf> --port 8080
python -m benchmark.run_benchmark --tasks 25
python -m benchmark.run_benchmark --task-ids 1 2 3
python -m benchmark.run_benchmark --category criar_planilha
```

Antes de qualquer tarefa, o CLI envia uma pergunta simples ao modelo, sem tools, para forçar o carregamento em memória e evitar que a primeira tarefa sofra timeout. O timeout desse warmup é de 300 segundos por padrão e pode ser configurado com `BENCHMARK_WARMUP_TIMEOUT`.

Opções úteis: `--output-dir`, para escolher a pasta de resultados, e `--delay`, para aguardar entre tarefas.

## Comparar execuções

```bash
python -m benchmark.compare_runs \
  --before benchmark/results/run_20260810_100000 \
  --after benchmark/results/run_20260811_100000
```

## Adicionar tarefa

Adicione uma instância de `MariaTask` em `tasks_core.py` ou `tasks_edges.py`, usando um ID novo, uma categoria, a mensagem do usuário e, quando aplicável, `expected_tool` e `confirm_sequence`. Tarefas de edição dependem de uma planilha existente no diretório isolado do benchmark.

Os resultados são gravados em `benchmark/results/run_<timestamp>/report.md` e `log.json`. Arquivos gerados durante a avaliação ficam em `benchmark/results/arquivos_gerados_benchmark`.
