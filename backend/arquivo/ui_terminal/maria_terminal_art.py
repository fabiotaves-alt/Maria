#!/usr/bin/env python3
"""
MARIA — Logo e rosto no terminal (half-block truecolor + rosa reforçado).

Uso:
    python maria_terminal_art.py                      # usa maria_face.png, se existir
    python maria_terminal_art.py --imagem outra.png
    python maria_terminal_art.py --mono               # âmbar sólido (sem truecolor)

Dependência opcional (apenas para logo/rosto):
    pip install pillow
"""

import argparse
import os
import shutil
import textwrap

AMBAR = (255, 176, 0)
AMBAR_SUAVE = (214, 150, 50)
ROSA = (255, 45, 120)
VERDE = (140, 255, 120)
CINZA = (170, 170, 170)
PRETO = (12, 12, 12)
RESET = "\033[0m"

# Escalas de tamanho (1.0 = original)
ESCALA_LOGO = 1.20   # logo 20% maior
ESCALA_ROSTO = 1.10  # rosto 10% maior

FONTE = {
    "M": ["10001", "11011", "10101", "10001", "10001", "10001", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
}

DESCRICAO = ("MARIA é uma assistente de IA de escritório que trabalha com você "
             "de forma inteligente e local, garantindo privacidade, agilidade e "
             "resultados reais no seu dia a dia.")

FUNCIONALIDADES = [
    ("▣", "PRIVADO", "Seus dados ficam apenas com você. Sem envio para a nuvem."),
    ("▤", "CRIA E EDITA", "Planilhas Excel, documentos Word e muito mais."),
    ("▧", "INTELIGENTE", "Respostas objetivas, sem alucinações. Focada em ajudar."),
    ("↯", "EFICIENTE", "Mais agilidade nas tarefas do dia a dia. Mais tempo para o que importa."),
]


def rgb(cor, texto):
    return f"\033[38;2;{cor[0]};{cor[1]};{cor[2]}m{texto}{RESET}"


def rgb2(fg, bg, texto):
    return (f"\033[38;2;{fg[0]};{fg[1]};{fg[2]}m"
            f"\033[48;2;{bg[0]};{bg[1]};{bg[2]}m{texto}{RESET}")


def lum(r, g, b):
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def eh_rosa(r, g, b):
    """Detecta pixels rosados/magenta (o acento de cor do banner)."""
    return r > 120 and (r - g) > 50 and (b - g) > 20


def cor_pixel(r, g, b):
    """Truecolor, mas pixels rosados viram o rosa forte do painel."""
    if eh_rosa(r, g, b):
        return ROSA
    return (r, g, b)


def _pares(segs):
    if isinstance(segs, str):
        return [(AMBAR, segs)]
    pares = []
    for item in segs:
        if isinstance(item, str):
            pares.append((AMBAR, item))
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
            pares = pares + [(AMBAR, " " * (pad - vis))]
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
            segs.append([(AMBAR, linha[:pos]), (ROSA, "●"), (AMBAR, linha[pos + 1:])])
        else:
            segs.append([(AMBAR, linha)])
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
        resultado.append((AMBAR_SUAVE, linha))
    return resultado


def painel_texto():
    L = []
    L.append([(AMBAR, "─" * 56)])
    L.append([(AMBAR, "")])
    L.append([(AMBAR, "SUA ASSISTENTE. SEU ESCRITÓRIO. SUA PRODUTIVIDADE.")])
    L.append([(AMBAR, "")])
    for texto in textwrap.wrap(DESCRICAO, 50):
        L.append([(AMBAR, "│ "), (AMBAR_SUAVE, texto)])
    L.append([(AMBAR, "")])
    L += montar_funcionalidades()
    return L


def _halfblock(img, colunas, linhas_max=None, mono=False):
    """Half-block truecolor (2 pixels por célula), com rosa reforçado."""
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
                    c1 = ROSA if eh_rosa(r1, g1, b1) else (AMBAR if l1 > 0.10 else PRETO)
                    c2 = ROSA if eh_rosa(r2, g2, b2) else (AMBAR if l2 > 0.10 else PRETO)
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

    # Logo: 20% maior (54 -> ~65 colunas)
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

    # Rosto: 10% maior (altura e largura), limitado pela largura do terminal
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
    print(rgb(AMBAR, "─" * t.columns))
    print(rgb(AMBAR_SUAVE, "MARIA CLI v1.0.0"))
    print(rgb(CINZA, "Digite 'ajuda' para ver os comandos disponíveis."))
    print(rgb(ROSA, "maria") + rgb(VERDE, "@assistente") + rgb(AMBAR, ":~$ _"))


def main():
    ap = argparse.ArgumentParser(description="Banner da MARIA no terminal.")
    ap.add_argument("--imagem", default="maria_face.png",
                    help="Caminho da imagem (padrão: maria_face.png)")
    ap.add_argument("--glifo", default="M", help="Glifo do logo fallback (padrão: M)")
    ap.add_argument("--mono", action="store_true", help="Âmbar sólido (sem truecolor)")
    args = ap.parse_args()
    exibir_banner(imagem=args.imagem, glifo=args.glifo, mono=args.mono)


if __name__ == "__main__":
    main()