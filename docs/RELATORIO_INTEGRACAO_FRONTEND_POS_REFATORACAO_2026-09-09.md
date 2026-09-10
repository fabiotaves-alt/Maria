# Relatório Técnico — Integração Backend → Frontend (pós-refatoração) + Nova Seção Análise de Desempenho

**Data:** 2026-09-09
**Branch base:** `chore/auditoria-documentacao-2026-09-09`
**Versão backend:** v4.2.5-dev · **Suíte:** 265 passed · **Baseline benchmark:** B0.5 (28 tasks, 3B e 7B)
**Escopo:** mapear tudo que funciona no backend hoje e precisa funcionar no frontend Tauri após a refatoração hexagonal, + especificar a nova seção Análise de Desempenho na interface principal.
**Fontes vivas:** `backend/bridge/comandos.py`, `backend/bridge/servidores.py`, `backend/application/maria_controller.py`, `backend/benchmarks/maria_bench/`, `frontend-tauri/src/`, `frontend-tauri/src-tauri/src/main.rs`, `shared/schema.sql`, `docs/dev_senior/plano_mestre_v5.md`.

---

## 1. Objetivo e premissa

Garantir que **tudo que funciona no backend via bridge hoje funcione no frontend Tauri após a refatoração**, + criar **seção Análise de Desempenho embutida na interface principal** consumindo o benchmark real, hoje acessível só via CLI (`backend/ui_terminal.py` → menu `2. Avaliação de Desempenho` → `run_benchmark_programatico()`).

**Premissas obrigatórias (pós-refatoração hexagonal Fase 1-4):**

1. Todo código novo no backend deve importar dos ports (`backend.domain.*`, `backend.application.*`, `backend.infrastructure.*`, `backend.interfaces.*`), nunca `backend.core.*` direto. Exceção atual a eliminar: `backend/benchmarks/maria_bench/analysis/report.py:6` importa `LLAMA_NUM_CTX` de `backend.core.config`.
2. Contrato de transporte congelado: `POST /chat` com `{id, comando, dados}` → `{id, status, dados, mensagemErro}` (campo é `dados`, não `payload` — `main.rs::PythonRequest` já usa `dados`; docstring antiga de `_modo_bridge` ainda cita `payload`).
3. Nomes de modelo canônicos: `qwen2.5-omni-3b` / `qwen2.5-omni-7b`. Remover `qwen3b/llama7b/8B` do TS.
4. Nenhum push/commit neste relatório — documento apenas (pedido explícito).

---

## 2. Inventário do backend — o que precisa funcionar no frontend

### 2.1 Protocolo bridge (`backend/bridge/comandos.py::_COMANDOS` — 21 comandos)

| # | Comando | Arquivo:linha | Payload | Retorno `dados` | Cobertura teste |
|---|---|---|---|---|---|
| 1 | `ping` | `comandos.py:76` | `{}` | `"pong"` | ✅ `useMariaBridge.test.ts` + Rust |
| 2 | `status` | `comandos.py:80` | `{}` | `{cpu, ram, gpu, plataforma, modelo}` | ✅ parcial (mock no Rust) |
| 3 | `chat` | `comandos.py:259` | `{mensagem: string}` | texto final (stream coletado; pergunta de confirmação se tool de escrita) | ✅ parcial (sem UI de confirmação) |
| 4 | `limpar_conversa` | `comandos.py:274` | `{}` | `"conversa limpa"` | ✅ backend |
| 5 | `exportar_conversa` | `comandos.py:282` | `{formato?: 'json'|'txt'}` | `"Exportado: <path>"` | ✅ BUG-4 corrigido |
| 6 | `listar_sessoes` | `comandos.py:292` | `{}` | `[{nome_arquivo, caminho, qtd_mensagens}]` | ✅ |
| 7 | `carregar_sessao` | `comandos.py:300` | `{nome: string}` | `[{role, conteudo}]` | ✅ BUG-1 corrigido |
| 8 | `analisar_arquivo` | `comandos.py:86` | `{caminho: string}` | resumo txt/md/csv/log/docx ou `ler_planilha_resumo` p/ xlsx | ✅ |
| 9 | `analisar_dados` | `comandos.py:110` | `{caminho: string}` | resumo planilha | ✅ BUG-5 corrigido |
| 10 | `upload_arquivo` | `comandos.py:132` | `{caminho: string}` | `"Arquivo copiado para: ..."` (limite 100 MB, anti-colisão) | ✅ |
| 11 | `transcrever_audio` | `comandos.py:170` | `{caminho: string}` | transcrição whisper.cpp (`WHISPER_ALLOWED_DIR`, timeout 60 s) | ✅ |
| 12 | `salvar_memoria` | `comandos.py:314` | `{fato, categoria?, relevancia?}` | `"memória salva"` | ✅ |
| 13 | `listar_memoria` | `comandos.py:328` | `{}` | `[{id, fato, categoria, relevancia}]` | ✅ BUG-7 corrigido (`id` incluído) |
| 14 | `deletar_memoria` | `comandos.py:341` | `{id: number}` | `"memória deletada"` | ✅ |
| 15 | `limpar_memorias` | `comandos.py:353` | `{}` | `"memórias limpas"` | ✅ |
| 16 | `criar_automacao` | `comandos.py:365` | `{nome, descricao?, passos, gatilho?, acao?}` | `"automação criada"` | ✅ BUG-2 corrigido |
| 17 | `listar_automacoes` | `comandos.py:395` | `{}` | `[{id, nome, descricao, passos, gatilho, ativa, criado_em}]` | ✅ BUG-3 corrigido |
| 18 | `deletar_automacao` | `comandos.py:410` | `{id: number}` | `"automação deletada"` | ✅ |
| 19 | `toggle_automacao` | `comandos.py:425` | `{id: number}` | `{ativa: bool}` | ✅ BUG-3 corrigido |
| 20 | `encerrar` | `comandos.py:268` | `{}` | `"encerrando"` | ✅ |
| 21 | Fluxo confirmação | `application/maria_controller.py:99-253` | implícito no `chat` | `tem_acao_pendente()` → `get_mensagem_confirmacao()` → `processar_confirmacao('sim'/'não')` p/ `criar_planilha|criar_documento|editar_planilha` | ✅ |

Detalhe do fluxo `chat` (`comandos.py:259-266`): chama `controller.processar_mensagem_stream(mensagem)` e coleta o stream em `resposta_final`; se `tem_acao_pendente()`, retorna a pergunta de confirmação em vez de executar. A confirmação do turno seguinte passa pelo mesmo `chat` (usuário responde `sim`/`não`).


## 3. Estado atual do frontend — o que existe vs. morto/mock

Shell fixo `src/App.tsx` = `TopBar + Sidebar + CenterStage + ChatPanel`, sem roteamento nem estado de view.

| Area | Arquivos | Estado | Problema (evidencia) |
|---|---|---|---|
| Chat | `ChatPanel/index.tsx`, `hooks/useMariaBridge.ts`, `main.rs::send_message/get_status/get_chat_history/save_message` | Parcial | `ChatResponse.modelo_usado: 'qwen3b'\|'llama7b'` incompativel: backend retorna **string pura**, `JSON.parse(raw)` cai sempre no `catch` → fallback `qwen3b` (`useMariaBridge.ts:24-37`); confirmacao pendente vira texto corrido, sem card dedicado; `save_message` Rust escreve no SQLite em paralelo ao Python (WAL ok, mas sem contrato unico) |
| Sidebar nav (8 itens) | `Sidebar/index.tsx:24-33` | 7/8 mortos | `arquivos, analise, visao, voz, memoria, automacoes, config` so fazem `setActiveItem` sem trocar view; footer `MARIA v0.1.0` vs real `4.2.5` (`Sidebar/index.tsx:171`) |
| Recursos sistema | `Sidebar/index.tsx:46-65` | Funciona | Polling `getSystemStatus()` a cada 2 s ok; cai para mock silencioso quando offline |
| CenterStage | `CenterStage/index.tsx`, `ActionBar.tsx`, `FeatureCard.tsx` | Estatico | 4 botoes `ActionBar` **sem `onClick`** (`ActionBar.tsx:43-48`); deveriam disparar `analisar_arquivo/analisar_dados/chat/transcrever_audio` |
| ChatInput | `ChatPanel/ChatInput.tsx` | Parcial | Botoes `Paperclip` e `Mic` sem handler (`ChatInput.tsx:28-56`); input so texto |
| TopBar | `TopBar/index.tsx` | Ok janela/tema | Badge `MODO LOCAL` estatico — deveria refletir `/health` |
| Bridge TS | `useMariaBridge.ts` (4 fns) | Incompleto | **17/21 comandos sem wrapper**; zero tipos p/ memoria/automacao/sessao/arquivo/audio/health/benchmark |
| Rust bridge | `main.rs:48-93,111-223` | HTTP+token ok | `get_status` retorna **mock `18/42/11%`** em fallback silencioso (`main.rs:73-80`) — mascara backend offline; `read_file/save_file` genericos fora das pastas permitidas (bypass de `file_utils`); paths `../shared/maria.db` + `../shared/.bridge_token` frageis (cwd-dependente, `main.rs:114,185`); `send_message` bloqueante sem timeout (chat pode levar 300 s/chamada) |
| Testes | `useMariaBridge.test.ts` (1 teste `pingBackend`) | Cobertura ~0 | vs 265 testes backend; `cargo test` tem 1 teste |
| Versoes | `package.json` + `tauri.conf.json` + `Cargo.toml` = `4.0.0` | Desatualizado | vs `pyproject.toml` `4.2.5` |

### 2.2 Transporte (`backend/bridge/servidores.py`)

## 4. Matriz de integracao — o que ligar (por fase)

| ID | Backend | Frontend hoje | Acao |
|---|---|---|---|
| F1.1 | `chat` + confirmacao (`application/maria_controller.py:99-253`) | texto corrido | Card `Acao pendente` em `MessageBubble`: mostra ferramenta + args + `[Confirmar][Cancelar]` → reenvia `sim`/`nao` via `chat`; exibir `cadeia_ferramentas` quando houver leitura encadeada |
| F1.2 | `status` + `GET /health` | polling c/ mock | Remover mock `18/42/11` (`main.rs:73-80`); tipar `SystemStatus{cpu,ram,gpu,plataforma,modelo,versao}`; badge TopBar `healthy/degraded/offline`; `getSystemStatus` tenta `/health` primeiro, `/chat status` como fallback |
| F1.3 | Nomes de modelo | `qwen3b/llama7b`, `Qwen 2.5 3B` hardcoded | Unificar `qwen2.5-omni-3b/7b` em `ChatPanel:22,49,85`, `Sidebar:159`, `useMariaBridge:27-35,55,64`, `main.rs:78,89` |
| F2.1 | `listar_sessoes/carregar_sessao/limpar_conversa/exportar_conversa` | `getChatHistory(1)` fixo | Seletor de conversas no header do `ChatPanel` + botoes retomar/limpar/exportar (paridade com `InterfaceTerminal._retomar_sessao`, `ui_terminal.py:523-556`) |
| F2.2 | `analisar_arquivo/analisar_dados/upload_arquivo` | `ActionBar` + `Paperclip` mortos | `ActionBar` com `onClick` reais + `Paperclip` → `dialog.open` (plugin `tauri-plugin-dialog` ja declarado no `Cargo.toml:14`) → `upload_arquivo` → `analisar_*`; resumo em bubble com link do arquivo |
| F3.1 | `transcrever_audio` | `Mic` morto | `Mic` → seletor `.wav` → comando; exibir transcricao + aviso `WHISPER_ALLOWED_DIR`; futuro: gravacao via `navigator.mediaDevices` |
| F3.2 | `salvar/listar/deletar/limpar_memoria` | item `memoria` morto | View `MemoriaView`: tabela `[{id, fato, categoria, relevancia}]` + criar/deletar/limpar (usa `id` — BUG-7 ja garante) |
| F3.3 | `criar/listar/deletar/toggle_automacao` | item `automacoes` morto | View `AutomacoesView`: tabela + form (`nome, descricao, passos, gatilho, acao`) + toggle `ativa` (BUG-2/3 corrigidos) |
| F4.1 | `configuracoes` (`shared/schema.sql:77-91`) | item `config` morto | View `ConfigView` + 2 comandos novos `obter_configuracoes/atualizar_configuracao` (hoje so Rust le SQLite direto) |
| F4.2 | `visao/voz` (sem backend) | itens mortos | Marcar `Em breve` explicito ou remover do nav ate existir backend; nao deixar botao morto |
| F4.3 | Versoes | footer `v0.1.0`, pacotes `4.0.0` | Sincronizar com `4.2.5` (ou ler `/health.versao` em runtime) |
| F5 | Benchmark | inexistente | Nova secao Desempenho — secao 5 |

Regra transversal: **toda escrita no SQLite passa pelos comandos Python** (fonte unica); Rust mantem so leitura. Upload/audio sempre via `upload_arquivo` (100 MB, pastas permitidas) — nunca `read_file/save_file` genericos.



## 5. Nova secao Analise de Desempenho (interface principal)

### 5.1 UX — onde entra

9º item no Sidebar (`Desempenho`, icone `Gauge`) → `CenterStage` alterna entre `HomeView` (conteudo atual: logo + FeatureCards + avatar + ActionBar) e `PerformanceView`; **`ChatPanel` permanece visivel** (acompanhar o run sem perder o chat). Alternativa descartada: janela/aba separada — fragmenta o contexto e exige nova capability.

```
Sidebar (260px)          CenterStage (flex-1)              ChatPanel (380px)
[Conversar] .........    HomeView | PerformanceView        (sempre visivel)
...
[Desempenho] <- novo
```

### 5.2 Requisitos funcionais

1. **Configurar run:** modelo (`qwen2.5-omni-3b|7b`, default do `config.py`), selecao de tasks (todas / categoria / IDs — listar via novo comando `listar_tasks_benchmark`), repeticoes (default `BENCHMARK_REPETICOES=2`).
2. **Executar sem travar UI nem Flask** → job assincrono (secao 5.3).
3. **Acompanhar progresso:** `job_id`, `estado` (`queued|running|done|error|cancelled`), `atual/total`, tarefa atual, ETA, tail de log.
4. **Visualizar resultado:** cards (`tool_accuracy`, `confirmation_elegiveis`, `keyword`, `runtime`, `p50/p90`, `TTFT`, `tok/s`, `contexto_ok`, `semantic_quality`, `parse_suspeito`); tabela por categoria; tabela `failed (ID|tarefa|motivo)`; detalhe por execucao (`prompt_enviado` mascarado, `resposta_bruta`, `fallbacks/correcoes`, `cadeia_ferramentas`).
5. **Comparar runs:** seletor `before|after` → delta (base para `compare_runs.py`).
6. **Historico:** listar `results/run_*` (meta: modelo, data, total, tool_acc). `results/` tem ~60 runs hoje — paginar + retencao (ex. ultimos 20).

### 5.3 Contrato novo — 3 comandos bridge (criar pos-refatoracao)

`listar_benchmarks {}` → `{runs: [{run_id, data, modelo, total_tarefas, tool_accuracy, dir}]}` — le `results/*/log.json` **leve** (so `meta` + metricas agregadas, sem `individual[]`).

`executar_benchmark {modelo, task_ids?, categoria?, repeticoes?}` → `{job_id}` — valida llama-server (`GET /v1/models`, 2 s), cria thread unica (409 se job ativo), grava em `results/run_<timestamp>/`. Respeita `BENCHMARK_TASK_TIMEOUT=400 s` / `BENCHMARK_TIMEOUT_POR_CHAMADA=300 s`; cancelamento cooperativo entre tarefas.

`status_benchmark {job_id}` → `{estado, progresso: {atual, total}, tarefa_atual, erro?}`; `resultado_benchmark {run_id, resumo?}` → metricas + categorias + falhas (+ `individual` paginado por `offset/limit`).

Sequencia:

```
UI -> executar_benchmark -> {job_id}
UI -> poll status_benchmark (2 s) -> running 12/56 ...
job done -> resultado_benchmark -> render cards + tabelas
```

### 5.4 Componentes novos (React + Rust + tipos)

- `src/components/PerformanceView/`: `index.tsx` (orquestra), `RunConfigForm.tsx`, `ProgressBar.tsx`, `MetricsCards.tsx`, `CategoryTable.tsx`, `FailuresTable.tsx`, `ExecutionDetail.tsx`, `CompareRuns.tsx`.

## 6. Riscos e bloqueios pos-refatoracao (decisoes necessarias)

1. **Imports:** novos comandos devem importar de `backend.application|infrastructure|interfaces|domain`, nunca `backend.core.*`. Debito atual: `analysis/report.py:6` importa `LLAMA_NUM_CTX` de `core.config` — mover para `benchmark_config.py` (ja absorvido em B2) antes de expor via bridge.
2. **Campo do protocolo:** congelar em `dados` (Rust ja usa). Atualizar docstring de `_modo_bridge` (`servidores.py:30-44`) que ainda documenta `payload`.
3. **`chat` bloqueante:** ate 300 s/chamada. Frontend precisa de timeout + indicador de progresso + botao cancelar (hoje `send_message` espera o texto final sem feedback).
4. **Confirmacao ambigua:** `processar_confirmacao` retorna `(None, ...)` e conta `tentativas_confirmacao_ambigua` (cancela apos 2). UI deve tratar os 3 estados (`true|false|None`), nao so ok/erro.
5. **Upload/audio:** passar por `upload_arquivo` (100 MB, pastas permitidas, anti-colisao). Desativar ou restringir `read_file/save_file` genericos do Rust.
6. **Concorrencia SQLite:** `WAL + busy_timeout=5000 + check_same_thread=False` ok; mesmo assim, centralizar escrita no Python (`TODO_MELHORIAS_BACKEND.md#3` propoe `threading.local` — nao bloqueia a integracao).
7. **Token/CSP/capability:** manter `127.0.0.1:8081`; CSP do `tauri.conf.json` ja libera; capability so permite `--bridge-http --porta 8081`.
8. **Plano mestre v5:** fases B3 (SQLite WAL + report v2 + compare SQL), B4 (tasks v2), B5 (CLI), B6 (semantica + LLM-judge) mudam o formato de `log.json`/`report.md` — versionar o contrato (`versao_benchmark: "2.0"` ja existe no `meta`) e a UI deve tolerar campos ausentes.

## 7. Plano de execucao pos-refatoracao (estimativa 30–44 h)

| Fase | Escopo | Horas | Aceite |
|---|---|---|---|
| F1 Paridade chat+saude | F1.1 card confirmacao, F1.2 `/health` + remover mock, F1.3 nomes de modelo | 6–8 | `uv run pytest` 265+, `npm run build + npm test + cargo test` verdes, E2E chat c/ `criar_planilha` confirmando na UI |
| F2 Sessoes+arquivos | F2.1 seletor conversas, F2.2 ActionBar+Paperclip funcionais | 6–8 | E2E upload→analise; retomar/limpar/exportar na UI |
| F3 Memoria+automacoes+voz | F3.1 transcricao, F3.2 MemoriaView, F3.3 AutomacoesView | 6–8 | CRUDs na UI batendo com `test_comandos_bridge.py` |
| F4 Config+limpeza | F4.1 ConfigView + 2 comandos, F4.2 `visao/voz`, F4.3 versoes | 3–5 | Sem botao morto; footer/versoes `4.2.5` |
| F5 Desempenho | Secao 5 completa (3 comandos + PerformanceView + polling + comparacao) | 9–15 | E2E run real com 2–3 tasks, progresso ao vivo, `report.md`/`log.json` gerados, comparacao before/after |


## 8. Anexos — contratos JSON exatos

### 8.1 `POST /chat` (existente, reutilizado por F1–F4)

Request: `{"id": "<uuid>", "comando": "chat", "dados": {"mensagem": "<texto>"}}` + header `Authorization: Bearer <token>`.
Response ok: `{"id": "<uuid>", "status": "ok", "dados": "<texto-final>", "mensagemErro": null}`.
Response erro: `{"id": "<uuid>", "status": "erro", "dados": null, "mensagemErro": "<motivo>"}`.

### 8.2 `GET /health` (existente, hoje nao consumido)

Response (HTTP 200 sempre): `{"status": "healthy|degraded", "timestamp": "<iso>", "checks": {"llama_server": {"ok": bool, "latencia_ms": n}, "banco_dados": {"ok": bool}, "disco": {"ok": bool, "livre_gb": n}}, "versao": "4.2.5", "modelo": "qwen2.5-omni-3b"}`.

### 8.3 Novos comandos F5 (a implementar)

`executar_benchmark`: `{"comando": "executar_benchmark", "dados": {"modelo": "qwen2.5-omni-3b", "task_ids": [1, 2, 3], "repeticoes": 2}}` → `{"dados": {"job_id": "<uuid>"}}` ou 409 `{"mensagemErro": "job em andamento"}`.
`status_benchmark`: `{"dados": {"job_id": "<uuid>"}}` → `{"dados": {"estado": "running", "progresso": {"atual": 12, "total": 56}, "tarefa_atual": "Planilha basica", "erro": null}}`.
`resultado_benchmark`: `{"dados": {"run_id": "run_20260908_161120", "resumo": true}}` → `{"dados": {"meta": {...}, "metricas": {"tool_accuracy": 0.821, ...}, "por_categoria": [...], "falhas": [...]}}`.

## 9. Referencias obrigatorias antes de implementar

Backend: `backend/bridge/comandos.py`, `backend/bridge/servidores.py`, `backend/application/maria_controller.py`, `backend/benchmarks/maria_bench/run_benchmark.py`, `.../tasks/task_schema.py`, `.../analysis/metrics.py`, `.../analysis/report.py`, `backend/ui_terminal.py` (menu avaliacao = spec de comportamento), `shared/schema.sql`.
Frontend: `frontend-tauri/src/App.tsx`, `.../Sidebar/index.tsx`, `.../CenterStage/index.tsx`, `.../ChatPanel/index.tsx`, `.../hooks/useMariaBridge.ts`, `.../src-tauri/src/main.rs`, `.../capabilities/default.json`.
Planos: `docs/dev_senior/plano_mestre_v5.md`, `docs/PROGRESSO_DESENVOLVIMENTO.md`, `CHANGELOG.md`.

Ordem obrigatoria: F1 → F2 → F3 → F4 → F5 (cada fase verde antes da proxima; F5 depende do job assincrono estavel). Validacao final: dev (`--bridge-http`) + instalador (sidecar) + `pytest backend/tests` + `npm run build + npm test` + `cargo test`.

| F2 Sessoes+arquivos | F2.1 seletor conversas, F2.2 ActionBar+Paperclip funcionais | 6–8 | E2E upload→analise; retomar/limpar/exportar na UI |
| F3 Memoria+automacoes+voz | F3.1 transcricao, F3.2 MemoriaView, F3.3 AutomacoesView | 6–8 | CRUDs na UI batendo com `test_comandos_bridge.py` |
| F4 Config+limpeza | F4.1 ConfigView + 2 comandos, F4.2 `visao/voz`, F4.3 versoes | 3–5 | Sem botao morto; footer/versoes `4.2.5` |
| F5 Desempenho | Secao 5 completa (3 comandos + PerformanceView + polling + comparacao) | 9–15 | E2E run real com 2–3 tasks, progresso ao vivo, `report.md`/`log.json` gerados, comparacao before/after |

Ordem obrigatoria: F1 → F2 → F3 → F4 → F5 (cada fase verde antes da proxima; F5 depende do job assincrono estavel). Validacao final: dev (`--bridge-http`) + instalador (sidecar) + `pytest backend/tests` + `npm run build + npm test` + `cargo test`.

## 8. Anexos — contratos JSON exatos

### 8.1 `POST /chat` (existente, reutilizado por todo F1–F4)

Request: `{"id": "<uuid>", "comando": "chat", "dados": {"mensagem": "<texto>"}}` — header `Authorization: Bearer <token>`.
Response ok: `{"id": "<uuid>", "status": "ok", "dados": "<texto-final>", "mensagemErro": null}`.
Response erro: `{"id": "<uuid>", "status": "erro", "dados": null, "mensagemErro": "<motivo>"}`.

### 8.2 `GET /health` (existente, hoje nao consumido)

Response: `{"status": "healthy|degraded", "timestamp": "<iso>", "checks": {"llama_server": {"ok": bool, "latencia_ms": n}, "banco_dados": {"ok": bool}, "disco": {"ok": bool, "livre_gb": n}}, "versao": "4.2.5", "modelo": "qwen2.5-omni-3b"}` — HTTP 200 sempre.

### 8.3 Novos comandos F5 (a implementar)

`executar_benchmark`: `{"id": "<uuid>", "comando": "executar_benchmark", "dados": {"modelo": "qwen2.5-omni-3b", "task_ids": [1, 2, 3], "repeticoes": 2}}` → `{"status": "ok", "dados": {"job_id": "<uuid>"}}` ou `409 {"status": "erro", "mensagemErro": "job em andamento"}`.

`status_benchmark`: `{"dados": {"job_id": "<uuid>"}}` → `{"dados": {"estado": "running", "progresso": {"atual": 12, "total": 56}, "tarefa_atual": "Planilha basica", "erro": null}}`.

`resultado_benchmark`: `{"dados": {"run_id": "run_20260908_161120", "resumo": true}}` → `{"dados": {"meta": {...}, "metricas": {"tool_accuracy": 0.821, "confirmation_elegiveis": 0.935, "p50_ms": 9338.8, "p90_ms": 32575.7, ...}, "por_categoria": [...], "falhas": [...]}}`.

## 9. Arquivos de referencia (leitura obrigatoria antes de implementar)

Backend: `backend/bridge/comandos.py`, `backend/bridge/servidores.py`, `backend/application/maria_controller.py`, `backend/benchmarks/maria_bench/run_benchmark.py`, `backend/benchmarks/maria_bench/tasks/task_schema.py`, `backend/benchmarks/maria_bench/analysis/metrics.py`, `backend/benchmarks/maria_bench/analysis/report.py`, `backend/ui_terminal.py` (menu avaliacao como spec de comportamento), `shared/schema.sql`.
Frontend: `frontend-tauri/src/App.tsx`, `frontend-tauri/src/components/Sidebar/index.tsx`, `frontend-tauri/src/components/CenterStage/index.tsx`, `frontend-tauri/src/components/ChatPanel/index.tsx`, `frontend-tauri/src/hooks/useMariaBridge.ts`, `frontend-tauri/src-tauri/src/main.rs`, `frontend-tauri/src-tauri/capabilities/default.json`.
Planos: `docs/dev_senior/plano_mestre_v5.md`, `docs/PROGRESSO_DESENVOLVIMENTO.md`, `CHANGELOG.md`.

- `src/hooks/useBenchmark.ts`: `listarBenchmarks()`, `executarBenchmark(cfg)`, `pollStatus(job_id)`, `obterResultado(run_id)` (polling 2 s, abort em unmount).
- `src/types/benchmark.ts`: `BenchmarkMetrics`, `BenchmarkRun`, `TaskResult`, `BenchmarkJob` espelhando `tasks/task_schema.py` + `analysis/metrics.py` (snake_case no Python → camelCase no TS na borda do hook).
- `main.rs`: +3 commands (`list_benchmarks`, `run_benchmark`, `benchmark_status`/`benchmark_result`) via `call_python_backend` — sem parsing novo em Rust, so repasse.
- Testes: Vitest (polling, parse `log.json`, estados) + `cargo test` (repasse) + E2E manual com 2–3 tasks.

### 5.5 Trade-offs decididos

- **Job em thread Flask (recomendado)** vs processo separado vs CLI sincrono: thread reaproveita `run_benchmark_programatico` e `log.json` incremental; processo escala melhor mas exige IPC; sincrono trava UI — descartado.
- **Leitura via Python (recomendado)** vs Rust direto no `results/`: Python mantem regra de negocio + auth num lugar; Rust direto duplica parsing e fura auth.
- **`CenterStage` condicional (recomendado)** vs rota nova: condicional preserva `ChatPanel` visivel e minimiza refactor (estado `activeView` no `App.tsx`).

- `POST /chat` autenticado (`Bearer` em `frontend-tauri/shared/.bridge_token`, escrita atomica). `main.rs::call_python_backend()` (`main.rs:177-223`) rele o token a cada chamada — manter.
- `GET /ping` e `GET /health` abertos. `/health` retorna `{status, checks: {llama_server, banco_dados, disco}, versao, modelo}` (`servidores.py:174-242`, testes em `test_health_http.py`). **Nenhum codigo do frontend consome `/health`** — perda direta de observabilidade (ver F1.2).
- Bind `127.0.0.1:8081`, CORS por `MARIA_ENV`. Capability `default.json` restringe o sidecar a `["--bridge-http", "--porta", "8081"]` — se o benchmark virar subcomando CLI, estender `args`.
- Sidecar producao: `main.rs:225-268` spawna `maria-backend --bridge-http` e mata no close. Dev: `uv run python backend/main.py --bridge-http`.

### 2.3 Benchmark real (`backend/benchmarks/maria_bench/`)

- **Runner:** `runners/maria_runner.py` + `run_benchmark.py::run_benchmark_programatico(modelo, task_ids, repeticoes, metricas_sistema)` (`run_benchmark.py:666`). CLI: `--task-ids/--tasks/--category/--output-dir/--delay/--repeticoes/--num-predict`.
- **Catalogo:** `tasks/__init__.py::load_all_maria_tasks()` = CORE+EDGES+EXTRACAO, 28 tasks com IDs unicos (Task 26 traducao redesenhada em FIX-1/2/3).
- **Metricas** (`analysis/metrics.py`): `tool_accuracy`, `confirmation_success_rate (+_elegiveis)`, `keyword_match_rate`, `runtime_success_rate`, `avg/p50/p90_latency_ms`, `avg_ttft_ms`, `avg_tokens_por_segundo`, `language_compliance_rate`, `args_accuracy`, `contexto_ok_rate`, `semantic_quality_rate + by_type`, `parse_suspeito_count`, `correcoes_count`, `by_category`.
- **Artefatos:** `results/run_*/report.md` + `log.json` (`meta` com sampler_params/warmup/`metricas_sistema`; `individual[]` com `prompt_enviado`, `resposta_bruta_modelo`, `fallbacks`, `correcoes`, `cadeia_ferramentas`; `agregado_por_tarefa`).
- **Baseline:** `results/run_baseline_v5_3b|_7b` (B0.5). Ex. 3B: 56 execs, tool 82.1%, conf-elegiveis 93.5%, keyword 83.9%, runtime 96.4%, idioma 100%, 3.5 tok/s, TTFT 3.6s, p50 9.3s/p90 32.5s.
- **Gap critico:** zero comandos bridge expoem o benchmark. `ui_terminal.py:441-593` e CLI-bloqueante — **nao reutilizavel no Flask**; extrair job assincrono (secao 5.3).

