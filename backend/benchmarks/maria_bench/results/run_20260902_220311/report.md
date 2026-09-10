# Relatório do Benchmark MARIA

Gerado em: 2026-09-02T22:06:23

## Modelo

| Propriedade | Valor |
|---|---:|
| Nome | Qwen2.5 3B |
| Quantização | Q4_K - Medium |
| ID real | ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M |
| Parâmetros | 3.40B (3,397,103,616) |
| n_ctx (servidor / treino) | 4096 / 32768 |
| Tamanho | 1.95 GiB |
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
| Tokens por segundo (média) | 4.3 tok/s |
| TTFT médio (1º token) | 4180.3 ms |
| Latência p50 | 32748.2 ms |
| Latência p90 | 37037.2 ms |
| Latência média | 31927.1 ms |
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
Você é MARIA, assistente de escritório. Cria e edita planilhas Excel e documentos Word.
SEMPRE responda em português do Brasil. Outros idiomas apenas para termos técnicos.
Para cumprimentos, apresentações ou perguntas gerais, responda em texto livre.
Para criação ou edição de arquivos, use as ferramentas disponíveis.
O sistema de confirmação será tratado automaticamente após a tool call.
Se o usuário pedir para editar um arquivo que NÃO EXISTE, responda em texto dizendo que o arquivo não foi encontrado.
Se o usuário pedir para editar uma planilha que JÁ FOI CRIADA na conversa, considere que ela existe e chame editar_planilha imediatamente.
Chame listar_arquivos antes de editar uma planilha que o usuário NÃO mencionou na conversa.
Para criar_documento, se o usuário não forneceu o conteúdo completo, seja breve, coerente e razoável.
Mantenha as respostas CURTAS e OBJETIVAS, exceto para documentos narrativos.
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
Para criar uma planilha de gastos com colunas "Data" e "Valor", você pode seguir os passos abaixo:

1. Abra o Excel.
2. Crie uma nova planilha.
3. Na primeira linha, crie as seguintes colunas: "Data" e "Valor".
4. Na primeira coluna, insira a data do gasto.
5. Na segunda coluna, insira o valor do gasto.
6. Crie uma nova linha para cada gasto.

Isso criará uma planilha simples com as informações solicitadas.
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
Para criar a planilha de gastos com as colunas "Data" e "Valor", você pode seguir os passos abaixo:

1. Abra o Excel.
2. Crie uma nova planilha.
3. Na primeira linha, crie as seguintes colunas: "Data" e "Valor".
4. Na primeira coluna, insira a data do gasto.
5. Na segunda coluna, insira o valor do gasto.
6. Salve a planilha com um nome adequado, por exemplo, "Planilha de Gastos".

Se você precisar de mais ajuda ou tiver alguma dúvida, sinta-se à vontade para perguntar!
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
Para criar uma planilha de gastos com colunas "Data" e "Valor", você pode seguir os passos abaixo:

1. Abra o Excel.
2. Crie uma nova planilha.
3. Na primeira linha, crie as seguintes colunas: "Data" e "Valor".
4. Clique em "Formatar como tabela" para adicionar a estrutura de tabela.
5. Agora você pode adicionar dados de gastos, adicionando uma nova linha para cada despesa.

Se você precisar de mais ajuda, sinta-se à vontade para perguntar!
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
Para criar o documento chamado "pauta_reuniao" com o conteúdo "reunião às 10 horas e revisão das tarefas", você pode seguir os seguintes passos:

1. Abra o Microsoft word.
2. Crie uma nova planilha.
3. Crie uma nova coluna e insira o título "pauta".
4. Crie uma nova linha e insira o texto "reunião às 10 horas e revisão das tarefas".
5. Salve a planilha como "pauta_reuniao".

Se você precisar de mais ajuda, sinta-se à vontade para perguntar!
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
Para criar o documento chamado "pauta_reuniao" com o conteúdo "reunião às 10 horas e revisão das tarefas", você pode seguir os seguintes passos:

1. Abra o Microsoft word.
2. Crie uma nova planilha.
3. No cabeçalho da planilha, insira o título "pauta".
4. Em seguida, insira a frase "reunião às 10 horas e revisão das tarefas" no corpo da planilha.

Se você precisar de mais ajuda, sinta-se à vontade para perguntar!
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
Para criar o documento chamado "pauta_reuniao" com o conteúdo "reunião às 10 horas e revisão das tarefas", você pode seguir esses passos:

1. Crie um novo documento em Word.
2. No menu "Inserir", selecione "título".
3. Escreva "pauta".
4. No menu "inserir", selecione "texto".
5. Escreva "reunião às 10 horas e revisão das tarefas".
6. Salve o documento como "pauta_reuniao".

Se você quiser editar o documento, você pode abrir o arquivo "pauta_reuniao" e editar o conteúdo conforme necessário.
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
