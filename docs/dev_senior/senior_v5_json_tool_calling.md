# REVISÃO SÊNIOR — `relatorio_v5_json_tool_calling.md`

**Revisor:** Antigravity (dev sênior)  
**Data:** 2026-09-08  
**Relatório base:** [`relatorio_v5_json_tool_calling.md`](file:///c:/Users/Sony%20Vaio/Documents/maria/docs/dev_base/relatorio_v5_json_tool_calling.md)

---

## Veredicto geral

**O mais completo e rigoroso dos três relatórios.** Bugs e inconsistências confirmados pelo código. Plano de fases B0–B7 coerente e bem sequenciado. Três pontos merecem atenção: um risco subestimado, uma lacuna de especificação no T2 e uma inconsistência no escopo de V3 vs BUG-4.

---

## 1. Confirmação dos bugs por código

| Bug/Incons. | Confirmado? | Evidência no código |
|-------------|-------------|---------------------|
| BUG-1: sem parser para `"ferramenta"` | ✅ SIM | `llama_client.py:79` exige `"name"` + `"arguments"`; linha 409 chama parser posicional. `"ferramenta"` não tem handler em nenhum dos dois caminhos. |
| BUG-2: `pd.DataFrame(linhas, columns=colunas)` case-sensitive | ✅ SIM | `excel_handler.py:117`: `df = pd.DataFrame(linhas_dados, columns=colunas)`. Não há normalização antes da construção do DataFrame. |
| BUG-3: `reindex` descarta chaves extras silenciosamente | ✅ SIM | `excel_handler.py:118`: `df = df.reindex(columns=colunas)` sem log ou telemetria de descarte. |
| BUG-4: `{k.lower()}` destrói chaves de `linhas` | ✅ SIM | `llama_client.py:100` (dentro de `_tentar_extrair_tool_call_textual`) e `:395` (no resolver): normalização flat de **todos** os argumentos, sem exceção para `linhas`. |
| BUG-5: `validar_argumentos_obrigatorios` ignora `linhas` | ✅ SIM | Verificado via busca — nenhum validador de tipo ou item em `linhas` antes da chamada ao handler. |
| INCONS-1: benchmark não avalia `linhas` | ✅ SIM | `_argumentos_compativeis` verifica não-vazio de coluna, não conteúdo das linhas. |
| INCONS-3: vocabulário de telemetria acoplado ao posicional | ✅ SIM | `tool_call_fonte` inclui `parser_posicional` como valor válido; será vocabulário morto após D1. |

**Todos os 7 pontos confirmados.**

---

## 2. Defeitos no relatório

### ❌ DEFEITO-1 (V3 e BUG-4 especificados de forma conflitante)

A seção 5, V3 diz:

> "Chaves de `linhas` × `colunas` case-insensitive — **REPARO**: Renomeia `"peso"` → `"Peso"` quando único match case-insensitive."

A seção 3, BUG-4 diz:

> "Correção: normalizar somente chaves de controle; chaves internas de `linhas` são **dados**, jamais normalizadas."

**Contradição:** V3 quer renomear chaves de `linhas` para bater com `colunas`. BUG-4 diz que chaves de `linhas` são dados e não devem ser tocadas. Ambos estão certos em seus domínios, mas a especificação do V3 não deixa claro que a normalização acontece **dentro do validador determinístico** (pós-parser), não **dentro do parser** (onde BUG-4 ocorre). A distinção de onde cada operação acontece é crítica e está ausente.

**Correção:** especificar explicitamente que:
- Parser (T4): normaliza somente chaves de controle de nível 1 (`ferramenta`, `nome_arquivo`, etc.) → sem tocar `linhas[*]`.
- Validador V3: recebe `linhas` já com chaves originais e faz correspondência case-insensitive contra `colunas`, renomeando no dict antes de passar ao DataFrame.

São dois módulos distintos com responsabilidades distintas.

### ❌ DEFEITO-2 (T2 subespecificado — ambiguidade no "scan balanceado")

Seção 4, nível T2:

> "Scan balanceado de `{...}` (respeitando strings) para extrair o primeiro objeto JSON; aceitar também `{"name":..., "arguments":...}` nativo."

"Respeitando strings" é uma especificação incompleta para implementação. O scan balanceado precisa cobrir:
1. Aspas escapadas (`\"`) dentro de strings.
2. Chaves dentro de valores string (`{"key": "valor com { chave }"}`).
3. Arrays aninhados com objetos (`{"linhas": [{"A": 1}]}`).

Sem essa especificação, a implementação vai divergir entre diferentes desenvolvedores/IAs. Recomendo referenciar `json.JSONDecoder.raw_decode` como estratégia alternativa ao scan manual (evita reimplementar um mini-parser de JSON).

---

## 3. Omissões

### ⚠️ OMISSÃO-1 (Critério de aceite do B0 não inclui `linhas` com dados reais)

O critério de aceite do B0:

> "0 execuções com coluna silenciosamente vazia na nova Task 26"

Isso cobre apenas `linhas` no contexto da Task 26. Não especifica como verificar que colunas com dados reais do 3B (que usa strings formatadas como `"R$ 25,00"`) não são descartadas. Recomendo adicionar: task de smoke com 3B gerando `linhas` com preços em string e verificar que a coluna **tem dados** (mesmo que seja string, não NaN).

### ⚠️ OMISSÃO-2 (Risco 1 subestimado — "mais exposto a crases/texto ao redor")

O risco 1 na seção 9:

> "Mais exposto a crases/texto ao redor que o posicional com whitelist — mitigado por T1–T3."

O T1 (strip de cercas) é robusto. O T2 (scan balanceado) depende da qualidade da implementação (ver DEFEITO-2). O risco real mais alto é o **T3 (reparo de truncamento)**: um `finish_reason=length` no meio de um dict de `linhas` pode produzir um objeto JSON válido mas com dados truncados (ex: `linhas` com 3 itens de 5), sem qualquer sinal de erro visível ao usuário. Isso é **pior** que uma falha total: o arquivo é criado com dados incompletos e nenhum warning explícito na UI.

**Recomendação:** quando `json_reparado=True` em `linhas`, propagar aviso visível na resposta ao usuário ("Dados truncados por limite de contexto — apenas N linhas escritas") além de telemetrar.

### ⚠️ OMISSÃO-3 (O1 — geração automática de schema sem tratamento de ferramentas sem `linhas`)**

A oportunidade O1 (gerar `json_schema` do `response_format` a partir de `TOOLS_SCHEMA`) é válida. Mas não trata o caso de ferramentas que não têm `linhas` no schema (ex: `criar_documento`). O schema gerado para o `response_format` do benchmark precisa ser por ferramenta específica, não um schema global — ou terá campos opcionais que o modelo vai preencher desnecessariamente (alucinação estrutural).

---

## 4. Oportunidades adicionais

| ID | Oportunidade |
|----|-------------|
| O-X1 | **Schema de validação como fonte única de verdade:** gerar tanto o prompt (seção "Ferramentas disponíveis" + exemplos) quanto o `response_format` schema automaticamente de `TOOLS_SCHEMA`. Elimina a trilogia prompt/validação/schema que deriva facilmente. |
| O-X2 | **Telemetria diferencial 3B×7B:** o benchmark grava resultados mas não agrupa automaticamente por modelo. Um `GROUP BY modelo, tool_name` no SQL do B3 mostraria quais ferramentas têm gap de qualidade entre modelos — dado direto para decisão de V6 (coerção numérica). |
| O-X3 | **`parse_suspeito` como alarme de mismatch formato/parser:** se o prompt instrui JSON plano e `parse_suspeito=True` aumenta, é sinal de que o modelo está gerando outro formato. Pode detectar regressões de prompt automaticamente. |

---

## 5. Sequência B0 — itens que precisam de ordem explícita

O B0 tem 5 entregáveis sem ordem definida. A ordem importa:

```
1. Escrever testes de falha para BUG-1/BUG-2/BUG-4/BUG-5 (TDD)
2. Implementar tool_call_json_parser.py (T1→T4)  [resolve BUG-1]
3. Implementar validacao_tool_call.py (V1→V5,V7)  [resolve BUG-2/3/5]
4. Corrigir normalização no parser (só chaves de controle)  [resolve BUG-4]
5. system_prompt.txt v4 (JSON plano + exemplo linhas + regra condicional)
6. Deletar tool_call_textual_parser.py + POSITIONAL_MAP + testes associados  [D1]
7. Atualizar vocabulário de telemetria  [INCONS-3]
8. Rodar suíte completa → 100% verde
9. Smoke test manual (B0 critério de aceite)
```

Deletar o parser posicional (passo 6) **antes** de implementar o JSON parser (passo 2) produz estado quebrado entre commits. A ordem TDD-first (passo 1 antes de tudo) garante que o critério de aceite já existe antes da implementação.

---

## 6. Resumo de ações derivadas

| Ação | Tipo | Prioridade |
|------|------|-----------|
| Clarificar na especificação onde V3 e BUG-4 atuam (parser vs validador) | Corrigir especificação | 🔴 Antes de implementar B0 |
| Especificar T2 usando `json.JSONDecoder.raw_decode` | Corrigir especificação | 🔴 Antes de implementar B0 |
| Adicionar aviso de dados truncados ao usuário quando `json_reparado=True` em `linhas` | Nova funcionalidade | 🟡 B0 ou B4 |
| Schema de `response_format` por ferramenta específica (não global) | Corrigir O1 | 🟡 B6 |
| Smoke test com 3B + `linhas` com valores numéricos como string | Adicionar critério aceite | 🟡 B0.5 |
| Definir ordem dos passos do B0 explicitamente | Processo | 🟡 Antes de iniciar B0 |
| `GROUP BY modelo` no report SQL | Nova métrica | 🟢 B3 |
| `parse_suspeito` como alarme de mismatch | Nova métrica | 🟢 B3 |

---

**Conclusão:** Relatório tecnicamente sólido. Os dois defeitos são de especificação (não de decisão): V3 vs BUG-4 precisam de separação de camada explícita, e T2 precisa de referência de implementação concreta. O risco de T3 (reparo silencioso de `linhas` truncadas) é o único ponto onde o impacto no usuário final foi subestimado.
