# Instalação do Whisper.cpp para Transcrição de Voz

O MARIA usa whisper.cpp para transcrição local de áudio. Esta é uma dependência opcional — sem ela, a funcionalidade de voz exibe uma mensagem informativa.

## Visão Geral

- **O que é:** whisper.cpp é um port em C/C++ do modelo Whisper da OpenAI, muito mais leve e rápido que a versão Python.
- **Por que usar:** Transcrição offline, sem envio de dados para nuvem, baixo consumo de RAM.
- **Status:** ⚠️ Opcional (funcionalidade degrada graciosamente se não instalado)

---

## Windows

### Opção A: Binário Pré-compilado (Recomendado)

1. Acesse https://github.com/ggerganov/whisper.cpp/releases
2. Baixe o arquivo `whisper-bin-x64.zip` (ou `arm64` para ARM)
3. Extraia e copie `whisper-main.exe` para:
   ```
   C:\Program Files\maria\bin\
   ```
4. Adicione ao PATH ou defina variável de ambiente:
   ```cmd
   setx WHISPER_BIN "C:\Program Files\maria\bin\whisper-main.exe"
   ```
5. Reinicie o terminal e teste:
   ```cmd
   whisper-main.exe -h
   ```

### Opção B: Compilar do Source

```cmd
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
mkdir build && cd build
cmake ..
cmake --build . --config Release
copy Release\whisper-main.exe C:\Program Files\maria\bin\
```

---

## Linux

### Ubuntu/Debian

```bash
# Instalar dependências
sudo apt-get update
sudo apt-get install -y build-essential cmake libasound2-dev

# Clonar e compilar
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make

# Copiar para PATH
sudo cp whisper-main /usr/local/bin/

# Testar
whisper-main -h
```

### Fedora/RHEL

```bash
sudo dnf install -y alsa-lib-devel
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
sudo cp whisper-main /usr/local/bin/
```

---

## macOS

```bash
# Com Homebrew
brew install cmake
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make

# Copiar para PATH
sudo cp whisper-main /usr/local/bin/

# Testar
whisper-main -h
```

---

## Download do Modelo

O whisper.cpp requer um modelo `.bin`. Recomendado:

```bash
cd whisper.cpp/models
# Modelo pequeno (bom equilíbrio qualidade/tamanho)
./download-ggml-model.sh small
# Ou use o base para menos RAM
./download-ggml-model.sh base
```

Modelos disponíveis: `tiny`, `base`, `small`, `medium`, `large-v3`

---

## Teste de Funcionamento

1. Grave um áudio de teste (ou use um existente):
   ```bash
   # Linux/macOS
   sox -d teste.wav trim 0 5
   
   # Windows (PowerShell)
   # Use o Gravador de Voz e salve como teste.wav
   ```

2. Execute a transcrição:
   ```bash
   whisper-main -f teste.wav -otxt -of saida
   cat saida.txt
   ```

3. Se funcionar, você verá o texto transcrito.

---

## Integração com MARIA

O backend do MARIA chama whisper.cpp assim:

```python
import subprocess
import os

whisper_bin = os.getenv("WHISPER_BIN", "whisper-main")
resultado = subprocess.run(
    [whisper_bin, "-f", "audio.wav", "-otxt", "-of", "temp_whisper"],
    capture_output=True,
    text=True,
    timeout=60
)
```

Se o binário não for encontrado, o MARIA exibe:
> "[Whisper.cpp não encontrado. Instale whisper.cpp ou use o áudio: ...]"

---

## Solução de Problemas

### Erro: `whisper-main: command not found`

- Verifique se o binário está no PATH:
  ```bash
  which whisper-main  # Linux/macOS
  where whisper-main  # Windows
  ```
- Ou defina a variável `WHISPER_BIN` com o caminho completo.

### Erro: `could not find model file`

- Baixe o modelo conforme seção "Download do Modelo"
- Certifique-se de que o arquivo `ggml-small.bin` (ou outro) esteja em `whisper.cpp/models/`

### Transcrição lenta

- Use um modelo menor (`tiny` ou `base`)
- Em CPUs fracas, considere usar GPU (requer compilação com CUDA)

### Áudio em formato incompatível

- whisper.cpp espera WAV 16kHz mono
- Converta com sox:
  ```bash
  sox entrada.mp3 -r 16000 -c 1 teste.wav
  ```

---

## Alternativas Futuras

1. **Empacotar binário no instalador:** Incluir `whisper-main.exe` diretamente no instalador do MARIA.
2. **Usar openai-whisper (Python):** Mais pesado, mas não requer binário externo.
3. **API de nuvem:** Google Speech-to-Text, Azure Speech, etc. (requer internet).

---

**Referências:**
- GitHub: https://github.com/ggerganov/whisper.cpp
- Hugging Face Models: https://huggingface.co/ggerganov/whisper.cpp
