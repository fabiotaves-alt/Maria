"""CLI para executar o benchmark live da MARIA."""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from dataclasses import asdict

from .analysis.metrics import calculate_maria_metrics, aggregate_by_task
from .analysis.report import generate_report, extrair_texto_system, mascarar_system_prompt
from .benchmark_config import (
    BENCHMARK_RESULTS_DIR,
    BENCHMARK_TIMEOUT_POR_CHAMADA,
    BENCHMARK_WARMUP_TIMEOUT,
    BENCHMARK_REPETICOES,
)
from .utils import (
    MARGEM_SEGURANCA_SYSTEM,
    definir_fator_calibracao,
    estimar_tokens,
    estimar_tokens_calibrado,
    obter_fator_calibracao,
)
from .runners.maria_runner import MariaRunner
from .tasks import load_all_maria_tasks

# llama_client é um módulo local da raiz do projeto, não um pacote instalado.
MARIA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if MARIA_ROOT not in sys.path:
    sys.path.insert(0, MARIA_ROOT)

import re
import requests

# Alias no módulo: permite patch consistente via unittest.mock e evita
# import local dentro de funções.
_requests = requests

from backend.core.config import LLAMA_BASE_URL, LLAMA_MODEL, LLAMA_NUM_CTX, MARIA_SYSTEM_PROMPT
from core.llama_client import (
    LlamaClient,
    LlamaClientError,
    montar_sampler_params,
)  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark live do tool calling da MARIA")
    parser.add_argument("--task-ids", type=int, nargs="+", help="IDs específicos de tarefas")
    parser.add_argument("--tasks", type=int, default=None, help="Número inicial de tarefas")
    parser.add_argument("--category", type=str, help="Categoria exata, por exemplo criar_planilha")
    parser.add_argument("--output-dir", default=BENCHMARK_RESULTS_DIR, help="Diretório base dos resultados")
    parser.add_argument("--delay", type=float, default=0.0, help="Espera entre tarefas em segundos")
    parser.add_argument("--repeticoes", type=int, default=BENCHMARK_REPETICOES,
                        help="Número de repetições por tarefa (padrão: BENCHMARK_REPETICOES)")
    parser.add_argument("--num-predict", type=int, default=None,
                        help="Override do número de tokens previstos pelo modelo no benchmark")
    return parser.parse_args()


def _select_tasks(tasks, args):
    if args.task_ids:
        requested = set(args.task_ids)
        selected = [task for task in tasks if task.id in requested]
        missing = sorted(requested - {task.id for task in selected})
        if missing:
            print(f"Aviso: IDs não encontrados: {missing}")
        return selected
    if args.category:
        return [task for task in tasks if task.category.value == args.category]
    if args.tasks is not None:
        return tasks[:max(args.tasks, 0)]
    return tasks


def _parece_caminho_local(id_modelo: str) -> bool:
    """Retorna True quando o id do modelo parece um caminho de arquivo local
    (blob do modelo, caminho com separadores, ou extensão .gguf)."""
    if not id_modelo:
        return False
    return (
        os.sep in id_modelo
        or "/" in id_modelo
        or id_modelo.lower().endswith(".gguf")
        or re.match(r"^[0-9a-f]{64}$", id_modelo) is not None
        or id_modelo.startswith("sha256-")
    )


def _derivar_rotulo_modelo(n_params: int | float, n_vocab: int) -> str:
    """Deriva um rótulo legível (ex.: 'Qwen2.5 3B') a partir da contagem de
    parâmetros e do tamanho do vocabulário.

    Mapeia n_params para o tamanho conhecido da família Qwen2.5 mais próximo
    e usa n_vocab == 151936 como sinal de família Qwen2.5.
    """
    if not n_params:
        return ""

    # Tamanhos conhecidos da família Qwen2.5 (em bilhões)
    tamanhos_qwen25 = (0.5, 1.5, 3, 7, 14, 32, 72)
    bilhoes = n_params / 1e9
    tamanho = min(tamanhos_qwen25, key=lambda t: abs(t - bilhoes))

    if tamanho == int(tamanho):
        rotulo = f"{int(tamanho)}B"
    else:
        rotulo = f"{tamanho}B"

    if n_vocab in (151936, 152064, 152128):
        return f"Qwen2.5 {rotulo}"
    return rotulo


_FTYPE_PARA_NOME: dict[int, str] = {
    0: "F32",
    1: "F16",
    2: "Q4_0",
    3: "Q4_1",
    6: "Q5_0",
    7: "Q5_1",
    8: "Q8_0",
    9: "Q2_K",
    10: "Q3_K_S",
    11: "Q3_K_M",
    12: "Q3_K_L",
    13: "Q4_K_S",
    14: "Q4_K_M",
    15: "Q5_K_S",
    16: "Q5_K_M",
    17: "Q6_K",
    18: "Q8_K",
    30: "IQ2_XXS",
    31: "IQ2_XS",
    32: "IQ2_S",
    33: "IQ2_M",
    34: "IQ1_S",
    35: "IQ1_M",
    36: "Q4_0_4_4",
    37: "Q4_0_4_8",
    38: "Q4_0_8_8",
    39: "TQ1_0",
    40: "TQ2_0",
}


def _ftype_para_nome(ftype: int | str | None) -> str:
    """Converte o campo ftype (enum GGML ou string) para nome legível."""
    if ftype is None:
        return ""
    if isinstance(ftype, str):
        return ftype
    return _FTYPE_PARA_NOME.get(ftype, f"tipo-{ftype}")


def _formatar_tamanho(tamanho_bytes: int | None) -> str:
    """Formata bytes como string legível (ex.: 2098976768 -> '1.95 GiB')."""
    if not tamanho_bytes:
        return ""
    gib = tamanho_bytes / (1024 ** 3)
    if gib >= 1:
        return f"{gib:.2f} GiB"
    return f"{tamanho_bytes / (1024 ** 2):.1f} MiB"


def _extrair_nome_exibicao(model_id: str) -> str:
    """Extrai um nome amigável do ID cru do modelo.

    Ex: ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M -> Qwen2.5 Omni 3B
    """
    if not model_id:
        return ""
    # Remove prefixo de organização
    nome = model_id.split('/')[-1] if '/' in model_id else model_id
    # Remove a parte de quantizacao apos ':' e o sufixo -GGUF
    nome = nome.split(':')[0]
    nome = nome.replace('-GGUF', '')
    # Converte hifen/traco baixo em espaco
    nome = nome.replace('_', ' ').replace('-', ' ')
    return nome.strip()


def _extrair_quantizacao(model_id: str) -> str:
    """Extrai a quantizacao do ID do modelo.

    Ex: ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M -> Q4_K_M
    """
    if ':' in model_id:
        return model_id.split(':')[-1]
    return 'desconhecida'


def _hash_prompt(prompt: str) -> str:
    """Gera um hash curto (12 hex) do prompt para rastreabilidade nos logs."""
    return hashlib.sha256(prompt.encode()).hexdigest()[:12]


def _obter_metadados_modelo() -> dict | None:
    """Consulta GET {LLAMA_BASE_URL}/v1/models e retorna metadados do primeiro
    modelo carregado no llama-server, ou None se não for possível obter.

    O dicionário retornado contém:
        id, id_exibicao, quantizacao, n_params, n_vocab, n_ctx, n_ctx_train,
        tamanho_bytes, rotulo_tamanho, tamanho_legivel
    """
    try:
        resp = _requests.get(f"{LLAMA_BASE_URL}/v1/models", timeout=5)
        if resp.status_code != 200:
            return None
        modelos = resp.json().get("data", [])
        if not modelos:
            return None
        primeiro = modelos[0]
        meta = primeiro.get("meta", {}) or {}
        id_modelo = primeiro.get("id", "") or ""
    except (_requests.exceptions.RequestException, ValueError, KeyError):
        return None

    n_params = meta.get("n_params")
    n_vocab = meta.get("n_vocab") or 0
    n_ctx = meta.get("n_ctx")
    n_ctx_train = meta.get("n_ctx_train")
    tamanho_bytes = meta.get("size")
    ftype_raw = meta.get("ftype")

    quantizacao = _ftype_para_nome(ftype_raw) or _extrair_quantizacao(id_modelo)
    rotulo = _derivar_rotulo_modelo(n_params, n_vocab) if n_params else ""
    tamanho_legivel = _formatar_tamanho(tamanho_bytes)

    # Se o id é um caminho local/blob, usa o rótulo derivado como exibição
    id_exibicao = rotulo if (_parece_caminho_local(id_modelo) and rotulo) else id_modelo
    # Nome amigável: id_exibicao derivado, ou extração direta do ID cru
    nome_exibicao = id_exibicao or _extrair_nome_exibicao(id_modelo)

    return {
        "id": id_modelo,
        "id_exibicao": id_exibicao,
        "nome_exibicao": nome_exibicao,
        "quantizacao": quantizacao,
        "n_params": n_params,
        "n_vocab": n_vocab,
        "n_ctx": n_ctx,
        "n_ctx_train": n_ctx_train,
        "tamanho_bytes": tamanho_bytes,
        "rotulo_tamanho": rotulo,
        "tamanho_legivel": tamanho_legivel,
    }


def _contar_tokens_exatos(base_url: str, texto: str) -> int | None:
    """Conta tokens exatos via POST {base_url}/tokenize do llama-server.

    Custa 1 chamada por execução do benchmark (sem inferência, ~ms). Retorna
    None se o endpoint não estiver disponível (versão antiga) ou falhar — o
    chamador faz fallback para a estimativa por caracteres.
    """
    try:
        resp = _requests.post(
            f"{base_url.rstrip('/')}/tokenize",
            json={"content": texto},
            timeout=10,
        )
        if resp.status_code == 200:
            return len(resp.json().get("tokens") or [])
    except (_requests.exceptions.RequestException, ValueError):
        pass
    return None


def _warmup_model() -> dict:
    """Aquece o modelo e retorna os metadados do modelo carregado.

    Aborta com erro fatal se /v1/models não responder ou não retornar modelo
    algum — o relatório do benchmark exibe apenas dados REAIS (nenhuma coluna
    "configurado" fake).
    """
    print(f"Aquecendo o modelo (timeout de warmup: {BENCHMARK_WARMUP_TIMEOUT}s)...")
    inicio = time.monotonic()

    # --- OBTEM METADADOS REAIS (fonte unica de verdade do modelo) ---
    metadados_modelo = _obter_metadados_modelo()
    if metadados_modelo is None:
        raise SystemExit(
            "FALHA CRITICA: Nao foi possivel obter o modelo carregado "
            f"via {LLAMA_BASE_URL}/v1/models. Verifique se o llama-server "
            "esta rodando e acessivel."
        )

    modelo_carregado = metadados_modelo.get("id")
    id_exibicao = metadados_modelo.get("id_exibicao") or modelo_carregado
    nome_exibicao = metadados_modelo.get("nome_exibicao") or id_exibicao
    quantizacao = metadados_modelo.get("quantizacao") or "desconhecida"

    print(
        f"[INFO] Modelo detectado: {nome_exibicao} ({quantizacao}) — "
        f"ID: {modelo_carregado}"
    )

    if modelo_carregado and modelo_carregado != LLAMA_MODEL:
        eh_local = _parece_caminho_local(modelo_carregado)
        rotulo = metadados_modelo.get("rotulo_tamanho", "")
        if not eh_local or not rotulo:
            print(
                f"[AVISO] LLAMA_MODEL configurado = '{LLAMA_MODEL}', mas o modelo "
                f"carregado no llama-server (/v1/models) = '{id_exibicao}'.\n"
                "As execuções podem não estar usando o modelo desejado."
            )
        elif rotulo and LLAMA_MODEL and rotulo.split()[-1].lower() not in LLAMA_MODEL.lower():
            print(
                f"[AVISO] LLAMA_MODEL configurado = '{LLAMA_MODEL}', mas o modelo "
                f"carregado no llama-server parece ser '{rotulo}'.\n"
                "As execuções podem não estar usando o modelo desejado."
            )

    # --- DETECTA O CONTEXTO REAL DO SERVIDOR (fonte unica: /v1/models) ---
    ctx_size = metadados_modelo.get("n_ctx")
    if ctx_size:
        ctx_fonte = "models"
        print(f"[INFO] Contexto real do servidor (via /v1/models): {ctx_size} tokens")
    else:
        ctx_size = LLAMA_NUM_CTX
        ctx_fonte = "fallback"
        print(
            "[AVISO] Nao foi possivel detectar o contexto real do servidor; "
            f"assumindo LLAMA_NUM_CTX={ctx_size}. Inicie o llama-server com "
            "--ctx-size explicito para maior precisao."
        )

    # --- CONTA O SYSTEM PROMPT (1 chamada exata via /tokenize + calibracao) ---
    prompt_tokens = _contar_tokens_exatos(LLAMA_BASE_URL, MARIA_SYSTEM_PROMPT)
    if prompt_tokens is not None:
        definir_fator_calibracao(prompt_tokens, MARIA_SYSTEM_PROMPT)
        origem_tokens = "contagem exata via /tokenize"
    else:
        prompt_tokens = estimar_tokens(MARIA_SYSTEM_PROMPT)
        origem_tokens = "estimativa (~4 chars/token; /tokenize indisponivel)"

    # --- VERIFICA SE O SYSTEM PROMPT CABE NO CONTEXTO ---
    limite_prompt = ctx_size - MARGEM_SEGURANCA_SYSTEM
    if prompt_tokens > limite_prompt:
        raise SystemExit(
            f"FALHA CRITICA: O system prompt tem ~{prompt_tokens} tokens ({origem_tokens}), "
            f"mas o servidor oferece apenas {ctx_size} tokens de contexto. Com margem de "
            f"seguranca de {MARGEM_SEGURANCA_SYSTEM} tokens, o prompt nao cabe. SOLUCOES: "
            "(1) Reduza o system prompt em backend/core/system_prompt.txt; "
            f"(2) Inicie o llama-server com --ctx-size maior "
            f"(ex: --ctx-size {prompt_tokens + MARGEM_SEGURANCA_SYSTEM + 1024})."
        )
    print(
        f"[OK] System prompt ({prompt_tokens} tokens; {origem_tokens}) cabe no contexto "
        f"de {ctx_size} tokens (margem: {limite_prompt - prompt_tokens})."
    )

    # --- WARMUP ---
    try:
        cliente_warmup = LlamaClient(timeout=BENCHMARK_WARMUP_TIMEOUT)
        resposta = cliente_warmup.enviar_mensagem(
            mensagens=[{"role": "user", "content": "Responda apenas com a palavra ok."}],
            tools=None,
            stream=False,
        )
    except LlamaClientError as error:
        raise SystemExit(
            "Falha no warmup do modelo: não foi possível obter resposta do llama-server.\n"
            f"Detalhes: {error}\n"
            "Verifique se o llama-server está rodando (`llama-server -m <modelo.gguf> --port 8080`) "
            f"e o modelo {LLAMA_MODEL} está carregado antes de rodar o benchmark."
        ) from error

    duracao_s = time.monotonic() - inicio
    print(f"Modelo aquecido em {duracao_s:.1f}s. Resposta de teste: {resposta.strip()!r}")
    print(f"Modelo carregado: {id_exibicao or 'N/D'}")

    # Metadados de contexto para o relatorio, log.json e pre-check do runner.
    metadados_modelo["ctx_size"] = ctx_size
    metadados_modelo["ctx_fonte"] = ctx_fonte
    metadados_modelo["system_prompt_tokens"] = prompt_tokens
    return metadados_modelo


def main() -> int:
    args = _parse_args()
    tasks = _select_tasks(load_all_maria_tasks(), args)
    if not tasks:
        raise SystemExit("Nenhuma tarefa selecionada.")

    metadados_modelo = _warmup_model()
    modelo_carregado = (metadados_modelo or {}).get("id")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(args.output_dir, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"Executando {len(tasks)} tarefa(s) em sequência. Resultados: {run_dir}")

    # Um único runner reduz reconexões; a execução sequencial evita sobrecarga da GPU.
    runner = MariaRunner(
        num_predict=args.num_predict,
        modelo_carregado=modelo_carregado,
        ctx_size=(metadados_modelo or {}).get("ctx_size"),
    )
    resultados_individuais_todas_tarefas = []
    agregados_todas_tarefas = []

    for index, task in enumerate(tasks, start=1):
        print(f"[{index}/{len(tasks)}] Tarefa {task.id}: {task.name} ({args.repeticoes}x)")

        def _mostrar_resultado_individual(indice_execucao, resultado, task=task):
            status = "✓" if resultado.tool_correct else "✗"
            esperado = (
                f" (esperado: {task.expected_tool})"
                if not resultado.tool_correct and task.expected_tool
                else ""
            )
            print(
                f"    rep {indice_execucao}/{args.repeticoes}: {status} "
                f"tool={resultado.tool_detected or '—'}{esperado} "
                f"args={'OK' if resultado.args_correct else 'DIVERGENTE'} "
                f"latência={resultado.latency_ms / 1000:.1f}s tokens={resultado.tokens_gerados}"
            )

        resultados_task = runner.run_repeated(
            task, args.repeticoes, apos_cada_execucao=_mostrar_resultado_individual
        )
        resultados_individuais_todas_tarefas.extend(resultados_task)
        agregados_todas_tarefas.append(aggregate_by_task(resultados_task))

        metricas_parciais = calculate_maria_metrics(resultados_individuais_todas_tarefas)
        print(
            f"    → acumulado: tool_accuracy={metricas_parciais.tool_accuracy * 100:.1f}% "
            f"confirmação={metricas_parciais.confirmation_success_rate * 100:.1f}% "
            f"latência média={metricas_parciais.avg_latency_ms / 1000:.1f}s"
        )

    # log.json final com estrutura individual + agregado_por_tarefa + meta.
    # Escrita feita SOMENTE aqui (fonte única), com metadados completos do
    # modelo real e hash do system prompt para rastreabilidade.
    system_prompt_hash = _hash_prompt(MARIA_SYSTEM_PROMPT)

    # Extrair o texto do system prompt uma única vez para incluir no meta
    system_prompt_texto = None
    for resultado in resultados_individuais_todas_tarefas:
        texto = extrair_texto_system(resultado.prompt_enviado)
        if texto:
            system_prompt_texto = texto
            break

    log_final = {
        "meta": {
            "id_modelo": (metadados_modelo or {}).get("id"),
            "modelo_quantizacao": (metadados_modelo or {}).get("quantizacao"),
            "data_execucao": datetime.now().isoformat(),
            "total_tarefas": len(tasks),
            "repeticoes_por_tarefa": args.repeticoes,
            "versao_benchmark": "2.0",
            "system_prompt_hash": system_prompt_hash,
            "system_prompt_completo": system_prompt_texto,
            "llama_base_url": LLAMA_BASE_URL,
            "llama_num_ctx_config": LLAMA_NUM_CTX,
            "ctx_size_detectado": (metadados_modelo or {}).get("ctx_size"),
            "ctx_fonte": (metadados_modelo or {}).get("ctx_fonte"),
            "system_prompt_tokens": (metadados_modelo or {}).get("system_prompt_tokens"),
            "fator_calibracao_tokens": obter_fator_calibracao(),
            "timeout_por_chamada_s": BENCHMARK_TIMEOUT_POR_CHAMADA,
            "sampler_params": montar_sampler_params(),
        },
        "individual": [
            {
                **asdict(r),
                "prompt_enviado": mascarar_system_prompt(r.prompt_enviado) if r.prompt_enviado else None,
            }
            for r in resultados_individuais_todas_tarefas
        ],
        "agregado_por_tarefa": [asdict(a) for a in agregados_todas_tarefas],
    }
    log_path = os.path.join(run_dir, "log.json")
    with open(log_path, "w", encoding="utf-8") as log_file:
        json.dump(log_final, log_file, ensure_ascii=False, indent=2)

    metricas_finais = calculate_maria_metrics(resultados_individuais_todas_tarefas)

    generate_report(resultados_individuais_todas_tarefas,
                    metricas_finais,
                    run_dir,
                    metadados_modelo=metadados_modelo,
                    sampler_params=montar_sampler_params(),
                    log_final=log_final)

    print("\nResumo")
    print(f"Tarefas: {metricas_finais.total_tasks}")
    print(f"Tool accuracy: {metricas_finais.tool_accuracy * 100:.1f}%")
    print(f"Confirmação: {metricas_finais.confirmation_success_rate * 100:.1f}%")
    print(f"Runtime: {metricas_finais.runtime_success_rate * 100:.1f}%")
    print(f"Latência média: {metricas_finais.avg_latency_ms:.1f} ms")
    print(f"Relatório: {os.path.join(run_dir, 'report.md')}")
    return 0


def _run_benchmark_programatico(
    modelo: str,
    task_ids: list[int] | None,
    repeticoes: int,
    metricas_sistema: dict | None = None,
) -> int:
    """
    Corpo da avaliação programática — garante o llama-server, faz warmup real
    e executa o benchmark. Deve ser chamado via run_benchmark_programatico(),
    que cuida do nível de logging (WARNING durante a avaliação, restaurado em
    try/finally).
    """
    import types

    # Garante o llama-server com o modelo escolhido no menu. Quando o servidor
    # não está ativo, abre nova janela de console (logs do llama-server visíveis)
    # e aguarda o /v1/models responder — a escolha do modelo deixa de ser apenas
    # cosmética.
    from .servidor_llama import garantir_servidor

    # Monta namespace de args equivalente ao _parse_args()
    args = types.SimpleNamespace(
        task_ids=task_ids,
        tasks=None,
        category=None,
        output_dir=BENCHMARK_RESULTS_DIR,
        delay=0.0,
        repeticoes=repeticoes,
        num_predict=None,
    )

    # Sobrescreve o modelo no config em runtime (sem alterar ENV permanentemente)
    import backend.core.config as _cfg
    _cfg.LLAMA_MODEL = modelo
    # Atualiza também o binding deste módulo (importado por valor no topo): o
    # warmup compara o modelo detectado com LLAMA_MODEL para emitir aviso de
    # divergência — com o menu, o "configurado" É o escolhido, então o aviso
    # não deve mais aparecer.
    globals()["LLAMA_MODEL"] = modelo

    todas = load_all_maria_tasks()
    tasks = _select_tasks(todas, args)
    if not tasks:
        raise SystemExit("Nenhuma tarefa selecionada.")

    # Servidor ativo com o modelo escolhido antes de aquecer (o warmup mede o
    # tempo real de carregamento/primeira resposta).
    garantir_servidor(modelo)

    # Warmup real com o modelo escolhido (mede tempo de aquecimento)
    inicio_warmup = time.monotonic()
    metadados_modelo = _warmup_model()
    duracao_warmup_s = round(time.monotonic() - inicio_warmup, 2)
    modelo_carregado = (metadados_modelo or {}).get("id")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(args.output_dir, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"Executando {len(tasks)} tarefa(s). Resultados: {run_dir}")

    runner = MariaRunner(
        num_predict=args.num_predict,
        modelo_carregado=modelo_carregado,
        ctx_size=(metadados_modelo or {}).get("ctx_size"),
    )
    resultados_individuais_todas_tarefas = []
    agregados_todas_tarefas = []

    for index, task in enumerate(tasks, start=1):
        print(f"[{index}/{len(tasks)}] Tarefa {task.id}: {task.name} ({repeticoes}x)")

        def _mostrar_resultado_individual(indice_execucao, resultado, task=task):
            status = "✓" if resultado.tool_correct else "✗"
            esperado = (
                f" (esperado: {task.expected_tool})"
                if not resultado.tool_correct and task.expected_tool
                else ""
            )
            print(
                f"    rep {indice_execucao}/{repeticoes}: {status} "
                f"tool={resultado.tool_detected or '—'}{esperado} "
                f"args={'OK' if resultado.args_correct else 'DIVERGENTE'} "
                f"latência={resultado.latency_ms / 1000:.1f}s tokens={resultado.tokens_gerados}"
            )

        resultados_task = runner.run_repeated(
            task, repeticoes, apos_cada_execucao=_mostrar_resultado_individual
        )
        resultados_individuais_todas_tarefas.extend(resultados_task)
        agregados_todas_tarefas.append(aggregate_by_task(resultados_task))

        metricas_parciais = calculate_maria_metrics(resultados_individuais_todas_tarefas)
        print(
            f"    → acumulado: tool_accuracy={metricas_parciais.tool_accuracy * 100:.1f}% "
            f"confirmação={metricas_parciais.confirmation_success_rate * 100:.1f}% "
            f"latência média={metricas_parciais.avg_latency_ms / 1000:.1f}s"
        )

    system_prompt_hash = _hash_prompt(MARIA_SYSTEM_PROMPT)
    system_prompt_texto = None
    for resultado in resultados_individuais_todas_tarefas:
        texto = extrair_texto_system(resultado.prompt_enviado)
        if texto:
            system_prompt_texto = texto
            break

    log_final = {
        "meta": {
            "id_modelo": (metadados_modelo or {}).get("id"),
            "modelo_quantizacao": (metadados_modelo or {}).get("quantizacao"),
            "data_execucao": datetime.now().isoformat(),
            "total_tarefas": len(tasks),
            "repeticoes_por_tarefa": repeticoes,
            "versao_benchmark": "2.0",
            "system_prompt_hash": system_prompt_hash,
            "system_prompt_completo": system_prompt_texto,
            "llama_base_url": LLAMA_BASE_URL,
            "llama_num_ctx_config": LLAMA_NUM_CTX,
            "ctx_size_detectado": (metadados_modelo or {}).get("ctx_size"),
            "ctx_fonte": (metadados_modelo or {}).get("ctx_fonte"),
            "system_prompt_tokens": (metadados_modelo or {}).get("system_prompt_tokens"),
            "fator_calibracao_tokens": obter_fator_calibracao(),
            "timeout_por_chamada_s": BENCHMARK_TIMEOUT_POR_CHAMADA,
            "sampler_params": montar_sampler_params(),
            "warmup_duracao_s": duracao_warmup_s,
            "metricas_sistema": metricas_sistema or {},
        },
        "individual": [
            {
                **asdict(r),
                "prompt_enviado": mascarar_system_prompt(r.prompt_enviado) if r.prompt_enviado else None,
            }
            for r in resultados_individuais_todas_tarefas
        ],
        "agregado_por_tarefa": [asdict(a) for a in agregados_todas_tarefas],
    }
    log_path = os.path.join(run_dir, "log.json")
    with open(log_path, "w", encoding="utf-8") as log_file:
        json.dump(log_final, log_file, ensure_ascii=False, indent=2)

    metricas_finais = calculate_maria_metrics(resultados_individuais_todas_tarefas)

    generate_report(
        resultados_individuais_todas_tarefas,
        metricas_finais,
        run_dir,
        metadados_modelo=metadados_modelo,
        sampler_params=montar_sampler_params(),
        log_final=log_final,
        metricas_sistema=metricas_sistema,
        warmup_duracao_s=duracao_warmup_s,
    )

    print("\nResumo")
    print(f"Tarefas: {metricas_finais.total_tasks}")
    print(f"Tool accuracy: {metricas_finais.tool_accuracy * 100:.1f}%")
    print(f"Confirmação: {metricas_finais.confirmation_success_rate * 100:.1f}%")
    print(f"Runtime: {metricas_finais.runtime_success_rate * 100:.1f}%")
    print(f"Latência média: {metricas_finais.avg_latency_ms:.1f} ms")
    print(f"Relatório: {os.path.join(run_dir, 'report.md')}")
    print("\nO llama-server continua ativo na janela de console aberta.")
    print("Você pode fechá-la ou mantê-la para reutilizar na próxima execução.")
    return 0


def run_benchmark_programatico(
    modelo: str,
    task_ids: list[int] | None,
    repeticoes: int,
    metricas_sistema: dict | None = None,
) -> int:
    """
    Ponto de entrada programático (chamado pelo menu do ui_terminal).

    Garante automaticamente o llama-server com o modelo escolhido (abre nova
    janela de console quando necessário) antes do warmup real, que mede o tempo
    de aquecimento registrado no report.md e no log.json.

    Mantém o terminal da MARIA limpo durante a avaliação: o logger raiz é
    elevado para WARNING (suprime os INFO de core.llama_client/tools_schema/
    maria_runner) e RESTAURADO ao nível anterior no finally — mesmo em caso de
    SystemExit, KeyboardInterrupt ou erro inesperado.

    Args:
        modelo: nome do modelo llama (ex: 'qwen2.5-omni-3b')
        task_ids: lista de IDs de tarefas ou None para todas
        repeticoes: número de repetições por tarefa
        metricas_sistema: dict coletado antes do warmup (snapshot de CPU/RAM/GPU)

    Returns:
        0 em sucesso, != 0 em falha
    """
    import logging
    root = logging.getLogger()
    nivel_anterior = root.getEffectiveLevel()
    root.setLevel(logging.WARNING)
    try:
        return _run_benchmark_programatico(
            modelo=modelo,
            task_ids=task_ids,
            repeticoes=repeticoes,
            metricas_sistema=metricas_sistema,
        )
    finally:
        root.setLevel(nivel_anterior)


if __name__ == "__main__":
    raise SystemExit(main())