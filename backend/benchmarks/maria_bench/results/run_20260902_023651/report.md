# Relatório do Benchmark MARIA

Gerado em: 2026-09-02T02:38:42

## Modelo

| Origem | Nome |
|---|---:|
| Configurado (`LLAMA_MODEL`) | qwen2.5-omni-3b |
| Carregado (`/v1/models`) | Qwen2.5 3B |
| Modelo (derivado) | Qwen2.5 3B |
| Quantização | Q4_K - Medium |
| Parâmetros | 3.40B (3,397,103,616) |
| n_ctx (servidor / treino) | 2048 / 32768 |
| Tamanho | 1.95 GiB |
> ℹ️ `LLAMA_NUM_CTX` (8192) é maior que o n_ctx real do servidor (2048). O contexto efetivo das execuções é 2048.

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 3 |
| Acurácia de tool calling | 100.0% |
| Taxa de confirmação | 100.0% |
| Taxa de palavras-chave | 100.0% |
| Taxa de execução | 100.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 0.0% |
| Tokens por segundo (média) | 2.5 tok/s |
| TTFT médio (1º token) | 28803.3 ms |
| Latência p50 | 10625.9 ms |
| Latência p90 | 138496.9 ms |
| Latência média | 37197.3 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| criar_planilha | 3 | 100.0% |

## Distribuição de erros

| Nenhum erro | 0 |
|---|---|

## Tarefas com falha

Nenhuma tarefa falhou.
