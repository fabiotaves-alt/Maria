# Relatório de Auditoria — Estado do Projeto MARIA

**Data:** 2026-09-10 · **Branch:** `feat/f1.1-confirmacao-card` (`50abedf`)
**Escopo:** `docs/dev_senior/`, `CHANGELOG.md`, guia canónico, histórico de commits, estrutura de branches.

---

## 1. Figura do estado real (integração e branches)

**`origin/main` está parado em `e75a65c` (2026-09-05)** — o último merge real foi o "PR #32". Toda a profissionalização recente vive fora de `main`, em fan-out de branches.

| Indicador | Valor |
|---|---|
| HEAD | `feat/f1.1-confirmacao-card` (`50abedf`, 2026-09-10) |
| `origin/main` | `e75a65c` (2026-09-05) |
| Commits de `main` até HEAD | 32 |
| Branches totais (local + remota) | 62 |
| Branches não mergeadas em `main` | 28 |
| Commits locais sem push | 1 (`f3269f9`, `feat/b7a-core-cleanup`) |

**Integrado no tronco atual:** B0 (parser JSON), B1 (hexagonal domain/interfaces), B2 (benchmark→ports), migração hexagonal Fase 1–4, auditoria de docs, F1.1. **269 testes.**

**Ainda em branches paralelas (não mergeadas):** `feat/b3-storage-report-v2`, `feat/b4-tasks-v2`, `feat/b5-cli-unificada`, `feat/b6-judge-response-format`, `feat/b7a-core-cleanup` (283 testes), + ~20 features pontuais.

> **Implicação crítica:** `feat/b7a-core-cleanup` — a fase que resolve o BUG-2 (esvazia as cópias divergentes de `core/`) — está não-mergeada e sem push.

---

## 2. Processo de documentação

### 2.1 Definido (e sólido)
Precedência de fontes vivas (guia §0/§4): **`CHANGELOG.md`** (nº 1) → **`docs/ARQUITETURA_SISTEMA.md`** → **`plano_mestre_v5.md`** → **`GUIA_DESENVOLVIMENTO.md`** (diretrizes).

Fluxo pós-tarefa: `git status` → atualizar `CHANGELOG` + `PROGRESSO_DESENVOLVIMENTO` → commit *Conventional Commits* em PT → push em branch nova (com autorização). Relatórios de execução com **gates binários** (`docs/dev_senior/execucao_*.md`) — prática madura.

### 2.2 Violado na prática
| # | Violação | Evidência |
|---|---|---|
| V1 | Sem integração em `main` | 32 commits atrás; 28 branches não mergeadas |
| V2 | SemVer quebrado | 17 entradas `[4.2.5-dev]` sem bump desde `[4.2.5]` |
| V3 | Contagem de testes divergente | 265 / 269 / 283 |
| V4 | Docs descrevem estado desatualizado | guia §5 dizia `domain/`/`interfaces/` "não existem"; ARQUITETURA descreve `core/*` como atual |
| V5 | Commit sem push | `f3269f9` |
| V6 | Corrupção de encoding | `execucao_etapa_1_2_destravar_suite.md` |
| V7 | Data CHANGELOG ≠ commit | F1.1: "09-09" vs "09-10" |

---

## 3. Auditoria dos últimos commits

**A manter:** Conventional Commits consistentes; escopo disciplinado; gates binários; baseline de benchmark versionada (3B vs 7B).

**A corrigir:** autor único (sem revisão por pares); merges regulares até 2026-09-05 e zero depois; datas divergentes; contagem de testes instável (252→262→263→265→269→273→283); encoding corrompido em relatórios.

---

## 4. Consolidação dos achados

| ID | Tipo | Descrição | Estado |
|---|---|---|---|
| BUG-1 | bug | `README.md` terminava com `# CHANGELOG` órfão | ✅ corrigido |
| BUG-2 | bug | Módulos divergentes: testes usam `core/`, produção usa `infrastructure/`/`domain/` | ✅ corrigido |
| BUG-3 | bug | `domain/` importa `core/` (viola camadas) | ⏳ aberto |
| BUG-4 | bug | Contagem de testes inconsistente (265/269/283) | ✅ corrigido |
| BUG-5 | bug | Comandos bridge 19 vs 21 | ⏳ aberto |
| LACUNA-1/2 | docs | guia §5 + `ARQUITETURA_SISTEMA.md` desatualizados | ✅ corrigido |
| LACUNA-3 | docs | README (árvore/diagrama/roadmap) | ✅ corrigido |
| CONCEITO-1/2/3 | conceito | taxonomia de fases; SemVer; fragmentação de branches | ⏳ aberto |

---

## 5. Caminhos recomendados

1. Definir a linha de integração canónica e reativar merge periódico para `main`.
2. Resolver BUG-2 (testes validando código divergente).
3. Reconciliar versão + contagem de testes numa fonte única.
4. Atualizar docs de arquitetura (guia §5 + `ARQUITETURA_SISTEMA.md`).
5. Corrigir encoding de relatórios de execução.
6. Alinhar taxonomia de fases (B0–B7 única).
7. Executar fluxo pós-tarefa (CHANGELOG + PROGRESSO + commit em branch nova).

*Fim do relatório.*
