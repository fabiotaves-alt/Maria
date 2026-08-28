# Instalação do Whisper para Transcrição de Voz

O MARIA usa um **sistema de fallback em cascata** para transcrição local de áudio, priorizando performance e compatibilidade:

1. **faster-whisper (GPU NVIDIA)** → Se disponível, oferece até 4x mais velocidade
2. **whisper.cpp (CPU/binário externo)** → Padrão, leve e portátil
3. **Fallback informativo** → Mensagem clara se nenhum motor estiver disponível

---

## Visão Geral

| Motor | Requisitos | Velocidade | Qualidade | Status |
|-------|------------|------------|-----------|--------|
| **faster-whisper** | GPU NVIDIA + CUDA | ⚡⚡⚡ Alta | Excelente | Opcional |
| **whisper.cpp** | Nenhum (binário) | ⚡⚡ Média | Muito boa | Padrão |
| **Nenhum** | — | — | — | Fallback informativo |

**Por que fallback?** Nem todos os usuários têm GPU NVIDIA. O sistema detecta automaticamente e usa o melhor motor disponível.

---

## Opção 1: faster-whisper (Recomendado para GPU NVIDIA)

### Pré-requisitos

- GPU NVIDIA com drivers atualizados
- CUDA Toolkit 11.8+ instalado
- Python 3.10+

### Instalação

```bash
# No ambiente virtual do projeto
cd /workspace
source .venv/bin/activate  # Linux/macOS
# ou .venv\\Scripts\\activate  # Windows

# Instalar dependências (inclui pynvml para detecção de GPU)
pip install -r requirements.txt

# Instalar faster-whisper com suporte a CUDA
pip install faster-whisper
```

### Configuração Opcional

Variáveis de ambiente suportadas:

```bash
# Modelo (tiny, base, small, medium, large-v3)
export WHISPER_MODEL_PATH="small"

# Diretório para cache dos modelos
export HF_HOME="$HOME/.cache/huggingface"
```

### Verificação

```python
import torch
print(f"CUDA disponível: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Nenhuma'}")
```

---

## Opção 2: whisper.cpp (Padrão - CPU)

### Windows

#### Binário Pré-compilado (Recomendado)

1. Acesse https://github.com/ggerganov/whisper.cpp/releases
2. Baixe `whisper-bin-x64.zip` (ou `arm64` para ARM)
3. Extraia e copie `whisper-main.exe` para:
   ```
   C:\Program Files\maria\bin\
   ```
4. Adicione ao PATH ou defina:
   ```cmd
   setx WHISPER_BIN "C:\Program Files\maria\bin\whisper-main.exe"
   ```
5. Reinicie o terminal e teste:
   ```cmd
   whisper-main.exe -h
   ```

#### Compilar do Source

```cmd
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
mkdir build && cd build
cmake ..
cmake --build . --config Release
copy Release\whisper-main.exe C:\Program Files\maria\bin\
```

### Linux

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libasound2-dev

git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make

sudo cp whisper-main /usr/local/bin/
whisper-main -h
```

#### Fedora/RHEL

```bash
sudo dnf install -y alsa-lib-devel
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
sudo cp whisper-main /usr/local/bin/
```

### macOS

```bash
brew install cmake
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
sudo cp whisper-main /usr/local/bin/
whisper-main -h
```

### Download do Modelo

```bash
cd whisper.cpp/models
./download-ggml-model.sh small  # ou base, tiny, medium
```

---

## Variáveis de Ambiente

| Variável | Valor Padrão | Descrição |
|----------|--------------|-----------|
| `WHISPER_BIN` | `whisper-main` | Caminho para binário whisper.cpp |
| `WHISPER_TIMEOUT` | `120` | Timeout em segundos para transcrição |
| `WHISPER_MODEL_PATH` | `small` | Modelo para faster-whisper |

Exemplo `.env`:

```bash
WHISPER_BIN=/usr/local/bin/whisper-main
WHISPER_TIMEOUT=180
WHISPER_MODEL_PATH=base
```

---

## Teste de Funcionamento

### Teste Rápido

```bash
# 1. Gravar áudio de 5 segundos (Linux/macOS)
sox -d teste.wav trim 0 5

# 2. Executar transcrição manual
whisper-main -f teste.wav -otxt -of saida -l pt
cat saida.txt
```

### Teste via Interface

1. Inicie o MARIA no modo bridge (JavaFX)
2. Clique no botão de microfone
3. Fale por alguns segundos
4. Verifique a mensagem de confirmação mostrando qual engine foi usada:
   - `✓ Áudio transcrito (faster-whisper (GPU))`
   - `✓ Áudio transcrito (whisper.cpp)`
   - `⚠️ Nenhum motor de transcrição disponível`

---

## Como o Fallback Funciona

Fluxo automático no backend:

```
[Início da Transcrição]
        ↓
[Detectar GPU NVIDIA?] ──Não──┐
        ↓ Sim                 │
[Tentar faster-whisper]       │
        ↓ Falha/Sem GPU       │
[Tentar whisper.cpp] ←────────┘
        ↓ Falha/Não instalado
[Retornar mensagem informativa]
```

Logs de exemplo:

```
INFO: Tentando transcrição com faster-whisper (GPU)
INFO: Transcrição concluída com faster-whisper (GPU): 245 caracteres
```

ou

```
INFO: faster-whisper não instalado, pulando para whisper.cpp
INFO: Tentando transcrição com whisper.cpp: whisper-main
INFO: Transcrição concluída com whisper.cpp: 245 caracteres
```

ou

```
INFO: faster-whisper não instalado, pulando para whisper.cpp
INFO: whisper.cpp não encontrado, usando fallback
WARNING: Nenhum motor de transcrição disponível. Arquivo mantido: /tmp/maria_audio_123.wav
```

---

## Solução de Problemas

### `ImportError: No module named 'pynvml'`

```bash
pip install pynvml
```

### `faster-whisper falhou: CUDA out of memory`

- Use modelo menor: `export WHISPER_MODEL_PATH=tiny`
- Feche outras aplicações usando GPU

### `whisper-main: command not found`

```bash
# Verificar se está no PATH
which whisper-main  # Linux/macOS
where whisper-main  # Windows

# Ou definir variável
export WHISPER_BIN=/caminho/completo/whisper-main
```

### Transcrição lenta

- Use faster-whisper com GPU (Opção 1)
- Reduza tamanho do modelo (`tiny` ou `base`)
- Converta áudio para 16kHz mono antes:
  ```bash
  sox entrada.mp3 -r 16000 -c 1 saida.wav
  ```

### Áudio em formato incompatível

whisper.cpp espera WAV 16kHz mono. Converta:

```bash
sox entrada.mp3 -r 16000 -c 1 saida.wav
```

---

## Comparativo de Performance

| Cenário | faster-whisper | whisper.cpp |
|---------|----------------|-------------|
| GPU NVIDIA RTX 3060 | ~10s (áudio 1min) | ~45s |
| CPU Intel i7 (8 núcleos) | N/A | ~40s |
| CPU Apple M1 | N/A | ~25s |
| RAM usage (modelo small) | ~2.9GB VRAM | ~1.2GB RAM |

*Valores aproximados, variam por hardware.*

---

## Próximos Passos (Futuro)

1. **Empacotar binário no instalador** → Incluir whisper.cpp diretamente
2. **Java FFM API** → Chamar whisper.cpp nativamente do Java 21, eliminando subprocess Python
3. **Modelos quantizados** → Melhor equilíbrio qualidade/performance

---

**Referências:**
- whisper.cpp: https://github.com/ggerganov/whisper.cpp
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- Modelos GGML: https://huggingface.co/ggerganov/whisper.cpp
