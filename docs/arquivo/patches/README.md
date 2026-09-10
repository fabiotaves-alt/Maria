# Patches arquivados

Trabalho preservado de branches órfãs — não integrado em `develop`, mantido aqui
para não se perder. Nenhum destes patches foi aplicado.

---

## `2026-09-02_language-check-fixture-planilha.patch`

**Origem:** commit `5f4e9b6` — *`feat(benchmark): fixtures reais de planilha, language check robusto e warmup estendido`*
**Branch:** `feat/benchmark-contexto-timeouts-numctx` (base `bf0fa67`, 2026-09-02)
**Estado da branch:** órfã. Nunca foi integrada em `develop`; a branch já não existe
no remoto (apenas um ref local *stale*, removido em 2026-09-10 com `git remote prune origin`).
Este patch é a **única cópia preservada** desse trabalho.
**Autor original:** Fábio Adriano Queirolo Taves — metadados de autoria preservados no patch.

**O que contém (10 ficheiros):**

| Ficheiro | Conteúdo |
|---|---|
| `backend/benchmark/analysis/language_check.py` | Lista de exclusão PT/EN ampliada (15 → 137 palavras), normalização NFKD (remove acentos, corrige `não`/`nao`), limiar recalibrado 3% → 4%, com nota de desenho a excluir `a`/`do`/`no`/`so`/`me` (também portuguesas). |
| `backend/benchmark/tasks/task_schema.py` | Novo campo `MariaTask.fixture_planilha: dict \| None = None` (retrocompatível). |
| `backend/benchmark/tasks/tasks_core.py` | Tarefas 11–13 (gastos, estoque, contatos) passam a declarar fixtures com colunas e linhas reais. |
| `backend/benchmark/runners/maria_runner.py` | `_garantir_planilha_existente()` deixa de usar regex sobre o `context` e passa a ser determinístico: cria a planilha a partir de `fixture_planilha`, com header em negrito e linhas reais (fim da planilha *dummy* `"Fixture do benchmark"`). |
| `backend/benchmark/run_benchmark.py` | Warmup estendido (3 chamadas variadas: latência pura, geração de texto, caminho de tool call) e `--delay` efetivamente aplicado (era parseado e ignorado). |
| `backend/tests/test_maria.py` | +173 linhas: `TestGarantirPlanilhaFixture` (4), `TestLanguageCheckRobusto` (4), `TestWarmupEstendido` (2), `TestFixturesTarefas` (1). |
| 2 × `gastos_3*.xlsx` | Fixtures binárias das tarefas de edição. |
| `CHANGELOG.md`, `docs/PROGRESSO_DESENVOLVIMENTO.md` | Entradas `[4.1.8]` da época (preservadas por contexto histórico). |

**⚠️ Exclusão deliberada de segurança:** este patch foi gerado com
`git format-patch --binary ... -- ':!frontend-tauri/shared/.bridge_token'`.
O commit original alterava também esse ficheiro (2 linhas); esse hunk foi
**removido** por conter o valor do token de autenticação do bridge. Ver a nota
de segurança em `docs/SEGURANCA.md` §5. O patch, tal como está, **não contém
qualquer valor de token** (verificado: 0 ocorrências).

**Porque não foi portado (2026-09-10):**
1. Exige adaptação, não aplicação direta: os ficheiros vivem agora em
   `backend/benchmarks/maria_bench/…` (migração B2) e o código instancia
   `OllamaClient`, enquanto `develop` usa `LlamaClient`.
2. O novo limiar de idioma (4%) é um **critério de aceite do benchmark** e só é
   validável por **reexecução real** do benchmark — os testes unitários que o
   acompanham fixam o corte mas não validam a calibração.
3. É a mesma área de trabalho da fase **R1/R2** da refatorização de tarefas
   (fixtures de planilha com dados reais) — candidato a retomar em conjunto.

**Como aplicar (se for retomado):**
```powershell
git am --3way docs/arquivo/patches/2026-09-02_language-check-fixture-planilha.patch
```
Esperar conflitos de caminho (`backend/benchmark/` → `backend/benchmarks/maria_bench/`)
e resolver manualmente — o patch é do layout pré-B2.

---

## 📤 Nota de handoff — sinergia com a Fase R3 (outra equipa)

A fase **R3** em curso mexe exatamente em **fixtures de planilha com dados reais** — a
mesma área de trabalho de `fixture_planilha` neste patch. **Nada foi decidido nem
portado:** este registo existe apenas para que a equipa da R3 avalie se há sinergia.

Pontos que podem ser úteis para eles:
- O patch resolve o mesmo problema de fundo: substituir a geração *dummy* de planilhas
  (via regex sobre o texto do `context`) por uma **declaração explícita e determinística**
  no schema da tarefa (nome + colunas + linhas reais).
- O contrato novo testado é: *um `context` que apenas menciona "já foi criada" não cria
  ficheiro nenhum* — evita fixtures fantasma que mascaravam falhas do modelo.
- Se a R3 introduzir fixture declarativa própria, este patch deve ser **descartado** em
  favor dela (evitar duas fontes de verdade para o mesmo conceito).

