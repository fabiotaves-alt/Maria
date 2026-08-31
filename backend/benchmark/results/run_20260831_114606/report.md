# Relatório do Benchmark MARIA

Gerado em: 2026-08-31T13:55:04

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 75 |
| Acurácia de tool calling | 88.0% |
| Taxa de confirmação | 92.0% |
| Taxa de palavras-chave | 80.0% |
| Taxa de execução | 92.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 100.0% |
| Tokens por segundo (média) | 0.0 tok/s |
| TTFT médio (1º token) | N/D |
| Latência p50 | 47309.0 ms |
| Latência p90 | 268010.1 ms |
| Latência média | 103163.6 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| ambiguidade | 9 | 100.0% |
| cancelamento | 6 | 50.0% |
| confirmacao | 6 | 100.0% |
| conversa | 6 | 100.0% |
| criar_documento | 15 | 100.0% |
| criar_planilha | 15 | 100.0% |
| editar_planilha | 18 | 66.7% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| OllamaClientError | 3 |
| TimeoutError | 3 |

## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 2 | Conversa sobre produtividade | Palavras-chave esperadas não encontradas |
| 2 | Conversa sobre produtividade | Palavras-chave esperadas não encontradas |
| 2 | Conversa sobre produtividade | Palavras-chave esperadas não encontradas |
| 15 | Confirmação de documento | TimeoutError: Tarefa excedeu o timeout de 400 segundos. |
| 15 | Confirmação de documento | TimeoutError: Tarefa excedeu o timeout de 400 segundos. |
| 15 | Confirmação de documento | TimeoutError: Tarefa excedeu o timeout de 400 segundos. |
| 20 | Negação documento | OllamaClientError: Erro na API do llama-server: status 500
Detalhes: {"error":{"code":500,"message":"Failed to parse messages: Missing tool call type: {\"function\":{\"name\":\"consultar_manual_redaca |
| 20 | Negação documento | OllamaClientError: Erro na API do llama-server: status 500
Detalhes: {"error":{"code":500,"message":"Failed to parse messages: Missing tool call type: {\"function\":{\"name\":\"consultar_manual_redaca |
| 20 | Negação documento | OllamaClientError: Erro na API do llama-server: status 500
Detalhes: {"error":{"code":500,"message":"Failed to parse messages: Missing tool call type: {\"function\":{\"name\":\"consultar_manual_redaca |
| 22 | Edição inexistente A | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
