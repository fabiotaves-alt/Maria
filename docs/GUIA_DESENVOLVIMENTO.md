# Guia de Desenvolvimento — MARIA

**Versão:** v4.0.0
**Última atualização:** 2026-08-30

Este documento serve como guia prático para novos desenvolvedores e para as próximas fases de desenvolvimento do projeto MARIA.

> **Nota sobre a v4:** o frontend JavaFX foi substituído por **Tauri v2 + React**. O backend Python permanece o mesmo, agora servido em modo **bridge HTTP** (porta 8081). Documentos da era JavaFX (v2.x/v3.x) foram arquivados em [`docs/arquivo/`](arquivo/).

---

## 1. Configuração do Ambiente

### Pré-requisitos

| Requisito | Versão | Observação |
|-----------|--------|------------|
| Python | 3.11+ | Ambiente virtual na raiz (`.venv/`) |
| Node.js + npm | 18+ | Para o frontend Tauri |
| Rust | estável | Necessário para compilar o Tauri (`rustup`) |
| llama.cpp / llama-server | atual | Servidor LLM local (produção) |
| Ollama | opcional | Caminho legado/opcional |
| **Modelo LLM (produção)** | **qwen2.5-omni-3b** | Via `llama-server` (porta 8080) |
| **Modelo LLM (legado)** | **qwen3.5:4b** | Via Ollama (porta 11434) — opcional |

### Instalação Passo a Passo

```bash
# 1. Clonar o repositório
git clone <repo-url>
cd maria

# 2. Ambiente Python (na raiz do monorepo)
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Frontend Tauri
cd frontend-tauri
npm install

# 5. Modelo LLM (produção — llama-server)
# Inicie o llama-server com o modelo qwen2.5-omni-3b (porta 8080)
# Caminho legado/opcional (Ollama):
#   ollama serve
#   ollama pull qwen3.5:4b

# 6. Configurar variáveis de ambiente (opcional)
# Copie backend/.env.example para backend/.env e ajuste se necessário
```

### Execução do Projeto

#### Backend (Python)

```bash
# Modo bridge HTTP (usado pelo frontend Tauri — porta 8081)
.venv\Scripts\python.exe backend\main.py --bridge-http

# Modo bridge stdin/stdout (usado pelo sidecar do Tauri em produção)
.venv\Scripts\python.exe backend\main.py --bridge

# Modo CLI (terminal interativo)
.venv\Scripts\python.exe backend\main.py
```

#### Frontend (Tauri v2 + React — atual)

```bash
cd frontend-tauri

# Modo desenvolvimento (janela do app + hot reload do Vite)
npm run tauri dev

# Build de produção (gera MSI/DMG/AppImage)
npm run tauri build   # antes: python src-tauri/build_sidecar.py
```

> ✅ **Estado atual:** o app compila e inicia corretamente. Para o chat funcionar em dev, inicie o backend Python em paralelo no modo bridge HTTP (porta 8081 — consumido pelo frontend Tauri):
> ```bash
> .venv\Scripts\python.exe backend\main.py --bridge-http
> ```
> O backend gera automaticamente um token de autenticação em `shared/.bridge_token` ao iniciar; o app Tauri o lê e injeta no header `Authorization` — nenhum passo manual é necessário. Para testes manuais com `curl`, consulte [`docs/SEGURANCA.md`](SEGURANCA.md).
> Veja [`frontend-tauri/IMPLEMENTACAO_COMPLETA.md`](../frontend-tauri/IMPLEMENTACAO_COMPLETA.md) para detalhes.

#### Testes

```bash
# Da raiz do monorepo
.venv\Scripts\python.exe -m pytest backend/tests/test_maria.py -v

# Ou via unittest
.venv\Scripts\python.exe -m unittest backend.tests.test_maria

# Frontend (dentro de frontend-tauri/)
npm run build    # type-check + build Vite
npm run test     # testes TypeScript
cargo test       # testes Rust (em src-tauri/)
```

---

## 2. Arquitetura do Sistema

Para detalhes completos da arquitetura, consulte [`docs/ARQUITETURA_SISTEMA.md`](ARQUITETURA_SISTEMA.md).

Resumo:

```
┌──────────────────────────┐   HTTP (8081)   ┌──────────────────────────┐
│  Frontend Tauri v2       │ ◄─────────────► │  Backend Python          │
│  React + TS + Tailwind   │  JSON (REST)    │  (LLM + ferramentas)     │
│  Rust (rusqlite, sidecar)│                 │  Python 3.11+            │
└──────────────────────────┘                 └──────────┬───────────────┘
                                                        │ HTTP localhost
                                              ┌─────────▼─────────┐
                                              │  llama-server     │
                                              │  qwen2.5-omni-3b  │
                                              │  (padrão)         │
                                              └───────────────────┘
                                              ┌───────────────────┐
                                              │  Ollama (legado)  │
                                              │  qwen3.5:4b       │
                                              └───────────────────┘
```

---

## 3. Roadmap / Backlog

Ações já concluídas nas fases anteriores (banco unificado, DAOs, desmockagem da interface, migração Tauri) — detalhes em [`docs/arquivo/`](arquivo/).

### Backlog atual

| Ação | Descrição | Prioridade |
|------|-----------|------------|
| **Fine-tuning LoRA (opcional)** | Fine-tuning do `qwen2.5-omni-3b` com dados em português para tarefas de escritório. Ferramentas: PEFT, Transformers, datasets pt-BR. | Média |
| **Avatar nas bolhas de chat** | Carregar imagem dinamicamente no chat (atualmente placeholder). | Média |
| **GPU NVIDIA** | Exibir uso real de GPU (pynvml) no card de recursos do sistema; detectar AMD/Intel opcionalmente. | Baixa |
| **Whisper.cpp empacotado** | Empacotar binário do Whisper para transcrição de voz sem instalação manual (guia: [`docs/INSTALACAO_WHISPER.md`](INSTALACAO_WHISPER.md)). | Média |
| **Router multi-modelo** | Ativação do `backend/core/router.py` para roteamento entre modelos (arquivo já presente, aguardando integração). | Média |

---

## 4. Estrutura de Pastas

```
maria/
├── README.md                  ← documentação geral
├── requirements.txt           ← dependências Python consolidadas
├── .venv/                     ← ambiente virtual Python (raiz)
├── docs/                      ← documentação técnica
│   ├── GUIA_DESENVOLVIMENTO.md     ← este arquivo
│   ├── ARQUITETURA_SISTEMA.md      ← arquitetura real
│   ├── GUIA_TESTES_EMPIRICOS.md    ← como construir e testar
│   ├── DECISOES_BANCO_DADOS.md     ← decisões de banco de dados
│   ├── SEGURANCA.md                ← medidas de segurança e pendências
│   ├── INSTALACAO_WHISPER.md       ← instalação do Whisper.cpp
│   ├── PLANO_MIGRACAO_TAURI_V4.md  ← referência da migração v4
│   └── arquivo/                    ← documentos históricos (era JavaFX, planos concluídos)
├── shared/                    ← banco SQLite compartilhado (maria.db + schema.sql)
├── backend/
│   ├── main.py                ← CLI + modos --bridge e --bridge-http
│   ├── core/
│   │   ├── config.py          ← fonte da verdade (modelos, URLs, parâmetros)
│   │   ├── llama_client.py    ← cliente llama-server (produção)
│   │   ├── ollama_client.py   ← cliente Ollama (legado/opcional)
│   │   ├── router.py          ← roteamento multi-modelo (em integração)
│   │   ├── tools_schema.py    ← schema das ferramentas
│   │   └── handlers/          ← excel_handler, word_handler, etc.
│   ├── database/              ← connection.py, schema.py
│   ├── tests/test_maria.py    ← suíte de testes pytest
│   └── CHANGELOG.md           ← changelog do backend
└── frontend-tauri/            ← atual (Tauri v2 + React, v4.0)
    ├── src/                   ← React + TypeScript + Tailwind
    │   ├── components/        ← TopBar, Sidebar, CenterStage, ChatPanel
    │   ├── hooks/             ← useTheme, useMariaBridge
    │   ├── pages/             ← ConversarPage, etc.
    │   └── App.tsx
    └── src-tauri/             ← Rust (Tauri v2)
        ├── src/main.rs        ← comandos + rusqlite + bridge Python
        ├── capabilities/default.json  ← permissões shell (v2)
        ├── binaries/          ← sidecar maria-backend (gerado por build_sidecar.py)
        ├── Cargo.toml         ← rusqlite, chrono, uuid, reqwest + plugins
        ├── tauri.conf.json    ← externalBin + updater + shell (v2)
        └── build_sidecar.py   ← gera sidecar via PyInstaller
```

---

## 5. Contribuição

### Padrões de Código

- **Python:** PEP 8, type hints quando aplicável
- **TypeScript/React:** ESLint + Prettier (config do projeto), componentes funcionais com hooks
- **Rust:** `cargo fmt` e `cargo clippy` sem warnings
- **Commits:** Mensagens claras e descritivas (preferencialmente em português)

### Fluxo de Trabalho Sugerido

1. Criar branch feature (`feature/nome-da-feature`)
2. Implementar mudanças
3. Rodar testes (`pytest` + `npm run build` + `cargo test`)
4. Commit com mensagem descritiva
5. Pull Request para review

---

## 6. Links Úteis

- [Tauri v2 — Documentação](https://v2.tauri.app/)
- [React — Documentação](https://react.dev/)
- [llama.cpp / llama-server](https://github.com/ggml-org/llama.cpp)
- [Documentação Ollama](https://ollama.com/) (legado)
- [PEFT Library](https://huggingface.co/docs/peft)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)

---

**Dúvidas?** Consulte a documentação ativa em `docs/` ou abra uma issue no repositório. Documentos da era JavaFX (v2.x/v3.x) estão em `docs/arquivo/`.
