# Segurança — MARIA

**Versão:** v4.0.0
**Última atualização:** 2026-08-30

Este documento registra o modelo de segurança da aplicação, as correções aplicadas na auditoria de segurança (P0/P1/P2) e as pendências conhecidas.

---

## 1. Modelo de Ameaças (App Desktop Local)

O MARIA roda **100% localmente**: frontend Tauri (webview) + backend Python em `127.0.0.1:8081` + llama-server em `127.0.0.1:8080`. As superfícies de ataque relevantes são:

1. **Sites maliciosos no navegador** do usuário tentando acessar a API local (CSRF/CORS contra `127.0.0.1`)
2. **Comandos vindos do LLM** manipulando caminhos de arquivos (path traversal)
3. **Escopo shell do Tauri** permitindo execução de comandos arbitrários
4. **Dependências** (Python, npm, Rust) com CVEs conhecidas

---

## 2. Medidas Implementadas (Auditoria 2026-08-30)

### P0 — Críticas

| Correção | Onde | Detalhe |
|----------|------|---------|
| Deleção/leitura arbitrária de arquivos | `backend/main.py` (`transcrever_audio`) | Caminho validado com `resolver_caminho_permitido()` antes de processar e apagar; `WHISPER_BIN` validado por regex `^[\w.-]+(\.exe)?$` |
| Exfiltração via upload | `backend/main.py` (`upload_arquivo`) | Validação `is_file()`, limite de 100 MB, log de auditoria |
| Shell scope permissivo | `frontend-tauri/src-tauri/capabilities/default.json` | Scopes `python`/`python3` removidos; sidecar restrito a `"args": ["--bridge-http", "--porta", "8081"]` (antes: `"args": true`) |

### P1 — Altas

| Correção | Onde | Detalhe |
|----------|------|---------|
| API sem autenticação | `backend/main.py` + `src-tauri/src/main.rs` | Token de 32 bytes (`secrets.token_hex(32)`) gerado a cada inicialização do backend, persistido em `shared/.bridge_token` (fora do git). Header `Authorization: Bearer` obrigatório em `/chat` (`before_request` + `secrets.compare_digest`); `/ping` aberto como health check. O Rust lê o token e injeta o header automaticamente. |
| CORS permissivo | `backend/main.py` (`_criar_app_http`) | Restrito a `tauri://localhost`, `http://tauri.localhost`, `http://localhost:5173` |
| CSP nula | `frontend-tauri/src-tauri/tauri.conf.json` | Política restritiva: `default-src 'self'`; `connect-src` limitado à bridge (8081) + IPC Tauri; `ws://localhost:5173` para HMR em dev |
| Updater com chave placeholder | `frontend-tauri/src-tauri/tauri.conf.json` | Bloco `updater` removido (config órfã — plugin não instalado). Reativar somente com chave real (`npx tauri signer generate`) e endpoint de distribuição definido |

### Correções não necessárias (verificadas)

- **Path traversal em `ler_documento`/`listar_arquivos`**: já protegidos — `resolver_caminho_permitido()` faz `Path.resolve()` (resolve symlinks) + `is_relative_to(base)` antes do acesso.
- **SQL Injection**: todas as queries usam placeholders (`?` no Python, `params![]` no rusqlite). Nenhuma f-string em SQL.

---

## 3. Ferramentas Automatizadas (resultados de 2026-08-30)

| Ferramenta | Resultado |
|------------|-----------|
| **bandit** (`bandit -r backend/`) | 0 HIGH, 0 MEDIUM, 4 LOW (assert em `benchmark/`, try/except pass, B404/B603 do subprocess — mitigado pelas validações acima) |
| **cargo check** | Compila sem erros |
| **npm audit** | 5 vulnerabilidades em **devDependencies** (vite/vitest/esbuild): `npm audit fix` aplicado sem breaking changes; as restantes exigem `--force` (afetam apenas o ambiente de desenvolvimento) |
| **cargo-audit** | ⚠️ Pendente — instalar com `cargo install cargo-audit` e rodar em `frontend-tauri/src-tauri/` |

---

## 4. Como Testar Manualmente

Com o backend rodando (`python backend/main.py --bridge-http`):

```bash
# 1. Sem token -> 401
curl -X POST http://localhost:8081/chat -H "Content-Type: application/json" ^
  -d "{\"id\":\"1\",\"comando\":\"status\",\"dados\":{}}"

# 2. Com token (lido de shared/.bridge_token) -> 200
$token = Get-Content shared\.bridge_token
curl -X POST http://localhost:8081/chat ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer $token" ^
  -d "{\"id\":\"1\",\"comando\":\"ping\",\"dados\":{}}"

# 3. Path traversal -> erro "fora das pastas permitidas"
curl -X POST http://localhost:8081/chat ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer $token" ^
  -d "{\"id\":\"2\",\"comando\":\"resumir_documento\",\"dados\":{\"caminho\":\"../../etc/passwd\"}}"
```

Testes automatizados: `TestSegurancaComandosBridge` e `TestSegurancaApiHttp` em `backend/tests/test_maria.py` (9 testes).

---

## 5. Pendências / Roadmap de Segurança

| Prioridade | Pendência |
|------------|-----------|
| P2 | Rodar `cargo-audit` e registrar baseline |
| P2 | Sanitizar logs para não expor caminhos absolutos do usuário |
| P3 | Reproducible build + assinatura de código (Authenticode/codesign) na Fase de distribuição |
| P3 | Reavaliar `npm audit` com upgrades major do Vite/Vitest quando disponíveis |

---

**Referências:** [Tauri Security](https://v2.tauri.app/security/), [OWASP Desktop App Security](https://owasp.org/www-project-desktop-app-security-top-10/), [bandit](https://bandit.readthedocs.io/)
