import sys
import shutil
import argparse
from PIL import Image

# Paleta de caracteres otimizada para fundo escuro e traços claros.
ASCII_CHARS = [" ", ".", "-", "~", "+", "=", "*", "#", "%", "@"]

# Códigos ANSI para colorir a arte (AZUL ESVERDEADO / TEAL)
ANSI_TEAL = "\033[38;5;37m" 
ANSI_RESET = "\033[0m"

def redimensionar_imagem(imagem, nova_largura=100):
    """Redimensiona mantendo a proporção e ajustando a altura para caber no terminal."""
    largura_original, altura_original = imagem.size
    proporcao = altura_original / largura_original
    
    fator_altura = 0.55 
    nova_altura = int(nova_largura * proporcao * fator_altura)
    
    return imagem.resize((nova_largura, nova_altura))

def converter_para_escala_de_cinza(imagem):
    return imagem.convert("L")

def pixels_para_ascii(imagem):
    pixels = imagem.getdata()
    caracteres = []
    max_indice = len(ASCII_CHARS) - 1

    for pixel in pixels:
        # Mapeia de 0-255 para 0-(max_indice)
        indice = int((pixel / 255) * max_indice)
        indice = min(indice, max_indice)
        caracteres.append(ASCII_CHARS[indice])

    return "".join(caracteres)

def aplicar_cores_ansi(linhas_ascii, colorir):
    if not colorir:
        return "\n".join(linhas_ascii)
    
    linhas_coloridas = []
    for linha in linhas_ascii:
        linhas_coloridas.append(f"{ANSI_TEAL}{linha}{ANSI_RESET}")
    return "\n".join(linhas_coloridas)

def converter_imagem_para_ascii(caminho_imagem, largura_terminal, usar_cores):
    try:
        imagem = Image.open(caminho_imagem)
    except Exception as e:
        print(f"Erro ao abrir a imagem: {e}")
        return

    img_redimensionada = redimensionar_imagem(imagem, largura_terminal)
    img_cinza = converter_para_escala_de_cinza(img_redimensionada)
    
    dados_ascii = pixels_para_ascii(img_cinza)
    total_pixels = len(dados_ascii)

    linhas_ascii = [
        dados_ascii[i : i + largura_terminal]
        for i in range(0, total_pixels, largura_terminal)
    ]

    return aplicar_cores_ansi(linhas_ascii, usar_cores)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Converte imagem para ASCII art para terminal.")
    parser.add_argument("imagem", help="Caminho da imagem PNG/JPG (ex: maria_face_1.png)")
    parser.add_argument("-w", "--width", type=int, default=0, 
                        help="Largura em caracteres (padrão: metade do tamanho da tela)")
    parser.add_argument("--no-color", action="store_false", dest="color", default=True,
                        help="Desativa as cores ANSI")

    args = parser.parse_args()

    # Definindo a largura
    if args.width > 0:
        largura = args.width
    else:
        # AQUI ESTÁ A ALTERAÇÃO: Metade do tamanho atual do terminal (-4 para margem)
        largura = int((shutil.get_terminal_size().columns - 4) * 0.5)
        if largura < 20:
            largura = 40 # Garante um mínimo visível

    resultado = converter_imagem_para_ascii(args.imagem, largura, args.color)

    if resultado:
        # Salva também o .txt (sem as cores ANSI para não poluir o texto)
        with open("arte_ascii.txt", "w", encoding="utf-8") as f:
            import re
            f.write(re.sub(r'\033\[[0-9;]*m', '', resultado))

        # Exibe no terminal com as cores
        print(resultado)
        print(f"\nSucesso! Gerado com {largura} colunas. O arquivo 'arte_ascii.txt' também foi criado.")