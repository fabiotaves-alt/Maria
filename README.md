# MARIA — Assistente de IA de Escritório, 100% Local

> **Versão atual:** v4.1.1 · **Status:** ✅ Estável

**MARIA** é uma assistente de inteligência artificial para escritório que roda **completamente no seu computador**, sem enviar dados para a internet e sem depender de serviços em nuvem. Ela entende linguagem natural em português, executa tarefas reais (criar documentos, preencher planilhas, transcrever áudio, gerenciar memórias e automações) e aprende com as informações que você compartilha ao longo do tempo.

O modelo de linguagem roda localmente via **llama-server** (llama.cpp) com o **Qwen2.5-Omni 3B**, um modelo multimodal compacto (~2,3 GB) que processa texto, imagem e áudio em um único arquivo GGUF — sem necessidade de GPU dedicada, embora se beneficie muito dela.

---

## Funcionalidades

### Para o usuário
- 💬 **Chat em português** com histórico de contexto e memória persistente entre sessões
- 📄 **Criação de documentos** (.docx) — ofícios, relatórios, atas, e-mails institucionais com formatação automática conforme o Manual de Redação da Presidência da República
- 📊 **Criação e edição de planilhas** (.xlsx) com confirmação antes de qualquer escrita
- 🎤 **Transcrição de áudio** via whisper.cpp (WAV → texto)
- 📎 **Análise de arquivos** (.txt, .md, .csv, .log, .docx, .xlsx) com resumo inteligente
- 🧠 **Memória persistente** — MARIA lembra fatos sobre você entre sessões
- ⚙️ **Automações** — crie e gerencie sequências de ações ativadas por gatilhos
- 📡 **Status do sistema** — CPU, RAM e GPU em tempo real

### Para o desenvolvedor
- 🔌 Três modos de execução: **CLI interativo**, **bridge JSON-lines** (sidecar) e **servidor HTTP REST** (dev)
- 🛡️ Camada de segurança completa: token de autenticação por sessão, CORS por ambiente, validação de caminhos contra path traversal, restrição de binários externos
- 🧪 Suíte de testes automatizados com 115+ testes (pytest)
- 📦 Sistema de benchmark próprio para avaliação de tool calling

---

## Arquitetura

O sistema é um monorepo com dois processos independentes que se comunicam via HTTP local e compartilham um banco SQLite:

```
┌─────────────────────────────────────┐   HTTP JSON (porta 8081)   ┌──────────────────────────────────┐
│  Frontend  —  Tauri v2 + React      │ ◄────────────────────────► │  Backend  —  Python 3.11+        │
│                                     │                             │                                  │
│  • React 18 + TypeScript + Vite     │    Authorization: Bearer    │  • main.py (CLI / bridge HTTP)   │
│  • Tailwind CSS + Framer Motion     │    <token por sessão>       │  • LlamaClient (llama-server)    │
│  • Zustand (estado global)          │                             │  • tools_schema.py (ferramentas) │
│  • useMariaBridge (hook HTTP)       │                             │  • chat_session.py (contexto)    │
│  • Rust: rusqlite, reqwest, sidecar │                             │  • database/ (SQLite)            │
└──────────────────┬──────────────────┘                             └────────────────┬─────────────────┘
                   │ rusqlite (WAL)                                                  │ HTTP localhost:8080
                   ▼                                                          ┌──────▼──────────┐
      ┌─────────────────────────┐                                             │  llama-server   │
      │  shared/maria.db        │ ◄───────────────────────────────────────── │  (llama.cpp)    │
      │  (SQLite, WAL mode)     │            Banco compartilhado              │  Qwen2.5-Omni   │
      │  6 tabelas unificadas   │                                             │  3B  —  Q4_K_M  │
      └─────────────────────────┘                                             └─────────────────┘
```

Em **produção**, o backend é empacotado como **sidecar Tauri** e se comunica via stdin/stdout JSON-lines diretamente com o frontend Rust — sem porta de rede exposta. Em **desenvolvimento**, o frontend Tauri faz chamadas HTTP para o backend Python rodando em paralelo.

Para a arquitetura completa, consulte [`docs/ARQUITETURA_SISTEMA.md`](docs/ARQUITETURA_SISTEMA.md).

---

## Requisitos de Sistema

### Hardware
| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| RAM | 8 GB | 16 GB |
| Armazenamento livre | 10 GB | 20 GB |
| GPU (opcional) | — | NVIDIA com 4 GB VRAM (aceleração CUDA) |

### Software (Windows)
| Dependência | Versão | Para quê |
|-------------|--------|----------|
| Windows | 10 (1809+) ou 11 | Sistema operacional suportado |
| Python | 3.11+ | Backend e scripts |
| Node.js + npm | 18 LTS+ | Frontend React |
| Rust (rustup) | estável | Compilação do Tauri |
| VS Build Tools 2022 | com C++ workload | Compilação Rust/llama.cpp no Windows |
| WebView2 Runtime | atual | Janela do app Tauri |
| llama.cpp (llama-server) | build recente | Servidor do modelo de linguagem local |

> **Linux / macOS:** os passos são equivalentes; substitua os comandos `winget` pelos gerenciadores de pacotes do seu sistema (`apt`, `brew`, etc.) e use `.venv/bin/activate` em vez de `.venv\Scripts\activate`.

---

## Instalação

### 1. Ferramentas do sistema (Windows — PowerShell como Administrador)

```powershell
# Instalar Node.js, Rust, Python e Visual Studio Build Tools de uma vez
winget install OpenJS.NodeJS.LTS Rustlang.Rustup Python.Python.3.11 `
    Microsoft.VisualStudio.2022.BuildTools --silent

# Instalar WebView2 (necessário para o Tauri; já incluído no Windows 11)
winget install Microsoft.EdgeWebView2Runtime

# Recarregar PATH sem reiniciar o terminal
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
            [System.Environment]::GetEnvironmentVariable("Path","User")
```

Verifique as instalações:

```powershell
node --version   # v18+
rustc --version  # stable
python --version # 3.11+
```

> Para um guia mais detalhado com troubleshooting, consulte [`docs/GUIA_INSTALACAO.md`](docs/GUIA_INSTALACAO.md).

### 2. Clonar o repositório e configurar o ambiente Python

```bash
git clone <repo-url>
cd maria

# Criar ambiente virtual na raiz do monorepo
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# Instalar dependências do backend
pip install -r requirements.txt
```

### 3. Compilar o llama.cpp e baixar o modelo

```powershell
# Clonar e compilar llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Com GPU NVIDIA (CUDA):
cmake -B build -DGGML_CUDA=ON
# Sem GPU (CPU only):
# cmake -B build

cmake --build build --config Release -j4
cd ..

# Criar pasta de modelos e baixar o Qwen2.5-Omni 3B (Q4_K_M, ~2,3 GB)
New-Item -ItemType Directory -Force "$env:USERPROFILE\models"
Invoke-WebRequest `
    -Uri "https://huggingface.co/ggml-org/Qwen2.5-Omni-3B-GGUF/resolve/main/qwen2_5-omni-3b-q4_k_m.gguf" `
    -OutFile "$env:USERPROFILE\models\qwen2_5-omni-3b-q4_k_m.gguf"
```

### 4. Instalar dependências do frontend

```bash
cd frontend-tauri
npm install
cd ..
```

### 5. (Opcional) Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do monorepo com os valores que quiser sobrescrever:

```env
# Conexão com o llama-server
LLAMA_BASE_URL=http://localhost:8080
LLAMA_MODEL=qwen2.5-omni-3b
LLAMA_NUM_CTX=8192

# Ambiente de execução: "development" habilita CORS para o Vite dev server
# Em produção, omita ou deixe como "production"
MARIA_ENV=development

# Pasta onde o binário whisper-main está instalado (transcrição de áudio)
# WHISPER_ALLOWED_DIR=C:\caminho\para\bin
```

---

## Como Executar

### Iniciar o llama-server (sempre necessário)

Abra um terminal separado e mantenha-o rodando:

```bash
# Ajuste o caminho conforme onde clonou o llama.cpp
.\llama.cpp\build\bin\Release\llama-server.exe `
    -m "$env:USERPROFILE\models\qwen2_5-omni-3b-q4_k_m.gguf" `
    -ngl 99 -c 8192 --flash-attn --host 127.0.0.1 --port 8080
```

> `-ngl 99` envia todas as camadas para a GPU. Em CPU only, remova essa flag.

---

### Modo 1 — CLI interativo (terminal)

O modo mais simples, sem frontend. Útil para testar o backend isoladamente.

```bash
.venv\Scripts\python.exe backend\main.py
```

Comandos disponíveis no prompt: `ajuda`, `limpar`, `retomar` (retoma sessão salva), `sair`.

---

### Modo 2 — App completo (Tauri + React)

O modo de uso normal. Requer dois processos rodando em paralelo.

**Terminal 1 — Backend Python (bridge HTTP):**

```bash
.venv\Scripts\python.exe backend\main.py --bridge-http
```

O backend gera um token de autenticação em `shared/.bridge_token` e registra no log:
```
INFO — Token da API bridge HTTP regenerado
INFO — Servidor bridge HTTP iniciado em http://127.0.0.1:8081
```

**Terminal 2 — Frontend Tauri (modo desenvolvimento):**

```bash
cd frontend-tauri
npm run tauri dev
```

O app abre automaticamente. O token é lido pelo frontend a cada requisição — nenhuma configuração manual é necessária.

---

### Modo 3 — Build de produção

Gera o instalador final (MSI no Windows, .deb/.AppImage no Linux):

```bash
# Gerar o sidecar do backend (necessário apenas na primeira vez ou após mudanças)
cd frontend-tauri\src-tauri
python build_sidecar.py
cd ..

# Build do instalador
npm run tauri build
```

O instalador gerado em `frontend-tauri/src-tauri/target/release/bundle/` inclui o backend Python empacotado como sidecar — o usuário final não precisa instalar Python separadamente.

---

## Testes

```bash
# Suíte principal do backend (pytest)
.venv\Scripts\python.exe -m pytest backend/tests/test_maria.py -v

# Smoke-test contra o llama-server ao vivo (requer servidor rodando na porta 8080)
.venv\Scripts\python.exe backend/tests/validate_llama_server.py

# Frontend — type-check + build Vite
cd frontend-tauri && npm run build

# Frontend — testes TypeScript (Vitest)
cd frontend-tauri && npm test

# Rust — testes unitários do Tauri
cd frontend-tauri/src-tauri && cargo test
```

> Para o guia completo de testes (build, smoke-test, bridge HTTP, benchmark e E2E), consulte [`docs/GUIA_TESTES_EMPIRICOS.md`](docs/GUIA_TESTES_EMPIRICOS.md).

---

## Segurança

O MARIA foi projetado para rodar 100% localmente. As principais medidas implementadas:

| Medida | Detalhe |
|--------|---------|
| **Autenticação por sessão** | Token de 64 hex chars gerado a cada inicialização, escrito atomicamente em `shared/.bridge_token` (chmod 600 em POSIX). O frontend injeta o token no header `Authorization: Bearer` automaticamente. |
| **CORS por ambiente** | Em `MARIA_ENV=production` (padrão), apenas origens do webview Tauri são aceitas. `http://localhost:5173` (Vite) só é liberado com `MARIA_ENV=development`. |
| **Thread-safety do banco** | SQLite com `check_same_thread=False`, WAL mode, `busy_timeout=5000ms` e double-checked locking na criação da conexão. |
| **Proteção contra PATH hijacking** | O binário do whisper.cpp é validado via `WHISPER_ALLOWED_DIR` — binários fora do diretório permitido são rejeitados. |
| **Path traversal** | Todo acesso a arquivos passa por `resolver_caminho_permitido()`, que resolve symlinks e rejeita caminhos fora das pastas permitidas. |
| **Bind local** | O servidor HTTP escuta exclusivamente em `127.0.0.1` — nunca exposto à rede local. |

Para detalhes completos, resultados do `bandit`, pendências e instruções de teste manual, consulte [`docs/SEGURANCA.md`](docs/SEGURANCA.md).

---

## Estrutura de Pastas

```
maria/
├── README.md                      ← este arquivo
├── CHANGELOG.md                   ← histórico de versões
├── requirements.txt               ← dependências Python (raiz do monorepo)
├── .venv/                         ← ambiente virtual Python
│
├── shared/                        ← recursos compartilhados entre frontend e backend
│   ├── schema.sql                 ← DDL canônico (6 tabelas em português)
│   ├── maria.db                   ← banco SQLite (gerado automaticamente)
│   └── .bridge_token              ← token de sessão HTTP (gerado em runtime, fora do git)
│
├── backend/                       ← backend Python
│   ├── main.py                    ← entry point (CLI / --bridge / --bridge-http)
│   ├── core/
│   │   ├── config.py              ← fonte da verdade: modelos, URLs, parâmetros
│   │   ├── llama_client.py        ← cliente llama-server (produção)
│   │   ├── ollama_client.py       ← cliente Ollama (legado/opcional)
│   │   ├── chat_session.py        ← histórico e prompt de sistema
│   │   ├── tools_schema.py        ← definição e execução das ferramentas
│   │   ├── file_utils.py          ← validação de caminhos e permissões
│   │   ├── manual_redacao.py      ← RAG via FTS5 (Manual de Redação)
│   │   └── tool_chaining.py       ← encadeamento automático de ferramentas de leitura
│   ├── database/
│   │   ├── connection.py          ← conexão SQLite thread-safe (WAL + busy_timeout)
│   │   ├── schema.py              ← criação de tabelas (init_db)
│   │   └── ingest_manual_redacao.py  ← ingestão do Manual de Redação no FTS5
│   ├── tests/
│   │   ├── test_maria.py          ← 115+ testes pytest
│   │   └── validate_llama_server.py  ← smoke-test ao vivo
│   └── benchmark/                 ← sistema de benchmark de tool calling
│
├── frontend-tauri/                ← frontend Tauri v2 + React
│   ├── src/
│   │   ├── App.tsx                ← entry point React
│   │   ├── components/            ← TopBar, Sidebar, CenterStage, ChatPanel
│   │   ├── hooks/                 ← useMariaBridge (HTTP), useTheme
│   │   └── types/                 ← tipos TypeScript compartilhados
│   └── src-tauri/
│       ├── src/main.rs            ← comandos Tauri, rusqlite, bridge Python
│       ├── capabilities/          ← permissões shell (Tauri v2)
│       ├── binaries/              ← sidecar maria-backend (gerado por build_sidecar.py)
│       ├── build_sidecar.py       ← empacota o backend via PyInstaller
│       ├── Cargo.toml
│       └── tauri.conf.json
│
└── docs/                          ← documentação técnica
    ├── ARQUITETURA_SISTEMA.md     ← arquitetura completa e estado por camada
    ├── SEGURANCA.md               ← modelo de ameaças, medidas e pendências
    ├── GUIA_DESENVOLVIMENTO.md    ← guia prático para novos desenvolvedores
    ├── GUIA_TESTES_EMPIRICOS.md   ← 5 níveis de teste (build → E2E)
    ├── GUIA_INSTALACAO.md         ← instalação completa e setup de IA (llama + whisper)
    ├── DECISOES_BANCO_DADOS.md    ← decisões de design do banco
    └── arquivo/                   ← histórico arquivado (diagnósticos, migrações e fases anteriores)
```

---

## Roadmap

| Versão | Status | Descrição |
|--------|--------|-----------|
| v4.0.0 | ✅ Concluída | Migração completa para Tauri v2 + React; bridge HTTP; sidecar |
| v4.1.0 | ✅ Concluída | RAG do Manual de Redação da Presidência (FTS5, 255 trechos) |
| v4.1.1 | ✅ Concluída | Correções críticas de segurança (token atômico, CORS, PATH hijacking, SQLite thread-safe) |
| v4.2.0 | 📋 Planejado | Instalador one-click (MSI/DEB/AppImage com Python embeddable e modelo pré-baixado) |
| v4.3.0 | 📋 Planejado | Roteamento multi-modelo (3B ↔ 8B via `router.py`) |
| v4.4.0 | 📋 Planejado | Voz da MARIA: TTS + STT + avatar animado |
| v5.0.0 | 📋 Planejado | Whisper.cpp empacotado; lançamento para parceiros fundadores |

---

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [`docs/ARQUITETURA_SISTEMA.md`](docs/ARQUITETURA_SISTEMA.md) | Diagrama completo, componentes, protocolo bridge e estado por camada |
| [`docs/SEGURANCA.md`](docs/SEGURANCA.md) | Modelo de ameaças, medidas implementadas e roadmap de segurança |
| [`docs/GUIA_DESENVOLVIMENTO.md`](docs/GUIA_DESENVOLVIMENTO.md) | Setup, padrões de código, fluxo de trabalho e backlog técnico |
| [`docs/GUIA_TESTES_EMPIRICOS.md`](docs/GUIA_TESTES_EMPIRICOS.md) | Como construir e validar os 5 níveis de teste |
| [`docs/GUIA_INSTALACAO.md`](docs/GUIA_INSTALACAO.md) | Instalação passo a passo completa, setup de LLM e Whisper (Windows/PowerShell) |
| [`docs/DECISOES_BANCO_DADOS.md`](docs/DECISOES_BANCO_DADOS.md) | Decisões de design do schema SQLite compartilhado |
| [`CHANGELOG.md`](CHANGELOG.md) | Histórico completo de versões |

---

## Contribuição

1. Faça um fork e crie uma branch descritiva (`feature/nome`, `fix/descricao`)
2. Implemente as mudanças seguindo os padrões do projeto:
   - **Python:** PEP 8, type hints, docstrings nas funções públicas
   - **TypeScript/React:** ESLint + Prettier do projeto, componentes funcionais com hooks
   - **Rust:** `cargo fmt` e `cargo clippy` sem warnings
3. Rode a suíte completa de testes antes de abrir o PR:
   ```bash
   .venv\Scripts\python.exe -m pytest backend/tests/test_maria.py -q
   cd frontend-tauri && npm run build && cargo test
   ```
4. Escreva mensagens de commit claras e em português
5. Abra o Pull Request com descrição do que foi feito e por quê

---

## Licença

Projeto proprietário — todos os direitos reservados. Uso, cópia ou distribuição não autorizados são proibidos.
