#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fotoASCII_terminal.py
=======================
Conversor de imagem para arte ASCII/Unicode otimizado para terminais.

Melhorias em relação à versão anterior:
- 3 modos de renderização (ASCII, Blocos Unicode, Braille)
- Pré-processamento de contraste e nitidez
- Proporção corrigida para caracteres de terminal
- Saída otimizada para larguras de terminal reais
- Preview direto no terminal

Uso:
    python fotoASCII_terminal.py imagem.png
    python fotoASCII_terminal.py imagem.png --modo braille --largura 100
    python fotoASCII_terminal.py imagem.png --modo blocos --contraste 1.5 --saida arte.txt
"""

import sys
import argparse
from pathlib import Path

try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError:
    print("Erro: Pillow não instalado. Execute: pip install Pillow")
    sys.exit(1)


# ============================================================
# RAMPAS DE CARACTERES
# ============================================================
ASCII_CHARS = "@%#*+=-:. "  # 10 níveis, do mais escuro ao mais claro

BLOCK_CHARS = {
    (0, 0): "█",  # escuro, escuro
    (0, 1): "▀",  # escuro, claro
    (1, 0): "▄",  # claro, escuro
    (1, 1): " ",  # claro, claro
}

BRAILLE_OFFSET = 0x2800


def ajustar_imagem(img, contraste=1.3, brilho=1.0, nitidez=1.0):
    """Aplica melhorias de contraste, brilho e nitidez."""
    if contraste != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contraste)
    if brilho != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brilho)
    if nitidez != 1.0:
        img = ImageEnhance.Sharpness(img).enhance(nitidez)
    return img


def to_ascii(img_pil, largura=80, inverter=False):
    """
    Modo ASCII clássico otimizado.
    Cada caractere = 1 pixel.
    """
    w, h = img_pil.size
    ratio = h / w
    # Caracteres de terminal têm proporção ~2:1 (altura:largura)
    nova_altura = int(largura * ratio * 0.5)
    img_small = img_pil.resize((largura, max(nova_altura, 1)), Image.Resampling.LANCZOS)

    import numpy as np
    arr = np.array(img_small)
    indices = (arr / 255 * (len(ASCII_CHARS) - 1)).astype(int)
    indices = np.clip(indices, 0, len(ASCII_CHARS) - 1)

    if inverter:
        indices = len(ASCII_CHARS) - 1 - indices

    linhas = []
    for row in indices:
        linhas.append("".join(ASCII_CHARS[i] for i in row))
    return "\n".join(linhas)


def to_blocks(img_pil, largura=80, inverter=False):
    """
    Modo Blocos Unicode.
    Cada caractere = 2 pixels verticais (dobra resolução vertical).
    """
    w, h = img_pil.size
    ratio = h / w
    nova_altura = int(largura * ratio * 0.5) * 2
    nova_altura = max(nova_altura, 2)

    img_small = img_pil.resize((largura, nova_altura), Image.Resampling.LANCZOS)

    import numpy as np
    arr = np.array(img_small)
    if arr.shape[0] % 2 == 1:
        arr = arr[:-1]

    limiar = 128
    linhas = []
    for y in range(0, arr.shape[0], 2):
        linha = ""
        for x in range(arr.shape[1]):
            top = arr[y, x] > limiar
            bot = arr[y + 1, x] > limiar
            if inverter:
                top, bot = not top, not bot
            linha += BLOCK_CHARS[(int(top), int(bot))]
        linhas.append(linha)
    return "\n".join(linhas)


def to_braille(img_pil, largura=80, inverter=False):
    """
    Modo Braille Patterns (recomendado).
    Cada caractere = matriz 2×4 de pontos (alta resolução).
    """
    w, h = img_pil.size
    ratio = h / w
    # Cada char braille cobre 2 cols × 4 rows
    nova_largura = largura * 2
    nova_altura = int(largura * ratio * 0.5) * 4
    nova_altura = max(nova_altura, 4)

    img_small = img_pil.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)

    import numpy as np
    arr = np.array(img_small)
    rows = (arr.shape[0] // 4) * 4
    cols = (arr.shape[1] // 2) * 2
    arr = arr[:rows, :cols]

    limiar = 128
    linhas = []
    for y in range(0, rows, 4):
        linha = ""
        for x in range(0, cols, 2):
            sub = arr[y:y+4, x:x+2]
            # Layout Braille:
            # dot0 = sub[0,0]   dot3 = sub[0,1]
            # dot1 = sub[1,0]   dot4 = sub[1,1]
            # dot2 = sub[2,0]   dot5 = sub[2,1]
            # dot6 = sub[3,0]   dot7 = sub[3,1]
            dots = [
                sub[0, 0], sub[1, 0], sub[2, 0],
                sub[0, 1], sub[1, 1], sub[2, 1],
                sub[3, 0], sub[3, 1],
            ]
            bits = 0
            for i, val in enumerate(dots):
                ligado = val < limiar  # escuro = ponto ligado
                if inverter:
                    ligado = not ligado
                if ligado:
                    bits |= (1 << i)
            linha += chr(BRAILLE_OFFSET + bits)
        linhas.append(linha)
    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(
        description="Converte imagens para arte ASCII/Unicode otimizada para terminal."
    )
    parser.add_argument("imagem", help="Caminho da imagem de entrada")
    parser.add_argument(
        "--modo", "-m",
        choices=["ascii", "blocos", "braille"],
        default="braille",
        help="Modo de renderização (padrão: braille)"
    )
    parser.add_argument(
        "--largura", "-w",
        type=int,
        default=80,
        help="Largura em caracteres (padrão: 80)"
    )
    parser.add_argument(
        "--contraste", "-c",
        type=float,
        default=1.3,
        help="Fator de contraste, 1.0 = original (padrão: 1.3)"
    )
    parser.add_argument(
        "--brilho", "-b",
        type=float,
        default=1.0,
        help="Fator de brilho (padrão: 1.0)"
    )
    parser.add_argument(
        "--nitidez", "-n",
        type=float,
        default=1.2,
        help="Fator de nitidez (padrão: 1.2)"
    )
    parser.add_argument(
        "--inverter", "-i",
        action="store_true",
        help="Inverte cores (útil para terminal com fundo claro)"
    )
    parser.add_argument(
        "--saida", "-o",
        default=None,
        help="Caminho do arquivo de saída (padrão: mostra no terminal)"
    )
    parser.add_argument(
        "--preview", "-p",
        action="store_true",
        help="Mostra preview no terminal mesmo se --saida for usado"
    )

    args = parser.parse_args()

    # Carregar imagem
    try:
        img = Image.open(args.imagem).convert("L")
    except Exception as e:
        print(f"Erro ao abrir imagem: {e}")
        sys.exit(1)

    # Ajustes
    img = ajustar_imagem(img, args.contraste, args.brilho, args.nitidez)

    # Converter
    modos = {
        "ascii": to_ascii,
        "blocos": to_blocks,
        "braille": to_braille,
    }
    resultado = modos[args.modo](img, args.largura, args.inverter)

    # Preview no terminal
    if args.preview or args.saida is None:
        print(resultado)

    # Salvar em arquivo
    if args.saida:
        try:
            with open(args.saida, "w", encoding="utf-8") as f:
                f.write(resultado)
            print(f"\n✓ Salvo em: {Path(args.saida).resolve()}")
        except Exception as e:
            print(f"Erro ao salvar: {e}")
            sys.exit(1)

    # Estatísticas
    linhas = resultado.splitlines()
    print(f"\n📊 Estatísticas:")
    print(f"   Modo:      {args.modo}")
    print(f"   Dimensões: {args.largura} cols × {len(linhas)} linhas")
    print(f"   Invertido: {'sim' if args.inverter else 'não'}")


if __name__ == "__main__":
    main()
