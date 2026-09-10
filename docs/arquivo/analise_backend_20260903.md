# Relatório de Análise do Backend — MARIA

> ⚠️ **ARQUIVADO** — Este documento foi arquivado após a conclusão das correções e testes de regressão. Data de arquivamento: 2026-09-06. Itens pendentes foram migrados para `docs/TODO_MELHORIAS_BACKEND.md`.

**Data original:** 2026-09-03
**Escopo:** análise de erros, bugs e oportunidades de melhoria no backend (`backend/`).
**Resultado dos testes:** 180 testes + 33 subtests aprovados (sem regressões).

---

## 1. Resumo executivo

O backend da MARIA é, em linhas gerais, bem organizado: separação por camadas
(`core/`, `bridge/`, `database/`, `benchmark/`), sanitização de nomes de arquivo,
restrição de leitura a pastas permitidas e confirmação do usuário antes de
qualquer escrita em disco. Apesar disso, a revisão encontrou **7 bugs concretos**
na camada de comandos do bridge e em utilitários, além de pontos de risco
(concorrência no SQLite, código morto, duplicação de clientes LLM) e
oportunidades de melhoria.

Todos os 7 bugs foram **corrigidos** nesta rodada e a suíte de testes passou
sem regressões. Em 2026-09-06, foram adicionados **23 testes de regressão**
(`backend/tests/test_comandos_bridge.py`) para prevenir reintrodução.

---

## 2. Bugs corrigidos

### BUG 1 — `carregar_sessao` acessava dict como objeto
**Arquivo:** `backend/bridge/comandos.py`

- `carregar_sessao()` retorna um `dict` (não um `ChatSession`), mas o código
  acessava `sessao.historico` → `AttributeError`.
- Era passado apenas o `nome` (filename) para uma função que exige **caminho
  completo**.
- **Correção:** resolve o nome do arquivo via `listar_sessoes_salvas()` (aceita
  também caminho absoluto), carrega o dict e acessa `dados["historico"]`.

### BUG 2 — `criar_automacao` violava `NOT NULL`
**Arquivo:** `backend/bridge/comandos.py`

- O `INSERT` omitia a coluna `acao`, que é `TEXT NOT NULL` no schema
  (`database/schema.py` e `shared/schema.sql`) → `IntegrityError`.
- **Correção:** inclui `acao` (default vazio) e `gatilho` no `INSERT`.

### BUG 3 — Nome de coluna incorreto em automações
**Arquivo:** `backend/bridge/comandos.py`

- `listar_automacoes` e `toggle_automacao` usavam a coluna `ativa`, mas o schema
  define `ativo` → `sqlite3.OperationalError: no such column`.
- **Correção:** SQL passa a usar `ativo` (a chave JSON de saída permanece
  `"ativa"` para não quebrar o contrato com o frontend).

### BUG 4 — `exportar_conversa` usava função inexistente
**Arquivos:** `backend/bridge/comandos.py`, `backend/core/session_storage.py`

- `from ...session_storage import exportar_sessao` importava uma função que não
  existia → `ImportError`.
- **Correção:** `exportar_sessao(sessao, formato)` foi implementada em
  `session_storage.py`, exportando para `.txt` (legível) ou `.json`.

### BUG 5 — `ler_planilha_resumo` unia com `\n` literal
**Arquivo:** `backend/core/excel_handler.py`

- `return "\\n".join(resumo)` produzia `\n` literal (barra invertida + "n") em
  vez de quebra de linha.
- **Correção:** `return "\n".join(resumo)`.

### BUG 6 — Modelo Ollama com espaço no nome
**Arquivo:** `backend/core/config.py`

- `OLLAMA_MODEL` padrão era `"qwen2.5:3b omni"` (tag de modelo com espaço, que
  não é válida no Ollama).
- **Correção:** alterado para `"qwen2.5:3b"`. *(Observação: o backend usa
  principalmente `LlamaClient`/`llama-server`; a tag exata do Ollama deve ser
  confirmada quando esse caminho voltar a ser usado.)*

### BUG 7 — `listar_memoria` não retornava `id`
**Arquivo:** `backend/bridge/comandos.py`

- `listar_memoria` devolvia apenas `fato/categoria/relevancia`, mas
  `deletar_memoria` exige `id`. O frontend nunca recebia o `id` necessário.

---

## 3. Riscos e observações (não bloqueantes)

| # | Item | Local | Status | Observação |
|---|------|-------|--------|------------|
| 1 | Conexão SQLite compartilhada entre threads | `database/connection.py` | ⚠️ Pendente | Uma única conexão global com `check_same_thread=False` atendendo múltiplas threads do Flask. Recomenda-se `threading.local` (uma conexão por thread) ou pool. |
| 2 | `core/router.py` (código morto) | `core/router.py` | ✅ Documentado | Mantido por decisão do projeto e **documentado** para integração futura (ver docstring do arquivo). |
| 3 | Duplicação `llama_client.py` × `ollama_client.py` | `core/` | ✅ Resolvido | `ollama_client.py` removido; apenas `llama_client.py` permanece. |
| 4 | Alias enganoso | `core/maria_controller.py:12` | ✅ Corrigido | `LlamaClient as OllamaClient` → `LlamaClient` (controller e runner). |
| 5 | `finalizar()` do controller vazio | `core/maria_controller.py` | ⚠️ Pendente | Não fecha conexão SQLite nem libera recursos no encerramento. |
| 6 | Token do bridge em Windows | `bridge/servidores.py` | 🟡 Risco baixo | `chmod 0o600` só roda em POSIX; no Windows o token fica com permissões padrão (servidor em 127.0.0.1). |
| 7 | `nvmlInit/nvmlShutdown` a cada status | `bridge/comandos.py` | ⚠️ Pendente | Inicialização da GPU sem cache; ineficiência leve. |

---

## 4. Oportunidades de melhoria

| # | Item | Status |
|---|------|--------|
| 1 | Refatorar `_despachar_comando` para registro de comandos (`_COMANDOS`) | ✅ Feito |
| 2 | Unificar os dois clientes LLM numa classe base | ✅ Feito |
| 3 | Connection pool / `threading.local` para o SQLite | ⚠️ Pendente |
| 4 | Tipar os payloads de tool call com `dataclass`/`TypedDict` | ⚠️ Pendente |
| 5 | Adicionar `PRAGMA synchronous` e fechar conexão no shutdown | ⚠️ Pendente |
| 6 | Ampliar testes da camada `bridge/comandos.py` | ✅ Feito (23 testes) |
| 7 | Remover código morto/arquivos de debug | ⚠️ Pendente |

---

## 5. Segurança (pontos positivos)

- Sanitização de nome de arquivo (`sanitizar_nome_arquivo`) e resolução de
  caminhos restrita a pastas permitidas (`resolver_caminho_permitido`).
- Escrita em disco exige confirmação do usuário (`acao_pendente` +
  `interpretar_confirmacao`).
- Bridge HTTP exige token Bearer (comparação em tempo constante) e CORS
  restrito; bind em `127.0.0.1`.

---

## 6. Arquivos alterados nesta análise

| Arquivo | Alteração |
|---------|-----------|
| `backend/bridge/comandos.py` | Corrigidos bugs 1, 2, 3 e 7 |
| `backend/core/session_storage.py` | Implementada `exportar_sessao` (bug 4) |
| `backend/core/excel_handler.py` | Corrigido `\n` literal (bug 5) |
| `backend/core/config.py` | Corrigido `OLLAMA_MODEL` (bug 6) |
| `backend/core/router.py` | Documentação para integração futura (mantido) |
| `backend/tests/test_comandos_bridge.py` | 23 testes de regressão (adicionado em 2026-09-06) |

- **Correção:** `id` incluído no `SELECT` e na resposta.
