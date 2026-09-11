# EXECUÇÃO — P0-resíduo: indicador de modelo 7B no Sidebar · Suíte verde

**Data:** 2026-09-11
**Branch:** `fix/p0-badge-modelo-sidebar` (de `develop` @ `eb7a995`)
**Escopo autorizado:** correção do resíduo do P0 — badge de modelo 7B no `Sidebar` (comparação case-insensitive + remoção do legado `8B`) + 1 ficheiro de teste novo.

---

## Diagnóstico que motivou a execução

- O badge do modelo (`frontend-tauri/src/components/Sidebar/index.tsx`) comparava `modeloAtivo.includes('7B') || modeloAtivo.includes('8B')` contra o nome canónico **minúsculo** (`qwen2.5-omni-7b`, `types/index.ts:52`). A condição era sempre falsa → indicador sempre rosa (deveria ser azul para o modelo pesado).
- `8B` é legado morto: `git grep "8B"` → 2 ocorrências, ambas neste bloco (zero usos reais).
- Convenção de comparação do backend é **case-insensitive**: `backend/config.py` usa `if "7b" in LLAMA_MODEL.lower()`.

## Execução

- **`frontend-tauri/src/components/Sidebar/index.tsx`:** extraído helper exportável `indicaModeloPesado(modelo: string): boolean` (`modelo.toLowerCase().includes('7b')`), espelhando `config.py`; o badge passa a usar `indicaModeloPesado(modeloAtivo)`; removido o ramo `'8B'`.
- **`frontend-tauri/src/components/Sidebar/index.test.tsx` (novo):** 3 testes (canónico 7B → true; 3B → false; maiúsculas → true).

## Resultados (gates)

| Gate | Resultado |
|---|---|
| G1 (`npm test`) | ✅ 9 passed (6 → 9, +3 novos) |
| G2 (`npm run build`) | ✅ tsc+vite sem erros |
| G3 (`uv run pytest`) | ✅ 288 passed (inalterado) |
| G4 (`cargo test`) | ✅ 1 passed (exit 0) |

- **Suíte frontend:** 6 → **9** (100% verde).
- **Suíte backend:** 288 (inalterada, 0 falhas).

## Fora de escopo (registado)

- Cartão "FUNCIONANDO LOCALMENTE" hardcoded no `Sidebar` (N1) — endereçado no P4.
- Alinhamento de versões `4.0.0` → `4.2.5` nos manifests — P4.
- Divergência `4.2.5` (pyproject) vs `4.2.5-dev` (cabeçalho do CHANGELOG) — registada na documentação.
