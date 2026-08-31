# Guia de Instalação - Tauri, Rust e llama.cpp no PowerShell

Este guia contém os comandos necessários para configurar o ambiente de desenvolvimento no Windows usando PowerShell.

---

## 1. Instalar Winget (Gerenciador de Pacotes do Windows)
*O Winget já vem instalado no Windows 10/11. Verifique se está disponível:*

```powershell
winget --version
```

---

## 2. Instalar Node.js e npm
*Necessário para o frontend do projeto Tauri.*

```powershell
winget install OpenJS.NodeJS.LTS
```

*Verifique a instalação:*
```powershell
node --version
npm --version
```

---

## 3. Instalar Rust (rustup)
*Necessário para compilar o backend Tauri e llama.cpp.*

```powershell
winget install Rustlang.Rustup
```

*Após instalar, reinicie o PowerShell ou execute:*
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

*Verifique a instalação:*
```powershell
rustc --version
cargo --version
```

---

## 4. Instalar Dependências do Tauri (Windows)
*Ferramentas de build necessárias para o Tauri.*

```powershell
# Instalar Microsoft Visual Studio Build Tools com suporte a C++
winget install Microsoft.VisualStudio.2022.BuildTools --override "--wait --quiet --add ProductLang Pt-br --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"

# Instalar WebView2 (já vem no Windows 10/11, mas caso não tenha)
winget install Microsoft.EdgeWebView2Runtime
```

*Nota: Após instalar o Build Tools, pode ser necessário reiniciar o computador.*

---

## 5. Instalar Python (para llama.cpp)
*Necessário para scripts e bindings do llama.cpp.*

```powershell
winget install Python.Python.3.11
```

*Verifique a instalação:*
```powershell
python --version
pip --version
```

---

## 6. Configurar Ambiente do Projeto

### Navegar até o diretório do projeto:
```powershell
cd C:\caminho\para\seu\projeto
```

### Instalar dependências do frontend:
```powershell
npm install
```

### Instalar Tauri CLI:
```powershell
cargo install tauri-cli
```

---

## 7. Compilar llama.cpp

### Clonar o repositório (se ainda não tiver):
```powershell
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
```

### Compilar com CMake e Visual Studio:
```powershell
# Criar diretório de build
mkdir build
cd build

# Configurar com CMake
cmake .. -G "Visual Studio 17 2022" -A x64 -T host=x64

# Compilar
cmake --build . --config Release
```

### Ou usar make (se disponível):
```powershell
make
```

---

## 8. Comandos de Verificação Final

Execute todos para confirmar que tudo está instalado:

```powershell
Write-Host "=== Verificando Instalações ===" -ForegroundColor Green
Write-Host "Node.js: $(node --version)"
Write-Host "npm: $(npm --version)"
Write-Host "Rust: $(rustc --version)"
Write-Host "Cargo: $(cargo --version)"
Write-Host "Python: $(python --version)"
Write-Host "Tauri CLI: $(cargo tauri --version)"
```

---

## 9. Comandos Úteis do Projeto

### Desenvolvimento (modo debug):
```powershell
npm run tauri dev
```

### Build para produção:
```powershell
npm run tauri build
```

### Limpar builds anteriores:
```powershell
cargo clean
rm -r src-tauri/target
```

---

## 10. Solução de Problemas Comuns

### Erro: "cargo não é reconhecido"
```powershell
# Recarregar variáveis de ambiente
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

### Erro: "MSVC não encontrado"
```powershell
# Reinstalar Build Tools com todas as dependências
winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

### Erro: "Python não encontrado"
```powershell
# Adicionar Python ao PATH manualmente
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($pythonPath) {
    $pythonDir = Split-Path $pythonPath -Parent
    [Environment]::SetEnvironmentVariable("Path", "$env:Path;$pythonDir", "User")
}
```

---

## Resumo Rápido (One-Liner para Instalação Completa)

```powershell
winget install OpenJS.NodeJS.LTS Rustlang.Rustup Python.Python.3.11 Microsoft.VisualStudio.2022.BuildTools --silent; RefreshEnv; cargo install tauri-cli
```

*Nota: O comando `RefreshEnv` requer reinicialização do terminal ou uso do Chocolatey.*

---

## Requisitos Mínimos

- Windows 10 (versão 1809+) ou Windows 11
- 10 GB de espaço em disco livre
- 8 GB de RAM (16 GB recomendado para llama.cpp)
- Conexão com internet para downloads

---

**Dica:** Execute o PowerShell como Administrador para evitar problemas de permissão durante a instalação.
