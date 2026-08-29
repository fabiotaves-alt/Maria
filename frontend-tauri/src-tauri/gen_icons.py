#!/usr/bin/env python3
"""Gera icones placeholder validos (PNG/ICO/ICNS) para o build do Tauri no Windows.
Uso apenas para destravar o build dev; substitua por icones reais quando disponiveis.
"""
import struct
import zlib
from pathlib import Path

OUT = Path(r"c:\Users\betti\IdeaProjects\Maria\frontend-tauri\src-tauri\icons")
OUT.mkdir(exist_ok=True)


def png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def make_png(w: int, h: int, rgb: tuple) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    idat = zlib.compress(raw, 9)
    return sig + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", idat) + png_chunk(b"IEND", b"")


def make_ico(png: bytes, w: int) -> bytes:
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", w, w, 0, 0, 1, 32, len(png), 22)
    return header + entry + png


def make_ico_dib(w: int, h: int, rgb: tuple) -> bytes:
    """ICO classico com DIB 32bpp + alpha (mais compativel que PNG embutido)."""
    r, g, b = rgb
    xor = bytearray()
    for y in range(h - 1, -1, -1):
        for _ in range(w):
            xor += bytes((b, g, r, 255))
    bmp = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0, len(xor), 0, 0, 0, 0)
    data = bmp + bytes(xor)
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), 22)
    return header + entry + data


def make_icns(png: bytes) -> bytes:
    data = b"ic07" + struct.pack(">I", len(png) + 8) + png
    return b"icns" + struct.pack(">I", len(data) + 8) + data


png32 = make_png(32, 32, (30, 60, 140))
png128 = make_png(128, 128, (30, 60, 140))

(OUT / "32x32.png").write_bytes(png32)
(OUT / "128x128.png").write_bytes(png128)
(OUT / "icon.ico").write_bytes(make_ico_dib(32, 32, (30, 60, 140)))
(OUT / "icon.icns").write_bytes(make_icns(png128))

print("Icones gerados em", OUT)
for f in sorted(OUT.iterdir()):
    print(" -", f.name, f.stat().st_size, "bytes")