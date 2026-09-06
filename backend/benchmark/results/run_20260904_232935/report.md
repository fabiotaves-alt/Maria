# Relatório do Benchmark MARIA

Gerado em: 2026-09-04T23:31:14

## Modelo

| Propriedade | Valor |
|---|---:|
| Quantização | Q4_K - Medium |
| ID modelo | ggml-org/Qwen2.5-Omni-7B-GGUF:Q4_K_M |
| Parâmetros | 7.62B (7,615,616,512) |
| n_ctx (servidor / treino) | 4096 / 32768 |
| Tamanho | 4.36 GiB |
## Parâmetros do sampler

| Parâmetro | Valor |
|---|---:|
| repeat_last_n | 64 |
| repeat_penalty | 1.100 |
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
| Taxa de confirmação (todas) | 100.0% |
| Taxa de confirmação (elegíveis) | N/D (sem tarefas elegíveis) |
| Suspeitas de falha de parser | 0 |
| Taxa de palavras-chave | 0.0% |
| Taxa de execução | 100.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 100.0% |
| Tokens por segundo (média) | 1.4 tok/s |
| TTFT médio (1º token) | 10237.3 ms |
| Latência p50 | 8678.7 ms |
| Latência p90 | 68863.0 ms |
| Latência média | 16479.0 ms |
| Contexto OK | 100.0% |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| editar_planilha | 6 | 0.0% |

## Distribuição de erros

| Nenhum erro | 0 |
|---|---|

## Detalhes por execução

**Prompt do system (injetado em todas as execuções abaixo):**

```text
Você é MARIA, brasileira, assistente de escritório. Além de interagir com o usuário você CRIA e EDITA planilhas Excel e documentos Word usando FERRAMENTAS. SEMPRE responda em português do Brasil.

## Como chamar uma ferramenta
Para criar ou editar arquivo, responda APENAS com a chamada, em UMA linha, sem texto antes ou depois, sem ponto final:
- Planilha nova: criar_planilha: ["nome_arquivo", ["Coluna1", "Coluna2"]]
- Documento novo: criar_documento: ["nome_arquivo", "Título", "conteúdo"]
- Editar planilha: editar_planilha: ["nome_arquivo", ["Coluna1", "Coluna2"]]

Regras: "colunas" é SEMPRE lista de strings; NÃO adicione explicações à chamada; nomes inseguros ("/", "..", "*") são corrigidos pelo sistema — chame normalmente; preencha TODOS os campos obrigatórios. A confirmação é automática após a tool call.


## Conteúdo de documento
Em "criar_documento", se o usuário não deu o conteúdo completo, seja breve, coerente e razoável. Documento narrativo pode ser mais longo; demais respostas, CURTAS.

## Correção de erro
Ao receber ERRO de chamada inválida (campo ausente, tipo incorreto, nome inválido), corrija SOMENTE o campo apontado e chame de novo na próxima resposta, sem desculpas nem perguntas.
```

### Execução 1 — Tarefa 22: Edição inexistente A (verificar antes) (editar_planilha)

rep 1/3: ✗ tool=editar_planilha args=OK latência=55.5s tokens=21 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Edite a planilha estoque com a coluna preco."
  }
]
```

**Resposta bruta do modelo:**

```text
editar_planilha: ["estoque.xlsx", ["Preço", "Quantidade", "Descrição"]]
```

### Execução 2 — Tarefa 22: Edição inexistente A (verificar antes) (editar_planilha)

rep 2/3: ✗ tool=editar_planilha args=OK latência=10.8s tokens=21 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Edite a planilha estoque com a coluna preco."
  }
]
```

**Resposta bruta do modelo:**

```text
editar_planilha: ["estoque.xlsx", ["Preço", "Quantidade", "Descrição"]]
```

### Execução 3 — Tarefa 22: Edição inexistente A (verificar antes) (editar_planilha)

rep 3/3: ✗ tool=editar_planilha args=OK latência=7.5s tokens=12 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Edite a planilha estoque com a coluna preco."
  }
]
```

**Resposta bruta do modelo:**

```text
editar_planilha: ["estoque", ["Preço"]]
```

### Execução 4 — Tarefa 23: Edição inexistente B (verificar antes) (editar_planilha)

rep 1/3: ✗ tool=editar_planilha args=OK latência=9.5s tokens=13 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Atualize a planilha clientes com as colunas nome e email."
  }
]
```

**Resposta bruta do modelo:**

```text
editar_planilha: ["clientes", ["nome", "email"]]
```

### Execução 5 — Tarefa 23: Edição inexistente B (verificar antes) (editar_planilha)

rep 2/3: ✗ tool=editar_planilha args=OK latência=7.7s tokens=13 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Atualize a planilha clientes com as colunas nome e email."
  }
]
```

**Resposta bruta do modelo:**

```text
editar_planilha: ["clientes", ["nome", "email"]]
```

### Execução 6 — Tarefa 23: Edição inexistente B (verificar antes) (editar_planilha)

rep 3/3: ✗ tool=editar_planilha args=OK latência=7.8s tokens=13 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Atualize a planilha clientes com as colunas nome e email."
  }
]
```

**Resposta bruta do modelo:**

```text
editar_planilha: ["clientes", ["nome", "email"]]
```



## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 22 | Edição inexistente A (verificar antes) | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A (verificar antes) | Tool call incorreto ou ferramenta inesperada |
| 22 | Edição inexistente A (verificar antes) | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B (verificar antes) | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B (verificar antes) | Tool call incorreto ou ferramenta inesperada |
| 23 | Edição inexistente B (verificar antes) | Tool call incorreto ou ferramenta inesperada |
