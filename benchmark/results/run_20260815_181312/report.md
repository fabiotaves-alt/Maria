# Relatório do Benchmark MARIA

Gerado em: 2026-08-15T18:33:13

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 75 |
| Acurácia de tool calling | 24.0% |
| Taxa de confirmação | 20.0% |
| Taxa de palavras-chave | 12.0% |
| Taxa de execução | 96.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 88.0% |
| Tokens por segundo (média) | 24.4 tok/s |
| TTFT médio (1º token) | 0.1 ms |
| Latência p50 | 5301.5 ms |
| Latência p90 | 34476.7 ms |
| Latência média | 16018.9 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| ambiguidade | 9 | 0.0% |
| cancelamento | 6 | 0.0% |
| confirmacao | 6 | 0.0% |
| conversa | 6 | 100.0% |
| criar_documento | 15 | 20.0% |
| criar_planilha | 15 | 0.0% |
| editar_planilha | 18 | 50.0% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| ValueError | 3 |

## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 3 | Planilha básica | Tool call incorreto ou ferramenta inesperada |
| 3 | Planilha básica | Tool call incorreto ou ferramenta inesperada |
| 3 | Planilha básica | Tool call incorreto ou ferramenta inesperada |
| 4 | Planilha financeira | Tool call incorreto ou ferramenta inesperada |
| 4 | Planilha financeira | Tool call incorreto ou ferramenta inesperada |
| 4 | Planilha financeira | Tool call incorreto ou ferramenta inesperada |
| 5 | Planilha estoque | Tool call incorreto ou ferramenta inesperada |
| 5 | Planilha estoque | Tool call incorreto ou ferramenta inesperada |
| 5 | Planilha estoque | Tool call incorreto ou ferramenta inesperada |
| 6 | Planilha contatos | Tool call incorreto ou ferramenta inesperada |
| 6 | Planilha contatos | Tool call incorreto ou ferramenta inesperada |
| 6 | Planilha contatos | Tool call incorreto ou ferramenta inesperada |
| 7 | Documento curto | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): nome_arquivo. |
| 7 | Documento curto | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): nome_arquivo. |
| 7 | Documento curto | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): nome_arquivo. |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 10 | Documento comunicado | Tool call incorreto ou ferramenta inesperada |
| 10 | Documento comunicado | Tool call incorreto ou ferramenta inesperada |
| 10 | Documento comunicado | Tool call incorreto ou ferramenta inesperada |
| 11 | Editar gastos | Tool call incorreto ou ferramenta inesperada |
| 11 | Editar gastos | Tool call incorreto ou ferramenta inesperada |
| 11 | Editar gastos | Tool call incorreto ou ferramenta inesperada |
| 12 | Editar estoque | Tool call incorreto ou ferramenta inesperada |
| 12 | Editar estoque | Tool call incorreto ou ferramenta inesperada |
| 12 | Editar estoque | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
| 14 | Confirmação de criação | Tool call incorreto ou ferramenta inesperada |
| 14 | Confirmação de criação | Tool call incorreto ou ferramenta inesperada |
| 14 | Confirmação de criação | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 16 | Ambiguidade planilha | Tool call incorreto ou ferramenta inesperada |
| 16 | Ambiguidade planilha | Tool call incorreto ou ferramenta inesperada |
| 16 | Ambiguidade planilha | Tool call incorreto ou ferramenta inesperada |
| 17 | Ambiguidade documento | Tool call incorreto ou ferramenta inesperada |
| 17 | Ambiguidade documento | Tool call incorreto ou ferramenta inesperada |
| 17 | Ambiguidade documento | Tool call incorreto ou ferramenta inesperada |
| 18 | Ambiguidade edição | Tool call incorreto ou ferramenta inesperada |
| 18 | Ambiguidade edição | Tool call incorreto ou ferramenta inesperada |
| 18 | Ambiguidade edição | Tool call incorreto ou ferramenta inesperada |
| 19 | Negação planilha | Tool call incorreto ou ferramenta inesperada |
| 19 | Negação planilha | Tool call incorreto ou ferramenta inesperada |
| 19 | Negação planilha | Tool call incorreto ou ferramenta inesperada |
| 20 | Negação documento | Tool call incorreto ou ferramenta inesperada |
| 20 | Negação documento | Tool call incorreto ou ferramenta inesperada |
| 20 | Negação documento | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A | Palavras-chave esperadas não encontradas |
| 22 | Edição inexistente A | Palavras-chave esperadas não encontradas |
| 22 | Edição inexistente A | Palavras-chave esperadas não encontradas |
| 23 | Edição inexistente B | Palavras-chave esperadas não encontradas |
| 23 | Edição inexistente B | Palavras-chave esperadas não encontradas |
| 23 | Edição inexistente B | Palavras-chave esperadas não encontradas |
| 24 | Nome com caminho relativo | Tool call incorreto ou ferramenta inesperada |
| 24 | Nome com caminho relativo | Tool call incorreto ou ferramenta inesperada |
| 24 | Nome com caminho relativo | Tool call incorreto ou ferramenta inesperada |
| 25 | Nome com caracteres inseguros | Tool call incorreto ou ferramenta inesperada |
| 25 | Nome com caracteres inseguros | Tool call incorreto ou ferramenta inesperada |
| 25 | Nome com caracteres inseguros | Tool call incorreto ou ferramenta inesperada |
