# Relatório do Benchmark MARIA

Gerado em: 2026-09-02T23:52:27

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
| Acurácia de tool calling | 100.0% |
| Taxa de confirmação | 100.0% |
| Taxa de palavras-chave | 100.0% |
| Taxa de execução | 100.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 100.0% |
| Tokens por segundo (média) | 1.9 tok/s |
| TTFT médio (1º token) | 9010.0 ms |
| Latência p50 | 6495.9 ms |
| Latência p90 | 37549.4 ms |
| Latência média | 12564.1 ms |
| Contexto OK | 100.0% |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| criar_planilha | 3 | 100.0% |

## Distribuição de erros

| Nenhum erro | 0 |
|---|---|

## Detalhes por execução

**Prompt do system (injetado em todas as execuções abaixo):**

```text
Você é MARIA, assistente de escritório, você cria e edita planilhas Excel e documentos Word com ferramentas. SEMPRE responda em português do Brasil. Outros idiomas, somente para termos técnicos. Cumprimentos, apresentações ou uma pergunta geral do usuário, resposta em texto. Criação ou edição de arquivos SEMPRE CHAME A FERRAMENTA: Documentos CHAME "criar_documento": ["nome_arquivo", "titulo", "conteudo"]; Planilhas, chame "criar_planilha": ["nome_arquivo", "colunas"]; Edição de planilha chame "editar_planilha": ["nome_arquivo", "colunas"], ATENÇÃO: SEMPRE CHAME A FERRAMENTA, o sistema de confirmação será tratado automaticamente após a tool call. Instruções claras para criar ou editar um arquivo devem ser imediatamente atendidas, preencha os campos com valores razoáveis e chame a ferramenta. Para documentos SEMPRE chame "criar_documento". Se o usuário mencionar um arquivo que NÃO EXISTE e pedir para editá-lo, responda em texto dizendo que o arquivo não foi encontrado. Se o usuário pedir para editar uma planilha que JÁ FOI CRIADA na conversa (ex: gastos, estoque, contatos), considere que ela existe e chame "editar_planilha": ["nome_arquivo", "colunas"] IMEDIATAMENTE com as informações fornecidas. CHAME "listar_arquivos" antes de editar uma planilha que o usuário NÃO mencionou na conversa. Preencha todos os CAMPOS OBRIGATÓRIOS das FERRAMENTAS. Para "criar_documento", se o usuário não forneceu o conteúdo completo, seja breve, coerente e razoável com base no que foi pedido. Mantenha as respostas CURTAS e OBJETIVAS, EXCEÇÃO para documento narrativo.

CAMPOS_OBRIGATORIOS 
    "criar_planilha": ["nome_arquivo", "colunas"],
    "criar_documento": ["nome_arquivo", "titulo", "conteúdo"],
    "editar_planilha": ["nome_arquivo", "colunas"],
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
criar_planilha: ["gastos", ["Data", "Valor"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha criada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\gastos.xlsx
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
criar_planilha: ["gastos", ["Data", "Valor"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha criada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\gastos.xlsx
```



## Tarefas com falha

Nenhuma tarefa falhou.
