# EXECUÇÃO — P4: navegação em breve + versões 4.2.5 + hardening · Suíte verde

**Data:** 2026-09-11
**Branch:** `feat/p4-nav-versoes-hardening` (de `develop` @ `eb7a995`)
**Escopo autorizado:** F4.2 (nav `emBreve`) + F4.3 (versões) + hardening (ErrorBoundary, `.env.example`, cartão de estado dinâmico N1).

---

## Diagnóstico que motivou a execução

1. **Nav mentia:** os 8 itens do `Sidebar` mudavam o realce ao clicar mas a navegação era inexistente (só "Conversar" é funcional) — o utilizador via o item "ativo" sem qualquer conteúdo novo.
2. **Versões inconsistentes:** `pyproject.toml` (fonte canónica, lida por `backend/config.py:_obter_versao()`) = `4.2.5`; `Cargo.toml`/`package.json`/`tauri.conf.json` = `4.0.0`; rodapé do `Sidebar` = `v0.1.0`.
3. **Cartão "FUNCIONANDO LOCALMENTE" mentia:** verde *hardcoded* mesmo com backend offline (TopBar dinâmico, Sidebar estático — N1).
4. **Sem boundary de erro:** exceção em render → tela branca.

## Execução

- **`Sidebar/index.tsx`:** `NavItem.emBreve?: boolean`; 7 itens marcados; `onClick` *short-circuit*; badge "em breve" + `title`; estado `online` via `getSystemStatus` (cartão dinâmico); rodapé `MARIA v4.2.5`.
- **Versões:** `tauri.conf.json`/`Cargo.toml`/`package.json` → `4.2.5`.
- **`ErrorBoundary.tsx` (novo):** boundary de erro global envolvendo o `App` (fallback com mensagem + recarregar).
- **`.env.example` (novo, raiz):** exemplo das variáveis do `backend/config.py`, sem segredos (token do bridge é ficheiro `frontend-tauri/shared/.bridge_token`).

## Resultados (gates)

| Gate | Resultado |
|---|---|
| G1 (`uv run pytest`) | ✅ 288 passed (inalterado) |
| G2 (`npm test`) | ✅ 6 passed (inalterado) |
| G3 (`npm run build`) | ✅ tsc+vite sem erros (exit 0) |
| G4 (`cargo test`) | ✅ 1 passed (exit 0) |
| G5 (`cargo clippy`) | ✅ exit 0 — 1 warning **pré-existente** (`use uuid;` em `main.rs:14`) |

## Fora de escopo (registado)

- DEF-12 (polling), DEF-25 (CI/CD), placeholder `18/42/11` (só flash no 1.º render — `getSystemStatus` devolve zeros no `catch`), override multimodal 600s.
- Warning clippy `use uuid;` (pré-existente, `main.rs:14`).
