# EXECUÇÃO — P1-restante: timeout 300s + estado vazio · Suíte verde

**Data:** 2026-09-11
**Branch:** `feat/p1-empty-state-timeout-300s` (de `develop` @ `eb7a995`)
**Escopo autorizado:** (a) alinhar `LLAMA_TIMEOUT` (Python) a 300s; (b) estado vazio com sugestões no `ChatPanel`. Baseline = `develop` pós-merge da P1 (sem `ResultadoArquivo`/`useChatStore`/`plugin-dialog` — código do P2 afastado).

---

## Diagnóstico que motivou a execução

1. **Timeout desalinhado:** `backend/config.py` mantinha `LLAMA_TIMEOUT=240` enquanto o bridge Rust (`main.rs`) usa `Duration::from_secs(300)`. O backend desistia aos ~240s → o `catch` no `ChatPanel` disparava com `tempoDecorrido ≈ 240 < 290` → mensagem de timeout ("demorou demasiado") **nunca** era mostrada; o utilizador via sempre "Não consegui me conectar" (falso).
2. **Estado vazio:** o chat abria com uma única saudação, sem affordance para começar.

## Execução

- **`backend/config.py`:** `LLAMA_TIMEOUT = int(os.getenv("LLAMA_TIMEOUT", "300"))` (+ comentário de alinhamento ao Rust).
- **`backend/tests/test_config.py` (novo):** `test_llama_timeout_padrao_300_segundos`.
- **`frontend-tauri/src/components/ChatPanel/index.tsx`:** constante `SUGESTOES` (3 itens) + bloco `messages.length <= 1 && !loading` que renderiza botões de sugestão a chamar `handleSendMessage`.

## Resultados (gates)

| Gate | Resultado |
|---|---|
| G1 (`uv run pytest`) | ✅ 289 passed (288 → 289, +1 novo) |
| G2 (`npm test`) | ✅ 6 passed (inalterado) |
| G3 (`npm run build`) | ✅ tsc+vite sem erros (exit 0) |
| G4 (`cargo test`) | ✅ 1 passed (exit 0) |
| G5 (`cargo clippy`) | ✅ exit 0 — 1 warning **pré-existente** (`use uuid;` redundante em `main.rs:14`) |

## Fora de escopo (registado)

- Override multimodal (600s) — mantido.
- DEF-13 debounce — invalidado (guard `if (loading) return` + `disabled={loading || !message.trim()}`).
- Margem Rust 310s — não aplicada (300s em ambas as camadas).
- Warning clippy `use uuid;` (pré-existente, `main.rs:14`).
