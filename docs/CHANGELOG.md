# CHANGELOG

Registro de alterações do **MARIA** (v4.x). Cada entrada descreve uma tarefa concluída.

## 2026-08-31 — Robustez do fluxo de confirmação e erros no MariaRunner (benchmark) + testes

### Alterações realizadas
- **Tarefa 4 — Negação/ambiguidade zera `tool_call_final`** (`backend/benchmark/runners/maria_runner.py`): quando o usuário **nega** a confirmação ou responde de forma **ambígua** (2 respostas ambíguas), `tool_call_final` é definido como `None` — a ferramenta não é executada e `confirmation_completed` é marcado como concluído, com mensagens "Ação cancelada." / "Ação cancelada por ambiguidade.".
- **Tarefa 5 — Preenchimento da mensagem de erro** (`backend/benchmark/runners/maria_runner.py`): quando a execução da ferramenta levanta exceção (ex.: `ValueError` de arquivo inexistente em edição), `final_message` passa a conter a mensagem do erro (prefixo `[ERRO]`/mensagem amigável) em vez de ficar vazia, e o erro é registrado em `errors` com `runtime_ok=False`.
- Ajustes correlatos de sessões anteriores nesta working tree: `report.py`, `run_benchmark.py`, `tasks_core.py`, `tasks_edges.py`, `config.py`, `llama_client.py` (TTFT), `README_benchmark.md`.
- **Novos testes** (`backend/tests/test_maria.py`):
  - `TestMariaRunnerNegaEAmbiguidade`: `test_negacao_anula_tool_call` e `test_ambiguidade_anula_tool_call` (verificam `tool_detected=None`, `tool_correct=True`, `confirmation_completed=True` e mensagem final).
  - `TestMariaRunnerMensagemDeErro`: `test_value_error_edicao_inexistente_preenche_final_message` (verifica `errors`, `runtime_ok=False` e `final_message` com "não encontrado").

### Status dos testes
- `backend/tests/test_maria.py`: **120 testes passados** (3.74s) — 116 anteriores + 4 novos.

### Cobertura de código
- Cobertura formal não medida (pendente item do roadmap); os módulos afetados estão cobertos pela suíte existente, agora com 4 casos novos de confirmação/erro.

### Arquivos alterados
- `backend/benchmark/runners/maria_runner.py`
- `backend/benchmark/analysis/report.py`
- `backend/benchmark/run_benchmark.py`
- `backend/benchmark/tasks/tasks_core.py`
- `backend/benchmark/tasks/tasks_edges.py`
- `backend/benchmark/README_benchmark.md`
- `backend/core/config.py`
- `backend/core/llama_client.py`
- `backend/tests/test_maria.py`
- `docs/CHANGELOG.md`
- `docs/PROGRESSO_DESENVOLVIMENTO_V1.md`


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