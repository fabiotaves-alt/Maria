# PLANO MESTRE — v5.0.0: Execução Integrada

**Data:** 2026-09-08  
**Escopo:** Decisões D1–D6 + Bugs BUG-1–5 + Inconsistências INCONS-1–4 + Oportunidades O1–O6 + revisões sênior  
**Estimativa total:** 58–80h (B0–B7 revisados + B4.5/B4.6 opcionais: 16–23h)

---

## 0. Mapa de dependências (bloqueantes)

```
B0 (parser JSON + validação + prompt v4 + deletar posicional)
 └─► B0.5 (baseline gravado com suite verde)
      └─► B1 (hexagonal fases 0-2: domain + interfaces)
           └─► B2 (benchmark → ports; zero imports privados)
                └─► B3 (SQLite WAL + report v2 + compare SQL)
                     └─► B4 (tasks v2: linhas_esperadas, multi-etapa, Task 26)
                          ├─► B4.5 (intent classification / entity extraction — pré-processamento)
                          ├─► B4.6 (roteamento para modelo especializado de tradução — NLLB-200)
                          └─► B5 (CLI completa)
                               └─► B6 (semântica + LLM-judge + response_format flag)
                                    └─► B7 (v5.0.0 final: docs + limpeza)
```

> **Nota sobre B4.5/B4.6:** ambas as fases dependem de B4 (Task 26 redesenhada e infraestrutura de benchmark v2), mas são independentes entre si e não bloqueiam B5–B7. Podem ser executadas em paralelo entre si ou adiadas para depois do v5.0.0, a critério de priorização. Origem: análise de viabilidade de 2026-09-08 (`analise_viabilidade_intent_processor.md`) sobre a proposta de pré-processamento validada em `relatorio_validacao_intent_processing.md`.

**Regra:** nenhuma fase começa sem a anterior 100% verde (suíte + critério de aceite específico).  
**Exceção única:** B1 pode começar em paralelo com B0.5 **se e somente se** B0.5 não precisar tocar em `core/`.

---

## 1. Inventário de arquivos afetados (referência cruzada)

| Arquivo | B0 | B1 | B2 | B3 | B4 | B4.5 | B4.6 | B5 | B6 | B7 |
|---------|----|----|----|----|----|------|------|----|----|-----|
| `core/tool_call_textual_parser.py` | **DELETE** | — | — | — | — | — | — | — | — | — |
| `core/tool_call_json_parser.py` | **NEW** | move→infra | — | — | — | — | — | — | — | — |
| `core/validacao_tool_call.py` | **NEW** | move→domain | — | — | — | — | — | — | — | — |
| `core/llama_client.py` | MODIFY | move→infra | — | — | — | — | — | — | — | — |
| `core/tools_schema.py` | MODIFY | move→infra | — | — | — | — | — | — | — | — |
| `core/excel_handler.py` | **MODIFY** | move→infra | — | — | — | — | — | — | — | — |
| `core/system_prompt.txt` | **MODIFY** | — | — | — | — | — | — | — | — | — |
| `core/chat_session.py` | — | move→domain | — | — | — | — | — | — | — | — |
| `core/confirmacao.py` | — | move→domain | — | — | — | — | — | — | — | — |
| `core/client_protocol.py` | — | move→iface | — | — | — | — | — | — | — | — |
| `core/interfaces.py` | — | move→iface | — | — | — | — | — | — | — | — |
| `core/maria_controller.py` | — | move→app | — | — | — | — | — | — | — | — |
| `core/tool_chaining.py` | — | move→app | — | — | — | — | — | — | — | — |
| `core/router.py` | — | move→app | — | — | — | — | — | — | — | — |
| `core/manual_redacao.py` | — | move→app | — | — | — | — | — | — | — | — |
| `core/word_handler.py` | — | move→infra | — | — | — | — | — | — | — | — |
| `core/file_utils.py` | — | move→infra | — | — | — | — | — | — | — | — |
| `core/paths.py` | — | move→infra | — | — | — | — | — | — | — | — |
| `core/session_storage.py` | — | move→iface | — | — | — | — | — | — | — | — |
| `benchmark/runners/maria_runner.py` | MODIFY | — | **REFACTOR** | MODIFY | MODIFY | — | — | — | MODIFY | — |
| `benchmark/tasks/task_schema.py` | MODIFY | — | — | MODIFY | **MODIFY** | — | — | — | MODIFY | — |
| `benchmark/tasks/tasks_*.py` | — | — | — | — | **MODIFY** | — | — | — | — | — |
| `benchmark/run_benchmark.py` | — | — | MODIFY | MODIFY | — | — | — | MODIFY | MODIFY | — |
| `tests/test_maria.py` | **MODIFY** | MODIFY | — | — | — | — | — | — | — | — |
| `domain/intent_classification.py` | — | — | — | — | — | **NEW** | — | — | — | — |
| `application/intent_router.py` | — | — | — | — | — | **NEW** | — | — | — | — |
| `infrastructure/tools/entity_extractor.py` | — | — | — | — | — | **NEW** | — | — | — | — |
| `infrastructure/translation/nllb_client.py` | — | — | — | — | — | — | **NEW** | — | — | — |
| `interfaces/translation_protocol.py` | — | — | — | — | — | — | **NEW** | — | — | — |
| `benchmark/tasks/tasks_intent.py` | — | — | — | — | — | **NEW** (tasks 29–32) | — | — | — | — |

---

## 2. Fase B0 — Correções críticas (fundação) · 8–11h

> **Bloqueante para tudo.** Sem B0 verde, o pipeline produz `tool_detected=None` em 100% das execuções com prompt atual.

### Ordem obrigatória de execução dentro do B0

```
B0.1 → B0.2 → B0.3 → B0.4 → B0.5b → B0.6 → B0.7 → B0.8 → B0.9
```

Deletar o parser posicional (B0.6) **depois** de implementar o JSON parser (B0.2) e validar os testes (B0.5b). Nunca antes.

---

### B0.1 · Escrever testes de falha TDD · ~1h

**Princípio:** os critérios de aceite existem antes do código.

Adicionar em `tests/test_maria.py` (ou novo `test_tool_call_json_parser.py`):

| Teste | O que verifica |
|-------|---------------|
| `test_parser_json_extrai_formato_ferramenta` | `{"ferramenta":"criar_planilha",...}` → `{name, arguments}` |
| `test_parser_json_strip_cercas_codigo` | ` ```json\n{...}\n``` ` → objeto limpo |
| `test_parser_json_scan_balanceado` | JSON dentro de texto livre extraído corretamente |
| `test_parser_json_reparo_truncamento` | JSON cortado com `finish_reason=length` → objeto parcial marcado |
| `test_parser_json_rejeita_ferramenta_desconhecida` | `{"ferramenta":"deletar_tudo"}` → `None` |
| `test_validacao_linhas_tipo` | `linhas` não-lista-de-dicts → `ERRO` claro |
| `test_validacao_linhas_case_insensitive` | `"peso"` vs coluna `"Peso"` → REPARO, não NaN |
| `test_validacao_linhas_chave_extra` | chave em `linhas` fora de `colunas` → aviso, não descarte silencioso |
| `test_validacao_derivar_colunas` | `colunas` ausente + `linhas` com chaves → `colunas` derivada (V5) |
| `test_normalizacao_controle_preserva_linhas` | `{k.lower()}` só nas chaves de controle; `linhas[*]` preservadas |
| `test_excel_nao_cria_nan_com_case_divergente` | `"peso"` vs `"Peso"` → célula tem valor, não string vazia |

**Todos devem falhar (RED) antes do B0.2.**

---

### B0.2 · `core/tool_call_json_parser.py` (novo) · ~2h

**Responsabilidade:** parsear content do modelo para `{name, arguments}`. Sem efeitos colaterais.

```python
# Contrato público:
def extrair_tool_call_json(conteudo: str) -> dict | None:
    """
    Tenta extrair tool call no formato JSON plano {"ferramenta":...}.
    Retorna {"name": str, "arguments": dict, "_fonte": "json", "_reparado": bool}
    ou None se não houver tool call reconhecível.
    
    Níveis de tolerância (T1→T4):
      T1: json.loads direto após strip de cercas markdown
      T2: json.JSONDecoder().raw_decode() sobre o primeiro '{' encontrado
      T3: reparo conservador de truncamento (finish_reason=length)
      T4: normalização de chaves de CONTROLE apenas; ferramenta validada contra whitelist
    """
```

**Regra crítica (BUG-4 / sênior DEFEITO-1):**  
T4 normaliza somente: `ferramenta`, `nome_arquivo`, `colunas`, `linhas`, `titulo`, `conteudo`, `descricao`, `tipo_documento`, `pasta`, `offset`, `linha_cabecalho`, `limite_linhas`.  
Chaves dentro de `linhas[*]` são **dados** — nunca tocadas pelo parser.

**Para T2, usar `json.JSONDecoder().raw_decode()`** em vez de scan manual — evita reimplementar um mini-parser de JSON (recomendação sênior).

**Metadados de telemetria:**  
Retornar `_fonte: "json"` e `_reparado: bool` junto ao resultado. Esses campos alimentam INCONS-3 (novo vocabulário).

**Whitelist de ferramentas:** importar de `CAMPOS_OBRIGATORIOS.keys()` em `tools_schema.py` — fonte única (O1 parcial).

---

### B0.3 · `core/validacao_tool_call.py` (novo) · ~1.5h

**Responsabilidade:** validação determinística pós-parser, pré-execução. Sem chamadas ao modelo.

**Separação de camadas (sênior DEFEITO-1 corrigido):**
- Parser (B0.2): normaliza chaves de controle → `linhas` chega com chaves originais do modelo.
- Validador (B0.3): compara `linhas[*].keys()` com `colunas` de forma case-insensitive → renomeia no dict (V3).

```python
# Validadores por ordem de execução:
# V1: campos obrigatórios/tipos (já existe, manter)
# V2: linhas é lista de dicts → ERRO se não for
# V3: chaves de linhas × colunas case-insensitive → REPARO (renomeia)
# V4: chaves de linhas sem match → aviso + criar coluna (nunca descartar)
# V5: colunas ausente → derivar das chaves do primeiro item de linhas
# V7: limite de linhas (já existe no handler, migrar para cá + telemetria)

# Retorno: {"tool_call": dict_corrigido, "erros": list, "reparos": list, "bloqueante": bool}
```

**Aviso de truncamento (sênior OMISSÃO-2):**  
Se `_reparado=True` E `"linhas"` nos argumentos → adicionar `reparos=[{"tipo": "linhas_truncadas", "n_linhas": N}]`. O runner deve propagar isso como aviso ao usuário na resposta final.

---

### B0.4 · Modificar `core/excel_handler.py` · ~0.5h

Remover BUG-2 e BUG-3 do `criar_planilha_real` e `editar_planilha_real`:

```python
# ANTES (linha 117-118):
df = pd.DataFrame(linhas_dados, columns=colunas)
df = df.reindex(columns=colunas)

# DEPOIS: V3 já fez a normalização de chaves; apenas logar chaves extras
# A validacao_tool_call.py (V4) garante que não há chave sem match silencioso.
# excel_handler não precisa mais normalizar — confia no validador upstream.
```

**Importante:** não duplicar lógica de V3 aqui. O handler recebe `linhas` já com chaves normalizadas pelo validador.

---

### B0.5a · Modificar `core/llama_client.py` · ~1h

1. Substituir import de `extrair_tool_call_textual` por `extrair_tool_call_json`.
2. Reordenar `_resolver_tool_call_final`: delta nativo → JSON parser → `parse_suspeito`.
3. Remover segunda chamada a `extrair_tool_call_textual` (linha 409).
4. Integrar metadados `_fonte` e `_reparado` do parser no objeto retornado.
5. Remover `{k.lower(): v for k, v in argumentos.items()}` flat — a normalização passa a ser responsabilidade do parser (chaves de controle) e do validador (chaves de `linhas`).

---

### B0.5b · Rodar suíte — todos os testes devem passar · ~0.5h

```bash
python -m pytest backend/tests/test_maria.py -q -k "not TestSegurancaApiHttp"
# Critério: 0 falhas; novos testes TDD passando (GREEN)
```

Se houver falha, corrigir antes de avançar.

---

### B0.6 · Deletar parser posicional (D1) · ~0.5h

**Somente após B0.5b verde.**

- Deletar `core/tool_call_textual_parser.py`.
- Remover import em `llama_client.py` (já substituído em B0.5a).
- Remover testes associados ao parser posicional em `test_maria.py` (buscar por `POSITIONAL_MAP`, `NOME_CANONICO`, `lista_reparada`, `parser_posicional`).
- Rodar suíte novamente — deve continuar verde.

---

### B0.7 · Atualizar vocabulário de telemetria (INCONS-3) · ~0.5h

Em `benchmark/tasks/task_schema.py` (`MariaTaskResult`):

```python
# ANTES:
tool_call_fonte: str | None = None  # "delta", "fallback_json", "parser_posicional"
fallbacks: list[str]  # lista_reparada, nome_mapeado, colunas_normalizadas

# DEPOIS:
tool_call_fonte: str | None = None  # "delta", "json", None
fallbacks: list[str]  # json_reparado, chaves_normalizadas, colunas_derivadas
```

Atualizar `maria_runner.py` onde esses campos são preenchidos.

---

### B0.8 · `system_prompt.txt` v4 · ~0.5h

**Novo arquivo completo** (não restaurar posicional — D1):

Estrutura do v4:
- Instrução de resposta JSON plano sem crases/texto.
- Seção "Ferramentas" com formato `{"ferramenta":"...", ...}` para cada uma.
- **Regra condicional:** "se o usuário fornecer dados, preencha `linhas` sempre".
- **1 exemplo com `linhas` preenchidas** (achado decisivo: 6/6 vs 0/6).
- Seção "Quando NÃO chamar ferramenta" (arquivo não mencionado, cumprimentos, etc.).
- Seção "Correção de erro": corrigir SOMENTE o campo apontado.
- Regra de encadeamento: "não narre, chame a próxima ferramenta".

---

### B0.9 · Smoke test manual do chat real · ~0.5h

Critérios de aceite antes de fechar B0:
- [ ] Criar planilha com `linhas` via JSON no terminal interativo — arquivo com dados corretos.
- [ ] Conversa em texto puro (cumprimento) — MARIA responde em texto, não JSON.
- [ ] Arquivo não existente — MARIA responde "Não encontrei o arquivo X."
- [ ] Confirmar operação — fluxo de confirmação intacto.

---

### Critério de aceite B0

- Suíte 100% verde (incluindo novos testes TDD).
- `grep -r "extrair_tool_call_textual\|POSITIONAL_MAP\|NOME_CANONICO" backend/` → zero resultados fora de arquivos deletados/arquivo.
- Smoke test manual passando.

---

## 3. Fase B0.5 — Baseline do benchmark · ~2h

> **Bloqueia B1+.** Capturar métricas pré-v5 para comparativo honesto.

- Rodar benchmark completo (3B e 7B, tasks atuais + nova Task 26) com B0 verde.
- Gravar resultados em `benchmark/results/run_baseline_v5/`.
- Não analisar agora — apenas preservar o artefato para `compare_runs` futuro (B3).

---

## 4. Fase B1 — Arquitetura hexagonal (Fases 0–3) · ~10–13h

> Bloqueia B2. Não modifica comportamento — apenas reorganiza estrutura de pacotes.

### Regra de dependência entre camadas (documentar em `docs/ARQUITETURA.md`)

```
domain/     → imports: stdlib apenas; ZERO de application/, infrastructure/, benchmark/
application/ → imports: domain/, interfaces/
interfaces/  → imports: domain/ (tipos), stdlib
infrastructure/ → imports: domain/, interfaces/; NEVER application/
benchmark/   → imports: somente via interfaces/ (ports públicos)
```

Violação = falha de CI (implementar via `import-linter` ou similar no B7).

### Estrutura-alvo

```
backend/
  domain/
    chat_session.py        ← de core/
    confirmacao.py         ← de core/  [esquecido no relatório hexagonal]
  interfaces/
    client_protocol.py     ← de core/
    interfaces.py          ← de core/
    session_storage.py     ← de core/  [classificado aqui: protocolo]
  application/
    maria_controller.py    ← de core/
    tool_chaining.py       ← de core/
    router.py              ← de core/
    manual_redacao.py      ← de core/
  infrastructure/
    llm/
      llama_client.py      ← de core/
    tools/
      tools_schema.py      ← de core/
      tool_call_json_parser.py  ← criado em B0
      validacao_tool_call.py   ← criado em B0 [classificar em domain/ ou application/]
      excel_handler.py     ← de core/
      word_handler.py      ← de core/
      file_utils.py        ← de core/
    paths.py               ← de core/  [esquecido no relatório hexagonal]
    database/              ← de database/ (mover na Fase 5)
  core/                    ← esvaziado; mantém __init__.py de compatibilidade por 1 versão
  config.py                ← permanece na raiz do backend
```

> **Nota sobre `validacao_tool_call.py`:** lógica pura (sem IO) → classificar em `domain/`. Se precisar de `CAMPOS_OBRIGATORIOS` de `tools_schema.py`, extrair essa constante para `domain/tool_call_contracts.py` para evitar dependência `domain→infrastructure`.

### Ordem de execução dentro do B1

```
B1.0: Criar pastas + __init__.py + ARQUITETURA.md com regras.
      Incluir em ARQUITETURA.md uma seção "Reservas de namespace (fases futuras)"
      listando, sem implementar:
        - domain/intent_classification.py       (a implementar em B4.5)
        - application/intent_router.py          (a implementar em B4.5)
        - infrastructure/tools/entity_extractor.py (a implementar em B4.5)
        - interfaces/translation_protocol.py    (a implementar em B4.6)
        - infrastructure/translation/nllb_client.py (a implementar em B4.6)
      Cada item deve indicar a camada e a regra de dependência que já se aplica a
      ela (ver regra de dependência entre camadas, já documentada nesta seção),
      de modo que B4.5/B4.6, quando executadas, não exijam redesenho de fronteiras.
B1.1: domain/ (chat_session, confirmacao) + atualizar imports
B1.2: interfaces/ (client_protocol, interfaces, session_storage) + atualizar imports
B1.3: application/ (maria_controller, tool_chaining, router, manual_redacao) + imports
B1.4: infrastructure/ (llama_client, tools_schema + parser + validador, handlers) + imports
B1.5: Manter core/ com re-exports de compatibilidade (from backend.infrastructure.llm.llama_client import *)
B1.6: Suíte 100% verde + smoke test manual
```

**Estratégia anti-regressão:** mover 1 arquivo por vez, rodar `pytest -x` antes do próximo. Não fazer big-bang.

---

## 5. Fase B2 — Benchmark → ports (zero acoplamento) · ~4–6h

> Bloqueia B3.

### Problema atual (INCONS-4 confirmado)

```python
# maria_runner.py hoje importa símbolo PRIVADO:
from core.llama_client import _montar_mensagens_com_reforco  # ← privado

# E mistura dois estilos:
from backend.core.config import ...   # estilo absoluto
from core.chat_session import ...     # sys.path.insert hack
```

### Ações

1. Tornar `_montar_mensagens_com_reforco` pública (renomear para `montar_mensagens_com_reforco`) em `infrastructure/llm/llama_client.py`, com `@` de deprecação do nome antigo por 1 versão.
2. Criar `BenchmarkConfig` injetável em `benchmark/benchmark_config.py` — absorver todas as constantes de config que o runner usa.
3. Reescrever imports do `maria_runner.py`: somente de `backend.interfaces.*` e `backend.application.*` e `benchmark.*`. Zero `sys.path.insert`.
4. Mover `benchmark/` para raiz do monorepo como `benchmarks/maria_bench/` (D4).
5. Critério de aceite: `grep -r "_montar_mensagens_com_reforco\|sys.path.insert" benchmarks/` → zero.

---

## 6. Fase B3 — Storage SQLite + report v2 · ~5–7h

> Bloqueia B4. Habilita `compare_runs` histórico.

### Schema SQLite (D5 — aprovado)

```sql
-- runs: metadados de cada execução
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    modelo TEXT NOT NULL,
    prompt_hash TEXT,
    config_json TEXT
);

-- results: uma linha por execução por task
CREATE TABLE results (
    id INTEGER PRIMARY KEY,
    run_id INTEGER REFERENCES runs(id),
    task_id INTEGER,
    task_name TEXT,
    category TEXT,
    model TEXT,
    tool_detected TEXT,
    tool_correct INTEGER,
    args_correct INTEGER,
    tool_call_fonte TEXT,   -- "delta", "json", NULL
    parse_suspeito INTEGER,
    latency_ms REAL,
    tokens_por_segundo REAL,
    runtime_ok INTEGER,
    finish_reason TEXT,
    fallbacks_json TEXT,    -- JSON serializado
    correcoes_json TEXT,
    dados_arquivo_validos INTEGER,
    contexto_ok INTEGER,
    correction_attempts INTEGER
);
```

### Report v2

- Default: resumido < 200 linhas (critério B3).
- Flag `--detail`: inclui prompt_enviado e resposta_bruta.
- `compare_runs` 100% via SQL: `GROUP BY modelo, task_id, tool_call_fonte`.

### Métricas novas (O3 + O4)

- Taxa `tool_call_fonte` por run: `delta vs json vs None`.
- `parse_suspeito` como alarme: se taxa > threshold, sinalizar no report.

---

## 7. Fase B4 — Tasks v2 + avaliação de `linhas` · ~6–8h

> Bloqueia B5.

### Novos campos em `MariaTask`

```python
linhas_esperadas: list[dict] | None = None  # conteúdo esperado para match
limite_conhecido: bool = False               # task marcada como limite do modelo
```

### Nova Task 26 (D6)

- Dados no corpo da mensagem (sem fixture mandarim).
- Validação via `linhas_esperadas` com match case-insensitive.
- Task original de tradução Mandarim→PT marcada como `limite_conhecido=True`.

### Correção de INCONS-1

`_argumentos_compativeis()` em `maria_runner.py` passa a verificar `linhas_esperadas`:
- Match exato ou subset case-insensitive dos valores.
- `dados_arquivo_validos` calculado via conteúdo real, não só "não-vazio".

### V6 (coerção numérica) — decisão com dados

Rodar benchmark com tasks de dados numéricos (3B e 7B). Se `Preco` como string atrapalha ordenação no frontend → subir V6 para default. Senão, manter como OPCIONAL.

---

## 8. Fase B4.5 — Intent Classification / Entity Extraction (pré-processamento) · ~10–14h

> Depende de B4 (Task 26 redesenhada + infraestrutura de tasks v2). Não bloqueia B5–B7.
> Origem: relatório de validação de literatura (2026-09-08) + análise de viabilidade
> concluindo que a implementação deve ocorrer como fase própria, posterior a B4, para
> evitar sobreposição com `validacao_tool_call.py` (B0.3) e com o redesenho da Task 26 (B4).

### Objetivo

Adicionar uma camada de middleware pré-LLM que classifica a intenção da mensagem do
usuário e extrai entidades estruturadas (nome de arquivo, colunas, linhas de dados)
antes de montar o prompt enviado ao modelo — reduzindo a dependência do LLM para
tarefas de baixo risco e alta frequência (classificação, extração de dados já
presentes na mensagem).

### Escopo

1. `domain/intent_classification.py` (novo): classificador heurístico em cascade —
   regex/keywords (< 1ms) → embedding opcional → fallback LLM (temperatura 0) apenas
   para casos ambíguos. Sem I/O, sem dependência de `application/` ou `infrastructure/`.
2. `infrastructure/tools/entity_extractor.py` (novo): extração de entidades híbrida —
   regex estruturado como padrão; fallback para LLM somente quando a heurística falhar.
   Reutiliza a whitelist de ferramentas já centralizada em `CAMPOS_OBRIGATORIOS`
   (mesma fonte usada por B0.2/B0.3 — não duplicar).
3. `application/intent_router.py` (novo): orquestra classificação → extração →
   construção do prompt; define thresholds de confiança por intenção (execução direta,
   fallback LLM, ou pedido de esclarecimento ao usuário).
4. `benchmark/tasks/tasks_intent.py` (novo): Tasks 29–32 (mensagem com dados embutidos,
   mensagem ambígua, múltiplas intenções na mesma mensagem — tradução tratada em B4.6).

### Restrição obrigatória (evitar regressão do tipo BUG-4)

A extração de entidades **não deve reimplementar** a normalização de chaves de
`linhas`/`colunas` já resolvida em `validacao_tool_call.py` (B0.3, validadores V3–V5).
`entity_extractor.py` produz um rascunho de argumentos a partir do texto livre da
mensagem; a validação/normalização final desses argumentos passa obrigatoriamente
pelo mesmo `validacao_tool_call.py` usado no fluxo pós-parser do LLM — um único
caminho de validação para os dois casos (dados extraídos pelo sistema ou gerados
pelo modelo).

### Critério de aceite

- [ ] Suíte 100% verde, incluindo os novos testes de `intent_classification` e `entity_extractor`.
- [ ] Tasks 29–31 (novas) executadas no benchmark v2 (SQLite, B3) com métrica `args_correct` registrada.
- [ ] `grep -r "df.reindex\|k.lower() for k" domain/intent_classification.py infrastructure/tools/entity_extractor.py` → zero (garante que a normalização não foi duplicada fora de `validacao_tool_call.py`).
- [ ] Nenhuma alteração em `core/validacao_tool_call.py` além de eventual exposição de função pública já existente para reuso.

---

## 9. Fase B4.6 — Roteamento para modelo especializado de tradução (NLLB-200) · ~6–9h

> Depende de B4. Independente de B4.5 — pode ser executada em paralelo ou isoladamente.
> Introduz uma dependência de infraestrutura nova (modelo de tradução dedicado);
> tratada como fase própria por não fazer parte do pipeline principal de tool calling.

### Objetivo

Rotear tarefas de tradução para um modelo especializado (NLLB-200 ou equivalente,
~600M parâmetros) em vez de sobrecarregar o modelo principal de tool calling
(Qwen2.5-Omni 7B) com uma tarefa de qualidade linguística especializada.

### Escopo

1. `interfaces/translation_protocol.py` (novo): `TranslationProtocol` (Protocol) —
   contrato estrutural mínimo (`traduzir(texto: str, idioma_origem: str, idioma_destino: str) -> str`).
2. `infrastructure/translation/nllb_client.py` (novo): cliente HTTP/local para o
   modelo de tradução, implementando `TranslationProtocol`. Falha de conexão/timeout
   deve ter fallback explícito: se o serviço de tradução não estiver disponível,
   devolver erro claro ao chamador (nunca traduzir "no escuro" via o modelo principal
   sem sinalizar a substituição).
3. Ponto de integração: `application/intent_router.py` (de B4.5) despacha para
   `TranslationProtocol` quando a intenção classificada for `traduzir` — **este é o
   único ponto de acoplamento entre B4.5 e B4.6**; nenhuma outra dependência cruzada.
4. Task 26 original (tradução Mandarim→Inglês, marcada `limite_conhecido=True` em B4)
   pode ser reavaliada com o roteamento ativo, mas isso é opcional e não é critério
   de aceite desta fase.

### Critério de aceite

- [ ] Suíte 100% verde, incluindo testes de `nllb_client` com mock de indisponibilidade do serviço (timeout/conexão recusada) e fallback de erro claro.
- [ ] `TranslationProtocol` documentado em `interfaces/` seguindo o mesmo padrão de `LLMClientProtocol` (B1).
- [ ] Nenhuma chamada a `nllb_client.py` fora de `application/intent_router.py`.
- [ ] Decisão explícita registrada no `CHANGELOG.md` sobre se o modelo de tradução roda local (novo download/binário) ou via serviço externo — pendência de decisão, não assumir.

---

## 10. Fase B5 — CLI completa · ~3–4h

Subcomandos:
```
maria-bench run   [--model 3b|7b] [--tasks 1,2,3] [--repeat N] [--response-format-schema]
maria-bench judge [run_id]
maria-bench report [run_id] [--detail]
maria-bench compare [run_id_a] [run_id_b]
```

Overrides de sampler via flags: `--temperature`, `--ctx-size`, `--system-prompt`.

---

## 11. Fase B6 — Semântica + LLM-judge + response_format · ~5–8h

### LLM-as-judge (O5)

- Calibração: ~30 execuções rotuladas manualmente antes de entrar no report como métrica.
- Concordância mínima: 80% contra rotulagem manual.
- Rubrica 4 eixos: tool_correta / args_completos / conteúdo_coerente / idioma.
- Temperatura 0; pós-processamento a partir do DB.

### `response_format` experimental (D3)

- Flag: `LLAMA_RESPONSE_FORMAT_SCHEMA=1` ou `--response-format-schema` na CLI.
- Schema gerado **por ferramenta** de `TOOLS_SCHEMA` (não global) — sênior OMISSÃO-3 corrigida.
- Aplicado somente em tasks com `expected_tool` declarado.
- **Não entra no pipeline de produção.**

### O1 — Fonte única de verdade

Gerar automaticamente:
1. Seção "Ferramentas" do `system_prompt.txt` via template de `TOOLS_SCHEMA`.
2. `response_format` schema via `TOOLS_SCHEMA`.
3. Validador V1 (campos obrigatórios) via `CAMPOS_OBRIGATORIOS`.

Zero duplicação manual.

---

## 12. Fase B7 — v5.0.0 final · ~2–3h

- `README_benchmark.md` reescrito.
- `docs/ARQUITETURA.md` finalizado com mapa de camadas.
- `docs/DECISOES_BANCO_DADOS.md` atualizado com SQLite do benchmark.
- `CHANGELOG.md` com v5.0.0.
- Limpeza: `core/` esvaziado com aviso de deprecação; remoção do `sys.path.insert` hack.
- `import-linter` ou `flake8-import-order` configurado para enforçar regra de camadas em CI.

---

## 13. Critérios de aceite por fase (resumo)

| Fase | Critério binário |
|------|-----------------|
| B0 | Suíte 100% verde; `grep POSITIONAL_MAP` → 0; smoke test manual OK |
| B0.5 | Artefato gravado em `results/run_baseline_v5/` |
| B1 | Suíte 100% verde; `grep "sys.path.insert" backend/` → 0; `grep "from core\." backend/` → apenas re-exports |
| B2 | `grep "_montar_mensagens_com_reforco" benchmarks/` → 0; zero imports privados |
| B3 | `compare_runs` 100% via SQL; report resumido < 200 linhas |
| B4 | Task 26 nova: 0 execuções com coluna vazia; `linhas_esperadas` avaliadas |
| B4.5 | Suíte 100% verde (testes de intent_classification/entity_extractor); Tasks 29–31 com `args_correct`; grep normalização duplicada → 0 |
| B4.6 | Suíte 100% verde (`nllb_client` com mock de indisponibilidade); `TranslationProtocol` documentado; zero chamadas fora de `application/intent_router.py` |
| B5 | `maria-bench run --help` funciona; todos os subcomandos executáveis |
| B6 | Concordância LLM-judge ≥ 80% antes de entrar no report |
| B7 | `import-linter` passa; `CHANGELOG.md` atualizado; `core/` vazio |

---

## 14. Oportunidades de evitar retrabalho

| Oportunidade | Como aplicar | Quando |
|---|---|---|
| **Mover apenas 1 arquivo por vez no B1** | `pytest -x` após cada movimento | B1 |
| **Re-exports em `core/__init__.py`** | Imports externos continuam funcionando durante transição | B1 |
| **TDD primeiro no B0** | Testes escritos antes do código eliminam descobertas tardias | B0.1 |
| **`CAMPOS_OBRIGATORIOS` como fonte única** | Parser, validador e `response_format` derivam daqui | B0.2, B6 |
| **SQLite desde B3** | Evita re-análise de JSONs gigantes em B4/B5/B6 | B3 |
| **Não tocar `core/config.py` até B7** | Evita quebrar todos os imports durante B0/B1 | B0–B6 |
| **Task 26 substituída, não consertada (D6)** | Evita iterar sobre tarefa insolúvel (tradução dentro de ferramenta) | B4 |
| **Schema `response_format` gerado, não escrito** | Elimina drift entre prompt/validação/flag experimental | B6 (com base em B0.2) |

---

## 15. Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| `domain/` importando `infrastructure/` por acidente | Alta | Alto | `import-linter` desde B1; `pytest -x` após cada movimento |
| T3 (reparo de truncamento) produz `linhas` parciais sem aviso | Média | Alto | Aviso explícito ao usuário quando `_reparado=True` em `linhas` |
| Regressão no chat real durante B0 (parser novo quebra casos existentes) | Média | Alto | Smoke test B0.9 antes de fechar B0 |
| 3B produz valores numéricos como string — V6 não ativado | Baixa | Médio | Documentar como diferença conhecida 3B×7B; decidir em B4 com dados |
| LLM-judge com concordância < 80% na calibração | Média | Médio | Não publicar como métrica até atingir threshold; usar como diagnóstico interno |
| Amostras n=3 nas decisões de prompt | Alta | Baixo | Revalidar prompt v4 no B0.5 (benchmark completo) antes de virar padrão |

---

*Próximo passo imediato: iniciar B0.1 (escrever testes TDD em RED).*
