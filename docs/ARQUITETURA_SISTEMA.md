# Arquitetura do Sistema — MARIA

**Versão:** v4.0.0
**Última atualização:** 2026-08-30
**Status:** ✅ Migração Tauri v4 concluída (frontend Tauri v2 + React + backend Python em bridge HTTP)

Este documento descreve a arquitetura real e atual do sistema MARIA, refletindo o modelo LLM configurado (`qwen2.5-omni-3b` via llama-server como padrão em produção; `qwen3.5:4b` via Ollama mantido como caminho legado/opcional) e a estrutura implementada no monorepo. Consulte `backend/core/config.py` como fonte da verdade para configurações de modelo.

---

## 1. Visão Geral

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo. O sistema consiste em dois processos independentes que se comunicam via **HTTP (bridge JSON, porta 8081)** e banco SQLite compartilhado:

- **Frontend**: Tauri v2 + React + TypeScript + Tailwind (interface visual com navegação por abas)
- **Backend**: Python 3.11+ (LLM local via llama-server, lógica de negócio, ferramentas)
- **Banco de Dados**: SQLite compartilhado (`shared/maria.db`) com schema canônico em `shared/schema.sql`

### Diagrama de Arquitetura

```
┌─────────────────────────────────────┐   HTTP JSON    ┌──────────────────────────────────┐
│  Frontend Tauri v2                  │ ◄────────────► │  Backend Python                  │
│  (React + TS + Tailwind)            │  porta 8081    │  (llama-server + ferramentas)    │
│  Rust: rusqlite, reqwest, sidecar   │  (--bridge-http│  Python 3.11+                    │
│                                     │   em produção: │                                  │
│  • App.tsx (entry point)            │   sidecar      │  • main.py (--bridge-http/CLI)   │
│  • pages/ (ConversarPage, etc.)     │   stdin/stdout)│  • llama_client.py (produção)    │
│  • components/ (TopBar, Sidebar,    │◄──────────────►│  • ollama_client.py (legado)     │
│    CenterStage, ChatPanel)          │                │  • router.py (multi-modelo,      │
│  • hooks/ (useMariaBridge, useTheme)│                │    em integração)                │
│  • useMariaBridge → reqwest HTTP    │                │  • tools_schema.py + handlers    │
│  • rusqlite (persistência local)    │                │  • session_storage.py            │
└──────────────────┬──────────────────┘                 └────────────────┬─────────────────┘
                   │                                                     │ HTTP localhost
                   │ rusqlite (WAL)                                      │ (porta 8080)
                   ▼                                              ┌──────▼──────────┐
┌─────────────────────────────────────┐                           │  llama-server   │
│  SQLite (shared/maria.db)           │◄──────────────────────────┤ qwen2.5-omni-3b │
│  - conversas                        │     Shared Database       └─────────────────┘
│  - mensagens (ON DELETE CASCADE)    │       (WAL mode)          ┌─────────────────┐
│  - memoria                          │                           │ Ollama (legado) │
│  - arquivos_indexados               │                           │ qwen3.5:4b      │
│  - automacoes                       │                           └─────────────────┘
│  - configuracoes                    │
└─────────────────────────────────────┘
```

---

## 2. Componentes do Sistema

### 2.1 Frontend (Tauri v2 + React)

**Tecnologias:** Tauri v2 (Rust), React 18, TypeScript, Tailwind CSS, Vite, rusqlite, reqwest

**Estrutura:** `frontend-tauri/`

#### Componentes Principais

| Camada | Responsabilidade |
|--------|------------------|
| `src/App.tsx` | Entry point React; roteamento entre páginas |
| `src/pages/ConversarPage.tsx` | Painel de chat; envio/recebimento de mensagens via bridge HTTP, persistência no banco |
| `src/components/TopBar.tsx` | Barra superior; indicador de modelo (MODO LOCAL/MODELO) e status do sistema |
| `src/components/Sidebar.tsx` | Navegação por abas; card de recursos do sistema (CPU/RAM/GPU) |
| `src/components/CenterStage.tsx` | Tela inicial (hero); cards de funcionalidades e ações rápidas |
| `src/components/ChatPanel.tsx` | Componente de chat reutilizável (bolhas, anexos, voz) |
| `src/hooks/useMariaBridge.ts` | Hook de comunicação com o backend Python via HTTP (porta 8081, `reqwest` no lado Rust) |
| `src/hooks/useTheme.ts` | Alternância de tema claro/escuro |
| `src-tauri/src/main.rs` | Comandos Tauri; ponte HTTP para o backend; sidecar `maria-backend` (produção) |
| `src-tauri/Cargo.toml` | Dependências Rust: rusqlite, chrono, uuid, reqwest + plugins Tauri |
| `src-tauri/build_sidecar.py` | Gera o binário sidecar do backend Python via PyInstaller |

#### Persistência (Rust)

| Módulo | Responsabilidade |
|--------|------------------|
| rusqlite (`main.rs`) | Conexão com `shared/maria.db`, aplica WAL mode e FKs |
| Comandos Tauri | CRUD de conversas, mensagens, memória, automações e configurações |

#### Estilização (Tailwind)

| Tema | Descrição |
|------|-----------|
| Escuro (padrão) | Fundo `#0a0a12`, aura e destaques rosa `#e05d8a` / `#f2a2bb` |
| Claro | Fundo `#f7f3ec`, accent terracota `#c47b54` |

---

## 3. Protocolo de Comunicação (Bridge)

O frontend Tauri consome o backend Python via **HTTP JSON na porta 8081** (modo `--bridge-http`), com os mesmos 19 comandos do protocolo bridge original. Em produção, o backend é empacotado como **sidecar** (`binaries/maria-backend`) e executado pelo Tauri em modo `--bridge` (stdin/stdout JSON-lines).

### Segurança da Camada HTTP

| Medida | Implementação |
|--------|---------------|
| **Autenticação** | Header `Authorization: Bearer <token>` obrigatório em `/chat`; token de 32 bytes gerado pelo backend a cada inicialização e persistido em `shared/.bridge_token` (ignorado pelo git). O Rust (`call_python_backend`) lê o token e injeta o header automaticamente. `/ping` fica aberto para health check. |
| **CORS** | Restrito às origens do frontend (`tauri://localhost`, `http://tauri.localhost`, `http://localhost:5173`). |
| **Bind** | Servidor escuta apenas em `127.0.0.1` (sem exposição à rede). |
| **CSP** | Política restritiva no `tauri.conf.json` (`default-src 'self'`; `connect-src` limitado à bridge + IPC Tauri). |
| **Shell scope** | Capabilities restritas ao sidecar `maria-backend` com argumentos fixos (`--bridge-http --porta 8081`); scopes `python`/`python3` removidos. |
| **Arquivos** | `upload_arquivo` valida tipo/limite de tamanho (100 MB); `transcrever_audio` valida caminho via `resolver_caminho_permitido()` e `WHISPER_BIN` por regex — impede leitura/deleção arbitrária de arquivos. |

Detalhes completos e pendências: [`docs/SEGURANCA.md`](SEGURANCA.md).

---

## 4. Banco de Dados Compartilhado

### Schema Canônico Unificado (6 Tabelas em Português)

Definido no arquivo [`shared/schema.sql`](../shared/schema.sql):

| Tabela | Colunas Principais | Responsável Escrita |
|--------|-------------------|---------------------|
| `conversas` | `id`, `titulo`, `criado_em`, `atualizado_em` | Ambos |
| `mensagens` | `id`, `conversa_id`, `role`, `conteudo`, `anexos`, `criado_em` (FK -> conversas CASCADE) | Ambos |
| `memoria` | `id`, `fato`, `categoria`, `relevancia`, `fonte`, `criado_em` | Ambos |
| `arquivos_indexados` | `id`, `caminho`, `tipo`, `tamanho_bytes`, `hash_checksum`, `indexado_em`, `ultima_leitura` | Ambos |
| `automacoes` | `id`, `nome`, `descricao`, `gatilho`, `acao`, `parametros`, `passos_json`, `ativo`, `execucoes_count`, `criado_em`, `ultima_execucao` | Ambos |
| `configuracoes` | `chave`, `valor`, `descricao`, `atualizado_em` | Ambos |

### Concorrência e Integridade
- **WAL Mode**: Ativado tanto no Python quanto no Rust (rusqlite) para concorrência de leitura/escrita sem locks.
- **Foreign Keys**: `ON DELETE CASCADE` configurado para mensagens vinculadas a conversas.

---

## 5. Estado Atual por Camada

| Camada | Estado | Observações |
|--------|--------|-------------|
| Backend core (llama-server, tools) | ✅ Funcional | MVP Fase 2 completo |
| Backend legado (Ollama) | ✅ Funcional | Mantido como caminho opcional (`ollama_client.py`) |
| Backend CLI | ✅ Funcional | `main.py` modo CLI |
| Backend Bridge stdin/stdout | ✅ 19 comandos | Usado pelo sidecar em produção |
| Backend Bridge HTTP | ✅ Funcional | Porta 8081, consumido pelo frontend Tauri em dev |
| Backend Database | ✅ Schema unificado | 6 tabelas + índices + WAL |
| Frontend Tauri (Rust) | ✅ Funcional | App compila e inicia; sidecar configurado |
| Frontend React (navegação) | ✅ Funcional | Abas implementadas (React Router) |
| Frontend chat | ✅ Funcional | Integrado ao backend via `useMariaBridge` (HTTP) |
| Frontend persistência | ✅ rusqlite | `shared/maria.db` compartilhado com o backend |
| Frontend design | ✅ Implementado | Tema escuro com efeitos rosa e transições |
| Testes Backend | ✅ 86/86 | pytest passando |
| Testes Frontend (TS) | ✅ Passando | `npm run test` |
| Testes Frontend (Rust) | ✅ Passando | `cargo test` |
| Documentação | ✅ Atualizada | v4.0; históricos em `docs/arquivo/` |

---

## Nota sobre Modelos LLM

- **Modelo padrão em produção:** `qwen2.5-omni-3b` via **llama-server** (`backend/core/llama_client.py`).
- **Modelo legado/opcional:** `qwen3.5:4b` via **Ollama** (`backend/core/ollama_client.py`) — mantido apenas como caminho alternativo.
- **Fonte da verdade:** `backend/core/config.py` — as constantes `LLAMA_MODEL` e `OLLAMA_MODEL` controlam o roteamento.
