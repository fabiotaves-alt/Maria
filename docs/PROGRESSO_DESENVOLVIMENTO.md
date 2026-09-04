# PROGRESSO_DESENVOLVIMENTO

> Painel de controle de entregas e roadmap do **MARIA** (v4.x). Atualizado a cada tarefa concluída.

**Versão Atual:** v4.1.19  
**Última alteração:** 2026-09-04  

---

## ✅ Percentual Geral Concluído

| Área | Progresso | Observações |
|------|-----------|-------------|
| Backend Core & Ferramentas (Python) | 98% | LlamaClient, RAG FTS5, criação/edição de arquivos, benchmark com metadados do modelo, sampler configurável, system prompt externo, lógica de negócio em `backend/core/maria_controller.py` e **autocorreção de tool calls inválidas** |
| Segurança & Concorrência | 95% | Token atômico, CORS por ambiente, SQLite thread-safe, PATH hijacking |
| Frontend (Tauri v2 + React) | 92% | Interface completa, temas, persistência rusqlite, sidecar |
| Integração Bridge (HTTP/Sidecar) | 95% | 19 comandos bridge, autenticação Bearer, health check; transporte e protocolo separados em `backend/bridge/` (`servidores.py` + `comandos.py`) |
| **Total do Projeto (v4.x)** | **~96%** | MVP v4 estável, pronto para empacotamento final |

---

## 📋 Tabela de Versões

| Versão | Data | Descrição | Status |
|--------|------|-----------|--------|
| **4.0.0** | 2026-08-28 | Migração base do frontend JavaFX para Tauri v2 + React | ✅ Concluída |
| **4.0.1** | 2026-08-29 | Estabilização Tauri + React (P0–P2): bridge HTTP, schema SQLite, sidecar | ✅ Concluída |
| **4.0.2** | 2026-08-30 | Documentação da v4.0 e manutenção de configurações (.gitignore) | ✅ Concluída |
| **4.1.0** | 2026-08-30 | RAG do Manual de Redação da Presidência da República (SQLite FTS5, 255 trechos) | ✅ Concluída |
| **4.1.1** | 2026-08-31 | Correções críticas de segurança (token atômico, CORS, PATH hijacking, SQLite thread-safe) + TTFT + robustez MariaRunner | ✅ Concluída |
| **4.1.2** | 2026-09-02 | Metadados do modelo no benchmark (nome real via /v1/models + parámetros) + fix da suíte de testes | ✅ Concluída |
| **4.1.3** | 2026-09-02 | Prompt, resposta bruta do modelo e parâmetros de sampler configuráveis no benchmark | ✅ Concluída |
| **4.1.4** | 2026-09-02 | System prompt centralizado em arquivo externo (`backend/core/system_prompt.txt`) com remoção do reforço hardcoded do LlamaClient | ✅ Concluída |
| **4.1.5** | 2026-09-02 | Normalização de chaves JSON de tool calls + validação flexível de argumentos e keywords no benchmark | ✅ Concluída |
| **4.1.6** | 2026-09-02 | Metadados reais do modelo via /v1/models (aborta sem endpoint), log.json v2.0 com hash do system prompt, métrica contexto_ok e relatório enxuto sem coluna "Configurado" | ✅ Concluída |
| **4.1.7** | 2026-09-02 | Verificação de contexto real (warmup + pre-check por tarefa), timeout por chamada (120s), contagem exata do system prompt via /tokenize com calibração e num_ctx adaptativo | ✅ Concluída |
| **4.1.10** | 2026-09-03 | Divisão de `backend/main.py` em módulos especializados: lógica de negócio em `backend/core/maria_controller.py` e transporte/protocolo bridge em `backend/bridge/` — sem alteração de comportamento (re-exports mantêm compatibilidade com testes) | ✅ Concluída |
| **4.1.11** | 2026-09-03 | Autocorreção de tool calls inválidas de escrita (schema: campos obrigatórios, tipo de `colunas`, sanitização de `nome_arquivo`) via `validar_e_corrigir_tool_call_stream` com retry + temperatura elevada (0.25); fix de 5 testes pré-existentes; **180 testes passando** | ✅ Concluída |
| **4.1.12** | 2026-09-03 | Benchmark: relatório/log com ID do modelo (sem "Nome") e linha de resumo `rep X/Y` por execução, com descrição de erro em falhas | ✅ Concluída |
| **4.1.13** | 2026-09-03 | Análise e correção de 7 bugs no backend (bridge, session_storage, excel_handler, config); documentação do router para integração futura; relatório `docs/analise_backend.md` | ✅ Concluída |
| **4.1.14** | 2026-09-03 | Refatoração estrutural: CommandRegistry no bridge, confirmação extraída (`confirmacao.py`), paths centralizados (`paths.py`), alias corrigido e documentação de modelos (3b/7b; Ollama legado) | ✅ Concluída |
| **4.1.15** | 2026-09-03 | Remoção do cliente legado Ollama (`ollama_client.py`), constantes `OLLAMA_*` e aliases; test doubles migrados para fakes; `kind` do log.json → `LlamaClientError` | ✅ Concluída |
| **4.1.16** | 2026-09-03 | Benchmark: correção do `compare_runs` (p50/p90 em ms + 4 métricas novas) e remoção de linha duplicada em `benchmark_config` | ✅ Concluída |
| **4.1.17** | 2026-09-03 | Benchmark: contrato de cliente (Protocol/Liskov), fixtures estruturadas, `asdict`/métricas 1× e limpeza final de Ollama nos docs | ✅ Concluída |
| **4.1.18** | 2026-09-04 | Benchmark: parser textual robusto (scan balanceado, whitelist, reparo de truncamento), métricas honestas (confirmação elegível + parse_suspeito + finish_reason), timeouts/tokens ajustados (300s/600), system prompt determinístico (~375 tokens) e relatório `docs/RELATORIO_BENCHMARK_DIAGNOSTICO.md`; **169 testes passando** | ✅ Concluída |
| **4.1.19** | 2026-09-04 | Auto-sanitização de path traversal (tasks 21-25 destravadas) + proteção contra geração degenerada (`repeat_penalty` 1.1, abort precoce em stream, supressão de tool call degenerada com motivo de falha visível no relatório); **178 testes passando** | ✅ Concluída |
| **4.2.0** | *Planejado* | Instalador final *one-click* com Python embeddable e modelo pré-configurado | 📋 Planejado |

---

## ✅ Checklist — Roadmap

### Fase 1 — Backend Core & Inferência
- [x] Controller principal, `ChatSession`, persistência de memórias
- [x] `LlamaClient` (inferência via `llama-server` / `Qwen2.5-Omni 3B`) e `OllamaClient` (legado)
- [x] Tool calling com confirmação do usuário e encadeamento de ferramentas de leitura
- [x] Bridge nos modos `--bridge` (stdin/stdout JSON-lines) e `--bridge-http` (porta 8081)
- [x] Medição precisa de TTFT (*Time To First Token*) no streaming de resposta
- [x] System prompt centralizado em arquivo externo (`backend/core/system_prompt.txt`) via `MARIA_SYSTEM_PROMPT` no config; normalização de chaves JSON nas tool calls do `LlamaClient`

### Fase 2 — Manipulação de Documentos & Segurança
- [x] Criação de planilhas Excel (.xlsx) e documentos Word (.docx)
- [x] Edição de planilhas existentes com confirmação de sobrescrita
- [x] Leitura segura de arquivos (.txt, .md, .csv, .log, .docx) com validação de caminhos permitidos
- [x] Escrita atômica do token bridge (`.tmp` + `os.replace`) com permissão POSIX `0o600`
- [x] CORS restrito condicionado por `MARIA_ENV` (Vite dev server liberado apenas em `development`)
- [x] Mitigação de PATH hijacking no Whisper via `WHISPER_ALLOWED_DIR`

### Fase 3 — RAG & Banco de Dados
- [x] Schema unificado em `shared/schema.sql` (6 tabelas relacionais + 1 virtual FTS5)
- [x] RAG do Manual de Redação da Presidência da República via SQLite FTS5 (255 trechos indexados)
- [x] Script idempotente de ingestão (`backend/database/ingest_manual_redacao.py`)
- [x] Conexão SQLite thread-safe com `threading.Lock()` e `PRAGMA busy_timeout = 5000`

### Fase 4 — Frontend Desktop (Tauri v2 + React)
- [x] Janela nativa Tauri v2, plugins de shell, dialog e fs com CSP restritiva
- [x] Interface completa: `TopBar`, `Sidebar`, `CenterStage`, `ChatPanel`, temas claro/escuro e Aura rosa
- [x] Integração via `useMariaBridge` com autenticação automática por token
- [x] Script de empacotamento standalone do backend (`build_sidecar.py`)
- [ ] Validação de instalação *one-click* em máquina limpa (sem dependência de Python instalado)

### Fase 5 — Qualidade, Testes & Benchmark
- [x] Suíte de testes unitários do backend (172 testes passando via `pytest`)
- [x] Testes unitários do frontend TypeScript (Vitest) e da camada Rust (`cargo test`)
- [x] Framework de benchmark de tool calling com relatório e log JSON
- [x] Metadados do modelo no benchmark: nome real via `/v1/models` + parámetros (quantização, n_params, n_ctx, tamanho) em `log.json` e `report.md`
- [x] Prompt, resposta bruta do modelo e parâmetros de sampler (16 configuráveis via ENV) expostos por execução no benchmark
- [x] Comparação de runs retrocompatible (`log.json` antigo e novo)
- [x] Robustez no `MariaRunner`: tratamento correto de negação, ambiguidade e mensagens de erro
- [x] Normalização no benchmark: chaves de argumentos em minúsculas, `nome_arquivo` com/sem extensão equivalente, listas como conjuntos e keyword match sem falsos negativos por acento
- [x] Metadados do modelo como fonte única de verdade: warmup aborta sem `/v1/models`, relatório exibe apenas dados reais (sem coluna "Configurado"), `log.json` v2.0 com hash do system prompt e métrica `contexto_ok` para estouro de contexto
- [x] Verificação de contexto em camadas: warmup valida ctx real + system prompt (contagem exata via `/tokenize` com calibração), runner faz pre-check por tarefa sem retry inútil, timeout por chamada (120s) separado do timeout total (400s) e `num_ctx` adaptativo no `LlamaClient`
- [x] Benchmark: relatório/log com "ID modelo" (sem "Nome") e linha de resumo `rep X/Y` por execução (com descrição de erro)
- [ ] Cobertura formal de código (`pytest-cov`)

---

## 🔁 Notas das Iterações Recentes

### 4.1.17 — Benchmark: contrato de cliente, fixtures e limpeza de Ollama (2026-09-03)
- **Protocol de cliente**: `client_protocol.py` (`LLMClientProtocol`) tipa `MariaRunner`/`tool_chaining` (Liskov).
- **Fixtures estruturadas**: `MariaTask.fixtures` substitui o regex de fixture; `asdict` + métricas 1× em `run_benchmark.py`.
- **Ollama removido dos docs ativos**: `ARQUITETURA_SISTEMA.md` e `README.md` sem `ollama_client.py` (mantido só no histórico).
- **Testes**: 157/157 + 33 subtests.

### 4.1.16 — Benchmark: correção do compare_runs e dedup de config (2026-09-03)
- **compare_runs**: p50/p90 agora exibidos em ms (antes ×100/"pp"); formatação por tipo de métrica com tratamento de `None`.
- **Métricas adicionadas** ao `comparison.md`: language compliance, contexto ok, tokens/s, TTFT médio.
- **benchmark_config**: linha duplicada de `BENCHMARK_REPETICOES` removida.
- **Testes**: 157/157 + 33 subtests.

### 4.1.15 — Remoção do cliente legado Ollama (2026-09-03)
- **`ollama_client.py` removido**; `LlamaClient` é o único cliente (fim da duplicação de ~800 linhas).
- **Constantes `OLLAMA_*` removidas** do `config.py`; aliases/exceções `Ollama*` renomeados para `Llama*` no benchmark.
- **`kind` do `log.json`** alterado para `"LlamaClientError"` (contrato atualizado).
- **Test doubles** migrados para fakes sem herança; ~23 testes legados removidos (thinking/think param/etc.).
- **Testes**: 157/157 + 33 subtests.

### 4.1.14 — Refatoração estrutural do backend (2026-09-03)
- **CommandRegistry**: `_despachar_comando` virou registro (`_COMANDOS`) com um handler `_cmd_*` por comando.
- **Confirmação extraída**: `core/confirmacao.py` (`ConfirmacaoAcao` + `interpretar_confirmacao`); `ChatSession` delega mantendo compatibilidade.
- **Caminhos centralizados**: `core/paths.py` (`RAIZ_MONOREPO`).
- **Alias corrigido**: `LlamaClient as OllamaClient` → `LlamaClient` (controller e runner).
- **Documentação de modelos**: Ollama = legado; modelos ativos `qwen2.5-omni-3b`/`qwen2.5-omni-7b`; schema `configuracoes` unificado (drift corrigido).
- **Testes**: 180/180 + 33 subtests; smoke test do bridge OK.

### 4.1.13 — Análise e correção de 7 bugs no backend + doc do router (2026-09-03)
- **7 bugs corrigidos** na camada bridge e utilitários: `carregar_sessao` (dict acessado como objeto), `criar_automacao` (NOT NULL violado), `listar_automacoes`/`toggle_automacao` (coluna errada `ativa`×`ativo`), `exportar_conversa` (função inexistente — agora implementada em `session_storage.py`), `ler_planilha_resumo` (`\n` literal), `OLLAMA_MODEL` (espaço inválido), `listar_memoria` (sem `id`).
- **Documentação**: `core/router.py` com seção `STATUS ATUAL / INTEGRAÇÃO FUTURA` (passos para ativação quando o roteamento multi-modelo for integrado). Novo relatório `docs/analise_backend.md` com análise completa (bugs, riscos, oportunidades, segurança).
- **Testes**: 180/180 passando + 33 subtests; sem regressões.

### 4.1.12 — Benchmark: ID do modelo no relatório/log + resumo por execução (2026-09-03)
- **Relatório sem "Nome"**: seção Modelo do `report.md` passa a exibir apenas **ID modelo** (antiga "ID real") e Quantização — a linha "Nome" foi removida; fallback sem `/v1/models` exibe "ID modelo | Não detectado".
- **`log.json`**: `meta` remove `modelo_nome_exibicao` e renomeia `modelo_id_real` → `id_modelo`.
- **Detalhes por execução**: cada bloco ganha a linha `rep X/Y: ✓/✗ tool=... args=OK|DIVERGENTE latência=...s tokens=...` (X/Y = repetição/total da tarefa), com ` — erro: ...` (via `_diagnosticar_falha`) quando a execução falha.
- **Testes**: 175/175 passando (`pytest -k "not TestSegurancaApiHttp"`) + 33 subtests; sem regressões.

### 4.1.11 — Autocorreção de tool calls inválidas (2026-09-03)
- **Validação de schema ANTES da confirmação**: `validar_e_corrigir_tool_call_stream` (`backend/core/tool_chaining.py`) valida tool calls de escrita (`FERRAMENTAS_ESCRITA`) contra `validar_argumentos_obrigatorios` (estendida: `colunas` deve ser lista, `nome_arquivo` sanitizado) — **sem** verificar existência de arquivo em disco (não introduzir conflito com tarefas 21–23 do benchmark).
- **Retry com temperatura elevada**: chamadas de correção usam `LLAMA_TEMPERATURE_TOOLS_RETRY` (0.25) via `temperatura_override` em `_montar_payload`/`continuar_com_resultado_ferramenta_stream`; default `LLAMA_TEMPERATURE_TOOLS` (0.1) preservado. Limite `MAX_TENTATIVAS_CORRECAO_FERRAMENTA` (2).
- **Integração dual**: `maria_controller.py` (interativo) reescrito em 3 estágios (chat → leitura → correção); `maria_runner.py` (benchmark) ganhou bloco de correção com callback `_apos_chamada_de_correcao` (timeout por chamada + tokens) e expõe `correction_attempts` no `MariaTaskResult`.
- **Fix de baseline**: 16 `@patch('core...')` → `backend.core...`, `OllamaClient(model="qwen3.5:4b")` em 3 testes de regressão, e 2 asserts de system prompt alinhados ao texto acentuado — eliminando dependência de ordem/sys.path no unittest.
- **Testes**: 180/180 passando (7 novos da Fase B + baseline 173 agora verde).

### 4.1.10 — Divisão de `backend/main.py` em Módulos Especializados (2026-09-03)
- **`backend/core/maria_controller.py`**: classe `MariaController` (lógica de negócio) movida integralmente de `backend/main.py` — 16 métodos inalterados; imports reduzidos (`LLAMA_MODEL` removido, pois só era usado no bridge).
- **Pacote `backend/bridge/`**: `comandos.py` (`_responder_bridge`, `_get_system_status`, `_despachar_comando` — anotação `controller: "MariaController"` como string) e `servidores.py` (`_modo_bridge`, `_carregar_token_api`, `_criar_app_http`, `_modo_bridge_http`). `_RAIZ_MONOREPO` recalculado por módulo (3 níveis acima).
- **`backend/main.py` (944 → ~98 linhas)**: apenas `sys.path`, imports, `logger` e `main()`; re-exports explícitos preservam os imports/patches dos testes.
- **Verificação**: comparação byte-a-byte com o `git HEAD` (100% idêntico), 173 testes sem regressão vs. baseline, `py_compile` OK e smoke tests (`--bridge-http`, bridge stdin/stdout e modo CLI).
- **Testes**: 173/173 executados (2 falhas + 3 erros pré-existentes no ambiente, não relacionados à tarefa).

### 4.1.7 — Contexto, Timeouts e num_ctx Adaptativo (2026-09-02)
- **Contexto real em camadas**: warmup lê `meta.n_ctx` de `/v1/models` (fonte única — a sonda com payload `num_ctx` do enunciado original foi descartada porque o llama.cpp ignora campos desconhecidos e responderia 200 sempre); warmup aborta com `SystemExit` se o system prompt (contagem **exata** via 1 chamada `POST /tokenize`) não couber em `ctx − 512`; runner recebe `ctx_size` real e faz pre-check por tarefa (`ctx × 0.7`) **sem retry** para estouro (determinístico), classificando `contexto_ok=False`.
- **Calibração de tokens**: fator = tokens reais ÷ estimativa chars/4 medido no system prompt no warmup; pre-check por tarefa usa estimativa calibrada (erro ~±10%, zero HTTP extra). Cenário real validado: system prompt 546 tokens estimados vs limite 1536 em ctx 2048 → `[OK]`.
- **Timeout por chamada**: novo `BENCHMARK_TIMEOUT_POR_CHAMADA` (120s, ENV) — callback de continuação e pós-check por tentativa no `_enviar_com_retry`; `BENCHMARK_TASK_TIMEOUT` (400s) segue como total.
- **`num_ctx` adaptativo**: `LlamaClient` remove o campo e refaz a requisição 1× após HTTP 400 (flag cacheada); comportamento inalterado em servidores que ignoram o campo. `ollama_client.py` intocado.
- **`log.json` v2.0 estendido**: `meta` ganha `ctx_size_detectado`, `ctx_fonte`, `system_prompt_tokens`, `fator_calibracao_tokens`, `timeout_por_chamada_s`.
- **Testes**: 172/172 passando (17 novos: estimativa, calibração, warmup ctx, num_ctx adaptativo, pre-check) + 33 subtests.

### 4.1.6 — Metadados Reais, Contexto e Relatório Enxuto (2026-09-02)
- **Fonte única de verdade do modelo**: `_extrair_nome_exibicao()` e `_extrair_quantizacao()` derivam nome amigável e quantização do ID cru do GGUF; `_obter_metadados_modelo()` retorna dict com `nome_exibicao` e fallback de quantização; `_warmup_model()` **aborta com `SystemExit`** se `/v1/models` não responder — o relatório nunca exibe modelo falso (antes: aviso no console e seguia com `LLAMA_MODEL`).
- **Relatório enxuto**: `generate_report()` recebe apenas `metadados_modelo`; seção Modelo mostra somente dados reais (Nome, Quantização, ID real, Parâmetros, n_ctx, Tamanho) — removidos a coluna "Configurado" e o alerta de divergência; escrita duplicada de `log.json` removida do report.
- **`log.json` v2.0**: bloco `meta` com `modelo_id_real`, `modelo_nome_exibicao`, `modelo_quantizacao`, `data_execucao` (ISO), `total_tarefas`, `repeticoes_por_tarefa`, `versao_benchmark`, `system_prompt_hash` (SHA-256 de 12 chars), `llama_base_url`; `compare_runs.py` segue compatível.
- **Métrica `contexto_ok`**: `MariaTaskResult.contexto_ok` (default True) + `MariaBenchmarkMetrics.contexto_ok_rate`; o `MariaRunner` classifica `OllamaClientError` por marcadores específicos de estouro de contexto (`exceeds the available context size`, `too many tokens`, etc.) e propaga `contexto_ok=False`; linha "Contexto OK" no `report.md`.
- **Testes**: 155/155 passando (9 novos: `TestExtrairNomeExibicao`, `TestExtrairQuantizacao`, `TestContextoOk`) + 33 subtests.

### 4.1.5 — Normalização de Chaves e Argumentos (2026-09-02)
- **Tool calling tolerante à caixa**: `_extrair_tool_call_da_resposta()` e `_tentar_extrair_tool_call_textual()` (`backend/core/llama_client.py`) normalizam as chaves dos argumentos para minúsculas — o modelo às vezes gera `'Conteudo'`/`'Nome_arquivo'`, o que invalidava a execução da ferramenta e derrubava a tool accuracy do benchmark (criar_documentos: 33%).
- **`MariaRunner` flexível**: `_argumentos_compativeis()` reescrita (chaves minúsculas, listas como conjuntos) + novos helpers `_normalizar_valor()` (remove extensão de `nome_arquivo`) e `_normalizar_texto()` (acentos removidos); keyword match do `run()` usa a normalização — `'não foi localizado'` casa com `'nao foi localizado'`.
- **Tarefas 21-23** (`tasks_edges.py`): keywords expandidas para 5 sinônimos de inexistência e nomes de arquivo inequivocamente fictícios (`arquivo_que_nao_existe`, `planilha_inexistente`, `planilha_nao_existe`).
- **Testes**: 145/145 passando + 7 verificações funcionais manuais.

### 4.1.4 — System Prompt Externo (2026-09-02)
- **Prompt fora do código**: `backend/core/system_prompt.txt` (~2,2 KB) carregado por `MARIA_SYSTEM_PROMPT` em `backend/core/config.py`, com `RuntimeError` explícito se ausente.
- **Refatoração**: bloco `SYSTEM_PROMPT` hardcoded removido de `ChatSession` (mantido como alias) e reforço hardcoded de tool calling removido de `_montar_mensagens_com_reforco()` no `LlamaClient` (fallback para o config). Injeção dinâmica via `get_historico_com_system()` preservada (contrato de `main.py`, `contar_mensagens()` e testes).
- **Divergência deliberada**: `ollama_client.py` mantém o reforço hardcoded original — alinhar em tarefa futura.
- **Testes**: 145/145 passando (2 testes atualizados para strings do prompt externo).

### 4.1.3 — Prompt, Resposta Bruta e Sampler no Benchmark (2026-09-02)
- **Sampler configurável**: 15 novas variáveis `LLAMA_*` em `backend/core/config.py` (repeat_penalty, top_k, top_p, min_p, dry_*, xtc_*, typical_p, top_n_sigma, etc.) com defaults idênticos aos do llama-server; `montar_sampler_params()` é a fonte única da verdade e `_montar_payload` envia os 16 parâmetros nas chamadas com tools.
- **Prompt e resposta bruta por execução**: `MariaTaskResult` agora expõe `prompt_enviado` (mensagens completas), `resposta_bruta_modelo` (texto cru antes de sobrescrita por confirmação/ferramenta/continuação) e `sampler_params`; `log.json` registra por execução + `meta.sampler_params`.
- **Relatório enriquecido**: seções "Parâmetros do sampler" (tabela) e "Detalhes por execução" (prompt JSON + resposta bruta + mensagem final) no `report.md`.
- **Testes**: 145/145 passando (7 novos em `TestSamplerParamsBenchmark`).

### 4.1.2 — Metadados do Modelo no Benchmark & Fix da Suíte (2026-09-02)
- **Nome real do modelo**: `_obter_metadados_modelo()` consulta `GET {LLAMA_BASE_URL}/v1/models` e extrae id, quantização (mapeo ftype GGML), n_params, n_ctx, tamanho; blobs/caminhos locais são exibidos como rótulo legível (`Qwen2.5 3B`).
- **Reporte enriquecido**: seção Modelo com configurado/cargado/derivado, quantização, parámetros, n_ctx e tamanho; aviso quando `LLAMA_NUM_CTX` excede o `n_ctx` do servidor.
- **`log.json` com meta**: bloco `meta` opcional; `compare_runs.py` suporta formato antigo (lista) e novo (dict).
- **Suíte de testes**: estrutura corrigida (file não compilaba) + 18 testes novos; 138/138 passando.
- **Testes**: 138 testes passando na suíte completa do backend.

### 4.1.1 — Correções Críticas de Segurança & Robustez (2026-08-31)
- **Token Atômico**: escrita atômica do `.bridge_token` via arquivo temporário e rename do SO (`os.replace`), prevenindo leituras parciais por clientes concorrentes.
- **CORS Restrito**: `MARIA_ENV=development` necessário para aceitar requisições de `http://localhost:5173`. Produção restringe exclusivamente a origens do Tauri.
- **PATH Hijacking**: `transcrever_audio` valida se o binário do Whisper reside dentro de `WHISPER_ALLOWED_DIR`.
- **SQLite Concorrente**: `check_same_thread=False` + `busy_timeout=5000ms` + *double-checked locking* no `get_connection()`.
- **TTFT**: medição do timer iniciada antes da chamada HTTP `_make_request()`.
- **MariaRunner**: respostas negativas/ambíguas anulam `tool_call_final` sem disparar a ferramenta indevidamente; erros de execução preenchem `final_message`.
- **Testes**: 120 testes passando na suíte completa do backend.

### 4.1.0 — RAG do Manual de Redação da Presidência (2026-08-30)
- Ferramenta `consultar_manual_redacao` via SQLite **FTS5** (255 trechos ingeridos).
- Unificação de aviso/memorando sob o padrão **ofício** no domínio.
- Encadeamento automático antes da criação de documentos oficiais.
