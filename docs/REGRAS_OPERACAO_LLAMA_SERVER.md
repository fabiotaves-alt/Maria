# Regras de Operação — llama-server (MARIA)

> Regras obrigatórias antes de iniciar ou testar o `llama-server` local. Atualizado após os Testes A/B de 2026-09-06.

## Ambiente de referência
- Build **CPU-only**: `llama-b10717-bin-win-cpu-x64`.
- Binário: `C:\Users\Sony Vaio\documents\llama_cpp\llama-b10717-bin-win-cpu-x64\llama-server.exe`.
- **RAM total: ~7,9 GB** (livre típico ~4,3 GB) — fator limitante para o 7B.

## IDs de modelo aceitos pela API (build b10717)
A API HTTP **não** aceita apelidos curtos (`qwen2.5-omni-3b` → `400 model not found`). Usar sempre o **ID completo**:

| Chave interna (projeto) | ID real para a API |
|---|---|
| `qwen2.5-omni-3b` | `ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M` |
| `qwen2.5-omni-7b` | `ggml-org/Qwen2.5-Omni-7B-GGUF:Q4_K_M` |

> Mapeamento interno em `backend/benchmarks/maria_bench/servidor_llama.py` (`MODELOS_HF`).

## Tamanho dos GGUF em cache (Q4_K_M)
| Modelo | Arquivo | Tamanho |
|---|---|---|
| 3B | `Qwen2.5-Omni-3B-Q4_K_M.gguf` | ~1,96 GB |
| 7B | `Qwen2.5-Omni-7B-Q4_K_M.gguf` | ~4,36 GB |

## Regras por modelo
### 3B — liberado
- ✅ Rodar testes e **encerrar o servidor** normalmente ao final.
- Pode coexistir com o backend (porta 8080).

### 7B — cautela máxima
- ⚠️ **Sempre rodar SOZINHO** (nunca com o 3B em RAM) — risco de OOM/travamento.
- ⚠️ **Exige autorização explícita** antes de carregar.
- ⚠️ Na máquina de referência (4,3 GB livres), o 7B `Q4_K_M` (4,36 GB) **não cabe com folga** — para testar 7B é necessário um quant menor (Q3_K_M/Q2_K) ou mais RAM.

## Bind de host
- `--host` default da build = **`localhost`** (→ `127.0.0.1`).
- Sempre `--host 127.0.0.1`; **nunca** `0.0.0.0` (não expor à rede).

## Comando canônico de lançamento
Fonte: `backend/benchmarks/maria_bench/servidor_llama.py` (`_abrir_janela_servidor`).

```powershell
<llama-server.exe> -hf <repo:quant> -c 2048 -t 4 -b 1024 -ub 256 --port 8080 -lv 1 --host 127.0.0.1
```

## Resultados dos Testes A/B (2026-09-06)
- **Teste A (bind):** `netstat` mostra `127.0.0.1:8080` (loopback); `--help` confirma `localhost by default`. Não exposto à rede.
- **Teste B (tool calling nativo):**
  - 3B = **0/5** `tool_calls` nativos; o modelo vazou a intenção como **prosa + tabela Markdown** (`finish_reason=stop`), sem JSON de function call.
  - 7B = **falhou ao carregar** (`500 failed to load`) por OOM (3B já em RAM); máquina com 4,3 GB livres não comporta o 7B Q4_K_M (4,36 GB).
