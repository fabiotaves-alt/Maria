# RELATÓRIO DE ANÁLISE TÉCNICA — Validação na Literatura: Achados dos Testes de Tool Calling

**Data:** 2026-09-07  
**Analista:** Cline (modo Plan → Act)  
**Escopo:** Análise detalhada da possibilidade de mudanças na estrutura do MARIA com base no relatório de validação da literatura de 2026 sobre few-shot prompting, self-correction, tool calling sem suporte nativo e limitações de SLMs 3B-7B.

---

## 🔴 RESUMO EXECUTIVO — ACHADO CRÍTICO

**O `backend/core/system_prompt.txt` na working tree atual está em um estado de REGRESSÃO que quebra o parser de tool calling e invalida múltiplos testes.** A versão atual (hash `2114d558f868`) usa formato JSON (`{"ferramenta":...}`) que o parser não suporta, e removeu seções críticas que existiam na versão commitada (HEAD, hash `222d0cafc974`).

**Evidência empírica:** O benchmark `run_20260907_141158` (7B Q4_K_M) com o prompt JSON mostra **todas as 9 execuções (tasks 5, 10, 13) com `tool_detected=None`** — o modelo gera JSON válido mas o parser não extrai.

---

## 1. ANÁLISE DO SYSTEM_PROMPT.txt — REGRESSÃO IDENTIFICADA

### 1.1 Estado Atual (Working Tree)

O arquivo `backend/core/system_prompt.txt` na working tree contém:
- Formato JSON: `{"ferramenta":"criar_planilha","nome_arquivo":"...","colunas":["..."]}`
- Apenas 2 exemplos simples (sem linhas preenchidas)
- Seções: "Ferramentas disponíveis", "Regras", "Exemplos"
- **AUSENTE:** seção "Extrair dados de planilha existente" / "Fluxo para transformar dados"
- **AUSENTE:** seção "Correção de erro"
- **AUSENTE:** seção "Quando NÃO chamar ferramenta"

### 1.2 Estado Commitado (HEAD — versão funcional)

O `git show HEAD:backend/core/system_prompt.txt` revela a versão commitada com:
- Formato posicional: `criar_planilha: ["nome_arquivo", ["Coluna1", "Coluna2"]]`
- Seção "## Extrair dados de planilha existente" com fluxo completo de paginação
- Seção "## Quando NÃO chamar ferramenta" com 5 regras
- Seção "## Correção de erro" com instrução de corrigir SOMENTE o campo apontado
- Seção "## Conteúdo de documento"

### 1.3 Diferenças-Chave (diff)

| Aspecto | HEAD (commitado) | Working Tree (atual) |
|---------|------------------|----------------------|
| Formato de tool call | Posicional (`criar_planilha: [...]`) | JSON (`{"ferramenta":...}`) |
| Parser compatível | ✅ Sim (extrair_tool_call_textual) | ❌ Não (formato não suportado) |
| Seção "Extrair dados" | ✅ Presente | ❌ Removida |
| Seção "Correção de erro" | ✅ Presente | ❌ Removida |
| Seção "Quando NÃO chamar" | ✅ Presente (5 regras) | ❌ Removida (substituída por "Regras" simplificadas) |
| Exemplos com `linhas` | ❌ Não presente | ❌ Não presente |
| Testes passando | ✅ 240/240 | ❌ 234/240 (1 falha de system prompt + 5 flask) |

### 1.4 Impacto no Parser

O parser (`tool_call_textual_parser.py`) suporta 3 formatos:
1. **Nativo (delta):** `tool_calls` no response da API — não usado pelo llama-server local
2. **Fallback JSON:** `{"name": "...", "arguments": {...}}` — verifica chaves `"name"` e `"arguments"`
3. **Posicional:** `criar_planilha: ["arg1", "arg2"]` — formato principal do Qwen 3B

O formato JSON do prompt atual (`{"ferramenta":...}`) **não corresponde a nenhum dos 3 padrões** — a chave `"ferramenta"` não é `"name"`, e não há `"arguments"`.

**Evidência do log (run_20260907_141158):**
```
Task 5: raw = ```json\n{"ferramenta":"criar_planilha","nome_arquivo":"estoque",...}\n```
         → tool_detected = None (parser não extrai)
```

---

## 2. ANÁLISE POR DIMENSÃO DO RELATÓRIO DE VALIDAÇÃO

### 2.1 Seção 7: Few-Shot Example > Instrução Abstrata

**Achado do relatório:** "O prompt v2 tinha só 1 exemplo de criar_planilha, e esse exemplo não mostrava linhas preenchida — apesar da regra em prosa descrever o campo."

**Análise do código:**

O `system_prompt.txt` atual tem apenas 2 exemplos:
1. `criar_planilha` com `colunas` (sem `linhas`)
2. `criar_documento` com `titulo` e `conteudo` (sem `linhas`)

**Nenhum exemplo demonstra o parâmetro `linhas`** (lista de dicts para preencher dados).

A função `_montar_mensagens_com_reforco` (llama_client.py:144-161) é minimalista:
```python
def _montar_mensagens_com_reforco(historico, mensagem_usuario):
    mensagens = list(historico or [])
    if not mensagens or mensagens[0].get("role") != "system":
        mensagens.insert(0, {"role": "system", "content": MARIA_SYSTEM_PROMPT})
### 2.2 Seção 8: Self-Correction Genérico Não Funciona

**Achado do relatório:** "Instrução de revisão genérica não funciona como mecanismo de auto-correção confiável no 3B."

**Análise do código:**

O mecanismo atual é `validar_e_corrigir_tool_call_stream` (tool_chaining.py:137-214):
```python
feedback = f"Erro na chamada da ferramenta: {erro}"
for chunk, tool_chunk in cliente.continuar_com_resultado_ferramenta_stream(
    historico=historico_com_system,
    tool_call=tool_call_atual,
    resultado=feedback,  # ← erro específico, não genérico
    tools=tools,
    temperatura_override=LLAMA_TEMPERATURE_TOOLS_RETRY,  # 0.25
):
```

**O mecanismo atual NÃO é genérico** — ele envia o erro específico da validação ao modelo, não "revise sua resposta".

**Conclusão:** O relatório está parcialmente correto. O mecanismo atual já implementa correção dirigida por campo (alinhado com CyberCorrect da literatura).

**Ação necessária:** Manter mecanismo atual.

### 2.3 Seção 7: Bug de Case Sensitivity no 3B

O código já implementa normalização de chaves em múltiplos pontos (`{k.lower(): v for k, v in argumentos.items()}`) e `NOME_CANONICO` para mapeamento de variantes.

**Conclusão:** O bug de case sensitivity já está mitigado no código atual.

**Ação necessária:** Manter normalização atual.

### 2.4 Seção 7: Tradução Falha = Limite de Capacidade

A Task 26 usa fixture real `produtos_mandarim.xlsx`. O modelo 3B vai direto para `criar_planilha` sem chamar `extrair_dados_planilha`, resultando em `dados_arquivo_validos = False`.

## 3. SÍNTESE FINAL — TABELA DE AÇÕES

| Achado do Relatório | Validação | Estado no Código | Ação Recomendada | Risco |
|---------------------|-----------|------------------|------------------|-------|
| Few-shot > instrução abstrata | ✅ Confirmado | ❌ Sem exemplo com `linhas` | Adicionar exemplo com `linhas` | 🟢 Baixo |
| Self-correction genérico não funciona | ✅ Confirmado | ✅ Já implementado (erro específico) | Manter atual | 🟢 Nenhum |
| Bug case sensitivity no 3B | ✅ Documentado | ✅ Já mitigado (lowercase) | Manter atual | 🟢 Nenhum |
| Tradução falha = limite | ✅ Confirmado | ❌ Não corrigível | Aceitar como limite | 🔴 Nenhum |
| Tool calling sem suporte nativo | ✅ Padrão da indústria | ✅ Já implementado | Manter atual | 🟢 Nenhum |
| Task 26: modelo narra em prosa | ❌ **INCORRETO** | Dados mostram oposto | Investigar versão do teste | 🟡 Médio |

---

## 4. RECOMENDAÇÕES PRIORITÁRIAS

### 4.1 URGENTE: Restaurar system_prompt.txt

O `system_prompt.txt` na working tree está em estado de regressão. Recomendo:

1. **Restaurar a versão HEAD** (formato posicional com todas as seções)
2. **Adicionar 1 exemplo com `linhas` preenchidas** (few-shot para dados)
3. **Manter seções "Extrair dados", "Correção de erro", "Quando NÃO chamar"**

### 4.2 Adicionar Exemplo com `linhas`

Exemplo a adicionar ao `system_prompt.txt`:
```
Usuário: "Crie planilha de gastos com 2 gastos: Data=2026-01-01, Valor=100; Data=2026-01-02, Valor=200"
MARIA:
criar_planilha: ["gastos", ["Data", "Valor"], [{"Data":"2026-01-01","Valor":100},{"Data":"2026-01-02","Valor":200}]]
```

### 4.3 Investigar Discrepância da Task 26

O diagnóstico da Seção 6 do relatório **não corresponde aos dados empíricos**. Recomendo:
1. Identificar qual versão do system prompt foi usada no teste do relatório
2. Identificar qual modelo (3B vs 7B) foi testado
3. Re-executar o benchmark com a versão atual para comparar

### 4.4 Manter Mecanismos Atuais

Os seguintes mecanismos já estão alinhados com a literatura e devem ser mantidos:
- `validar_e_corrigir_tool_call_stream` (correção dirigida por campo)
- `continuar_com_resultado_ferramenta_stream` (role: tool + tool_call_id)
- `encadear_leitura_stream` (loop de leitura → escrita)
- Normalização de chaves para lowercase
- `NOME_CANONICO` para mapeamento de variantes

---

## 5. CONCLUSÃO

O relatório de validação da literatura de 2026 está **tecnicamente sólido em 5 dos 6 pontos analisados**. A exceção é a Seção 6 (diagnóstico da Task 26), cujo diagnóstico **não corresponde aos dados empíricos** do benchmark atual — o modelo 3B não chama `extrair_dados_planilha`, indo direto para `criar_planilha`.

**O achado mais crítico desta análise** é que o `backend/core/system_prompt.txt` na working tree está em estado de **regressão** que:
1. Quebra o parser de tool calling (formato JSON não suportado)
2. Removeu seções críticas (Extrair dados, Correção de erro, Quando NÃO chamar)
3. Causou 1 falha de teste (`test_system_prompt_contem_excecao_para_arquivo_ficticio`)
4. Causou 100% de falha no benchmark `run_20260907_141158` (9/9 execuções com `tool_detected=None`)

**Recomendação imediata:** Restaurar o `system_prompt.txt` para a versão HEAD (formato posicional) e adicionar 1 exemplo com `linhas` preenchidas. Esta mudança é de BAIXO risco e ALTO impacto.

---

**Fim do relatório.**
