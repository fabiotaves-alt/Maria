# Relatório do Benchmark MARIA

Gerado em: 2026-09-03T11:51:17

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
| Acurácia de tool calling | 100.0% |
| Taxa de confirmação | 100.0% |
| Taxa de palavras-chave | 100.0% |
| Taxa de execução | 100.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 100.0% |
| Tokens por segundo (média) | 1.9 tok/s |
| TTFT médio (1º token) | 3553.3 ms |
| Latência p50 | 28802.4 ms |
| Latência p90 | 52992.6 ms |
| Latência média | 30216.2 ms |
| Contexto OK | 100.0% |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| criar_documento | 3 | 100.0% |
| editar_planilha | 3 | 100.0% |

## Distribuição de erros

| Nenhum erro | 0 |
|---|---|

## Detalhes por execução

**Prompt do system (injetado em todas as execuções abaixo):**

```text
Você é MARIA, assistente de escritório, você cria e edita planilhas Excel e documentos Word com ferramentas. SEMPRE responda em português do Brasil. Outros idiomas, somente para termos técnicos. Cumprimentos, apresentações ou uma pergunta geral do usuário, resposta em texto. Criação ou edição de arquivos SEMPRE CHAME A FERRAMENTA: Documentos CHAME "criar_documento": ["nome_arquivo", "titulo", "conteudo"]; Planilhas, chame "criar_planilha": ["nome_arquivo", "colunas"]; Edição de planilha chame "editar_planilha": ["nome_arquivo", "colunas"], ATENÇÃO: SEMPRE CHAME A FERRAMENTA, o sistema de confirmação será tratado automaticamente após a tool call. Para documentos SEMPRE chame "criar_documento". Se o usuário mencionar um arquivo que NÃO EXISTE e pedir para editá-lo, responda em texto dizendo que o arquivo não foi encontrado. Se o usuário pedir para editar uma PLANILHA que JÁ FOI CRIADA na conversa considere que ela EXISTE e CHAME "editar_planilha": ["nome_arquivo", "colunas"]. CHAME "listar_arquivos" antes de editar uma planilha que o usuário NÃO mencionou na conversa. Preencha todos os CAMPOS OBRIGATÓRIOS das FERRAMENTAS. Para "criar_documento", se o usuário não forneceu o conteúdo completo, seja breve, coerente e razoável com base no que foi pedido. Mantenha as respostas CURTAS e OBJETIVAS, EXCEÇÃO para documento narrativo.

CAMPOS OBRIGATORIOS, SIGA EXATAMENTE ESSE FORMATO.
    "criar_planilha": ["nome_arquivo", "colunas"],
    "criar_documento": ["nome_arquivo", "titulo", "conteúdo"],
    "editar_planilha": ["nome_arquivo", "colunas"],
```

### Execução 1 — Tarefa 10: Documento comunicado (criar_documento)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um comunicado formal informando a equipe sobre a mudança do horário de atendimento."
  }
]
```

**Resposta bruta do modelo:**

```text
criar_documento: ["comunicado_horario", "Comunicado Formal sobre Mudança de Horário de Atendimento", "Estimados membros da equipe, informamos que haverá uma mudança no horário de atendimento. A nova tabela de horários será implementada a partir do próximo dia 15 de maio. Por favor, verifique o novo horário em nosso sistema de controle de acesso. Agradecemos a compreensão e colaboração. Atenciosamente, [Seu Nome]"]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Documento criado com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\comunicado_horario.docx
```

### Execução 2 — Tarefa 10: Documento comunicado (criar_documento)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um comunicado formal informando a equipe sobre a mudança do horário de atendimento."
  }
]
```

**Resposta bruta do modelo:**

```text
criar_documento: ["comunicado_horario", "Comunicado Formal sobre Mudança de Horário de Atendimento", "Estimados membros da equipe, informamos que haverá uma mudança no horário de atendimento. O novo horário começa a valer a partir de [data]. Por favor, verifique e ajuste suas agendas de acordo. Agradecemos a compreensão e colaboração. Atenciosamente, [seu nome]"]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Documento criado com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\comunicado_horario.docx
```

### Execução 3 — Tarefa 10: Documento comunicado (criar_documento)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um comunicado formal informando a equipe sobre a mudança do horário de atendimento."
  }
]
```

**Resposta bruta do modelo:**

```text
criar_documento: ["comunicado_horario", "Comunicado de Mudança de Horário", "Prezados Colaboradores,

Informamos que haverá uma mudança no horário de atendimento. A nova tabela de horários será:

- Segunda a Sexta: 8h às 18h
- Sábado: 9h às 16h

Por favor, verifique e ajuste seus horários de trabalho de acordo com as novas configurações.

Atenciosamente,
[Seu Nome]"]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Documento criado com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\comunicado_horario.docx
```

### Execução 4 — Tarefa 11: Editar gastos (editar_planilha)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha gastos.xlsx já foi criada."
  },
  {
    "role": "user",
    "content": "Edite a planilha gastos para incluir as colunas Data, Valor e Categoria."
  }
]
```

**Resposta bruta do modelo:**

```text
editar_planilha: ["gastos.xlsx", ["Data", "Valor", "Categoria"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha atualizada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\gastos.xlsx
```

### Execução 5 — Tarefa 11: Editar gastos (editar_planilha)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha gastos.xlsx já foi criada."
  },
  {
    "role": "user",
    "content": "Edite a planilha gastos para incluir as colunas Data, Valor e Categoria."
  }
]
```

**Resposta bruta do modelo:**

```text
editar_planilha: ["gastos.xlsx", ["Data", "Valor", "Categoria"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha atualizada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\gastos.xlsx
```

### Execução 6 — Tarefa 11: Editar gastos (editar_planilha)

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha gastos.xlsx já foi criada."
  },
  {
    "role": "user",
    "content": "Edite a planilha gastos para incluir as colunas Data, Valor e Categoria."
  }
]
```

**Resposta bruta do modelo:**

```text
editar_planilha: ["gastos.xlsx", ["Data", "Valor", "Categoria"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha atualizada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\gastos.xlsx
```



## Tarefas com falha

Nenhuma tarefa falhou.
