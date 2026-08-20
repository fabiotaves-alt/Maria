# Relatório do Benchmark MARIA

Gerado em: 2026-08-16T09:37:30

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 75 |
| Acurácia de tool calling | 74.7% |
| Taxa de confirmação | 54.7% |
| Taxa de palavras-chave | 40.0% |
| Taxa de execução | 64.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 88.0% |
| Tokens por segundo (média) | 333.7 tok/s |
| TTFT médio (1º token) | 0.1 ms |
| Latência p50 | 45454.3 ms |
| Latência p90 | 122204.2 ms |
| Latência média | 57450.9 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| ambiguidade | 9 | 88.9% |
| cancelamento | 6 | 100.0% |
| confirmacao | 6 | 50.0% |
| conversa | 6 | 66.7% |
| criar_documento | 15 | 80.0% |
| criar_planilha | 15 | 100.0% |
| editar_planilha | 18 | 44.4% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| ValueError | 27 |

## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 2 | Conversa sobre produtividade | Tool call incorreto ou ferramenta inesperada |
| 2 | Conversa sobre produtividade | Tool call incorreto ou ferramenta inesperada |
| 3 | Planilha básica | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 3 | Planilha básica | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 3 | Planilha básica | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 4 | Planilha financeira | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 4 | Planilha financeira | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 4 | Planilha financeira | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 5 | Planilha estoque | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 5 | Planilha estoque | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 5 | Planilha estoque | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 6 | Planilha contatos | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 6 | Planilha contatos | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 6 | Planilha contatos | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 11 | Editar gastos | ValueError: Não foi possível executar 'editar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 11 | Editar gastos | ValueError: Não foi possível executar 'editar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 11 | Editar gastos | ValueError: Não foi possível executar 'editar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 12 | Editar estoque | ValueError: Arquivo 'estoque.xlsx.xlsx' não encontrado na pasta de arquivos gerados. |
| 12 | Editar estoque | ValueError: Arquivo 'estoque.xlsx.xlsx' não encontrado na pasta de arquivos gerados. |
| 12 | Editar estoque | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 13 | Editar contatos | ValueError: Arquivo 'contatos.xlsx.xlsx' não encontrado na pasta de arquivos gerados. |
| 13 | Editar contatos | ValueError: Arquivo 'contatos.xlsx.xlsx' não encontrado na pasta de arquivos gerados. |
| 13 | Editar contatos | ValueError: Arquivo 'contatos.xlsx.xlsx' não encontrado na pasta de arquivos gerados. |
| 14 | Confirmação de criação | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 14 | Confirmação de criação | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 14 | Confirmação de criação | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 17 | Ambiguidade documento | Tool call incorreto ou ferramenta inesperada |
| 21 | Negação edição | Tool call incorreto ou ferramenta inesperada |
| 21 | Negação edição | Tool call incorreto ou ferramenta inesperada |
| 21 | Negação edição | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
| 24 | Nome com caminho relativo | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 24 | Nome com caminho relativo | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
| 24 | Nome com caminho relativo | ValueError: Não foi possível executar 'criar_planilha': campo(s) obrigatório(s) ausente(s) ou vazio(s): colunas. |
