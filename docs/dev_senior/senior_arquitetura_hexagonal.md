# REVISÃO SÊNIOR — `relatorio_arquitetura_hexagonal`

**Revisor:** Antigravity (dev sênior)  
**Data:** 2026-09-08  
**Relatório base:** [`relatorio_arquitetura_hexagonal`](file:///c:/Users/Sony%20Vaio/Documents/maria/docs/dev_base/relatorio_arquitetura_hexagonal)

---

## Veredicto geral

**Relatório SÓLIDO e tecnicamente preciso** nas análises de estado atual e mapeamento de dependências. Problema principal: cronograma ainda otimista mesmo após a revisão (20-30h), e dois pontos arquiteturais críticos não foram tratados.

---

## 1. O que está correto

### ✅ Mapeamento de estado atual (~40% hexagonal já implementado)

Correto. `LLMClientProtocol`, `ToolExecutorProtocol`, `SessionStorageProtocol` existem. `MariaController` já usa injeção de dependência. `database/` já é separado de `core/`. A análise "não precisamos partir do zero" está fundamentada.

### ✅ Acoplamento do benchmark — identificado corretamente

Imports diretos de símbolos privados (`_montar_mensagens_com_reforco`, `TOOLS_SCHEMA`, `executar_ferramenta_real`) confirmados no `relatorio_v5` como INCONSISTÊNCIA-4. A recomendação de tratar benchmark como consumer externo está alinhada com D4.

### ✅ system_prompt.txt como bloqueador da migração

Corretamente marcado como "Crítico" na tabela de riscos. A falha é real e foi confirmada: formato JSON no prompt quebra 100% das execuções do benchmark.

### ✅ Revisão de cronograma (12-18h → 20-30h)

A justificativa é sólida: testes com `@patch` e caminhos antigos são o maior custo oculto. O novo `relatorio_v5` acrescentou estimativa separada de 40-55h para o plano B0-B7 completo — consistente com a revisão deste relatório.

---

## 2. Defeitos encontrados

### ❌ DEFEITO-1 (Fase 0 equivocada — restaurar prompt posicional)

Fase 0, item 1:

> "Corrigir `system_prompt.txt` (restaurar formato posicional)"

**Isso contraria a decisão D1 aprovada** no `relatorio_v5`: remoção total do formato posicional. Restaurar o posicional seria um passo na direção errada. A Fase 0 correta é:

1. Implementar o parser JSON plano (`tool_call_json_parser.py`, T1–T4).  
2. Escrever o `system_prompt.txt` v4 com formato JSON plano e exemplo com `linhas`.

Restaurar posicional e depois remover posicional = trabalho duplo.

### ❌ DEFEITO-2 (Fase 6 — Schemas Pydantic sem base no plano aprovado)

A proposta cria `schemas/tool_calls.py` e `schemas/health.py` com Pydantic. Isso **não aparece nas decisões D1–D6 aprovadas**. O plano aprovado usa SQLite + `BenchmarkConfig` injetável, não Pydantic schemas de requests. Risco de escopo desnecessário antes de validar a base hexagonal.

**Recomendação:** adiar Fase 6 até que as Fases 1-5 estejam consolidadas e haja demanda clara (ex: FastAPI com validação de requests).

---

## 3. Omissões

### ⚠️ OMISSÃO-1 (Não trata `tool_call_json_parser.py` como novo módulo de infrastructure)

O mapeamento de migração lista `tool_call_textual_parser.py` para `infrastructure/tools/`. Mas o plano B0 cria `core/tool_call_json_parser.py` como **substituto**. O relatório de arquitetura precisa refletir que:

- `tool_call_textual_parser.py` → **deletado** (D1), não movido.
- `tool_call_json_parser.py` → criado em `infrastructure/tools/` ou `core/` (a definir).

### ⚠️ OMISSÃO-2 (Regra de dependências entre camadas não documentada operacionalmente)

O relatório menciona "seguir regra de dependência" na tabela de riscos mas não define a regra explicitamente. Para um projeto com múltiplos colaboradores (human + AI), a regra deve ser expressa como uma invariante verificável:

```
domain/ → sem imports de application/, infrastructure/, benchmark/
application/ → pode importar domain/ e interfaces/
infrastructure/ → pode importar domain/ e interfaces/; nunca application/
benchmark/ → importa somente via ports/ (interfaces públicas)
```

Sem isso documentado, a regressão de acoplamento é inevitável ao longo do tempo.

### ⚠️ OMISSÃO-3 (Sem critério de aceite por fase)

O `relatorio_v5` tem critérios de aceite por fase (B0: suíte 100% verde + smoke test; B2: grep limpo; etc.). O relatório hexagonal não tem. Cada fase deve ter um critério de aceitação binário (passou/não passou) antes de avançar.

---

## 4. Oportunidades não capturadas

| ID | Oportunidade |
|----|-------------|
| O-A | `grep -r "core\." backend/benchmark/` como critério de aceite do B2 — já sugerido implicitamente mas não formalizado. |
| O-B | `validacao_tool_call.py` (camada determinística V1–V8) é um novo módulo que não aparece no mapeamento hexagonal. Deve ser classificado como `domain/` (lógica pura) ou `application/` (orquestração de validação). |
| O-C | O `BenchmarkConfig` injetável (D4) é a interface de configuração que substitui o efeito colateral de `core/config.py`. Deveria aparecer no mapeamento como `interfaces/benchmark_config.py`. |

---

## 5. Correções ao plano de fases

| Fase | Problema | Correção |
|------|---------|---------|
| Fase 0 | "Restaurar formato posicional" | Substituir por: implementar parser JSON + system_prompt v4 |
| Fase 4 | `tool_call_textual_parser.py` → `infrastructure/tools/` | Corrigir: **deletar** (D1), não mover |
| Fase 4 | Não inclui `tool_call_json_parser.py` | Adicionar: criar em `infrastructure/tools/` |
| Fase 4 | Não inclui `validacao_tool_call.py` | Adicionar: criar em `domain/` ou `application/` |
| Fase 6 | Schemas Pydantic sem demanda identificada | Mover para backlog pós-hexagonal |

---

**Conclusão:** Relatório de arquitetura é o mais técnico dos três e o mais reutilizável. Os dois defeitos principais são tratáveis com substituição da Fase 0 e remoção da Fase 6 do escopo imediato. A omissão da regra de dependência documentada é o risco arquitetural de prazo mais longo.
