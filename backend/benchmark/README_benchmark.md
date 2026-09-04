# Benchmark MARIA

O benchmark mede o comportamento real da MARIA usando o llama-server local e o modelo configurado, normalmente `qwen2.5-omni-3b`. Não há modo `--reference-only`: é necessário executar o llama-server e manter o modelo carregado. O relatório inclui agora a taxa de conformidade de idioma (`language_compliance_rate`) nas respostas finais, além das métricas de tool calling, confirmação, execução, erros e latência.

## Executar

A partir da raiz `MARIA/`:

```bash
llama-server -m <caminho/para/qwen2.5-omni-3b.gguf> --port 8080
python -m backend.benchmark.run_benchmark --tasks 25
python -m backend.benchmark.run_benchmark --task-ids 1 2 3
python -m backend.benchmark.run_benchmark --category criar_planilha
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

## Orçamento de tokens por tipo de resposta

Para caber no `BENCHMARK_TASK_TIMEOUT` (400s) deste hardware (CPU, sem GPU, ~1,15–1,22 tok/s), as respostas que compõem documentos narrativos usam um orçamento de tokens **reduzido** (`LLAMA_NUM_PREDICT_DOCUMENTO=300`, configurável via ENV). Antes esse valor era 600 e uma única tarefa de documento (ex.: Task 15) podia ultrapassar 400s de geração, estourando o timeout.

- `LLAMA_NUM_PREDICT_DOCUMENTO` **padrão 300** — documentos narrativos (carta, relatório, ata, comunicado).
- `LLAMA_NUM_PREDICT_CONTINUACAO` **padrão 200** — continuação após ferramenta de leitura.
- `LLAMA_NUM_PREDICT` **padrão 400** — demais respostas.

> ⚠️ Aumentar `LLAMA_NUM_PREDICT_DOCUMENTO` de volta para 600 não é recomendado neste hardware: o problema subjacente é o throughput (~1,2 tok/s), não um timeout configurável. O orçamento reduzido mantém as tarefas de documento dentro do limite enquanto o hardware for CPU-only.

## Parâmetros de sampler

Todos os parâmetros de sampler são enviados explicitamente no payload das chamadas com tools (mesmos defaults do llama-server) e podem ser ajustados via ENV. Os valores efetivos aparecem no `report.md` (seção **Parâmetros do sampler**) e no `meta.sampler_params` do `log.json`.

| Variável | Default | Descrição |
|---|---|---|
| `LLAMA_REPEAT_LAST_N` | `64` | Quantos tokens recentes considerar na penalidade de repetição |
| `LLAMA_REPEAT_PENALTY` | `1.1` | Penalidade de repetição de tokens (1.0 desativa; 1.1 evita loops degenerados, ex.: `\n` × 600) |
| `LLAMA_FREQUENCY_PENALTY` | `0.0` | Penalidade por frequência |
| `LLAMA_PRESENCE_PENALTY` | `0.0` | Penalidade por presença |
| `LLAMA_DRY_MULTIPLIER` | `0.0` | Multiplicador do sampler DRY |
| `LLAMA_DRY_BASE` | `1.75` | Base exponencial do DRY |
| `LLAMA_DRY_ALLOWED_LENGTH` | `2` | Comprimento de sequência permitido no DRY |
| `LLAMA_DRY_PENALTY_LAST_N` | `64` | Janela do DRY |
| `LLAMA_TOP_K` | `40` | Top-K sampling |
| `LLAMA_TOP_P` | `0.95` | Top-P (nucleus) sampling |
| `LLAMA_MIN_P` | `0.05` | Min-P sampling |
| `LLAMA_XTC_PROBABILITY` | `0.0` | Probabilidade do sampler XTC |
| `LLAMA_XTC_THRESHOLD` | `0.1` | Limiar do XTC |
| `LLAMA_TYPICAL_P` | `1.0` | Typical-P sampling |
| `LLAMA_TOP_N_SIGMA` | `-1.0` | Top-N-Sigma (desativado quando negativo) |
| `LLAMA_TEMPERATURE_TOOLS` | `0.1` | Temperatura (tool calling) |

Exemplo: `LLAMA_TOP_K=50 LLAMA_TEMPERATURE_TOOLS=0.4 python -m backend.benchmark.run_benchmark --tasks 25`

## Prompt e resposta bruta por execução

O `report.md` inclui a seção **Detalhes por execução**, que mostra para cada tarefa/repetição:

- **Prompt enviado** — as mensagens completas (system reforçado + histórico + usuário) em JSON.
- **Resposta bruta do modelo** — o texto cru gerado pelo modelo, antes de qualquer sobrescrita por confirmação/ferramenta/continuação.
- **Mensagem final** — a mensagem pós-processamento (ex.: caminho do arquivo criado), quando diferente da resposta bruta.

Os mesmos campos (`prompt_enviado`, `resposta_bruta_modelo`, `sampler_params`) são gravados por execução no `log.json`, permitindo comparar runs com o `compare_runs.py`.
