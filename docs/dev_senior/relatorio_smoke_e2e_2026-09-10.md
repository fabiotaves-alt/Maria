# Relatório — Smoke Tests E2E (funcional + multimodal)

**Data:** 2026-09-10
**Branch:** `feat/smoke-e2e-multimodal` (a partir de `develop`)
**Modelo:** Qwen2.5-Omni-3B (Q4_K_M) via llama-server local
**Servidor:** `http://localhost:8080` · `n_ctx=4096`

---

## 1. Resumo executivo

Os dois harnesses de smoke ao vivo foram executados contra o llama-server real e **todos os itens passaram**:

| Suite | Resultado | Detalhe |
|---|---|---|
| **Funcional** (`smoke_e2e_chat.py`) | **7/7 passaram** | fluxo completo de chat + tool calling + escrita |
| **Multimodal** (`smoke_multimodal.py`) | **1/1 passou** | visão descreveu corretamente o logotipo MARIA |

A execução validou end-to-end o pipeline do MARIA: **tool calling → parser → validador V3 → confirmação → escrita real → cancelamento**, além do processamento de imagem (multimodal).

---

## 2. Resultados funcionais (7/7)

| # | Item | Resultado | Observação |
|---|---|---|---|
| 1 | Modelo acessível | ✅ OK | `ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M` |
| 2 | `criar_planilha` real | ✅ OK | `gastos_smoke_20260910_153418.xlsx` criado em `arquivos_gerados/` |
| 3 | Validador V3 (case-insensitive) | ✅ OK | chaves normalizadas `['Data', 'Valor']` |
| 3b | Conteúdo do `.xlsx` | ✅ OK | `{'Data': '2026-01-01', 'Valor': 100}` — sem NaN, fidelidade perfeita |
| 4 | Fluxo de confirmação | ✅ OK | "Entendi! Vou criar uma planilha chamada … Posso seguir?" |
| 5 | Cancelamento | ✅ OK | "Ação cancelada." — nenhum arquivo novo criado |
| 6 | Tool call detectada | ✅ OK | `name='criar_planilha'` |

> **Nota sobre o item 6:** o critério original do harness exigia `_fonte` (`json`/`delta`) na tool call final. Constatou-se que `_fonte` é **metadado interno do parser** (`llama_client`), consumido antes da validação; o `finalizar_mensagem()` devolve a tool call limpa (`{name, arguments}`) vinda de `validar_e_corrigir_tool_call_stream`. O critério foi corrigido para **`name` + `arguments` válidos**, com `_fonte` reportado como informativo — não é contrato público.

---

## 3. Resultado multimodal (1/1)

| Item | Resultado | Observação |
|---|---|---|
| Visão (`--image backend/maria_opening.png`) | ✅ OK | "A imagem apresenta um logotipo de uma assistente de IA chamada 'MARIA'. O logotipo é feito de pontos e linhas…" |

- **Áudio:** não testado (sem fixture `.wav` no repositório).

---

## 4. Aprendizados (importante para a operação)

1. **`n_ctx=2048` era insuficiente para multimodal.** Com o system prompt + imagem, o payload chegou a **2.080 tokens** > 2.048, resultando em `exceed_context_size_error`. **`n_ctx=4096` resolve** (folga de ~50%).
2. **Timeout de 240s (default `LLAMA_TIMEOUT`) era curto** para o 3B CPU processar imagem (mmproj + geração a ~1–3,6 tok/s). **600s** resolve — o harness multimodal aceita `--timeout` configurável.
3. **O fluxo funcional do MARIA está estável e fiel**: criação de planilha com dados corretos (`2026-01-01` preservado como string, `100` como número), normalização case-insensitive das chaves (`valor` → `Valor`) e cancelamento sem efeitos colaterais.
4. **Separação por suites** foi acertada: o funcional roda em ~5 min (gate rápido do dia a dia); o multimodal é lento (CPU) e isolado, com skip automático se o contexto for insuficiente.

---

## 5. Harnesses versionados

| Arquivo | Conteúdo | Uso |
|---|---|---|
| `docs/dev_base/smoke_e2e_chat.py` | 6 itens funcionais do B0.9 | `uv run python docs/dev_base/smoke_e2e_chat.py` |
| `docs/dev_base/smoke_multimodal.py` | visão/áudio com `--timeout` e skip por `n_ctx` | `uv run python docs/dev_base/smoke_multimodal.py --image … --timeout 600` |

Ambos requerem `PYTHONUTF8=1` (o terminal Windows usa cp1252 e os símbolos `✓`/`✗` do script não são codificáveis em cp1252).

---

## 6. Itens fora de escopo / pendências

- **Frente B (system_prompt v4):** adiada — com `n_ctx=4096` sobrou margem de contexto; a reescrita do prompt (~700 tokens) deixa de ser obrigatória e fica como otimização futura.
- **Áudio:** não testado (sem fixture `.wav`).
- **7B:** não testado (RAM insuficiente nesta máquina — ver `REGRAS_OPERACAO_LLAMA_SERVER.md`).

---

*Fim do relatório.*
