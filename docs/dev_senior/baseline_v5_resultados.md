# Baseline v5 — Resultados do Benchmark (Fase B0.5)

> Captura do estado pré-v5 para servir de referência comparativa quando B3
> (`compare_runs` via SQLite) estiver pronto. Sem análise de correção aqui —
> apenas preservação do artefato e leitura dos números.

**Data:** 2026-09-08
**Escopo:** 28 tarefas × 2 repetições (56 execuções) por modelo, com B0 verde.
**Sampler:** temperature 0.1, top_k 40, top_p 0.95, DRY 0.8, repeat_penalty 1.1 (defaults).

## Artefatos

| Modelo | Pasta | report.md | log.json |
|---|---|---|---|
| Qwen2.5-Omni **3B** (Q4_K_M) | `backend/benchmark/results/run_baseline_v5_3b/` | ✅ | ✅ |
| Qwen2.5-Omni **7B** (Q4_K_M) | `backend/benchmark/results/run_baseline_v5_7b/` | ✅ | ✅ |

> Ambos versionados no repositório (convenção do projeto: `report.md` + `log.json`
> são rastreados; `arquivos_gerados` é ignorado).

## Comparativo geral

| Métrica | 3B | 7B | Δ |
|---|---:|---:|---|
| Acurácia de tool calling | 82,1% | **96,4%** | +14,3 pp |
| Taxa de confirmação (todas) | 94,6% | **100,0%** | +5,4 pp |
| Taxa de execução (runtime) | 96,4% | 96,4% | = |
| Acurácia de argumentos | 94,6% | **96,4%** | +1,8 pp |
| Qualidade semântica | **96,4%** | 94,6% | −1,8 pp |
| Conformidade de idioma | 100% | 100% | = |
| Latência média | **14,5 s** | 31,2 s | ~2,2× |
| Latência p50 / p90 | 9,3 s / 32,6 s | 22,4 s / 57,0 s | — |
| Tokens/s | **3,5** | 1,6 | ~2,2× |
| TTFT (1º token) | **3,6 s** | 6,2 s | — |
| Suspeitas de falha de parser | 20 | 20 | = |

## Por categoria (acurácia de tool calling)

| Categoria | 3B | 7B |
|---|---:|---:|
| ambiguidade | 100% | 100% |
| cancelamento | 100% | 100% |
| confirmacao | 75% | **100%** |
| conversa | 87,5% | **100%** |
| criar_documento | **60%** | **100%** |
| criar_planilha | 83,3% | 83,3% |
| editar_planilha | 83,3% | **100%** |

## Achados principais

1. **7B domina em precisão, a ~2,2× da latência do 3B.** O 7B errou somente a
   Task 26; o 3B perde pontos em `criar_documento`, `confirmacao` e `conversa`.

2. **Task 26 (tradução Mandarim→Inglês) é o ponto cego comum.** Ambos chamaram
   `editar_planilha` quando o esperado era `criar_planilha` (com `args=DIVERGENTE`).
   É o `limite_conhecido` previsto — valida a motivação da **B4** (Task 26
   redesenhada) e da **B4.6** (roteamento para NLLB-200).

3. **Falha sistemática do 3B em `criar_documento`.** Erro repetido
   `campo(s) obrigatório(s) ausente(s): conteudo` (Tasks 8, 10, 15, 17, 20) —
   o 3B gera o JSON sem o campo `conteudo`, ou com chave camelCase
   (`criarDocumento`, fora da whitelist). O 7B não apresenta esse padrão.

4. **`Suspeitas de falha de parser = 20` idêntico nos dois modelos**
   (20/56 = ~35,7% das execuções). Sinal relevante para o alarme `parse_suspeito`
   de **B3** — investigar se é artefato do vocabulário de telemetria ou falha real.

5. **RAM:** o `REGRAS_OPERACAO_LLAMA_SERVER.md` previa OOM no 7B Q4_K_M, mas o
   modelo **carregou e rodou** nesta máquina (0,56 GB livres; compressão/swap).
   A premissa daquele documento precisa ser revisada.

6. **Divergência de contexto (não crítico):** `LLAMA_NUM_CTX` = 4096 no config,
   mas o servidor subiu com `n_ctx=2048` (contexto efetivo 2048). Alinhar quando
   conveniente.

## Implicações para o plano mestre

- **B4 (Task 26)** e **B4.6 (NLLB-200)** seguem justificadas pelos dados.
- **B4.5 (intent/entity)** pode atacar o caso `criar_documento` do 3B via
  pré-processamento de entidades (extrair `conteudo` da mensagem).
- **B3** deve transformar `parse_suspeito` (20/56) em alarme visível no report.
