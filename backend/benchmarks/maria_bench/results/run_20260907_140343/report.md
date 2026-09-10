# Relatório do Benchmark MARIA

Gerado em: 2026-09-07T14:08:38

## Modelo

| Propriedade | Valor |
|---|---:|
| Quantização | Q4_K - Medium |
| ID modelo | ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M |
| Parâmetros | 3.40B (3,397,103,616) |
| n_ctx (servidor / treino) | 2048 / 32768 |
| Tamanho | 1.95 GiB |
> ℹ️ `LLAMA_NUM_CTX` (4096) é maior que o n_ctx real do servidor (2048). O contexto efetivo das execuções é 2048.

## Sistema

| Campo | Valor |
|-------|-------|
| Plataforma | Windows-11-10.0.26100-SP0 |
| Processador | Intel64 Family 6 Model 142 Stepping 9, GenuineIntel |
| Núcleos físicos / lógicos | 2 / 4 |
| Frequência CPU | 2900.0 MHz |
| Uso CPU (pré-warmup) | 10.2% |
| RAM total | 7.89 GB |
| RAM disponível (pré-warmup) | 4.99 GB |
| Uso RAM (pré-warmup) | 36.7% |
| GPU | Não detectada (pynvml indisponível) |
| Tempo de warmup | 7.7s |

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
| Total de tarefas | 18 |
| Acurácia de tool calling | 0.0% |
| Taxa de confirmação (todas) | 0.0% |
| Taxa de confirmação (elegíveis) | 0.0% |
| Suspeitas de falha de parser | 0 |
| Taxa de palavras-chave | 66.7% |
| Taxa de execução | 100.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 100.0% |
| Tokens por segundo (média) | 3.9 tok/s |
| TTFT médio (1º token) | 3808.1 ms |
| Latência p50 | 9544.4 ms |
| Latência p90 | 33731.9 ms |
| Latência média | 16374.8 ms |
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
| criar_documento | 6 | 0.0% |
| criar_planilha | 6 | 0.0% |
| editar_planilha | 6 | 0.0% |

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

rep 1/3: ✗ tool=— args=OK latência=28.5s tokens=36 — erro: Tool call incorreto ou ferramenta inesperada

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
`{"ferramenta":"criar_planilha","nome_arquivo":"estoque","colunas":["Produto","SKU","Quantidade","Custo","Fornecedor"]}`
```

### Execução 2 — Tarefa 5: Planilha estoque (criar_planilha)

rep 2/3: ✗ tool=— args=OK latência=12.1s tokens=52 — erro: Tool call incorreto ou ferramenta inesperada

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
{
  "ferramenta": "criar_planilha",
  "nome_arquivo": "estoque",
  "colunas": ["Produto", "SKU", "Quantidade", "Custo", "Fornecedor"]
}
```
```

### Execução 3 — Tarefa 5: Planilha estoque (criar_planilha)

rep 3/3: ✗ tool=— args=OK latência=9.0s tokens=36 — erro: Tool call incorreto ou ferramenta inesperada

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
`{"ferramenta":"criar_planilha","nome_arquivo":"estoque","colunas":["Produto","SKU","Quantidade","Custo","Fornecedor"]}`
```

### Execução 4 — Tarefa 6: Planilha contatos (criar_planilha)

rep 1/3: ✗ tool=— args=OK latência=8.3s tokens=29 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma planilha de contatos com Nome, Email e Telefone."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"criar_planilha","nome_arquivo":"contatos","colunas":["Nome","Email","Telefone"]}`
```

### Execução 5 — Tarefa 6: Planilha contatos (criar_planilha)

rep 2/3: ✗ tool=— args=OK latência=7.7s tokens=29 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma planilha de contatos com Nome, Email e Telefone."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"criar_planilha","nome_arquivo":"contatos","colunas":["Nome","Email","Telefone"]}`
```

### Execução 6 — Tarefa 6: Planilha contatos (criar_planilha)

rep 3/3: ✗ tool=— args=OK latência=7.7s tokens=29 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma planilha de contatos com Nome, Email e Telefone."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"criar_planilha","nome_arquivo":"contatos","colunas":["Nome","Email","Telefone"]}`
```

### Execução 7 — Tarefa 8: Documento carta (criar_documento)

rep 1/3: ✗ tool=— args=OK latência=52.8s tokens=262 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma carta de apresentação em documento Word, com texto completo e formal."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"criar_documento","nome_arquivo":"carta_apresentacao","titulo":"Carta de Apresentação"," Conteudo":"Aqui está a carta de apresentação:\n\nSenhor(a) [Nome do destinatário],\n\nCom muito prazer me apresento à vocês. Sou [Seu nome] e sou [seu cargo ou função]. Estou aqui hoje para compartilhar um pouco sobre minha experiência e habilidades que me tornam ideal para o [cargo ou posição desejada]. Tenho uma vasta experiência em [especificar sua área de especialização], onde atuei com sucesso em [exemplos de projetos ou tarefas relevantes]. Além disso, tenho uma forte capacidade de comunicação e trabalho em equipe, habilidades que acredito serem fundamentais para qualquer ambiente de trabalho. Me sinto extremamente empolgado(a) por contribuir para a equipe e ajudar no desenvolvimento da empresa. Espero poder conversar mais sobre essa oportunidade e como posso contribuir. Agradeço pela atenção e espero ter a oportunidade de discutir essa questão em detalhes. Com cordialidade, [seu nome]."}`
```

### Execução 8 — Tarefa 8: Documento carta (criar_documento)

rep 2/3: ✗ tool=— args=OK latência=11.1s tokens=47 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma carta de apresentação em documento Word, com texto completo e formal."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"criar_documento","nome_arquivo":"carta_apresentacao","titulo":"Carta de Apresentação","Conteudo":"Aqui está a carta de apresentação completa e formal."}`
```

### Execução 9 — Tarefa 8: Documento carta (criar_documento)

rep 3/3: ✗ tool=— args=OK latência=27.6s tokens=135 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie uma carta de apresentação em documento Word, com texto completo e formal."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"criar_documento","nome_arquivo":"carta_apresentacao","titulo":"Carta de Apresentação","Conteudo":"Aqui está a carta de apresentação:\n\nSr./Sra. [Nome do destinatário],\n\nCom muito prazer, me apresento como [seu nome]. Sou [seu cargo] na [sua empresa]. Meus principais responsabilidades incluem [especificar suas funções principais]. Estou ansioso para contribuir com meu conhecimento e experiência no seu projeto. Espero que possamos trabalhar juntos em breve."}`
```

### Execução 10 — Tarefa 9: Documento relatório (criar_documento)

rep 1/3: ✗ tool=— args=OK latência=31.6s tokens=138 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um documento word com um relatório sobre a reunião de hoje com introdução, decisões e próximos passos em texto corrido. Na reunião foi discutida a expansão da empresa com aporte de 25 por cento do capital social atual da empresa, dividido igualmente entre os sócios, a proposta foi aceita."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"criar_documento","nome_arquivo":"relatorio_reuniao","titulo":"Relatório da Reunião de Hoje","Conteudo":"Senhor(a) diretor(a),\n\nNa reunião de hoje, foram discutidas as mudanças na estratégia da empresa. Foi apresentada uma proposta para expandir o negócio, solicitando um aporte de 25% do capital social atual da empresa, que será distribuído igualmente entre os sócios.\n\nA proposta foi aceita e agora estamos prontos para avançar com essa nova etapa estratégica."}`
```

### Execução 11 — Tarefa 9: Documento relatório (criar_documento)

rep 2/3: ✗ tool=— args=OK latência=26.1s tokens=127 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um documento word com um relatório sobre a reunião de hoje com introdução, decisões e próximos passos em texto corrido. Na reunião foi discutida a expansão da empresa com aporte de 25 por cento do capital social atual da empresa, dividido igualmente entre os sócios, a proposta foi aceita."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"criar_documento","nome_arquivo":"relatorio_reuniao","titulo":"Relatório da Reunião de Hoje","conteudo":"Senhor(a) diretor(a),\n\nNa reunião de hoje, foram discutidas as mudanças na estrutura organizacional e a expansão da empresa. Foi apresentada uma proposta para a expansão, que prevê um aumento de 25% no capital social atual da empresa, dividido igualmente entre os sócios.\n\nA proposta foi aceita pelos sócios presentes."}`
```

### Execução 12 — Tarefa 9: Documento relatório (criar_documento)

rep 3/3: ✗ tool=— args=OK latência=20.5s tokens=97 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "user",
    "content": "Crie um documento word com um relatório sobre a reunião de hoje com introdução, decisões e próximos passos em texto corrido. Na reunião foi discutida a expansão da empresa com aporte de 25 por cento do capital social atual da empresa, dividido igualmente entre os sócios, a proposta foi aceita."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"criar_documento","nome_arquivo":"relatorio_reuniao","titulo":"Relatório da Reunião de Hoje","conteudo":"Senhor(a) diretor(a),\n\nNa reunião de hoje, foi discutida a expansão da empresa com o aporte de 25% do capital social atual da empresa, dividido igualmente entre os sócios.\nA proposta foi aceita."}`
```

### Execução 13 — Tarefa 12: Editar estoque (editar_planilha)

rep 1/3: ✗ tool=— args=OK latência=10.0s tokens=33 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha estoque.xlsx já foi criada."
  },
  {
    "role": "user",
    "content": "Atualize a planilha estoque com Produto, Quantidade e Estoque mínimo."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"editar_planilha","nome_arquivo":"estoque.xlsx","colunas":["Produto","Quantidade","Estoque_minimo"]}`
```

### Execução 14 — Tarefa 12: Editar estoque (editar_planilha)

rep 2/3: ✗ tool=— args=OK latência=8.5s tokens=33 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha estoque.xlsx já foi criada."
  },
  {
    "role": "user",
    "content": "Atualize a planilha estoque com Produto, Quantidade e Estoque mínimo."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"editar_planilha","nome_arquivo":"estoque.xlsx","colunas":["Produto","Quantidade","Estoque_minimo"]}`
```

### Execução 15 — Tarefa 12: Editar estoque (editar_planilha)

rep 3/3: ✗ tool=— args=OK latência=8.5s tokens=33 — erro: Tool call incorreto ou ferramenta inesperada

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha estoque.xlsx já foi criada."
  },
  {
    "role": "user",
    "content": "Atualize a planilha estoque com Produto, Quantidade e Estoque mínimo."
  }
]
```

**Resposta bruta do modelo:**

```text
`{"ferramenta":"editar_planilha","nome_arquivo":"estoque.xlsx","colunas":["Produto","Quantidade","Estoque_minimo"]}`
```

### Execução 16 — Tarefa 13: Editar contatos (editar_planilha)

rep 1/3: ✗ tool=— args=OK latência=9.1s tokens=29 — erro: Tool call incorreto ou ferramenta inesperada

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
`{"ferramenta":"editar_planilha","nome_arquivo":"contatos.xlsx","colunas":["Nome","Email","Empresa"]}`
```

### Execução 17 — Tarefa 13: Editar contatos (editar_planilha)

rep 2/3: ✗ tool=— args=OK latência=7.7s tokens=29 — erro: Tool call incorreto ou ferramenta inesperada

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
`{"ferramenta":"editar_planilha","nome_arquivo":"contatos.xlsx","colunas":["Nome","Email","Empresa"]}`
```

### Execução 18 — Tarefa 13: Editar contatos (editar_planilha)

rep 3/3: ✗ tool=— args=OK latência=7.7s tokens=29 — erro: Tool call incorreto ou ferramenta inesperada

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
`{"ferramenta":"editar_planilha","nome_arquivo":"contatos.xlsx","colunas":["Nome","Email","Empresa"]}`
```



## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 5 | Planilha estoque | Tool call incorreto ou ferramenta inesperada |
| 5 | Planilha estoque | Tool call incorreto ou ferramenta inesperada |
| 5 | Planilha estoque | Tool call incorreto ou ferramenta inesperada |
| 6 | Planilha contatos | Tool call incorreto ou ferramenta inesperada |
| 6 | Planilha contatos | Tool call incorreto ou ferramenta inesperada |
| 6 | Planilha contatos | Tool call incorreto ou ferramenta inesperada |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 8 | Documento carta | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 9 | Documento relatório | Tool call incorreto ou ferramenta inesperada |
| 12 | Editar estoque | Tool call incorreto ou ferramenta inesperada |
| 12 | Editar estoque | Tool call incorreto ou ferramenta inesperada |
| 12 | Editar estoque | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
| 13 | Editar contatos | Tool call incorreto ou ferramenta inesperada |
