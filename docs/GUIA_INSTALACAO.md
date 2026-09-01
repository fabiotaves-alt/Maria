# Guia Completo de Instalação e Configuração — MARIA

**Versão:** v4.1.1  
**Última atualização:** 2026-08-31  
**Ambiente de Referência:** Windows 10 (1809+) ou Windows 11 (PowerShell)  

Este documento é o guia definitivo para configurar do zero o ambiente de desenvolvimento e execução do monorepo **MARIA**, incluindo ferramentas de sistema, ambiente Python, frontend Tauri/React, servidor LLM local (`llama-server`) e transcrição de áudio local (`whisper.cpp`).

---

## 1. Requisitos de Sistema

### Hardware
| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| **RAM** | 8 GB | 16 GB |
| **Armazenamento** | 10 GB livres | 20 GB livres (SSD) |
| **GPU (Opcional)** | — | NVIDIA com 4+ GB VRAM (suporte a CUDA) |

### Software
| Dependência | Versão Mínima | Função no Projeto |
|---|---|---|
| **Python** | 3.11+ | Backend, scripts de RAG, testes e benchmark |
| **Node.js + npm** | 18 LTS+ | Frontend React, Vite, Tailwind CSS |
| **Rust (`rustup`)** | Estável | Compilação nativa da aplicação desktop Tauri v2 |
| **VS Build Tools 2022** | Workload C++ | Compilador MSVC para Rust e `llama.cpp` |
| **WebView2 Runtime** | Atual | Renderizador nativo da interface gráfica do Tauri |
| **llama.cpp** | Build recente | Servidor HTTP de inferência local (OpenAI-compatible) |
| **whisper.cpp (Opcional)** | Build recente | Transcrição local de áudio (.wav → texto) |

---

## 2. Instalação das Ferramentas Base (Windows)

Abra o **PowerShell como Administrador** e utilize o `winget` para instalar todas as ferramentas de uma vez:

```powershell
# 1. Instalar Node.js LTS, Rustup, Python 3.11 e Visual Studio 2022 Build Tools
winget install OpenJS.NodeJS.LTS Rustlang.Rustup Python.Python.3.11 `
  Microsoft.VisualStudio.2022.BuildTools --override "--wait --quiet --add ProductLang Pt-br --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"

# 2. Instalar WebView2 Runtime (já incluso nativamente no Windows 11)
winget install Microsoft.EdgeWebView2Runtime

# 3. Recarregar o PATH na sessão atual sem precisar fechar o terminal
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
            [System.Environment]::GetEnvironmentVariable("Path","User")
```

---

## 3. Configuração do Monorepo e Dependências

Clone o projeto e prepare os ambientes isolados de backend e frontend:

```powershell
# 1. Clonar o repositório
git clone <repo-url>
cd maria

# 2. Criar e ativar o ambiente virtual Python
python -m venv .venv
.\.venv\Scripts\activate

# 3. Instalar dependências do backend
pip install -r requirements.txt

# 4. Instalar dependências do frontend Tauri / React
cd frontend-tauri
npm install
cd ..
```

---

## 4. Configuração dos Motores de IA Locais

### 4.1. LLM Principal — `llama-server` (`llama.cpp`)

O MARIA consome a API OpenAI-compatible do `llama-server` na porta `8080`.

#### Compilação do `llama.cpp`:
```powershell
# Clonar repositório oficial
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Opção A: Com aceleração GPU NVIDIA (CUDA)
cmake -B build -DGGML_CUDA=ON
# Opção B: Processamento em CPU pura
# cmake -B build

# Compilar em Release (utilizando 4 threads)
cmake --build build --config Release -j4
cd ..
```

#### Download do Modelo Multimodal `Qwen2.5-Omni 3B`:
```powershell
# Criar diretório de modelos
New-Item -ItemType Directory -Force "$env:USERPROFILE\models"

# Baixar o arquivo GGUF quantizado (Q4_K_M, ~2,3 GB)
Invoke-WebRequest `
  -Uri "https://huggingface.co/ggml-org/Qwen2.5-Omni-3B-GGUF/resolve/main/qwen2_5-omni-3b-q4_k_m.gguf" `
  -OutFile "$env:USERPROFILE\models\qwen2_5-omni-3b-q4_k_m.gguf"
```

#### Inicialização do Servidor LLM:
```powershell
.\llama.cpp\build\bin\Release\llama-server.exe `
  -m "$env:USERPROFILE\models\qwen2_5-omni-3b-q4_k_m.gguf" `
  -ngl 99 -c 8192 --flash-attn --host 127.0.0.1 --port 8080
```
> Em CPU pura, remova o argumento `-ngl 99`.

---

### 4.2. Transcrição de Áudio — `whisper.cpp` (Opcional)

O suporte à voz e transcrição de áudio utiliza o `whisper.cpp`. Por diretriz de segurança do MARIA (v4.1.1), o binário deve residir dentro de um diretório restrito (`WHISPER_ALLOWED_DIR`, padrão: `<raiz_monorepo>/bin/`).

#### Instalação do Binário:
```powershell
# 1. Criar pasta segura de binários na raiz do monorepo
New-Item -ItemType Directory -Force "bin"

# 2. Baixar binário pré-compilado ou compilar via cmake
# Exemplo: Baixar release oficial do whisper.cpp
Invoke-WebRequest `
  -Uri "https://github.com/ggerganov/whisper.cpp/releases/latest/download/whisper-bin-x64.zip" `
  -OutFile "bin\whisper-bin.zip"

Expand-Archive -Path "bin\whisper-bin.zip" -DestinationPath "bin\temp_whisper" -Force
Copy-Item "bin\temp_whisper\whisper-main.exe" "bin\whisper-main.exe" -Force
Remove-Item "bin\temp_whisper", "bin\whisper-bin.zip" -Recurse -Force
```

#### Download do Modelo de Áudio (`ggml-small.bin` ou `ggml-base.bin`):
```powershell
# Baixar modelo Whisper em português/multilíngue (~460 MB)
Invoke-WebRequest `
  -Uri "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin" `
  -OutFile "$env:USERPROFILE\models\ggml-small.bin"
```

---

## 5. Configuração de Variáveis de Ambiente (`.env`)

Crie um arquivo `.env` na raiz do monorepo com as configurações desejadas:

```env
# Conexão com o servidor LLM
LLAMA_BASE_URL=http://localhost:8080
LLAMA_MODEL=qwen2.5-omni-3b
LLAMA_NUM_CTX=8192

# Modo de Ambiente: "development" habilita CORS para o Vite dev server
# Em produção, mantenha "production"
MARIA_ENV=development

# Diretório seguro permitido para execução do Whisper
WHISPER_ALLOWED_DIR=C:\Users\Sony Vaio\Documents\maria\bin
```

---

## 6. Script de Verificação Automática

Execute este bloco no PowerShell para validar que todas as ferramentas estão operacionais:

```powershell
Write-Host "=== Validando Ambiente MARIA ===" -ForegroundColor Green
Write-Host "Node.js:      $(node --version)"
Write-Host "npm:          $(npm --version)"
Write-Host "Rust (rustc): $(rustc --version)"
Write-Host "Cargo:        $(cargo --version)"
Write-Host "Python:       $(.\.venv\Scripts\python.exe --version)"
Write-Host "Tauri CLI:    $(npx @tauri-apps/cli --version)"

# Teste estático do backend
.\.venv\Scripts\python.exe -m py_compile backend\main.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "Backend Python: OK (sem erros de sintaxe)" -ForegroundColor Green
} else {
    Write-Host "Backend Python: ERRO" -ForegroundColor Red
}
```

---

## 7. Solução de Problemas Comuns (Troubleshooting)

| Problema | Causa | Solução |
|---|---|---|
| `'cargo' ou 'rustc' não é reconhecido` | PATH não atualizado após instalação do Rustup | Reinicie o PowerShell ou redefina `$env:Path` conforme a Seção 2. |
| `MSVC / C++ build tools not found` | VS Build Tools incompleto | Execute `winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"` e reinicie o PC. |
| `401 Unauthorized` ao chamar a bridge | Token de autenticação ausente | As rotas de `/chat` exigem o header `Authorization: Bearer <token>` gerado em `shared/.bridge_token`. O frontend Tauri faz isso de forma transparente. |
| `llama-server: Connection refused` | Servidor LLM não iniciado | Inicie o `llama-server` na porta 8080 antes de abrir o aplicativo. |
| `Whisper binary rejected` | Binário fora de pasta autorizada | Certifique-se de que `whisper-main.exe` está localizado estritamente dentro da pasta configurada em `WHISPER_ALLOWED_DIR`. |
| `UnicodeEncodeError (cp1252)` | Terminal Windows em codificação legada | Defina `$env:PYTHONIOENCODING = "utf-8"` antes de executar scripts Python no console. |
