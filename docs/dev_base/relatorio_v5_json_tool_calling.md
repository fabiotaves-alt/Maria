# RELATÓRIO TÉCNICO — v5.0.0: Tool Calling JSON-Objeto Plano, Validação Determinística e Benchmark na Raiz

**Data:** 2026-09-08  
**Branch:** `feat/arquitetura-hexagonal-fase4`  
**Status:** Plano aprovado pelo usuário (decisões na seção 1) — implementação ainda não iniciada  
**Base empírica:** 7 blocos de testes isolados contra llama-server (3B e 7B Q4_K_M, 2026-09-07/08) + auditoria de código do pipeline atual

---

## 1. Decisões aprovadas

| # | Decisão | Detalhe |
|---|---------|---------|
| D1 | **Remoção total do formato posicional** | Sem janela de transição: `tool_call_textual_parser.py` (`POSITIONAL_MAP`, `NOME_CANONICO`, reparo de lista) sai do caminho de produção e é removido com os testes associados. O formato canônico passa a ser o **JSON-objeto plano** `{"ferramenta": "...", ...}` |
| D2 | **Validação determinística obrigatória** antes de execução e antes de qualquer auto-correção por turno de modelo | Caso real que a motiva: bug sistemático do 3B (`"peso"` minúsculo vs coluna `"Peso"`) — 3/3 execuções. Conserto em código (match case-insensitive), não por turno extra (que custou +34–71s e corrigiu na direção errada no teste) |
| D3 | **`response_format` (JSON Schema restrito) documentado como experimental** | Confirmado funcional nesta build do llama-server (3/3 JSON válido mesmo com prompt ruim), mas **não pode ser global em produção**: a MARIA responde em texto puro em turnos legítimos (cumprimentos, "arquivo não encontrado", confirmações). Uso restrito ao benchmark (task com ferramenta esperada) via flag |
| D4 | **Benchmark movido para a raiz do monorepo** | `benchmarks/maria_bench/`, consumindo apenas a superfície pública pós-hexagonal (ports + composition root) |
| D5 | **Logs em SQLite** (WAL) como store canônico; reports resumidos gerados a partir do DB; JSONL como export opcional | Schema aprovado na seção 8 do relatório de arquitetura |
| D6 | **Task 26 substituída**, não consertada | Nova versão validada em teste (dados no corpo da mensagem, tradução Mandarim→PT + `linhas`); a tradução dentro do fluxo de ferramenta vira task separada marcada como `limite_conhecido` |

---

## 2. Evidências dos testes isolados (consolidado)

| Teste | Modelo | Resultado-chave |
|---|---|---|
| `response_format` + JSON Schema (prompt v1 ruim, de propósito) | 7B | 3/3 JSON válido, sem crase — decodificação restrita **funciona nesta build**; resolve FORMA, não CONTEÚDO |
| Task 26 antiga + schema obrigando `linhas` | 7B | 3/3 `linhas` com 5 itens; tradução falhou (mais mandarim em `English Description`); `colunas` (3 itens, minúsculas, sem NCM) inconsistente com chaves de `linhas` (4 chaves, capitalizadas); campos-cópia corrompidos 2/3 (`QFY000031`→`QFY00031`) |
| Tradução simples isolada (Mandarim→PT, Inglês→PT) | 7B | 2/2 corretas em cada — o modelo **sabe** traduzir fora do fluxo de ferramenta |
| Prompt v2 (JSON plano, sem exemplo de `linhas`) — 3 tarefas | 7B | 3/3 JSON válido, mas `linhas` **nunca preenchida** (dados ignorados) |
| **Prompt v3 (v2 + 1 exemplo com `linhas`)** | 3B e 7B | **6/6 `linhas` preenchida (5 itens)** — achado decisivo: o gap era de *exemplo ausente*, não de formato/coerção |
| Comparativo 3B × 7B no v3 | ambos | 7B: chaves corretas, tipos numéricos, 3/3 determinístico, ~2× mais lento. 3B: bug sistemático de case (`peso` vs `Peso`) 3/3, preços como string com símbolo |
| Auto-correção com instrução genérica (3B) | 3B | 3/3 "corrigiu" na **direção errada** (mudou `colunas` para bater com o erro em `linhas`). Instrução genérica é insegura como mecanismo; o veredito "CORRIGIU" do script era falso positivo de critério |

**Ressalvas metodológicas:** amostras de n=3 sustentam conclusões binárias replicadas, não taxas finas; mojibake do PowerShell 5.1 é só visual (UTF-8 íntegro); qualquer harness futuro de auto-correção deve validar contra a fonte de verdade original, não contra consistência interna da resposta.

---

## 3. Auditoria de código — bugs e inconsistências encontrados

### BUG-1 (CRÍTICO) — O formato JSON plano não é parseado por nenhum caminho do pipeline
- `llama_client.py:79-80`: `_tentar_extrair_tool_call_textual()` exige `'\"name\"'` **e** `'\"arguments\"'` no content — só casa o formato **nativo OpenAI** vazado em texto.
- `llama_client.py:406-412`: segundo fallback chama `extrair_tool_call_textual()` — só casa **array posicional**.
- **Consequência:** o objeto `{"ferramenta":"criar_planilha",...}` que o prompt (working tree) instrui **não tem parser**. Explica integralmente o run `run_20260907_141158` (7B): 9/9 `tool_detected=None`. Não é "regressão de prompt" isolada — é **parser inexistente para o formato alvo**.
- **Correção:** parser novo (`tool_call_json_parser.py`) — ver seção 4. O trabalho é maior do que "promover o fallback": é implementar o casamento do formato plano.

### BUG-2 (CRÍTICO) — `pd.DataFrame(linhas_dados, columns=colunas)` é case-sensitive
- `excel_handler.py` em `criar_planilha_real` (~linha 130) e `editar_planilha_real` (~linha 235): chaves dos dicts casam com `colunas` **por igual exato**.
- Com a saída real do 3B (`"peso"` vs coluna `"Peso"`): chave não casa → `NaN` → `fillna("")` → **coluna vazia, silenciosamente, sem erro e sem warning**.
- **Correção (D2):** normalização case-insensitive (e opcionalmente acento-insensitive) das chaves de cada dict de `linhas` contra `colunas`, antes do DataFrame. Determinístico, custo zero de latência, elimina a classe inteira do erro.

### BUG-3 — `df.reindex(columns=colunas)` descarta chaves extras sem registro
- Caso real do teste com schema: `linhas` com `NCM`, `colunas` sem `NCM` → coluna inteira descartada silenciosamente.
- **Correção:** registrar em `correcoes`/telemetria quando houver chaves de `linhas` fora de `colunas` (ou derivar `colunas`, ver V5).

### BUG-4 — Normalização lowercase atual destruiria chaves de dados
- `llama_client.py:395`: `{k.lower(): v for k, v in argumentos.items()}` — hoje normaliza **todas** as chaves dos argumentos (correto para `Conteudo`/`Nome_arquivo`, catastrófico para `linhas`: `English Description` → `english description` → divergência com a coluna → coluna vazia).
- **Correção:** no parser novo, normalizar **somente chaves de controle** (`ferramenta`, `nome_arquivo`, `colunas`, `linhas`, `titulo`, `conteudo`, `descricao`, `tipo_documento`, `pasta`, `offset`, `linha_cabecalho`, `limite_linhas`); chaves internas de `linhas` são **dados**, jamais normalizadas (o casamento com `colunas` fica a cargo da validação case-insensitive do BUG-2).

### BUG-5 — `validar_argumentos_obrigatorios` não valida `linhas`
- `tools_schema.py:339-397`: valida `colunas` (lista de strings não-vazias) e sanitiza `nome_arquivo`, mas `linhas` passa sem qualquer checagem (tipo, item dict, chaves×colunas).
- **Correção:** novos validadores na camada determinística (V2–V5, seção 5).

### INCONSISTÊNCIA-1 — Benchmark não avalia `linhas`
- `_argumentos_compativeis()` (`maria_runner.py:538+`): compara `colunas` como conjunto (case-insensitive) mas ignora `linhas`; `coluna_dados_obrigatoria`/`dados_arquivo_validos` só confere **não-vazio** de uma coluna.
- **Correção:** validador de conteúdo esperado (`linhas_esperadas` na task v2) — match exato/subset case-insensitive dos valores.

### INCONSISTÊNCIA-2 — Prompt diz "opcional", tasks exigem
- Prompt v2/v3: "linhas (opcional, para preencher dados)". Tasks de dados (nova Task 26 e futuras) exigem preenchimento. O modelo imita exemplo + regra: no teste v2 (dados na mensagem, sem exemplo), `linhas` nunca veio.
- **Correção:** prompt v4 com regra condicional explícita: "se o usuário fornecer dados, preencha `linhas` sempre" + exemplo (já validado).

### INCONSISTÊNCIA-3 — Metadados de diagnóstico atrelados ao posicional
- `task_schema.py`: `tool_call_fonte ∈ {delta, fallback_json, parser_posicional}`; `fallbacks` inclui `lista_reparada`, `nome_mapeado`, `colunas_normalizadas` (específicos do posicional); `report.py:formatar_avisos()` e testes de `TestFormatarAvisos` os referenciam.
- **Correção:** novo vocabulário `tool_call_fonte ∈ {delta, json, None}` + fallbacks `{json_reparado, chaves_normalizadas, colunas_derivadas}`; `parse_suspeito` mantido (continua valioso para separar "modelo não chamou" de "parser falhou").

### INCONSISTÊNCIA-4 — Acoplamento benchmark↔core (já mapeado no relatório hexagonal)
- `maria_runner.py` importa `_montar_mensagens_com_reforco` (símbolo **privado**), `TOOLS_SCHEMA`, `executar_ferramenta_real`, `validar_e_corrigir_tool_call_stream`; dois estilos de import (`core.X` via `sys.path.insert` e `backend.core.X`); config via efeito colateral (`core/config.py`).
- **Correção:** B2 — benchmark consome ports/composition root; `BenchmarkConfig` injetável.

---

## 4. Especificação — Parser JSON primário (`core/tool_call_json_parser.py`)

Ordem de resolução em `_resolver_tool_call_final()` (substitui a atual):

1. **delta nativo** (tool_calls estruturado) — inalterado;
2. **parser JSON do content** (novo, primário sobre texto);
3. `parse_suspeito` quando há padrão de chamada conhecida e nada foi parseado.

Etapas do parser JSON (nível de tolerância progressivo):

| Nível | Estratégia |
|---|---|
| T1 | `json.loads` direto do content limpo (strip de cercas de código ```` ```json ```` e texto ao redor) |
| T2 | Scan balanceado de `{...}` (respeitando strings) para extrair o primeiro objeto JSON; aceitar também `{"name":..., "arguments":...}` nativo (mantém o fallback atual como caso particular) |
| T3 | Reparo de truncamento (`finish_reason=length`): fechar `}`/`]`/aspas pendentes de forma conservadora (equivalente JSON do `_reparar_lista_truncada`), marcar `fallbacks=["json_reparado"]` |
| T4 | Normalização: chaves de controle → minúsculas (BUG-4); `ferramenta`/`name` → nome canônico; rejeitar ferramenta fora da whitelist |

Saída: `{"name": str, "arguments": dict}` + metadados (`_fonte`, `_reparado`). Rejeita (retorna `None` + telemetria) quando: JSON inválido mesmo com reparo, ferramenta desconhecida, ou objeto sem `ferramenta`/`name`.

## 5. Especificação — Camada de validação determinística (D2)

Módulo novo `core/validacao_tool_call.py` (ou extensão de `tools_schema.py`), executado **antes** da execução da ferramenta e **antes** de qualquer correção por turno de modelo. Cada validador classifica-se em **REPARO** (corrige e telemetra) ou **ERRO** (bloqueia e alimenta retry direcionado).

| ID | Validador | Tipo | Detalhe |
|----|-----------|------|---------|
| V1 | Campos obrigatórios/tipos (colunas lista de strings não-vazias, nome_arquivo sanitizável) | ERRO | Já existe (`validar_argumentos_obrigatorios`); mantido |
| V2 | `linhas` é lista de dicts | ERRO | Item não-dict → erro claro (hoje: erro genérico do pandas) |
| V3 | **Chaves de `linhas` × `colunas` case-insensitive** | REPARO | Renomeia `"peso"`→`"Peso"` quando único match case-insensitive; telemetra em `correcoes` |
| V4 | Chaves de `linhas` sem match | REPARO+aviso | Cria coluna correspondente OU deriva via V5 — nunca descartar silenciosamente (BUG-3) |
| V5 | `colunas` ausente/inconsistente com chaves de `linhas` | REPARO | **Derivar `colunas` das chaves do primeiro item de `linhas`** (ordem de inserção preservada) — elimina a inconsistência por design (aprovada) |
| V6 | Valor numérico como string formatada (`"R$ 25,00"`, `"0,5 kg"`) | OPCIONAL | Coerção quando a coluna tem tipo homogêneo detectado; default **desligado** (v1 registra como observação semântica; decide em B4 com dados) |
| V7 | Limite de linhas (`get_max_linhas_por_chamada`) | REPARO | Já existe no handler; passa a telemetrar |
| V8 | Conteúdo semântico estrutural (título/conteúdo invertido, placeholder, curto) | Aviso | Já existe no benchmark; promovido a utilitário compartilhado no B4 |

**Auto-correção por turno de modelo:** só dispara quando a validação determinística falha (V1/V2) — e sempre **direcionada** (campo exato apontado, padrão do `validar_e_corrigir_tool_call_stream` existente). Instrução genérica: **descartada** (evidência: seção 2, teste 7).

---

## 6. Documentação — `response_format` / JSON Schema restrito (D3, experimental)

**O que é:** parâmetro `response_format: {"type": "json_schema", "json_schema": {...}}` no payload de `/v1/chat/completions`. O llama.cpp converte o schema em gramática GBNF internamente (`json_schema_to_grammar`) e restringe a amostragem aos tokens que produzem JSON válido conforme o schema. **Independente** de `supports_tools`/`supports_tool_calls` (confirmados `false` no `/props` desta build) — um é chat template, o outro é restrição de amostragem.

**Confirmado empiricamente (7B, 3/3):** JSON válido e sem crases mesmo com prompt deliberadamente ruim; latência menor (sem texto solto); `linhas` sempre presente quando `required`.

**Limites (por que NÃO é mecanismo primário):**
1. **Não pode ser global em produção** — a MARIA responde em texto puro em turnos legítimos (cumprimentos, "não encontrei o arquivo", perguntas de confirmação). Um schema forçado quebraria esses turnos.
2. Garante **forma, não conteúdo**: não impede tradução errada, campos-cópia corrompidos (`QFY000031`→`QFY00031`) nem escolha errada (mitigável com `enum` em `ferramenta`, mas só quando se sabe qual ferramenta esperar).
3. Não expressa invariantes entre campos ("chaves de `linhas` == `colunas`") — observado: `colunas` veio inconsistente com `linhas` em 3/3.
4. Exige schema por chamada — só faz sentido quando o chamador já sabe que turno é de tool call (caso do benchmark com task declarada).

**Uso aprovado:** flag experimental do benchmark (`LLAMA_RESPONSE_FORMAT_SCHEMA=1`, B6), aplicando o schema derivado de `TOOLS_SCHEMA` (ver O1) por tarefa; **não** entra no fluxo de produção do chat.

## 7. Oportunidades registradas

- **O1 — Fonte única de verdade do schema:** gerar automaticamente o `json_schema` do `response_format` a partir de `TOOLS_SCHEMA` (por ferramenta), eliminando duplicação e drift entre prompt/validação/flag experimental.
- **O2 — Derivação de `colunas` (V5)** já cobre a inconsistência colunas×linhas por design, mais simples que validação pós-hoc.
- **O3 — `compare_runs` via SQL** quando o SQLite entrar: comparação histórica entre prompts/modelos/perfis vira `GROUP BY` (hoje: dois JSONs gigantes em memória).
- **O4 — `tool_call_fonte` como métrica de formato:** taxa delta vs json vs `parse_suspeito` por run — dado já coletado, hoje não analisado; vira coluna do report v2.
- **O5 — LLM-as-judge calibrado** (pós-processamento a partir do DB, temperatura 0, rubrica 4 eixos, concordância medida contra ~30 execuções rotuladas antes de virar métrica).
- **O6 — Coerção numérica (V6)** pode subir de OPCIONAL para default se o B4 mostrar que `Preco` como string atrapalha ordenação/uso no frontend.

---

## 8. Plano revisado — fases B0–B7 (decisões embutidas)

| Fase | Conteúdo | Decisões/achados embutidos | Estimativa |
|---|---|---|---|
| **B0** | Prompt v4 (JSON plano + exemplo `linhas` + regra condicional + regra de encadeamento "não narre, chame a próxima ferramenta"); parser JSON primário (T1–T4, BUG-4); **validação determinística V1–V5,V7 (BUG-2/3/5)**; remoção do posicional (D1); vocabulário de telemetria novo (INCONS-3); testes reescritos; suíte 100% verde | D1, D2; BUG-1..5 | 8–10h |
| **B0.5** | Baseline gravado (3B e 7B, tasks atuais + nova Task 26) para comparativo honesto | — | 2h |
| **B1** | Hexagonal Fases 0–2 (domain + interfaces/ports públicos) | D4 pré-requisito | 5–7h |
| **B2** | `benchmarks/maria_bench/` na raiz; runner consome ports + composition root; `BenchmarkConfig` injetável | D4, INCONS-4 | 4–6h |
| **B3** | Storage SQLite (WAL) + report v2 (resumido default / detalhado flag) + `compare` via SQL | D5, O3, O4 | 5–7h |
| **B4** | Tasks v2 (etapas/multi-etapa/auto-correção direcionada; planilhas com `linhas` + `linhas_esperadas`; documentos complexos; Task 26 substituída + task `limite_conhecido` de tradução; V6 decidido com dados) | D6, INCONS-1, O6 | 6–8h |
| **B5** | CLI completa (perfis, overrides sampler/modelo/ctx, `--system-prompt`, subcomandos run/judge/report/compare) | — | 3–4h |
| **B6** | Semântica (validadores ricos + LLM-as-judge calibrado) + flag experimental `response_format` com schema gerado de `TOOLS_SCHEMA` | D3, O1, O5 | 5–8h |
| **B7** | v5.0.0 + docs (README_benchmark reescrito, seção response_format) + limpeza final | — | 2–3h |

**Total: ~40–55h.**

## 9. Riscos

1. **Liberdade textual do JSON plano**: mais exposto a crases/texto ao redor que o posicional com whitelist — mitigado por T1–T3 (strip, scan balanceado, reparo) e `parse_suspeito` medindo.
2. **Reparo de truncamento JSON é mais arriscado** que o de lista: fechar `}` pode produzir objeto válido mas semanticamente incompleto (última linha parcial de `linhas`) — validar pós-reparo (V2) e telemetrar `json_reparado` para auditoria.
3. **Regressão silenciosa em produção** durante B0 (o terminal também usa o pipeline) — critério de aceite exige smoke test funcional manual do chat real.
4. **3B em produção**: bug de case resolvido por V3, mas a tipagem string (`"r$ 45,00"`) permanece — V6/observação semântica cobre; documentar como diferença conhecida 3B×7B.
5. **Amostras n=3**: decisões de prompt (v4) devem ser revalidadas no benchmark real (B0.5) antes de virar padrão.

## 10. Pendências de teste (da sessão de testes, não cobertas)

1. Prompt v4 no **fluxo real de 2 turnos** (extração real injetada → escrita) — onde o modelo narrava em prosa; inclui verificação de UTF-8 end-to-end com mandarim (o openpyxl/pandas preservam, mas precisa confirmar no caminho completo).
2. `--ctx-size 4096` efetivo do servidor (run antigo detectou 2048).
3. Auto-correção **direcionada** com o formato JSON (variante "campo apontado") — decide se o turno extra sobrevive no v5 ou é 100% substituído pela validação determinística.
4. Comportamento do delta nativo (`supports_tool_calls=false`): amostra pequena até agora.

## 11. Critérios de aceite

- **B0**: suíte 100% verde; smoke test manual do chat real (criação de planilha com `linhas` via JSON, conversa em texto puro, confirmação, arquivo inexistente); run de benchmark com `tool_accuracy` ≥ baseline do formato posicional no 7B; 0 execuções com coluna silenciosamente vazia na nova Task 26.
- **B2**: zero imports de símbolos privados no benchmark; `grep "_montar_mensagens_com_reforco"` sem resultados fora do core.
- **B3**: `compare_runs` 100% via SQL; report resumido < 200 linhas para run completo.
- **B6**: concordância do juiz ≥ 80% contra rotulagem manual antes de entrar no report como métrica.




