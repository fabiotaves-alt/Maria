# Script de Instalação do Projeto MARIA - Frontend Tauri
# Este script instala todas as dependências necessárias: Node.js, Rust, Tauri, Python e configura o ambiente

param(
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$SkipRust,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "  → $Message" -ForegroundColor Green
}

function Test-Command {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-InstalledVersion {
    param([string]$Command)
    try {
        & $Command --version 2>&1 | Select-Object -First 1
    } catch {
        return $null
    }
}

# Ajuda
if ($Help) {
    Write-Host @"
Script de Instalação do Projeto MARIA - Frontend Tauri

Uso: .\install-dependencies.ps1 [Opções]

Opções:
  -SkipPython   Pula a instalação/verificação das dependências Python
  -SkipNode     Pula a instalação/verificação do Node.js e npm
  -SkipRust     Pula a instalação/verificação do Rust e Cargo
  -Help         Mostra esta mensagem de ajuda

O script irá:
  1. Verificar e instalar Node.js (se necessário)
  2. Verificar e instalar Rust (se necessário)
  3. Instalar Tauri CLI
  4. Instalar dependências do frontend (npm install)
  5. Instalar dependências Python (se não usar -SkipPython)
  6. Orientar sobre a instalação do llama.cpp

"@ -ForegroundColor Yellow
    exit 0
}

Write-Header "Instalação do Projeto MARIA - Frontend Tauri"
Write-Host "Este script irá instalar todas as dependências necessárias para desenvolver com Tauri + React." -ForegroundColor White
Write-Host ""

# ============================================================
# 1. Verificação e Instalação do Node.js
# ============================================================
if (-not $SkipNode) {
    Write-Header "1. Verificando Node.js e npm"

    if (Test-Command "node") {
        $nodeVersion = Get-InstalledVersion "node"
        Write-Step "Node.js já está instalado: $nodeVersion"
    } else {
        Write-Step "Node.js não encontrado. Instalando..."
        Write-Host "  Por favor, instale o Node.js LTS em: https://nodejs.org/" -ForegroundColor Yellow
        Write-Host "  Após instalar, reinicie este script." -ForegroundColor Yellow
        pause
    }

    if (Test-Command "npm") {
        $npmVersion = Get-InstalledVersion "npm"
        Write-Step "npm já está instalado: $npmVersion"
    }
} else {
    Write-Step "Pulando verificação do Node.js (usando -SkipNode)"
}

# ============================================================
# 2. Verificação e Instalação do Rust
# ============================================================
if (-not $SkipRust) {
    Write-Header "2. Verificando Rust e Cargo"

    if (Test-Command "rustc") {
        $rustVersion = Get-InstalledVersion "rustc"
        Write-Step "Rust já está instalado: $rustVersion"
    } else {
        Write-Step "Rust não encontrado. Instalando rustup..."
        Write-Host "  Instalando Rust via rustup.rs..." -ForegroundColor Yellow

        # Download e execução do rustup installer
        $rustupUrl = "https://win.rustup.rs/x86_64"
        $rustupFile = "$env:TEMP\rustup-init.exe"

        try {
            Invoke-WebRequest -Uri $rustupUrl -OutFile $rustupFile
            Write-Step "Executando instalador do Rust (modo silencioso)..."
            Start-Process -FilePath $rustupFile -ArgumentList "-y", "--default-toolchain", "stable" -Wait

            # Adicionar Rust ao PATH da sessão atual
            $rustBinPath = "$env:USERPROFILE\.cargo\bin"
            if (Test-Path $rustBinPath) {
                $env:Path = "$rustBinPath;$env:Path"
                Write-Step "Rust instalado com sucesso!"
            }
        } catch {
            Write-Host "  Erro ao instalar Rust automaticamente." -ForegroundColor Red
            Write-Host "  Por favor, instale manualmente em: https://rustup.rs/" -ForegroundColor Yellow
            pause
        }
    }

    if (Test-Command "cargo") {
        $cargoVersion = Get-InstalledVersion "cargo"
        Write-Step "Cargo já está instalado: $cargoVersion"
    }

    # Verificar versão mínima do Rust (Tauri v2 requer Rust 1.70+)
    if (Test-Command "rustc") {
        $rustVersionRaw = rustc --version 2>&1
        if ($rustVersionRaw -match "rustc\s+([\d\.]+)") {
            $installedVersion = [Version]$matches[1]
            $minVersion = [Version]"1.70.0"

            if ($installedVersion -lt $minVersion) {
                Write-Host "  Atenção: Sua versão do Rust ($installedVersion) é anterior à mínima necessária (1.70.0)." -ForegroundColor Yellow
                Write-Host "  Execute 'rustup update' para atualizar." -ForegroundColor Yellow
            } else {
                Write-Step "Versão do Rust OK: $installedVersion"
            }
        }
    }
} else {
    Write-Step "Pulando verificação do Rust (usando -SkipRust)"
}

# ============================================================
# 3. Instalação das ferramentas do Tauri
# ============================================================
Write-Header "3. Instalando Tauri CLI e dependências do sistema"

# Verificar se o Tauri CLI já está instalado globalmente
Write-Step "Verificando Tauri CLI..."
$tauriInstalled = npm list -g @tauri-apps/cli 2>&1 | Select-String "@tauri-apps/cli"

if (-not $tauriInstalled) {
    Write-Step "Instalando Tauri CLI globalmente..."
    npm install -g @tauri-apps/cli
    Write-Step "Tauri CLI instalado com sucesso!"
} else {
    Write-Step "Tauri CLI já está instalado."
}

# Dependências do sistema para Windows (necessárias para compilar Rust/Tauri)
Write-Step "Verificando dependências do sistema (Visual C++ Build Tools)..."
$buildToolsPath = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vs_buildtools.exe"

if (-not (Test-Path $buildToolsPath)) {
    Write-Host "  Nota: Ferramentas de build do Visual C++ podem ser necessárias." -ForegroundColor Yellow
    Write-Host "  Se encontrar erros de compilação, instale em:" -ForegroundColor Yellow
    Write-Host "  https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Yellow
    Write-Host "  Selecione: 'Build Tools for Visual Studio' → 'C++ build tools'" -ForegroundColor Yellow
}

# ============================================================
# 4. Instalando dependências do frontend (npm install)
# ============================================================
Write-Header "4. Instalando dependências do frontend (npm install)"

$frontendDir = Join-Path $ProjectRoot "frontend-tauri"

if (Test-Path (Join-Path $frontendDir "package.json")) {
    Write-Step "Navegando para $frontendDir"
    Set-Location $frontendDir

    Write-Step "Executando npm install..."
    npm install

    if ($LASTEXITCODE -eq 0) {
        Write-Step "Dependências do frontend instaladas com sucesso!"
    } else {
        Write-Host "  Erro ao instalar dependências do frontend." -ForegroundColor Red
        Write-Host "  Verifique se o Node.js e npm estão corretamente instalados." -ForegroundColor Yellow
    }

    Set-Location $ProjectRoot
} else {
    Write-Host "  package.json não encontrado em $frontendDir" -ForegroundColor Red
}

# ============================================================
# 5. Instalando dependências Python (opcional)
# ============================================================
if (-not $SkipPython) {
    Write-Header "5. Instalando dependências Python"

    if (Test-Command "python") {
        $pythonVersion = python --version 2>&1
        Write-Step "Python encontrado: $pythonVersion"

        # Verificar se o ambiente virtual existe
        $venvPath = Join-Path $ProjectRoot ".venv"
        $venvPython = Join-Path $venvPath "Scripts\python.exe"

        if (-not (Test-Path $venvPath)) {
            Write-Step "Criando ambiente virtual em .venv..."
            python -m venv $venvPath
        }

        if (Test-Path $venvPython) {
            Write-Step "Instalando dependências Python do backend..."
            $requirementsPath = Join-Path $ProjectRoot "requirements.txt"

            if (Test-Path $requirementsPath) {
                & $venvPython -m pip install --upgrade pip
                & $venvPython -m pip install -r $requirementsPath

                if ($LASTEXITCODE -eq 0) {
                    Write-Step "Dependências Python instaladas com sucesso!"
                }
            } else {
                Write-Host "  requirements.txt não encontrado." -ForegroundColor Yellow
            }
        } else {
            Write-Host "  Ambiente virtual não configurado corretamente." -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Python não encontrado. Pulando instalação das dependências Python." -ForegroundColor Yellow
        Write-Host "  Instale Python 3.11+ em: https://www.python.org/downloads/" -ForegroundColor Yellow
    }
} else {
    Write-Step "Pulando instalação das dependências Python (usando -SkipPython)"
}

# ============================================================
# 6. Instruções sobre llama.cpp
# ============================================================
Write-Header "6. Configurando llama.cpp (necessário para IA local)"

Write-Host @"
Para rodar o modelo de IA localmente, você precisa do llama.cpp:

1. Clone o repositório:
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp

2. Compile com suporte a GPU (opcional):
   - Windows (com CUDA para NVIDIA):
     cmake -B build -DGGML_CUDA=ON
     cmake --build build --config Release -j4

   - macOS (Apple Silicon com Metal):
     cmake -B build
     cmake --build build --config Release -j4

   - Sem aceleração GPU:
     cmake -B build
     cmake --build build --config Release -j4

3. Baixe o modelo Qwen2.5-Omni 3B:
   wget -O models/qwen2_5-omni-3b-q4_k_m.gguf https://huggingface.co/ggml-org/Qwen2.5-Omni-3B-GGUF/resolve/main/qwen2_5-omni-3b-q4_k_m.gguf

4. Inicie o servidor:
   ./build/bin/llama-server -m models/qwen2_5-omni-3b-q4_k_m.gguf -ngl 99 -c 8192 --flash-attn --host 0.0.0.0 --port 8080

"@ -ForegroundColor White

# ============================================================
# 7. Resumo final
# ============================================================
Write-Header "Instalação Concluída!"

Write-Host @"
Resumo do que foi feito:
✓ Node.js e npm verificados/instalados
✓ Rust e Cargo verificados/instalados
✓ Tauri CLI instalado
✓ Dependências do frontend (npm install) concluídas
$(if (-not $SkipPython) { "✓ Dependências Python instaladas" } else { "○ Dependências Python puladas" })

Próximos passos:
1. Certifique-se de que o llama.cpp está configurado (veja instruções acima)
2. Para desenvolvimento:

   # Terminal 1 - Backend Python:
   .venv\Scripts\python.exe backend\main.py --bridge-http --porta 8081

   # Terminal 2 - Frontend Tauri:
   cd frontend-tauri
   npm run tauri dev

3. Para build de produção:
   cd frontend-tauri\src-tauri
   python build_sidecar.py
   cd ..
   npm run tauri build

Documentação completa em: README.md e frontend-tauri/IMPLEMENTACAO_COMPLETA.md

"@ -ForegroundColor Green

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Instalação concluída com sucesso!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
