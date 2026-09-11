# PROMPTS DE EXECUÇÃO — Demo MARIA (P0-resíduo · P1-restante · P4)

**Data:** 2026-09-10
**Versão alvo:** 4.2.5 (fonte canónica `pyproject.toml:3`, lida por `backend/config.py:_obter_versao()`)
**Baseline verificado:** 288 backend · 6 frontend · 1 cargo · build Vite ok
**Branches:** `fix/p0-badge-modelo-sidebar` · `feat/p1-empty-state-timeout-300s` · `feat/p4-nav-versoes-hardening` (todas a partir de `develop`)

> **Precedência (guia §0):** `CHANGELOG.md` → `docs/ARQUITETURA_SISTEMA.md` → `plano_mestre_v5.md` → `GUIA_DESENVOLVIMENTO.md`.
> **Regra de referência:** indicações a código são **por conteúdo**, nunca por número de linha — a P1 e a P2 deslocam linhas do `ChatPanel` (ex.: o limiar `>= 290` está em `:117` no commit `373bea7` e em `:126` com a P2 aplicada).

---

## 0. Estado do repositório no início

| Ref | Commit | Estado |
|---|---|---|
| `develop` | `8697551` | P0 integrada (PR #34) |
| `fix/p1-paridade-chat` | `373bea7` | P1 concluída e verde (288+6), **não integrada** |
| `main` (local / origin) | `e75a65c` / `6163954` | ⚠️ origin recebeu P0 (PR #33) **sem bump**; local 56 atrás |

### Decisões travadas

- **D1** — P2 afastado por WIP commit em `feat/p2-momento-magico` (`ca3efc5`); retoma após P4.
- **D2** — integrar P1 em `develop` (`--no-ff`) antes de ramificar.
- **D3** — manifests do frontend → `4.2.5` (divergência com `4.2.5-dev` do cabeçalho do `CHANGELOG` registada como convenção documental).
- **D4** — `config.py` `LLAMA_TIMEOUT` 240→300; Rust mantém 300; limiar da UI `>= 290`.
- **N1** (incluído no P4) — cartão "FUNCIONANDO LOCALMENTE" do Sidebar passa a refletir o estado real (hoje é verde *hardcoded* e mente quando offline).

---

## 1. Prompt P0-resíduo — indicador de modelo 7B

**Branch:** `fix/p0-badge-modelo-sidebar` (de `develop`)
**Objetivo:** corrigir o resíduo vivo do P0 — o badge do modelo no Sidebar compara `includes('7B') || includes('8B')` contra o nome canónico **minúsculo** (`qwen2.5-omni-7b`), logo fica sempre rosa; `8B` é legado morto.

### Escopo (1 ficheiro + 1 teste novo)

- `frontend-tauri/src/components/Sidebar/index.tsx`
  - Localizar por conteúdo: `modeloAtivo.includes('7B') || modeloAtivo.includes('8B')` (2 ocorrências: `backgroundColor` e `boxShadow`).
  - Extrair helper exportável que espelha a convenção do backend (`backend/config.py` — `if "7b" in LLAMA_MODEL.lower()`):
    ```ts
    export function indicaModeloPesado(modelo: string): boolean {
      return modelo.toLowerCase().includes('7b');
    }
    ```
  - Remover o ramo `'8B'` (legado — `git grep "8B"` confirma zero usos fora destas linhas).
- `frontend-tauri/src/components/Sidebar/index.test.tsx` (novo; convenção colocalizada `<modulo>.test.tsx`):
  - `qwen2.5-omni-7b` → `true` (azul); `qwen2.5-omni-3b` → `false` (rosa); `LLAMA-7B` (maiúsculas) → `true`.

### Gates (binários)

| Gate | Comando | Esperado |
|---|---|---|
| G1 | `cd frontend-tauri; npm test` | 6 → **9** |
| G2 | `cd frontend-tauri; npm run build` | sucesso (tsc+vite) |
| G3 | `uv run pytest` | **288** (inalterado) |
| G4 | `cd frontend-tauri/src-tauri; cargo test` | 1 passed |

**Commit:** `fix(p0): corrige indicador de modelo no Sidebar (comparacao case-insensitive)`

---

## 2. Prompt P1-restante — timeout 300s + estado vazio

**Branch:** `feat/p1-empty-state-timeout-300s` (de `develop`, **após** o merge da P1)
**Objetivo:** fechar os dois pontos que a P1 deixou em aberto — (a) alinhar o timeout no backend Python e (b) estado vazio com sugestões no chat.

### ⚠️ Baseline declarada (obrigatório)

`develop` **pós-merge da P1**. Nesta baseline **não existem**: `ResultadoArquivo`, `stores/useChatStore`, `executarAnalise`, `@tauri-apps/plugin-dialog`, `Message.anexo`, `AnexoResultado`. **Não** usar o store zustand (é P2): o empty-state usa prop/callback local.

### (a) Timeout Python

- `backend/config.py` — localizar `LLAMA_TIMEOUT = int(os.getenv("LLAMA_TIMEOUT", "240"))` → trocar `"240"` por `"300"`.
- **Racional:** com 240s, o backend devolve **erro** aos ~240s → `tempoDecorrido(≈240) >= 290` é **falso** → a UI mostra sempre "Não consegui me conectar" (falso). Com 300s, a falha chega aos ~300s → mensagem correta.
- Teste novo em `backend/tests/test_config.py` (criar se não existir): `LLAMA_TIMEOUT` default = 300.

### (b) Estado vazio com sugestões

- `frontend-tauri/src/components/ChatPanel/index.tsx`
  - Localizar por conteúdo o limiar `tempoDecorridoRef.current >= 290` (não alterar o valor).
  - Renderizar, quando `messages.length <= 1 && !loading`, uma grelha de sugestões (ex.: "Criar uma planilha", "Analisar um arquivo", "Resumir um documento") que chamam `handleSendMessage(sugestao)`.
  - Sugestões como constantes locais (não store).
- `frontend-tauri/src/components/ChatPanel/ChatInput.tsx` — só se necessário; **não** introduzir store.

### Gates

| Gate | Comando | Esperado |
|---|---|---|
| G1 | `uv run pytest` | ≥ 288 |
| G2 | `cd frontend-tauri; npm test` | ≥ 6 |
| G3 | `cd frontend-tauri; npm run build` | sucesso |
| G4 | `cd frontend-tauri/src-tauri; cargo test` | 1 passed |
| G5 | `cd frontend-tauri/src-tauri; cargo clippy` | sem warnings (§8.3) |

### Fora de escopo (registado)

Override multimodal (600s) · DEF-13 debounce (**invalidado** — `ChatPanel` `if (loading) return` + `ChatInput` `disabled={loading || !message.trim()}`) · margem Rust 310s (por omissão **não** aplicada).

**Commit:** `feat(p1): timeout 300s no backend e estado vazio com sugestoes no chat`

---

## 3. Prompt P4 — navegação + versões + hardening

**Branch:** `feat/p4-nav-versoes-hardening` (de `develop`)
**Objetivo:** F4.2 (nav `emBreve`) + F4.3 (versões) + hardening (ErrorBoundary + `.env.example` + cartão de estado dinâmico).

### Escopo

1. **Versões → `4.2.5`** (sem bump de produto; alinhamento com `pyproject.toml`):
   - `frontend-tauri/src-tauri/tauri.conf.json` (`"version": "4.0.0"` → `"4.2.5"`)
   - `frontend-tauri/src-tauri/Cargo.toml` (`version = "4.0.0"` → `"4.2.5"`)
   - `frontend-tauri/package.json` (`"version": "4.0.0"` → `"4.2.5"`)
   - `frontend-tauri/src/components/Sidebar/index.tsx` (`MARIA v0.1.0` → `MARIA v4.2.5`)
   - Registar a divergência `4.2.5` vs `4.2.5-dev` (cabeçalho do `CHANGELOG`) na documentação.
2. **Nav `emBreve` (F4.2)** — `frontend-tauri/src/components/Sidebar/index.tsx`:
   - Interface **local** `NavItem` (linhas ~17-22): adicionar `emBreve?: boolean`.
   - Itens não implementados (`arquivos`, `analise`, `visao`, `voz`, `memoria`, `automacoes`, `config`) → `emBreve: true`.
   - `onClick`: *short-circuit* para não alterar `activeItem` quando `emBreve` (seleção permanece em `conversar`); renderizar badge "em breve".
   - Apenas `conversar` é funcional.
3. **Cartão de estado dinâmico (N1)** — `frontend-tauri/src/components/Sidebar/index.tsx`:
   - O cartão "FUNCIONANDO LOCALMENTE" (verde, *hardcoded*) passa a refletir o estado real do backend: offline → "OFFLINE" + ponto vermelho, em vez de mentir.
4. **ErrorBoundary** — `frontend-tauri/src/components/ErrorBoundary.tsx` (novo) e envolver o `App.tsx` dentro do `ThemeProvider`.
5. **`.env.example`** — na **raiz** (whitelist `.gitignore:131` `!.env.example`), com as chaves de `backend/config.py` **sem segredos** (o token do bridge é ficheiro `frontend-tauri/shared/.bridge_token`, não variável de ambiente). Lista mínima: `LLAMA_BASE_URL`, `LLAMA_MODEL`, `LLAMA_TIMEOUT`, `LLAMA_NUM_CTX`, `LLAMA_NUM_PREDICT`, `MARIA_ENV` (+ nota de que existem ~30 parâmetros de sampler adicionais em `config.py`).

### Gates

| Gate | Comando | Esperado |
|---|---|---|
| G1 | `uv run pytest` | 288 |
| G2 | `cd frontend-tauri; npm test` | ≥ 6 |
| G3 | `cd frontend-tauri; npm run build` | sucesso |
| G4 | `cd frontend-tauri/src-tauri; cargo test` | 1 passed |
| G5 | `cd frontend-tauri/src-tauri; cargo clippy` | sem warnings |

### Fora de escopo (registado)

DEF-12 (polling) · DEF-25 (CI/CD) · placeholder `18/42/11` (só *flash* no 1.º render — `getSystemStatus` devolve zeros no `catch`, não persiste) · override multimodal 600s.

**Commit:** `feat(frontend): navegacao emBreve, alinhamento de versoes 4.2.5 e ErrorBoundary`

---

## 4. Ordem de execução e gates globais

1. `git checkout develop` + merge `--no-ff` da P1 + push (confirmação).
2. P0-resíduo → gates → `CHANGELOG` + `PROGRESSO` → commit → push (confirmação).
3. P1-restante → gates → docs → commit → push (confirmação).
4. P4 → gates → docs → commit → push (confirmação).
5. Merge `--no-ff` de cada branch → `develop`, na ordem P0-resíduo → P1-restante → P4; push.
6. Limpeza após `git merge-base --is-ancestor <branch> develop` (exit 0).
7. Retoma P2: `git checkout feat/p2-momento-magico` → `git rebase develop` (conflito esperado em `package.json`/`Cargo.toml` → resolver a favor de `4.2.5`).

## 5. Regras observadas

- Sem `&&` no PowerShell (`;` ou comandos separados).
- Docs (`CHANGELOG` + `PROGRESSO`) **antes** do commit.
- Conventional Commits em PT; tipos `fix`/`feat`.
- Branch sempre a partir de `develop`.
- `main` intocado (sem bump de versão).
