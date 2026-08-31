# PROGRESSO_DESENVOLVIMENTO_V1

> Controle do desenvolvimento do **MARIA** (v4.x). Atualizado a cada tarefa concluída.

**Última alteração:** 2026-08-30

---

## ✅ Percentual Geral Concluído

| Área | Progresso |
|------|-----------|
| Backend (Python) | 87% |
| Frontend (Tauri + React) | 90% |
| Integração Bridge/HTTP | 90% |
| **Total (v4.x)** | **~88%** |

<sup>Percentual estimado pela combinação de módulos implementados e suíte de testes automatizados. Números revisados à medida que cada entregável do roadmap é concluído.</sup>

---

## 📋 Tabela de Versões

| Versão | Data | Descrição | Status |
|--------|------|-----------|--------|
| 4.0.0 | — | Migração base para Tauri v2 + React | ✅ Concluída |
| 4.0.1 | — | Migração Tauri + React (P0–P2): bridge HTTP, schema SQLite, fixes | ✅ Concluída |
| 4.0.2 | — | Documentação da v4.0 e manutenção (README, .gitignore) | ✅ Concluída |
| **4.1.0** | **2026-08-30** | **RAG do Manual de Redação da Presidência da República (SQLite FTS5)** | ✅ Concluída |

---

## ✅ Checklist — Roadmap

### Fase 1 — Backend Core
- [x] Controller, ChatSession, persistência de memória
- [x] LlamaClient (llama-server / Qwen2.5-Omni) e OllamaClient (legado qwen3.5:4b)
- [x] Tool calling (function calling) + encadeamento de ferramentas de leitura
- [x] Bridge `--bridge` (stdin/stdout JSON-lines) e `--bridge-http` (porta 8081)

### Fase 2 — Gerência de Arquivos e Documentos
- [x] Criação de planilhas (Excel) e documentos Word
- [x] Edição de planilhas existentes
- [x] Leitura de arquivos (txt, md, csv, log, docx) com segurança de pastas permitidas
- [x] Upload/segurança de comandos bridge e token da API HTTP

### Fase 3 — RAG e Conhecimento
- [x] RAG de memória persistente (fatos sobre o usuário)
- [ ] ~~RAG vetorial~~ *(substituído por FTS5 lexical)*
- [x] **Manual de Redação da Presidência da República (RAG via SQLite FTS5)** — `consultar_manual_redacao`
- [x] Ingestão do manual (`ingest_manual_redacao.py`, idempotente) — 255 trechos

### Fase 4 — Frontend (Tauri + React)
- [x] Janela Tauri v2, plugins shell/dialog/fs, CSP
- [x] UI: TopBar, Sidebar, CenterStage, ChatPanel, temas, Aura
- [x] Bridge do frontend com o backend (HTTP localhost:8081)
- [ ] Distribuição/instalador validado em máquina limpa (sem Python)

### Fase 5 — Qualidade e Testes
- [x] Suíte unitária `unittest` (backend) — **116 testes OK**
- [x] Vitest (frontend)
- [x] Critérios de aceite do RAG validados (contagem, idempotência, isolamento de `_DB_PATH`)
- [ ] Medir cobertura formal (`coverage`) sobre os módulos novos

---

## 🔁 Notas das iterações mais recentes

### 4.1.0 — RAG do Manual de Redação (2026-08-30)
- Nova ferramenta de leitura `consultar_manual_redacao`, encadeada antes de `criar_documento` para documentos oficiais.
- Arquitetura: SQLite **FTS5** (zero dependências novas), tabela `manual_redacao_fts` com `remove_diacritics`.
- Fato do domínio: "aviso" e "memorando" unificados sob **ofício** → enum usa `oficio`.
- Ingestão: `ingest_manual_redacao.py` → **255 trechos** em `shared/maria.db`; artefato `manual_redacao_chunks.json` ignorado no Git.
- Modo de contexto: trechos truncados em `MANUAL_REDACAO_MAX_CHARS_POR_TRECHO` (800) para não estourar `OLLAMA_NUM_CTX`/`LLAMA_NUM_CTX`.
- Arquivos: `schema.sql`, `schema.py`, `ingest_manual_redacao.py`, `manual_redacao.py`, `tools_schema.py`, `config.py`, `chat_session.py`, `ollama_client.py`, `llama_client.py`, `test_maria.py`, `.gitignore`.
- Testes: **116/116 OK** (2× execuções), incluindo 11 novos (3 classes).