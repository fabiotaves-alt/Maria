# EXECUÇÃO — (a) B0.6 + (b) B1 (re-exports) · Suíte verde

**Data:** 2026-09-08
**Branch:** `feat/arquitetura-hexagonal-fase4`
**Escopo autorizado:** (a) B0.6 (deletar parser posicional — remover testes legados) + (b) B1 (restaurar re-exports/contratos dos módulos movidos). Na ordem, cada um com gate.

---

## Diagnóstico que motivou a execução

1. **Ambiente**: `flask` ausente no Python global (3.14), presente no `.venv`. → todos os pytest devem usar `& .venv\Scripts\python.exe -m pytest`.
2. **B0.6**: `tool_call_textual_parser.py` já deletado, mas `test_maria.py` ainda tinha 3 blocos de testes legados que o importavam → `ModuleNotFoundError`.
3. **B1 (causa-raiz da maioria das falhas)**: a migração hexagonal **não foi um "move puro"** — os módulos novos foram reescritos/encurtados e perderam comportamento testado pelo HEAD:
   - `application/tool_chaining.py` perdeu `FERRAMENTAS_ESCRITA`, a auto-sanitização de path traversal, e mudou o contrato de `validar_e_corrigir_tool_call_stream` (formato `{"valida","erro"}` em vez de `{"tool_call","tentativas","correcoes"}`). Quebrou **dezenas** de testes em cascata (via `maria_runner.py:30`).
   - `infrastructure/tools/tools_schema.py` e `excel_handler.py` encurtados com perdas de contrato.
4. **2 testes** usavam `mock.patch`/`patch.object` com caminho antigo (`backend.core.*`), que deixou de interceptar após os re-exports.

---

## Execução

### (a) B0.6 — remoção de testes legados
- `backend/tests/test_maria.py`: removidas as classes `TestMapeamentoNomeFerramenta`, `TestToolCallTextualParser` e o método `test_extrair_dados_planilha_no_positional_map` (154 linhas).
- Preservados os testes de vocabulário de telemetria (`TestFormatarAvisos` com `tool_call_fonte="parser_posicional"` / `fallbacks=["lista_reparada", ...]`) — pertencem ao B0.7 (posterior).
- **Gate A1**: `git grep "tool_call_textual_parser|extrair_tool_call_textual|POSITIONAL_MAP|NOME_CANONICO"` → **zero**.
- **Gate A2**: falhas B0.6 zeradas (109 → 85, com `.venv`).

### (b) B1 — restauração de contratos (move puro)
- **`application/tool_chaining.py`** ← restaurado do HEAD, com imports ajustados (`backend.infrastructure.tools.tools_schema`, `backend.interfaces.client_protocol`). Recuperou `FERRAMENTAS_ESCRITA` e o contrato original de `validar_e_corrigir_tool_call_stream`.
- **`infrastructure/tools/tools_schema.py`** ← restaurado do HEAD (imports lazy ajustados para `backend.infrastructure.tools.*` e `backend.application.manual_redacao`). `CAMPOS_OBRIGATORIOS` idêntico (whitelist do parser preservada).
- **`infrastructure/tools/excel_handler.py`** ← restaurado do HEAD (import `file_utils` ajustado). **B0.4 (remover `df.reindex`) NÃO aplicado** — pertence à Etapa 3, fora deste escopo.
- **`core/tools_schema.py`** (re-export): exposto `_sanitizar_nome_seguro` (privado consumido pelos testes).
- **Testes atualizados** (patch/paths antigos → novos):
  - `test_interfaces_injection.py`: `mock.patch("backend.application.maria_controller.salvar_sessao")`; `from backend.application import tool_chaining`.
  - `test_maria.py`: `patch("backend.infrastructure.tools.excel_handler.get_max_linhas_*")` (2 lugares); `assertLogs("backend.infrastructure.tools.excel_handler")`.
- **Conferência de símbolos** (HEAD vs novo) dos demais módulos movidos (`maria_controller`, `router`, `manual_redacao`, `word_handler`, `file_utils`, `chat_session`, `confirmacao`, `client_protocol`, `interfaces`, `session_storage`, `paths`): **todos "ok"** — nenhum símbolo perdido.

---

## Resultados (gates)

| Gate | Resultado |
|---|---|
| A1 (grep parser posicional) | ✅ zero referências em `.py` |
| B1 (suíte completa, `.venv`) | ✅ **263 passed** (0 falhas) |
| B1-2 (`from core.`) | apenas `benchmark/` (consumer externo → B2) |

- **Suíte**: saiu de *"1 erro de coleta / 42 itens"* → **263 passed** (100% verde).
- Itens ainda pendentes **fora deste escopo**: B0.4 (`df.reindex`), B0.7 (vocabulário telemetria), B0.9 (smoke), B0.5 (baseline), B2 (benchmark→ports / remover `sys.path.insert` e `_montar_mensagens_com_reforco`), B3–B7.
