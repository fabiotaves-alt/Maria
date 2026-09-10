"""Contratos de tool call — lista de campos obrigatorios por ferramenta.

Modulo de dominio: constante pura, sem I/O, sem dependencia de
infrastructure/application. Extraida de infrastructure/tools/tools_schema.py
na fase B7a para permitir que domain/validacao_tool_call.py deixe de
importar infrastructure (violacao de camada corrigida).
"""

CAMPOS_OBRIGATORIOS = {
    # Escrita
    "criar_planilha": ["nome_arquivo", "colunas"],
    "criar_documento": ["nome_arquivo", "titulo", "conteudo"],
    "editar_planilha": ["nome_arquivo", "colunas"],
    # Leitura
    "listar_arquivos": [],  # nenhum campo obrigatório
    "resumir_documento": ["nome_arquivo"],
    "extrair_dados_planilha": ["nome_arquivo"],
    "consultar_manual_redacao": ["tipo_documento"],
}
