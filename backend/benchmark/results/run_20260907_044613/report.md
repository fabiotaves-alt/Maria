# Relatório do Benchmark MARIA

Gerado em: 2026-09-07T04:50:07

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
| Uso CPU (pré-warmup) | 3.9% |
| RAM total | 7.89 GB |
| RAM disponível (pré-warmup) | 5.63 GB |
| Uso RAM (pré-warmup) | 28.6% |
| GPU | Não detectada (pynvml indisponível) |
| Tempo de warmup | 13.2s |

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
| Total de tarefas | 5 |
| Acurácia de tool calling | 80.0% |
| Taxa de confirmação (todas) | 100.0% |
| Taxa de confirmação (elegíveis) | 100.0% |
| Suspeitas de falha de parser | 0 |
| Taxa de palavras-chave | 100.0% |
| Taxa de execução | 0.0% |
| Taxa de conformidade de idioma | 100.0% |
| Acurácia de argumentos | 0.0% |
| Tokens por segundo (média) | 2.6 tok/s |
| TTFT médio (1º token) | 11188.8 ms |
| Latência p50 | 39638.7 ms |
| Latência p90 | 83105.8 ms |
| Latência média | 46778.6 ms |
| Contexto OK | 100.0% |
| Qualidade semântica | 80.0% |

## Qualidade Semântica

Acurácia semântica (heurística): **80.0%**

| Indicador | Ocorrências |
|---|---:|
| Título/conteúdo invertidos | 0 |
| Placeholders não preenchidos ([...]) | 0 |
| Conteúdo muito curto (<20 chars) | 0 |
| nome_arquivo com extensão (.xlsx/.docx) | 1 |
| Correções automáticas (sanitização) | 0 |

## Métricas por categoria

| Categoria | Total | Acurácia de tool calling |
|---|---:|---:|
| criar_planilha | 5 | 80.0% |

## Distribuição de erros

| Tipo | Ocorrências |
|---|---:|
| DadosIncompletos | 5 |

## Detalhes por execução

**Prompt do system (injetado em todas as execuções abaixo):**

```text
Você é MARIA, assistente de escritório. Cria e edita planilhas Excel e documentos Word usando ferramentas. SEMPRE responda em português do Brasil.

## Como chamar uma ferramenta
Para criar ou editar arquivo, responda APENAS com a chamada, em UMA linha, sem texto antes ou depois, sem ponto final:
- Planilha nova: criar_planilha: ["nome_arquivo", ["Coluna1", "Coluna2"]]
- Documento novo: criar_documento: ["nome_arquivo", "Título", "conteúdo"]
- Editar planilha: editar_planilha: ["nome_arquivo", ["Coluna1", "Coluna2"]]

Regras: "colunas" é SEMPRE lista de strings; NÃO adicione explicações à chamada; nomes inseguros ("/", "..", "*") são corrigidos pelo sistema — chame normalmente; preencha TODOS os campos obrigatórios. A confirmação é automática após a tool call.

## Quando NÃO chamar ferramenta
- Cumprimentos, apresentações ou perguntas gerais: responda em texto curto.
- Editar planilha JÁ CRIADA na conversa: ela EXISTE, chame "editar_planilha".
- Editar planilha NÃO mencionada antes: chame "listar_arquivos" primeiro.
- Arquivo mencionado que NÃO EXISTE: responda em texto dizendo que o arquivo não foi encontrado.
- Se o usuário pedir para editar/criar um arquivo e você NÃO tiver certeza absoluta de que ele existe (foi mencionado antes na conversa), NÃO chame a ferramenta — responda em texto que o arquivo não foi encontrado.

## Extrair dados de planilha existente
Antes de criar_planilha ou editar_planilha para TRANSFORMAR, TRADUZIR, FILTRAR, CALCULAR ou REORGANIZAR dados que já existem em uma planilha, chame extrair_dados_planilha para obter os dados reais. NUNCA invente dados que deveriam vir de um arquivo existente.

Formato da chamada (mesmo padrão das demais, em UMA linha, sem texto antes ou depois):
- extrair_dados_planilha: ["nome_arquivo"]
- extrair_dados_planilha: ["nome_arquivo", offset]  (offset começa em 0; omita ou use 0 na primeira chamada)

Fluxo:
1. Chame extrair_dados_planilha com offset 0 (ou omitido).
2. Se a resposta trouxer "tem_mais": true, chame de novo com offset igual ao "proximo_offset" recebido, repetindo até "tem_mais": false.
3. Processe TODOS os dados extraídos e só então chame criar_planilha ou editar_planilha com o resultado em "linhas".

Planilhas grandes demais para uma única chamada de escrita: use o padrão "salvar e continuar" — cada chamada a editar_planilha SOBRESCREVE o arquivo inteiro, então inclua em "linhas" TODOS os dados já processados até aquele ponto (os anteriores + o novo lote), nunca apenas o lote mais recente.

## Conteúdo de documento
Em "criar_documento", se o usuário não deu o conteúdo completo, seja breve, coerente e razoável. Documento narrativo pode ser mais longo; demais respostas, CURTAS.

## Correção de erro
Ao receber ERRO de chamada inválida (campo ausente, tipo incorreto, nome inválido), corrija SOMENTE o campo apontado e chame de novo na próxima resposta, sem desculpas nem perguntas.
```

### Execução 1 — Tarefa 26: Tradução de planilha (Mandarim → Inglês) (criar_planilha)

rep 1/5: ✓ tool=criar_planilha args=DIVERGENTE latência=72.1s tokens=83 — erro: DadosIncompletos: coluna 'english description' não encontrada no arquivo gerado.

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha produtos_mandarim.xlsx está disponível na pasta de arquivos."
  },
  {
    "role": "user",
    "content": "Tenho uma planilha chamada 'produtos_mandarim' com produtos descritos em Mandarim. Preencha a coluna 'english description' traduzindo a coluna 'product' para inglês e salve o resultado como 'produtos_traduzidos'."
  }
]
```

**Resposta bruta do modelo:**

```text
extrair_dados_planilha: ['produtos_mandarim', 0]
criar_planilha: ['produtos_traduzidos', ["English description", "product"]]
- extrair_dados_planilha: ["produtos_mandarim.xlsx"]- criar_planilha: ["produtos_mandarim.xlsx", ["model", "product", "english_description", "NCM"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha criada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\produtos_mandarim_1.xlsx
```

### Execução 2 — Tarefa 26: Tradução de planilha (Mandarim → Inglês) (criar_planilha)

rep 2/5: ✗ tool=editar_planilha args=DIVERGENTE latência=39.6s tokens=82 — erro: DadosIncompletos: arquivo gerado não tem nenhuma linha de dados.

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha produtos_mandarim.xlsx está disponível na pasta de arquivos."
  },
  {
    "role": "user",
    "content": "Tenho uma planilha chamada 'produtos_mandarim' com produtos descritos em Mandarim. Preencha a coluna 'english description' traduzindo a coluna 'product' para inglês e salve o resultado como 'produtos_traduzidos'."
  }
]
```

**Resposta bruta do modelo:**

```text
extrair_dados_planilha: ['produtos_mandarim', 0]
criar_planilha: ['produtos_traduzidos', ["product", "english_description"]]
- extrair_dados_planilha: ["produtos_mandarim"]- editar_planilha: ["produtos_mandarim.xlsx", ["model", "product", "english description", "NCM"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha atualizada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\produtos_mandarim.xlsx
```

### Execução 3 — Tarefa 26: Tradução de planilha (Mandarim → Inglês) (criar_planilha)

rep 3/5: ✓ tool=criar_planilha args=DIVERGENTE latência=39.3s tokens=82 — erro: DadosIncompletos: arquivo gerado não tem nenhuma linha de dados.

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha produtos_mandarim.xlsx está disponível na pasta de arquivos."
  },
  {
    "role": "user",
    "content": "Tenho uma planilha chamada 'produtos_mandarim' com produtos descritos em Mandarim. Preencha a coluna 'english description' traduzindo a coluna 'product' para inglês e salve o resultado como 'produtos_traduzidos'."
  }
]
```

**Resposta bruta do modelo:**

```text
extrair_dados_planilha: ['produtos_mandarim', 0]
criar_planilha: ['produtos_traduzidos', ["product", "english_description"]]
- extrair_dados_planilha: ["produtos_mandarim.xlsx"]- criar_planilha: ["produtos_mandarim", ["model", "product", "english description", "NCM"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha criada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\produtos_mandarim_1.xlsx
```

### Execução 4 — Tarefa 26: Tradução de planilha (Mandarim → Inglês) (criar_planilha)

rep 4/5: ✓ tool=criar_planilha args=DIVERGENTE latência=44.4s tokens=97 — erro: DadosIncompletos: arquivo gerado não tem nenhuma linha de dados.

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha produtos_mandarim.xlsx está disponível na pasta de arquivos."
  },
  {
    "role": "user",
    "content": "Tenho uma planilha chamada 'produtos_mandarim' com produtos descritos em Mandarim. Preencha a coluna 'english description' traduzindo a coluna 'product' para inglês e salve o resultado como 'produtos_traduzidos'."
  }
]
```

**Resposta bruta do modelo:**

```text
extrair_dados_planilha: ['produtos_mandarim', 0]
Criar_planilha: ['produtos_traduzidos', ["product", "english_description"]]
- extrair_dados_planilha: ["produtos_mandarim"]- extrair_dados_planilha: ["produtos_mandarim"]- criar_planilha: ["produtos_mandarim", ["model", "product", "english description", "NCM"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha criada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\produtos_mandarim_1.xlsx
```

### Execução 5 — Tarefa 26: Tradução de planilha (Mandarim → Inglês) (criar_planilha)

rep 5/5: ✓ tool=criar_planilha args=DIVERGENTE latência=38.4s tokens=78 — erro: DadosIncompletos: arquivo gerado não tem nenhuma linha de dados.

**Prompt enviado (mensagens):**

```json
[
  {
    "role": "system",
    "content": "prompt do system injetado"
  },
  {
    "role": "assistant",
    "content": "A planilha produtos_mandarim.xlsx está disponível na pasta de arquivos."
  },
  {
    "role": "user",
    "content": "Tenho uma planilha chamada 'produtos_mandarim' com produtos descritos em Mandarim. Preencha a coluna 'english description' traduzindo a coluna 'product' para inglês e salve o resultado como 'produtos_traduzidos'."
  }
]
```

**Resposta bruta do modelo:**

```text
extrair_dados_planilha: ['produtos_mandarim']
criar_planilha: ['produtos_traduzidos', ["English description", "product"]]
- extrair_dados_planilha: ["produtos_mandarim"]- criar_planilha: ["produtos_mandarim", ["model", "product", "english description", "NCM"]]
```

**Mensagem final (pós-ferramenta/confirmação):**

```text
Planilha criada com sucesso: C:\Users\Sony Vaio\Documents\maria\backend\benchmark\results\arquivos_gerados_benchmark\produtos_mandarim_1.xlsx
```



## Tarefas com falha

| ID | Tarefa | Motivo da falha |
|---:|---|---|
| 26 | Tradução de planilha (Mandarim → Inglês) | DadosIncompletos: coluna 'english description' não encontrada no arquivo gerado. |
| 26 | Tradução de planilha (Mandarim → Inglês) | DadosIncompletos: arquivo gerado não tem nenhuma linha de dados. |
| 26 | Tradução de planilha (Mandarim → Inglês) | DadosIncompletos: arquivo gerado não tem nenhuma linha de dados. |
| 26 | Tradução de planilha (Mandarim → Inglês) | DadosIncompletos: arquivo gerado não tem nenhuma linha de dados. |
| 26 | Tradução de planilha (Mandarim → Inglês) | DadosIncompletos: arquivo gerado não tem nenhuma linha de dados. |
