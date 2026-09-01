# Relatório do Benchmark MARIA

Gerado em: 2026-09-01T15:45:01

## Modelo

| Origem | Nome |
|---|---:|
| Configurado (`LLAMA_MODEL`) | qwen2.5-omni-3b |
| Carregado (`/v1/models`) | C:\Users\Sony Vaio\.ollama\models\blobs\sha256-4a188102020e9c9530b687fd6400f775c45e90a0d7baafe65bd0a36963fbb7ba |

> ⚠️ **Atenção:** `LLAMA_MODEL` (qwen2.5-omni-3b) diverge do modelo efetivamente carregado no llama-server via `/v1/models` (C:\Users\Sony Vaio\.ollama\models\blobs\sha256-4a188102020e9c9530b687fd6400f775c45e90a0d7baafe65bd0a36963fbb7ba). As execucas podem não estar usando o modelo desejado.

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 75 |
| Acurácia de tool calling | 82.7% |
| Taxa de confirmação | 92.0% |
| Taxa de palavras-chave | 85.3% |
| Taxa de execução | 100.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 96.0% |
| Tokens por segundo (média) | 2.7 tok/s |
| TTFT médio (1º token) | 6258.9 ms |
| Latência p50 | 23000.5 ms |
| Latência p90 | 101743.5 ms |
| Latência média | 42779.6 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| ambiguidade | 9 | 100.0% |
| cancelamento | 6 | 100.0% |
| confirmacao | 6 | 50.0% |
| conversa | 6 | 100.0% |
| criar_documento | 15 | 93.3% |
| criar_planilha | 15 | 100.0% |
| editar_planilha | 18 | 50.0% |

## Distribuição de erros

| Nenhum erro | 0 |
|---|---|

## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | Tool call incorreto ou ferramenta inesperada |
| 17 | Ambiguidade documento | Confirmação não concluída |
| 17 | Ambiguidade documento | Confirmação não concluída |
| 21 | Negação edição | Tool call incorreto ou ferramenta inesperada |
| 21 | Negação edição | Tool call incorreto ou ferramenta inesperada |
| 21 | Negação edição | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B | Tool call incorreto ou ferramenta inesperada |
| 25 | Nome com caracteres inseguros | Tool call incorreto ou ferramenta inesperada |
