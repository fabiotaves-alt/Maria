# Relatório de Diagnóstico do Benchmark MARIA

**Data:** 2026-09-04
**Escopo:** Revisão da lógica do benchmark, tasks, prompts e ferramentas com foco em melhorar os resultados dos modelos — o problema não estava nos modelos em si.

---

## 1. Resumo executivo

A hipótese de partida ("o problema não parece ser os modelos") foi **confirmada**. A análise execução a execução do run mais recente com dados (`run_20260903_190549`, Qwen2.5-Omni-7B Q4_K_M) mostrou que na maioria das falhas o modelo **gerou a chamada de ferramenta correta**, mas a infraestrutura (parser textual, prompt e métricas em cascata) não a reconheceu.

**Resultado do run analisado (baseline):**

| Métrica | Valor |
|---|---:|
| Acurácia de tool calling (global) | 65,3% |
| `criar_planilha` | 26,7% |
| `criar_documento` | 46,7% |
| `confirmacao` | 0,0% |
| `editar_planilha` | 94,4% |
| `conversa` / `ambiguidade` / `cancelamento` | 100% |
| Taxa de confirmação (global) | 61,3% |
| Tokens/s (média) | 1,8 tok/s |

**Comparação com runs anteriores** (75 tarefas cada):

| Run | Modelo | Tool acc | Confirmação |
|---|---|---:|---:|
| 20260902_235411 | 3B Q4_K_M | **81,3%** | 78,7% |
| 20260903_115326 | 7B Q4_K_M | 72,0% | 60,0% |
| 20260903_190549 | 7B Q4_K_M | 65,3% | 61,3% |
| 20260903_174138 | 3B Q4_K_M | 57,3% | 82,7% |
| 20260902_173034 | 3B Q4_K_M | 40,0% | 20,0% |

A variação de 40%→81% entre runs do **mesmo** modelo (3B) sem mudança de pesos confirma que a instabilidade vem da infraestrutura, não do modelo.

---

## 2. Causas raiz identificadas (com evidências do log)

### 2.1 Parser textual frágil — maior alavanca de ganho

O llama-server local não emite `tool_calls` nativas: **100% das detecções** dependem do parser textual `extrair_tool_call_textual`. A versão antiga exigia que o texto INTEIRO casasse com `^\s*nome\s*:\s*(\[.*\])\s*$`. Variações reais do log que o parser antigo rejeitava:

| Variação gerada pelo modelo | Por que falhava | Tasks |
|---|---|---|
| `criar_planilha: ["agenda", ["Dia","Compromisso"]]**;**` | ponto-e-vírgula final vs âncora `$` | 3, 5, 14 |

---

## 3. Mudanças aplicadas

### 3.1 Parser textual robusto — `backend/core/tool_call_textual_parser.py`

Reescrita interna de `extrair_tool_call_textual` (mesma assinatura e contrato):

- **Scan balanceado** em vez de regex ancorada: localiza a 1ª ocorrência de ferramenta conhecida e percorre o texto contando profundidade de `[`/`]` respeitando aspas. Resolve texto extra antes/depois, `;`/`.` finais e a 2ª pseudo-chamada da task 9.
- **Whitelist de ferramentas**: só aceita nomes em `POSITIONAL_MAP` (elimina falso positivo de texto corrido e da pseudo-chamada "Listar arquivos").
- **Reparo de truncamento**: se a lista não fechar (corte por `max_tokens`), fecha aspas/colchetes pendentes e tenta `ast.literal_eval`; falha → `None` (contrato inalterado).
- **Normalização de args**: lista achatada → agrupada como `colunas`; string `"Dia, Compromisso"` → split em lista.

Novos helpers internos: `_extrair_lista_balanceada`, `_reparar_lista_truncada`, `_normalizar_argumentos`.

### 3.2 Métricas e log honestos

- **`tasks/task_schema.py`**: novos campos em `MariaTaskResult` — `confirmacao_elegivel`, `parse_suspeito`, `finish_reason`.
- **`analysis/metrics.py`**: nova métrica `confirmation_success_rate_elegiveis` (só tasks com `confirm_sequence`) e `parse_suspeito_count`. A métrica global antiga é **mantida** para comparabilidade.
- **`runners/maria_runner.py`**: popula os três novos campos; `parse_suspeito` = True quando não há tool call mas a resposta bruta contém padrão de ferramenta conhecida.
- **`analysis/report.py`**: exibe "Taxa de confirmação (elegíveis)" e "Suspeitas de falha de parser".
- **`core/llama_client.py`**: `chat_stream` expõe `finish_reason` em `metricas_saida`; `chat_com_tools_stream_com_metricas` ganha parâmetro opcional `extras_saida` (retrocompatível, tupla de 5 elementos preservada).

### 3.3 Timeouts e orçamento de tokens

- **`benchmark/benchmark_config.py`**: `BENCHMARK_TIMEOUT_POR_CHAMADA` default 120s → **300s** (a ~2 tok/s, 400 tokens = ~220s; 120s era falso negativo estrutural).
- **`core/config.py`**: `LLAMA_NUM_PREDICT_DOCUMENTO` 300 → **600** (é teto, não geração fixa; o valor anterior truncava a tool call de `criar_documento`).

### 3.4 System prompt — `backend/core/system_prompt.txt`

Reescrito de prosa única para estrutura com seções, **sem mudar nenhuma regra de negócio**. Instrução de formato explícita e determinística:

> "Para criar ou editar arquivo, responda APENAS com a chamada, em UMA linha, sem texto antes ou depois, sem ponto final. `colunas` é SEMPRE lista de strings. Nomes inseguros são corrigidos pelo sistema — chame normalmente."

Tamanho: 451 → **~375 tokens estimados** (mais curto e mais claro). A regra "nomes inseguros são corrigidos automaticamente" destrava as tasks 24/25.

### 3.5 Tasks — `backend/benchmark/tasks/tasks_core.py`

Task 2 ("Conversa sobre produtividade") ganhou sinônimos de keyword (`organizar`, `planejar`, `rotina`, `produtividade`). Nenhuma outra task alterada — 24/25 são resolvidas pelo prompt novo, não pela expectativa.

---

## 4. Verificação

- **169 testes passando** (157 anteriores + 12 novos) + 33 subtests.
- Nova classe `TestToolCallTextualParser` com 1 teste por variação real do log.
- Imports de `llama_client`, `maria_runner`, `run_benchmark` e `report` sem erro.
- Ajuste de compatibilidade: `TestAvisoNctx`/`TestSamplerParamsBenchmark` usam `MagicMock` para métricas — a renderização da nova linha de confirmação elegível passou a usar verificação por tipo (`isinstance` numérico) em vez de `is not None`.

**Validação empírica pendente (etapa 6):** smoke live `--task-ids 3 4 5 9 14 15` e run completo com `compare_runs.py` contra `run_20260903_190549` — **requer o llama-server ativo**, deixado por último a pedido.

---

## 5. Estimativa de impacto (baseada no log)

| Métrica | Antes | Meta |
|---|---:|---:|
| Tool accuracy global | 65% | ≥90% |
| `criar_planilha` | 27% | ≥80% |
| `criar_documento` | 47% | ≥80% |
| `confirmacao` | 0% | ~100% (as falhas eram de parse/timeout, não de confirmação) |

---

## 6. Dívida técnica (fora deste ciclo)

1. **Tool calling nativo via `--jinja` no llama-server**: eliminaria a dependência do parser textual. Investigar se o servidor suporta template com tools para o Qwen2.5-Omni.
2. **`criar_documento` em duas fases**: tool call com conteúdo curto + geração de conteúdo dedicada — reduziria truncamento e latência em documentos narrativos longos.

---

## 7. Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `backend/core/tool_call_textual_parser.py` | Parser robusto (scan balanceado, whitelist, reparo, normalização) |
| `backend/core/llama_client.py` | `finish_reason` em métricas; `extras_saida` opcional |
| `backend/core/config.py` | `LLAMA_NUM_PREDICT_DOCUMENTO` 300→600 |
| `backend/core/system_prompt.txt` | Reescrito (estruturado, determinístico, ~375 tokens) |
| `backend/benchmark/benchmark_config.py` | `BENCHMARK_TIMEOUT_POR_CHAMADA` 120→300s |
| `backend/benchmark/tasks/task_schema.py` | 3 novos campos em `MariaTaskResult` |
| `backend/benchmark/tasks/tasks_core.py` | Keywords da task 2 |
| `backend/benchmark/runners/maria_runner.py` | Popula novos campos; captura `extras` |
| `backend/benchmark/analysis/metrics.py` | 2 novas métricas |
| `backend/benchmark/analysis/report.py` | 2 novas linhas no relatório |
| `backend/tests/test_maria.py` | +12 testes (parser + métricas) |

| `criar_planilha: [...]` + `\n\nEsta planilha será usada para...` | texto explicativo após a lista | 4 |
| `criar_documento: [...]` + `\n\nListar arquivos: ["..."]` | 2ª pseudo-chamada após a 1ª | 9 |
| `criar_planilha: ["gastos", "Data", "Valor"]` (lista achatada) | `colunas` virava string → erro de validação | 3, 14 |
| conteúdo longo cortado por `max_tokens` | lista sem `]` de fechamento → `ast.literal_eval` falha | 8, 10, 15 |

**Evidência mais contundente (task 9):** o modelo gerou a tool call correta e depois adicionou uma 2ª pseudo-chamada; o parser falhou por causa disso — não por culpa do modelo.

### 2.2 System prompt induzia o formato que o parser não tolerava

O prompt antigo (prosa única, 451 tokens) **ensinava** o formato posicional `criar_planilha: ["nome_arquivo", "colunas"]`, mas não dizia: "emita SOMENTE a chamada, sem texto extra, sem pontuação final, colunas sempre como lista". Também não explicava que nomes inseguros são sanitizados pelo sistema — por isso o Qwen se **recusava** por segurança nas tasks 24/25 ("Desculpe, mas não posso criar arquivos com nomes que possam ser maliciosos...").

### 2.3 Métricas em cascata distorciam o resultado

- Tool não parseada ⇒ confirmação nunca oferecida ⇒ `confirmation_completed=False` ⇒ categoria `confirmacao` = 0% **sem nenhuma falha real de confirmação** (tasks 14/15 falharam no parse/timeout, não na confirmação).
- `keyword_match` mede a mensagem final pós-execução ("Planilha criada com **sucesso**"); se o parse falha, a mensagem final é o texto bruto ⇒ keyword falha junto.
- A taxa global misturava 21 execuções triviais "sem tool esperada" (100% fáceis), diluindo as categorias fracas reais.
- Não havia como distinguir "modelo não chamou" de "parser não entendeu" — ambos apareciam como `tool_detected: null`.

### 2.4 Timeout de 120s/chamada incompatível com o hardware (~2 tok/s)

`max_tokens=400` a 1,8 tok/s ⇒ até ~220s por chamada. A task 15 estourou 2× (~125-131s). E a heurística `_sugere_composicao_de_documento` **reduzia** para 300 tokens exatamente nos casos de documento narrativo que precisam de mais — causando truncamento da lista (parse falha) quando não timeout.
