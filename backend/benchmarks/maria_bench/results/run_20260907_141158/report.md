# Relatório do Benchmark MARIA

Gerado em: 2026-09-07T14:17:35

## Modelo

| Propriedade | Valor |
|---|---:|
| Quantização | Q4_K - Medium |
| ID modelo | ggml-org/Qwen2.5-Omni-7B-GGUF:Q4_K_M |
| Parâmetros | 7.62B (7,615,616,512) |
| n_ctx (servidor / treino) | 2048 / 32768 |
| Tamanho | 4.36 GiB |
> ℹ️ `LLAMA_NUM_CTX` (4096) é maior que o n_ctx real do servidor (2048). O contexto efetivo das execuções é 2048.

## Sistema

| Campo | Valor |
|-------|-------|
| Plataforma | Windows-11-10.0.26100-SP0 |
| Processador | Intel64 Family 6 Model 142 Stepping 9, GenuineIntel |
| Núcleos físicos / lógicos | 2 / 4 |
| Frequência CPU | 400.0 MHz |
| Uso CPU (pré-warmup) | 20.2% |
| RAM total | 7.89 GB |
| RAM disponível (pré-warmup) | 0.35 GB |
| Uso RAM (pré-warmup) | 95.6% |
| GPU | Não detectada (pynvml indisponível) |
| Tempo de warmup | 10.0s |

## Parâmetros do sampler

| Parâmetro | Valor |
|---|---:|
| repeat_last_n | 128 |
| repeat_penalty | 1.100 |
| frequency_penalty | 0.000 |
| presence_penalty | 0.000 |
| dry_multiplier | 0.800 |
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
| Total de tarefas | 9 |
| Acurácia de tool calling | 0.0% |
| Taxa de confirmação (todas) | 0.0% |
| Taxa de confirmação (elegíveis) | 0.0% |
| Suspeitas de falha de parser | 0 |
| Taxa de palavras-chave | 66.7% |
| Taxa de execução | 100.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 100.0% |
| Tokens por segundo (média) | 1.9 tok/s |
| TTFT médio (1º token) | 8506.0 ms |
| Latência p50 | 24111.8 ms |
| Latência p90 | 67147.7 ms |
| Latência média | 37394.7 ms |
| Contexto OK | 100.0% |
| Qualidade semântica | 100.0% |

## Qualidade Semântica

Acurácia semântica (heurística): **100.0%**

| Indicador | Ocorrências |
|---|---:|
| Título/conteúdo invertidos | 0 |
| Placeholders não preenchidos ([...]) | 0 |
| Conteúdo muito curto (<20 chars) | 0 |
| nome_arquivo com extensão (.xlsx/.docx) | 0 |
| Correções automáticas (sanitização) | 0 |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| criar_documento | 3 | 0.0% |
| criar_planilha | 3 | 0.0% |
| editar_planilha | 3 | 0.0% |

## Distribuição de erros

| Nenhum erro | 0 |
|---|---|

## Detalhes por execução

**Prompt do system (injetado em todas as execuções abaixo):**

```text
# Prompt de Sistema — MARIA, Assistente de Escritório

Você é MARIA, assistente de escritório. Cria e edita planilhas Excel e documentos Word. SEMPRE responda em português do Brasil. Para QUALQUER ação de ferramenta, responda **APENAS** com um objeto JSON, sem texto antes ou depois.

## Ferramentas disponíveis

- **criar_planilha**  
  `{"ferramenta":"criar_planilha","nome_arquivo":"...","colunas":["..."]}`

- **editar_planilha**  
  `{"ferramenta":"editar_planilha","nome_arquivo":"...","colunas":["..."]}`

- **criar_documento**  
  `{"ferramenta":"criar_documento","nome_arquivo":"...","titulo":"...","conteudo":"..."}`

**editar_documento**  
  `{"ferramenta":"criar_documento","nome_arquivo":"...","titulo":"...","conteudo":"..."}`

- **extrair_dados_planilha**  
  `{"ferramenta":"extrair_dados_planilha","nome_arquivo":"..."}`

## Regras

- `colunas` é sempre lista de strings.  
- `linhas` é lista de listas.  
- Conteúdo de documento: se o usuário não especificar, seja breve e coerente.  
- Se o arquivo não foi mencionado antes, responda em texto:  
  `Não encontrei o arquivo [nome]. Deseja listar seus arquivos?`  
- Cumprimentos e perguntas gerais: responda em texto curto (máx. 2 frases).

## Exemplos

**Usuário:** "Crie planilha com nomes e idades"  
**MARIA:**  
`{"ferramenta":"criar_planilha","nome_arquivo":"nomes_idades","colunas":["Nome","Idade"]}`

**Usuário:** "Crie um ofício solicitando reunião"  
**MARIA:**  
`{"ferramenta":"criar_documento","nome_arquivo":"oficio_reuniao","titulo":"Ofício de Solicitação de Reunião","conteudo":"Senhor(a) Diretor(a),\n\nSolicitamos reunião para discutir..."}`
```

### Execução 1 — Tarefa 5: Planilha estoque (criar_planilha)

rep 1/3: ✗ tool=— args=OK latência=67.1s tokens=38 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma planilha de estoque com Produto, SKU, Quantidade, Custo e Fornecedor."
  }
]
```

**Resposta bruta do modelo:**

```text
```json
{"ferramenta":"criar_planilha","nome_arquivo":"estoque","colunas":["Produto","SKU","Quantidade","Custo","Fornecedor"]}
```
```

### Execução 2 — Tarefa 5: Planilha estoque (criar_planilha)

rep 2/3: ✗ tool=— args=OK latência=18.0s tokens=38 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma planilha de estoque com Produto, SKU, Quantidade, Custo e Fornecedor."
  }
]
```

**Resposta bruta do modelo:**

```text
```json
{"ferramenta":"criar_planilha","nome_arquivo":"estoque","colunas":["Produto","SKU","Quantidade","Custo","Fornecedor"]}
```
```

### Execução 3 — Tarefa 5: Planilha estoque (criar_planilha)

rep 3/3: ✗ tool=— args=OK latência=17.8s tokens=38 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma planilha de estoque com Produto, SKU, Quantidade, Custo e Fornecedor."
  }
]
```

**Resposta bruta do modelo:**

```text
```json
{"ferramenta":"criar_planilha","nome_arquivo":"estoque","colunas":["Produto","SKU","Quantidade","Custo","Fornecedor"]}
```
```

### Execução 4 — Tarefa 10: Documento comunicado (criar_documento)

rep 1/3: ✗ tool=— args=OK latência=56.9s tokens=128 — erro: Tool call incorreto ou ferramenta inesperada

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
```json
{"ferramenta":"criar_documento","nome_arquivo":"comunicado_horario_atendimento","titulo":"Comunicado: Mudança no Horário de Atendimento","conteudo":"Prezados Colaboradores,\n\nInformamos que haverá uma mudança no horário de atendimento.\n\nNovo horário:\n- Segunda à Sexta-feira: 8h às 17h\n- Sábado: 9h às 13h\n\nAgradecemos pela compreensão e colaboração.\n\nAtenciosamente,"}
```
```

### Execução 5 — Tarefa 10: Documento comunicado (criar_documento)

rep 2/3: ✗ tool=— args=OK latência=62.7s tokens=131 — erro: Tool call incorreto ou ferramenta inesperada

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
```json
{
  "ferramenta": "criar_documento",
  "nome_arquivo": "comunicado_horario_atendimento",
  "titulo": "Comunicado: Mudança no Horário de Atendimento",
  "conteudo": "Prezados Colaboradores,\n\nInformamos que haverá uma mudança no horário de atendimento.\n\nNovo horário:\n- Segunda à Sexta-feira: das 8h às 17h\n\nAgradecemos pela compreensão e colaboração.\n\nAtenciosamente, Equipe."
}
```
```

### Execução 6 — Tarefa 10: Documento comunicado (criar_documento)

rep 3/3: ✗ tool=— args=OK latência=47.0s tokens=106 — erro: Tool call incorreto ou ferramenta inesperada

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
```json
{"ferramenta":"criar_documento","nome_arquivo":"comunicado_horario_atendimento","titulo":"Comunicado: Mudança no Horário de Atendimento","conteudo":"Prezados Colaboradores,\n\nInformamos que haverá uma mudança no horário de atendimento.\n\nNovo horário:\n- Segunda à Sexta-feira: 8h às 17h\n- Sábado: 9h às 13h"}}
```
```

### Execução 7 — Tarefa 13: Editar contatos (editar_planilha)

rep 1/3: ✗ tool=— args=OK latência=24.1s tokens=43 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha contatos.xlsx já foi criada."
  },
  {
    "role": "user",
    "content": "Corrija a planilha contatos para conter Nome, Email e Empresa."
  }
]
```

**Resposta bruta do modelo:**

```text
```json
{
  "ferramenta": "editar_planilha",
  "nome_arquivo": "contatos.xlsx",
  "colunas": ["Nome", "Email", "Empresa"]
}
```
```

### Execução 8 — Tarefa 13: Editar contatos (editar_planilha)

rep 2/3: ✗ tool=— args=OK latência=21.5s tokens=43 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha contatos.xlsx já foi criada."
  },
  {
    "role": "user",
    "content": "Corrija a planilha contatos para conter Nome, Email e Empresa."
  }
]
```

**Resposta bruta do modelo:**

```text
```json
{
  "ferramenta": "editar_planilha",
  "nome_arquivo": "contatos.xlsx",
  "colunas": ["Nome", "Email", "Empresa"]
}
```
```

### Execução 9 — Tarefa 13: Editar contatos (editar_planilha)

rep 3/3: ✗ tool=— args=OK latência=21.3s tokens=43 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha contatos.xlsx já foi criada."
  },
  {
    "role": "user",
    "content": "Corrija a planilha contatos para conter Nome, Email e Empresa."
  }
]
```

**Resposta bruta do modelo:**

```text
```json
{
  "ferramenta": "editar_planilha",
  "nome_arquivo": "contatos.xlsx",
  "colunas": ["Nome", "Email", "Empresa"]
}
```
```



## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 5 | Planilha estoque | Tool call incorreto ou ferramenta inesperada |
| 5 | Planilha estoque | Tool call incorreto ou ferramenta inesperada |
| 5 | Planilha estoque | Tool call incorreto ou ferramenta inesperada |
| 10 | Documento comunicado | Tool call incorreto ou ferramenta inesperada |
| 10 | Documento comunicado | Tool call incorreto ou ferramenta inesperada |
| 10 | Documento comunicado | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
