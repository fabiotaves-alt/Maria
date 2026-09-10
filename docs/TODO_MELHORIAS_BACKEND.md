# TODO — Melhorias Pendentes do Backend

> Itens extraídos do relatório de análise (`docs/arquivo/analise_backend_20260903.md`).
> Prioridade: baixa/média (não bloqueantes).

---

## Riscos pendentes

### 1. Conexão SQLite compartilhada entre threads
- **Arquivo:** `backend/database/connection.py`
- **Prioridade:** Média
- **Descrição:** Uma única conexão global com `check_same_thread=False` atendendo múltiplas threads do Flask. `sqlite3` do Python não permite uso concorrente real da mesma conexão.
- **Solução sugerida:** Usar `threading.local` (uma conexão por thread) ou pool de conexões.
- **Relacionado:** Melhoria #3.

### 5. `finalizar()` do controller vazio
- **Arquivo:** `backend/core/maria_controller.py`
- **Prioridade:** Média
- **Descrição:** Não fecha conexão SQLite nem libera recursos no encerramento.
- **Solução sugerida:** Chamar `close_connection()` no `finalizar()`.
- **Relacionado:** Melhoria #5.

### 7. `nvmlInit/nvmlShutdown` a cada status
- **Arquivo:** `backend/bridge/comandos.py`
- **Prioridade:** Baixa
- **Descrição:** Inicialização da GPU sem cache; ineficiência leve.
- **Solução sugerida:** Cache lazy singleton do handle NVML.

---

## Melhorias pendentes

### 3. Connection pool / `threading.local` para SQLite
- **Arquivo:** `backend/database/connection.py`
- **Prioridade:** Média
- **Descrição:** Mitiga o risco #1. Uma conexão por thread via `threading.local`.
- **Nota:** Requer `PRAGMA journal_mode=WAL` em cada nova conexão.

### 4. Tipar payloads de tool call
- **Arquivo:** `backend/bridge/comandos.py` (handlers)
- **Prioridade:** Baixa
- **Descrição:** Hoje dicts soltos `{"name", "arguments"}`. Usar `TypedDict` ou `dataclass`.
- **Benefício:** Melhor autocompletar, validação estática, documentação.

### 5. `PRAGMA synchronous` + fechar conexão no shutdown
- **Arquivos:** `backend/database/connection.py`, `backend/core/maria_controller.py`
- **Prioridade:** Média
- **Descrição:** Adicionar `PRAGMA synchronous = NORMAL` (WAL-compatible) e garantir `close_connection()` no shutdown.
- **Relacionado:** Risco #5.

### 7. Remover código morto/arquivos de debug
- **Arquivos:** `backend/arquivo/debug_raw_ollama.py`, `backend/arquivo/debug_raw_ollama_2systems.py`, `backend/arquivo/saida_task*.json`
- **Prioridade:** Baixa
- **Descrição:** Arquivos de debug que referenciam constantes já removidas (`OLLAMA_MODEL`, `OLLAMA_BASE_URL` etc.) — estão funcionalmente quebrados.
- **Ação:** Deletar arquivos.

---

## Resumo

| Prioridade | Itens |
|------------|-------|
| Média | SQLite threading.local, `finalizar()`, PRAGMA synchronous |
| Baixa | Tipar payloads, cache NVML, remover debug |

---

*Última atualização: 2026-09-06*
