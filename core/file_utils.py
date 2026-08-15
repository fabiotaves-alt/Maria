"""
Módulo utilitário para operações com arquivos no projeto MARIA.
"""

import os
import re
import logging
from pathlib import Path
from core.config import EXTENSOES_LEITURA, MAX_CHARS_LEITURA, MAX_TAMANHO_ARQUIVO_MB

logger = logging.getLogger(__name__)


def _pasta_arquivos_gerados() -> str:
    """Lê a pasta de saída no momento da chamada, inclusive em testes."""
    return os.getenv("PASTA_ARQUIVOS_GERADOS", "arquivos_gerados")


def garantir_pasta_arquivos() -> str:
    """
    Garante que a pasta de arquivos gerados existe.
    
    Returns:
        Caminho absoluto da pasta de arquivos gerados
    """
    pasta = _pasta_arquivos_gerados()
    os.makedirs(pasta, exist_ok=True)
    logger.debug(f"Pasta '{pasta}' garantida.")
    
    return os.path.abspath(pasta)


def sanitizar_nome_arquivo(nome_base: str) -> str:
    """Remove caminhos e caracteres inseguros de um nome de arquivo."""
    nome_sem_caminho = os.path.basename(nome_base.strip())
    nome_seguro = re.sub(r"[^\w\-. ]", "", nome_sem_caminho).strip()

    if not nome_seguro:
        raise ValueError(
            f"Nome de arquivo inválido: '{nome_base}'. "
            "Use apenas letras, números, espaços, '-', '_' ou '.'."
        )

    return nome_seguro


def gerar_nome_unico(nome_base: str, extensao: str) -> str:
    """
    Gera um nome de arquivo único adicionando sufixo numérico se necessário.
    
    Args:
        nome_base: Nome base do arquivo (sem extensão)
        extensao: Extensão do arquivo (ex: '.xlsx', '.docx')
        
    Returns:
        Nome do arquivo com sufixo numérico se necessário para evitar sobrescrita
        
    Exemplo:
        >>> gerar_nome_unico("relatorio", ".xlsx")
        'relatorio.xlsx'  # se não existir
        >>> gerar_nome_unico("relatorio", ".xlsx")  # se relatorio.xlsx já existir
        'relatorio_1.xlsx'
    """
    nome_base_seguro = sanitizar_nome_arquivo(nome_base)
    pasta_absoluta = garantir_pasta_arquivos()
    
    # Primeiro tenta sem sufixo
    nome_arquivo = f"{nome_base_seguro}{extensao}"
    caminho_completo = os.path.join(pasta_absoluta, nome_arquivo)
    
    if not os.path.exists(caminho_completo):
        return nome_arquivo
    
    # Se já existe, adicionar sufixo numérico
    contador = 1
    while True:
        nome_arquivo = f"{nome_base_seguro}_{contador}{extensao}"
        caminho_completo = os.path.join(pasta_absoluta, nome_arquivo)
        
        if not os.path.exists(caminho_completo):
            return nome_arquivo
        
        contador += 1


def _pastas_permitidas() -> list[str]:
    """Lê a lista de pastas permitidas para leitura no momento da chamada,
    permitindo isolamento em testes via variável de ambiente PASTAS_PERMITIDAS."""
    bruto = os.getenv("PASTAS_PERMITIDAS", _pasta_arquivos_gerados())
    pastas = [p.strip() for p in bruto.split(os.pathsep) if p.strip()]
    if not pastas:
        raise ValueError("Nenhuma pasta permitida configurada (PASTAS_PERMITIDAS).")
    return pastas


def resolver_caminho_permitido(caminho_bruto: str) -> Path:
    """Resolve um caminho e garante que ele está dentro de uma pasta permitida.

    Raises:
        ValueError: se o caminho resolvido estiver fora de todas as pastas permitidas.
    """
    pastas_permitidas = _pastas_permitidas()
    alvo = Path(caminho_bruto or ".")

    if not alvo.is_absolute():
        candidato_encontrado = None
        for pasta in pastas_permitidas:
            candidato = (Path(pasta) / alvo).resolve()
            if candidato.exists():
                candidato_encontrado = candidato
                break
        alvo = candidato_encontrado or (Path(pastas_permitidas[0]) / alvo).resolve()
    else:
        alvo = alvo.resolve()

    for pasta in pastas_permitidas:
        base = Path(pasta).resolve()
        if alvo == base or alvo.is_relative_to(base):
            return alvo

    raise ValueError(f"Acesso negado: '{caminho_bruto}' está fora das pastas permitidas.")


def listar_arquivos(pasta: str = "") -> list[dict]:
    """Lista nome e tamanho (KB) dos arquivos de uma pasta permitida.

    Quando `pasta` não é informada, usa a primeira pasta permitida como
    padrão e a cria automaticamente se ainda não existir (equivalente a
    "nenhum arquivo ainda", não um erro).

    Raises:
        ValueError: pasta explicitamente informada não existe, não é
            diretório, ou está fora das pastas permitidas.
        PermissionError: sem permissão de leitura/criação na pasta.
    """
    pastas_permitidas = _pastas_permitidas()

    if pasta:
        base = resolver_caminho_permitido(pasta)
    else:
        base = Path(pastas_permitidas[0]).resolve()
        os.makedirs(base, exist_ok=True)

    if not base.is_dir():
        raise ValueError(f"A pasta '{base.name}' não existe ou não é um diretório.")

    try:
        return [
            {"nome": item.name, "tamanho_kb": round(item.stat().st_size / 1024, 1)}
            for item in sorted(base.iterdir())
            if item.is_file()
        ]
    except PermissionError as error:
        logger.error(f"Permissão negada ao listar pasta: {error}")
        raise PermissionError(
            f"Não foi possível listar a pasta '{base.name}'. Verifique as permissões."
        ) from error


def ler_documento(caminho: str, max_chars: int | None = None) -> dict:
    """Lê um documento de texto (.txt, .md, .csv, .log, .docx) de uma pasta permitida.

    Raises:
        ValueError: arquivo inexistente, extensão não suportada, acima do limite de
            tamanho, fora das pastas permitidas, ou .docx corrompido/ilegível.
        PermissionError: sem permissão de leitura no arquivo.
        OSError: erro de disco durante a leitura.
    """
    max_chars = max_chars or MAX_CHARS_LEITURA
    alvo = resolver_caminho_permitido(caminho)

    if not alvo.is_file():
        raise ValueError(f"Arquivo não encontrado: {alvo.name}")
    if alvo.suffix.lower() not in EXTENSOES_LEITURA:
        raise ValueError(f"Tipo não suportado para leitura: {alvo.suffix}")
    if alvo.stat().st_size > MAX_TAMANHO_ARQUIVO_MB * 1024 * 1024:
        raise ValueError(f"Arquivo muito grande (limite: {MAX_TAMANHO_ARQUIVO_MB} MB).")

    try:
        if alvo.suffix.lower() == ".docx":
            from docx import Document
            texto = "\n".join(p.text for p in Document(alvo).paragraphs)
        else:
            texto = alvo.read_text(encoding="utf-8", errors="replace")
    except PermissionError as error:
        logger.error(f"Permissão negada ao ler documento: {error}")
        raise PermissionError(
            f"Não foi possível ler o arquivo '{alvo.name}'. Verifique as permissões."
        ) from error
    except OSError as error:
        logger.error(f"Erro de disco ao ler documento: {error}")
        raise OSError(
            f"Não foi possível ler o arquivo '{alvo.name}' devido a um erro de disco."
        ) from error
    except Exception as error:
        logger.error(f"Erro inesperado ao ler documento .docx: {error}")
        raise ValueError(f"Não foi possível interpretar o arquivo '{alvo.name}': {error}") from error

    return {
        "nome": alvo.name,
        "texto": texto[:max_chars],
        "truncado": len(texto) > max_chars,
        "total_chars": len(texto),
    }
