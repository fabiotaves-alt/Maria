# Relatório do Benchmark MARIA

Gerado em: 2026-08-10T21:43:22

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 25 |
| Acurácia de tool calling | 72.0% |
| Taxa de confirmação | 68.0% |
| Taxa de palavras-chave | 44.0% |
| Taxa de execução | 92.0% |
| Latência média | 63284.8 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| ambiguidade | 3 | 66.7% |
| cancelamento | 3 | 33.3% |
| confirmacao | 2 | 100.0% |
| conversa | 2 | 100.0% |
| criar_documento | 5 | 60.0% |
| criar_planilha | 5 | 100.0% |
| editar_planilha | 5 | 60.0% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| TimeoutError | 2 |

## Tarefas com falha

| ID | Tarefa | Erro resumido |
|---:|---|---|
| 9 | Documento relatório | Tarefa excedeu o timeout de 180 segundos. |
| 10 | Documento comunicado | tool calling incorreto |
| 15 | Confirmação de documento | Tarefa excedeu o timeout de 180 segundos. |
| 17 | Ambiguidade documento | tool calling incorreto |
| 20 | Negação documento | tool calling incorreto |
| 21 | Negação edição | tool calling incorreto |
| 22 | Edição inexistente A | tool calling incorreto |
| 23 | Edição inexistente B | tool calling incorreto |
