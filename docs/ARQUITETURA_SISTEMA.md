# Arquitetura do Sistema — MARIA

**Versão:** v4.1.1
**Última atualização:** 2026-08-31
**Status:** ✅ Estável (Frontend Tauri v2 + React, Backend Python bridge HTTP/Sidecar, SQLite FTS5)

Este documento descreve a arquitetura real e atual do sistema MARIA, refletindo o modelo LLM configurado (`qwen2.5-omni-3b` via llama-server como padrão em produção; `qwen3.5:4b` via Ollama mantido como caminho legado/opcional) e a estrutura implementada no monorepo. Consulte `backend/core/config.py` como fonte da verdade para configurações de modelo.

---

## 1. Visão Geral

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo. O sistema consiste em dois processos independentes que se comunicam via **HTTP local (porta 8081 em dev) ou IPC stdin/stdout (sidecar em produção)** e um banco SQLite compartilhado:

- **Frontend**: Tauri v2 (Rust) + React 18 + TypeScript + Tailwind CSS + Framer Motion (interface visual moderna)
- **Backend**: Python 3.11+ (LLM local via llama-server, lógica de ferramentas, RAG FTS5, processamento de documentos)
- **Banco de Dados**: SQLite compartilhado (`shared/maria.db`) com schema canônico em `shared/schema.sql`

### Diagrama de Arquitetura

```
┌─────────────────────────────────────┐   HTTP JSON (porta 8081)   ┌──────────────────────────────────┐
│  Frontend Tauri v2                  │ ◄────────────────────────► │  Backend Python                  │
│  (React 18 + TS + Tailwind)         │    Authorization: Bearer   │  (llama-server + ferramentas)    │
│  Rust: rusqlite, reqwest, sidecar   │    <token atômico>         │  Python 3.11+                    │
│                                     │   em produção:             │                                  │
│  • App.tsx (entry point e layout)   │   sidecar (stdin/stdout)   │  • main.py (--bridge-http/CLI)   │
│  • components/ (TopBar, Sidebar,    │◄──────────────────────────►│  • llama_client.py (produção)    │
│    CenterStage, ChatPanel)          │                            │  • ollama_client.py (legado)     │
│  • hooks/ (useMariaBridge, useTheme)│                            │  • manual_redacao.py (RAG FTS5)  │
│  • useMariaBridge → reqwest HTTP    │                            │  • tools_schema.py + handlers    │
│  • rusqlite (persistência local)    │                            │  • connection.py (thread-safe)   │
└──────────────────┬──────────────────┘                            └────────────────┬─────────────────┘
                   │                                                                │ HTTP localhost
                   │ rusqlite (WAL mode)                                            │ (porta 8080)
                   ▼                                                         ┌──────▼──────────┐
┌─────────────────────────────────────┐                                      │  llama-server   │
│  SQLite (shared/maria.db)           │◄─────────────────────────────────────┤  (llama.cpp)    │
│  - conversas                        │           Shared Database            │  Qwen2.5-Omni   │
│  - mensagens (ON DELETE CASCADE)    │             (WAL mode)               │  3B — Q4_K_M    │
│  - memoria (fatos RAG)              │                                      └─────────────────┘
│  - arquivos_indexados               │                                      ┌─────────────────┐
│  - automacoes                       │                                      │ Ollama (legado) │
│  - configuracoes                    │                                      │ qwen3.5:4b      │
│  - manual_redacao_fts (FTS5)        │                                      └─────────────────┘
└─────────────────────────────────────┘
```

---

## 2. Componentes do Sistema

### 2.1 Frontend (Tauri v2 + React)

**Tecnologias:** Tauri v2 (Rust), React 18, TypeScript, Tailwind CSS, Vite, Framer Motion, Zustand, rusqlite, reqwest

**Estrutura:** `frontend-tauri/`

#### Componentes Principais

| Camada | Responsabilidade |
|--------|------------------|
| `src/App.tsx` | Entry point React; orquestra layout principal (`TopBar`, `Sidebar`, `CenterStage`, `ChatPanel`) |
| `src/components/TopBar.tsx` | Barra superior; indicador de status (MODO LOCAL/MODELO) e tema |
| `src/components/Sidebar.tsx` | Navegação lateral; métricas de recursos do sistema em tempo real (CPU/RAM/GPU) |
| `src/components/CenterStage.tsx` | Área central inicial (hero); cards de funcionalidades e atalhos rápidos |
| `src/components/ChatPanel.tsx` | Interface de chat interativa (mensagens em bolhas, upload de anexos, gravação de voz) |
| `src/hooks/useMariaBridge.ts` | Hook de integração com o backend Python via HTTP (porta 8081 via `reqwest` no Rust) |
| `src/hooks/useTheme.ts` | Gerenciamento de tema claro/escuro dinâmico |
| `src-tauri/src/main.rs` | Comandos Tauri IPC; ponte HTTP autenticada com backend; gerenciamento de sidecar |
| `src-tauri/Cargo.toml` | Dependências Rust: `rusqlite`, `uuid`, `reqwest`, plugins Tauri (`dialog`, `fs`, `shell`) |
| `src-tauri/build_sidecar.py` | Empacotador PyInstaller para gerar o executável standalone do backend (`maria-backend`) |

#### Persistência (Rust)

| Módulo | Responsabilidade |
|--------|------------------|
| rusqlite (`main.rs`) | Conexão direta com `shared/maria.db`, aplicando WAL mode e Foreign Keys |
| Comandos Tauri | CRUD de histórico de conversas, mensagens, memórias, automações e preferências |

#### Estilização (Tailwind)

| Tema | Descrição |
|------|-----------|
| Escuro (padrão) | Fundo `#0a0a12`, efeito aura e destaques rosa `#e05d8a` / `#f2a2bb` |
| Claro | Fundo `#f7f3ec`, acento terracota `#c47b54` |

---

## 3. Protocolo de Comunicação (Bridge)

O frontend Tauri consome o backend Python via **HTTP JSON na porta 8081** (modo `--bridge-http`). Em distribuição/produção, o backend é empacotado como **sidecar** (`binaries/maria-backend`) e executado pelo Tauri via stdin/stdout JSON-lines (modo `--bridge`).

### Segurança da Camada HTTP e Runtime

| Medida | Implementação |
|--------|---------------|
| **Autenticação por token** | Token de 32 bytes (`secrets.token_hex(32)`) gerado a cada startup e persistido de forma atômica (`.tmp` + `os.replace()`) em `shared/.bridge_token` com permissão POSIX `0o600`. Header `Authorization: Bearer <token>` obrigatório em `/chat`; `/ping` aberto apenas para health check. O Rust relê o arquivo a cada requisição e injeta o header. |
| **CORS por ambiente** | Em produção (`MARIA_ENV=production`), restrito estritamente a `tauri://localhost` e `http://tauri.localhost`. `http://localhost:5173` (Vite dev server) é aceito apenas quando `MARIA_ENV=development`. |
| **Proteção contra PATH hijacking** | O comando `transcrever_audio` valida se o binário resolvido via `shutil.which()` reside estritamente dentro do diretório configurado em `WHISPER_ALLOWED_DIR` (padrão: `<raiz_monorepo>/bin`). |
| **Isolamento de caminhos (Path Traversal)** | Funções de arquivo (`resumir_documento`, `analisar_arquivo`, `upload_arquivo`, etc.) utilizam `resolver_caminho_permitido()`, que resolve symlinks e restringe acessos a pastas permitidas (`PASTAS_PERMITIDAS`). |
| **Thread-Safety e Concorrência** | Módulo `backend/database/connection.py` com `check_same_thread=False`, `PRAGMA busy_timeout = 5000` e proteção de instanciação com `threading.Lock()` (*double-checked locking*). |
| **Bind Local** | O servidor Flask escuta exclusivamente na interface loopback `127.0.0.1`. |
| **CSP & Capabilities** | `tauri.conf.json` com `default-src 'self'`; permissões de shell estritamente restritas aos argumentos fixos do sidecar. |

Detalhes completos e auditoria: [`docs/SEGURANCA.md`](SEGURANCA.md).

---

## 4. Banco de Dados Compartilhado

### Schema Canônico Unificado

Definido no arquivo [`shared/schema.sql`](../shared/schema.sql):

| Tabela | Tipo | Finalidade | Responsável de Escrita |
|--------|------|------------|------------------------|
| `conversas` | Relacional | Sessões de chat do usuário | Ambos (Rust / Python) |
| `mensagens` | Relacional | Histórico de mensagens (`ON DELETE CASCADE` via `conversa_id`) | Ambos (Rust / Python) |
| `memoria` | Relacional | Fatos persistentes aprendidos sobre o usuário (RAG pessoal) | Ambos (Rust / Python) |
| `arquivos_indexados` | Relacional | Metadados e checksums de arquivos analisados | Backend Python |
| `automacoes` | Relacional | Rotinas e sequências de passos automatizados | Ambos (Rust / Python) |
| `configuracoes` | Relacional | Preferências de sistema (tema, modelo, áudio) | Ambos (Rust / Python) |
| `manual_redacao_fts` | Virtual (FTS5) | 255 trechos do Manual de Redação da Presidência da República (tokenizer `unicode61 remove_diacritics 2`) | Backend (`ingest_manual_redacao.py`) |

### Concorrência e Integridade
- **WAL Mode (`PRAGMA journal_mode = WAL`)**: Ativado tanto no Python quanto no Rust para permitir leituras concorrentes com escrita.
- **Foreign Keys (`PRAGMA foreign_keys = ON`)**: Ativado em todas as conexões para garantir integridade referencial.
- **Busy Timeout (`PRAGMA busy_timeout = 5000`)**: Evita travamentos imediatos sob contenção de escrita de múltiplas threads.

---

## 5. Estado Atual por Camada

| Camada | Estado | Observações |
|--------|--------|-------------|
| Backend Core (llama-server, tools) | ✅ Funcional | Suporte multimodal, encadeamento de leitura e tool calling |
| Backend RAG (Manual de Redação) | ✅ Funcional | Consulta FTS5 com BM25 e truncamento inteligente de contexto |
| Backend CLI | ✅ Funcional | `main.py` interativo no terminal |
| Backend Bridge stdin/stdout | ✅ 19 comandos | Utilizado pelo sidecar em produção |
| Backend Bridge HTTP | ✅ Funcional | Porta 8081, autenticada por token, usada pelo frontend em dev |
| Backend Database | ✅ Schema unificado | 6 tabelas relacionais + 1 tabela virtual FTS5 + WAL |
| Frontend Tauri (Rust) | ✅ Funcional | App compila e inicia; comandos rusqlite e sidecar configurados |
| Frontend React (UI) | ✅ Funcional | Interface com Glassmorphism, Aura rosa, TopBar, Sidebar e Chat |
| Frontend Persistência | ✅ rusqlite | Compartilha `shared/maria.db` com o backend |
| Testes Backend | ✅ 120/120 | pytest passando |
| Testes Frontend (TS) | ✅ Passando | `npm run test` (Vitest) |
| Testes Frontend (Rust) | ✅ Passando | `cargo test` |
| Documentação | ✅ Atualizada | v4.1.1; referências históricas organizadas |

---

## Nota sobre Modelos LLM

- **Modelo padrão em produção:** `qwen2.5-omni-3b` via **llama-server** (`backend/core/llama_client.py`).
- **Modelo legado/opcional:** `qwen3.5:4b` via **Ollama** (`backend/core/ollama_client.py`) — mantido como caminho alternativo.
- **Fonte da verdade:** `backend/core/config.py` — as constantes `LLAMA_MODEL` e `OLLAMA_MODEL` controlam a configuração.

