# Relatório do Benchmark MARIA

Gerado em: 2026-09-01T18:01:21

## Modelo

| Origem | Nome |
|---|---:|
| Configurado (`LLAMA_MODEL`) | qwen2.5-omni-3b |
| Carregado (`/v1/models`) | C:\Users\Sony Vaio\.ollama\models\blobs\sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730 |

> ⚠️ **Atenção:** `LLAMA_MODEL` (qwen2.5-omni-3b) diverge do modelo efetivamente carregado no llama-server via `/v1/models` (C:\Users\Sony Vaio\.ollama\models\blobs\sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730). As execucas podem não estar usando o modelo desejado.

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 12 |
| Acurácia de tool calling | 91.7% |
| Taxa de confirmação | 91.7% |
| Taxa de palavras-chave | 91.7% |
| Taxa de execução | 91.7% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 100.0% |
| Tokens por segundo (média) | 1.1 tok/s |
| TTFT médio (1º token) | 5518.1 ms |
| Latência p50 | 73176.9 ms |
| Latência p90 | 549155.2 ms |
| Latência média | 134391.1 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| confirmacao | 3 | 100.0% |
| editar_planilha | 9 | 88.9% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| TimeoutError | 1 |

## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 15 | Confirmação de documento | TimeoutError: Tarefa excedeu o timeout de 400 segundos. |
| 21 | Negação edição | Tool call incorreto ou ferramenta inesperada |
