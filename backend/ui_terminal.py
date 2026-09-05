#!/usr/bin/env python3
"""
MARIA — Interface de Terminal (UI).

Responsabilidades:
    - Exibir banner artístico com imagem
    - Gerenciar o loop de interação com o usuário
    - Processar comandos especiais (ajuda, limpar, retomar, sair)
    - Exibir respostas em streaming
    - Delegar lógica de negócio ao controller (main.py)

Uso:
    python main.py
"""

import argparse
import os
import shutil
import sys
import textwrap

# ───────────────────────────────────────────────────────────────
# Paleta de cores
# ───────────────────────────────────────────────────────────────
TEAL = (64, 224, 208)
TEAL_SUAVE = (42, 160, 150)
ROSA = (255, 45, 120)
VERDE = (140, 255, 210)
CINZA = (150, 180, 178)
PRETO = (12, 12, 12)
RESET = "\033[0m"

ESCALA_LOGO = 1.20
ESCALA_ROSTO = 1.30

FONTE = {
    "M": ["10001", "11011", "10101", "10001", "10001", "10001", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
}

DESCRICAO = (
    "MARIA é uma assistente de IA de escritório que trabalha com você "
    "de forma inteligente e local, garantindo privacidade, agilidade e "
    "resultados reais no seu dia a dia."
)

FUNCIONALIDADES = [
    ("▣", "PRIVADO", "Seus dados ficam apenas com você. Sem envio para a nuvem."),
    ("▤", "CRIA E EDITA", "Planilhas Excel, documentos Word e muito mais."),
    ("▧", "INTELIGENTE", "Respostas objetivas, sem alucinações. Focada em ajudar."),
    ("↯", "EFICIENTE", "Mais agilidade nas tarefas do dia a dia. Mais tempo para o que importa."),
]


# ═══════════════════════════════════════════════════════════════
# Funções utilitárias de cor e renderização
# ═══════════════════════════════════════════════════════════════

def rgb(cor, texto):
    return f"\033[38;2;{cor[0]};{cor[1]};{cor[2]}m{texto}{RESET}"


def rgb2(fg, bg, texto):
    return (
        f"\033[38;2;{fg[0]};{fg[1]};{fg[2]}m"
        f"\033[48;2;{bg[0]};{bg[1]};{bg[2]}m{texto}{RESET}"
    )


def lum(r, g, b):
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def eh_rosa(r, g, b):
    return r > 120 and (r - g) > 50 and (b - g) > 20


def cor_pixel(r, g, b):
    if eh_rosa(r, g, b):
        return ROSA
    l = lum(r, g, b) ** 0.85
    return (int(TEAL[0] * l), int(TEAL[1] * l), int(TEAL[2] * l))


def _pares(segs):
    if isinstance(segs, str):
        return [(TEAL, segs)]
    pares = []
    for item in segs:
        if isinstance(item, str):
            pares.append((TEAL, item))
        elif isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], tuple):
            pares.append(item)
        elif isinstance(item, tuple) and len(item) == 3 and all(isinstance(v, int) for v in item):
            pares.append((item, ""))
        else:
            raise TypeError(f"Segmento inválido no painel: {item!r}")
    return pares


def largura_seg(segs):
    return sum(len(t) for _, t in _pares(segs))


def render_seg(segs, pad=None):
    pares = _pares(segs)
    if pad is not None:
        vis = sum(len(t) for _, t in pares)
        if vis < pad:
            pares = pares + [(TEAL, " " * (pad - vis))]
    return "".join(rgb(c, t) for c, t in pares)


def render_logo(glifo="M"):
    brutas = []
    for r in range(7):
        linha = ""
        for letra in "MARIA":
            mapa = FONTE[letra][r]
            linha += "".join((glifo * 2) if c == "1" else "  " for c in mapa) + "  "
        linha = " " * ((6 - r) // 2) + linha
        brutas.append(linha)
    segs = []
    for r, linha in enumerate(brutas):
        if r == 5 and len(linha) > 20:
            pos = 16 + ((6 - r) // 2)
            segs.append([(TEAL, linha[:pos]), (ROSA, "●"), (TEAL, linha[pos + 1:])])
        else:
            segs.append([(TEAL, linha)])
    return segs


def montar_funcionalidades():
    LARG = 12
    colunas = []
    for icone, titulo, desc in FUNCIONALIDADES:
        bloco = [icone.center(LARG), titulo.center(LARG), " " * LARG]
        for t in textwrap.wrap(desc, LARG):
            bloco.append(t.center(LARG))
        colunas.append(bloco)
    altura = max(len(c) for c in colunas)
    for c in colunas:
        while len(c) < altura:
            c.append(" " * LARG)
    corpo = []
    for i in range(altura):
        corpo.append("│ " + " │ ".join(c[i] for c in colunas) + " │")
    interno = len(corpo[0]) - 2
    topo = "┌" + " FUNCIONALIDADES " + "─" * max(0, interno - 18) + "┐"
    base = "└" + "─" * interno + "┘"
    resultado = []
    for linha in [topo] + corpo + [base]:
        resultado.append((TEAL_SUAVE, linha))
    return resultado


def painel_texto():
    L = []
    L.append([(TEAL, "─" * 56)])
    L.append([(TEAL, "")])
    L.append([(TEAL, "SUA ASSISTENTE LOCAL, SEUS DADOS NO SEU ESCRITÓRIO.")])
    L.append([(TEAL, "")])
    for texto in textwrap.wrap(DESCRICAO, 50):
        L.append([(TEAL, "│ "), (TEAL_SUAVE, texto)])
    L.append([(TEAL, "")])
    L += montar_funcionalidades()
    return L


def _halfblock(img, colunas, linhas_max=None, mono=False):
    A = img.width / img.height
    R = max(4, round(colunas / A / 2))
    if linhas_max:
        R = min(R, linhas_max)
    C = max(4, min(colunas, round(2 * R * A)))
    nh = 2 * R
    img = img.resize((C, nh))
    px = img.load()
    rows = []
    for y in range(0, nh, 2):
        parts = []
        for x in range(C):
            r1, g1, b1 = px[x, y]
            r2, g2, b2 = px[x, y + 1]
            if mono:
                l1 = lum(r1, g1, b1)
                l2 = lum(r2, g2, b2)
                if l1 < 0.10 and l2 < 0.10:
                    parts.append(" ")
                else:
                    c1 = ROSA if eh_rosa(r1, g1, b1) else (TEAL if l1 > 0.10 else PRETO)
                    c2 = ROSA if eh_rosa(r2, g2, b2) else (TEAL if l2 > 0.10 else PRETO)
                    parts.append(rgb2(c1, c2, "▀"))
            else:
                l1 = lum(r1, g1, b1)
                l2 = lum(r2, g2, b2)
                if l1 < 0.03 and l2 < 0.03:
                    parts.append(" ")
                else:
                    c1 = cor_pixel(r1, g1, b1)
                    c2 = cor_pixel(r2, g2, b2)
                    parts.append(rgb2(c1, c2, "▀"))
        rows.append("".join(parts))
    return rows, C


def eh_banner_largo(img):
    return img.width / img.height > 1.4


def logo_ascii(caminho, colunas, mono):
    from PIL import Image
    img = Image.open(caminho).convert("RGB")
    if not eh_banner_largo(img):
        return [], 0
    w, h = img.size
    rec = img.crop((0, int(h * 0.03), int(w * 0.52), int(h * 0.33)))
    return _halfblock(rec, colunas, mono=mono)


def rosto_ascii(caminho, largura_max, altura_max, mono):
    from PIL import Image
    img = Image.open(caminho).convert("RGB")
    if eh_banner_largo(img):
        w, h = img.size
        img = img.crop((int(w * 0.55), 0, w, int(h * 0.90)))
    return _halfblock(img, largura_max, linhas_max=altura_max, mono=mono)


def combinar(esq, dir_linhas, larg_esq, sep=3):
    saida = []
    for i in range(max(len(esq), len(dir_linhas))):
        if i < len(esq):
            rendered, vis = esq[i]
            es = rendered + " " * max(0, larg_esq - vis)
        else:
            es = " " * larg_esq
        dr = dir_linhas[i] if i < len(dir_linhas) else ""
        saida.append(es + " " * sep + dr)
    return saida


def exibir_banner(imagem=None, glifo="M", mono=False):
    t = shutil.get_terminal_size((120, 30))

    tem_img = bool(imagem)
    if tem_img and not os.path.exists(imagem):
        print(f"Imagem não encontrada: {imagem} — exibindo apenas o painel de texto.")
        tem_img = False
    if tem_img:
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            print("Para desenhar logo/rosto, instale o Pillow: pip install pillow")
            tem_img = False

    logo_rows, logo_w = [], 0
    if tem_img:
        try:
            logo_rows, logo_w = logo_ascii(imagem, int(54 * ESCALA_LOGO), mono)
        except Exception as e:
            print(f"Aviso: não foi possível processar o logo da imagem ({e}).")
            logo_rows, logo_w = [], 0

    texto = painel_texto()
    larg_texto = max(largura_seg(s) for s in texto)
    larg_esq = max(logo_w, larg_texto)

    esq = []
    if logo_rows:
        for row in logo_rows:
            esq.append((row, logo_w))
        esq.append(("", 0))
    else:
        for segs in render_logo(glifo):
            esq.append((render_seg(segs), largura_seg(segs)))
        esq.append(("", 0))
    for segs in texto:
        esq.append((render_seg(segs, pad=larg_esq), larg_esq))

    rosto = []
    if tem_img:
        alt_face = int(max(t.lines - 6, 32) * ESCALA_ROSTO)
        base_face = max(t.columns - larg_esq - 3, 40)
        larg_face = min(int(base_face * ESCALA_ROSTO), t.columns - larg_esq - 3, 132)
        rosto, _ = rosto_ascii(imagem, larg_face, alt_face, mono)

    if rosto:
        for linha in combinar(esq, rosto, larg_esq):
            print(linha)
    else:
        for rendered, _vis in esq:
            print(rendered)

    print()
    print(rgb(TEAL, "─" * t.columns))
    print(rgb(TEAL_SUAVE, "MARIA CLI v1.0.0"))
    print(rgb(CINZA, "Comandos: 'ajuda' | 'limpar' | 'retomar' | 'sair'"))
    print(rgb(ROSA, "maria") + rgb(VERDE, "@assistente") + rgb(TEAL, ":~$ _"))


# ═══════════════════════════════════════════════════════════════
# Modo de avaliação de desempenho (menu integrado ao fluxo principal)
# ═══════════════════════════════════════════════════════════════

def _coletar_metricas_sistema() -> dict:
    """Coleta snapshot de CPU, RAM e GPU antes do warmup."""
    import datetime
    import platform

    import psutil

    mem = psutil.virtual_memory()
    cpu_freq = psutil.cpu_freq()
    dados = {
        "timestamp": datetime.datetime.now().isoformat(),
        "plataforma": platform.platform(),
        "cpu_modelo": platform.processor(),
        "cpu_nucleos_fisicos": psutil.cpu_count(logical=False),
        "cpu_nucleos_logicos": psutil.cpu_count(logical=True),
        "cpu_freq_mhz": round(cpu_freq.current, 1) if cpu_freq else None,
        "cpu_uso_percent": psutil.cpu_percent(interval=0.5),
        "ram_total_gb": round(mem.total / 1024**3, 2),
        "ram_disponivel_gb": round(mem.available / 1024**3, 2),
        "ram_uso_percent": mem.percent,
        "gpu": [],
    }
    try:
        import pynvml
        pynvml.nvmlInit()
        contagem = pynvml.nvmlDeviceGetCount()
        for i in range(contagem):
            h = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem_gpu = pynvml.nvmlDeviceGetMemoryInfo(h)
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            dados["gpu"].append({
                "nome": pynvml.nvmlDeviceGetName(h),
                "vram_total_gb": round(mem_gpu.total / 1024**3, 2),
                "vram_livre_gb": round(mem_gpu.free / 1024**3, 2),
                "gpu_uso_percent": util.gpu,
                "vram_uso_percent": util.memory,
            })
        pynvml.nvmlShutdown()
    except Exception:
        pass  # sem GPU NVIDIA ou pynvml não instalado
    return dados


def _caixa(titulo: str, linhas: list[str], largura: int | None = None) -> None:
    """Desenha uma caixa teal com título no topo e linhas alinhadas.

    `linhas` são os textos internos SEM bordas. A largura da área útil é
    derivada do maior conteúdo (ou `largura`, quando informada), garantindo
    que todas as bordas fechem no mesmo caractere.
    """
    largura_util = largura or max([len(t) for t in linhas] + [len(titulo) + 2])
    base_topo = f"─ {titulo} " if titulo else "─"
    topo_interno = base_topo + "─" * max(0, largura_util - len(base_topo))
    print(rgb(TEAL, "┌" + topo_interno + "┐"))
    for texto in linhas:
        print(rgb(TEAL, "│") + texto.ljust(largura_util) + rgb(TEAL, "│"))
    print(rgb(TEAL, "└" + "─" * largura_util + "┘"))


def _menu_modo() -> str:
    """
    Exibe menu de modo e retorna 'chat' ou 'avaliacao'.
    Fica em loop até entrada válida.
    """
    opcoes = {"1": "chat", "2": "avaliacao"}
    while True:
        print()
        _caixa("MODO DE OPERAÇÃO", ["  1. Chat", "  2. Avaliação de Desempenho"])
        escolha = input(rgb(CINZA, "Escolha [1/2]: ")).strip()
        if escolha in opcoes:
            return opcoes[escolha]
        print(rgb(ROSA, "Opção inválida. Digite 1 ou 2."))


def _menu_avaliacao() -> dict:
    """
    Exibe menus de modelo e tarefas para a Avaliação de Desempenho.
    Retorna dict com chaves: modelo (str), task_ids (list[int] | None), repeticoes (int).
    """
    # --- Escolha de modelo ---
    modelos = {"1": "qwen2.5-omni-3b", "2": "qwen2.5-omni-7b"}
    while True:
        print()
        _caixa("MODELO", [
            "  1. Qwen2.5-Omni 3B  (rápido, ~2,3 GB)",
            "  2. Qwen2.5-Omni 7B  (preciso, ~4,5 GB)",
        ])
        escolha = input(rgb(CINZA, "Escolha [1/2]: ")).strip()
        if escolha in modelos:
            modelo = modelos[escolha]
            break
        print(rgb(ROSA, "Opção inválida. Digite 1 ou 2."))

    # --- Escolha de tarefas ---
    from backend.benchmark.tasks import load_all_maria_tasks
    todas = load_all_maria_tasks()
    print()
    linhas_tarefas = [f"  0. Todas as tarefas ({len(todas)} tarefas)"]
    for t in todas:
        linhas_tarefas.append(f"  {t.id:2d}. [{t.category.value}] {t.name}")
    _caixa("TAREFAS", linhas_tarefas)
    print(rgb(CINZA, "Digite IDs separados por espaço, ou 0 para todas (ex: 1 3 5):"))
    entrada_ids = input(rgb(CINZA, "IDs: ")).strip()

    task_ids = None
    if entrada_ids and entrada_ids != "0":
        try:
            task_ids = [int(x) for x in entrada_ids.split()]
        except ValueError:
            print(rgb(ROSA, "Entrada inválida. Usando todas as tarefas."))
            task_ids = None

    # --- Repetições ---
    from backend.benchmark.benchmark_config import BENCHMARK_REPETICOES
    while True:
        print()
        entrada_rep = input(
            rgb(CINZA, f"Repetições por tarefa [{BENCHMARK_REPETICOES}]: ")
        ).strip()
        if not entrada_rep:
            repeticoes = BENCHMARK_REPETICOES
            break
        try:
            repeticoes = int(entrada_rep)
            if repeticoes > 0:
                break
            print(rgb(ROSA, "Digite um número maior que zero."))
        except ValueError:
            print(rgb(ROSA, "Valor inválido."))

    return {"modelo": modelo, "task_ids": task_ids, "repeticoes": repeticoes}


def _executar_avaliacao(config: dict, metricas_sistema: dict):
    """
    Chama run_benchmark_programatico() com os parâmetros escolhidos no menu.
    Trata SystemExit (erros fatais do benchmark, ex: llama-server offline).
    """
    try:
        from backend.benchmark.run_benchmark import run_benchmark_programatico
        run_benchmark_programatico(
            modelo=config["modelo"],
            task_ids=config["task_ids"],
            repeticoes=config["repeticoes"],
            metricas_sistema=metricas_sistema,
        )
    except SystemExit as e:
        print(rgb(ROSA, f"\n[ERRO] {e}"))
    except KeyboardInterrupt:
        print(rgb(ROSA, "\nAvaliação interrompida pelo usuário."))
    except Exception as e:
        print(rgb(ROSA, f"\n[ERRO inesperado] {e}"))


# ═══════════════════════════════════════════════════════════════
# Interface Terminal — loop de interação
# ═══════════════════════════════════════════════════════════════

class InterfaceTerminal:
    """
    Gerencia toda a interação com o usuário via terminal.
    Delega a lógica de negócio para um controller.
    """

    def __init__(self, controller, imagem_banner="maria_opening.png"):
        """
        Args:
            controller: objeto com a interface definida em main.py (MariaController)
            imagem_banner: caminho para a imagem do banner
        """
        self.controller = controller
        self.imagem_banner = imagem_banner

    # ── Exibição ──────────────────────────────────────────────

    def mostrar_ajuda(self):
        print("\n--- Comandos Disponíveis ---")
        print("  ajuda    - Mostra esta mensagem de ajuda")
        print("  limpar   - Limpa o histórico da conversa")
        print("  retomar  - Retoma uma conversa salva de uma execução anterior")
        print("  sair     - Encerra a aplicação")
        print("  exit     - Encerra a aplicação (alternativo)")
        print("-" * 30)
        print("\nDica: você pode pedir em linguagem natural, como")
        print("  'crie uma planilha de gastos' ou")
        print("  'crie um documento com uma carta de apresentação'.")
        print("A MARIA identificará automaticamente e perguntará antes de criar.\n")

    def exibir_prompt(self):
        t = shutil.get_terminal_size((120, 30))
        print()
        print(rgb(TEAL, "─" * t.columns))
        print(rgb(TEAL_SUAVE, "MARIA CLI v1.0.0"))
        print(rgb(CINZA, "Digite 'ajuda' para ver os comandos disponíveis."))
        print(rgb(ROSA, "maria") + rgb(VERDE, "@assistente") + rgb(TEAL, ":~$ "), end="")

    # ── Comandos ──────────────────────────────────────────────

    def _processar_comando(self, entrada: str) -> bool:
        """
        Processa comandos especiais.
        Retorna True se o loop deve ser encerrado.
        """
        cmd = entrada.lower()

        if cmd in ("sair", "exit"):
            print("\nEncerrando MARIA. Até logo!")
            return True

        if cmd == "ajuda":
            self.mostrar_ajuda()
            return False

        if cmd == "limpar":
            self.controller.limpar_historico()
            print("\nHistórico da conversa limpo!")
            return False

        if cmd == "retomar":
            self._retomar_sessao()
            return False

        return False  # não era comando especial conhecido

    def _retomar_sessao(self):
        """Interage com o usuário para retomar uma sessão salva."""
        if self.controller.tem_acao_pendente():
            self.controller.limpar_acao_pendente()
            print("\nAção pendente cancelada para retomar outra sessão.")

        sessoes = self.controller.listar_sessoes()
        if not sessoes:
            print("\nNenhuma sessão salva encontrada.")
            return

        print("\n--- Sessões salvas (mais recentes primeiro) ---")
        for indice, info in enumerate(sessoes, start=1):
            print(f"  {indice}. {info['nome_arquivo']} ({info['qtd_mensagens']} mensagens)")

        escolha = input("Digite o número da sessão para retomar (ou Enter para cancelar): ").strip()
        if not escolha:
            print("\nRetomada cancelada.")
            return

        try:
            indice = int(escolha)
            sucesso, msg = self.controller.retomar_sessao(indice)
            print(f"\n{msg}")
        except (ValueError, IndexError):
            print("\nSeleção inválida. Retomada cancelada.")

    # ── Processamento de mensagens ────────────────────────────

    def _processar_mensagem_normal(self, entrada: str):
        """Envia mensagem para o modelo e exibe resposta em streaming."""
        print("\nMARIA: ", end="", flush=True)

        stream = self.controller.enviar_mensagem(entrada)
        for chunk, tool_chunk in stream:
            if chunk is not None:
                print(chunk, end="", flush=True)
            self.controller.processar_chunk(chunk, tool_chunk)
        print()

        tem_tool, info = self.controller.finalizar_mensagem()
        if tem_tool:
            print(self.controller.get_mensagem_confirmacao())

    def _processar_confirmacao(self, entrada: str):
        """Processa resposta de confirmação de uma ação pendente."""
        status, msg = self.controller.processar_confirmacao(entrada)

        if status is True:
            print(f"\n[SISTEMA] {msg}")
        elif status is False:
            print(f"\n{msg}")
        else:  # None = ambíguo
            print(f"\n{msg}")

    # ── Loop principal ────────────────────────────────────────

    def iniciar(self):
        """Ponto de entrada da interface. Exibe banner e entra no loop."""
        # Configurar encoding UTF-8 (Windows)
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

        # Exibir banner (sem inicializar o modelo ainda)
        exibir_banner(imagem=self.imagem_banner)

        # Menu de modo
        modo = _menu_modo()

        if modo == "avaliacao":
            config_aval = _menu_avaliacao()
            metricas_sistema = _coletar_metricas_sistema()
            print()
            print(rgb(TEAL, "Iniciando Avaliação de Desempenho..."))
            print(rgb(CINZA, f"Modelo: {config_aval['modelo']}"))
            _executar_avaliacao(config_aval, metricas_sistema)
            return

        # Modo chat: fluxo original a partir daqui
        try:
            self.controller.inicializar()
        except Exception as e:
            print(f"\n[ERRO] Falha ao inicializar: {e}")
            return

        print("\nOlá! Eu sou a MARIA, sua assistente de escritório.")
        print("Rodando 100% localmente no seu computador, sem internet.\n")

        print("Aquecendo o modelo, aguarde um instante...")
        self.controller.aquecer_modelo()

        print("Como posso ajudar você hoje?")

        # Loop de chat
        while True:
            try:
                self.exibir_prompt()
                entrada = input().strip()

                if not entrada:
                    continue

                # Comandos especiais (funcionam mesmo com ação pendente)
                if self._processar_comando(entrada):
                    break
                # Se _processar_comando retornou False, pode ter sido um comando
                # reconhecido (ajuda, limpar, retomar) ou não. Precisamos verificar
                # se a entrada era de fato um comando conhecido.
                # Mas como os comandos são verificados por lower() exato,
                # uma mensagem normal não bate. No entanto, precisamos de uma
                # forma de saber se foi tratado. Vamos verificar novamente.
                if entrada.lower() in ("ajuda", "limpar", "retomar"):
                    continue

                # Ação pendente → confirmação
                if self.controller.tem_acao_pendente():
                    self._processar_confirmacao(entrada)
                    continue

                # Mensagem normal
                self._processar_mensagem_normal(entrada)

            except KeyboardInterrupt:
                print("\n\nInterrupção detectada. Digite 'sair' para encerrar ou continue digitando.")
                continue
            except EOFError:
                print("\n\nFim de arquivo detectado. Encerrando.")
                break

        print("\nObrigado por usar MARIA!\n")
        self.controller.finalizar()


# ═══════════════════════════════════════════════════════════════
# Ponto de entrada standalone (para testar o banner isoladamente)
# ═══════════════════════════════════════════════════════════════

def _main_standalone():
    ap = argparse.ArgumentParser(description="Banner da MARIA no terminal.")
    ap.add_argument("--imagem", default="maria_opening.png",
                    help="Caminho da imagem (padrão: maria_opening.png)")
    ap.add_argument("--glifo", default="M", help="Glifo do logo fallback (padrão: M)")
    ap.add_argument("--mono", action="store_true", help="Teal sólido (sem truecolor)")
    args = ap.parse_args()
    exibir_banner(imagem=args.imagem, glifo=args.glifo, mono=args.mono)


if __name__ == "__main__":
    _main_standalone()