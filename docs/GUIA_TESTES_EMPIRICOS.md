# Guia de Testes Empíricos — MARIA v4.1.1

**Versão:** v4.1.1  
**Última atualização:** 2026-08-31  
**Escopo:** Backend Python (Flask bridge HTTP + LlamaClient) + Frontend Tauri v2/React + Sidecar PyInstaller  

Este guia descreve, passo a passo, como **construir** e **executar** os testes do sistema MARIA, do build inicial ao teste de ponta a ponta em máquina limpa. Os comandos são para **PowerShell no Windows** (ambiente de referência do projeto).

---

## Visão Geral — 5 Níveis de Teste

| Nível | O que valida | Tempo | Requer modelo LLM? |
|---|---|---|---|
| **0.** Construção/ambientes | Compilação e ambiente pronto para testar | 2–5 min | ❌ |
| **1.** Testes automatizados | Lógica isolada de cada módulo (Python, Rust, TS) | ~30s | ❌ |
| **2.** Validação do llama-server ao vivo | LLM responde (texto, stream, TTFT, visão, áudio) | 1–2 min | ✅ (GPU/CPU) |
| **3.** Integração HTTP (bridge) | Backend ↔ frontend via `localhost:8081` autenticado | ~2 min | Parcial |
| **4.** Benchmark de tool calling | Avaliação quantitativa das tarefas de ferramentas | 5–30 min | ✅ |
| **5.** E2E de UI (dev e instalador) | App completo de ponta a ponta | 10–20 min | ✅ |

> **Modelo padrão em produção:** `qwen2.5-omni-3b` via llama-server (`backend/core/llama_client.py`), configurado em `backend/core/config.py` (`LLAMA_MODEL`, `LLAMA_BASE_URL=http://localhost:8080`).

---

## NÍVEL 0 — Construção e Ambientes

### 0.1 Backend Python

```powershell
# Na raiz do monorepo
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Teste rápido de sintaxe e importação do backend:

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\main.py
# Sem saída = OK (exit code 0)
```

### 0.2 Frontend Tauri (Node)

```powershell
cd frontend-tauri
npm install
cd ..
```

### 0.3 Sidecar do Backend (Gera o Executável Empacotado)

```powershell
cd frontend-tauri\src-tauri
$env:PYTHONIOENCODING = "utf-8"   # evita UnicodeEncodeError (cp1252) no Windows
python build_sidecar.py
cd ..\..
```

**Verificação:** `frontend-tauri\binaries\maria-backend-x86_64-pc-windows-msvc.exe` deve ter **~20 MB** (nunca 0 bytes).

### 0.4 Build Completo do Instalador

```powershell
cd frontend-tauri
npm run tauri build
cd ..
```

**Artefatos gerados em:** `frontend-tauri\src-tauri\target\release\bundle\`
- `msi\MARIA_*.msi`
- `nsis\MARIA_*-setup.exe`

---

## NÍVEL 1 — Testes Automatizados

### 1.1 Backend Python (pytest)

Cobre lógica determinística: `ChatSession`, `tools_schema`, `excel_handler`, `file_utils`, `session_storage`, `manual_redacao` (FTS5), `LlamaClient` (com mocks de rede) e métricas de benchmark.

```powershell
# Executar a suíte de testes unitários do backend
.\.venv\Scripts\python.exe -m pytest backend/tests/test_maria.py -v
```

**Resultado esperado:** `120 passed` no final, sem falhas.

### 1.2 Rust (Tauri)

```powershell
cd frontend-tauri\src-tauri
cargo test
cd ..\..
```

**Resultado esperado:** `test result: ok. 1 passed; 0 failed` (`test_garantir_conversa_e_insercao_de_mensagem`).

### 1.3 TypeScript (Vitest)

```powershell
cd frontend-tauri
npm run test
cd ..
```

**Resultado esperado:** `Test Files  1 passed (1)` e `Tests  1 passed (1)`.

---

## NÍVEL 2 — Validação do llama-server ao Vivo

> **Pré-requisito:** `llama-server` em execução na porta 8080 com o modelo `qwen2.5-omni-3b`.

### 2.1 Iniciar o Servidor

```powershell
.\llama.cpp\build\bin\Release\llama-server.exe `
  -m "$env:USERPROFILE\models\qwen2_5-omni-3b-q4_k_m.gguf" `
  -ngl 99 -c 8192 --flash-attn --host 127.0.0.1 --port 8080
```

### 2.2 Rodar o Smoke-Test do Cliente LLM

```powershell
.\.venv\Scripts\python.exe backend\tests\validate_llama_server.py
```

Executa sequencialmente:
1. `[1]` GET `/v1/models` (handshake de conexão)
2. `[2]` Chat texto simples
3. `[3]` Streaming (medição de tokens/s e TTFT real)
4. `[4]` Visão (opcional com `--image`)
5. `[5]` Áudio (opcional com `--audio`)

**Resultado esperado:** `=== Resultado: X/X testes passaram ===` com exit code 0.

---

## NÍVEL 3 — Integração HTTP (Bridge)

### 3.1 Iniciar o Backend

```powershell
.\.venv\Scripts\python.exe backend\main.py --bridge-http --porta 8081
```

O backend gera atomicamente o token de autenticação em `shared\.bridge_token`.

### 3.2 Testar os Endpoints Autenticados (em outro terminal)

```powershell
# 1. Carregar o token da sessão
$token = Get-Content shared\.bridge_token

# 2. Health check aberto (não requer token)
curl.exe http://localhost:8081/ping
# Esperado: {"status":"ok","dados":"pong"}

# 3. Ping autenticado via /chat
curl.exe -X POST http://localhost:8081/chat `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $token" `
  -d '{"id":"1","comando":"ping","dados":{}}'
# Esperado: {"dados":"pong","id":"1","mensagemErro":null,"status":"ok"}

# 4. Status do sistema (telemetria em tempo real)
curl.exe -X POST http://localhost:8081/chat `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $token" `
  -d '{"id":"2","comando":"status","dados":{}}'
# Esperado: {"status":"ok","dados":{"cpu":..,"ram":..,"gpu":..,"plataforma":"Windows","modelo":"qwen2.5-omni-3b"}}

# 5. Chat integrado (requer llama-server ativo)
curl.exe -X POST http://localhost:8081/chat `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $token" `
  -d '{"id":"3","comando":"chat","dados":{"mensagem":"Olá, quem é você?"}}'
```

---

## NÍVEL 4 — Benchmark de Tool Calling

> **Pré-requisito:** llama-server rodando na porta 8080 com `qwen2.5-omni-3b`.

```powershell
# Executar as 25 tarefas do benchmark
.\.venv\Scripts\python.exe -m backend.benchmark.run_benchmark --tasks 25

# Executar tarefas de uma categoria específica
.\.venv\Scripts\python.exe -m backend.benchmark.run_benchmark --category criar_planilha

# Comparar duas execuções
.\.venv\Scripts\python.exe -m backend.benchmark.compare_runs `
  --before backend\benchmark\results\run_AAA `
  --after backend\benchmark\results\run_BBB
```

**Resultados gerados em:** `backend\benchmark\results\run_<timestamp>\report.md` e `log.json`.

---

## NÍVEL 5 — Teste E2E de UI

### 5.1 Modo Desenvolvimento

```powershell
# Terminal 1 — Backend Python
.\.venv\Scripts\python.exe backend\main.py --bridge-http

# Terminal 2 — Frontend Tauri
cd frontend-tauri
npm run tauri dev
```

### 5.2 Roteiro de Aceite Manual

| # | Ação | Resultado Esperado |
|---|---|---|
| 1 | Abrir o app | Janela carregada com Glassmorphism, Aura rosa, badge `MODO LOCAL` verde |
| 2 | Recursos do Sistema | Telemetria dinâmica de CPU/RAM/GPU (não zerados fixos) e modelo exibido |
| 3 | Janela / Topbar | Minimizar, maximizar e restaurar funcionam sem bugs visuais |
| 4 | Chat e Ferramentas | Enviar mensagem solicitando documento oficial ou planilha com confirmação |
| 5 | Persistência SQLite | `shared\maria.db` registra a conversa na tabela `mensagens` |
| 6 | Fechamento | Fechar o app encerra os processos filhos associados |

Verificação da persistência no SQLite:

```powershell
sqlite3 shared\maria.db "SELECT role, substr(conteudo,1,50) FROM mensagens ORDER BY id DESC LIMIT 5;"
```

---

## Diagnóstico Rápido

| Sintoma | Causa Provável | Ação Recomendada |
|---|---|---|
| `/chat` retorna `401 Unauthorized` | Token ausente ou divergente | Ler `$token = Get-Content shared\.bridge_token` e enviar `-H "Authorization: Bearer $token"` |
| `validate_llama_server` aborta no `[1]` | llama-server desligado ou em porta incorreta | Iniciar `llama-server` na porta 8080 |
| CORS bloqueado no browser | `MARIA_ENV` em produção | Definir `MARIA_ENV=development` no `.env` para dev web |
| Monitor de recursos zerado | Primeira amostra de CPU do psutil | Fazer duas chamadas consecutivas ao comando `status` |
| `ModuleNotFoundError: backend` no Sidecar | Build PyInstaller desatualizado | Rebuild com `python src-tauri\build_sidecar.py` |
| `cargo test` com `os error 4551` | Bloqueio de DLL no Windows Defender/WDAC | Executar `cargo clean` e rodar novamente |

---

## Teste de Fumaça Rápido (~5 min)

```powershell
# 1. Compilação estática
.\.venv\Scripts\python.exe -m py_compile backend\main.py
cd frontend-tauri; npm run build; cd ..

# 2. Testes automatizados unitários
cd frontend-tauri\src-tauri; cargo test; cd ..\..
cd frontend-tauri; npm run test; cd ..
.\.venv\Scripts\python.exe -m pytest backend/tests/test_maria.py -q

# 3. Teste rápido de bridge HTTP
.\.venv\Scripts\python.exe backend\main.py --bridge-http
# Em outro terminal: curl.exe http://localhost:8081/ping
```