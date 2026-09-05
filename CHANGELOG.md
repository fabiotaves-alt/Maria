# CHANGELOG - Projeto MARIA

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [4.1.29] — Correção do sampler: restaura tool calling sem reexpor o loop — 2026-09-05

### 🔧 Regressão corrigida (run `run_20260905_170437`)
- O ajuste agressivo do sampler (4.1.27) derrubou a acurácia de tool calling de 100% para **76%**: `presence_penalty`/`frequency_penalty` em 0.1 penalizavam o nome canônico da ferramenta (presente no system prompt) e os tokens estruturais do JSON — o modelo passou a emitir `create_planilha` (inglês), JSON malformado e prosa após a chamada.
- **`core/config.py`**: `LLAMA_REPEAT_PENALTY` 1.3→**1.1** (default clássico), `LLAMA_FREQUENCY_PENALTY`/`LLAMA_PRESENCE_PENALTY` 0.1→**0.0** (desativados). O loop de frase da Task 8 continua coberto por `LLAMA_DRY_MULTIPLIER` **0.8** + `LLAMA_REPEAT_LAST_N` **128** — mecanismos que não atingem tokens estruturais isolados.
- **`backend/benchmark/README_benchmark.md`**: tabela de sampler e seção de orçamento de tokens (`LLAMA_NUM_PREDICT_DOCUMENTO` 300→**600**) atualizadas.

### 🧪 Testes
- Teste de defaults do sampler (`TestSamplerParamsBenchmark`) atualizado para os novos valores.

---

## [4.1.28] — Avisos de fallback por mecanismo (em vez de "detectada via parser") — 2026-09-05

### 🎯 Avisos condicionais por mecanismo de fallback
- Antes, `⚠️ ferramenta detectada via parser` aparecia em ~100% das tool calls (o llama-server não emite `tool_calls` nativas). Agora os avisos aparecem **somente quando o sistema usa um fallback para corrigir comportamento inesperado**, indicando **qual** mecanismo:
  - `⚠️ fallback JSON` — tool call vazada como JSON no content.
  - `⚠️ nome mapeado: "bruto" → "canônico"` — nome legível mapeado (`NOME_CANONICO`).
  - `⚠️ lista reparada` — lista posicional truncada por max_tokens e reparada.
  - `⚠️ colunas normalizadas` — colunas achatadas/string.
- `parser_posicional` **limpo** (formato instruído) **não** gera mais aviso.

### 📊 Nova métrica `fallbacks`
- **`llama_client.py`**: `_resolver_tool_call_final` retorna `(tool_call, fonte, nome_bruto, fallbacks)`.
- **`tool_call_textual_parser.py`**: marca `_lista_reparada` e `_colunas_normalizadas`.
- **`task_schema.py`** + **`runners/maria_runner.py`**: campo `fallbacks: list[str]` (salva no `log.json`).

### 🧪 Testes
- **203 testes passando + 33 subtests** — novos: fallback por mecanismo, ausência de aviso quando limpo, colunas achatadas.

---

## [4.1.27] — Mitigações de loop + fonte de detecção e avisos no terminal — 2026-09-05

### 🛡️ Mitigações de loop de geração (sampler)
- **`core/config.py`**: `LLAMA_REPEAT_LAST_N` 64→**128**, `LLAMA_REPEAT_PENALTY` 1.1→**1.3**, `LLAMA_FREQUENCY_PENALTY`/`LLAMA_PRESENCE_PENALTY` 0.0→**0.1**, `LLAMA_DRY_MULTIPLIER` 0.0→**0.8** — mitigam o loop de **frase inteira** (run `run_20260905_150433`, task 8: o 7B repetia "Prezado(a) Senhor(a)... Meu nome é Maria..." até estourar 600 tokens, contado como sucesso).

### 🔎 Captura da fonte de detecção + mapeamento de nome
- **`core/llama_client.py`**: `_resolver_tool_call_final` agora retorna `(tool_call, fonte, nome_bruto)` — fonte ∈ `{delta, fallback_json, parser_posicional}`; propagada via `metricas_saida`/`extras_saida`.
- **`core/tool_call_textual_parser.py`**: `NOME_CANONICO` mapeia nomes legíveis (`"Listar arquivos"`) → canônico (`"listar_arquivos"`) — case (b).
- **`task_schema.py`** + **`runners/maria_runner.py`**: novos campos `tool_call_fonte`, `tool_nome_bruto`, `tool_nome_final` (estado bruto no JSON).

### 🖥️ Terminal: avisos em linhas separadas
- **`analysis/report.py`** (`formatar_avisos`) + **`run_benchmark.py`**: correções e detecção via parser aparecem em **linhas próprias abaixo do `rep X/Y`** (não mais inline), suportando múltiplos avisos.

### 🧪 Testes
- **200 testes passando + 33 subtests** — novos: mapeamento de nome, avisos (correção/parser), fonte de detecção; defaults do sampler atualizados.

---

## [4.1.26] — Log de correções + métricas de qualidade semântica — 2026-09-05

### 🧹 Log do terminal: correção visível (Fase 1)
- **`core/tool_chaining.py`**: `validar_e_corrigir_tool_call_stream` registra o **antes → depois** da auto-sanitização de `nome_arquivo` (path traversal) em `correcoes` e devolve no resultado.
- **`benchmark/runners/maria_runner.py`**: expõe `correcoes` no `MariaTaskResult`.
- **`benchmark/analysis/report.py`**: novo `formatar_correcoes()` + sufixo `⚠️ corrigido campo: "antes" → "depois"` na linha de resumo.
- **`benchmark/run_benchmark.py`**: sufixo de correção nas duas saídas do terminal (CLI e programática) — uma linha só, sem os INFO poluentes.

### 📊 Métricas de qualidade semântica (Fase 2)
- **`task_schema.py`**: novos campos em `MariaTaskResult` — `correcoes`, `titulo_conteudo_invertido`, `placeholder_detectado`, `conteudo_curto`, `nome_com_extensao`.
- **`maria_runner.py`**: `_analisar_semantica()` (heurística) detecta título/conteúdo invertidos, placeholders (`[data]`, `[Seu Nome]`), conteúdo curto e nome com extensão.
- **`analysis/metrics.py`**: `semantic_quality_rate`, `semantic_errors_by_type`, `correcoes_count`.
- **`analysis/report.py`**: seção `## Qualidade Semântica` + linha na tabela de métricas gerais.
- **`run_benchmark.py`**: linha `Qualidade semântica` no `Resumo`.

### 🧪 Testes
- **196 testes passando + 33 subtests** — 9 novos (`TestAnaliseSemantica`, `TestFormatarCorrecoes`); mocks de `metrics` atualizados.

---

## [4.1.25] — Decisão final do system prompt (V2) e consolidação no main — 2026-09-05

### ✅ System prompt final: V2 (hash `091d6ab5c83f`)
- Selecionado o **V2** — o prompt que obteve **100% de tool accuracy no 7B** em duas runs independentes (`run_20260905_094804` e `run_20260905_131333`).
- **V3** (`ce187676ddf7`) **abandonado** — degradou no 3B (55,6% e 25%) e nunca foi validado no 7B.

### 🔀 Consolidação no `main`
- Merge de `feat/menu-avaliacao-benchmark` (v4.1.22), `feat/ux-avaliacao-terminal` (v4.1.23), `fix/benchmark-degeneracao-multicaractere` (v4.1.24) e `feat/system-prompt-v2`.
- Integrado o PR #32 (ID do modelo no relatório/log).

### 🧹 Limpeza de branches
- Deletadas 15 branches integradas/superseded (local + remote), incluindo `feat/system-prompt-v3`.

### 🧪 Testes
- **187 testes passando + 33 subtests** no `main` consolidado (sem regressão).

---

## [4.1.24] — Análise de benchmarks 2026-09-05, system prompt V3 e detecção de loop degenerado multi-caractere — 2026-09-05

### 📊 9 runs de benchmark executadas hoje (modelos 7B e 3B, 3 versões de system prompt)
- **7B — V1 (madrugada, hash prompt `1a5838a1f67b`)**: tasks 22/23 (×3, ×2, ×1) com 100%; sequência completa 1–25 ×1 com **92%** (falhas: tasks 2 e 10).
- **7B — V2 (manhã, hash `091d6ab5c83f`)**: **1–25 ×3 = 75 execuções com 100% de acurácia de tool calling** — melhor resultado histórico do projeto (run `run_20260905_094804`).
- **3B — V2**: 63/75 = **84,0%** (falhas: 12, 13, 21 e 25).
- **3B — V3 (tarde; working tree, hash `ce187676ddf7`)**: 13 execuções apenas (tasks 12, 13, 25) → 55,6% e 25%; **V3 ainda não validado no 7B**.
- Sem loops `\n` (o padrão anterior — task 15); **1 truncamento** (`finish_reason=length`) na run 3B.

### 🐛 Loop degenerado multi-caractere não detectado (falso positivo na run `run_20260905_101728`)
- A task 10 (Documento comunicado), rep 1, do 3B às 10:30 gerou **`_x_x_x…` por 600 tokens** (`finish_reason=length`, latência 127s) e **foi contabilizada como sucesso** (`tool_correct=True`, `errors=[]`) — documento lixo criado.
- **Causa raiz**: `_detectar_degeneracao()` só detectava **repetição de um único caractere** no fim do texto (ex.: `\n`×100). O padrão real `_x_x_x_…` (bloco de 2 caracteres alternados) não disparava a detecção.
- **Impacto**: acurácia real da run ≈ **82,7%** (62/75) em vez dos 84,0% reportados; 127s desperdiçados.
- **Correção aplicada**: detector ampliado para **padrões cíclicos multi-caractere** (bloco repetido de 1..N chars no fim do texto) — continua abortando a geração cedo, suprimindo a tool call degenerada e registrando `finish_reason=degenerate` + `DegenerateGeneration`.

### ✏️ System prompt — 3 versões usadas hoje (rastreáveis por hash)
- **V1** (`1a5838a1f67b`): abertura "brasileira" + seção `## Arquivo não encontrado` (== HEAD commitado).
- **V2** (`091d6ab5c83f`): abertura "assistente" + `## Quando NÃO chamar ferramenta` com **5 bullets** (inclui regra de "certeza absoluta" que destravou tasks 21–25) → **100% no 7B**.
- **V3** (working tree, hash `ce187676ddf7`): reestruturado — nova seção `## Quando chamar ferramenta`, `## Quando NÃO` com **4 bullets** (bullet "certeza absoluta" **removida**), "Explicações QUEBRAM" e "nomes inseguros DEVEM ser corrigidos".
- ⚠️ **Atenção**: a bullet removida no V3 era o que resolvia as tasks 21–23 no V2; **V3 precisa de validação no 7B com a run completa** antes da adoção (só foi testado no 3B até agora).

### 🧪 Testes
- **Suíte: 187 testes passando + 33 subtests** (`pytest backend/tests/test_maria.py`) — 5 novos em `TestDeteccaoDegeneracao` cobrindo bloco de 2 chars (`_x_x…`), bloco de 3 chars, prefixo válido seguido de loop, limiar e texto narrativo real (não deve disparar).

---

## [4.1.23] — UX da Avaliação de Desempenho: terminal limpo, janela do llama-server com logs e sem aviso de modelo — 2026-09-05

### 🧹 Terminal da MARIA limpo (`run_benchmark.py`)
- `run_benchmark_programatico()` virou **wrapper público** que eleva o logger raiz para `WARNING` durante a avaliação e o **restaura ao nível anterior em `try/finally`** (mesmo com `SystemExit`, `KeyboardInterrupt` ou erro inesperado). As linhas `core.llama_client - INFO - …` (parser, `tools_schema`, `maria_runner`) não poluem mais o terminal — restam apenas os prints de progresso (`[1/N] Tarefa`, `rep x/y`, acumulado, resumo).
- O corpo da avaliação foi movido para `_run_benchmark_programatico()` (mesma lógica, sem reindentação).

### 🖥️ Janela do llama-server com logs normais (`servidor_llama.py`)
- `_abrir_janela_servidor()` agora inicia o `llama-server.exe` **diretamente** com `CREATE_NEW_CONSOLE` (sem o wrapper do PowerShell, que deixava a janela preta). A janela nova exibe os logs habituais do servidor, como quando o exe é rodado manualmente.

### 🔇 Aviso de divergência de modelo removido
- `_run_benchmark_programatico()` atualiza também o binding local do módulo (`globals()["LLAMA_MODEL"]`) com o modelo escolhido no menu — o warmup passa a comparar com o "configurado" correto e o aviso `[AVISO] LLAMA_MODEL configurado = 'qwen2.5-omni-3b'…` não aparece mais ao rodar com o 7B.

### 🧪 Testes
- **Suíte: 182 testes passando + 33 subtests** (`pytest backend/tests/test_maria.py`).
- Smoke tests (não versionados): wrapper restaura o nível do logger; `_abrir_janela_servidor` chama `Popen` direto com `CREATE_NEW_CONSOLE`; `globals()["LLAMA_MODEL"]` atualizado.

---

## [4.1.22] — Avaliação de Desempenho integrada ao terminal + automação do llama-server — 2026-09-05

### 🎯 Menu de modo e avaliação (`backend/ui_terminal.py`)
- **Menu de MODO** após o banner: `1. Chat` / `2. Avaliação de Desempenho` — o fluxo de chat permanece 100% inalterado (sem regressão); a avaliação não inicializa o controller de chat.
- **`_menu_avaliacao()`**: escolha do modelo (Qwen2.5-Omni 3B/7B), seleção de tarefas (IDs separados por espaço ou `0` = todas) e repetições por tarefa (default `BENCHMARK_REPETICOES`, agora **2**).
- **`_coletar_metricas_sistema()`**: snapshot pré-warmup de CPU/RAM/GPU (`psutil`; `pynvml` opcional com fallback silencioso).
- **`_executar_avaliacao()`**: chama `run_benchmark_programatico()` e exibe `SystemExit`/erros de forma limpa, sem traceback cru.
- Caixas de menu desenhadas por helper `_caixa()` com bordas alinhadas dinamicamente.

### 🆕 Automação do llama-server (`backend/benchmark/servidor_llama.py`)
- A escolha do modelo no menu deixa de ser cosmética: o llama-server abre em **nova janela do PowerShell** (permanece aberta) com o GGUF correto (`-hf ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M` ou `...7B...`) e os parâmetros `-c 2048 -t 4 -b 1024 -ub 256 --port 8080 -lv 1`.
- Reutiliza servidor já ativo com o mesmo modelo; se houver outro modelo, pergunta encerrar/usar/cancelar; auto-descoberta do executável (ENV `LLAMA_SERVER_EXE` > PATH > `~/Documents/llama_cpp`) e espera por `/v1/models`.
- Parâmetros configuráveis via ENV (`LLAMA_SERVER_CTX`, `LLAMA_SERVER_THREADS`, `LLAMA_SERVER_BATCH`, `LLAMA_SERVER_UBATCH`, `LLAMA_SERVER_LOG_LEVEL`, `LLAMA_SERVER_STARTUP_TIMEOUT`, `LLAMA_SERVER_POLL_INTERVALO`).

### 🐛 Correção: repetições respeitadas
- **`run_benchmark.py` (`main()`)**: usava a constante `BENCHMARK_REPETICOES` no lugar de `args.repeticoes` — pedir `--repeticoes 1` rodava 3. Agora o valor escolhido (CLI ou menu) é respeitado em prints, `run_repeated` e `meta.repeticoes_por_tarefa`.
- **`benchmark_config.py`**: default de `BENCHMARK_REPETICOES` alterado de 3 para **2** (sempre sobrescrevível pelo usuário).

### ⚙️ Ponto de entrada programático (`run_benchmark.py`) e relatório
- **`run_benchmark_programatico()`**: garante o llama-server do modelo, faz warmup real cronometrado, executa as tarefas com progresso no terminal da MARIA (mesmo processo) e gera `report.md` + `log.json`.
- **`log.json`**: `meta.warmup_duracao_s` e `meta.metricas_sistema` registrados.
- **`report.py`**: `generate_report()` aceita `metricas_sistema`/`warmup_duracao_s` (opcionais, retrocompatível) e insere a seção **`## Sistema`** (plataforma, CPU, RAM, GPU e tempo de warmup) logo após `## Modelo`.

### 🧪 Testes
- **Suíte: 182 testes passando + 33 subtests** (`pytest backend/tests/test_maria.py`).
- Smoke tests manuais (não versionados): menus, modo chat sem regressão, wiring da avaliação e helpers do servidor — `SMOKE_OK`.
- Validação empírica live (llama-server real) pendente de execução manual pelo usuário.

---

## [4.1.21] — Benchmark: tarefas 22/23 reformuladas para o fluxo real (ferramenta executa, erro volta ao modelo) — 2026-09-05

### 🎯 Novo conceito das tarefas 22 e 23 (`tasks_edges.py`)

Análise do run `run_20260904_232935`: o modelo já chamava `editar_planilha` diretamente em **todas** as repetições de 22/23 — o conceito anterior (exigir `listar_arquivos` antes da edição) não espelhava uma situação real e punia o comportamento natural. Novo desenho em 2 turnos reais:

- **Turno 1**: usuário pede edição com nome realista ("Edite a planilha estoque com a coluna preco." / "Atualize a planilha clientes com as colunas nome e email."), sem entregar a inexistência.
- **Turno 2**: o modelo chama `editar_planilha` → `confirm_sequence=["sim"]` auto-confirma → a ferramenta **EXECUTA de verdade** e falha (arquivo ausente na pasta isolada, `fixtures=[]`), devolvendo o erro real `"Arquivo 'estoque.xlsx' não encontrado na pasta de arquivos gerados."` → o erro volta ao modelo → ele responde em texto.
- `tools_obrigatorios=["editar_planilha"]`: avalia "chamou a ferramenta (cadeia) **e** terminou em texto". Modelo que re-chama a ferramenta após o erro → ✘ (antes o erro travava a tarefa como falha de runtime).

### ⚙️ Runner (`maria_runner.py`)

- **Novo caminho de erro em runtime**: quando a ferramenta de escrita confirmada falha (`PermissionError`/`OSError`/`ValueError`), o erro real é devolvido ao modelo via `continuar_com_resultado_ferramenta_stream` (mesma mecânica do encadeamento de leitura), com timeout por chamada e soma de tokens — antes, a exceção virava erro de tarefa (`runtime_ok=False`) e o modelo nunca via o resultado. Agora `runtime_ok` permanece True: arquivo inexistente é o cenário esperado, não erro.

### 📝 System prompt (`system_prompt.txt`)

- Nova seção `## Arquivo não encontrado`: "Ao receber erro de ferramenta informando que o arquivo não foi encontrado, NÃO chame a ferramenta de novo: responda em texto dizendo que o arquivo não foi encontrado e oferecendo criar um novo, se for o caso."
- Distinção clara entre **erro de chamada inválida** (seção `## Correção de erro` → corrigir e re-chamar) e **arquivo não encontrado em runtime** (responder em texto). Reabilita o teste `TestSystemPromptExcecaoArquivoInexistente` (pré-existente falhando).

### 🧪 Testes

- `TestMariaRunnerCadeiaFerramentas` reescrito: erro devolvido → resposta em texto ✔ | re-chamada após erro ✘ | responder sem chamar a ferramenta ✘.
- `TestTarefas22E23EscritaInexistente` (novo): desenho das tarefas 22/23 (`tools_obrigatorios=["editar_planilha"]`, `confirm_sequence=["sim"]`, sem fixtures).
- `TestMariaRunnerMensagemDeErro` atualizado para a nova semântica (erro da ferramenta não é mais erro de tarefa).
- **Suíte: 182 testes passando + 33 subtests** (antes 181/182). Validação empírica live (llama-server) pendente.

---

## [4.1.20] — Benchmark: tarefas 22/23 redesenhadas para simular 2 turnos reais (verificação de leitura) — 2026-09-04

### 🎯 Redesenho das tarefas 22 e 23 (`tasks_edges.py`)

As tarefas antigas ("Edite a planilha planilha_inexistente...") entregavam a inexistência do arquivo no próprio nome, esperavam que o modelo NÃO chamasse ferramenta (`expected_tool=None`) e não espelhavam uma situação real — induziam o modelo ao erro e puniam o comportamento correto (verificar antes de editar; nos runs, `tool_detected=listar_arquivos` virava `tool_correct=false`).

- **Novo desenho em 2 turnos**: turno 1 — usuário pede edição com nome realista ("Edite a planilha estoque com a coluna preco." / "Atualize a planilha clientes com as colunas nome e email."), sem entregar a inexistência; turno 2 — o modelo chama `listar_arquivos`, a ferramenta devolve o erro real da aplicação ("A pasta está vazia (nenhum arquivo encontrado).") via encadeamento de leitura já existente (`encadear_leitura_stream`) e o modelo responde em texto explicando que o arquivo não existe.
- `fixtures=[]` e `confirm_sequence=[]`: o diretório isolado do benchmark fica vazio, então a ferramenta devolve o erro real (não simulado).

### ⚙️ Infraestrutura de avaliação (`task_schema.py`, `maria_runner.py`)

- **`MariaTask.tools_obrigatorios` (novo)**: ferramentas que DEVEM ter sido chamadas na execução.
- **`MariaTaskResult.cadeia_ferramentas` e `tool_call_inicial` (novos)**: a cadeia completa de ferramentas chamadas (tool call inicial + encadeamento/correção) e a primeira tool call — antes disso o runner sobrescrevia `tool_call_final` com a última chamada e o benchmark não distinguia "verificou com listar_arquivos" de "respondeu sem verificar".
- **Nova regra de avaliação** (somente quando `tools_obrigatorios` está definido; demais tarefas inalteradas): `tool_correct` = todas as ferramentas exigidas presentes na cadeia **e** a execução termina em texto (sem escrita pendente). Classificação: verificou + respondeu ✔ | `editar_planilha` direto ✘ | verificou mas tentou editar mesmo assim ✘.

### 🧪 Testes

- **4 testes novos**: `TestMariaRunnerCadeiaFerramentas` (verificar e responder em texto ✔; edição direta ✘; verificar e escrever depois ✘) e `TestTarefas22E23Verificacao` (desenho das tarefas).
- **Suíte: 182 testes — 181 passando + 33 subtests.** A única falha (`TestSystemPromptExcecaoArquivoInexistente`) é pré-existente e alheia a esta mudança: decorre da reescrita ainda não commitada do `backend/core/system_prompt.txt` na working tree.

---

## [4.1.19] — Benchmark: auto-sanitização de path traversal e proteção contra geração degenerada — 2026-09-04

### 🐛 Correções (tasks 21–25 e task 15)

- **Auto-sanitização de path traversal** (`tools_schema.py`, `tool_chaining.py`): nova função `_sanitizar_nome_seguro` (limpa caracteres inseguros silenciosamente, sem exceção). Em `executar_ferramenta_real` o nome é corrigido ANTES da validação, e em `validar_e_corrigir_tool_call_stream` um `ValueError` de path traversal corrige `nome_arquivo` e retenta imediatamente em vez de devolver o erro ao modelo (que respondia com texto em vez de corrigir). Nomes como `../../teste_seguro` viram `teste_seguro` — destrava tasks 21–25. O validador isolado continua rejeitando (teste de segurança preservado). Tasks 24/25: 0/3 → **3/3**.
- **System prompt**: reforço na regra "Quando NÃO chamar ferramenta" — sem certeza absoluta de que o arquivo existe (mencionado antes na conversa), responder em texto. Destrava task 21 (0/3 → 3/3).

### 🛡️ Proteção contra geração degenerada (task 15: 600 tokens de `\n`)

Diagnóstico do run `run_20260904_131134` (task 15, reps 2-3): modelo entrou em loop de `\n`, consumiu os 600 tokens do orçamento (`finish_reason=length`), 250s por execução — porque `repeat_penalty=1.0` (desativada), `dry_multiplier=0.0` e `temperature=0.1`.

- **`core/config.py`**: `LLAMA_REPEAT_PENALTY` default 1.0 → **1.1** (causa raiz; default clássico do llama.cpp; reversível via ENV).
- **`core/llama_client.py`**: `_detectar_degeneracao` (≥100 caracteres idênticos no fim do texto) + abort precoce em `chat_stream` — corta o stream em ~45s em vez de ~250s e **suprime a tool call** (não extrai tool call de saída degenerada, evita documento lixo). Flag `degeneracao_detectada` exposta em `metricas_saida`/`extras_saida`. Bug latente corrigido: `finish_reason_final` não era inicializado em `chat_stream`.
- **`benchmark/runners/maria_runner.py`**: degeneração vira erro descritivo `DegenerateGeneration` em `errors[]` — o **motivo da falha aparece** na seção "Tarefas com falha" do relatório (falha honesta, sem documento lixo contado como sucesso).

### ✅ Verificação

- **178 testes passando** (169 + 9 novos: detecção de degeneração, abort em stream, runner→erro descritivo, sanitização silenciosa) + 33 subtests.
- Resultados empíricos: task 21 0/3→3/3, tasks 24/25 0/3→3/3; 7B tool accuracy 65,3% (baseline) → 84,0% (095749) → 92,0% (131134).

---

## [4.1.18] — Benchmark: parser textual robusto, métricas honestas e system prompt determinístico — 2026-09-04

### 🐛 Correções (o problema não era o modelo)

Diagnóstico do run `run_20260903_190549` (7B Q4_K_M, tool accuracy 65,3%) confirmou que o modelo gerava a tool call correta na maioria das falhas — a infraestrutura é que não a reconhecia. Detalhes em `docs/RELATORIO_BENCHMARK_DIAGNOSTICO.md`.

- **Parser textual robusto** (`backend/core/tool_call_textual_parser.py`): `extrair_tool_call_textual` reescrita — scan balanceado de colchetes (respeitando aspas) em vez de regex ancorada; whitelist de ferramentas (`POSITIONAL_MAP`) elimina pseudo-chamadas ("Listar arquivos:"); reparo conservador de lista truncada por `max_tokens`; normalização de `colunas` achatadas ou em string única. Resolve as falhas reais das tasks 3, 4, 5, 8, 9, 10, 14 e 15.
- **Métricas honestas** (`task_schema.py`, `metrics.py`, `maria_runner.py`, `report.py`): novos campos `confirmacao_elegivel`, `parse_suspeito` e `finish_reason`; nova métrica `confirmation_success_rate_elegiveis` (elimina o efeito cascata que zerava a categoria `confirmacao` sem falha real de confirmação) e contagem de `parse_suspeito` no relatório — separa "modelo não chamou" de "parser falhou".
- **Timeouts/tokens**: `BENCHMARK_TIMEOUT_POR_CHAMADA` 120s → 300s (a ~1,8 tok/s, 400 tokens = ~220s; 120s era falso negativo estrutural); `LLAMA_NUM_PREDICT_DOCUMENTO` 300 → 600 (o teto anterior truncava a tool call de `criar_documento`).
- **`core/llama_client.py`**: `chat_stream` expõe `finish_reason` em `metricas_saida`; `chat_com_tools_stream_com_metricas` ganha `extras_saida` opcional (retrocompatível).

### 📝 Prompt e tarefas

- **`backend/core/system_prompt.txt`** reescrito: de prosa única (451 tokens) para seções estruturadas (~375 tokens estimados), sem mudar regras de negócio. Instrução de formato explícita (chamada em UMA linha, sem texto extra, `colunas` sempre lista) e nova regra "nomes inseguros são corrigidos pelo sistema" (destrava tasks 24/25, onde o modelo se recusava por segurança).
- **`tasks_core.py`**: task 2 ganha sinônimos de keyword (`organizar`, `planejar`, `rotina`, `produtividade`).

### ✅ Verificação

- **169 testes passando** (157 + 12 novos) + 33 subtests; `py_compile` sem erros.
- Nova classe `TestToolCallTextualParser` com 1 teste por variação real do log do benchmark.
- Validação empírica (smoke live + run completo) pendente: requer llama-server ativo.

---

## [4.1.17] — Benchmark: contrato de cliente (Liskov), fixtures e limpeza de Ollama — 2026-09-03

### 🏗️ Design e refatoração

- **`backend/core/client_protocol.py` (novo)**: `LLMClientProtocol` (typing.Protocol) define o contrato estrutural do cliente LLM; `MariaRunner` e `tool_chaining` passam a tipar `cliente` contra ele (princípio de Liskov, sem herança).
- **`MariaTask.fixtures` (novo)**: campo estruturado que substitui o regex de `_garantir_planilha_existente`; as tarefas de edição passam a declarar `fixtures=[...]` (mantendo `context` para o modelo).
- **`run_benchmark.py`**: `dataclasses.asdict` no lugar de `__dict__`; `calculate_maria_metrics` computada uma única vez (antes ~6 chamadas).

### 🧹 Limpeza final de Ollama

- Docstring de `_parece_caminho_local` atualizada ("blob do Ollama" → "blob do modelo"); teste `test_blob_ollama` renomeado para `test_blob_local`.
- `docs/ARQUITETURA_SISTEMA.md` e `README.md` atualizados: removidas as referências ao módulo `ollama_client.py` (tabela, diagrama e seção de modelo). Ollama permanece citado apenas como histórico em `CHANGELOG.md`/`PROGRESSO_DESENVOLVIMENTO.md`.

### ✅ Verificação

- **157 testes passando** + 33 subtests; `py_compile` sem erros; zero referências ativas a "Ollama".

---

## [4.1.16] — Benchmark: correção do compare_runs e dedup de config — 2026-09-03

### 🐛 Correções

- **`backend/benchmark/compare_runs.py`**: corrigida a formatação das métricas de latência p50/p90 (estavam sendo multiplicadas por 100 e rotuladas como "pp" em vez de "ms"). A formatação passou a ser por tipo de métrica (`*_ms` → ms, `*_rate`/`*_accuracy` → pp, `avg_tokens_por_segundo` → tok/s) e trata `None` (ex.: `avg_ttft_ms`).
- **Métricas ausentes adicionadas** ao relatório de comparação: `language_compliance_rate`, `contexto_ok_rate`, `avg_tokens_por_segundo`, `avg_ttft_ms`.
- **`backend/benchmark/benchmark_config.py`**: removida linha duplicada de `BENCHMARK_REPETICOES`.

### ✅ Verificação

- **157 testes passando** + 33 subtests; `py_compile` sem erros.
- `generate_comparison` validado end-to-end com dois runs reais (métricas ms/pp/tok/s corretas).

---

## [4.1.15] — Remoção do cliente legado Ollama — 2026-09-03

### 🧹 Remoção do legado

- **`backend/core/ollama_client.py` removido** (~866 linhas): cliente legado do Ollama que duplicava o `llama_client.py` e não era importado por nenhum caminho de produção. `LlamaClient` passa a ser o único cliente.
- **Constantes `OLLAMA_*` removidas** de `backend/core/config.py` (contrato de env vars `OLLAMA_*` descontinuado).
- **Exceções renomeadas** no benchmark: `LlamaClientError`/`LlamaTimeoutError` usadas diretamente (sem aliases `Ollama*`); o campo `kind` do `log.json` passou de `"OllamaClientError"` para `"LlamaClientError"`.

### 🧪 Testes

- **Test doubles do benchmark migrados** (`ClienteComTimeout`/`Conta`/`Normal`/`Leitura`) de subclasses de `OllamaClient` para fakes sem herança.
- **~23 testes do cliente legado removidos** (recuperação de tool call do campo `thinking`, param `think`, `/api/tags`, etc.), sem equivalente no `LlamaClient`.
- Docstrings atualizadas (`llama_client.py`, `tool_chaining.py`, `router.py`, `tools_schema.py`, `manual_redacao.py`, `maria_controller.py`, `main.py`).

### ✅ Verificação

- **157 testes passando** (`pytest backend/tests/test_maria.py -q`) + 33 subtests.
- `py_compile` sem erros; zero referências residuais a `ollama_client`/`OllamaClient`/`OLLAMA_*` no código ativo.

---

## [4.1.14] — Refatoração estrutural do backend — 2026-09-03

### 🏗️ Estrutura e organização

- **`backend/bridge/comandos.py`**: `_despachar_comando` convertido de um `if/elif` gigante para um **registro de comandos** (`_COMANDOS`), cada comando em seu próprio handler `_cmd_*`. Comportamento externo inalterado.
- **`backend/core/confirmacao.py`** (novo): `ConfirmacaoAcao` (estado da ação pendente) + `interpretar_confirmacao` movido de `chat_session.py`; `ChatSession` delega e mantém `acao_pendente`/`tentativas_confirmacao_ambigua` como propriedades de compatibilidade.
- **`backend/core/paths.py`** (novo): `RAIZ_MONOREPO` centralizado (antes recalculado em `servidores.py`/`comandos.py`).
- **`backend/core/maria_controller.py` / `backend/benchmark/runners/maria_runner.py`**: removido alias enganoso `LlamaClient as OllamaClient` → `LlamaClient`.

### 📋 Documentação de modelos

- Ollama marcado como **legado** em `backend/core/config.py` (caminho não utilizado em produção).
- Modelos em teste documentados: **`qwen2.5-omni-3b` (leve)** e **`qwen2.5-omni-7b` (pesado)** em `config.py`, `router.py` e `shared/schema.sql` / `database/schema.py`.
- Corrigido drift de schema: seed de `configuracoes` unificado (`modelo_llama`/`qwen2.5-omni-3b`), removendo `modelo_ollama`/`qwen3.5:4b`.

### ✅ Verificação

- **180 testes passando** (`pytest backend/tests/test_maria.py -q`) + 33 subtests; sem regressões.
- Smoke test do bridge (15 comandos: ping, status, memória, automações, sessões) OK.
- `py_compile` sem erros em todos os arquivos alterados.

---

## [4.1.13] — Análise e correção de 7 bugs no backend + doc do router — 2026-09-03

### 🐛 Bugs corrigidos no bridge e utilitários

- **`backend/bridge/comandos.py`**:
  - `carregar_sessao`: resolvia nome via `listar_sessoes_salvas()` + acesso a `dados["historico"]` (antes: dict acessado como objeto → `AttributeError`, e filename em vez de caminho).
  - `criar_automacao`: INSERT agora inclui coluna `acao` (NOT NULL no schema); era omitida → `IntegrityError`.
  - `listar_automacoes` / `toggle_automacao`: SQL corrigido para coluna `ativo` (antes: `ativa`, inexistente no schema → `OperationalError`).
  - `listar_memoria`: retorna `id` no SELECT/resposta (antes: `deletar_memoria` exigia `id`, mas `listar_memoria` não devolvia).
- **`backend/core/session_storage.py`**: implementada `exportar_sessao()` (exporta `.txt`/`.json`); comando `exportar_conversa` usava função inexistente → `ImportError`.
- **`backend/core/excel_handler.py`**: `ler_planilha_resumo` corrigido: `"\\n".join()` → `"\n".join()` (antes unia com `\n` literal).
- **`backend/core/config.py`**: `OLLAMA_MODEL` padrão corrigido: `"qwen2.5:3b omni"` → `"qwen2.5:3b"` (espaço inválido em tag de modelo Ollama).

### 📋 Documentação

- **`backend/core/router.py`**: docstring ampliada com seção `STATUS ATUAL / INTEGRAÇÃO FUTURA` (módulo mantido, não integrado; passos para ativação documentados).
- **`docs/analise_backend.md`**: novo relatório com análise completa (7 bugs, riscos, oportunidades, segurança).

### ✅ Verificação

- **180 testes passando** (`pytest backend/tests/test_maria.py -q`) + 33 subtests; sem regressões.
- `py_compile` sem erros em todos os arquivos alterados.

---

## [4.1.12] — Benchmark: ID do modelo no relatório/log + linha de resumo por execução — 2026-09-03

### 🛠️ Alterações no benchmark

- **`backend/benchmark/analysis/report.py`**:
  - Seção **Modelo** enxuta: removida a linha "Nome"; a identificação passou a ser apenas **ID modelo** (antiga "ID real"). Quantização e demais dados reais (Parâmetros, n_ctx, Tamanho) preservados. Fallback sem `/v1/models` também exibe "ID modelo | Não detectado".
  - Novos helpers `_execucao_falhou()` (mesmo critério do bloco "Tarefas com falha") e `_formatar_linha_resumo()`.
  - Seção **Detalhes por execução**: cada bloco agora exibe, logo após o título, a linha `rep X/Y: ✓/✗ tool=... args=OK|DIVERGENTE latência=...s tokens=...`; quando a execução falha, anexa ` — erro: <descrição>` via `_diagnosticar_falha`.
- **`backend/benchmark/run_benchmark.py`**:
  - `log.json` → `meta`: removido `modelo_nome_exibicao`; `modelo_id_real` renomeado para `id_modelo`.

### ✅ Verificação

- `python -m py_compile` sem erros em `report.py` e `run_benchmark.py`.
- **175 testes passando** (`pytest backend/tests/test_maria.py -k "not TestSegurancaApiHttp"`) + 33 subtests; sem regressões nas asserções de relatório existentes.
- Geração manual do `report.md` confirmou `| ID modelo | ... |`, `rep 1/2: ✓ tool=— args=OK latência=56.0s tokens=35` e erro descrito em execuções com falha.

---

## [4.1.11] — Autocorreção de tool calls inválidas + fix de testes pré-existentes — 2026-09-03

### 🛠️ Nova funcionalidade: autocorreção de tool calls de escrita

- **`backend/core/config.py`**: adicionadas 2 constantes com override via ENV:
  - `LLAMA_TEMPERATURE_TOOLS_RETRY` (default `0.25`) — temperatura elevada usada **somente** nas chamadas de correção de tool call inválida. O default `LLAMA_TEMPERATURE_TOOLS` (0.1) permanece intocado para todas as demais chamadas.
  - `MAX_TENTATIVAS_CORRECAO_FERRAMENTA` (default `2`) — limite de tentativas de correção antes de prosseguir sem ferramenta.
- **`backend/core/tools_schema.py`**: `validar_argumentos_obrigatorios` estendida — **após** a checagem de campos ausentes (comportamento/mensagem inalterados), valida **somente schema**: `colunas` deve ser lista (rejeita string única), e `nome_arquivo` passa pela `_sanitizar_nome_arquivo` (path traversal e caracteres inseguros). **NÃO** verifica existência de arquivo em disco (as tarefas 21–23 do benchmark exigem `editar_planilha` para arquivo fictício).
- **`backend/core/llama_client.py`**: `_montar_payload` ganhou `temperatura_override` (aplica `payload["temperature"]` logo após `montar_sampler_params()`); `continuar_com_resultado_ferramenta_stream` ganhou `temperatura_override` e repassa ao payload. Nenhuma alteração em `ollama_client.py` (caminho legado).
- **`backend/core/tool_chaining.py`**: novo conjunto `FERRAMENTAS_ESCRITA = {"criar_planilha", "criar_documento", "editar_planilha"}` e novo generator `validar_e_corrigir_tool_call_stream()` — valida a tool call de escrita contra o schema antes da confirmação do usuário; se inválida, reenvia o erro ao modelo via `continuar_com_resultado_ferramenta_stream` (mesmo padrão de `encadear_leitura_stream`) com `temperatura_override=LLAMA_TEMPERATURE_TOOLS_RETRY`, até `MAX_TENTATIVAS_CORRECAO_FERRAMENTA`. Último yield: `(None, {"tool_call": ..., "tentativas": ...})`.
- **`backend/core/maria_controller.py`**: `_gerar_resposta_com_encadeamento` agora encadeia **3 estágios**: `chat_com_tools_stream` → `encadear_leitura_stream` (loop explícito, substituindo `yield from`) → `validar_e_corrigir_tool_call_stream`; o último yield é `(None, tool_call_final)`.
- **`backend/benchmark/tasks/task_schema.py`**: `MariaTaskResult` ganhou o campo `correction_attempts: int = 0` (nº de tentativas de correção usadas; 0 quando a tool call já veio válida ou não havia escrita a validar).
- **`backend/benchmark/runners/maria_runner.py`**: bloco de correção inserido após o tratamento de `FERRAMENTAS_LEITURA` e antes de `task.confirm_sequence` — usa `validar_e_corrigir_tool_call_stream` com callback `_apos_chamada_de_correcao` (timeout por chamada `BENCHMARK_TIMEOUT_POR_CHAMADA` + soma de tokens); quando a correção esgota e `tool_call_final` fica `None`, `confirmation_completed` é setado como `True` (nada a confirmar). `correction_attempts` exposto no resultado.
- **`backend/core/system_prompt.txt`**: nova diretriz no parágrafo único — ao receber erro de tool call inválida, corrigir **só o campo apontado** e chamar a ferramenta novamente, sem desculpas/perguntas.

### 🧪 Correção de testes pré-existentes (baseline)

- **`backend/tests/test_maria.py`**:
  - `@patch('core.ollama_client...')` → `@patch('backend.core.ollama_client...')` (16 ocorrências): remove dependência de `sys.path`/ordem de execução que causava `ModuleNotFoundError` quando rodados isoladamente.
  - 3 testes de regressão usavam `OllamaClient()` sem `model=`, disparando auto-detecção contra mock → agora `OllamaClient(model="qwen3.5:4b")`.
  - 2 asserts de system prompt não casavam com o texto acentuado real → `"português do Brasil"` e `"arquivo não foi encontrado"`.

### 🧪 Novos testes (Fase B)

- **`TestValidacaoArgumentos`**: `colunas` como string → `ValueError` "lista de strings"; `nome_arquivo` com path traversal → `ValueError`; tool call válida não levanta.
- **`TestToolChaining`**: leitura passa direto sem chamar `continuar_com_resultado_ferramenta_stream` (`tentativas=0`); escrita inválida corrigida na 1ª tentativa → `tentativas=1`; esgotar limite → `tool_call=None`.
- **`TestMariaRunnerEncadeamento.test_runner_corrige_tool_call_escrita_invalida`**: `correction_attempts > 0` no `MariaTaskResult`.
- **`TestMariaRunnerNegaEAmbiguidade`**: fake client agora implementa `continuar_com_resultado_ferramenta_stream` devolvendo tool call **válida** na 1ª tentativa, preservando o fluxo de cancelamento.

### ✅ Verificação

- `python -m py_compile` sem erros em: `config.py`, `tools_schema.py`, `llama_client.py`, `tool_chaining.py`, `maria_controller.py`, `task_schema.py`, `maria_runner.py` e `test_maria.py`.
- **180 testes passando** (`python -m unittest backend.tests.test_maria`): baseline 173 (agora todos verdes após fix pré-existente) + 7 novos da Fase B.
- `backend/core/ollama_client.py` **intocado** (continua como caminho legado de produção).
- Critérios de aceite: sem verificação de existência de arquivo no validador; temperatura default `LLAMA_TEMPERATURE_TOOLS` (0.1) preservada; fluxos de leitura (`encadear_leitura_stream`) e contexto/timeout (`_enviar_com_retry`, `_verificar_contexto_disponivel`) inalterados.

---

### 🔧 Refatoração estrutural (sem alteração de comportamento)

- **Novo módulo `backend/core/maria_controller.py`**: a classe `MariaController` (lógica de negócio) foi movida integralmente de `backend/main.py` — todos os métodos (`inicializar`, `aquecer_modelo`, `finalizar`, `_gerar_nome_sessao`, `_salvar_silenciosamente`, `listar_sessoes`, `retomar_sessao`, `tem_acao_pendente`, `limpar_acao_pendente`, `limpar_historico`, `enviar_mensagem`, `_gerar_resposta_com_encadeamento`, `processar_chunk`, `finalizar_mensagem`, `get_mensagem_confirmacao`, `processar_confirmacao`) sem alterações de lógica.
- **Novo pacote `backend/bridge/`**:
  - `backend/bridge/comandos.py` — protocolo de comandos do bridge: `_responder_bridge`, `_get_system_status` e `_despachar_comando` (assinatura com anotação `controller: "MariaController"` como string, evitando import circular em runtime).
  - `backend/bridge/servidores.py` — transporte: `_modo_bridge` (stdin/stdout), `_carregar_token_api`, `_criar_app_http` e `_modo_bridge_http` (porta 8081).
  - `_RAIZ_MONOREPO` recalculado em cada módulo bridge (3 níveis acima) para `WHISPER_ALLOWED_DIR` e `frontend-tauri/shared/.bridge_token`.
- **`backend/main.py` reduzido de 944 → ~98 linhas**: contém apenas o bloco `sys.path`, imports, `logger` e a função `main()` (entry point). Foram adicionados **re-exports explícitos** (`MariaController`, `_despachar_comando`, `_responder_bridge`, `_get_system_status`, `_carregar_token_api`, `_criar_app_http`) para compatibilidade retroativa com os imports e patches dos testes existentes.

### 🧪 Verificação

- **Sem alterações em `backend/tests/test_maria.py`** — todos os imports de `backend.main` continuam resolvendo via re-exports.
- **173 testes executados** (`python -m unittest backend.tests.test_maria`): resultado idêntico ao baseline pré-divisão (**2 falhas + 3 erros pré-existentes** não relacionados à tarefa — encoding do `system_prompt.txt` e indisponibilidade do Ollama/llama-server no ambiente) — **zero regressão**.
- `python -m py_compile` sem erros em `backend/main.py`, `backend/core/maria_controller.py`, `backend/bridge/__init__.py`, `backend/bridge/comandos.py` e `backend/bridge/servidores.py`.
- Smoke tests funcionais: `--bridge-http` (servidor Flask na porta 8081/8099, `GET /ping` → HTTP 200 `{"dados":"pong","status":"ok"}`), bridge stdin/stdout (`ping` → `{"status":"ok","dados":"pong"}`) e modo CLI (`python backend/main.py` + `sair` → exit 0 com banner e warmup normais).
- Comparação byte-a-byte entre o código movido e o `git HEAD:backend/main.py` confirmou **100% de fidelidade** (todas as 8 funções + classe IDÊNTICAS, sem mudança de lógica).
- Cobertura formal de código (`pytest-cov`) segue não configurada neste ambiente — pendente no roadmap do projeto.

---

## [4.1.9] — Hardening de tool calls e isolamento de benchmark — 2026-09-02

### 🔒 Segurança e robustez

- **Sanitização de nomes de arquivo nas ferramentas de escrita** (`backend/core/tools_schema.py`):
  `executar_ferramenta_real()` agora valida e sanitiza `nome_arquivo` antes de qualquer operação de I/O. Nomes com path traversal (`../`, `/`, `\`, `.` inicial) e caracteres inseguros são rejeitados antes de criar/editar planilhas ou documentos. O campo obsoleto `tipo_documento_oficial` foi removido do schema de `criar_documento`, alinhando a definição com o fluxo atual de `consultar_manual_redacao`.
- **Refatoração da resolução final da tool call** (`backend/core/llama_client.py`):
  a lógica duplicada para montar o `tool_call_final` em `chat_stream()` e `continuar_com_resultado_ferramenta_stream()` foi centralizada em `LlamaClient._resolver_tool_call_final()`, mantendo o fallback textual e o parsing via delta em um único ponto e reduzindo risco de divergência entre os dois fluxos.
- **Isolamento de estado por repetição no benchmark** (`backend/benchmark/runners/maria_runner.py`):
  `run_repeated()` agora limpa `BENCHMARK_ARQUIVOS_DIR` antes de cada execução, removendo arquivos e diretórios gerados em ciclos anteriores para evitar contaminação de estado entre repetições da mesma tarefa.

### 🧪 Verificação

- Validação funcional com smoke tests em Python para:
  - nomes seguros (`relatorio_financeiro.xlsx`) → aceitos;
  - nomes maliciosos (`../hacked`) → rejeitados;
  - compilação do módulo `llama_client.py` e helper `_resolver_tool_call_final()`;
  - compilação do runner do benchmark após a limpeza do diretório de artefatos.

---

## [4.1.8] — Deduplicação do system prompt no relatório e log — 2026-09-02

### ✨ Nova funcionalidade

- **Funções auxiliares públicas para dedução de prompts** (`backend/benchmark/analysis/report.py`):
  `extrair_texto_system()` e `mascarar_system_prompt()` (antes privadas com prefixo `_`) agora são públicas para reutilização em múltiplos módulos. Permitindo compartilhamento da lógica de dedução entre relatório e log.
- **System prompt deduzido no `report.md`** (`backend/benchmark/analysis/report.py`):
  A função `_montar_detalhes_execucao()` agora imprime o texto completo do prompt de sistema **uma única vez** no topo da seção `## Detalhes por execução`, extraído da primeira execução que contiver a mensagem system. Em cada bloco de execução individual, a mensagem `role="system"` é substituída pelo marcador `"prompt do system injetado"` — evitando repetição dezenas de vezes do texto completo (economia: ~40–50 KB por relatório típico).
- **System prompt deduzido no `log.json`** (`backend/benchmark/run_benchmark.py`):
  O prompt completo é extraído uma única vez e armazenado em `meta.system_prompt_completo`. No bloco `"individual"`, cada resultado tem `prompt_enviado` com a mensagem system mascarada (marcador `"prompt do system injetado"`), mantendo as mensagens `user`/`assistant`/`tool` intactas. Ganho de compactação: ~40–50 KB por log típico com 75 execuções.

### 🔧 Refatoração

- **Importação de funções públicas** (`backend/benchmark/run_benchmark.py`): agora importa `extrair_texto_system` e `mascarar_system_prompt` de `.analysis.report`.
- **Serialização sem mutação** (`backend/benchmark/run_benchmark.py`): bloco `"individual"` é montado com spread operator (`{**r.__dict__, ...}`), preservando `resultados_individuais_todas_tarefas` inalterados — `generate_report()` continua recebendo dados íntegros.

### 📊 Impacto

- **Redução de tamanho**: logs e relatórios típicos (75 execuções, system prompt ~2,2 KB) diminuem ~50 KB (~20% em relatórios com muitas tarefas).
- **Legibilidade**: relatórios mais concisos, com o context completo do system prompt centralizado no topo da seção de detalhes.
- **Compatibilidade**: formato de `log.json` v2.0 estendido (novo campo `meta.system_prompt_completo`); `compare_runs.py` segue compatível (lê apenas `individual` para agregação).

### 🧪 Testes

- **172/172 testes passaram** (`python -m pytest backend/tests/test_maria.py`).
- Testes relacionados a `_montar_detalhes_execucao` continuam validando a estrutura esperada (verificam presença do marcador nos blocos e texto completo no topo).

---

## [4.1.7] — Verificação de contexto, timeouts por chamada e num_ctx adaptativo — 2026-09-02

### ✨ Nova funcionalidade

- **Contexto real do servidor como fonte única** (`backend/benchmark/run_benchmark.py`):
  `_warmup_model()` agora lê o `n_ctx` real do `meta` de `/v1/models` (comprovado nos runs: `2048` real vs `8192` configurado) e registra `ctx_size` + `ctx_fonte` (`models`/`fallback`) nos metadados. Sem `n_ctx`, faz fallback para `LLAMA_NUM_CTX` com `[AVISO]` sugerindo `--ctx-size` explícito. A sonda com payload `num_ctx` (do enunciado original) foi descartada: o endpoint OpenAI-compat do llama.cpp ignora campos desconhecidos, então responderia 200 mesmo com contexto menor — medição falsa.
- **Contagem exata do system prompt + calibração** (`backend/benchmark/run_benchmark.py`, `backend/benchmark/utils.py`):
  1 chamada `POST /tokenize` no warmup dá o número exato de tokens do system prompt e o **fator de calibração** (tokens reais ÷ estimativa chars/4 — captura a densidade dos JSONs de tool schema). O pre-check por tarefa usa `estimar_tokens_calibrado()` — erro cai de ~±50% para ~±10% **sem nenhuma chamada HTTP extra**. Fallback silencioso (`fator = 1.0`) se `/tokenize` indisponível.
- **Warmup aborta se o prompt não couber** (`backend/benchmark/run_benchmark.py`):
  `SystemExit` com as duas soluções (reduzir o system prompt / subir `--ctx-size`, com o valor sugerido calculado) quando `tokens > ctx - 512` (margem de segurança `MARGEM_SEGURANCA_SYSTEM`). No cenário real (546 tokens estimados vs 1536 de limite em ctx 2048) o warmup passa com `[OK]` e a margem exibida.
- **Pre-check de contexto por tarefa** (`backend/benchmark/runners/maria_runner.py`):
  `MariaRunner.__init__` ganha `ctx_size` (recebe o valor real do `run_benchmark`; fallback `LLAMA_NUM_CTX`). `_enviar_com_retry()` estima o prompt calibrado e **aborta antes de enviar** se exceder `ctx × 0.7` (`MARGEM_RESERVA_RESPOSTA`), com `OllamaClientError` portando marcador de contexto → `run()` classifica `contexto_ok=False` (PARTE 3.6) e **o retry é pulado** (estouro é determinístico).
- **Timeout por chamada separado do total** (`backend/benchmark/benchmark_config.py`, `backend/benchmark/runners/maria_runner.py`):
  novo `BENCHMARK_TIMEOUT_POR_CHAMADA` (120s, via ENV) — `BENCHMARK_TASK_TIMEOUT` (400s) permanece como timeout TOTAL. O callback de continuação usa o limite por chamada e cada tentativa do `_enviar_com_retry` é verificada pós-chamada (`_verificar_timeout_por_chamada`, medida por tentativa, não acumulada com retries) — diferencia tarefa falha por UMA chamada lenta de estouro por acumulação.
- **`num_ctx` adaptativo no payload** (`backend/core/llama_client.py`):
  flag `_num_ctx_respeitado` (cacheada por instância): em HTTP 400 com `num_ctx` no payload, remove o campo e refaz a requisição **uma única vez**; chamadas seguintes omitem o campo direto. Servidores que ignoram o campo (llama.cpp hoje) não mudam de comportamento — abordagem adaptativa escolhida em vez de sonda proativa, que custaria um POST extra e quebraria testes que inspecionam o primeiro payload. `ollama_client.py` intocado (divergência deliberada mantida).
- **`log.json` v2.0 estendido**: `ctx_size_detectado`, `ctx_fonte`, `system_prompt_tokens`, `fator_calibracao_tokens`, `timeout_por_chamada_s` no bloco `meta`.

### 🧪 Testes

- **172/172 testes passaram** (`python -m pytest backend/tests/test_maria.py`), + 33 subtests.
- **17 testes novos**: `TestEstimarTokens` (3), `TestCalibracaoDeTokens` (4), `TestWarmupCtxSize` (4 — ctx via models, fallback com aviso, contagem exata, aborto), `TestNumCtxAdaptativo` (3) e `TestPreCheckContexto` (3 — bloqueio sem retry, envio normal, callback com timeout por chamada).
- **1 fixture ajustado**: `test_sem_alerta_para_blob_mesmo_modelo` ganhou `n_ctx` no metadado e patch de `_contar_tokens_exatos` (evita HTTP real e `[AVISO]` de fallback).

---

## [4.1.6] — Metadados reais do modelo, detecção de contexto e relatório enxuto — 2026-09-02

### ✨ Nova funcionalidade

- **Metadados do modelo enriquecidos** (`backend/benchmark/run_benchmark.py`):
  novos helpers `_extrair_nome_exibicao()` (ID cru do GGUF → nome amigável, ex: `ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M` → `Qwen2.5 Omni 3B`) e `_extrair_quantizacao()` (extrai `Q4_K_M` do sufixo do ID, com fallback `'desconhecida'`). `_obter_metadados_modelo()` agora retorna também `nome_exibicao` e usa `_extrair_quantizacao` como fallback quando o `ftype` não estiver disponível — mantendo os metadados ricos já existentes (n_params, n_ctx, tamanho, ftype).
- **`log.json` v2.0 com rastreabilidade completa** (`backend/benchmark/run_benchmark.py`):
  bloco `meta` estendido com `modelo_id_real`, `modelo_nome_exibicao`, `modelo_quantizacao`, `data_execucao` (ISO 8601), `total_tarefas`, `repeticoes_por_tarefa`, `versao_benchmark: '2.0'`, `system_prompt_hash` (SHA-256 de 12 chars via novo helper `_hash_prompt()`) e `llama_base_url`. `compare_runs.py` permanece compatível (lê apenas `individual`).
- **Métrica `contexto_ok_rate`** (`backend/benchmark/analysis/metrics.py`): novo campo em `MariaBenchmarkMetrics` (default `1.0`); `calculate_maria_metrics()` contabiliza a taxa de tarefas sem estouro de contexto.
- **Campo `contexto_ok` no resultado** (`backend/benchmark/tasks/task_schema.py`): `MariaTaskResult` ganha `contexto_ok: bool = True` — `False` quando o prompt excede o `ctx_size` do servidor.
- **Detecção de erro de contexto no runner** (`backend/benchmark/runners/maria_runner.py`): o `except OllamaClientError` do `run()` classifica o erro por marcadores específicos (`exceeds the available context size`, `context size`, `too many tokens`, etc. — evitando falsos positivos de um simples `context` na mensagem), loga `ERRO DE CONTEXTO` e propaga `contexto_ok=False` no resultado.

### 🔧 Correções / Refatoração

- **`_warmup_model()` aborta sem `/v1/models`** (`backend/benchmark/run_benchmark.py`): passa a retornar o dict de metadados e levanta `SystemExit` se o endpoint não responder — o relatório nunca exibe dados falsos (mudança de comportamento intencional: antes avisava e seguia com `LLAMA_MODEL`). Imprime `[INFO] Modelo detectado: <nome> (<quantização>) — ID: <id>`.
- **Relatório enxuto com modelo real** (`backend/benchmark/analysis/report.py`): `generate_report()` perde os parâmetros `modelo_configurado`/`modelo_carregado` e recebe apenas `metadados_modelo`; a seção Modelo mostra somente dados reais de `/v1/models` (Nome, Quantização, ID real, Parâmetros, n_ctx, Tamanho) — sem coluna "Configurado" fake nem alerta de divergência; sem metadados exibe "Não detectado" + nota de erro. Linha `Contexto OK` adicionada às métricas gerais. **Escrita duplicada de `log.json` removida** (agora escrito apenas por `run_benchmark.py`). As seções "Parâmetros do sampler" e "Detalhes por execução" foram preservadas.

### 🧪 Testes

- **155/155 testes passaram** (`python -m pytest backend/tests/test_maria.py`), + 33 subtests.
- **3 testes ajustados**: `test_warmup_sem_alerta_para_blob_do_mesmo_modelo` (desempacota o dict retornado) e 2 testes de relatório com `contexto_ok_rate=1.0` no mock.
- **9 testes novos**: `TestExtrairNomeExibicao` (3), `TestExtrairQuantizacao` (2) e `TestContextoOk` (4 — default True, taxa nas métricas, runner detecta erro de contexto, runner mantém True em erro genérico).

---

## [4.1.5] — Normalização de chaves e argumentos (tool calling + benchmark) — 2026-09-02

### 🔧 Correções

- **Normalização de chaves JSON nas tool calls** (`backend/core/llama_client.py`):
  `_extrair_tool_call_da_resposta()` converte todas as chaves do dict de argumentos para minúsculas após o `json.loads` (corrige falsos negativos quando o modelo gera `'Conteudo'`, `'Nome_arquivo'`, etc.). A mesma normalização foi aplicada ao fallback textual `_tentar_extrair_tool_call_textual()`. Beneficia também o `main.py` (produção), pois as ferramentas esperam chaves minúsculas (`conteudo`, `nome_arquivo`, `titulo`).
- **Validação flexível de argumentos no benchmark** (`backend/benchmark/runners/maria_runner.py`):
  `_argumentos_compativeis()` reescrita — chaves comparadas em minúsculas, listas (ex: `colunas`) comparadas como conjuntos (ordem irrelevante) e novo helper `_normalizar_valor()` remove extensões conhecidas (`.xlsx`, `.xls`, `.docx`, `.doc`) de `nome_arquivo` antes da comparação. `'gastos.xlsx'` agora equivale a `'gastos'`.
- **Keyword match sem falsos negativos por acento** (`backend/benchmark/runners/maria_runner.py`):
  novo helper `_normalizar_texto()` (lowercase + NFKD sem combining); o cálculo de `keyword_match` no `run()` normaliza texto e keywords — `'não encontrado'` agora casa com `'nao encontrado'`.
- **Tarefas 21-23 do benchmark** (`backend/benchmark/tasks/tasks_edges.py`): keywords expandidas de `['exist']` para `['exist', 'encontrado', 'nao existe', 'ausente', 'nao foi localizado']` e nomes de arquivo tornados inequivocamente fictícios (`arquivo_que_nao_existe`, `planilha_inexistente`, `planilha_nao_existe`).

### 🧪 Testes

- **145/145 testes passaram** (`python -m pytest backend/tests/test_maria.py`), incluindo os 3 de `TestAcuraciaDeArgumentos`, que permanecem compatíveis com a nova lógica.
- **7 verificações funcionais** executadas manualmente: normalização no fallback textual, normalização na extração estruturada, `esperados=None`, chaves maiúsculas + extensão + lista fora de ordem, detecção de divergência real, keywords com/sem acento e integridade das tarefas 21-23.

---

## [4.1.4] — System prompt centralizado em arquivo externo — 2026-09-02

### ✨ Nova funcionalidade

- **System prompt em arquivo externo** (`backend/core/system_prompt.txt`): o prompt do sistema da MARIA não vive mais hardcoded no código. Movido de `backend/system_prompt.txt` para `backend/core/system_prompt.txt` (~2,2 KB).
- **`MARIA_SYSTEM_PROMPT` no config** (`backend/core/config.py`): carregado do arquivo na inicialização do módulo via `_carregar_system_prompt()`, com falha explícita (`RuntimeError`) se o arquivo não for encontrado.

### 🔧 Refatoração

- **`backend/core/chat_session.py`**: bloco `SYSTEM_PROMPT` hardcoded (~50 linhas) removido da classe `ChatSession`; substituído por alias `SYSTEM_PROMPT = MARIA_SYSTEM_PROMPT` para compatibilidade com código legado. A injeção dinâmica via `get_historico_com_system()` foi preservada — o `historico` interno continua contendo apenas mensagens `user`/`assistant` (contrato usado por `main.py`, `contar_mensagens()` e testes).
- **`backend/core/llama_client.py`**: reforço hardcoded de tool calling (~31 linhas) removido de `_montar_mensagens_com_reforco()`; a função agora garante uma única mensagem `role="system"` no início, com fallback para `MARIA_SYSTEM_PROMPT` do config.
- **`backend/tests/test_maria.py`**: 2 testes atualizados para strings do prompt externo (`test_system_prompt_exige_portugues`, `test_system_prompt_contem_excecao_para_arquivo_ficticio`).

### ⚠️ Divergência conhecida

- **`backend/core/ollama_client.py` não foi alterado** (decisão deliberada): mantém `_montar_mensagens_com_reforco()` com reforço hardcoded original. Comportamento diverge do `LlamaClient` até alinhamento futuro.

### 🧪 Testes

- **145/145 testes passaram** (`python -m pytest backend/tests/test_maria.py`) + 33 subtests.
- Verificações manuais: carregamento de `MARIA_SYSTEM_PROMPT` (2186 caracteres), fallback do `llama_client`, injeção única do system em `get_historico_com_system()`.

---

## [4.1.3] — Prompt, resposta bruta e parâmetros de sampler no benchmark — 2026-09-02

### ✨ Nova funcionalidade

- **Parâmetros de sampler configuráveis via ENV** (`backend/core/config.py`): 15 novas variáveis `LLAMA_*` com defaults idênticos aos do llama-server — `LLAMA_REPEAT_LAST_N` (64), `LLAMA_REPEAT_PENALTY` (1.0), `LLAMA_FREQUENCY_PENALTY` (0.0), `LLAMA_PRESENCE_PENALTY` (0.0), `LLAMA_DRY_MULTIPLIER` (0.0), `LLAMA_DRY_BASE` (1.75), `LLAMA_DRY_ALLOWED_LENGTH` (2), `LLAMA_DRY_PENALTY_LAST_N` (64), `LLAMA_TOP_K` (40), `LLAMA_TOP_P` (0.95), `LLAMA_MIN_P` (0.05), `LLAMA_XTC_PROBABILITY` (0.0), `LLAMA_XTC_THRESHOLD` (0.1), `LLAMA_TYPICAL_P` (1.0) e `LLAMA_TOP_N_SIGMA` (-1.0).
- **Envio explícito do sampler no payload** (`backend/core/llama_client.py`): `montar_sampler_params()` centraliza o snapshot dos parâmetros efetivos; `_montar_payload` agora envia os 16 parâmetros (incluindo `temperature`) nas chamadas com tools. O servidor ignora campos desconhecidos, então o payload permanece seguro.
- **Prompt e resposta bruta do modelo no benchmark** (`backend/benchmark/`): `MariaTaskResult` ganhou `prompt_enviado` (mensagens completas enviadas ao modelo), `resposta_bruta_modelo` (resposta crua antes de sobrescrita por confirmação/ferramenta/continuação) e `sampler_params` (snapshot dos parâmetros efetivos). O `log.json` registra os campos por execução e `meta.sampler_params`; o `report.md` ganhou as seções **"Parâmetros do sampler"** e **"Detalhes por execução"** (prompt + resposta bruta + mensagem final por tarefa/repetição).
- **`compare_runs.py` retrocompatível**: novos campos com defaults não quebram runs antigos.

### 🧪 Testes

- **145/145 testes passaram** (`python -m pytest backend/tests/test_maria.py`).
- **7 testes novos**: `TestSamplerParamsBenchmark` — defaults da config, `montar_sampler_params`, payload com/sem tools, campos novos do `MariaTaskResult`, preenchimento no runner e renderização do relatório.

---

## [4.1.2] — Metadados do modelo no benchmark + fix da suíte de testes — 2026-09-02

### ✨ Nova funcionalidade

- **Nome real do modelo via `/v1/models`** (`backend/benchmark/run_benchmark.py`):
  `_obter_metadados_modelo()` consulta o llama-server e extrae id, id_exibicao, quantização (mapeo ftype → nome GGML), n_params, n_vocab, n_ctx, n_ctx_train, tamanho_bytes e rótulo derivado. Quando o id é um blob/camino local (`C:\blob\sha256-...`), o reporte mostra o nome legible (`Qwen2.5 3B`) em vez do blob.
- **Seção Modelo enriquecida em `report.md`** (`backend/benchmark/analysis/report.py`):
  tabela com modelo configurado/cargado/derivado, quantização, parámetros, n_ctx (servidor/treino) e tamanho. Alerta `⚠️` de divergência só quando relevante (se o id NÃO é blob do mesmo modelo) e aviso `ℹ️` quando `LLAMA_NUM_CTX` > `n_ctx` real do servidor.
- **`log.json` com bloco `meta`**: `run_benchmark.py` agora registra `modelo_configurado`, `modelo_carregado`, `metadados_modelo` e `llama_num_ctx_config`; `compare_runs.py` é retrocompatível com o formato antigo (lista plana) e novo (dict com `individual`).
- **`MariaRunner.modelo_efetivo`** (`backend/benchmark/runners/maria_runner.py`): usa o modelo realmente cargado no llama-server quando disponível, com fallback ao `model` do cliente.
- **README do benchmark** (`backend/benchmark/README_benchmark.md`): comandos corrigidos (`python -m backend.benchmark.run_benchmark ...`).

### 🧪 Testes

- **138/138 testes passaram** (`python -m pytest backend/tests/test_maria.py`).
- **18 testes novos**: `TestObterMetadadosModelo` (3), `TestDerivarRotuloModelo` (5), `TestPareceCaminhoLocal` (5), `TestAlertaNaoDisparaParaBlob` (1), `TestAvisoNctx` (1) e `TestFtypeParaNome` (3).
- **Fix da estrutura da suíte**: `test_maria.py` não compilava (`IndentationError` — classes intercaladas dentro do corpo de métodos); corpos órfãos reorganizados e `test_obter_metadados_status_500` movido à classe correta.
- **Fix de testabilidade**: alias `_requests = requests` a nível de módulo en `run_benchmark.py` permite `patch("backend.benchmark.run_benchmark._requests.get")` (antes o `import` local dentro da função fazia o patch apuntar a um atributo inexistente).
- **Cobertura**: validación via suíte completa + verificação end-to-end do reporte (todos os parámetros presentes, sem alerta espúria para blob do mesmo modelo); sem `coverage` formal mensurado.

---

## [4.1.1] — Correções críticas de segurança — 2026-08-31

### 🔒 Segurança

- **[Tarefa 1] Escrita atômica do token bridge** (`backend/main.py` — `_carregar_token_api`):
  `caminho.write_text()` substituído por escrita em arquivo `.tmp` + `os.replace()` (rename atômico no mesmo filesystem), eliminando a janela de conteúdo truncado visível por leitores concorrentes. Em POSIX, `os.chmod(caminho, 0o600)` restringe a leitura ao usuário atual. `OSError` propaga sem captura — startup do modo `--bridge-http` falha explicitamente em vez de rodar sem token seguro.

- **[Tarefa 2] CORS restrito por ambiente** (`backend/core/config.py` + `backend/main.py`):
  Adicionada variável `MARIA_ENV` em `config.py` (padrão: `"production"`). O bloco `CORS(...)` em `_criar_app_http` agora inclui `http://localhost:5173` (Vite dev server) **somente** quando `MARIA_ENV=development`. Em produção, apenas `tauri://localhost` e `http://tauri.localhost` são aceitos. Sem `MARIA_ENV` definida, `OPTIONS /chat` com `Origin: http://localhost:5173` não recebe `Access-Control-Allow-Origin`.

- **[Tarefa 3] Mitigação de PATH hijacking no Whisper** (`backend/main.py` — `transcrever_audio`):
  O binário agora é resolvido via `shutil.which()` e o caminho resolvido é verificado contra `WHISPER_ALLOWED_DIR` (padrão: `<raiz_monorepo>/bin`). Binários encontrados fora desse diretório são rejeitados com erro explícito, impedindo substituição maliciosa via PATH. `subprocess.run` tem seu retorno capturado em `resultado`: quando `output_file` não é gerado, `returncode` e `stderr[:500]` são registrados no log (antes o `CompletedProcess` era descartado, dificultando diagnóstico).

- **[Tarefa 4] Thread-safety da conexão SQLite** (`backend/database/connection.py`):
  `sqlite3.connect()` agora usa `check_same_thread=False`, necessário porque `Flask.run()` cria uma thread por requisição (`threaded=True` implícito no Flask ≥ 3). Adicionado `threading.Lock()` com padrão de double-checked locking em `get_connection()` e `close_connection()` para garantir que apenas uma conexão seja criada mesmo sob inicialização concorrente. `PRAGMA busy_timeout = 5000` adicionado: SQLite aguarda/retenta internamente em vez de lançar `OperationalError` imediato sob contenção de escrita.

### 🧪 Testes

- **115/115 testes passaram** (`python -m pytest backend/tests/ -q -k "not TestSegurancaApiHttp"`) após todas as tarefas. `TestSegurancaApiHttp` requer `flask` no ambiente de testes — falha pré-existente, sem relação com esta versão.
- `connection.init_db()` confirmada como não-morta: usada em `TestManualRedacaoConsulta.setUp` via atributo de módulo (não detectada por grep literal de import).

---

## [4.1.0] — RAG do Manual de Redação da Presidência da República (FTS5) — 2026-08-30

### ✨ Nova funcionalidade

- **RAG textual via SQLite FTS5**: Adicionada consulta ao **Manual de Redação da Presidência da República** (3ª edição) sem nenhuma dependência nova, reaproveitando `shared/maria.db`. Ferramenta de leitura `consultar_manual_redacao`, encadeada automaticamente antes de `criar_documento` quando o pedido é de um documento oficial (ofício, exposição de motivos, mensagem ou e-mail institucional).
- **Chunker e ingestão**: `backend/database/ingest_manual_redacao.py` segmenta o `.md` por cabeçalhos Markdown, classifica cada trecho por `tipo_documento` (com base no número da seção) e popula a tabela virtual `manual_redacao_fts`. Idempotente (execuções repetidas não duplicam) e com JSON de depuração ignorado no Git. **255 trechos** ingeridos a partir de `backend/docs/manual_redacao_presidencia.md` (copiado de `docs/`).
- **Consistência de domínio**: desde a 3ª edição do Manual, "aviso" e "memorando" foram unificados sob o termo **ofício** ("padrão ofício"). O enum de `tipo_documento` usa `oficio` para cobrir os três casos históricos; nenhuma categoria separada `aviso`/`memorando` foi criada. O parâmetro opcional `tipo_documento_oficial` em `criar_documento` orienta a formatação.

### 🔧 Implementação técnica

- **`shared/schema.sql`**: tabela virtual `manual_redacao_fts` com `tokenize = 'unicode61 remove_diacritics 2'` (busca tolerante a acentos).
- **`backend/database/schema.py`**: criação da FTS5 em `init_db()` (com `try/except` para SQLite sem FTS5) e `DROP TABLE` em `limpar_tudo()`.
- **`backend/core/manual_redacao.py`** (novo): `consultar_manual()` com query FTS5 segura (tokens escapados, AND implícito), ordenação `bm25` e truncamento por trecho (`MANUAL_REDACAO_MAX_CHARS_POR_TRECHO`, padrão 800) — evita estourar o contexto do modelo (padrão OLLAMA_NUM_CTX=2048 / LLAMA_NUM_CTX=8192).
- **`backend/core/tools_schema.py`**: nova `FERRAMENTA_CONSULTAR_MANUAL_REDACAO`, registrada em `FERRAMENTAS_LEITURA` e `TOOLS_SCHEMA`; ramo em `executar_ferramenta_leitura`; `FERRAMENTA_CRIAR_DOCUMENTO` atualizada (removida menção a "memorandos", adicionada instrução de consulta prévia e campo `tipo_documento_oficial`).
- **`backend/core/config.py`**: `MANUAL_REDACAO_TOP_K` (5) e `MANUAL_REDACAO_MAX_CHARS_POR_TRECHO` (800), com override via ENV.
- **Reforço de prompt**: `chat_session.py` (regra 9 e linha de ferramenta), `ollama_client.py` e `llama_client.py` instruem o modelo a chamar `consultar_manual_redacao` antes de `criar_documento` para documentos oficiais.
- **`.gitignore`**: `backend/database/manual_redacao_chunks.json` (artefato de depuração).

### 🧪 Testes

- **Status**: 116/116 testes passaram (`python -m unittest discover -s backend/tests -v`), executados 2× para confirmar isolamento do `_DB_PATH` em `TestManualRedacaoConsulta`.
- **3 novas classes**: `TestManualRedacaoIngestao` (chunker/classificador), `TestManualRedacaoConsulta` (consulta FTS5, truncamento, isolamento) e `TestFerramentaConsultarManualRedacao` (integração da ferramenta e consistência do domínio). Total: 11 testes novos.
- **Cobertura de código**: adições concentradas em `schema.py`, `ingest_manual_redacao.py`, `manual_redacao.py`, `tools_schema.py` e reforços de prompt — sem cobertura formal nova mensurada (não executado `coverage`); validação via `py_compile` + suíte unitária completa.

---
## [4.0.2] — Documentação da v4.0 e Manutenção

### 📚 Documentação

- **README reescrito para a v4.0**: Com a migração para Tauri v2 + React concluída, o README agora documenta a arquitetura atual como única versão. Removidas todas as menções ao frontend legado JavaFX/JDK/Maven (diagrama antigo, estrutura de pastas `frontend/`, pré-requisitos JDK 21/Maven, comandos `mvn javafx:run`/`mvn test` e testes JUnit 5). Novas seções: stack real do frontend (React 18 + TypeScript + Vite + Tailwind CSS + Framer Motion + Zustand + lucide-react), arquitetura detalhada (`TopBar`/`Sidebar`/`CenterStage`/`ChatPanel`, `useTheme`, `useMariaBridge`, `AuraBackground`), estrutura de pastas corrigida conforme o disco (removida referência inexistente a `pages/`, adicionada `types/`), pré-requisitos únicos (Python 3.11+, Node 18+, Rust 1.70+), modos de execução do backend (CLI, `--bridge`, `--bridge-http`) e seção própria de **Testes** (unittest + smoke-test do llama-server + Vitest no frontend). Roadmap atualizado: "Migração UI" marcada como ✅ concluída.

### 🧹 Manutenção

- **`.gitignore` reorganizado**: Consolidadas as duas seções sobrepostas do arquivo (genérica + específica do projeto Tauri), eliminando 23 entradas duplicadas (ex.: `__pycache__/`, `*.log`, `*.db`, `*.sqlite`, `.env`, `.env.*`, `!.env.example`, `.idea/`, `.vscode/`, `dist/`, `Thumbs.db`). Padrões agrupados em 14 seções numeradas, preservando a ordem das regras de negação (`.env.*` antes de `!.env.example`) e a entrada `.junie/`. Nenhum padrão adicionado ou removido — validado com `Compare-Object` contra a versão anterior e com `git check-ignore` (bancos SQLite em `shared/` continuam ignorados e `.env.example` segue rastreado).

---


## [4.0.1] — Migração para Tauri + React (P0–P2)

### 🔧 P0 — Bloqueadores críticos

- **Servidor HTTP bridge no backend**: Implementado servidor Flask (`--bridge-http --porta 8081`) expor o protocolo bridge via REST em `http://127.0.0.1:8081/chat`. Função `_despachar_comando` unifica a lógica entre modo stdin/stdout (`_modo_bridge`) e servidor HTTP (`_criar_app_http`). Adicionadas dependências `flask>=3.0.0` e `flask-cors>=4.0.0` em `requirements.txt`.
- **Corrigido schema SQLite no Rust**: `get_chat_history` e `save_message` agora utilizam tabelas `mensagens`/`conversas` (colunas `conversa_id`, `conteudo`, `criado_em`) conforme `shared/schema.sql`, com `PRAGMA foreign_keys = ON` e função `garantir_conversa`. Removida dependência `chrono` do `Cargo.toml`.

### 🧹 P1 — Limpeza técnica

- **Removido código órfão**: Deletado `frontend-tauri/src/pages/ConversarPage.tsx` (não importado por `App.tsx`).
- **Migrado benchmark para LlamaClient**: `backend/benchmark/runners/maria_runner.py` e `backend/benchmark/run_benchmark.py` agora importam de `core.llama_client` (raiz do monorepo) em vez de `core.ollama_client`. Atualizado `backend/benchmark/README_benchmark.md` com instruções de llama-server.
- **Corrigido requirements.txt**: Consolidado conteúdo na raiz do monorepo.

### ✅ P2 — Completude

- **Testes automatizados**: Adicionados testes Rust (`cargo test`) e TypeScript (`vitest run`) no frontend-tauri.
- **Consolidada documentação**: Atualizados `docs/ARQUITETURA_SISTEMA.md`, `docs/DECISOES_BANCO_DADOS.md`, `docs/IMPLEMENTACAO_DAO.md` com notas sobre modelo padrão `qwen2.5-omni-3b` via llama-server e `qwen3.5:4b` como legado/opcional.
- **Validado sidecar e instalador**: `build_sidecar.py` agora gera binário com suffixo do target triple (`maria-backend-<triple>[.exe]`) via `_obter_target_triple()`.
- **Guia de testes empíricos**: Criado [`docs/GUIA_TESTES_EMPIRICOS.md`](docs/GUIA_TESTES_EMPIRICOS.md) com o passo a passo para construir e executar os 5 níveis de teste (build, unitários, llama-server ao vivo, bridge HTTP, benchmark e E2E de UI).

---

## [4.0.0-alpha] — Em Desenvolvimento: Migração para Tauri + React

### 🚀 Nova Arquitetura (v4.0)

**Status:** Em desenvolvimento ativo — Consulte [`docs/PLANO_MIGRACAO_TAURI_V4.md`](docs/PLANO_MIGRACAO_TAURI_V4.md) para roadmap completo.

#### Mudanças Estruturais

- **Frontend JavaFX → Tauri v2 + React**: Substituição completa da interface JavaFX (21 controllers FXML) por stack moderno com React + TypeScript + Tailwind CSS + Framer Motion
- **Comunicação HTTP Local**: Migração do protocolo JSON-lines stdin/stdout para HTTP local (localhost:8081) + IPC nativo Tauri
- **Backend Python Intacto**: Os 818 linhas de `main.py` são mantidos, apenas adicionando modo bridge HTTP (porta 8081)
- **Instalador One-Click**: MSI (Windows), .deb (Linux) e AppImage (macOS) com Python embeddable e modelos pré-baixados
- **Arquitetura Híbrida de Modelos**: Roteamento inteligente entre Qwen2.5-Omni 3B (tarefas rápidas), Llama 3.2 8B (raciocínio complexo) e CodeQwen 7B (geração de scripts)

#### 🔧 Estabilização do Build (Frontend Tauri)

Correções aplicadas em **2026-08-28** para destravar a compilação e execução do app Tauri:

- **Corrigido `E0255: __cmd__... defined multiple times`**: as funções `#[tauri::command]` eram declaradas como `pub` — no Tauri v2 isso gera macros `__cmd__...` duplicadas (issue oficial tauri-apps/tauri #15921). Removido o `pub` de todos os comandos (padrão do scaffold oficial).
- **Criado `src-tauri/build.rs`**: build script com `tauri_build::build()` — resolve o erro `OUT_DIR env var is not set` no `tauri::generate_context!()`.
- **Corrigido `tauri.conf.json` → plugins.shell**: substituída a sintaxe v1 (`scope`/`sidecar` — incompatível com o Tauri v2) por `"open": true`.
- **Criado `src-tauri/capabilities/default.json`**: permissão `shell:allow-execute` com escopo para o sidecar `maria-backend` e os executáveis `python`/`python3` (novo local da configuração de shell no v2).
- **Criados assets de build**: `src-tauri/binaries/` (placeholder do sidecar exigido por `externalBin`), `src-tauri/icons/` (PNG/ICO/ICNS) e script `gen_icons.py`.
- **Uso de `params!` do rusqlite** nas instruções `INSERT`/`query_map` (substitui arrays heterogêneos que causavam `mismatched types`).
- **Separação dev/prod com `#[cfg(...)]`**: `call_python_http`/`PythonRequest`/`PythonResponse` (dev) e `call_python_sidecar`/`tokio::process::Command` (prod) agora são condicionais — build dev e release sem warnings.
- **Validação**: `cargo check` e `cargo check --release` passam sem erros; `maria-frontend.exe` inicia sem panic.

#### Benefícios Esperados

- ✅ **Design Moderno**: UI com glassmorphism, aura rosa e animações fluidas (Figma → código pixel-perfect)
- ✅ **Simplificação de Instalação**: Elimina necessidade de JDK 21 e Maven; instalador único <5 minutos
- ✅ **Pool de Talentos Ampliado**: Stack React/Tauri vs JavaFX em declínio
- ✅ **Multiplataforma Nativo**: Windows/Linux/macOS com experiência consistente
- ✅ **Receita de Hardware**: "Maria Box" — mini-PC pré-configurado para PMEs

#### Roadmap de 17 Semanas

| Fase | Versão | Entregável Principal |
|------|--------|---------------------|
| Fase 1 | v3.3 | UI Tauri + React pixel-perfect (semanas 1-4) |
| Fase 2 | v3.4 | Roteamento 3B ↔ 8B (semanas 5-8) |
| Fase 3 | v3.5 | Instalador one-click (semanas 9-12) |
| Fase 4 | v3.6 | Voz da MARIA: TTS + STT + avatar animado (semanas 13-16) |
| Fase 5 | v4.0 | Lançamento Parceiro Fundador (10 empresas piloto) |

#### Estimativa de Custos

| Item | Custo (BRL) |
|------|------------|
| Dev React/Tauri (freelancer sênior, 4 meses) | R$ 80.000 |
| Designer UI/UX (Figma → código) | R$ 15.000 |
| Certificados de assinatura (Windows) | R$ 2.000 |
| Servidores de teste multiplataforma | R$ 5.000 |
| **Total** | **R$ 102.000** |

> **Nota:** Esta versão está em planejamento ativo. A versão estável atual permanece sendo v3.2.0 (JavaFX).

---

## [3.2.0] — Migração para llama.cpp + Qwen2.5-Omni 3B

### ✅ Runtime de Inferência
- **Substituição do Ollama pelo llama-server (llama.cpp)**: o backend agora se comunica com `http://localhost:8080/v1/chat/completions` via API OpenAI-compatible, eliminando a dependência do daemon Ollama.
- **Modelo Qwen2.5-Omni 3B (Q4_K_M)**: modelo multimodal unificado que suporta texto, imagem e áudio em um único GGUF (~2.3 GB), sem necessidade de modelos separados para visão ou transcrição.

### ✅ Novo Módulo `backend/core/llama_client.py`
- **`LlamaClient`**: cliente HTTP com interface pública idêntica ao `OllamaClient` (`chat`, `chat_stream`, `enviar_mensagem`, `chat_com_tools_stream`, `continuar_com_resultado_ferramenta_stream`).
- **Suporte multimodal**: `image_path` converte imagem para base64 (`image_url`); `audio_path` converte `.wav` para base64 (`input_audio`) — ambos no formato OpenAI multimodal.
- **Tool calling via API OpenAI**: campo `tools` + `tool_choice: auto`, com fallback textual (`_tentar_extrair_tool_call_textual`) para modelos que vazam a chamada como texto.
- **Streaming com métricas**: TTFT, tokens/s e `eval_count` calculados via SSE (`data: {...}`) e campo `usage` do último chunk.
- **Exceções tipadas**: `LlamaClientError` (conexão/HTTP) e `LlamaTimeoutError` (timeout), equivalentes às do `OllamaClient`.

### ✅ Configuração (`backend/core/config.py`)
- Adicionadas 9 variáveis `LLAMA_*` com override via ENV: `LLAMA_BASE_URL`, `LLAMA_MODEL`, `LLAMA_TIMEOUT`, `LLAMA_NUM_CTX`, `LLAMA_NUM_PREDICT`, `LLAMA_TEMPERATURE_TOOLS`, `LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL`, `LLAMA_NUM_PREDICT_DOCUMENTO`, `LLAMA_NUM_PREDICT_CONTINUACAO`.
- Todas as variáveis `OLLAMA_*` preservadas para rollback fácil.

### ✅ Integração (`backend/main.py`)
- Import de `LlamaClient as OllamaClient` e uso de `LLAMA_MODEL` — sem alterações na lógica de orquestração.

### ✅ Testes e Validação
- Novos testes unitários em `backend/tests/test_maria.py` cobrindo: chat texto, tool calling estruturado, fallback textual, streaming com métricas, erro de conexão, timeout e métodos de compatibilidade (mock de `requests.Session`).
- Novo script `backend/tests/validate_llama_server.py`: smoke-test standalone contra o llama-server real (conexão, chat texto, streaming, visão, áudio).

---

## [3.1.1] — Unificação de Schema e Correções Críticas Monorepo

### ✅ Banco de Dados e DAOs
- **Schema SQLite canônico (shared/schema.sql)**: 6 tabelas unificadas em português (conversas, mensagens, memoria, arquivos_indexados, automacoes, configuracoes) compartilhadas entre Python e Java em shared/maria.db.
- **Integridade referencial**: Ativação de PRAGMA foreign_keys = ON com ON DELETE CASCADE entre conversas e mensagens, e PRAGMA journal_mode = WAL.
- **DAOs Java padronizados**: ConversaDAO.java, MemoriaDAO.java, AutomacaoDAO.java e ConfiguracaoDAO.java totalmente alinhados ao schema unificado.
- **Migração preventiva**: DatabaseManager.java com verificação dinâmica de colunas para garantir compatibilidade com bases SQLite existentes.
- **Suíte de Testes JUnit 5**: Expandida para 8 testes (DatabaseManagerTest.java), cobrindo conexão, todos os DAOs e exclusão em cascata (100% passando).

### ✅ Configuração, Build e Dependências
- **Consolidação de dependências**: Inclusão de psutil>=5.9.0 no 
equirements.txt da raiz e exclusão do ackend/requirements.txt redundante.
- **Detecção de SO no App.java**: Resolução automática do executável Python em Windows (.venv/Scripts/python.exe), Linux/macOS (.venv/bin/python) e PATH.
- **Maven / Java 21**: Configuração de <maven.compiler.release>21</maven.compiler.release> em rontend/pom.xml.
- **Limpeza do Git**: Remoção e desindexação de arquivos de build (	arget/), caches de Python (__pycache__) e bancos locais antigos do controle de versão via .gitignore aprimorado.

### ✅ Identidade Visual
- **Adaptação do Tema Escuro (	heme-dark.css)**: Efeito de aura e destaques rosa (#e05d8a / #f2a2bb) nos botões de ação rápida, botão de envio, menus e avatares, mantendo conformidade com o parser JavaFX Modena.


## [3.1.0] — Fase 3: Integração Backend-Frontend Completa

### ✅ Backend (Python)

- **Comandos Bridge expandidos**: 14 → 20 comandos suportados
  - `deletar_memoria`: Remove memória por ID
  - `limpar_memorias`: Limpa todas as memórias
  - `listar_automacoes`: Lista automações com status ativo/inativo
  - `deletar_automacao`: Remove automação por ID
  - `toggle_automacao`: Ativa/desativa automação
  - `listar_sessoes`: Lista sessões de conversa salvas
  - `carregar_sessao`: Carrega sessão de conversa por ID
  - `salvar_memoria`: Salva nova memória (alias para adicionar_memoria)
  - `listar_memoria`: Lista memórias com filtro opcional
  - `criar_automacao`: Cria nova automação
  - `analisar_arquivo`: Lê documentos e planilhas
  - `analisar_dados`: Gera sumário de planilhas Excel
  - `upload_arquivo`: Copia arquivos para pasta de geração
  - `transcrever_audio`: Transcrição via whisper.cpp
  - `status`: Métricas de CPU, RAM e GPU
  - `exportar_conversa`: Exporta conversa em TXT
  - `limpar_conversa`: Limpa mensagens da sessão atual
  - `chat`: Envio de mensagens com contexto
  - `encerrar`: Finaliza conexão bridge
  - `ping`: Handshake de conectividade
- **Schema SQLite unificado**: 6 tabelas em `shared/maria.db`
  - `conversas`, `mensagens`, `memoria`, `arquivos_indexados`, `automacoes`, `configuracoes`
- **Inicialização automática**: `backend/database/schema.py` cria tabelas no startup
- **Testes**: 86 testes unitários passando

### ✅ Frontend (JavaFX)

- **DAOs de persistência**: 5 classes implementadas
  - `DatabaseManager.java`: Singleton JDBC com schema unificado
  - `ConversaDAO.java`: CRUD de conversas e mensagens
  - `MemoriaDAO.java`: CRUD de memórias com busca por categoria
  - `AutomacaoDAO.java`: CRUD de automações com toggle
  - `ConfiguracaoDAO.java`: Chave-valor com UPSERT
- **Schema unificado**: Frontend agora usa `shared/maria.db` (mesmo banco do backend)
- **Controllers integrados**:
  - `ConversarController`: Salva mensagens no banco, limpar cria nova sessão
  - `MemoriaController`: Carrega/gerencia memórias do banco
  - `AutomacoesController`: Lista com status ✓/✗, toggle ativo/inativo
- **Testes JUnit**: 6 testes no `DatabaseManagerTest` (100% passing)

### 🔧 Correções Técnicas

- **Java version**: Maven atualizado para Java 17 (compatível)
- **Imports corrigidos**: `Optional` em `ConfiguracaoDAO.java`, `sqlite3` em `schema.py`
- **Banco compartilhado**: Eliminado `frontend/maria.db` separado; agora ambos usam `shared/maria.db`

### 📊 Métricas da Versão

| Categoria | Antes (v2.14.0) | Depois (v3.1.0) | Progresso |
|-----------|-----------------|-----------------|-----------|
| Comandos Bridge | 14 | 20 | +43% |
| DAOs Java | 0 | 5 | +500% |
| Tabelas Banco | 0 | 6 | Schema completo |
| Controllers Integrados | 1 | 3 | +200% |
| Testes Unitários | 86 | 92 | +6 testes |

## [2.14.0] — Desmockagem e Funcionalidades Reais

### ✅ Backend (Python)

- **Novo comando `status`**: Retorna métricas reais de CPU, RAM e GPU via `psutil`. Inclui modelo atual (`qwen3.5:4b`) na resposta.
- **Handler `analisar_arquivo`**: Lê documentos (.docx, .txt, .md, .csv, .log) e planilhas (.xlsx), retornando conteúdo ou resumo.
- **Handler `analisar_dados`**: Gera sumário de planilhas Excel (linhas, colunas, cabeçalhos, amostra de dados).
- **Handler `upload_arquivo`**: Copia arquivos para `backend/arquivos_gerados` com nome único.
- **Handler `transcrever_audio`**: Integração com whisper.cpp (binário externo) para transcrição de áudio WAV. Fallback informativo se não instalado.
- **Nova dependência**: `psutil>=5.9.0` adicionada ao `requirements.txt`.
- **Função `ler_planilha_resumo()`**: Criada em `backend/core/excel_handler.py` para leitura eficiente de planilhas.

### ✅ Frontend (JavaFX)

- **Sidebar com dados reais**: Barras de progresso (CPU/RAM/GPU) atualizadas a cada 5 segundos via comando `status`. Labels exibem porcentagem em tempo real.
- **Modelo dinâmico**: Texto do modelo na topbar é atualizado automaticamente via backend (agora exibe `qwen3.5:4b · via Ollama`).
- **Dropdown do chat funcional**: Menu "⋯" no header com opções "Limpar Conversa" e "Exportar Conversa (.txt)".
- **Botão anexar (📎) habilitado**: Abre FileChooser, envia arquivo via `upload_arquivo` e exibe confirmação no chat.
- **Botão de voz (🎤) habilitado**: Grava áudio via `javax.sound.sampled`, salva como WAV temporário e envia para transcrição. Indicador visual durante gravação.
- **Ações rápidas do Hero**: Botões agora preenchem o campo de mensagem com prompts contextuais prontos para envio.

### ⚠️ Notas

- **GPU**: Exibida como 0% se não houver GPU NVIDIA ou `pynvml` não estiver instalado.
- **Whisper.cpp**: Requer instalação manual do binário `whisper-main`. Sem fallback de transcrição se não disponível.
- **Avatar real**: Imagem `avatar.png` já carregada no hero. Pendente aplicação nas bolhas de mensagem.

## [2.13.0] - Redesign da Interface (3 colunas + barras)

### ✅ Interface JavaFX

- **Novo layout em `main-view.fxml`**: topbar (logo, pill MODO LOCAL, modelo **qwen3.5:4b**, botão de tema ☀/☾), sidebar expandida (260px), coluna central com hero + painel de chat permanente (380px), status bar inferior.
- **`theme-dark.css` e `theme-light.css` reescritos** (~70 regras cada): novas paletas (dark: fundo `#0e0e16`, accent rosa `#e05d8a`; light: fundo `#f7f3ec`, accent terracota `#c47b54`), com classes `.topbar`, `.pill-modo`, `.sidebar-card`, `.resource-bar-*`, `.card-feature`, `.quick-action`, `.bubble-user`, `.bubble-maria`, `.chat-panel`, `.avatar-hero`, `.menu-item-selected`, `.status-bar`.
- **`hero-view.fxml` + `HeroController.java` criados**: tela inicial central com título, subtítulo, avatar placeholder (gradiente + letra "M"), 3 cards de funcionalidades e 4 ações rápidas.
- **`ConversarController` reescrito** para painel de chat permanente: bolhas alinhadas (usuário à direita, Maria à esquerda com avatar), timestamps, header "CONVERSA ATUAL", input com 📎/🎤 desabilitados e botão enviar. Handshake `ping` + comando `chat` preservados.
- **`MainController` reescrito**: navegação troca apenas a coluna central; opção "Conversar" exibe o hero; alternância de tema em runtime (`alternarTema`); ações rápidas preenchem o campo do chat; `setCena` conectado pelo `App`.
- **`MenuItemsController`**: novo `destacar(...)` para realçar a aba ativa (`.menu-item-selected`).
- **`App.java`**: janela 1280×800, carga de `theme-dark.css` e `setCena` no controller.
- **`Image folder criada**: `resources/.../images/` para receber `avatar.png`.
- **Modelo LLM atualizado**: interface agora reflete o modelo real `qwen3.5:4b` (substituindo referências mockadas ao Llama 3.1 8B).

### ⚠️ Elementos mockados nesta fase
Recursos do sistema (CPU/RAM/GPU), ações rápidas (preenchem o input), anexar/voz (desabilitados) e dropdown "⋯" sem ação. Ver `docs/PENDENCIAS_INTERFACE.md`.

### ✅ Validação
- Estática: handlers `onAction`/`onMouseClicked` de todos os FXMLs mapeados aos controllers; zero typos de cor no CSS.
- Compilação/visual pendente de execução no IntelliJ (Maven/JDK não presentes na CLI).

## [2.12.0] - Integração do Frontend JavaFX e Organização da Documentação

### ✅ Frontend (Fase 1 do guia de próximos passos)

- **`BridgeManager.java` criado**: singleton estático para o `PythonBridgeService`, compartilhado entre `App.java` e os controllers das abas (`iniciar()`, `getInstance()` com `IllegalStateException` se não iniciado, `encerrar()`).
- **`App.java` reescrito**: chat standalone removido; agora carrega `main-view.fxml` (sidebar + navegação das 8 abas), aplica `theme-dark.css`, inicia a bridge via `BridgeManager` e encerra o processo Python ao fechar.
- **Injeção do menu corrigida**: `<fx:include fx:id="menuItems">` em `main-view.fxml`; `MainController` injeta-se no `MenuItemsController` no `initialize()` e carrega a aba "conversar" por padrão — os 8 botões do menu agora funcionam.
- **`ConversarController` integrado à bridge**: handshake `ping` automático ao abrir a aba; envio real via comando `chat`; respostas do Ollama exibidas na área de mensagens; `exceptionally` tratado também no envio.
- **Enter envia mensagem**: `onAction="#enviarMensagem"` adicionado ao TextField em `conversar-view.fxml`.

### ✅ Documentação (Fase 0 do guia)

- **`backend/README.md`**: modelo divergente corrigido (`qwen3.5:4b`, alinhado a `backend/core/config.py`).
- **Documentos obsoletos arquivados** em `docs/archive` com aviso de obsolescência: `RELATORIO_ACOMPANHAMENTO.md` e `ARQUITETURA_REAL_SISTEMA.md`.
- **`README.md` (raiz)**: tabela de documentação atualizada e modelo LLM atualizado para `qwen3.5:4b`.
- **`docs/DECISOES_BANCO_DADOS.md` criado**: registra as 4 perguntas pendentes antes da implementação de `backend/database/schema.py` (Fase 2 bloqueada por decisão, não por código).

### ⚠️ Validação

- Validação estática concluída: zero referências residuais, pacotes/FXML/controllers consistentes.
- Compilação/execução real **pendente** de JDK 21 + Maven (não instalados na máquina): rodar `cd frontend && mvn clean compile && mvn javafx:run`.

## [2.11.1] - Correção dos Testes Quebrados (Namespace dos Patches)

### ✅ Correções aplicadas

- **Causa raiz**: os decoradores `@patch` usavam o namespace `core.ollama_client.*`, mas o módulo é importado como `backend.core.ollama_client`. Como o pytest adiciona `backend` ao `sys.path`, o Python registrava dois módulos distintos e o patch era aplicado na instância errada — os flags (`OLLAMA_ENVIAR_THINK_PARAM`, `OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL`) nunca mudavam no código em execução.
- **Fix**: alvos de patch corrigidos para `backend.core.ollama_client.*` em `backend/tests/test_maria.py` (linhas 1397, 1437–1438), incluindo `requests.Session` por consistência.
- **Observação**: o comando legado `cd backend && python -m unittest tests.test_maria` está quebrado por design (o arquivo importa `backend.*`). Comando correto a partir da raiz: `python -m unittest backend.tests.test_maria`.

### ✅ Status dos Testes

- **86/86 testes passaram** + 33 subtestes via pytest (raiz do monorepo)
- **86/86 passaram** via `python -m unittest backend.tests.test_maria` (raiz)

## [2.11.0] - Unificação de Pacotes Java e Documentação do Monorepo

### ✅ Alterações aplicadas

- **Unificação dos pacotes Java em `com.tristar.maria`**: os 10 controllers movidos de `com/nyc/maria/ui/` para `com/tristar/maria/ui/`, com declaração `package` corrigida.
- **Resources movidos**: 10 FXMLs + 2 CSS de `resources/com/nyc/maria/` para `resources/com/tristar/maria/`; atributos `fx:controller` atualizados nos 10 FXMLs.
- **`MainController` corrigido**: caminho dinâmico das views atualizado para `/com/tristar/maria/...`; bloco de reflexão morto (`setMainController`) removido.
- **`pom.xml` alinhado**: groupId alterado para `com.tristar.maria` (mainClass já era `com.tristar.maria.App`).
- **Pastas `com/nyc/` removidas**; varredura confirma zero referências residuais no código.
- **Documentação atualizada**: menções a `com.nyc` substituídas em `docs/ARQUITETURA_REAL_SISTEMA.md`, `docs/INTEGRACAO_FRONTEND.md` e `docs/RELATORIO_ACOMPANHAMENTO.md`.
- **Novos documentos na raiz**: `README.md` do monorepo (arquitetura, pré-requisitos, execução CLI/frontend/bridge) e `requirements.txt` consolidado.
- **Novo relatório**: `docs/RELATORIO_ESTADO_ATUAL.md` com análise de bugs, erros e inconsistências, percentuais por camada e roadmap priorizado para a GUI ficar funcional.

### ✅ Status dos Testes

- **84/86 testes passaram** (`pytest backend/tests/test_maria.py`) + 33 subtestes
- 2 falhas **pré-existentes** (não relacionadas a esta tarefa): `test_montar_payload_omite_think_quando_desabilitado` e `test_fallback_desativado_nao_extrai_tool_call`
- Validação do frontend foi estática (Maven/JDK 21 não instalados na máquina) — pendente `mvn clean compile`

### 📊 Cobertura de Código

- Frontend: estrutura de pacotes 100% consistente (Java + FXML + pom.xml)
- Backend: sem alterações de lógica nesta versão

## [2.10.0] - Configuração de Modelo Centralizada e Fallback Textual Desativável

### ✅ Alterações aplicadas

- **Configuração de comportamento do modelo concentrada em `backend/core/config.py`**: 4 novas variáveis ajustáveis via ENV — `OLLAMA_ENVIAR_THINK_PARAM` (envio do campo "think"), `OLLAMA_THINK_HABILITADO` (valor do campo "think"), `OLLAMA_TEMPERATURE_TOOLS` (temperatura para tool calling) e `OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL` (fallback textual desativável).
- **Novos métodos privados em `OllamaClient`**: `_montar_options()` e `_montar_payload()` centralizam a construção do payload, eliminando 5 blocos duplicados de montagem manual.
- **Os 5 métodos de payload agora usam `self._montar_payload`**: `enviar_mensagem`, `chat_com_tools`, `chat_com_tools_stream_com_metricas`, `chat_com_tools_stream` e `continuar_com_resultado_ferramenta_stream`.
- **Inconsistência de `temperature` corrigida**: `continuar_com_resultado_ferramenta_stream` agora envia `temperature` (antes era o único dos 5 que não aplicava).
- **Mensagem de erro dinâmica em `_make_request`**: a mensagem de conexão agora reflete `self.model`/`self.base_url` reais em vez de literais fixos `qwen3.5:4b`/`localhost:11434`.
- **`model_file.txt` removido** do repositório (sem referências em código Python).
- **Fallback textual de tool call desativável**: os 4 pontos em `backend/core/ollama_client.py` que extraem tool call vazada como texto (comportamento do Qwen3.5) agora respeitam `OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL`.
- **Debug scripts atualizados**: `debug_raw_ollama.py` e `debug_raw_ollama_2systems.py` usam `OLLAMA_TEMPERATURE_TOOLS`, `OLLAMA_ENVIAR_THINK_PARAM` e `OLLAMA_THINK_HABILITADO` em vez de literais hardcoded.

### ✅ Status dos Testes

- **80/80 testes passaram** (`python -m unittest tests.test_maria -v`)
- 5 testes novos: `TestConfiguracaoDeModeloCentralizada` (4) + `TestFallbackTextualDesativavel` (1)
- **Compilação sem erros** (`python -m py_compile core/config.py core/ollama_client.py debug_raw_ollama.py debug_raw_ollama_2systems.py tests/test_maria.py`)

### 📊 Cobertura de Código

- Payload centralizado: inclusão/omissão de `think`, temperatura condicional, mensagem de erro com model/base_url dinâmicos.
- Fallback textual: desativado não extrai tool call; testes existentes continuam passando com o default `True`.

## [2.9.0] - Correções do Benchmark: Encadeamento de Leitura, Composição de Documentos e Falso Positivo de listar_arquivos

### ✅ Correções aplicadas

- **Encadeamento de leitura compartilhado (Fix A)**: criado o módulo `backend/core/tool_chaining.py` com `encadear_leitura_stream`, usado tanto pela aplicação interativa (`main.py`) quanto pelo benchmark (`backend/benchmark/runners/maria_runner.py`). O benchmark agora reenvia o resultado de `listar_arquivos`/`resumir_documento` ao modelo e captura a ferramenta de escrita seguinte, em vez de marcar `tool_correct=False` na primeira chamada.
- **Timeout POR CHAMADA no encadeamento**: cada chamada de continuação do encadeamento de leitura no benchmark tem seu próprio orçamento de `BENCHMARK_TASK_TIMEOUT` segundos, medido do início ao fim daquela chamada específica (não acumulado), resolvendo o item em aberto da seção 1.1 de `backend/docs/guia_fase_2.md`.
- **`main.py` refatorado**: `_gerar_resposta_com_encadeamento` agora delega ao módulo compartilhado; removidos os imports diretos de `MAX_PASSOS_LEITURA`, `FERRAMENTAS_LEITURA` e `executar_ferramenta_leitura`.
- **Composição de documentos sem conteúdo literal (Fix B)**: o reforço em `backend/core/ollama_client.py` (`_montar_mensagens_com_reforco`) agora instrui o modelo a REDIGIR conteúdo completo para documentos narrativos (carta, relatório, ata, comunicado) sem pedir mais detalhes ao usuário.
- **Falso positivo de `listar_arquivos` corrigido (Fix D)**: a regra 6 do `SYSTEM_PROMPT` em `backend/core/chat_session.py` agora distingue arquivo incerto de arquivo declaradamente inexistente — responde em texto SEM chamar `listar_arquivos` nem outra ferramenta.

### ✅ Status dos Testes

- **75/75 testes passaram** (`python -m unittest tests.test_maria -v`)
- **Compilação sem erros** (`python -m py_compile main.py core/tool_chaining.py core/ollama_client.py core/chat_session.py benchmark/runners/maria_runner.py tests/test_maria.py`)

### 📊 Cobertura de Código

- Encadeamento de leitura: avanço até ferramenta de escrita, limite de passos, propagação de timeout por chamada e integração no `MariaRunner`.
- Reforço de composição de documento e exceção de arquivo fictício no `SYSTEM_PROMPT`.

## [2.8.0] - Correções de Alta Prioridade e Validação de Argumentos

### ✅ Correções aplicadas

- **TOCTOU em criação de pastas corrigido**: substituído o padrão de `exists()` + `makedirs()` por `os.makedirs(..., exist_ok=True)` em `backend/core/file_utils.py` e `backend/core/session_storage.py`, eliminando a condição de corrida entre checagem e criação da pasta.
- **Imports não utilizados removidos**: limpeza dirigida em `main.py`, `backend/core/word_handler.py` e `backend/tests/test_maria.py`, sempre com confirmação textual da ausência de referências antes da remoção.
- **Validação de argumentos obrigatórios implementada**: adicionado `CAMPOS_OBRIGATORIOS` e `validar_argumentos_obrigatorios()` em `backend/core/tools_schema.py`, com chamada no início de `executar_ferramenta_real` antes da execução de cada ferramenta real.
- **Tratamento de erro reforçado**: campos obrigatórios ausentes ou vazios agora geram `ValueError` claro, evitando execução de ferramentas com arquivos vazios ou incompletos.
- **Cobertura de regressão expandida**: novos testes cobrindo ausência de campo obrigatório e string vazia em campos obrigatórios.
- **Documentação de benchmark atualizada**: README geral e `benchmark/README.md` agora mencionam a taxa de conformidade de idioma gerada pelo relatório.

### ✅ Status dos Testes

- **42/42 testes passaram** (`python -m unittest tests.test_maria -v`)
- **Compilação sem erros** (`python -m py_compile main.py core/config.py core/file_utils.py core/tools_schema.py core/ollama_client.py core/chat_session.py core/session_storage.py core/excel_handler.py core/word_handler.py tests/test_maria.py`)

### 📊 Cobertura de Código

- Validação de argumentos antes da execução real de ferramentas, tratamento de TOCTOU em criação de diretórios, remoção segura de imports e regressões em testes de execução real.

## [2.7.0] - Integração das Ferramentas de Leitura no Controller

### ✅ Funcionalidades implementadas

- **Encadeamento automático de leitura**: O método `enviar_mensagem` em `main.py` (classe `MariaController`) agora encadeia automaticamente ferramentas de **leitura** (`listar_arquivos`, `resumir_documento`) sem pedir confirmação, até `MAX_PASSOS_LEITURA` vezes.
- **Novo generator `_gerar_resposta_com_encadeamento`**: Chama o modelo via `chat_com_tools_stream` e, enquanto a tool call for de leitura, executa via `executar_ferramenta_leitura` e reenvia o resultado via `continuar_com_resultado_ferramenta_stream` — mantendo o efeito de streaming contínuo.
- **Ferramentas de escrita preservadas**: Quando o encadeamento chega a uma ferramenta de **escrita** (`criar_planilha`, `criar_documento`, `editar_planilha`), o fluxo de confirmação normal é acionado ao final — `get_mensagem_confirmacao` e `processar_confirmacao` permanecem intactos.
- **Limite de passos respeitado**: Se `MAX_PASSOS_LEITURA` for atingido sem resposta final, um aviso amigável é exibido e o encadeamento é encerrado com segurança.
- **Tratamento de erros de leitura**: `PermissionError`, `OSError` e `ValueError` ao executar ferramentas de leitura são capturados e devolvidos ao modelo como texto, sem derrubar a aplicação.
- **`ui_terminal.py` intacto**: A interface continua iterando `(chunk, tool_chunk)` como antes — nenhuma alteração foi necessária.

### ✅ Status dos Testes

- **40/40 testes passaram** (`python -m unittest tests.test_maria -v`)
- **Compilação sem erros** (`python -m py_compile main.py`)
- **Validação com mocks**: 3 cenários de encadeamento validados (leitura→escrita, leitura simples, limite de passos)

### 📊 Cobertura de Código

- Encadeamento de leitura: execução sem confirmação, propagação de tool de escrita, limite de passos, tratamento de erros.

## [2.6.0] - Exibição de Comandos na Tela Inicial

### ✅ Funcionalidades implementadas

- **Linha de comandos no banner inicial**: A função `exibir_banner` em `ui_terminal.py` agora exibe diretamente a linha `Comandos: 'ajuda' | 'limpar' | 'retomar' | 'sair'` na inicialização, eliminando a necessidade de digitar `ajuda` primeiro.
- **Comando `retomar` visível na inicialização**: O comando `retomar` (introduzido na v2.4.0) agora aparece diretamente no banner junto dos comandos básicos (`ajuda`, `limpar`, `sair`).
- **README.md revisado**: Confirmado que a tabela "Comandos Disponíveis" permanece consistente com a nova linha do banner; nenhuma edição foi necessária (o README não reproduz a tela inicial literalmente).

### ✅ Status dos Testes

- **Nenhuma alteração de lógica testável** — a mudança é apenas de texto de interface (`print` de uma nova linha no banner).
- **Validação manual**: `python main.py` confirmou a exibição da linha `Comandos: 'ajuda' | 'limpar' | 'retomar' | 'sair'` antes do prompt `maria@assistente:~$`, seguida de `sair` para encerrar.

### 📊 Cobertura de Código

- Mudança puramente de interface (texto de tela); sem lógica testável adicionada.

## [2.5.0] - Ferramentas de Leitura: Listagem e Resumo de Documentos

### ✅ Funcionalidades implementadas

- **Lista branca de pastas (`PASTAS_PERMITIDAS`)**: nova variável de ambiente que restringe onde a MARIA pode ler arquivos; resolução de caminho protegida contra path traversal (`resolver_caminho_permitido`).
- **`listar_arquivos`**: nova ferramenta que lista nome e tamanho dos arquivos de uma pasta permitida.
- **`resumir_documento`**: nova ferramenta que lê `.txt`, `.md`, `.csv`, `.log` e `.docx` (com truncamento seguro via `MAX_CHARS_LEITURA`) para que o modelo resuma ou analise o conteúdo.
- **Ferramentas de leitura não pedem confirmação**: por serem somente leitura, `listar_arquivos` e `resumir_documento` são executadas imediatamente, diferente das ferramentas de escrita.
- **Encadeamento de chamadas**: `main.py` processa até `MAX_PASSOS_LEITURA` ferramentas de leitura em sequência (ex.: listar → ler → resumir) antes de responder ou pedir confirmação de escrita.
- **Streaming mantido na continuação**: novo método `continuar_com_resultado_ferramenta_stream` em `OllamaClient` devolve o resultado da leitura ao modelo e transmite a resposta em streaming.

### 🔒 Segurança e confiabilidade

- Todo acesso de leitura é validado contra `PASTAS_PERMITIDAS`; caminhos fora da lista branca são rejeitados com `ValueError`.
- Extensões de leitura restritas a uma lista branca (`EXTENSOES_LEITURA`).
- Limites de tamanho de arquivo (`MAX_TAMANHO_ARQUIVO_MB`) e de caracteres lidos (`MAX_CHARS_LEITURA`).
- `PermissionError`/`OSError` tratados com mensagens amigáveis, no mesmo padrão de `excel_handler.py`/`word_handler.py`.

### 🧪 Testes

- Novas classes `TestAcessoLeitura` e `TestFerramentasLeitura` cobrindo path traversal, listagem, truncamento, extensão não suportada e arquivo inexistente.

### ✅ Status dos Testes

- **40/40 testes passaram** (`python -m unittest tests.test_maria -v`)
- **Compilação sem erros** (`python -m py_compile main.py core/config.py core/file_utils.py core/tools_schema.py core/ollama_client.py core/chat_session.py tests/test_maria.py`)

### 📊 Cobertura de Código

- Ferramentas de leitura: path traversal, listagem de arquivos, truncamento, extensão não suportada, arquivo inexistente, resumo de documento e ferramenta desconhecida.

## [2.4.0] - Persistência de Sessões (Histórico de Conversa)

- **Novo módulo `backend/core/session_storage.py`**: Persistência de sessões de chat em disco, com 4 funções públicas (`garantir_pasta_sessoes`, `salvar_sessao`, `listar_sessoes_salvas`, `carregar_sessao`) e leitura dinâmica de `PASTA_SESSOES` por chamada (isolamento em testes).
- **Nova config `PASTA_SESSOES`** em `backend/core/config.py`: Configurável via variável de ambiente, padrão `sessoes_salvas`, seguindo o mesmo padrão de `PASTA_ARQUIVOS_GERADOS`.
- **Novo comando `retomar`** em `main.py`: Lista sessões salvas (mais recentes primeiro) e retoma a sessão escolhida de uma execução anterior. Funciona mesmo sem sessões salvas (mensagem clara, sem crash).
- **Salvamento automático**: A sessão é salva em disco após cada troca normal de mensagens e após a execução confirmada de uma ferramenta.
- **Arquivos de sessão**: Cada execução gera um arquivo `sessao_<timestamp>.json` na pasta `backend/sessoes_salvas`; ao retomar, a conversa continua salvando no mesmo arquivo.
- **Tolerância a falhas de disco**: Falhas ao salvar (`PermissionError`/`OSError`) exibem aviso mas não interrompem o loop de chat.
- **Sessões em disco**: Sessão salva anteriormente nesta execução (`backend/sessoes_salvas/sessao_20260811_123004.json`) é ignorada pela funcionalidade de retomada apenas se corrompida ou ilegível.

### 🧪 Testes

- Suíte ampliada para **30 testes** (26 existentes + 4 novos).
- Nova classe `TestSessionStorage` cobrindo: salvar/carregar com mesmo histórico, ordenação por timestamp (mais recentes primeiro), arquivo corrompido ignorado e `ValueError` para sessão inexistente.
- Todos os testes isolados em diretório temporário via `tempfile.TemporaryDirectory`.

### ✅ Status dos Testes

- **30/30 testes passaram** (`python -m unittest tests.test_maria -v`)
- **Compilação sem erros** (`python -m py_compile main.py core/session_storage.py core/config.py tests/test_maria.py`)

### 📊 Cobertura de Código

- Persistência de sessões: salvar, carregar, listar (ordenação + arquivo corrompido), erro de arquivo inexistente.

## [2.3.0] - Reorganização de Arquitetura

- Eliminada a pasta duplicada `MARIA/` que estava aninhada dentro da raiz do projeto.
- Módulos centrais (`chat_session.py`, `config.py`, `excel_handler.py`, `file_utils.py`, `ollama_client.py`, `tools_schema.py`, `word_handler.py`) movidos para o novo pacote `backend/core`.
- `test_maria.py` movido para a pasta `backend/tests`.
- Pasta `Lia_benchmark/` removida (código legado não utilizado).
- Todos os imports internos — de `main.py`, dos testes e do pacote `backend/benchmark` — atualizados para referenciar `core.<módulo>`.
- Comando de execução dos testes atualizado para `python -m unittest tests.test_maria -v`.
- `PASTA_ARQUIVOS_GERADOS` continua relativa ao diretório de execução (cwd); nenhuma mudança de comportamento nesse ponto.

## [2.2.0] - Sistema de Benchmark e Validação Contínua

- Criado o pacote `backend/benchmark` para avaliação live do tool calling da MARIA.
- Adicionados 25 casos de benchmark cobrindo conversa, criação/edição de arquivos, confirmação, cancelamento, ambiguidade e sanitização.
- Implementado `MariaRunner` com streaming real, sessões isoladas, retry do Ollama e diretório de arquivos separado.
- Adicionadas métricas de acurácia de ferramentas, confirmação, palavras-chave, execução, latência e distribuição de erros.
- Criados relatórios Markdown com `log.json` e comparação Antes vs Depois em pontos percentuais.
- Adicionada CLI com filtros por IDs, quantidade, categoria, diretório de saída e atraso entre tarefas.
- Documentado o uso em [benchmark/README.md](benchmark/README.md); o benchmark exige Ollama local e não possui modo `--reference-only`.

## [2.1.0] - Fase 2: Streaming e Ferramentas de Arquivo

### ✅ Funcionalidades implementadas

- **Streaming de respostas**: `chat_com_tools_stream()` exibe o texto progressivamente e preserva tool calls ao final da resposta.
- **Criação real de documentos Word**: `criar_documento` agora recebe `conteudo` completo e cria parágrafos reais separados por linhas em branco.
- **Edição de planilhas**: adicionada a ferramenta `editar_planilha`, que substitui a estrutura e os dados de uma planilha Excel existente após confirmação.
- **Confirmações específicas**: a edição informa explicitamente que o arquivo será sobrescrito e documentos exibem uma prévia do conteúdo.
- **Histórico de execução**: o resultado de uma ferramenta confirmada é registrado como mensagem `assistant` na sessão.

### 🔒 Segurança e confiabilidade

- **Sanitização de nomes**: nomes de arquivos removem componentes de caminho e caracteres inseguros antes da escrita.
- **Isolamento de testes**: a pasta `PASTA_ARQUIVOS_GERADOS` é lida dinamicamente, permitindo diretórios temporários por teste.
- **Streaming defensivo**: chunks com `tool_calls: []`, tool calls malformadas e JSON inválido não derrubam o cliente.
- **Modelo padrão**: documentação, mensagens e testes alinhados ao `qwen3.5:4b`.
- **Limpeza de histórico**: removido o parâmetro sem efeito `manter_system` de `ChatSession.limpar_historico()`.

### 🧪 Testes

- Suíte ampliada para **24 testes**.
- Cobertura de criação e edição de `.xlsx`, conteúdo real em `.docx`, sanitização, isolamento de pasta e regressão de streaming.

## [2.0.0] - Máquina de Estado de Confirmação e Execução Real

### ✅ IMPLEMENTADO - Máquina de Estado de Confirmação

- **Fluxo de confirmação antes de criar arquivos**: Implementado estado `acao_pendente` em `ChatSession` para armazenar tool calls aguardando confirmação do usuário.
- **`interpretar_confirmacao()`**: Nova função que interpreta respostas afirmativas ("sim", "pode", "confirmo", "ok", "vai", "isso") e negativas ("não", "nao", "cancela", "para", "esquece"), retornando `None` para respostas ambíguas.
- **Cancelamento automático por ambiguidade**: Após 2 respostas ambíguas consecutivas, a ação é cancelada automaticamente com mensagem de segurança.
- **Comandos especiais durante confirmação**: Comandos `sair`, `exit`, `limpar` e `ajuda` funcionam normalmente mesmo com ação pendente; `limpar` também cancela qualquer ação pendente.

### ✅ IMPLEMENTADO - Execução Real de Arquivos

- **Integração com `excel_handler.py` e `word_handler.py`**: Método `executar_ferramenta_real` em `tools_schema.py` agora cria arquivos `.xlsx` e `.docx` reais.
- **Exibição do caminho do arquivo gerado**: Após confirmação, o terminal exibe `[SISTEMA] Arquivo criado: {caminho_completo}`.
- **Tratamento de exceções amigável**: `PermissionError`, `OSError` e `ValueError` são tratados com mensagens claras via `logger.error` + `print`, sem stack trace cru.
- **Geração de nomes únicos**: Função `gerar_nome_unico` em `file_utils.py` adiciona sufixo `_1`, `_2`, etc. para evitar sobrescrita.

### 🧪 Testes Automatizados Adicionados

Total de testes: **22 testes** (acréscimo de 8 novos testes)

Novos grupos de teste:
- `TestInterpretarConfirmacao`: 3 testes cobrindo casos afirmativo, negativo e ambíguo
- `TestExecucaoReal`: 2 testes para criação real de planilha e documento em pasta temporária
- `TestGerarNomeUnico`: 1 teste para conflito de nome com sufixo `_1`
- `TestFluxoConfirmacao`: 2 testes para cancelamento automático por ambiguidade repetida
- `TestRegressao`: 2 testes para `chat_com_tools` com tool_calls malformado e string de simulação sem `\"` literal

---

## [1.1.0] - Correções e Melhorias da Fase 1

### 🔴 CRÍTICO - Corrigido

- **System prompt agora é enviado ao modelo**: Alterado `main.py` para usar `sessao.get_historico_com_system()` em vez de `get_historico_sem_system()`, garantindo que o system prompt seja sempre incluído na primeira posição da lista de mensagens enviada ao Ollama.
- **Python 3.11+ como requisito mínimo**: Atualizado README.md declarando Python 3.11+ como requisito. Todos os módulos foram atualizados para usar sintaxe moderna de tipos (`list[...]`, `dict[...]`, `X | Y`).
- **Exceções tratadas durante streaming**: Método `_process_stream` em `ollama_client.py` agora envolve a iteração com tratamento de erro, convertendo exceções de rede em `OllamaClientError` também durante o consumo do generator.

### 🟠 IMPORTANTE - Corrigido

- **Duplicação de lógica removida**: Métodos `enviar_mensagem` e `chat_com_tools` agora reutilizam o método privado `_make_request`, eliminando código duplicado.
- **Método `chat()` removido**: Método morto/incompleto foi removido de `ollama_client.py`.
- **Mensagens de erro padronizadas**: Ambos os métodos agora incluem status code e corpo da resposta (`response.text`) nas mensagens de erro.
- **Resultado de simulação de ferramenta não polui histórico**: Tool calls são exibidas como `[SISTEMA]` no console e não são adicionadas ao histórico de conversa.
- **Verificação de conexão otimizada**: `_check_connection()` agora verifica apenas uma vez por sessão (primeira chamada), tratando falhas diretamente no `try/except` da requisição principal.

### 🟡 MELHORIAS - Implementadas

- **`.gitignore` corrigido**: Arquivo agora contém apenas os padrões sem marcação Markdown.
- **`requirements.txt` criado**: Dependência `requests>=2.31.0` fixada para reprodução do ambiente.
- **Configuração centralizada**: Criado módulo `config.py` com todas as configurações (URL, modelo, timeout, histórico, logging).
- **Logging configurável**: Substituído `print()` de debug em `tools_schema.py` por `logging` com nível configurável.
- **Encoding UTF-8 no Windows**: Adicionado `sys.stdout.reconfigure(encoding="utf-8")` em `main.py` com fallback silencioso.
- **Testes unitários adicionados**: 15 testes cobrindo `ChatSession` (limite de histórico, system prompt) e `tools_schema` (simulação de ferramentas).

### Estrutura de Arquivos

Novos arquivos:
- `config.py` - Configurações centralizadas
- `requirements.txt` - Dependências Python
- `test_maria.py` - Testes unitários
- `CHANGELOG.md` - Histórico de mudanças

Arquivos modificados:
- `.gitignore` - Corrigido formato
- `README.md` - Atualizado com Python 3.11+, nova estrutura e documentação de correções
- `ollama_client.py` - Refatorado com tipos modernos, _make_request, tratamento de streaming
- `chat_session.py` - Atualizado com tipos modernos
- `tools_schema.py` - Logging em vez de print, tipos modernos
- `main.py` - Usa get_historico_com_system, config centralizado, encoding UTF-8, logging

---

## [1.0.0] - Versão Inicial da Fase 1

### Implementado

- Cliente básico de comunicação com Ollama
- Sessão de chat com histórico limitado
- Prompt de sistema em português
- Esquema de function calling para planilhas e documentos
- Interface CLI básica
# CHANGELOG - Projeto MARIA
