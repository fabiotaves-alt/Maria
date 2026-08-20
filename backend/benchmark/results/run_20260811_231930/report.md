# Relatório do Benchmark MARIA

Gerado em: 2026-08-12T00:18:32

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 75 |
| Acurácia de tool calling | 88.0% |
| Taxa de confirmação | 89.3% |
| Taxa de palavras-chave | 74.7% |
| Taxa de execução | 97.3% |
| Taxa de conformidade de idioma | 97.3% |
| Tokens por segundo (média) | 80861.4 tok/s |
| Latência média | 47222.0 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| ambiguidade | 9 | 88.9% |
| cancelamento | 6 | 83.3% |
| confirmacao | 6 | 100.0% |
| conversa | 6 | 100.0% |
| criar_documento | 15 | 80.0% |
| criar_planilha | 15 | 100.0% |
| editar_planilha | 18 | 77.8% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| ValueError | 2 |

## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 1 | Conversa simples | Palavras-chave esperadas não encontradas |
| 1 | Conversa simples | Palavras-chave esperadas não encontradas |
| 1 | Conversa simples | Palavras-chave esperadas não encontradas |
| 8 | Documento carta | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): titulo. |
| 8 | Documento carta | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): titulo. |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 10 | Documento comunicado | Tool call incorreto ou ferramenta inesperada |
| 12 | Editar estoque | Tool call incorreto ou ferramenta inesperada |
| 17 | Ambiguidade documento | Tool call incorreto ou ferramenta inesperada |
| 19 | Negação planilha | Tool call incorreto ou ferramenta inesperada |
| 21 | Negação edição | Palavras-chave esperadas não encontradas |
| 21 | Negação edição | Palavras-chave esperadas não encontradas |
| 21 | Negação edição | Resposta em idioma incorreto |
| 22 | Edição inexistente A | Palavras-chave esperadas não encontradas |
| 22 | Edição inexistente A | Palavras-chave esperadas não encontradas |
| 22 | Edição inexistente A | Palavras-chave esperadas não encontradas |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
