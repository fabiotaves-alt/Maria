# MARIA — Assistente de IA Pessoal 100% Local

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo. 

## ⚠️ Status: Em Migração para v4.0 (Tauri + React)

Este projeto está em transição ativa da arquitetura JavaFX (v3.x) para uma arquitetura moderna com **Tauri v2 + React + TypeScript**. Acompanhe o plano completo em [`docs/PLANO_MIGRACAO_TAURI_V4.md`](docs/PLANO_MIGRACAO_TAURI_V4.md).

### 🔄 Arquitetura Atual (v3.x - Legado)

Monorepo com dois processos independentes que se comunicam via IPC (stdin/stdout, protocolo JSON por linha) e banco SQLite compartilhado:

```
┌─────────────────────────┐   JSON-lines    ┌──────────────────────────┐
│  Frontend JavaFX        │ ◄─────────────► │  Backend Python          │
│  (com.tristar.maria)    │   stdin/stdout  │  (llama.cpp + ferramentas)│
│  Java 21 / JavaFX 21    │                 │  Python 3.11+            │
└────────────┬────────────┘                 └───────────┬──────────────┘
             │                                          │ HTTP localhost
             │ JDBC (WAL)                         ┌─────▼──────────┐
             ▼                                    │  llama-server  │
    ┌─────────────────┐                           │  :8080         │
    │ shared/maria.db │ ◄──────────────────────── │  Qwen2.5-Omni  │
    └─────────────────┘                           └────────────────┘
```

### 🚀 Nova Arquitetura (v4.0 - Em Desenvolvimento)

```
┌─────────────────────────┐   HTTP/Tauri IPC   ┌──────────────────────────┐
│  Frontend Tauri + React │ ◄────────────────► │  Backend Python (MANTIDO)│
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

**Principais Mudanças:**
- **Frontend**: JavaFX 21 → Tauri v2 + React + TypeScript + Tailwind CSS
- **Comunicação**: JSON-lines stdin/stdout → HTTP local (localhost:8081) + IPC nativo Tauri
- **Design**: UI "de 2010" → Design moderno com glassmorphism, aura rosa e animações fluidas
- **Instalação**: Manual e complexa → MSI one-click com Python embeddable e modelos pré-baixados
- **Modelos**: Qwen 3.5B único → Arquitetura híbrida (3.5B + 8B + CodeQwen 7B com roteamento inteligente)

---

## Arquitetura Detalhada (v3.x - Versão Estável Atual)

- **Frontend**: interface JavaFX 21 com 8 abas (Conversar, Arquivos, Análise de Dados, Visão, Voz, Memória, Automações, Configurações), tema claro/escuro dinâmico e bridge para o backend.
- **Backend**: `LlamaClient` (API OpenAI-compatible) conectado ao llama-server com histórico de contexto, prompt de sistema em pt-BR anti-alucinação, function calling com confirmação, suporte multimodal (imagem + áudio), geração de arquivos reais e persistência de sessões.
- **Banco de Dados**: SQLite compartilhado em `shared/maria.db` com schema canônico definido em `shared/schema.sql` (WAL mode e integridade referencial com ON DELETE CASCADE).

## Estrutura de Pastas

### v4.0 (Nova Arquitetura - Em Desenvolvimento)

```
maria/
├── README.md                  ← este arquivo
├── requirements.txt           ← dependências Python consolidadas
├── .venv/                     ← ambiente virtual Python (raiz do monorepo)
├── docs/                      ← documentação técnica e relatórios
│   ├── PLANO_MIGRACAO_TAURI_V4.md  ← plano completo de migração
│   └── ...                    ← demais documentos técnicos
├── shared/                    ← banco SQLite compartilhado e DDL
│   ├── schema.sql             ← schema canônico unificado em português
│   └── maria.db               ← arquivo de banco de dados SQLite
├── backend/                   ← MANTIDO (Python existente, intacto)
│   ├── main.py                ← Modo bridge HTTP (porta 8081) + CLI
│   ├── core/                  ← LlamaClient, tools, handlers (INTACTO)
│   ├── database/              ← connection.py e schema.py
│   ├── tests/                 ← 86 testes pytest (MANTIDOS)
│   └── benchmark/             ← sistema de benchmark live
└── frontend-tauri/            ← atual (Tauri v2 + React, v4.0)
    ├── src/                   ← React + TypeScript
    │   ├── components/        ← TopBar, Sidebar, CenterStage, ChatPanel
    │   ├── pages/             ← ConversarPage, etc.
    │   ├── hooks/             ← useTheme, useMariaBridge
    │   └── App.tsx
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

### v3.x (Arquitetura Atual - Legado)

```
maria/
├── README.md                  ← este arquivo
├── requirements.txt           ← dependências Python consolidadas (inclui psutil)
├── .venv/                     ← ambiente virtual Python (raiz do monorepo)
├── docs/                      ← documentação técnica e relatórios
│   ├── ARQUITETURA_SISTEMA.md
│   ├── DECISOES_BANCO_DADOS.md
│   ├── GUIA_DESENVOLVIMENTO.md
│   ├── GUIA_DESENVOLVIMENTO_FASE3.md
│   ├── GUIA_TESTES_EMPIRICOS.md
│   ├── IMPLEMENTACAO_DAO.md
│   ├── INSTALACAO_WHISPER.md
│   ├── INTEGRACAO_FRONTEND.md
│   ├── PENDENCIAS_INTERFACE.md
│   ├── RELATORIO_ESTADO_ATUAL.md
│   └── RELATORIO_IMPLEMENTACAO_FASE3.md
├── shared/                    ← banco SQLite compartilhado e DDL
│   ├── schema.sql             ← schema canônico unificado em português
│   └── maria.db               ← arquivo de banco de dados SQLite
├── backend/
│   ├── main.py                ← CLI interativa + modo --bridge (frontend)
│   ├── ui_terminal.py         ← interface de terminal legada
│   ├── core/                  ← llama_client, ollama_client, chat_session,
│   │                            tools_schema, excel_handler, word_handler,
│   │                            file_utils, session_storage, tool_chaining, config
│   ├── database/              ← connection.py (SQLite singleton) e schema.py
│   ├── tests/
│   │   ├── test_maria.py      ← suíte de testes unitários (unittest)
│   │   └── validate_llama_server.py ← smoke-test para o llama-server ao vivo
│   └── benchmark/             ← sistema de benchmark live (opcional)
└── frontend/                  ← LEGADO (será substituído por frontend-tauri/)
    ├── pom.xml                ← Maven (Java 21, JavaFX 21, SQLite JDBC, JUnit 5)
    └── src/
        ├── main/
        │   ├── java/com/tristar/maria/
        │   │   ├── App.java       ← ponto de entrada JavaFX com detecção de SO
        │   │   ├── bridge/        ← PythonBridgeService, Requisicao, Resposta, BridgeManager
        │   │   ├── dao/           ← DatabaseManager, ConversaDAO, MemoriaDAO, AutomacaoDAO, ConfiguracaoDAO
        │   │   └── ui/            ← MainController + controllers das 8 abas
        │   └── resources/com/tristar/maria/
        │       ├── *.fxml         ← views das abas
        │       └── theme-*.css    ← temas escuro (pink aura) / claro
        └── test/java/com/tristar/maria/
            └── dao/DatabaseManagerTest.java ← 8 testes JUnit 5 de persistência
```

## Pré-requisitos

### Para v3.x (Versão Atual - JavaFX)

| Requisito | Versão | Observação |
|-----------|--------|------------|
| Python | 3.11+ | venv na raiz (` .venv/`) |
| llama.cpp | build recente | compilar com `-DGGML_CUDA=ON` (NVIDIA) ou Metal (macOS) |
| Modelo GGUF | `qwen2_5-omni-3b-q4_k_m.gguf` | ~2.3 GB — ver seção Instalação |
| JDK | 21 | OpenJDK / Temurin / Oracle JDK 21 |
| Maven | 3.9+ | ou wrapper integrado da IDE |

### Para v4.0 (Nova Versão - Tauri + React)

| Requisito | Versão | Observação |
|-----------|--------|------------|
| Python | 3.11+ | venv na raiz (` .venv/`) |
| Node.js | 18+ | para frontend React |
| Rust | 1.70+ | para Tauri v2 |
| llama.cpp | build recente | compilar com `-DGGML_CUDA=ON` (NVIDIA) ou Metal (macOS) |
| Modelos GGUF | Qwen2.5-Omni 3B + Llama 3.2 8B | Arquitetura híbrida multi-modelo |

> **Nota:** A versão v4.0 eliminará a necessidade de JDK e Maven, simplificando significativamente a instalação.

---

### Instalação (v3.x - Versão Atual)

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

### v3.x (Versão Atual - JavaFX)

#### Frontend JavaFX (interface gráfica)

```bash
cd frontend
mvn javafx:run
```

O frontend detecta o SO e inicia automaticamente o processo Python (`backend/main.py --bridge`) e valida a conexão com handshake ping/pong.

#### Backend via CLI (terminal)

```bash
.venv\Scripts\python.exe backend\main.py
```

Comandos da CLI: `ajuda`, `limpar`, `retomar` (retoma sessão salva), `sair`.

#### Backend modo bridge (usado pelo frontend)

```bash
.venv\Scripts\python.exe backend\main.py --bridge
```

Protocolo: `{"id": "1", "comando": "ping"}` → `{"id": "1", "status": "ok", "dados": "pong", "mensagemErro": null}`. Comandos suportados: `ping`, `chat`, `encerrar`, `salvar_memoria`, `listar_memoria`, `deletar_memoria`, `limpar_memorias`, `criar_automacao`, `listar_automacoes`, `deletar_automacao`, `toggle_automacao`, etc.

#### Testes

```bash
# Testes do Backend (unittest)
.venv\Scripts\python.exe -m unittest discover -s backend/tests -v

# Smoke-test contra o llama-server ao vivo (requer servidor rodando)
.venv\Scripts\python.exe backend/tests/validate_llama_server.py

# Testes do Frontend (8 testes JUnit 5)
cd frontend
mvn test
```

---

### v4.0 (Nova Versão - Funcional)

> ✅ **Status:** o frontend Tauri compila e inicia corretamente no Windows. Documentação completa em [`frontend-tauri/IMPLEMENTACAO_COMPLETA.md`](frontend-tauri/IMPLEMENTACAO_COMPLETA.md). Roadmap em [`docs/PLANO_MIGRACAO_TAURI_V4.md`](docs/PLANO_MIGRACAO_TAURI_V4.md). Guia de testes em [`docs/GUIA_TESTES_EMPIRICOS.md`](docs/GUIA_TESTES_EMPIRICOS.md).

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

---

## Roadmap de Migração

| Fase | Versão | Status | Descrição |
|------|--------|--------|-----------|
| Fase 1 | v3.3 | 📋 Planejado | UI Tauri + React pixel-perfect com aura rosa |
| Fase 2 | v3.4 | 📋 Planejado | Roteamento inteligente de modelos (3B ↔ 8B) |
| Fase 3 | v3.5 | 📋 Planejado | Instalador one-click (MSI/DEB/AppImage) |
| Fase 4 | v3.6 | 📋 Planejado | Voz da MARIA (TTS + STT + avatar animado) |
| Fase 5 | v4.0 | 📋 Planejado | Lançamento Parceiro Fundador (10 empresas piloto) |

Para detalhes completos, veja [`docs/PLANO_MIGRACAO_TAURI_V4.md`](docs/PLANO_MIGRACAO_TAURI_V4.md).

---

## Licença

Projeto em desenvolvimento. Todos os direitos reservados.
