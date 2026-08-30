# MARIA — Assistente de IA Pessoal 100% Local

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo.

## ✅ Status: v4.0 — Migração para Tauri + React Concluída

A migração do frontend Java para **Tauri v2 + React + TypeScript** está concluída: o frontend Tauri compila, inicia e conversa com o backend Python (HTTP em desenvolvimento, sidecar em produção). O histórico completo do processo está em [`docs/PLANO_MIGRACAO_TAURI_V4.md`](docs/PLANO_MIGRACAO_TAURI_V4.md) e [`frontend-tauri/IMPLEMENTACAO_COMPLETA.md`](frontend-tauri/IMPLEMENTACAO_COMPLETA.md).

```
┌─────────────────────────┐   HTTP/Tauri IPC   ┌──────────────────────────┐
│  Frontend Tauri + React │ ◄────────────────► │  Backend Python          │
│  Tailwind CSS + Framer  │    localhost:8081  │  (LlamaClient intacto)   │
│  TypeScript + Zustand   │                    │  Python 3.11+            │
└────────────┬────────────┘                    └───────────┬──────────────┘
             │                                             │ HTTP localhost
             │ Rust IPC (sidecar)                    ┌─────▼──────────┐
             ▼                                       │  llama-server  │
    ┌─────────────────┐                              │  :8080         │
    │ shared/maria.db │ ◄─────────────────────────── │  Qwen2.5-Omni  │
    └─────────────────┘                              └────────────────┘
```

**Stack (v4.0):**
- **Frontend**: Tauri v2 (Rust) + React 18 + TypeScript + Vite + Tailwind CSS + Framer Motion + Zustand + lucide-react
- **Comunicação**: HTTP local (`localhost:8081`) em desenvolvimento + IPC nativo/sidecar Tauri em produção
- **Backend** (mantido): Python 3.11+ com `LlamaClient` (API OpenAI-compatible), function calling e suporte multimodal
- **Banco**: SQLite compartilhado em `shared/maria.db` com schema canônico (`shared/schema.sql`)

---

## Arquitetura Detalhada

- **Frontend (`frontend-tauri/`)**: React 18 + TypeScript + Vite com layout `TopBar` / `Sidebar` / `CenterStage` / `ChatPanel`, tema claro/escuro dinâmico (`useTheme`), aura rosa animada (`AuraBackground`) e bridge com o backend via `useMariaBridge` (HTTP `localhost:8081` em desenvolvimento, sidecar em produção). Shell Rust (Tauri v2) com comandos IPC, rusqlite e plugins de shell/dialog/fs.
- **Backend (`backend/`, mantido)**: `LlamaClient` (API OpenAI-compatible) conectado ao llama-server com histórico de contexto, prompt de sistema em pt-BR anti-alucinação, function calling com confirmação, suporte multimodal (imagem + áudio), geração de arquivos reais e persistência de sessões. Executa como CLI, bridge JSON-lines (`--bridge`) ou servidor HTTP (`--bridge-http`, porta 8081).
- **Banco de Dados**: SQLite compartilhado em `shared/maria.db` com schema canônico definido em `shared/schema.sql` (WAL mode e integridade referencial com ON DELETE CASCADE).

## Estrutura de Pastas

```
maria/
├── README.md                  ← este arquivo
├── requirements.txt           ← dependências Python consolidadas
├── .venv/                     ← ambiente virtual Python (raiz do monorepo)
├── docs/                      ← documentação técnica e relatórios
│   ├── PLANO_MIGRACAO_TAURI_V4.md  ← histórico do plano de migração
│   └── ...                    ← demais documentos técnicos
├── shared/                    ← banco SQLite compartilhado e DDL
│   ├── schema.sql             ← schema canônico unificado em português
│   └── maria.db               ← arquivo de banco de dados SQLite
├── backend/                   ← backend Python (mantido)
│   ├── main.py                ← modo bridge HTTP (porta 8081) + CLI
│   ├── core/                  ← LlamaClient, tools, handlers
│   ├── database/              ← connection.py e schema.py
│   ├── tests/                 ← suíte de testes (unittest + smoke-test)
│   └── benchmark/             ← sistema de benchmark live
└── frontend-tauri/            ← frontend Tauri v2 + React (v4.0)
    ├── src/                   ← React + TypeScript
    │   ├── components/        ← TopBar, Sidebar, CenterStage, ChatPanel
    │   ├── hooks/             ← useTheme, useMariaBridge
    │   ├── types/             ← tipos TypeScript compartilhados
    │   ├── App.tsx
    │   └── main.tsx
    ├── src-tauri/             ← Rust (Tauri v2)
    │   ├── src/main.rs        ← comandos + rusqlite + bridge Python
    │   ├── capabilities/      ← permissões shell (v2)
    │   ├── binaries/          ← sidecar maria-backend
    │   ├── icons/             ← 32x32, 128x128, .ico, .icns
    │   ├── build.rs           ← build script Tauri
    │   ├── build_sidecar.py   ← gera sidecar via PyInstaller
    │   ├── Cargo.toml
    │   └── tauri.conf.json
    └── package.json
```

## Pré-requisitos

| Requisito | Versão | Observação |
|-----------|--------|------------|
| Python | 3.11+ | venv na raiz (`.venv/`) |
| Node.js | 18+ | para o frontend React |
| Rust | 1.70+ | para o Tauri v2 |
| llama.cpp | build recente | compilar com `-DGGML_CUDA=ON` (NVIDIA) ou Metal (macOS) |
| Modelos GGUF | Qwen2.5-Omni 3B + Llama 3.2 8B | Arquitetura híbrida multi-modelo |

---

## Instalação

```bash
# 1. Ambiente Python (na raiz do monorepo)
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 2. Build do llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CUDA=ON   # omitir flag em macOS Apple Silicon
cmake --build build --config Release -j4

# 3. Download do modelo Qwen2.5-Omni 3B (Q4_K_M)
mkdir %USERPROFILE%\models
# Windows (PowerShell):
Invoke-WebRequest -Uri "https://huggingface.co/ggml-org/Qwen2.5-Omni-3B-GGUF/resolve/main/qwen2_5-omni-3b-q4_k_m.gguf" -OutFile "$env:USERPROFILE\models\qwen2_5-omni-3b-q4_k_m.gguf"
# Linux/macOS:
# wget -O ~/models/qwen2_5-omni-3b-q4_k_m.gguf https://huggingface.co/ggml-org/Qwen2.5-Omni-3B-GGUF/resolve/main/qwen2_5-omni-3b-q4_k_m.gguf

# 4. Iniciar o llama-server
./build/bin/llama-server -m ~/models/qwen2_5-omni-3b-q4_k_m.gguf -ngl 99 -c 8192 --flash-attn --host 0.0.0.0 --port 8080
```

#### Variáveis de ambiente opcionais (`.env`)

```env
LLAMA_BASE_URL=http://localhost:8080
LLAMA_MODEL=qwen2.5-omni-3b
LLAMA_NUM_CTX=8192
```

## Como Executar

### Backend via CLI (terminal)

```bash
.venv\Scripts\python.exe backend\main.py
```

Comandos da CLI: `ajuda`, `limpar`, `retomar` (retoma sessão salva), `sair`.

### Backend modo bridge (JSON-lines via stdin/stdout)

```bash
.venv\Scripts\python.exe backend\main.py --bridge
```

Protocolo: `{"id": "1", "comando": "ping"}` → `{"id": "1", "status": "ok", "dados": "pong", "mensagemErro": null}`. Comandos suportados: `ping`, `chat`, `encerrar`, `salvar_memoria`, `listar_memoria`, `deletar_memoria`, `limpar_memorias`, `criar_automacao`, `listar_automacoes`, `deletar_automacao`, `toggle_automacao`, etc.

### Backend modo bridge HTTP (usado pelo frontend Tauri)

```bash
.venv\Scripts\python.exe backend\main.py --bridge-http --porta 8081
```

Expõe o protocolo bridge via REST em `http://127.0.0.1:8081/chat`.

### Frontend Tauri + React (v4.0)

> ✅ **Status:** o frontend Tauri compila e inicia corretamente no Windows. Documentação completa em [`frontend-tauri/IMPLEMENTACAO_COMPLETA.md`](frontend-tauri/IMPLEMENTACAO_COMPLETA.md). Guia de testes em [`docs/GUIA_TESTES_EMPIRICOS.md`](docs/GUIA_TESTES_EMPIRICOS.md).

**Fluxo:**

```bash
# 1. Backend Python (modo bridge HTTP, porta 8081) — necessário para o chat
.venv\Scripts\python.exe backend\main.py --bridge-http

# 2. Frontend Tauri (desenvolvimento)
cd frontend-tauri
npm install
npm run tauri dev

# 3. Build para produção (instalador MSI/DEB)
cd src-tauri && python build_sidecar.py   # gera o sidecar real (1x)
cd .. && npm run tauri build
```

O instalador one-click incluirá:
- Python embeddable (sem necessidade de instalar Python separadamente)
- Modelos GGUF pré-baixados (3B + 8B)
- Backend Python configurado como sidecar Tauri
- Banco SQLite inicializado automaticamente

## Testes

```bash
# Backend (unittest)
.venv\Scripts\python.exe -m unittest discover -s backend/tests -v

# Smoke-test contra o llama-server ao vivo (requer servidor rodando)
.venv\Scripts\python.exe backend/tests/validate_llama_server.py

# Frontend (Vitest)
cd frontend-tauri
npm test
```

---

## Roadmap

| Fase | Status | Descrição |
|------|--------|-----------|
| Migração UI | ✅ Concluída | Frontend Tauri v2 + React com aura rosa (v4.0) |
| Roteamento multi-modelo | 📋 Planejado | Roteamento inteligente de modelos (3B ↔ 8B) |
| Instalador one-click | 📋 Planejado | MSI/DEB/AppImage com Python embeddable e modelos pré-baixados |
| Voz da MARIA | 📋 Planejado | TTS + STT + avatar animado |
| Lançamento Parceiro Fundador | 📋 Planejado | 10 empresas piloto |

O histórico completo do processo de migração está em [`docs/PLANO_MIGRACAO_TAURI_V4.md`](docs/PLANO_MIGRACAO_TAURI_V4.md).

---

## Licença

Projeto em desenvolvimento. Todos os direitos reservados.
