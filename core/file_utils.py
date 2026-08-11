"""
Módulo utilitário para operações com arquivos no projeto MARIA.
"""

import os
import re
import logging

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
    if not os.path.exists(pasta):
        os.makedirs(pasta)
        logger.debug(f"Pasta '{pasta}' criada.")
    
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
