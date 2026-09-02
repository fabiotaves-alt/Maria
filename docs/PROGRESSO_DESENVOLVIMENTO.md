# PROGRESSO_DESENVOLVIMENTO

> Painel de controle de entregas e roadmap do **MARIA** (v4.x). Atualizado a cada tarefa concluída.

**Versão Atual:** v4.1.5  
**Última alteração:** 2026-09-02  

---

## ✅ Percentual Geral Concluído

| Área | Progresso | Observações |
|------|-----------|-------------|
| Backend Core & Ferramentas (Python) | 97% | LlamaClient, RAG FTS5, criação/edição de arquivos, benchmark com metadados do modelo, sampler configurável e system prompt externo |
| Segurança & Concorrência | 95% | Token atômico, CORS por ambiente, SQLite thread-safe, PATH hijacking |
| Frontend (Tauri v2 + React) | 92% | Interface completa, temas, persistência rusqlite, sidecar |
| Integração Bridge (HTTP/Sidecar) | 95% | 19 comandos bridge, autenticação Bearer, health check |
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
- [x] Suíte de testes unitários do backend (145 testes passando via `pytest`)
- [x] Testes unitários do frontend TypeScript (Vitest) e da camada Rust (`cargo test`)
- [x] Framework de benchmark de tool calling com relatório e log JSON
- [x] Metadados do modelo no benchmark: nome real via `/v1/models` + parámetros (quantização, n_params, n_ctx, tamanho) em `log.json` e `report.md`
- [x] Prompt, resposta bruta do modelo e parâmetros de sampler (16 configuráveis via ENV) expostos por execução no benchmark
- [x] Comparação de runs retrocompatible (`log.json` antigo e novo)
- [x] Robustez no `MariaRunner`: tratamento correto de negação, ambiguidade e mensagens de erro
- [x] Normalização no benchmark: chaves de argumentos em minúsculas, `nome_arquivo` com/sem extensão equivalente, listas como conjuntos e keyword match sem falsos negativos por acento
- [ ] Cobertura formal de código (`pytest-cov`)

---

## 🔁 Notas das Iterações Recentes

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