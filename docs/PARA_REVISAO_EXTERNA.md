# Guia de Revisão Externa — Projeto MARIA

**Repositório:** https://github.com/fabiotaves-alt/Maria
**Branch principal de desenvolvimento:** [`develop`](https://github.com/fabiotaves-alt/Maria/tree/develop) — é aqui que está o trabalho mais recente e verde. `main` é a linha de releases estáveis (avança apenas em bumps de versão formais).
**Versão atual:** v4.2.5-dev · **Suíte de testes:** 288 passed
**Data deste guia:** 2026-09-10

---

## Por onde começar

Sugestão de ordem de leitura, do geral para o específico:

1. **[`README.md`](https://github.com/fabiotaves-alt/Maria/blob/develop/README.md)** — o que o projeto é, arquitetura de alto nível, como rodar.
2. **[`docs/ARQUITETURA_SISTEMA.md`](https://github.com/fabiotaves-alt/Maria/blob/develop/docs/ARQUITETURA_SISTEMA.md)** — diagrama de componentes, protocolo de comunicação, estado por camada.
3. **[`docs/GUIA_DESENVOLVIMENTO.md`](https://github.com/fabiotaves-alt/Maria/blob/develop/docs/GUIA_DESENVOLVIMENTO.md)** — referencial teórico (arquitetura hexagonal, DDD, SOLID) aplicado concretamente ao código real, com exemplos.
4. **[`CHANGELOG.md`](https://github.com/fabiotaves-alt/Maria/blob/develop/CHANGELOG.md)** — histórico completo, versão a versão, com justificativas técnicas de cada decisão.
5. **[`docs/PROGRESSO_DESENVOLVIMENTO.md`](https://github.com/fabiotaves-alt/Maria/blob/develop/docs/PROGRESSO_DESENVOLVIMENTO.md)** — painel de controle vivo: o que está feito, o que está em andamento, o que foi adiado e por quê.

---

## O que este projeto é

**MARIA** é uma assistente de IA de escritório que roda 100% localmente (LLM via `llama-server`/llama.cpp, sem dependência de nuvem). Backend em Python 3.11+ com arquitetura hexagonal (domain/application/infrastructure/interfaces), frontend em Tauri v2 + React, e um **framework de benchmark próprio** para avaliar a qualidade do tool-calling do modelo de linguagem em tarefas reais de escritório (criar planilhas, documentos, RAG de manual de redação oficial, etc.).

---

## O fluxo de desenvolvimento — o que vale destacar na revisão

Este projeto foi desenvolvido com um método específico, deliberado, que vale a pena examinar como parte da avaliação (não é só "o código", é a **disciplina de processo** por trás dele):

- **Cada fase de trabalho** (identificadas como B0, B1, B2... no `plano_mestre_v5.md` e no CHANGELOG) segue um ciclo fixo: diagnóstico de código real (greps direcionados, nunca suposição) → prompt de execução com critérios de aceite verificáveis e binários → execução → relatório de fechamento com evidência literal (saída de comandos, contagem de testes) → documentação obrigatória (CHANGELOG + PROGRESSO) → commit → autorização explícita para push.
- **Nenhuma fase avança sem a suíte de testes 100% verde.** A contagem de testes é rastreável commit a commit no CHANGELOG (22 → ... → 283 → 288 ao longo do histórico).
- **Débitos técnicos nunca ficam implícitos.** Toda decisão de adiar algo é registrada com o motivo (ver exemplo abaixo).
- Histórico de branches consolidado recentemente (higiene de repositório: de ~30 branches acumuladas para `develop` + `main`), documentado em `CHANGELOG.md` na entrada mais recente.

### Exemplo concreto de rastreabilidade de débito técnico

Em 2026-09-02, uma sessão de trabalho produziu melhorias reais (heurística de detecção de idioma mais robusta, fixtures determinísticas de planilha) numa branch que acabou não sendo integrada a tempo e ficou órfã. Em vez de simplesmente descartar esse trabalho ao limpar o repositório:
- O patch completo foi **preservado e versionado** em [`docs/arquivo/patches/`](https://github.com/fabiotaves-alt/Maria/tree/develop/docs/arquivo/patches).
- O motivo de não integrar imediatamente foi documentado (risco de circularidade: o novo critério de aceite do benchmark só é validável por reexecução real, não pelos testes unitários que o acompanham).
- Uma imprecisão na documentação original daquele trabalho (uma mudança apresentada como "correção de bug" quando na verdade era uma decisão de design preventiva) foi identificada e corrigida na nova entrada, **sem reescrever o histórico antigo**.

Isso está documentado na entrada mais recente do `CHANGELOG.md`.

---

## Estado atual do projeto (v4.2.5-dev)

Ciclo de refatoração hexagonal do backend (fases B0 a B7a do `docs/dev_senior/plano_mestre_v5.md`) concluído:
- Separação em camadas `domain/` / `application/` / `infrastructure/` / `interfaces/`, com `core/` sendo esvaziado progressivamente (módulos legados viram stubs de compatibilidade com `DeprecationWarning`, nunca removidos abruptamente).
- Framework de benchmark próprio com storage SQLite, CLI unificada (`run`/`report`/`compare`), e um módulo experimental de avaliação por LLM-as-judge (explicitamente marcado como não calibrado até haver rotulagem manual — nada é apresentado como métrica oficial sem validação humana).

**Pendente (fase B7b, próxima):** configuração de `import-linter` para enforçar automaticamente as regras de dependência entre camadas, `ARQUITETURA.md` consolidado, e CI (`.github/workflows`).

---

## Segurança e transparência

Ver [`docs/SEGURANCA.md`](https://github.com/fabiotaves-alt/Maria/blob/develop/docs/SEGURANCA.md), §5 — inclui o registro transparente de um token de sessão (gerado dinamicamente a cada execução, sem valor persistente) que esteve em commits históricos do repositório. Avaliação de impacto e decisão de não reescrever o histórico (para preservar a integridade de hashes/rastreabilidade) estão documentadas ali.

---

## Dúvidas ou pontos específicos

O código-fonte é a fonte de verdade em caso de qualquer divergência com a documentação — mas se a documentação estiver desatualizada em algum ponto, isso também é, por si, um dado relevante sobre o estado do projeto (é tratado como tal nos relatórios de auditoria em `docs/`, ex. `RELATORIO_AUDITORIA_ESTADO_2026-09-10.md`).
