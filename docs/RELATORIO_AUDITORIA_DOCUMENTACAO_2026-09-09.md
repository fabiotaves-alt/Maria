# Relatório de Auditoria da Documentação — MARIA

**Data:** 2026-09-09
**Branch:** `docs/guia-canonico-principios`
**Escopo:** apenas documentação (`README.md`, `CHANGELOG.md`, `docs/*.md`, `docs/arquivo/`, `docs/dev_base/`, `docs/dev_senior/`, `TO DO.txt` da raiz, `docs/install-dependencies.ps1`). Código (`backend/arquivo/debug_*`, `saida_task*.json`) citado como débito, sem movimentação.
**Baseline de testes:** 265 passed (2026-09-08). **Versão:** v4.2.5-dev.
**Metodologia:** leitura integral dos docs vivos + `Test-Path` de links/paths + `git mv` (histórico preservado) + correção de referências quebradas.

---

## 1. Resumo executivo

- **Ativos e relevantes (mantidos + atualizados):** `README.md`, `CHANGELOG.md`, `docs/PROGRESSO_DESENVOLVIMENTO.md`, `docs/GUIA_DESENVOLVIMENTO_v2_canonico.md` (canônico), `docs/PRINCIPIOS_DE_ENGENHARIA_DE_SOFTWARE.md`, `docs/ARQUITETURA_SISTEMA.md`, `docs/GUIA_TESTES_EMPIRICOS.md`, `docs/GUIA_INSTALACAO.md`, `docs/SEGURANCA.md`, `docs/DECISOES_BANCO_DADOS.md`, `docs/TODO_MELHORIAS_BACKEND.md`, `docs/REGRAS_OPERACAO_LLAMA_SERVER.md`, `docs/install-dependencies.ps1`, `docs/dev_base/` (3), `docs/dev_senior/` (7, inclui `plano_mestre_v5.md`).
- **Arquivados em `docs/arquivo/` (4):** `GUIA_DESENVOLVIMENTO.md` (superado pelo v2 canônico); `MELHORIAS_RELATORIO.md` (backlog v4.1.1 fechado); `RELATORIO_BENCHMARK_DIAGNOSTICO.md` (snapshot pré-B0, era posicional); `TO DO.txt` da raiz (brainstorm era JavaFX + ASCII-art + bug superado). Banners inseridos no topo de cada arquivo.
- **Correções aplicadas:** `README.md` (versão, status, 265 testes, links, árvore `benchmarks/maria_bench/`, roadmap B4.5/B4.6); `GUIA_TESTES_EMPIRICOS.md` (versão, 265 passed, `maria_bench`, setup `uv`); `ARQUITETURA_SISTEMA.md` (header + tabela); `GUIA_INSTALACAO.md` (header + nota `uv`); `REGRAS_OPERACAO_LLAMA_SERVER.md` (2 paths); `GUIA_DESENVOLVIMENTO_v2_canonico.md` (§6.2); `install-dependencies.ps1` (`--host 127.0.0.1`); `PROGRESSO_DESENVOLVIMENTO.md` (path `dev_base`).
- **Testes:** alterações restritas a `.md`/`.ps1`/`.txt` — suíte `pytest` não afetada (baseline 265 passed mantido).

## 2. Tabela MANTER / ARQUIVAR

| Arquivo | Veredito | Motivo |
|---|---|---|
| `README.md` | MANTER + CORRIGIR (feito) | Ativo; versão, testes, links e árvore defasados |
| `CHANGELOG.md` | MANTER (sem toque) | Fonte viva, topo B2/FIX-4/B0.5 correto |
| `docs/PROGRESSO_DESENVOLVIMENTO.md` | MANTER + patch path (feito) | Roadmap vivo; path `desenvolvedor_base` quebrado |
| `docs/GUIA_DESENVOLVIMENTO_v2_canonico.md` | MANTER + patch path (feito) | Canônico v2.0; §6.2 citava path antigo |
| `docs/PRINCIPIOS_DE_ENGENHARIA_DE_SOFTWARE.md` | MANTER | Genérico, ref da Seção 2.4 do canônico |
| `docs/ARQUITETURA_SISTEMA.md` | MANTER + CORRIGIR (feito) | Header e contagem de testes defasados |
| `docs/GUIA_TESTES_EMPIRICOS.md` | MANTER + CORRIGIR (feito) | O mais defasado (120 passed, paths, pip) |
| `docs/GUIA_INSTALACAO.md` | MANTER + CORRIGIR (feito) | Faltava menção ao `uv` canônico |
| `docs/SEGURANCA.md` | MANTER | Auditado v4.1.1, sem refs quebradas |
| `docs/DECISOES_BANCO_DADOS.md` | MANTER | Schema canônico válido |
| `docs/TODO_MELHORIAS_BACKEND.md` | MANTER | Backlog vivo do backend |
| `docs/REGRAS_OPERACAO_LLAMA_SERVER.md` | MANTER + CORRIGIR (feito) | 2 paths de benchmark antigos |
| `docs/install-dependencies.ps1` | MANTER + CORRIGIR (feito) | Tinha `--host 0.0.0.0` inseguro |
| `docs/dev_base/` (3) + `docs/dev_senior/` (7) | MANTER | Working set v5 (`plano_mestre_v5.md` = fonte do ciclo) |
| `docs/arquivo/` (15 pré-existentes) | MANTER | Era JavaFX já arquivada corretamente |
| `docs/GUIA_DESENVOLVIMENTO.md` | ARQUIVADO → `arquivo/GUIA_DESENVOLVIMENTO_v1_legado.md` | Duplicata superada pelo v2 canônico |
| `docs/MELHORIAS_RELATORIO.md` | ARQUIVADO → `arquivo/MELHORIAS_RELATORIO_v411_legado.md` | Backlog v4.1.1 fechado |
| `docs/RELATORIO_BENCHMARK_DIAGNOSTICO.md` | ARQUIVADO → `arquivo/RELATORIO_BENCHMARK_DIAGNOSTICO_20260904.md` | Snapshot pré-B0 da era posicional |
| `TO DO.txt` (raiz) | ARQUIVADO → `arquivo/TO_DO_legacy_raiz.txt` | Brainstorm legado (JavaFX, ASCII-art) |


## 3. Código morto / links quebrados / débitos

- **Código morto (registrado, não movido — fora do escopo docs):** `backend/arquivo/debug_raw_ollama.py`, `debug_raw_ollama_2systems.py`, `saida_task*.json` — referenciam `OLLAMA_MODEL`/`OLLAMA_BASE_URL` removidos (`TODO_MELHORIAS_BACKEND.md#7` sugere deletar em ciclo de código).
- **Links quebrados corrigidos (`Test-Path` False → path real):** `docs/INSTALL_GUIDE.md` → `docs/GUIA_INSTALACAO.md`; `docs/INSTALACAO_WHISPER.md` → `docs/REGRAS_OPERACAO_LLAMA_SERVER.md` (Whisper vive em `GUIA_INSTALACAO.md` §4.2); `backend/benchmark/*` → `backend/benchmarks/maria_bench/*` (pós-B2); `docs/desenvolvedor_base/*` → `docs/dev_base/*`.
- **Débitos futuros:** `ARQUITETURA_SISTEMA.md` ainda descreve `core/*` como atual (completar seção hexagonal); Roadmap `README` v4.3–v5.0 ignora fases B0–B7 (alinhar pós-B7); `install-dependencies.ps1` + `GUIA_INSTALACAO.md` §3 ainda priorizam `pip` sobre `uv`; menção a `frontend-tauri/IMPLEMENTACAO_COMPLETA.md` (arquivado) no script.

## 4. Arquivos alterados (2026-09-09)

`git mv` (4): GUIA_DESENVOLVIMENTO, MELHORIAS_RELATORIO, RELATORIO_BENCHMARK_DIAGNOSTICO, TO DO.txt → `docs/arquivo/` com banners. Editados (8): `README.md`, `GUIA_TESTES_EMPIRICOS.md`, `ARQUITETURA_SISTEMA.md`, `GUIA_INSTALACAO.md`, `REGRAS_OPERACAO_LLAMA_SERVER.md`, `GUIA_DESENVOLVIMENTO_v2_canonico.md`, `install-dependencies.ps1`, `PROGRESSO_DESENVOLVIMENTO.md`. Novo (1): este relatório.
