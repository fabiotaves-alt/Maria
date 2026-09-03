# Guia de Desenvolvimento — MARIA

**Versão:** v4.1.1
**Última atualização:** 2026-09-03
**Status:** ✅ Estável (Tauri v2 + React, Backend Python, SQLite FTS5)

Este documento serve como guia prático para novos desenvolvedores e para o ciclo contínuo de desenvolvimento do projeto MARIA.

> **Nota de Arquitetura:** O frontend JavaFX foi totalmente substituído por **Tauri v2 + React + TypeScript**. O backend Python é executado em modo **bridge HTTP** (porta 8081) em desenvolvimento e como **sidecar nativo** em produção. Documentos históricos e planos de migração concluídos estão arquivados em [`docs/arquivo/`](arquivo/).

---

## 1. Configuração do Ambiente

### Pré-requisitos

| Requisito | Versão | Observação |
|-----------|--------|------------|
| Python | 3.11+ | Ambiente virtual na raiz (`.venv/`) |
| Node.js + npm | 18 LTS+ | Para o frontend Tauri/React |
| Rust | estável | Para compilar a camada nativa do Tauri (`rustup`) |
| llama.cpp / llama-server | atual | Servidor LLM local (produção) |
| **Modelo LLM (produção)** | **qwen2.5-omni-3b** | Via `llama-server` (porta 8080) |
| **Modelo LLM (legado)** | **qwen3.5:4b** | Via Ollama (porta 11434) — opcional |

### Instalação Passo a Passo

```bash
# 1. Clonar o repositório
git clone <repo-url>
cd maria

# 2. Ambiente Python (na raiz do monorepo)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Instalar dependências do frontend Tauri
cd frontend-tauri
npm install
cd ..

# 5. Iniciar o llama-server (porta 8080)
# Exemplo com aceleração GPU (CUDA):
# .\llama.cpp\build\bin\Release\llama-server.exe -m "$env:USERPROFILE\models\qwen2_5-omni-3b-q4_k_m.gguf" -ngl 99 -c 8192 --flash-attn --host 127.0.0.1 --port 8080

# 6. Variáveis de ambiente opcionais (.env na raiz)
# Copie o arquivo de exemplo caso exista ou crie um .env:
# LLAMA_BASE_URL=http://localhost:8080
# MARIA_ENV=development
```

### Execução do Projeto

#### Backend (Python)

```bash
# Modo bridge HTTP (usado pelo frontend Tauri em dev — porta 8081)
.venv\Scripts\python.exe backend\main.py --bridge-http

# Modo bridge stdin/stdout (usado pelo sidecar do Tauri em produção)
.venv\Scripts\python.exe backend\main.py --bridge

# Modo CLI (terminal interativo standalone)
.venv\Scripts\python.exe backend\main.py
```

#### Frontend (Tauri v2 + React)

```bash
cd frontend-tauri

# Modo desenvolvimento (janela do app com hot reload do Vite)
npm run tauri dev

# Build de produção (gera instalador MSI/DEB/AppImage)
# (Executar build_sidecar.py uma vez antes se tiver alterado o backend)
python src-tauri/build_sidecar.py
npm run tauri build
```

> **Autenticação Automática da Bridge:** Ao iniciar com `--bridge-http`, o backend regenera atomicamente o token de autenticação em `shared/.bridge_token`. O frontend Tauri relê este arquivo a cada chamada e injeta o header `Authorization: Bearer <token>` automaticamente. Em desenvolvimento, use `MARIA_ENV=development` no `.env` para permitir CORS do Vite dev server (`http://localhost:5173`).

#### Testes Automatizados

```bash
# Backend — Suíte completa com pytest
.venv\Scripts\python.exe -m pytest backend/tests/test_maria.py -v

# Backend — Smoke-test contra o llama-server ao vivo (porta 8080)
.venv\Scripts\python.exe backend/tests/validate_llama_server.py

# Frontend — Type-check e build Vite
cd frontend-tauri && npm run build

# Frontend — Testes unitários TypeScript (Vitest)
cd frontend-tauri && npm test

# Rust — Testes da camada nativa do Tauri
cd frontend-tauri/src-tauri && cargo test
```

---

## 2. Arquitetura do Sistema

Para o detalhamento completo dos componentes e segurança, consulte [`docs/ARQUITETURA_SISTEMA.md`](ARQUITETURA_SISTEMA.md).

```
┌──────────────────────────┐   HTTP (8081)   ┌──────────────────────────┐
│  Frontend Tauri v2       │ ◄─────────────► │  Backend Python          │
│  React + TS + Tailwind   │  JSON (REST)    │  (LLM + RAG + tools)     │
│  Rust (rusqlite, sidecar)│                 │  Python 3.11+            │
└──────────────────────────┘                 └──────────┬───────────────┘
                                                        │ HTTP localhost
                                              ┌─────────▼─────────┐
                                              │  llama-server     │
                                              │  qwen2.5-omni-3b  │
                                              │  (porta 8080)     │
                                              └───────────────────┘
```

**Organização do backend (`backend/`):** o `main.py` é um *entry point* fino (argparse + despacho dos modos CLI, `--bridge` e `--bridge-http`). O transporte e o protocolo do bridge vivem no pacote `bridge/` (`servidores.py` e `comandos.py`) e a lógica de negócio na classe `MariaController` (`core/maria_controller.py`). Detalhes na seção 2.2 de [`docs/ARQUITETURA_SISTEMA.md`](ARQUITETURA_SISTEMA.md).

---

## 3. Backlog e Próximas Entregas

| Ação | Descrição | Prioridade |
|------|-----------|------------|
| **Instalador One-Click** | Empacotar instalador completo com Python embeddable e modelos pré-configurados | Alta |
| **Roteador Multi-Modelo** | Ativação do roteamento dinâmico entre modelos (`qwen2.5-omni-3b` para tarefas rápidas / 8B para raciocínio denso) | Média |
| **Whisper.cpp Empacotado** | Empacotamento do binário do Whisper para transcrição de áudio sem dependência de compilação externa manual | Média |
| **Avatar e Voz da MARIA** | Integração completa de áudio TTS + STT e animações no chat | Média |
| **Métricas Avançadas de GPU** | Detecção e telemetria de GPUs AMD/Intel além do suporte NVIDIA/pynvml | Baixa |

---

## 4. Estrutura de Pastas

```
maria/
├── README.md                      ← apresentação geral do produto
├── CHANGELOG.md                   ← changelog canônico (SemVer)
├── requirements.txt               ← dependências Python consolidadas
├── .venv/                         ← ambiente virtual Python
│
├── docs/                          ← documentação técnica viva
│   ├── ARQUITETURA_SISTEMA.md     ← diagrama e componentes
│   ├── SEGURANCA.md               ← modelo de ameaças e auditoria
│   ├── GUIA_DESENVOLVIMENTO.md    ← este guia
│   ├── GUIA_TESTES_EMPIRICOS.md   ← guia dos 5 níveis de teste
│   ├── DECISOES_BANCO_DADOS.md    ← decisões do schema SQLite
│   ├── GUIA_INSTALACAO.md         ← instalação completa e setup de IA (llama + whisper)
│   ├── MELHORIAS_RELATORIO.md     ← propostas de otimização
│   ├── PROGRESSO_DESENVOLVIMENTO.md ← controle de progresso
│   └── arquivo/                   ← histórico arquivado (diagnósticos, migrações e fases anteriores)
│
├── shared/                        ← recursos compartilhados
│   ├── schema.sql                 ← DDL canônico (6 tabelas + FTS5)
│   ├── maria.db                   ← banco de dados SQLite
│   └── .bridge_token              ← token de sessão HTTP (gerado em runtime)
│
├── backend/                       ← código do backend Python
│   ├── main.py                    ← entry point fino (CLI / --bridge / --bridge-http)
│   ├── bridge/                    ← transporte (servidores.py) e protocolo (comandos.py) do bridge
│   ├── core/                      ← lógica de negócio, LLM clients, tools e RAG
│   │   ├── config.py              ← fonte da verdade de configurações
│   │   ├── maria_controller.py    ← controller: cliente LLM, sessão, ferramentas
│   │   ├── llama_client.py        ← cliente llama-server
│   │   ├── chat_session.py        ← gerenciamento de contexto
│   │   ├── tools_schema.py        ← registro e validação de ferramentas
│   │   ├── tool_call_textual_parser.py  ← parser de tool calls textuais
│   │   ├── manual_redacao.py      ← RAG FTS5 do Manual de Redação
│   │   └── file_utils.py          ← validação e segurança de caminhos
│   ├── ui_terminal.py             ← interface CLI interativa
│   ├── database/                  ← conexão SQLite e scripts de ingestão
│   ├── tests/                     ← suíte pytest e smoke-tests
│   └── benchmark/                 ← framework de avaliação de tool calling
│
└── frontend-tauri/                ← interface Tauri v2 + React
    ├── src/                       ← React, TypeScript, Tailwind e Zustand
    │   ├── components/            ← TopBar, Sidebar, CenterStage, ChatPanel
    │   ├── hooks/                 ← useMariaBridge, useTheme
    │   └── types/                 ← contratos de dados TypeScript
    └── src-tauri/                 ← camada nativa Rust
        ├── src/main.rs            ← comandos Tauri, rusqlite e bridge
        ├── capabilities/          ← permissões e escopos de segurança
        ├── build_sidecar.py       ← gerador do executável standalone
        ├── Cargo.toml             ← dependências Rust
        └── tauri.conf.json        ← configuração do Tauri v2
```

---

## 5. Padrões de Contribuição

- **Python:** Conformidade com PEP 8, type hints estritos, docstrings explicativas em métodos públicos.
- **TypeScript / React:** Componentes funcionais, hooks customizados, tipagem estrita com TypeScript, Tailwind CSS para estilos.
- **Rust:** Formatação via `cargo fmt` e checagem estrita sem avisos via `cargo clippy`.
- **Commits:** Mensagens em português, concisas e orientadas à funcionalidade alterada.

---

## 6. Links e Referências

- [Documentação Oficial do Tauri v2](https://v2.tauri.app/)
- [Repositório e Servidor llama.cpp](https://github.com/ggml-org/llama.cpp)
- [Guia Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
- [Auditoria e Diretrizes de Segurança do MARIA](SEGURANCA.md)

