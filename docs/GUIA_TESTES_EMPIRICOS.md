# Guia de Testes Empíricos — MARIA v4.0

**Versão:** v4.0.0
**Última atualização:** 2026-08-29
**Escopo:** Backend Python (Flask bridge HTTP + LlamaClient) + Frontend Tauri v2/React + Sidecar PyInstaller

Este guia descreve, passo a passo, como **construir** e **executar** os testes do sistema MARIA, do build inicial ao teste de ponta a ponta em máquina limpa. Os comandos são para **PowerShell no Windows** (ambiente de referência do projeto).

---

## Visão geral — 5 níveis de teste

| Nível | O que valida | Tempo | Requer modelo LLM? |
|---|---|---|---|
| **0.** Construção/ambientes | Ambiente pronto para testar | 2–10 min | ❌ |
| **1.** Testes automatizados | Lógica de cada módulo isolada (Python, Rust, TS) | ~1 min | ❌ |
| **2.** Validação do llama-server ao vivo | LLM responde (texto/stream/visão/áudio) | 1–2 min | ✅ (GPU) |
| **3.** Integração HTTP (bridge) | Backend ↔ frontend via `localhost:8081` | ~2 min | Parcial |
| **4.** Benchmark de tool calling | Qualidade das tarefas reais | 5–40 min | ✅ |
| **5.** E2E de UI (dev e instalador) | App completo de ponta a ponta | 10–30 min | ✅ |

> **Modelo padrão em produção:** `qwen2.5-omni-3b` via llama-server (`backend/core/llama_client.py`), configurado em `backend/core/config.py` (`LLAMA_MODEL`, `LLAMA_BASE_URL=http://localhost:8080`). `qwen3.5:4b` via Ollama é caminho legado/opcional.

---

## NÍVEL 0 — Construção e ambientes

### 0.1 Backend Python

```powershell
cd c:\Users\betti\IdeaProjects\Maria
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Teste rápido de que o backend importa sem erros:

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\main.py
# Sem saída = OK (exit code 0)
```

### 0.2 Frontend Tauri (Node)

```powershell
cd c:\Users\betti\IdeaProjects\Maria\frontend-tauri
npm install
```

### 0.3 Sidecar do backend (gera o executável empacotado)

```powershell
cd c:\Users\betti\IdeaProjects\Maria\frontend-tauri\src-tauri
$env:PYTHONIOENCODING = "utf-8"   # evita UnicodeEncodeError (cp1252) no Windows
python build_sidecar.py
```

**Verificação:** `frontend-tauri\binaries\maria-backend-x86_64-pc-windows-msvc.exe` deve ter **~20 MB** (nunca 0 bytes — 0 bytes indica stub quebrado).

### 0.4 Build completo do instalador

```powershell
cd c:\Users\betti\IdeaProjects\Maria\frontend-tauri
npm run tauri build
```

**Artefatos gerados em:** `frontend-tauri\src-tauri\target\release\bundle\`

- `msi\MARIA_4.0.0_x64_en-US.msi`
- `nsis\MARIA_4.0.0_x64-setup.exe`

---

## NÍVEL 1 — Testes automatizados

### 1.1 Backend Python (unittest)

Cobre lógica determinística: `ChatSession`, `tools_schema`, `excel_handler`, `file_utils`, `session_storage`, token/tool chaining, `LlamaClient` (com mocks de rede) e métricas de benchmark.

```powershell
cd c:\Users\betti\IdeaProjects\Maria
.\.venv\Scripts\python.exe -m unittest discover -s backend\tests -v
```

**Resultado esperado:** `OK` no final, sem `FAIL`/`ERROR` (arquivo principal: `backend/tests/test_maria.py`).

### 1.2 Rust (Tauri)

```powershell
cd c:\Users\betti\IdeaProjects\Maria\frontend-tauri\src-tauri
cargo test
```

**Resultado esperado:** `test result: ok. 1 passed; 0 failed` (teste `test_garantir_conversa_e_insercao_de_mensagem`).

### 1.3 TypeScript (Vitest)

```powershell
cd c:\Users\betti\IdeaProjects\Maria\frontend-tauri
npm run test
```

**Resultado esperado:** `Test Files  1 passed (1)` e `Tests  1 passed (1)`.

> **Dica:** `cargo check` (debug) e `cargo check --release` validam a compilação sem erros/warnings de import — o release é o que compila o código de produção (spawn do sidecar).

---
## NÍVEL 2 — Validação do llama-server ao vivo

> **Pré-requisito:** binário `llama-server` (llama.cpp com suporte multimodal) e modelo `qwen2.5-omni-3b.gguf`. Configurações em `backend/core/config.py` (`LLAMA_BASE_URL`, `LLAMA_MODEL`).

### 2.1 Subir o servidor

```powershell
llama-server -m <caminho>\qwen2.5-omni-3b.gguf --port 8080
```

### 2.2 Rodar a bateria de validação

```powershell
cd c:\Users\betti\IdeaProjects\Maria
.\.venv\Scripts\python.exe backend\tests\validate_llama_server.py
```

Executa, na ordem:

1. `[1]` GET `/v1/models` (conexão) — **aborta** se o servidor estiver inacessível
2. `[2]` Chat texto simples
3. `[3]` Streaming (medição de tokens/s e TTFT)
4. `[4]` Visão — opcional: `--image imagem.jpg`
5. `[5]` Áudio — opcional: `--audio audio.wav`

**Resultado esperado:** `=== Resultado: X/X testes passaram ===` e exit code 0.

---

## NÍVEL 3 — Integração HTTP (bridge)

### 3.1 Subir o backend

```powershell
cd c:\Users\betti\IdeaProjects\Maria
.\.venv\Scripts\python.exe backend\main.py --bridge-http --porta 8081
```

**Alternativa — sidecar standalone** (valida o exe empacotado, sem Tauri):

```powershell
.\frontend-tauri\binaries\maria-backend-x86_64-pc-windows-msvc.exe --bridge-http --porta 8081
```

### 3.2 Testar os endpoints (outro terminal)

```powershell
# Ping
curl.exe -X POST http://localhost:8081/chat -H "Content-Type: application/json" -d '{"id":"1","comando":"ping","dados":{}}'
# Esperado: {"dados":"pong","id":"1","mensagemErro":null,"status":"ok"}

# Status (métricas reais + modelo)
curl.exe -X POST http://localhost:8081/chat -H "Content-Type: application/json" -d '{"id":"2","comando":"status","dados":{}}'
# Esperado: {"status":"ok","dados":{"cpu":..,"ram":..,"gpu":..,"plataforma":"Windows","modelo":"qwen2.5-omni-3b"}}

# Health check
curl.exe http://localhost:8081/ping
# Esperado: {"status":"ok","dados":"pong"}

# Chat (requer llama-server ativo)
curl.exe -X POST http://localhost:8081/chat -H "Content-Type: application/json" -d '{"id":"3","comando":"chat","dados":{"mensagem":"Ola, quem e voce?"}}'
# Esperado: status ok com texto de resposta
```

**Critério do card "RECURSOS DO SISTEMA":** `dados.cpu/ram/gpu` devem variar (não 0.0 fixos). Nota: a **1ª amostra** de CPU pode ser 0 por semântica de `psutil.cpu_percent(interval=None)` — faça 2 chamadas seguidas.

---

## NÍVEL 4 — Benchmark de tool calling

> **Pré-requisito:** llama-server rodando na porta 8080 com `qwen2.5-omni-3b` (o CLI aborta com mensagem clara se não conectar).

### 4.1 Execução padrão

```powershell
cd c:\Users\betti\IdeaProjects\Maria
.\.venv\Scripts\python.exe -m benchmark.run_benchmark --tasks 25
```

### 4.2 Variações úteis

```powershell
# Tarefas específicas
.\.venv\Scripts\python.exe -m benchmark.run_benchmark --task-ids 1 2 3

# Por categoria
.\.venv\Scripts\python.exe -m benchmark.run_benchmark --category criar_planilha

# Mais/menos repetições por tarefa (padrão: 3)
.\.venv\Scripts\python.exe -m benchmark.run_benchmark --tasks 5 --repeticoes 5

# Pasta de saída customizada
.\.venv\Scripts\python.exe -m benchmark.run_benchmark --tasks 5 --output-dir benchmark/results
```

### 4.3 Resultados gerados

- `backend\benchmark\results\run_<timestamp>\report.md` — relatório legível
- `backend\benchmark\results\run_<timestamp>\log.json` — dados brutos (individuais + agregados por tarefa)

### 4.4 Comparar execuções

```powershell
.\.venv\Scripts\python.exe -m benchmark.compare_runs --before benchmark\results\run_AAA --after benchmark\results\run_BBB
```

---
## NÍVEL 5 — Teste E2E de UI

### 5.1 Modo desenvolvimento

```powershell
# Terminal 1 — backend
cd c:\Users\betti\IdeaProjects\Maria
.\.venv\Scripts\python.exe backend\main.py --bridge-http --porta 8081

# Terminal 2 — frontend Tauri
cd c:\Users\betti\IdeaProjects\Maria\frontend-tauri
npm run tauri dev
```

### 5.2 Roteiro manual obrigatório (checklist de aceite)

| # | Ação | Esperado |
|---|---|---|
| 1 | Abrir o app | Janela sem console, badge `MODO LOCAL` com bolinha verde |
| 2 | Card "RECURSOS DO SISTEMA" | CPU/RAM/GPU reais (não 0% fixo) e modelo `qwen2.5-omni-3b` |
| 3 | Topbar: minimizar | Janela some da barra |
| 4 | Topbar: maximizar/restaurar | Alterna entre fullscreen/normal |
| 5 | Topbar: fechar | App fecha; processo `maria-backend*` encerrado |
| 6 | Enviar mensagem no chat | Resposta real do LLM (não mockada) |
| 7 | `window.__TAURI__.core.invoke('ping')` no DevTools | Promise resolve `"pong"` |
| 8 | Persistência | `shared\maria.db` — tabela `mensagens` com a conversa |

Verificação SQL da persistência (item 8):

```powershell
sqlite3 c:\Users\betti\IdeaProjects\Maria\shared\maria.db "SELECT role, substr(conteudo,1,50) FROM mensagens ORDER BY id DESC LIMIT 5;"
```

### 5.3 Modo produção (instalador em máquina limpa)

1. Rodar `python build_sidecar.py` (Nível 0.3).
2. Rodar `npm run tauri build` (Nível 0.4).
3. Instalar o `.msi` (ou `.setup.exe`) em **máquina sem Python**.
4. Repetir o roteiro 5.2 (itens 1–8) no app instalado.

**Como confirmar que o sidecar foi usado:** no Gerenciador de Tarefas, o processo deve ser `maria-backend-x86_64-pc-windows-msvc.exe`, e o app deve funcionar na máquina que **não tem Python** instalado.

---

## Diagnóstico rápido

| Sintoma | Causa provável | Verificação/ação |
|---|---|---|
| `validate_llama_server` aborta no `[1]` | llama-server não subiu | `curl.exe localhost:8080/v1/models` |
| `curl /chat` (ping) → erro de conexão | Backend não está escutando / porta ocupada | `netstat -ano \| findstr 8081` |
| Monitor de recursos 0.0 fixo | `psutil` ausente, ou 1ª amostra de CPU | `pip show psutil`; chamar `status` 2× seguidas |
| Chat mockado no exe | Sidecar falhou ao subir | Logs do app (`[maria-backend][erro] ...` no stderr) |
| Sidecar `ModuleNotFoundError: backend` | Build PyInstaller antigo | Rebuild com `python build_sidecar.py` (versão atual usa `--paths` + `--collect-submodules`) |
| `cargo test` com `os error 4551` | WDAC/AppLocker bloqueando DLL de build | `cargo clean` e rodar de novo (recompila com outro hash) |
| Botões da topbar sem ação | Capacidade de janela ausente | `capabilities/default.json` deve ter `core:window:allow-*` |
| `UnicodeEncodeError` em script Python | Console cp1252 | `$env:PYTHONIOENCODING = "utf-8"` antes de rodar |

---

## Teste de fumaça completo (~15 min)

```powershell
# 1. Builds
python -m py_compile backend\main.py
cd frontend-tauri; npm run build            # TS + Vite

# 2. Testes automatizados
cd frontend-tauri\src-tauri; cargo test
cd frontend-tauri; npm run test
cd ..\..; .\.venv\Scripts\python.exe -m unittest discover -s backend\tests -v

# 3. Bridge HTTP
.\.venv\Scripts\python.exe backend\main.py --bridge-http --porta 8081
# (outro terminal) curl ping + status 2x

# 4. (Opcional, requer GPU/llama-server) validate_llama_server.py + benchmark
```