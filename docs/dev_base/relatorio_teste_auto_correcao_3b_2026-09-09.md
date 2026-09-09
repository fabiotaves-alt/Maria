# RELATÓRIO DE TESTE — Auto-correção genérica do 3B (Qwen2.5-Omni) com harness corrigido

**Data:** 2026-09-09
**Branch:** `chore/registro-teste-auto-correcao-3b`
**Modelo:** `ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M` (Q4_K_M, ~1,96 GB) via `llama-server` local em `127.0.0.1:8080`
**Harness:** `teste_auto_correcao_3b.ps1` (UTF-8 **com BOM** — necessário no PowerShell 5.1)
**Status:** Evidência registrada; reforça D2 do `relatorio_v5_json_tool_calling.md` (2026-09-08)

---

## 1. Objetivo

Registrar de forma reproduzível o teste de **auto-correção por turno extra de revisão** no 3B, agora com o harness corrigido. O cenário reaproveita uma resposta real do 3B que continha o bug de capitalização (`"peso"` minúsculo nas chaves de `linhas` vs coluna `"Peso"` declarada) e testa se o modelo se auto-audita com **instrução genérica** (sem apontar o bug específico).

## 2. Por que o harness precisou ser corrigido

O veredito original usava `-in`/`-notin` do PowerShell, que são **case-insensitive** por padrão:

```powershell
'Peso' -in @('peso','Produto','Preco')   # → True (falso positivo)
'Peso' -cin @('peso','Produto','Preco')  # → False (correto)
```

Ou seja: o script reportaria `CORRIGIU` mesmo com o bug `peso` vs `Peso` ainda presente — **falso positivo de critério**, confirmado empiricamente nesta sessão.

Correções aplicadas no harness versionado:
- Comparação de chaves com `-cnotcontains` (**case-sensitive**).
- Conjunto de referência com as colunas **pedidas pelo usuário** (`Produto`, `Preço`, `Peso`) — valida contra a fonte de verdade original, não apenas contra a consistência interna da resposta (ressalva já apontada no relatório v5).
- Veredito em 3 níveis: `CORRIGIU corretamente` / `AUTO-CONSISTENTE mas DIVERGENTE` / `NAO CORRIGIU`.

## 3. Metodologia

- 4 mensagens: `system` (MARIA) → `user` (pedido de planilha com tradução Mandarim→PT e 5 produtos) → `assistant` (resposta real do 3B **com o bug**) → `user` (instrução genérica de revisão).
- Sampler: `temperature 0.1`, `max_tokens 400`, `repeat_penalty 1.1`, `top_k 40`, `top_p 0.95`, `min_p 0.05`, `dry_multiplier 0.8`, `dry_base 1.75`, `dry_allowed_length 2`, `dry_penalty_last_n 64`, `frequency_penalty 0.0`, `presence_penalty 0.0`.
- 3 execuções (n=3), modelo já carregado no servidor (ctx 2048).

## 4. Resultados

### 4.1 Execuções

| Exec | Latência | finish | tokens | JSON | Veredito |
|---|---|---|---|---|---|
| 1 | ~79,5 s | stop | 173 | válido (5 linhas) | AUTO-CONSISTENTE mas DIVERGENTE |
| 2 | ~37,1 s | stop | 173 | válido (5 linhas) | AUTO-CONSISTENTE mas DIVERGENTE |
| 3 | ~37,2 s | stop | 173 | válido (5 linhas) | AUTO-CONSISTENTE mas DIVERGENTE |

3/3 **determinístico**: mesmo JSON, mesmos 173 tokens nas 3 execuções.

### 4.2 Saída típica (idêntica nas 3 execuções)

```json
{"ferramenta":"criar_planilha","nome_arquivo":"produtos_importados",
 "colunas":["Produto","Preco","peso"],
 "linhas":[
   {"Produto":"Bola","Preco":"r$ 25,00","peso":"0,3 kg"},
   {"Produto":"brinquedo de boneca","Preco":"r$ 45,00","peso":"0,5 kg"},
   {"Produto":"carro de brinquedo","Preco":"r$ 35,00","peso":"0,4 kg"},
   {"Produto":"livro","Preco":"r$ 15,00","peso":"0,2 kg"},
   {"Produto":"caixa de lápis","Preco":"r$ 12,00","peso":"0,15 kg"}]}
```

- Colunas declaradas na saída: `Produto, Preco, peso` (no turno bugado injetado: `Produto, Preco, Peso`).
- Chaves de todas as linhas: `Produto, Preco, peso` → internamente consistentes (`autoOk` verdadeiro).
- **Divergência do pedido:** o usuário pediu `Produto, Preço, Peso`; o modelo **rebaixou a coluna `Peso` → `peso`** e perdeu o acento (`Preço` → `Preco`) em vez de corrigir as chaves das linhas.
- `R$` normalizado para `r$` minúsculo em todas as linhas.

### 4.3 Auditoria de tradução (Mandarim → PT) na saída final

| Mandarim | Saída do 3B | Avaliação |
|---|---|---|
| 球 | Bola | ✅ correta |
| 玩具娃娃 | brinquedo de boneca | ⚠️ aceitável, porém invertida (natural: "boneca (de brinquedo)") |
| 玩具车 | carro de brinquedo | ✅ correta |
| 笔记本 | livro | ❌ **errada** (é caderno/notebook/laptop) |
| 文具盒 | caixa de lápis | ⚠️ aproximação (correto: "estojo (escolar)") |

O turno de revisão **não detectou** a tradução errada (`笔记本` → "livro"): auto-auditoria genérica também não valida semântica dos valores.

## 5. Interpretação

1. A auto-correção por instrução genérica **não corrige** no 3B: ela resolve a inconsistência pela via de menor esforço, alterando a **declaração** (colunas) para casar com o erro nos **dados** (linhas). Reforça D2 do relatório v5 (conserto em código, não por turno extra) e a decisão de que instrução genérica é insegura como mecanismo.
2. **Falso positivo do veredito original confirmado:** o teste anterior só "passava" por causa do operador case-insensitive do PowerShell — não por mérito do modelo.
3. Tradução no 3B dentro do fluxo de ferramenta permanece frágil (`笔记本` → "livro"). Alinhado à pendência **D6** do B4 (nova Task 26 de tradução avaliada por `linhas_esperadas`, com design para não reintroduzir o problema).

## 6. Recomendações

- **Produção:** manter a validação determinística em código (match de chaves e normalização), sem depender de turno extra de auto-revisão do 3B.
- **Se houver turno extra:** apenas **dirigido** (apontando campo/critério exato), nunca instrução genérica; e validar sempre contra a fonte de verdade do pedido.
- **Harness futuro:** veredito contra a referência original + operadores case-sensitive (`-ceq`/`-cin`/`-cnotcontains`).
- **Prompt:** adicionar regras a medir em teste dirigido — "não altere os nomes das colunas pedidas pelo usuário; corrija SEMPRE as linhas" e "traduza pelo termo comercial correto (ex.: 笔记本 = caderno)".

## 7. Reprodução

Pré-requisito: `llama-server` ativo com o modelo carregado (ver `docs/REGRAS_OPERACAO_LLAMA_SERVER.md`).

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File docs/dev_base/teste_auto_correcao_3b.ps1
```

> ⚠️ O arquivo é UTF-8 **com BOM** (necessário para o PowerShell 5.1 ler acentos e mandarim corretamente). Não converter para UTF-8 sem BOM.

## 8. Ressalvas

- n=3 sustenta conclusão binária replicada (determinismo 3/3), não taxas finas.
- Nenhum código de produção alterado; suíte **274 passed inalterada** (docs-only).

