#!/usr/bin/env python3
"""
Script wrapper para empacotar o backend Python como sidecar do Tauri.

Este script é chamado pelo processo de build do Tauri para criar
um executável único do backend Python usando PyInstaller.

Uso:
    python build_sidecar.py

 Saída:
    src-tauri/binaries/maria-backend-<target-triple> (ou .exe no Windows)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def _obter_target_triple() -> str:
    resultado = subprocess.run(["rustc", "-vV"], capture_output=True, text=True, check=True)
    for linha in resultado.stdout.splitlines():
        if linha.startswith("host:"):
            return linha.split(":", 1)[1].strip()
    raise RuntimeError("Não foi possível determinar o target triple via 'rustc -vV'.")

def main():
    # Diretórios
    root_dir = Path(__file__).parent.parent
    backend_dir = root_dir.parent / "backend"
    binaries_dir = root_dir / "binaries"
    
    # Criar diretório de saída
    binaries_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Construindo sidecar MARIA Backend")
    print("=" * 60)
    
    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
        print("✓ PyInstaller encontrado")
    except ImportError:
        print("✗ PyInstaller não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Verificar dependências
    requirements_file = backend_dir.parent / "requirements.txt"
    if requirements_file.exists():
        print("Instalando dependências do backend...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
    
        # Comando PyInstaller
    target = _obter_target_triple()
    output_name = f"maria-backend-{target}"
    if sys.platform == "win32":
        output_name += ".exe"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", f"maria-backend-{target}",
        "--workpath", str(root_dir / "build"),
        "--distpath", str(binaries_dir),
        "--specpath", str(root_dir),
        "--clean",
        "--noconfirm",
    ]
    
    # Adicionar dados estáticos (modelos, se existirem)
    models_dir = backend_dir / "models"
    if models_dir.exists():
        cmd.extend(["--add-data", f"{models_dir}{os.pathsep}models"])
    
    # Raiz do monorepo no path de análise: o pacote `backend` (namespace
    # package, sem __init__.py) só é resolvível com a raiz no sys.path, que
    # o main.py adiciona apenas em runtime — o analisador do PyInstaller não
    # executa isso. `--collect-submodules` garante também os imports feitos
    # dentro de funções (ex.: backend.core.file_utils, excel_handler).
    cmd.extend([
        "--paths", str(backend_dir.parent),
        "--collect-submodules", "backend",
    ])

    # Garantir que o Flask (modo --bridge-http) seja embutido no executável
    cmd.extend([
        "--hidden-import", "flask",
        "--hidden-import", "flask_cors",
    ])

    # Script principal
    main_script = backend_dir / "main.py"
    if not main_script.exists():
        print(f"✗ Erro: {main_script} não encontrado")
        sys.exit(1)
    
    cmd.append(str(main_script))
    
    print(f"\nExecutando PyInstaller...")
    print(f"Script: {main_script}")
    print(f"Saída: {binaries_dir / output_name}")
    
    try:
        subprocess.check_call(cmd)
        print(f"\n✓ Sidecar construído com sucesso: {binaries_dir / output_name}")
        
        # Limpar arquivos temporários do PyInstaller
        build_dir = root_dir / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
        
        spec_file = root_dir / "maria-backend.spec"
        if spec_file.exists():
            spec_file.unlink()
            
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Erro ao construir sidecar: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
