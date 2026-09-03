# Relatório do Benchmark MARIA

Gerado em: 2026-09-03T13:48:18

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
| Total de tarefas | 3 |
| Acurácia de tool calling | 66.7% |
| Taxa de confirmação | 66.7% |
| Taxa de palavras-chave | 100.0% |
| Taxa de execução | 100.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 100.0% |
| Tokens por segundo (média) | 3.4 tok/s |
| TTFT médio (1º token) | 7972.3 ms |
| Latência p50 | 22026.1 ms |
| Latência p90 | 25014.7 ms |
| Latência média | 21807.6 ms |
| Contexto OK | 100.0% |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| criar_documento | 3 | 66.7% |

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
criar_documento: ["comunicado_horario", "Mudanca_horario", "equipe"]
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
criar_documento: ["comunicado_hora_atendimento", "Mudanca_horario", "A equipe de atendimento da nossa empresa está informando a todos que a mudança do horário de atendimento será efetivada a partir de [data_inicial] até [data_final]. A nova hora de atendimento será [novo_horario]. Agradecemos a compreensão e esperamos que a mudança seja benéfica para a eficiência do atendimento."]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Documento criado com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\comunicado_hora_atendimento.docx
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
criar_documento: ["comunicado_hora_atendimento", "Mudanca_horario", "A equipe de atendimento da nossa empresa informa que haverá uma mudança no horário de atendimento. A partir de agora, os horários de atendimento serão alterados conforme a tabela abaixo. Agradecemos a compreensão e esperamos que a mudança seja benéfica para todos os envolvidos."];
```



## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 10 | Documento comunicado | Tool call incorreto ou ferramenta inesperada |
