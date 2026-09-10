# Relatório do Benchmark MARIA

Gerado em: 2026-09-03T14:10:40

## Modelo

| Propriedade | Valor |
|---|---:|
| Nome | Qwen2.5 7B |
| Quantização | Q4_K - Medium |
| ID real | ggml-org/Qwen2.5-Omni-7B-GGUF:Q4_K_M |
| Parâmetros | 7.62B (7,615,616,512) |
| n_ctx (servidor / treino) | 4096 / 32768 |
| Tamanho | 4.36 GiB |
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
| Acurácia de tool calling | 50.0% |
| Taxa de confirmação | 50.0% |
| Taxa de palavras-chave | 83.3% |
| Taxa de execução | 83.3% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 66.7% |
| Tokens por segundo (média) | 1.8 tok/s |
| TTFT médio (1º token) | 8887.2 ms |
| Latência p50 | 61377.2 ms |
| Latência p90 | 140826.6 ms |
| Latência média | 60661.3 ms |
| Contexto OK | 100.0% |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| confirmacao | 3 | 66.7% |
| criar_planilha | 3 | 33.3% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| TimeoutError | 1 |

## Detalhes por execução

**Prompt do system (injetado em todas as execuções abaixo):**

```text
Você é MARIA, assistente de escritório, você cria e edita planilhas Excel e documentos Word com ferramentas. SEMPRE responda em português do Brasil. Outros idiomas, somente para termos técnicos. Cumprimentos, apresentações ou uma pergunta geral do usuário, resposta em texto. Criação ou edição de arquivos SEMPRE CHAME A FERRAMENTA: Documentos CHAME "criar_documento": ["nome_arquivo", "titulo", "conteudo"]; Planilhas, chame "criar_planilha": ["nome_arquivo", "colunas"]; Edição de planilha chame "editar_planilha": ["nome_arquivo", "colunas"], ATENÇÃO: SEMPRE CHAME A FERRAMENTA, o sistema de confirmação será tratado automaticamente após a tool call. Para documentos SEMPRE chame "criar_documento". Se o usuário mencionar um arquivo que NÃO EXISTE e pedir para editá-lo, responda em texto dizendo que o arquivo não foi encontrado. Se o usuário pedir para editar uma PLANILHA que JÁ FOI CRIADA na conversa considere que ela EXISTE e CHAME "editar_planilha": ["nome_arquivo", "colunas"]. CHAME "listar_arquivos" antes de editar uma planilha que o usuário NÃO mencionou na conversa. Preencha todos os CAMPOS OBRIGATÓRIOS das FERRAMENTAS. Para "criar_documento", se o usuário não forneceu o conteúdo completo, seja breve, coerente e razoável com base no que foi pedido. Mantenha as respostas CURTAS e OBJETIVAS, EXCEÇÃO para documento narrativo.
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
criar_planilha: ["gastos", ["Data", "Valor"]];
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
criar_planilha: ["gastos", ["Data", "Valor"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha criada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\gastos.xlsx
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
criar_planilha: ["gastos", ["Data", "Valor"]];
```

### Execução 4 — Tarefa 15: Confirmação de documento (confirmacao)

**Prompt enviado:** *(não capturado)*

**Resposta bruta do modelo:** *(vazia)*

**Mensagem final (pós-ferramenta/confirmação):**

```text
[ERRO] Chamada ao modelo excedeu 120s (timeout por chamada). Latência: 130.0s
```

### Execução 5 — Tarefa 15: Confirmação de documento (confirmacao)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um documento de ata com título Ata e conteúdo completo sobre uma reunião."
  }
]
```

**Resposta bruta do modelo:**

```text
criar_documento: ["ata_reunião", "Ata", "Aqui está um exemplo de conteúdo para uma ata de reunião: \n\nData: [data da reunião]\nLocal: [local da reunião]\nParticipantes: [nomes dos participantes]\n\nPonto a ponto da reunião:\n\n1. [Tema do primeiro ponto]\n   - [Detalhes do primeiro ponto]\n2. [Tema do segundo ponto]\n   - [Detalhes do segundo ponto]\n3. [Tema do terceiro ponto]\n   - [Detalhes do terceiro ponto]\n\nDecisões tomadas:\n\n- [Decisão 1]\n- [Decisão 2]\n- [Decisão 3]\n\nObservações:\n\n- [Observação 1]\n- [Observação 2]\n- [Observação 3]\n\nAssinaturas: [Assinaturas dos participantes]"]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Documento criado com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\ata_reunião.docx
```

### Execução 6 — Tarefa 15: Confirmação de documento (confirmacao)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um documento de ata com título Ata e conteúdo completo sobre uma reunião."
  }
]
```

**Resposta bruta do modelo:**

```text
criar_documento: ["ata", "Ata", "Aqui está um exemplo de conteúdo para uma ata de reunião: \n\n\n\nData: [Insira a data da reunião]\nLocal: [Insira o local da reunião]\nParticipantes: [Insira os nomes dos participantes]\n\n\n\nPonto a ponto da reunião:\n\n\n\n1. Discussão sobre o projeto XYZ\n2. Análise de resultados do último mês\n3. Planejamento para o próximo trimestre\n4. Decisões tomadas\n5. Ações a serem tomadas\n6. Data da próxima reunião\n\n\n\nObservações:\n\n\n\n[Insira quaisquer observações adicionais]\n\n\n\nAssinatura dos participantes: [Insira as assinaturas dos participantes]"]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Documento criado com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\ata.docx
```



## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 3 | Planilha básica | Tool call incorreto ou ferramenta inesperada |
| 3 | Planilha básica | Tool call incorreto ou ferramenta inesperada |
| 15 | Confirmação de documento | TimeoutError: Chamada ao modelo excedeu 120s (timeout por chamada). Latência: 130.0s |
