# Relatório do Benchmark MARIA

Gerado em: 2026-08-16T11:11:00

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 75 |
| Acurácia de tool calling | 76.0% |
| Taxa de confirmação | 80.0% |
| Taxa de palavras-chave | 85.3% |
| Taxa de execução | 97.3% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 88.0% |
| Tokens por segundo (média) | 3.3 tok/s |
| TTFT médio (1º token) | 0.1 ms |
| Latência p50 | 51101.4 ms |
| Latência p90 | 122291.1 ms |
| Latência média | 56685.3 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| ambiguidade | 9 | 55.6% |
| cancelamento | 6 | 50.0% |
| confirmacao | 6 | 50.0% |
| conversa | 6 | 100.0% |
| criar_documento | 15 | 66.7% |
| criar_planilha | 15 | 93.3% |
| editar_planilha | 18 | 88.9% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| ValueError | 2 |

## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 4 | Planilha financeira | Tool call incorreto ou ferramenta inesperada |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | ValueError: Ferramenta desconhecida: listar_arquivos |
| 13 | Editar contatos | ValueError: Ferramenta desconhecida: listar_arquivos |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 17 | Ambiguidade documento | Tool call incorreto ou ferramenta inesperada |
| 18 | Ambiguidade edição | Tool call incorreto ou ferramenta inesperada |
| 18 | Ambiguidade edição | Tool call incorreto ou ferramenta inesperada |
| 18 | Ambiguidade edição | Tool call incorreto ou ferramenta inesperada |
| 20 | Negação documento | Tool call incorreto ou ferramenta inesperada |
| 20 | Negação documento | Tool call incorreto ou ferramenta inesperada |
| 20 | Negação documento | Tool call incorreto ou ferramenta inesperada |
