# Relatório do Benchmark MARIA

Gerado em: 2026-08-31T19:10:16

## Modelo

| Origem | Nome |
|---|---:|
| Configurado (`LLAMA_MODEL`) | qwen2.5-omni-3b |
| Carregado (`/v1/models`) | ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M |

> ⚠️ **Atenção:** `LLAMA_MODEL` (qwen2.5-omni-3b) diverge do modelo efetivamente carregado no llama-server via `/v1/models` (ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M). As execucas podem não estar usando o modelo desejado.

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 75 |
| Acurácia de tool calling | 76.0% |
| Taxa de confirmação | 58.7% |
| Taxa de palavras-chave | 69.3% |
| Taxa de execução | 93.3% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 88.0% |
| Tokens por segundo (média) | 3.3 tok/s |
| TTFT médio (1º token) | 5750.9 ms |
| Latência p50 | 18615.2 ms |
| Latência p90 | 72201.3 ms |
| Latência média | 29285.8 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| ambiguidade | 9 | 100.0% |
| cancelamento | 6 | 100.0% |
| confirmacao | 6 | 50.0% |
| conversa | 6 | 100.0% |
| criar_documento | 15 | 40.0% |
| criar_planilha | 15 | 100.0% |
| editar_planilha | 18 | 66.7% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| ValueError | 5 |

## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 7 | Documento curto | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): conteudo. |
| 7 | Documento curto | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): conteudo. |
| 7 | Documento curto | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): conteudo. |
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
| 12 | Editar estoque | Tool call incorreto ou ferramenta inesperada |
| 12 | Editar estoque | Tool call incorreto ou ferramenta inesperada |
| 12 | Editar estoque | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 17 | Ambiguidade documento | Confirmação não concluída |
| 17 | Ambiguidade documento | Confirmação não concluída |
| 17 | Ambiguidade documento | Confirmação não concluída |
| 18 | Ambiguidade edição | Confirmação não concluída |
| 18 | Ambiguidade edição | Confirmação não concluída |
| 20 | Negação documento | Confirmação não concluída |
| 20 | Negação documento | Confirmação não concluída |
| 20 | Negação documento | Confirmação não concluída |
| 21 | Negação edição | Palavras-chave esperadas não encontradas |
| 21 | Negação edição | Palavras-chave esperadas não encontradas |
| 21 | Negação edição | Palavras-chave esperadas não encontradas |
| 22 | Edição inexistente A | Palavras-chave esperadas não encontradas |
| 23 | Edição inexistente B | Palavras-chave esperadas não encontradas |
| 23 | Edição inexistente B | Palavras-chave esperadas não encontradas |
| 25 | Nome com caracteres inseguros | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): conteudo. |
| 25 | Nome com caracteres inseguros | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): conteudo. |
