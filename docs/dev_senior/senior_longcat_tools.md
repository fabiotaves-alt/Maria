# REVISÃO SÊNIOR — `relatório_dev_longcat_tools.md`

**Revisor:** Antigravity (dev sênior)  
**Data:** 2026-09-08  
**Relatório base:** [`relatório_dev_longcat_tools.md`](file:///c:/Users/Sony%20Vaio/Documents/maria/docs/dev_base/relatório_dev_longcat_tools.md)

---

## Veredicto geral

**Relatório VÁLIDO**, mas com uma confusão importante de temporalidade e uma omissão de impacto no diagnóstico do BUG-4.

---

## 1. O que está correto

### ✅ Achado central (regressão do system_prompt.txt) — CONFIRMADO

Verifiquei o `system_prompt.txt` atual em `backend/core/system_prompt.txt`. Ele **de fato está no formato JSON** (`{"ferramenta":"criar_planilha",...}`). O parser (`_tentar_extrair_tool_call_textual`, linha 79 do `llama_client.py`) só reconhece `"name"` + `"arguments"` — não `"ferramenta"`. O fallback posicional (`extrair_tool_call_textual`, linha 409) também não casa. **Conclusão do relatório confirmada empiricamente pelo código.**

### ✅ Evidência do benchmark run_20260907_141158

O diagnóstico de 100% de falha (`tool_detected=None`) está consistente com o código: o modelo gera JSON válido com `"ferramenta"`, o pipeline não extrai nada, resultado é `None`. O relatório identifica a causa raiz correta.

### ✅ Auto-correção dirigida — análise correta

O código em `tool_chaining.py` envia erro específico ao modelo, não uma instrução genérica. A conclusão "mecanismo atual já implementa correção dirigida" está correta.

---

## 2. Defeitos encontrados

### ❌ DEFEITO-1 (Confusão de temporalidade — case sensitivity)

O relatório diz na seção 2.3:

> "O código já implementa normalização de chaves em múltiplos pontos e `NOME_CANONICO` para mapeamento de variantes. **Conclusão:** O bug de case sensitivity já está mitigado."

**Isso é parcialmente falso como mitigação do BUG-2.** O `{k.lower(): v}` normaliza **todas** as chaves dos argumentos — incluindo as chaves internas de `linhas`. O `relatorio_v5` identifica exatamente isso como **BUG-4**: normalizar `"English Description"` → `"english description"` diverge da coluna real no DataFrame. A "mitigação" existente destrói dados de `linhas`.

**Correção:** o bug de case sensitivity **não está mitigado** para chaves de `linhas`. Está mitigado apenas para chaves de controle de nível superior.

### ❌ DEFEITO-2 (Tabela de ações — linha "Bug case sensitivity no 3B")

> | Bug case sensitivity no 3B | ✅ Documentado | ✅ Já mitigado (lowercase) | Manter atual | 🟢 Nenhum |

Status errado. Deveria ser ❌ (mitigação parcial / destrutiva para `linhas`). Ação: implementar V3 do `relatorio_v5` (normalização somente de chaves de controle).

---

## 3. Omissões

### ⚠️ OMISSÃO-1 (BUG-5 implícito não capturado)

Propõe adicionar exemplo com `linhas` ao prompt — correto. Mas não menciona que `validar_argumentos_obrigatorios` não valida `linhas`. Resolver o prompt resolve o modelo não preencher o campo; não resolve o pipeline aceitar `linhas` malformadas silenciosamente.

### ⚠️ OMISSÃO-2 (Recomendação desatualizada pela D1)

Recomendação 4.1: restaurar `system_prompt.txt` para formato posicional. Isso foi superado pela decisão D1 aprovada na sessão seguinte (remover parser posicional, implementar parser JSON plano). O relatório não sabia das decisões D1–D6 — cronologicamente justificado, mas precisa ser explicitado ao usar o relatório como referência.

---

## 4. Oportunidades não capturadas

| ID | Oportunidade |
|----|-------------|
| O-A | Adicionar 1 exemplo com `linhas` preenchidas é o item de maior ROI — 6/6 acertos vs 0/6 sem exemplo (evidência do `relatorio_v5`). |
| O-B | `_montar_mensagens_com_reforco` não injeta few-shot dinâmico. Com histórico longo, o exemplo de `linhas` fica soterrado no system prompt. |
| O-C | Nenhuma métrica proposta para quantificar o impacto da regressão. `compare_runs` entre run pré-regressão e `20260907_141158` daria o custo em `tool_accuracy`. |

---

## 5. Ações derivadas

| Ação | Prioridade | Fase |
|------|-----------|------|
| Implementar parser JSON plano (BUG-1 do `relatorio_v5`) — **não** restaurar posicional | 🔴 CRÍTICA | B0 |
| Corrigir normalização: somente chaves de controle, não chaves de `linhas` (BUG-4) | 🔴 CRÍTICA | B0 |
| Adicionar exemplo com `linhas` ao `system_prompt.txt` v4 | 🟡 ALTA | B0 |
| Adicionar validação de `linhas` em `validar_argumentos_obrigatorios` (BUG-5) | 🟡 ALTA | B0 |

---

**Conclusão:** Relatório base válido na causa raiz. Erro principal: tratar lowercase como mitigação suficiente do case-sensitivity em `linhas` — é, na verdade, parte do problema (BUG-4). Recomendação de restaurar prompt posicional foi ultrapassada pelas decisões D1 posteriores.
