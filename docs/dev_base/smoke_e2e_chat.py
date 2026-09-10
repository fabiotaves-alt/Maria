"""
Smoke test E2E do chat real — replica os 6 itens do B0.9 (CHANGELOG 2026-09-08).

Requer llama-server rodando em LLAMA_BASE_URL (padrão http://localhost:8080).
Executa o fluxo real do MariaController (chat → tool call → confirmação → escrita).

Uso (a partir da raiz do monorepo):
    $env:PYTHONUTF8='1'
    uv run python docs/dev_base/smoke_e2e_chat.py

Os testes multimodais (visão/áudio) foram movidos para smoke_multimodal.py.

Itens validados (B0.9 — funcionais):
    1. Carga do modelo (GET /v1/models + aquecimento)
    2. criar_planilha real (fluxo completo: pedido → ação pendente → confirmação → .xlsx)
    3. Validador V3 (case-insensitive) — colunas e dados no .xlsx sem NaN
    4. Fluxo de confirmação (mensagem amigável com "Posso seguir")
    5. Cancelamento ("não" → "Ação cancelada." e nenhum arquivo novo)
    6. Tool call detectada (name + arguments; _fonte reportado como info)
"""

import glob
import os
import sys
from datetime import datetime
from pathlib import Path

# Garantir que a raiz do monorepo esteja no sys.path (docs/dev_base → raiz = 2 níveis acima)
_RAIZ = str(Path(__file__).resolve().parent.parent.parent)
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

import requests  # noqa: E402

from backend.application.maria_controller import MariaController  # noqa: E402
from backend.config import LLAMA_BASE_URL, LLAMA_MODEL  # noqa: E402

PASTA_GERADOS = os.getenv("PASTA_ARQUIVOS_GERADOS", "arquivos_gerados")

_resultados: list[tuple[str, bool, str]] = []


def _ok(item: str, msg: str = "") -> None:
    _resultados.append((item, True, msg))
    print(f"  [OK]   {item}" + (f" — {msg}" if msg else ""))


def _fail(item: str, msg: str) -> None:
    _resultados.append((item, False, msg))
    print(f"  [FALHA] {item} — {msg}")


def _info(msg: str) -> None:
    print(f"  [info] {msg}")


def _arquivos_planilha() -> set[str]:
    return set(glob.glob(os.path.join(PASTA_GERADOS, "*.xlsx")))


def _rodar_turno(controller: MariaController, mensagem: str) -> tuple[str, dict | None]:
    """Roda um turno completo de chat e retorna (texto, tool_call_final)."""
    for chunk, tool_chunk in controller.enviar_mensagem(mensagem):
        controller.processar_chunk(chunk, tool_chunk)
    tem_pendente, tool_call = controller.finalizar_mensagem()
    return controller._resposta_textual, (tool_call if tem_pendente else None)


def item_1_modelo() -> None:
    print("\n[1] Carga do modelo multimodal")
    try:
        r = requests.get(f"{LLAMA_BASE_URL}/v1/models", timeout=10)
        if r.status_code != 200:
            _fail("1. Modelo acessível", f"status {r.status_code}")
            return
        modelos = [m.get("id", "") for m in r.json().get("data", [])]
        if not modelos:
            _fail("1. Modelo acessível", "lista vazia")
            return
        _ok("1. Modelo acessível", f"{modelos[0]}")
    except Exception as e:
        _fail("1. Modelo acessível", f"conexão falhou: {e}")


def item_2_3_4_6_criar_planilha(controller: MariaController) -> str | None:
    """Itens 2 (criar_planilha), 3 (V3), 4 (confirmação) e 6 (parser JSON)."""
    print("\n[2-6] criar_planilha real + validador V3 + confirmação + parser JSON")
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_alvo = f"gastos_smoke_{marca}"

    before = _arquivos_planilha()

    texto, tool_call = _rodar_turno(
        controller,
        f"Crie uma planilha Excel chamada {nome_alvo} com as colunas Data e Valor "
        f"e adicione uma linha com Data igual a 2026-01-01 e Valor igual a 100.",
    )

    if tool_call is None:
        _fail("2. criar_planilha real", "modelo não emitiu tool call (resposta textual apenas)")
        _info(f"Texto recebido: {texto[:200]!r}")
        return None

    fonte = tool_call.get("_fonte", "")
    if fonte:
        _info(f"_fonte do parser: {fonte!r}")
    if tool_call.get("name") and isinstance(tool_call.get("arguments"), dict):
        _ok("6. Tool call detectada", f"name={tool_call.get('name')!r}")
    else:
        _fail("6. Tool call detectada", "tool call sem name/arguments válidos")

    if tool_call.get("name") != "criar_planilha":
        _fail("2. criar_planilha real", f"ferramenta errada: {tool_call.get('name')!r}")
        return None

    mensagem = controller.get_mensagem_confirmacao()
    if "Posso seguir" in mensagem and nome_alvo in mensagem:
        _ok("4. Fluxo de confirmação", mensagem.splitlines()[0][:80])
    else:
        _fail("4. Fluxo de confirmação", f"mensagem inesperada: {mensagem[:120]!r}")

    args = tool_call.get("arguments", {})
    linhas = args.get("linhas") or []
    if linhas and isinstance(linhas[0], dict):
        chaves = list(linhas[0].keys())
        if {c.lower() for c in chaves} >= {"data", "valor"}:
            _ok("3. Validador V3 (case-insensitive)", f"chaves normalizadas: {chaves}")
        else:
            _info(f"V3: chaves da linha: {chaves} (conferir após execução)")

    executou, resposta = controller.processar_confirmacao("sim")
    if executou is not True:
        _fail("2. criar_planilha real", f"confirmação não executou: {resposta[:120]!r}")
        return None

    novos = _arquivos_planilha() - before
    if not novos:
        _fail("2. criar_planilha real", f"nenhum .xlsx novo em {PASTA_GERADOS}/")
        return None

    caminho = sorted(novos)[0]
    _ok("2. criar_planilha real", Path(caminho).name)
    return caminho


def item_3_conteudo_xlsx(caminho: str) -> None:
    """Item 3 (concluído no arquivo): colunas Data/Valor e dados sem NaN."""
    print("\n[3] Conteúdo do .xlsx (fidelidade de dados)")
    try:
        import pandas as pd

        df = pd.read_excel(caminho)
        colunas = [str(c).strip() for c in df.columns]
        if colunas != ["Data", "Valor"]:
            _fail("3. Conteúdo do .xlsx", f"colunas: {colunas}")
            return
        if df.empty:
            _fail("3. Conteúdo do .xlsx", "planilha sem linhas de dados")
            return
        if df.isnull().values.any():
            _fail("3. Conteúdo do .xlsx", "existem células vazias (NaN)")
            return
        _ok("3. Conteúdo do .xlsx", f"colunas {colunas}; primeira linha: {df.iloc[0].to_dict()}")
    except Exception as e:
        _fail("3. Conteúdo do .xlsx", f"erro ao ler: {e}")


def item_5_cancelamento(controller: MariaController) -> None:
    print("\n[5] Cancelamento ('não')")
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    before = _arquivos_planilha()

    _, tool_call = _rodar_turno(
        controller,
        f"Crie uma planilha Excel chamada cancelar_smoke_{marca} com a coluna Item.",
    )
    if tool_call is None:
        _fail("5. Cancelamento", "modelo não emitiu tool call (não dá para testar cancelamento)")
        return

    resultado, resposta = controller.processar_confirmacao("não")
    if resultado is not False:
        _fail("5. Cancelamento", f"resultado inesperado: {resultado!r} — {resposta[:120]!r}")
        return
    if "cancelada" not in resposta.lower():
        _fail("5. Cancelamento", f"mensagem inesperada: {resposta[:120]!r}")
        return

    novos = _arquivos_planilha() - before
    if novos:
        _fail("5. Cancelamento", f"arquivo criado mesmo com cancelamento: {novos}")
        return
    _ok("5. Cancelamento", "Ação cancelada., sem arquivo novo")


def main() -> None:
    print("=== Smoke E2E do chat real (B0.9) ===")
    print(f"URL: {LLAMA_BASE_URL}  |  Modelo: {LLAMA_MODEL}")

    item_1_modelo()
    if any(not ok for _, ok, _ in _resultados):
        print("\n[ABORTADO] Servidor inacessível. Verifique o llama-server.")
        sys.exit(1)

    controller = MariaController()
    controller.inicializar()
    _info("Aquecendo o modelo...")
    controller.aquecer_modelo()

    caminho = item_2_3_4_6_criar_planilha(controller)
    if caminho:
        item_3_conteudo_xlsx(caminho)
    item_5_cancelamento(controller)

    passou = sum(1 for _, ok, _ in _resultados if ok)
    total = len(_resultados)
    print(f"\n=== Resultado: {passou}/{total} itens passaram ===")
    for item, ok, msg in _resultados:
        status = "OK   " if ok else "FALHA"
        detalhe = f" — {msg}" if msg and not ok else ""
        print(f"  [{status}] {item}{detalhe}")

    sys.exit(0 if passou == total else 1)


if __name__ == "__main__":
    main()
