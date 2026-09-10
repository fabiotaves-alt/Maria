# Relatório do Benchmark MARIA

Gerado em: 2026-09-01T20:30:29

## Modelo

| Origem | Nome |
|---|---:|
| Configurado (`LLAMA_MODEL`) | qwen2.5-omni-3b |
| Carregado (`/v1/models`) | C:\Users\Sony Vaio\.ollama\models\blobs\sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730 |

> ⚠️ **Atenção:** `LLAMA_MODEL` (qwen2.5-omni-3b) diverge do modelo efetivamente carregado no llama-server via `/v1/models` (C:\Users\Sony Vaio\.ollama\models\blobs\sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730). As execucas podem não estar usando o modelo desejado.

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 75 |
| Acurácia de tool calling | 98.7% |
| Taxa de confirmação | 94.7% |
| Taxa de palavras-chave | 93.3% |
| Taxa de execução | 97.3% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 96.0% |
| Tokens por segundo (média) | 1.1 tok/s |
| TTFT médio (1º token) | 5418.2 ms |
| Latência p50 | 47848.7 ms |
| Latência p90 | 193200.5 ms |
| Latência média | 87642.6 ms |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| ambiguidade | 9 | 100.0% |
| cancelamento | 6 | 83.3% |
| confirmacao | 6 | 100.0% |
| conversa | 6 | 100.0% |
| criar_documento | 15 | 100.0% |
| criar_planilha | 15 | 100.0% |
| editar_planilha | 18 | 100.0% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| TimeoutError | 1 |
| ValueError | 1 |

## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 15 | Confirmação de documento | ValueError: Não foi possível executar 'criar_documento': campo(s) obrigatório(s) ausente(s) ou vazio(s): nome_arquivo, titulo, conteudo. |
| 20 | Negação documento | TimeoutError: Uma chamada de continuação (leitura) excedeu o timeout de 400 segundos. |
| 20 | Negação documento | Confirmação não concluída |
| 20 | Negação documento | Confirmação não concluída |
| 22 | Edição inexistente A | Palavras-chave esperadas não encontradas |
