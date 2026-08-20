"""
Módulo para criação e manipulação de planilhas Excel no projeto MARIA.
Usa a biblioteca openpyxl para gerar arquivos .xlsx.
"""

import os
import logging
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from backend.core.file_utils import garantir_pasta_arquivos, gerar_nome_unico, sanitizar_nome_arquivo
from backend.core.config import PASTA_ARQUIVOS_GERADOS

logger = logging.getLogger(__name__)


def criar_planilha_real(nome_arquivo: str, colunas: list[str], descricao: str = "") -> str:
    """
    Cria uma planilha Excel com as colunas especificadas.
    
    Args:
        nome_arquivo: Nome do arquivo (com ou sem extensão .xlsx - extensão será normalizada)
        colunas: Lista de nomes das colunas
        descricao: Descrição opcional da planilha
        
    Returns:
        Caminho absoluto do arquivo criado
        
    Raises:
        PermissionError: Se não houver permissão de escrita
        OSError: Se houver erro de disco
    """
    try:
        # Remover extensão .xlsx se presente para evitar duplicação
        if nome_arquivo.endswith('.xlsx'):
            nome_arquivo = nome_arquivo[:-5]
        
        # Gerar nome único para evitar sobrescrita
        nome_final = gerar_nome_unico(nome_arquivo, ".xlsx")
        pasta_absoluta = garantir_pasta_arquivos()
        caminho_completo = os.path.join(pasta_absoluta, nome_final)
        
        # Criar nova workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Dados"
        
        # Adicionar título/descrição se fornecido
        if descricao:
            ws.cell(row=1, column=1, value=descricao)
            ws.merge_cells(f"A1:{get_column_letter(len(colunas))}1")
            inicio_dados = 3
        else:
            inicio_dados = 1
        
        # Adicionar cabeçalhos das colunas
        for col_idx, coluna in enumerate(colunas, start=1):
            ws.cell(row=inicio_dados, column=col_idx, value=coluna)
        
        # Estilizar cabeçalhos (negrito)
        from openpyxl.styles import Font
        font_negrito = Font(bold=True)
        for col_idx in range(1, len(colunas) + 1):
            ws.cell(row=inicio_dados, column=col_idx).font = font_negrito
        
        # Ajustar largura das colunas automaticamente
        for col_idx, coluna in enumerate(colunas, start=1):
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = max(len(str(coluna)) + 2, 10)
        
        # Salvar arquivo
        wb.save(caminho_completo)
        
        logger.info(f"Planilha criada: {caminho_completo}")
        return caminho_completo
        
    except PermissionError as e:
        logger.error(f"Permissão negada ao criar planilha: {e}")
        raise PermissionError(
            f"Não foi possível salvar o arquivo. Verifique as permissões da pasta '{PASTA_ARQUIVOS_GERADOS}'."
        ) from e
        
    except OSError as e:
        logger.error(f"Erro de disco ao criar planilha: {e}")
        raise OSError(
            "Não foi possível salvar o arquivo. Verifique se há espaço em disco disponível."
        ) from e
        
    except Exception as e:
        logger.error(f"Erro inesperado ao criar planilha: {e}")
        raise


def editar_planilha_real(
    nome_arquivo: str,
    colunas: list[str],
    linhas: list[dict] | None = None,
    descricao: str = ""
) -> str:
    """Sobrescreve uma planilha existente com novas colunas e linhas."""
    try:
        # Remover extensão .xlsx se presente para evitar duplicação
        if nome_arquivo.endswith('.xlsx'):
            nome_arquivo = nome_arquivo[:-5]
        
        nome_seguro = sanitizar_nome_arquivo(nome_arquivo)
        pasta_absoluta = garantir_pasta_arquivos()
        caminho_completo = os.path.join(pasta_absoluta, f"{nome_seguro}.xlsx")

        if not os.path.exists(caminho_completo):
            raise ValueError(
                f"Arquivo '{nome_seguro}.xlsx' não encontrado na pasta de arquivos gerados."
            )

        wb = Workbook()
        ws = wb.active
        ws.title = "Dados"

        if descricao:
            ws.cell(row=1, column=1, value=descricao)
            ws.merge_cells(f"A1:{get_column_letter(len(colunas))}1")
            inicio = 3
        else:
            inicio = 1

        from openpyxl.styles import Font

        for col_idx, coluna in enumerate(colunas, start=1):
            ws.cell(row=inicio, column=col_idx, value=coluna).font = Font(bold=True)
            ws.column_dimensions[get_column_letter(col_idx)].width = max(len(str(coluna)) + 2, 10)

        if linhas:
            for row_idx, linha in enumerate(linhas, start=inicio + 1):
                for col_idx, nome_coluna in enumerate(colunas, start=1):
                    ws.cell(row=row_idx, column=col_idx, value=linha.get(nome_coluna, ""))

        wb.save(caminho_completo)
        logger.info(f"Planilha sobrescrita: {caminho_completo}")
        return caminho_completo

    except ValueError:
        raise
    except PermissionError as error:
        logger.error(f"Permissão negada ao editar planilha: {error}")
        raise PermissionError(
            "Não foi possível salvar o arquivo. Verifique as permissões da pasta de arquivos gerados."
        ) from error
    except OSError as error:
        logger.error(f"Erro de disco ao editar planilha: {error}")
        raise OSError(
            "Não foi possível salvar o arquivo. Verifique se há espaço em disco disponível."
        ) from error
    except Exception as error:
        logger.error(f"Erro inesperado ao editar planilha: {error}")
        raise
