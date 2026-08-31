# CHANGELOG

Registro de alterações do **MARIA** (v4.x). Cada entrada descreve uma tarefa concluída.

---

## 2026-08-31 — Correção do cálculo de TTFT (Time To First Token) no LlamaClient

### Alterações realizadas
- Em `backend/core/llama_client.py`, nos métodos `chat_stream()` e `continuar_com_resultado_ferramenta_stream()`, a chamada `inicio = time.monotonic()` foi **movida de após** `self._make_request(payload, stream=True)` para **antes** da requisição HTTP.
- Anteriormente o timer começava no início da iteração do streaming (`for line in response.iter_lines()`), ignorando o tempo de envio do POST, processamento pelo llama-server e geração do primeiro token (TTFT de ~0.07ms, fisicamente impossível).
- Após a correção, o timer inicia no momento exato do envio da requisição, de modo que `t_primeiro_token = time.monotonic() - inicio` reflete o TTFT real (típico entre 50ms e 5s segundo hardware).

### Status dos testes
- `backend/tests/test_maria.py`: **116 passados, 33 subtests passados** (3.31s).
- `python -m py_compile backend/core/llama_client.py`: **OK** (sem erros de sintaxis/importación).

### Cobertura de código
- Não fue alterada por esta tarefa; os módulos afetados (`llama_client.py`) estão cobertos pela suíte existente.

### Arquivos alterados
- `backend/core/llama_client.py`
- `docs/CHANGELOG.md` (novo)
- `docs/PROGRESSO_DESENVOLVIMENTO_V1.md`