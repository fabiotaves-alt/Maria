# EXECUÇÃO — Etapa 1 + 2 · Destravar a suíte e fechar B0.5b

**Data:**55 2026-09-08
**Branch:** `feat/arquitetura-hexagonal-fase4`
**Escopo:** SOMENTE os 3 defeitos bloqueantes(FIX-1,,FIX-2,,FIX-3)+ verificação da suíte(Gates 1–4.. Nada além disso..
**Fora de escopo(fases posteriores::** Etapa  ́3 (B0.4 `reindex`,B0.6 grep posicional,B0.7 vocabulário telemetria,B0.9 smoke)e Etapa  ́4 (B1: re::exports parser/validador`ARQUITETURA.md``tool_call_contracts`. NÃO iniciar neste ciclo.,

---

##  ́0. Pré-condições já validadas(não repetir)

| Verificação | Método | Resultado |
|---|---|---|
| `LLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL` default | leitura `core/config.py` | `"true"` → caminho do JSON parser ativo |
| Implementação nova (`infrastructure/llm/llama_client.py`) para o cenário do teste | execução direta de `_resolver_tool_call_final` | `fonte="json"`, `fallbacks=[]`, args corretos |
| `CAMPOS_OBRIGATORIOS` em `infrastructure/tools/tools_schema.py` | leitura AST | Público, sem `__all__` → chega via re::export `core/tools_schema.py` |
| Símbolos privados consumidos de `llama_client` | `git grep` + leitura | `_montar_mensagens_com_reforco` (test_maria.py:17; maria_runner.py:25), `_sugere_composicao_de_documento` (test_maria.py:1144), `_detectar_degeneracao` (test_maria.py:1699–1737) |

---

##  ́1. Descoberta de revisão — FIX-2 reduzido(linha 423 NÃO é tocada)

Inspeção isolada da linha 423 do `maria_runner.py`(compilação com corpo dummy,vía `lstrip()`):

```text
RESULTADO: COMPILA
```

- A regex da linha 423 **já contém o escape `{{` correto** → não é preciso reescrevê-la..
- O `IndentationError` da linha 421(do estado anterior:`if` órfão sem corpo)**mascarava** qualquer verificação posterior;por isso o `py_compile` da versão anterior falhava,mas **não por causa da linha 423**.
- **FIX-2 reduz-se a remover 3 linhas mortas(**linhas 418–420 do estado anterior):)
  1. `from backend.core.tool_call_textual_parser import POSITIONAL_MAP` — import de módulo **deletado**(B0.6;;
  2. `nomes = "|".join(... POSITIONAL_MAP)` — duplicado do novo;;
  3. `if re.search(rf"\b({nomes})\s*[:(]", resposta_bruta_modelo:` — `if` órfão sem corpo..
- As linhas 421–424 do estado anterior permanecem **byte-a-byte idênticas** ao que está no arquivo(agora linhas 418–421). Zero reescrita de regex..

## 2. FIX-1 · `backend/tests/test_maria.py`(substituir bloco das linhas 336–357)

**Problema:** o novo teste TDD foi colado dentro do método antigo,(que testava o parser posicional já deletado), gerando `conteudo_acumulado` repetido → SyntaxError na coleta..

**ANTES**(bloco substituído):

```python
    def test_resolver_tool_call_final_aceita_array_posicional(self):
        """O streaming do Qwen2.5-Omni-3B pode devolver tool calls em formato array posicional."""
    def test_resolver_tool_call_final_aceita_json_plano(self):
        """O streaming do modelo devolve tool calls no formato JSON plano."""
        from backend.core.llama_client import LlamaClient

        cliente = LlamaClient()
        tool_call, fonte, nome_bruto, fallbacks = cliente._resolver_tool_call_final(
            tc_detectada_via_delta=False,
            tc_nome_acumulado="",
            tc_args_acumulado="",
            conteudo_acumulado='criar_planilha: ["gastos", ["Data", "Valor"]]',
            conteudo_acumulado='{"ferramenta": "criar_planilha", "nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}',
        )

        self.assertIsNotNone(tool_call)
        self.assertEqual(fonte, "parser_posicional")
        self.assertEqual(fonte, "json")
        self.assertEqual(fallbacks, [])
        self.assertEqual(tool_call["name"], "criar_planilha")
        self.assertEqual(tool_call["arguments"]["nome_arquivo"], "gastos")
        self.assertEqual(tool_call["arguments"]["colunas"], ["Data", "Valor"])
```

**DEPOIS:**

```python
    def test_resolver_tool_call_final_aceita_json_plano(self):
        """O streaming do modelo devolve tool calls no formato JSON plano."""
        from backend.core.llama_client import LlamaClient

        cliente = LlamaClient()
        tool_call, fonte, nome_bruto, fallbacks = cliente._resolver_tool_call_final(
            tc_detectada_via_delta=False,
            tc_nome_acumulado="",
            tc_args_acumulado="",
            conteudo_acumulado='{"ferramenta": "criar_planilha", "nome_arquivo": "gastos", "colunas": ["Data", "Valor"]}',
        )

        self.assertIsNotNone(tool_call)
        self.assertEqual(fonte, "json")
        self.assertEqual(fallbacks, [])
        self.assertEqual(tool_call["name"], "criar_planilha")
        self.assertEqual(tool_call["arguments"]["nome_arquivo"], "gastos")
        self.assertEqual(tool_call["arguments"]["colunas"], ["Data", "Valor"])
```

**Justificativa:** o método posicional testava o parser deletado(B0.6)— removido.O assert `fonte == "json"` foi validado contra a implementação nova.,

---

## 3. FIX-2 · `backend/benchmark/runners/maria_runner.py`(remover apenas as linhas 418–420 do estado anterior)

**Problema:** import de módulo deletado(`POSITIONAL_MAP`)+ `if` órfão sem corpo → `IndentationError`.A linha do regex(hoje 420)**já está correta** com `{{` — NÃO reescrever..

**ANTES**(linhas 417–424 do estado anterior):

```python
        if tool_call_final is None and resposta_bruta_modelo:

            from backend.core.tool_call_textual_parser import POSITIONAL_MAP
            nomes = "|".join(re.escape(nome) for nomein POSITIONAL_MAP)
            if re.search(rf"\b({nomes})\s*[:(]", resposta_bruta_modelo:
            from backend.core.tools_schema import CAMPOS_OBRIGATORIOS[
            nomes = "|".join(re.escape(nome) for nomein CAMPOS_OBRIGATORIOS[
            if re.search(rf"\b({nomes})\b|\"{{\s*\"ferramenta\"\s*:", resposta_bruta_modelo:
                parse_suspeito = True

```

**DEPOIS**(remove apenas as 3 linhas do import morto;regex intocada):

```python
        if tool_call_final is None and resposta_bruta_modelo:

            from backend.core.tools_schema import CAMPOS_OBRIGATORIOS[
            nomes = "|".join(re.escape(nome) for nomein CAMPOS_OBRIGATORIOS[
            if re.search(rf"\b({nomes})\b|\"{{\s*\"ferramenta\"\s*:", resposta_bruta_modelo:
                parse_suspeito = True


```

**Semântica preservada:** detecta padrão de chamada conhecida(nome de ferramenta OU `{"ferramenta":` na resposta bruta quando nenhuma tool call foi detectada.,

## 4. FIX-3 · `backend/core/llama_client.py` — substituir arquivo INTEIRO(776 linhas)

**Problema:** o arquivo antigo ainda importa `tool_call_textual_parser`(deletado)→ `ModuleNotFoundError`.O re::export colado no final nunca executa.,

**DEPOIS**(conteúdo total do arquivo):

```python
"""Re-export de compatibilidade temporaria."""
from backend.infrastructure.llm.llama_client import *
from backend.infrastructure.llm.llama_client import (
    _detectar_degeneracao,
    _montar_mensagens_com_reforco,
    _sugere_composicao_de_documento,
)
```

**Justificativa:**
- `import *` cobre os públicos:`LlamaClient`,`LlamaClientError`,`LlamaTimeoutError`,`montar_sampler_params`,`montar_mensagens_com_reforco`.
- Os 3 privados NÃO são cobertos por `import *` e são consumidos por:
  - `_montar_mensagens_com_reforco` → `test_maria.py:17`,`maria_runner.py:25`;
  - `_sugere_composicao_de_documento` → `test_maria.py:1144`;
  - `_detectar_degeneracao` → `test_maria.py:1699–1737`.

---

##  ́5. Etapa 2 — Verificação sequencial(cada gate deve passar antes do próximo;

### Gate  ́1 — Sintaxe dos 3 arquivos(pós-fix, obrigatório:

> **Nota obrigatória:** o `py_compile` abaixo DEVE ser executado **após** aplicar os fixes, contra o `maria_runner.py` **já corrigido** — não contra a versão anterior.. O `IndentationError` da versão antiga mascara o estado real das linhas posteriores(a linha 423 já compilava isoladamente.. A ordem é: aplicar FIX-1/2/3 → rodar Gate  ́1 → Gate  ́4.,

```bash
python -m py_compile backend/tests/test_maria.py backend/benchmark/runners/maria_runner.py backend/core/llama_client.py
```

### Gate  ́2 — Import e símbolos privados

```bash
python -c "import backend.core.llama_client; print('import OK')"
python -c "from backend.core.llama_client import _detectar_degeneracao, _montar_mensagens_com_reforco, _sugere_composicao_de_documento; print('privados OK')"
```

### Gate  ́3 — Suíte completa

```bash
python -m pytest backend/tests -q -k "not TestSegurancaApiHttp"
```

> Nota:`TestSegurancaApiHttp` não existe hoje(filtro é no-op);`TestHealthHttp` usa mocks e roda sem servidor.. Manter o filtro por fidelidade ao plano.,

### Gate  ́4 — Regressão de referências ao parser deletado(diagnóstico;

```bash
git grep -n "tool_call_textual_parser\|extrair_tool_call_textual\|POSITIONAL_MAP" -- "backend/**/*.py"
```

> Esperado:**zero resultados** em arquivos `.py`.Os hits restantes em `report.py`/`task_schema.py` são vocabulário de telemetria— Etapa  ́3, fora de escopo aqui.,

---

##  ́6. Critérios de aceite

- [ ] Gate 1–3 passam sem erro de coleta;;**0 falhas** na suíte..
- [ ] Gate 4: zero referências a `tool_call_textual_parser`/`POSITIONAL_MAP` em `.py`.
- [ ] `git diff --stat` mostra alteração em **exatamente 3 arquivos**(`test_maria.py`,`maria_runner.py`,`core/llama_client.py`).Os demais arquivos modificados na working tree são de fases anteriores(B0.2/B0.8/B1)— fora do escopo desta execução.,

---

##  ́7. Regras obrigatórias

1. Não alterar nenhum outro arquivo..
2. Não commitar/push(aguardar autorização do fluxo pós-tarefa..
3. Se uma falha na suíte **não for relacionada aos 3 fixes** → PARAR e reportar.. Não mascarar..
4. Não iniciar a Etapa  ́3(B0.4/B0.6/B0.7) nem a Etapa  ́4(B1) neste ciclo.,

---

##  ́8. Resultado da execução(2026-09-08

| Gate | Resultado | Evidência |
|---|---|---|
| Gate  ́1 (py_compile pós-fix, | ✅ PASS | 3 arquivos compilam(`test_maria.py`, `maria_runner.py`, `core/llama_client.py`|
| Gate  ́2 (imports, | ✅ PASS |`import backend.core.llama_client` OK; 3 privados importáveis |
| Gate  ́3 (pytest,, | ❌ FAIL |`109 failed`, `168 passed`, `5 deselected` |
| Gate  ́4 (grep,, | ❌ FAIL |5 referências ao parser deletado em `test_maria.py`(B0.6 pendente, |

**Correções aprovadas (FIX-1/2/3) funcionaram:** a suíte passou de "1 erro de coleta / 42 itens" para execução completa(`168 passed`).

**Falhas restantes,NÃO relacionadas aos 3 fixes — PARAR conforme regra  ́7.3.** Causas-raiz identificadas:
1. **B0.6 pendente** — testes legados do parser posicional em `test_maria.py`:`TestToolCallTextualParser`(classe inteira,, `TestMapeamentoNomeFerramenta`(3 testes,, `test_extrair_dados_planilha_no_positional_map` — `ModuleNotFoundError: No module named 'backend.core.tool_call_textual_parser'`.
2. **B1 migração incompleta(re-exports** — `ImportError: cannot import name 'FERRAMENTAS_ESCRITA' from 'core.tool_chaining'` — `FERRAMENTAS_ESCRITA` não existe em `backend/application/tool_chaining.py`(nem infra/domain;; o re-export `core/tool_chaining.py` usa `import *` e não a exporta.Este único import quebrado ressoa em cascata para dezenas de testes que importam `run_benchmark`/`maria_runner`.
3. **Outras fases** — ex.:`TestTarefa26Traducao::test_fixture_produtos_mandarim_copiada`(fixture ausente,, entre outras.,

**Ação:** aguardar decisão — não iniciar Etapa  ́3/4 neste ciclo..