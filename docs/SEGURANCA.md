# Segurança — MARIA

**Versão:** v4.1.1
**Última atualização:** 2026-08-31
**Status:** ✅ Auditado e Mitigado

Este documento registra o modelo de segurança da aplicação, as medidas de proteção ativas contra ameaças locais, as correções aplicadas na auditoria (v4.0 e v4.1.1) e o roadmap de segurança.

---

## 1. Modelo de Ameaças (App Desktop Local)

O MARIA roda **100% localmente**: frontend Tauri (webview nativa) + backend Python em `127.0.0.1:8081` (modo `--bridge-http`) + llama-server em `127.0.0.1:8080`. As principais superfícies de ataque em ambiente desktop local são:

1. **Acesso não autorizado via navegador**: páginas web maliciosas visitadas pelo usuário tentando invocar a API local via CSRF/CORS contra `127.0.0.1`.
2. **Manipulação de arquivos (*Path Traversal*)**: comandos do modelo de linguagem tentando ler, escrever ou apagar arquivos fora das pastas gerenciadas.
3. **Substituição maliciosa de binários (*PATH Hijacking*)**: execução de executáveis maliciosos posicionados no PATH do sistema.
4. **Condições de corrida e concorrência**: corrupção de estado por acessos simultâneos de threads HTTP ao SQLite ou ao arquivo de token.
5. **Escopo permissivo de shell no Tauri**: execução inadvertida de comandos arbitrários no sistema operacional.
6. **Vulnerabilidades de dependências**: CVEs em bibliotecas Python, crates Rust ou pacotes npm.

---

## 2. Medidas de Segurança Implementadas

### P0 — Bloqueadores Críticos e Integridade de Arquivos

| Medida | Onde | Implementação Técnica |
|--------|------|------------------------|
| **Isolamento de caminhos de áudio** | `backend/main.py` (`transcrever_audio`) | O arquivo de áudio deve estar dentro das pastas permitidas, validado via `resolver_caminho_permitido()` antes de ser processado ou deletado. |
| **Mitigação de PATH hijacking** | `backend/main.py` (`transcrever_audio`) | O nome do binário é validado via regex `^[\w.-]+(\.exe)?$`. O caminho resolvido via `shutil.which()` deve pertencer obrigatoriamente a `WHISPER_ALLOWED_DIR` (padrão: `<raiz_monorepo>/bin`), rejeitando binários em diretórios genéricos do PATH. O `returncode` e `stderr` são registrados em log em caso de falha. |
| **Proteção contra exfiltração no upload** | `backend/main.py` (`upload_arquivo`) | Validação estrita de arquivo existente (`is_file()`), limite máximo de 100 MB, sanitização de nome com incremento numérico anti-colisão e log de auditoria. |
| **Shell capabilities restritas** | `frontend-tauri/src-tauri/capabilities/default.json` | Scopes genéricos `python`/`python3` removidos. Execução limitada ao sidecar `maria-backend` com argumentos fixos (`["--bridge-http", "--porta", "8081"]`). |

### P1 — Autenticação, CORS e Concorrência

| Medida | Onde | Implementação Técnica |
|--------|------|------------------------|
| **Autenticação por token atômico** | `backend/main.py` + `src-tauri/src/main.rs` | Token criptográfico de 32 bytes (`secrets.token_hex(32)`) gerado a cada inicialização do backend e salvo atomicamente via `.tmp` + `os.replace()` em `shared/.bridge_token` (permissão `0o600` em POSIX). Header `Authorization: Bearer <token>` obrigatório para todas as rotas exceto `/ping`. O Rust relê o arquivo a cada requisição e injeta o header. Falha de I/O (`OSError`) interrompe o startup. |
| **CORS restrito por ambiente** | `backend/core/config.py` + `backend/main.py` | Controlado por `MARIA_ENV` (padrão: `"production"`). Em produção, aceita apenas origens do webview (`tauri://localhost`, `http://tauri.localhost`). `http://localhost:5173` (Vite dev server) é liberado **apenas** quando `MARIA_ENV=development`. |
| **Thread-Safety da Conexão SQLite** | `backend/database/connection.py` | Conexão com `check_same_thread=False` protegida por `threading.Lock()` (*double-checked locking*), impedindo `ProgrammingError` em threads simultâneas do Flask. `PRAGMA busy_timeout = 5000` evita bloqueios imediatos sob concorrência. |
| **CSP Restritiva** | `frontend-tauri/src-tauri/tauri.conf.json` | `default-src 'self'`; `connect-src` limitado à bridge (`http://127.0.0.1:8081`) e ao IPC nativo do Tauri. |
| **Proteção contra Path Traversal em leitura** | `backend/core/file_utils.py` | `resolver_caminho_permitido()` executa `Path.resolve()` (resolvendo symlinks) e valida `is_relative_to(base)`. Extensões restritas a `EXTENSOES_LEITURA` com limites de tamanho e caracteres. |
| **Prevenção de SQL Injection** | `backend/database/` + `src-tauri/src/main.rs` | Todas as queries utilizam *parameter binding* com placeholders (`?` no Python e macro `params![]` no rusqlite). Zero interpolação de strings em consultas. |

---

## 3. Ferramentas Automatizadas e Auditorias

| Ferramenta | Escopo | Resultado |
|------------|--------|-----------|
| **bandit** (`bandit -r backend/`) | Backend Python | 0 HIGH, 0 MEDIUM. As ocorrências LOW são limitadas a `assert` em testes/benchmark e `subprocess` devidamente mitigado por validações de caminho e binário. |
| **cargo check** | Frontend Rust | Compilação limpa sem erros ou warnings de segurança. |
| **npm audit** | Frontend React | Dependências de produção limpas. Vulnerabilidades residuais limitadas a ferramentas de build (`devDependencies`: esbuild/vite) que não são distribuídas no pacote final. |
| **cargo-audit** | Dependências Rust | Em acompanhamento periódico no roadmap P2. |

---

## 4. Como Testar e Validar Manualmente

Com o backend rodando em modo bridge HTTP (`python backend/main.py --bridge-http`):

### 1. Requisição sem token (deve retornar 401 Unauthorized)
```bash
curl -X POST http://127.0.0.1:8081/chat \
  -H "Content-Type: application/json" \
  -d '{"id":"1","comando":"status","dados":{}}'
```
*Resposta esperada:* `{"dados":null,"id":"","mensagemErro":"Não autorizado: token inválido ou ausente.","status":"erro"}` (HTTP 401).

### 2. Requisição autenticada com token válido (deve retornar 200 OK)
```powershell
$token = Get-Content shared\.bridge_token
curl -X POST http://127.0.0.1:8081/chat `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $token" `
  -d '{"id":"1","comando":"ping","dados":{}}'
```
*Resposta esperada:* `{"dados":"pong","id":"1","mensagemErro":null,"status":"ok"}` (HTTP 200).

### 3. Tentativa de Path Traversal (deve ser bloqueada)
```powershell
$token = Get-Content shared\.bridge_token
curl -X POST http://127.0.0.1:8081/chat `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $token" `
  -d '{"id":"2","comando":"resumir_documento","dados":{"caminho":"../../etc/passwd"}}'
```
*Resposta esperada:* Erro informando que o caminho está fora das pastas permitidas.

### 4. Validação de CORS em Produção
```powershell
# Com MARIA_ENV=production (padrão), a origem localhost:5173 é rejeitada no preflight
curl -I -X OPTIONS http://127.0.0.1:8081/chat `
  -H "Origin: http://localhost:5173" `
  -H "Access-Control-Request-Method: POST"
```
*Resposta esperada:* Ausência do header `Access-Control-Allow-Origin: http://localhost:5173`.

---

## 5. Pendências e Roadmap de Segurança

| Prioridade | Ação | Status |
|------------|------|--------|
| **P2** | Executar `cargo-audit` periodicamente e registrar baseline de crates Rust | 📋 Planejado |
| **P2** | Sanitizar mensagens de log para evitar exposição de caminhos absolutos de usuários | 📋 Planejado |
| **P3** | Assinatura de código digital (Authenticode no Windows e Codesign no macOS) para o instalador de produção | 📋 Planejado (Fase de Distribuição) |
| **P3** | Atualização contínua de dependências de desenvolvimento do ecossistema Vite/Node | 🔄 Contínuo |

---

**Referências de Conformidade:**
- [Tauri v2 Security Guidelines](https://v2.tauri.app/security/)
- [OWASP Desktop App Security Top 10](https://owasp.org/www-project-desktop-app-security-top-10/)
- [Bandit Security Linter for Python](https://bandit.readthedocs.io/)

