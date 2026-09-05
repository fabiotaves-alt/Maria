"""Automação do llama-server para o benchmark da MARIA.

Abre (ou reutiliza) o llama-server em uma nova janela de console com o modelo
Hugging Face escolhido no menu de Avaliação de Desempenho. A janela permanece
aberta enquanto o servidor rodar e exibe os LOGS NORMAIS do llama-server —
nada é encerrado automaticamente ao final da avaliação (o servidor pode ser
reutilizado por uma próxima execução ou pelo modo chat).

Tudo é configurável via ENV:
    LLAMA_SERVER_EXE            caminho completo do llama-server.exe
    LLAMA_SERVER_CTX            contexto (-c, padrão 2048)
    LLAMA_SERVER_THREADS        threads (-t, padrão 4)
    LLAMA_SERVER_BATCH          batch (-b, padrão 1024)
    LLAMA_SERVER_UBATCH         ubatch (-ub, padrão 256)
    LLAMA_SERVER_LOG_LEVEL      nível de log (-lv, padrão 1)
    LLAMA_SERVER_STARTUP_TIMEOUT    timeout p/ subir/responder (padrão 600s)
    LLAMA_SERVER_POLL_INTERVALO     intervalo do polling (padrão 2.0s)

A porta/host vem de LLAMA_BASE_URL (backend.core.config), garantindo que o
servidor iniciado seja exatamente o que o benchmark e o modo chat usam.
"""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests as _requests

# Chave LLAMA_MODEL -> repositório/quantização HF usado no llama-server (-hf).
# A escolha do modelo no menu deixa de ser cosmética: o servidor sobe com o
# GGUF correspondente (3B leve ou 7B pesado).
MODELOS_HF: dict[str, str] = {
    "qwen2.5-omni-3b": "ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M",
    "qwen2.5-omni-7b": "ggml-org/Qwen2.5-Omni-7B-GGUF:Q4_K_M",
}

# Diretórios candidatos para auto-descoberta do executável (além de ENV/PATH).
_DIRETORIOS_CANDIDATOS = (
    Path.home() / "Documents" / "llama_cpp",
    Path.cwd() / "llama",
)

# Limiar (params) para distinguir 3B de 7B a partir de meta.n_params do
# /v1/models (ex.: Qwen2.5-Omni-3B ~= 3.1B, 7B ~= 7.6B).
_LIMIAR_BILHOES = 5e9


def _env_int(nome: str, default: int) -> int:
    try:
        return int(os.getenv(nome, str(default)))
    except (TypeError, ValueError):
        return default


def _env_float(nome: str, default: float) -> float:
    try:
        return float(os.getenv(nome, str(default)))
    except (TypeError, ValueError):
        return default


# ───────────────────────────────────────────────────────────────────────────
# Descoberta do executável
# ───────────────────────────────────────────────────────────────────────────
def _localizar_llama_server() -> str | None:
    """Localiza o llama-server.exe.

    Ordem de busca:
      1. ENV LLAMA_SERVER_EXE
      2. PATH (shutil.which)
      3. Diretórios candidatos (busca direta e em subpastas de 1º nível, ex.:
         '.../Documents/llama_cpp/llama-b10717-bin-win-cpu-x64/llama-server.exe')
    """
    env_path = os.getenv("LLAMA_SERVER_EXE")
    if env_path and Path(env_path).is_file():
        return env_path

    import shutil
    na_path = shutil.which("llama-server")
    if na_path:
        return na_path

    for diretorio in _DIRETORIOS_CANDIDATOS:
        if not diretorio.is_dir():
            continue
        direto = diretorio / "llama-server.exe"
        if direto.is_file():
            return str(direto)
        try:
            for sub in diretorio.iterdir():
                if sub.is_dir():
                    candidato = sub / "llama-server.exe"
                    if candidato.is_file():
                        return str(candidato)
        except OSError:
            continue
    return None


# ───────────────────────────────────────────────────────────────────────────
# Configuração efetiva do servidor
# ───────────────────────────────────────────────────────────────────────────
def _config_servidor() -> dict:
    """Monta a configuração efetiva (exe, base_url, host, porta, flags)."""
    from backend.core.config import LLAMA_BASE_URL

    parsed = urlsplit(LLAMA_BASE_URL)
    host = parsed.hostname or "127.0.0.1"
    porta = parsed.port or 8080

    cfg = {
        "exe": _localizar_llama_server(),
        "base_url": LLAMA_BASE_URL,
        "host": host,
        "porta": porta,
        "ctx": _env_int("LLAMA_SERVER_CTX", 2048),
        "threads": _env_int("LLAMA_SERVER_THREADS", 4),
        "batch": _env_int("LLAMA_SERVER_BATCH", 1024),
        "ubatch": _env_int("LLAMA_SERVER_UBATCH", 256),
        "log_level": os.getenv("LLAMA_SERVER_LOG_LEVEL", "1"),
        "timeout_inicio": _env_int("LLAMA_SERVER_STARTUP_TIMEOUT", 600),
        "poll_intervalo": _env_float("LLAMA_SERVER_POLL_INTERVALO", 2.0),
    }
    return cfg


# ───────────────────────────────────────────────────────────────────────────
# Consultas ao servidor
# ───────────────────────────────────────────────────────────────────────────
def _obter_modelo_ativo(base_url: str) -> dict | None:
    """Consulta GET {base_url}/v1/models e retorna o primeiro modelo (ou None)."""
    url = f"{base_url.rstrip('/')}/v1/models"
    try:
        resp = _requests.get(url, timeout=3)
        if resp.status_code == 200:
            dados = resp.json().get("data", [])
            if dados:
                return dados[0] or {}
    except (_requests.exceptions.RequestException, ValueError, KeyError):
        pass
    return None


def _detectar_familia(ativo: dict | None) -> str | None:
    """Retorna '3b' ou '7b' conforme o modelo carregado no servidor.

    Prioriza meta.n_params (/v1/models) quando disponível; fallback para o
    texto do id/nome do modelo (ex.: 'Qwen2.5-Omni-7B-GGUF:Q4_K_M').
    """
    if not ativo:
        return None
    meta = ativo.get("meta") or {}
    n_params = meta.get("n_params")
    if n_params:
        try:
            return "3b" if float(n_params) < _LIMIAR_BILHOES else "7b"
        except (TypeError, ValueError):
            pass
    texto = (
        f"{ativo.get('id') or ''} {meta.get('name') or ''} "
        f"{meta.get('general.name') or ''}"
    ).lower()
    if "3b" in texto:
        return "3b"
    if "7b" in texto:
        return "7b"
    return None


def _familia_esperada(modelo: str) -> str:
    """Mapeia a chave do menu ('qwen2.5-omni-3b'/'7b') para '3b'/'7b'."""
    return "3b" if "3b" in modelo.lower() else "7b"


# ───────────────────────────────────────────────────────────────────────────
# Início do servidor
# ───────────────────────────────────────────────────────────────────────────
def _abrir_janela_servidor(cfg: dict, modelo: str):
    """Abre o llama-server em uma nova janela de console própria.

    No Windows o executável é iniciado DIRETAMENTE com CREATE_NEW_CONSOLE:
    a janela nova exibe os logs normais do llama-server (mesma experiência de
    rodar o exe manualmente). Em outros SOs, roda o processo herdando o
    terminal.
    """
    exe = cfg["exe"]
    repo = MODELOS_HF[modelo]
    args = [
        "-hf", repo,
        "-c", str(cfg["ctx"]),
        "-t", str(cfg["threads"]),
        "-b", str(cfg["batch"]),
        "-ub", str(cfg["ubatch"]),
        "--port", str(cfg["porta"]),
        "-lv", str(cfg["log_level"]),
    ]
    print()
    print("Abrindo o llama-server em uma nova janela (logs do servidor visíveis)...")
    print(f"  {exe}")
    print(f"  {' '.join(args)}")
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        subprocess.Popen([exe] + args, creationflags=creationflags)
    else:
        subprocess.Popen([exe] + args)


def _encerrar_servidor_na_porta(cfg: dict):
    """Encerra o processo do llama-server que está ouvindo na porta configurada.

    Usa psutil para achar o PID dono do socket; só encerra processos cujo nome
    contenha 'llama' (nunca um HTTP server qualquer da porta).
    """
    import psutil

    porta = cfg["porta"]
    pids: set[int] = set()
    try:
        for conn in psutil.net_connections(kind="tcp"):
            try:
                if conn.laddr.port == porta and conn.pid:
                    pids.add(conn.pid)
            except (AttributeError, OSError):
                continue
    except (psutil.Error, OSError):
        pass

    if not pids:
        print("Nenhum processo ouvindo na porta; nada a encerrar.")
        return
    for pid in pids:
        try:
            processo = psutil.Process(pid)
            nome = (processo.name() or "").lower()
            if "llama" not in nome:
                print(
                    f"[aviso] PID {pid} na porta {porta} não parece ser o "
                    "llama-server; ignorado."
                )
                continue
            processo.terminate()
            processo.wait(timeout=10)
            print(f"Servidor antigo encerrado (PID {pid}).")
        except (psutil.Error, subprocess.TimeoutExpired):
            print(f"[aviso] Não foi possível encerrar o PID {pid}.")


def _aguardar_servidor(cfg: dict) -> dict:
    """Faz polling em /v1/models até o servidor responder (ou timeout)."""
    timeout = cfg["timeout_inicio"]
    inicio = time.monotonic()
    print(
        f"Aguardando o llama-server responder em {cfg['base_url']} "
        f"(timeout: {timeout}s). A janela fica aberta; modelos grandes podem "
        "demorar para carregar na primeira execução..."
    )
    ultimo_aviso = 0.0
    while True:
        ativo = _obter_modelo_ativo(cfg["base_url"])
        if ativo:
            print(f"Servidor pronto em {cfg['base_url']}.")
            return ativo
        decorrido = time.monotonic() - inicio
        if decorrido >= timeout:
            raise SystemExit(
                "Timeout ao aguardar o llama-server responder. Verifique a janela "
                "do PowerShell aberta (pode haver erro de download/modelo ou a "
                "porta pode estar ocupada)."
            )
        if decorrido - ultimo_aviso >= 10:
            print(f"    ... {decorrido:.0f}s — servidor ainda não respondeu.")
            ultimo_aviso = decorrido
        time.sleep(cfg["poll_intervalo"])


# ───────────────────────────────────────────────────────────────────────────
# API pública
# ───────────────────────────────────────────────────────────────────────────
def garantir_servidor(modelo: str) -> dict:
    """Garante um llama-server ativo com o modelo escolhido no menu.

    Fluxo:
      1. Se já houver servidor na porta com o MESMO modelo → reutiliza.
      2. Se houver com OUTRO modelo → pergunta: encerrar e iniciar o escolhido,
         usar o atual mesmo assim, ou cancelar.
      3. Se não houver servidor → abre nova janela de console (logs do
         llama-server visíveis) e aguarda o /v1/models responder.

    Returns:
        dict com os dados do primeiro modelo de /v1/models.

    Raises:
        SystemExit em falhas fatais (exe não encontrado, timeout, cancelamento).
    """
    if modelo not in MODELOS_HF:
        raise SystemExit(
            f"Modelo desconhecido para o llama-server: '{modelo}'. "
            f"Opções: {', '.join(sorted(MODELOS_HF))}."
        )

    cfg = _config_servidor()
    esperado = _familia_esperada(modelo)
    ativo = _obter_modelo_ativo(cfg["base_url"])

    if ativo:
        atual = _detectar_familia(ativo)
        if atual == esperado:
            print(
                f"Servidor já ativo em {cfg['base_url']} com o modelo escolhido. "
                "Reutilizando."
            )
            return ativo

        print()
        print("Já existe um llama-server ativo, mas com OUTRO modelo carregado:")
        print(f"  ativo:     {ativo.get('id') or 'desconhecido'}")
        print(f"  escolhido: {MODELOS_HF[modelo]}")
        escolha = input(
            "O que fazer? [1] encerrar e iniciar o escolhido, "
            "[2] usar o atual mesmo assim, [3] cancelar: "
        ).strip()
        if escolha == "2":
            print("Usando o servidor já ativo (modelo pode divergir do escolhido).")
            return ativo
        if escolha == "3":
            raise SystemExit("Avaliação cancelada pelo usuário.")
        print("Encerrando o servidor atual para iniciar com o modelo escolhido...")
        _encerrar_servidor_na_porta(cfg)
        _abrir_janela_servidor(cfg, modelo)
        ativo = _aguardar_servidor(cfg)
    else:
        if not cfg["exe"]:
            raise SystemExit(
                "llama-server.exe não encontrado. Configure LLAMA_SERVER_EXE com o "
                "caminho completo (ex.: C:\\...\\llama-bXXXX-bin-win-cpu-x64\\llama-server.exe) "
                "ou baixe o llama.cpp em ~/Documents/llama_cpp."
            )
        _abrir_janela_servidor(cfg, modelo)
        ativo = _aguardar_servidor(cfg)

    # Conferência final: o servidor subiu com o modelo certo?
    carregado = _detectar_familia(ativo)
    if carregado != esperado:
        raise SystemExit(
            f"O llama-server respondeu, mas o modelo carregado não é o escolhido "
            f"(esperado {esperado}, detectado {carregado or 'desconhecido'}). "
            "Feche a janela do llama-server e tente novamente."
        )
    return ativo



