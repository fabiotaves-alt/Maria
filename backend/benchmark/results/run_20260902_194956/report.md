# Relatório do Benchmark MARIA

Gerado em: 2026-09-02T19:53:32

## Modelo

| Propriedade | Valor |
|---|---:|
| Nome | Qwen2.5 3B |
| Quantização | Q4_K - Medium |
| ID real | ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M |
| Parâmetros | 3.40B (3,397,103,616) |
| n_ctx (servidor / treino) | 4096 / 32768 |
| Tamanho | 1.95 GiB |
> ℹ️ `LLAMA_NUM_CTX` (8192) é maior que o n_ctx real do servidor (4096). O contexto efetivo das execuções é 4096.

## Parâmetros do sampler

| Parâmetro | Valor |
|---|---:|
| repeat_last_n | 64 |
| repeat_penalty | 1.000 |
| frequency_penalty | 0.000 |
| presence_penalty | 0.000 |
| dry_multiplier | 0.000 |
| dry_base | 1.750 |
| dry_allowed_length | 2 |
| dry_penalty_last_n | 64 |
| top_k | 40 |
| top_p | 0.950 |
| min_p | 0.050 |
| xtc_probability | 0.000 |
| xtc_threshold | 0.100 |
| typical_p | 1.000 |
| top_n_sigma | -1.000 |
| temperature | 0.100 |

## Métricas gerais

| Métrica | Resultado |
|---|---:|
| Total de tarefas | 6 |
| Acurácia de tool calling | 0.0% |
| Taxa de confirmação | 0.0% |
| Taxa de palavras-chave | 100.0% |
| Taxa de execução | 100.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 0.0% |
| Tokens por segundo (média) | 3.9 tok/s |
| TTFT médio (1º token) | 6605.3 ms |
| Latência p50 | 26964.7 ms |
| Latência p90 | 106443.9 ms |
| Latência média | 36022.2 ms |
| Contexto OK | 100.0% |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| criar_documento | 3 | 0.0% |
| criar_planilha | 3 | 0.0% |

## Distribuição de erros

| Nenhum erro | 0 |
|---|---|

## Detalhes por execução

**Prompt do system (injetado em todas as execuções abaixo):**

```text
Voce e MARIA, uma assistente de escritorio que ajuda usuarios a criar e editar planilhas Excel e documentos Word. Responda SEMPRE em portugues do Brasil. Nunca responda em outro idioma, nem mesmo para termos tecnicos — traduza ou adapte para o portugues quando necessario. Se o usuario cumprimentar ou fizer uma pergunta geral, responda normalmente em texto, sem chamar ferramentas. Se o usuario pedir para criar ou editar arquivos, voce DEVE usar a ferramenta apropriada imediatamente, sem pedir confirmacao antes de chamar a ferramenta. O sistema de confirmacao sera tratado automaticamente apos a tool call. Nao responda apenas com texto pedindo mais detalhes quando o usuario ja forneceu instrucoes claras para criar ou editar um arquivo — preencha os campos com valores razoaveis e chame a ferramenta. Para documentos narrativos (carta, relatorio, ata, comunicado), redija o conteudo completo com no maximo 5 paragrafos curtos e chame criar_documento imediatamente. Para documentos oficiais (oficio, memorando, exposicao de motivos, mensagem ao Congresso, e-mail institucional), consulte consultar_manual_redacao com o tipo_documento apropriado ANTES de chamar criar_documento, e preencha tipo_documento_oficial no criar_documento. Se o usuario mencionar um arquivo que NAO EXISTE e pedir para edita-lo, responda em texto dizendo que o arquivo nao foi encontrado. NAO chame nenhuma ferramenta nesse caso. Se o usuario pedir para editar uma planilha que JA FOI CRIADA na conversa (ex: gastos, estoque, contatos), considere que ela existe e chame editar_planilha imediatamente com as colunas fornecidas. NAO chame listar_arquivos antes de editar uma planilha que o usuario ja mencionou. Todas as chaves no JSON de argumentos das ferramentas DEVEM estar em MINUSCULAS. O campo nome_arquivo NAO deve incluir extensao (.xlsx, .docx). Nunca duplique a extensao (ex: planilha.xlsx.xlsx). Preencha todos os campos obrigatorios das ferramentas. Para criar_documento, se o usuario nao forneceu o conteudo completo, gere um conteudo coerente e razoavel com base no que foi pedido. Mantenha as respostas curtas e objetivas, exceto quando estiver redigindo o conteudo de um documento narrativo.
```

### Execução 1 — Tarefa 3: Planilha básica (criar_planilha)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma planilha de gastos com colunas Data e Valor."
  }
]
```

**Resposta bruta do modelo:**

```text
Para criar a planilha de gastos, vamos começar com a estrutura básica. Vou criar uma planilha simples com as colunas "Data" e "Valor". Vou usar o Excel para isso.

```excel
| Data | valor |
|------|-------|
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |       |
|      |      
```

### Execução 2 — Tarefa 3: Planilha básica (criar_planilha)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma planilha de gastos com colunas Data e Valor."
  }
]
```

**Resposta bruta do modelo:**

```text
Para criar a planilha de gastos com as colunas "Data" e "Valor", você pode usar a ferramenta "criar_planilha_excel" e preencher os campos conforme necessário. Aqui está um exemplo de como você pode configurar a planilha:

```json
{
  "nome_arquivo": "planilha_gastos.xlsx",
  "colunas": ["Data", "Valor"],
  "linhas": [
    ["01/01/2023", "100"],
    ["02/01/2023", "200"],
    ["03/01/2023", "300"]
  ]
}
```

Esta planilha inclui uma coluna "Data" e uma coluna "Valor", com algumas linhas de exemplo. Você pode adicionar mais linhas conforme necessário.
```

### Execução 3 — Tarefa 3: Planilha básica (criar_planilha)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma planilha de gastos com colunas Data e Valor."
  }
]
```

**Resposta bruta do modelo:**

```text
Para criar a planilha de gastos com as colunas "Data" e "Valor", você pode usar o Excel. Vou criar uma planilha simples para você.

```excel
| Data       | valor   |
|------------|---------|
| 01/01/2023| R$ 100 |
| 02/01/2023| r$ 200 |
| 03/01/2023| r$ 300 |
| 04/01/2023| r$ 400 |
| 05/01/2023| r$ 500 |
```

Se você precisar de mais alguma coisa, por favor, me informe!
```

### Execução 4 — Tarefa 7: Documento curto (criar_documento)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um documento chamado pauta_reuniao, título Pauta, com conteúdo: reunião às 10 horas e revisão das tarefas."
  }
]
```

**Resposta bruta do modelo:**

```text
```json
{
  "nome_arquivo": "pauta_reuniao",
  "tipo_documento": "documento_narrativo",
  "conteudo": "reunião às 10 horas e revisão das tarefas."
}
```
```

### Execução 5 — Tarefa 7: Documento curto (criar_documento)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um documento chamado pauta_reuniao, título Pauta, com conteúdo: reunião às 10 horas e revisão das tarefas."
  }
]
```

**Resposta bruta do modelo:**

```text
```json
{
  "nome_arquivo": "pauta_reuniao",
  "tipo_documento": "pauta_reuniao",
  "conteudo": "reunião às 10 horas e revisão das tarefas."
}
```
```

### Execução 6 — Tarefa 7: Documento curto (criar_documento)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um documento chamado pauta_reuniao, título Pauta, com conteúdo: reunião às 10 horas e revisão das tarefas."
  }
]
```

**Resposta bruta do modelo:**

```text
```json
{
  "nome_arquivo": "pauta_reuniao",
  "tipo_documento": "carta",
  "conteudo": "Reunião às 10 horas e revisão das tarefas."
}
```
```



## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 3 | Planilha básica | Tool call incorreto ou ferramenta inesperada |
| 3 | Planilha básica | Tool call incorreto ou ferramenta inesperada |
| 3 | Planilha básica | Tool call incorreto ou ferramenta inesperada |
| 7 | Documento curto | Tool call incorreto ou ferramenta inesperada |
| 7 | Documento curto | Tool call incorreto ou ferramenta inesperada |
| 7 | Documento curto | Tool call incorreto ou ferramenta inesperada |
