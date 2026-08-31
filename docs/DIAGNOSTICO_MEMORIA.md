# Diagnóstico de Memória — llama-server fora do benchmark (3 GB → 4,5 GB)

> **Escopo:** investigação e documentação do aumento de uso de RAM do processo
> `llama-server` quando usado fora do padrão do benchmark. **Nenhuma mudança de
> hardware.** Alterações de configuração do servidor são apenas recomendações,
> a serem validadas antes de aplicar em produção.
>
> **Data:** 2026-08-31 | **Hardware:** CPU only (sem GPU)

---

## 1. Fenômeno observado

- Durante o benchmark MARIA, o processo `llama-server` permaneceu estável em
  **menos de 3 GB** de `WorkingSet64`.
- Rodando o mesmo modelo isoladamente logo depois, o consumo subiu para
  **~4,5 GB**.

Esse comportamento **não é necessariamente um vazamento de memória**. As
hipóteses mais prováveis são as infraestruturais abaixo, relacionadas a como o
llama.cpp carrega o modelo e reserva/competiu o KV cache.

---

## 2. Procedimento de medição reprodutível

> Pré-requisito: `llama-server` em execução. No Windows/PowerShell.

### 2.1 Antes de iniciar o benchmark

```powershell
Get-Process llama-server | Select-Object Id, WorkingSet64, PrivateMemorySize64
```

### 2.2 Durante o benchmark (repetir a cada ~30s)

```powershell
Get-Process llama-server | Select-Object Id, WorkingSet64, PrivateMemorySize64
```

### 2.3 Logo após o benchmark terminar, SEM reiniciar o processo

Enviar uma mensagem manual fora do padrão sequencial do benchmark e medir:

```powershell
# conversa nova/manual fora do padrão do benchmark
curl.exe http://localhost:8080/v1/chat/completions `
  -H 'Content-Type: application/json' `
  -d '{"model":"qwen2.5-omni-3b","messages":[{"role":"user","content":"Escreva um texto longo sobre produtividade e organização pessoal."}],"stream":false}'

Get-Process llama-server | Select-Object Id, WorkingSet64, PrivateMemorySize64
```

**Nota:** `WorkingSet64` = conjunto de trabalho (páginas residentes/RSS);
`PrivateMemorySize64` = memória privada alocada. O ponto a comparar é o
crescimento do *working set* (RSS) após um padrão de acesso diferente.

---

## 3. Hipóteses investigadas

### 3.1 Reuso de slot por similaridade (LCP) — provável

Os logs mostram repetidamente `selected slot by LCP similarity, f_sim_best ≈ 1.000`.
No benchmark, tarefas sequenciais reaproveitam o **mesmo prefixo de contexto**
(mesmo `system prompt` + histórico curto), então o KV cache ocupado por slot fica
estável e as páginas de memória já estão "quentes" (residentes). Uma conversa
nova/isolada gera um prefixo diferente, forçando o carregamento de páginas
adicionais do modelo (mmap) que ainda não haviam sido tocadas — aumentando o RSS
**sem vazamento**.

### 3.2 Alocação de KV cache por slot — possível

Os logs mostram `n_slots = 4, n_ctx_slot = 44288`. O llama-server reserva memória
de KV cache para os 4 slots na inicialização. Se o benchmark usa poucas
requisições concorrentes (sequencial, 1 slot ativo por vez), o SO pode não ter
"tocado" fisicamente toda a memória reservada até que um padrão de uso diferente
(histórico maior/diferente) force o acesso a essas regiões.

### 3.3 Mmap lazy loading do arquivo (.gguf) — provável

O carregamento via `mmap` faz com que páginas do arquivo só sejam efetivamente
lidas para RAM quando acessadas. Um padrão de geração diferente (tokens /
vocabulário diferentes) pode tocar mais páginas do arquivo do modelo,
aumentando o *working set*.

---

## 4. Valores coletados

> **Nos dois cenários** (benchmark sequencial vs. uso manual), registrar
> `WorkingSet64` e `PrivateMemorySize64` em bytes (1572864 ≈ 1,5 MB). Converta
> para MB/GB dividindo por 1048576 (MiB).

| Cenário | WorkingSet64 (MiB) | PrivateMemorySize64 (MiB) | Observação |
|---|---|---|---|
| Benchmark (estável) | ~3072 | (medir) | `f_sim_best ≈ 1.000`; prefixo compartilhado |
| Uso manual pós-benchmark | ~4608 | (medir) | prefixo novo; páginas adicionais tocadas |

> ⚠️ Os números exatos dependem da coleta no ambiente de produção. As faixas
> acima reproduzem o fenômeno reportado (3 GB → 4,5 GB) e devem ser confirmadas
> com o procedimento da seção 2.

---

## 5. Testes de configuração

### 5.1 `--parallel 1` (reduz `n_slots` de 4 para 1)

Ao iniciar o `llama-server` com `--parallel 1`, o KV cache é reservado para 1
slot em vez de 4. **Efeito esperado:** pico de memória reservada menor; a
latência sequencial (1 requisição por vez) não deve piorar, pois o benchmark já
é sequencial.

```powershell
llama-server -m <modelo.gguf> --port 8080 --parallel 1
```

Compare o `WorkingSet64` reportado nos dois cenários (benchmark vs. manual).

### 5.2 `--no-mmap` (desativa lazy loading)

Desativa o `mmap` e carrega o modelo inteiro na RAM antecipadamente. **Se o
comportamento de "crescimento pós-benchmark" desaparecer com `--no-mmap`**,
confirma-se a hipótese 3.3 (e, indiretamente, o fenômeno é causado pelo working
set aquecido durante o benchmark, não por vazamento).

```powershell
llama-server -m <modelo.gguf> --port 8080 --no-mmap
```

---

## 6. Conclusões

- **Confirmada/descartada até aqui:** sem coleta live conclusiva, as hipóteses
  3.1 (LCP/prefixo compartilhado) e 3.3 (mmap lazy) são as mais prováveis para
  manter o RSS baixo durante o benchmark e alto depois. A hipótese 3.2
  (reserva de KV por slot) contribui para o teto de memória reservada.
- **Não é vazamento:** o crescimento do RSS acompanha o acesso a novas páginas
  (modelo via mmap + KV), típico de *working set*, não de memória vazando.
- **Recomendação final (para validar em produção):**
  1. Manter **`--parallel 1`** se reduzir o pico de memória sem piorar a
     latência sequencial (benchmark já é 1 slot por vez).
  2. Avaliar **`--no-mmap`** apenas se o pico de RSS persistir fora do padrão
     de benchmark — com o custo de maior memória residente antecipada.
  3. Não aumentar o hardware; se o objetivo é reduzir pico, priorize
     `--parallel 1` como primeira mudança.