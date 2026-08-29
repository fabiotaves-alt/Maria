# Guia de Implementação Completa - MARIA v4.0

## ✅ Status da Implementação

### Frontend React + Tauri (COMPLETO)
- [x] Interface pixel-perfect com temas claro/escuro
- [x] Layout de 3 colunas (Sidebar 260px | Centro flex | Chat 380px)
- [x] Glassmorphism em todos os cards
- [x] Animações Framer Motion (aura, breathe, pulse, message appear)
- [x] Componentes: TopBar, Sidebar, CenterStage, ChatPanel
- [x] Sistema de temas com persistência localStorage
- [x] Barras de recursos (CPU/RAM/GPU) com dados reais via backend
- [x] Badge dinâmico do modelo ativo (Qwen 3B / Llama 7B)

### Backend Rust (COMPLETO - Compilando e Rodando ✅)
- [x] `Cargo.toml` atualizado com rusqlite, chrono, uuid e reqwest
- [x] `main.rs` com comandos:
  - `send_message()` - envia mensagem para o backend Python (HTTP em dev / sidecar em prod)
  - `get_status()` - obtém status do sistema
  - `get_chat_history()` - lê SQLite diretamente (Rust → DB)
  - `save_message()` - salva mensagens no SQLite
  - `read_file()` - lê arquivos do sistema
  - `save_file()` - salva conteúdo em arquivos
  - `ping()` - health check
- [x] `build.rs` criado com `tauri_build::build()` (requisito do `generate_context!()`)
- [x] Comandos `#[tauri::command]` declarados **sem `pub`** — padrão oficial do Tauri (corrige erro `E0255: __cmd__... defined multiple times`)
- [x] `tauri.conf.json` configurado para:
  - Sidecar `maria-backend` via `externalBin`
  - Plugin updater OTA
  - Plugin shell na sintaxe v2 (`"open": true`)
- [x] `capabilities/default.json` com `shell:allow-execute` (permissões para o sidecar `maria-backend`, `python` e `python3`)
- [x] `icons/` e `binaries/` criados (necessários para o `tauri-build` no Windows)
- [x] Validação: `cargo check` e `cargo check --release` passam sem erros; `maria-frontend.exe` inicia sem panic

### Backend Python (EXISTENTE - Adaptado)
- [x] `backend/core/router.py` - Roteador MoE implementado
  - Tarefas simples → Qwen 2.5 Omni 3B
  - Tarefas complexas → Llama 3.2 8B
  - Visão/áudio → Qwen 2.5 Omni 3B (multimodal)
- [x] `backend/main.py --bridge` - Modo bridge funcional
  - Comandos: `chat`, `status`, `analisar_arquivo`, `upload_arquivo`, etc.
  - Respostas JSON padronizadas
  - Métricas reais de CPU/RAM/GPU via psutil

### Scripts de Build (COMPLETO)
- [x] `src-tauri/build_sidecar.py` - Script PyInstaller
- [x] `src-tauri/binaries/` - Diretório para executável sidecar

---

## 🚀 Como Rodar o Projeto

### Pré-requisitos

```bash
# Node.js 18+ e npm
node --version  # v18 ou superior
npm --version   # v9 ou superior

# Python 3.10+
python --version  # 3.10 ou superior

# Rust (para build Tauri)
# Instalar via: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustc --version   # 1.70 ou superior
cargo --version

# Dependências Python
pip install -r requirements.txt
```

### 1. Desenvolvimento (Hot Reload)

```bash
cd frontend-tauri

# Instalar dependências npm
npm install

# Rodar em modo desenvolvimento (frontend + Tauri)
npm run tauri dev
```

**Nota:** O backend Python deve estar rodando separadamente (modo bridge HTTP, porta 8081):
```bash
cd backend
python main.py --bridge-http
```

> ⚠️ **Assets obrigatórios do `tauri-build`** (já criados neste repo):
> - `src-tauri/binaries/maria-backend-x86_64-pc-windows-msvc.exe` — exigido por `externalBin` (placeholder em dev)
> - `src-tauri/icons/` — `32x32.png`, `128x128.png`, `icon.ico`, `icon.icns`
> - `src-tauri/build.rs` — build script do Tauri (obrigatório)
>
> Em produção, substitua o placeholder pelo sidecar real com `python src-tauri/build_sidecar.py`.

### 2. Build de Produção

```bash
cd frontend-tauri

# 1. Construir sidecar Python
python src-tauri/build_sidecar.py

# 2. Build completo do Tauri
npm run tauri build
```

Saída:
- Windows: `src-tauri/target/release/bundle/msi/MARIA_4.0.0_x64_en-US.msi`
- macOS: `src-tauri/target/release/bundle/dmg/MARIA_4.0.0_x64.dmg`
- Linux: `src-tauri/target/release/bundle/appimage/MARIA_4.0.0_amd64.AppImage`

---

## 📁 Estrutura de Arquivos

```
workspace/
├── backend/
│   ├── main.py                 # Backend Python (modo bridge)
│   ├── core/
│   │   └── router.py           # Roteador MoE (3B ↔ 8B)
│   └── ...
├── frontend-tauri/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TopBar/
│   │   │   ├── Sidebar/
│   │   │   ├── CenterStage/
│   │   │   └── ChatPanel/
│   │   ├── hooks/
│   │   │   ├── useTheme.tsx
│   │   │   └── useMariaBridge.ts
│   │   ├── types/
│   │   └── App.tsx
│   ├── src-tauri/
│   │   ├── src/
│   │   │   └── main.rs         # Comandos Tauri + rusqlite + bridge Python
│   │   ├── capabilities/
│   │   │   └── default.json    # Permissões shell:allow-execute (sidecar + Python)
│   │   ├── binaries/
│   │   │   └── maria-backend   # Sidecar (gerado por build_sidecar.py)
│   │   ├── icons/              # Ícones 32x32.png, 128x128.png, icon.ico, icon.icns
│   │   ├── build.rs            # Build script Tauri (tauri_build::build())
│   │   ├── gen_icons.py        # Gera ícones placeholder (opcional)
│   │   ├── build_sidecar.py    # Script PyInstaller
│   │   ├── Cargo.toml          # rusqlite, chrono, uuid, reqwest + plugins Tauri
│   │   └── tauri.conf.json     # externalBin + updater + plugin shell (v2)
│   └── package.json
└── shared/
    └── maria.db                # SQLite (histórico de chats)
```

---

## 🔌 Comunicação Frontend ↔ Backend

### Fluxo de Mensagens

```
┌─────────────┐      invoke()      ┌─────────────┐      HTTP/Stdin     ┌─────────────┐
│   React UI  │ ─────────────────▶ │  Rust (Tauri) │ ─────────────────▶ │  Python     │
│  ChatPanel  │                    │  main.rs     │                    │  main.py    │
└─────────────┘                    └─────────────┘                    └─────────────┘
       ▲                                  │                                  │
       │                                  │                                  │
       │            SQLite (rusqlite)     │            LLM (Ollama/llama.cpp)│
       │◀─────────────────────────────────┘                                  │
       │                                                                     │
       └─────────────────────────────────────────────────────────────────────┘
                         Resposta JSON parseada
```

### Comandos Disponíveis

| Comando Rust | Descrição | Origem dos Dados |
|--------------|-----------|------------------|
| `send_message(text)` | Envia mensagem ao LLM | Python (HTTP dev / sidecar prod) |
| `get_status()` | CPU, RAM, GPU, modelo | Python (psutil) |
| `get_chat_history(id)` | Histórico de conversas | SQLite (Rust direto) |
| `save_message(conv, role, content)` | Salva nova mensagem | SQLite (Rust direto) |
| `read_file(path)` | Lê arquivo do sistema | Rust (tokio::fs) |
| `save_file(path, content)` | Salva conteúdo em arquivo | Rust (tokio::fs) |
| `ping()` | Health check | Rust |

---

## 🔐 Permissões Shell (Tauri v2)

No Tauri v2, o escopo de execução de comandos do plugin shell **não** fica mais no `tauri.conf.json` (sintaxe v1 removida). Ele é declarado em **arquivos de capability**:

### `src-tauri/capabilities/default.json`

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability principal da janela main",
  "windows": ["main"],
  "permissions": [
    "core:default",
    {
      "identifier": "shell:allow-execute",
      "allow": [
        { "name": "maria-backend", "sidecar": true, "args": true },
        { "name": "python", "cmd": "python", "args": true },
        { "name": "python3", "cmd": "python3", "args": true }
      ]
    }
  ]
}
```

- **`shell:allow-execute`** habilita a execução de comandos via frontend.
- O escopo (`allow`) define exatamente **quais** comandos podem ser executados e com quais argumentos (`args: true` = qualquer argumento).
- A chave `"open": true` em `tauri.conf.json → plugins.shell` habilita o `shell.open()` (abrir links externos).

---

## 🧠 Roteamento de Modelos (MoE)

### Como Funciona

O roteador analisa a complexidade da mensagem e decide qual modelo usar:

```python
# backend/core/router.py

mensagem = "Oi, tudo bem?"
→ Score: 0.0 (simples)
→ Modelo: Qwen 2.5 Omni 3B (rápido, ~1-3s)

mensagem = "Gere um relatório jurídico detalhado de 10 páginas"
→ Score: 0.85 (complexo)
→ Modelo: Llama 3.2 8B (potente, ~5-15s)
```

### Palavras-chave que Ativam Llama 8B

- `relatório`, `relatorio`, `análise profunda`
- `código`, `script`, `programa`, `desenvolver`
- `jurídico`, `juridico`, `contrato`, `cláusula`
- `financeiro`, `contábil`, `imposto`
- `compare`, `contraste`, `síntese`
- Mensagens > 100 palavras
- Múltiplas perguntas (>1 `?`)

---

## 🎨 Customização Visual

### Variáveis CSS (Tailwind)

```css
/* Tema Claro */
--maria-bg: #f0eeeb;
--maria-text: #1a1a1a;
--maria-muted: #6b6b6b;
--maria-pink: #e85a8a;
--maria-card-bg: rgba(255, 255, 255, 0.7);
--maria-card-border: rgba(0, 0, 0, 0.06);

/* Tema Escuro */
--maria-bg: #0d0d12;
--maria-text: #f0f0f0;
--maria-muted: #9a9a9a;
--maria-pink: #ff6b9d;
--maria-card-bg: rgba(255, 255, 255, 0.05);
--maria-card-border: rgba(255, 255, 255, 0.08);
```

### Animações CSS

```css
@keyframes aura-pulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.1); }
}

@keyframes avatar-breathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(1.3); }
}
```

---

## 🔄 Atualizações OTA (Over-the-Air)

### Configuração

```json
// tauri.conf.json
{
  "plugins": {
    "updater": {
      "active": true,
      "endpoints": ["https://maria-ai.app/api/updater/{{target}}/{{arch}}/{{current_version}}"],
      "dialog": true,
      "pubkey": "YOUR_PUBLIC_KEY_HERE"
    }
  }
}
```

### Gerar Chave Pública

```bash
# Instalar cargo-crate
cargo install cargo-crate

# Gerar par de chaves
crate generate-keypair

# Saída: chave pública (adicionar ao tauri.conf.json)
```

---

## 📊 Métricas e Monitoramento

### Recursos do Sistema

O backend Python coleta métricas em tempo real:

```python
import psutil

cpu_percent = psutil.cpu_percent(interval=None)
ram_percent = psutil.virtual_memory().percent

# GPU NVIDIA (opcional)
import pynvml
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)
gpu_percent = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
```

### Exibição na UI

```tsx
// Sidebar.tsx
useEffect(() => {
  const loadStatus = async () => {
    const status = await getSystemStatus();
    setSystemStatus([
      { label: 'CPU', value: status.cpu },
      { label: 'RAM', value: status.ram },
      { label: 'GPU', value: status.gpu },
    ]);
    setModeloAtivo(status.modelo);
  };
  
  loadStatus();
  const interval = setInterval(loadStatus, 2000);
  return () => clearInterval(interval);
}, []);
```

---

## 🧪 Testes

### Testar Comunicação Backend

```bash
# Terminal 1: Backend Python (modo bridge HTTP)
cd backend
python main.py --bridge-http

# Terminal 2: Enviar comando via HTTP (protocolo consumido pelo frontend Tauri)
curl -X POST http://localhost:8081/chat -H "Content-Type: application/json" \
  -d '{"id":"test-1","comando":"ping","dados":{}}'
# Saída: {"id":"test-1","status":"ok","dados":"pong","mensagemErro":null}

curl -X POST http://localhost:8081/chat -H "Content-Type: application/json" \
  -d '{"id":"test-2","comando":"status","dados":{}}'
# Saída: {"id":"test-2","status":"ok","dados":{"cpu":12.5,"ram":45.2,"gpu":0.0,"modelo":"qwen2.5-omni-3b"},"mensagemErro":null}
```

### Testar Frontend

```bash
cd frontend-tauri
npm run tauri dev

# No DevTools do Tauri:
window.__TAURI__.core.invoke('ping')
# → "pong"

window.__TAURI__.core.invoke('get_status')
# → { cpu: 12.5, ram: 45.2, gpu: 0, modelo: "Qwen 2.5 3B" }
```

---

## 📝 Próximos Passos (Roadmap)

### Fase 1 - Integração Completa ✅
- [x] Hook useMariaBridge
- [x] ChatPanel com dados reais
- [x] Sidebar com métricas reais
- [x] Rust acessa SQLite diretamente

### Fase 2 - Multi-Modelo (MoE) ✅
- [x] Router backend/core/router.py
- [x] Badge dinâmico na sidebar
- [ ] Streaming WebSocket (respostas em tempo real)

### Fase 3 - Empacotamento 1-Clique ⏳
- [x] Script build_sidecar.py
- [x] Build Tauri validado (dev e release — `cargo check` sem erros, app inicia)
- [x] Capabilities com `shell:allow-execute`
- [ ] Sidecar real (`build_sidecar.py`) testado em Windows limpo (sem Python)
- [ ] Wizard de primeira execução

### Fase 4 - Programa Fundador 📅
- [ ] Landing page de captação
- [ ] Dashboard de feedback
- [ ] Sistema de métricas anônimas (opt-in)

---

## 🆘 Troubleshooting

### Erro: "Backend offline"

**Causa:** Python não está rodando ou porta 8081 ocupada.

**Solução:**
```bash
# Verificar se backend está rodando
ps aux | grep main.py

# Matar processo travado
kill $(pgrep -f main.py)

# Reiniciar backend
cd backend && python main.py --bridge-http
```

### Erro: "rusqlite não encontrado"

**Causa:** Dependência Rust faltando.

**Solução:**
```bash
cd frontend-tauri/src-tauri
cargo update
cargo build
```

### Erro: "PyInstaller não encontrado"

**Causa:** PyInstaller não instalado no ambiente Python.

**Solução:**
```bash
pip install pyinstaller
# OU
python src-tauri/build_sidecar.py  # Instala automaticamente
```

### Erro: `__cmd__ping` is defined multiple times (E0255)

**Sintoma:** Erro de compilação no `main.rs` apontando para **toda** função `#[command]`.

**Causa:** Funções de comando declaradas como `pub fn`. No Tauri v2, `#[tauri::command]` + `pub` + multi-crate-type gera os `macro_rules!` `__cmd__...` duas vezes (issue oficial tauri-apps/tauri #15921).

**Solução:** Remover o `pub` dos comandos (padrão do scaffold oficial do Tauri):
```rust
#[command]
async fn ping() -> Result<String, String> { ... }  // sem "pub"
```

### Erro: `OUT_DIR env var is not set, do you have a build script?`

**Causa:** Arquivo `src-tauri/build.rs` ausente — o `tauri::generate_context!()` depende das variáveis definidas pelo build script.

**Solução:** Criar `src-tauri/build.rs`:
```rust
fn main() {
    tauri_build::build()
}
```

### Erro: `PluginInitialization("shell", ... unknown field 'scope', expected 'open')`

**Causa:** `tauri.conf.json` usando a sintaxe v1 (`"scope"`/`"sidecar"`) no bloco `plugins.shell`, removida no Tauri v2.

**Solução:** Usar o formato v2 e mover o escopo de execução para as capabilities:
```json
"plugins": { "shell": { "open": true } }
```
Conforme descrito na seção [Permissões Shell](#-permissões-shell-tauri-v2).

### Erro: `resource path binaries\maria-backend-...exe doesn't exist`

**Causa:** O binário listado em `bundle.externalBin` não existe — exigido pelo `tauri-build` mesmo em dev.

**Solução:** Criar `src-tauri/binaries/` com o placeholder (dev) ou o binário real:
```bash
python src-tauri/build_sidecar.py   # gera o sidecar real (PyInstaller)
```

### Erro: `icons/icon.ico not found`

**Causa:** Faltando `src-tauri/icons/` no Windows (necessário para gerar o recurso do executável).

**Solução:** Adicionar `32x32.png`, `128x128.png`, `icon.ico` e `icon.icns` (ex.: rodar `python src-tauri/gen_icons.py` para placeholders).

---

## 📞 Suporte

- **Documentação:** `/backend/README.md`
- **Changelog:** `/CHANGELOG.md`
- **Issues:** GitHub Issues
- **Discord:** [link]

---

**MARIA v4.0** - Assistente de IA Pessoal 100% Local  
© 2024 TriStar Intelligence Systems
