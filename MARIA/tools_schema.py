"""
Módulo que define o esquema das ferramentas (function calling) para a MARIA.
Estas ferramentas serão usadas pelo modelo Qwen2.5-3B via Ollama para identificar
intenções do usuário relacionadas a planilhas e documentos.

As ferramentas são executadas após confirmação explícita do usuário.
"""

import logging

# Configurar logger do módulo
logger = logging.getLogger(__name__)

# Esquema JSON para a ferramenta de criação de planilha
FERRAMENTA_CRIAR_PLANILHA = {
    "type": "function",
    "function": {
        "name": "criar_planilha",
        "description": """Cria uma nova planilha Excel com colunas estruturadas em linhas e colunas.
Use PARA: dados tabulares, controle financeiro, listas com múltiplas colunas, relatórios numéricos, inventários, orçamentos.
Exemplos de frases-gatilho:
- "crie uma planilha de gastos"
- "quero uma tabela com colunas para nome, idade e salário"
- "preciso de um arquivo Excel para controle de estoque"
NÃO use para textos corridos ou documentos narrativos.""",
        "parameters": {
            "type": "object",
            "properties": {
                "nome_arquivo": {
                    "type": "string",
                    "description": "Nome do arquivo da planilha (sem extensão). Ex: 'controle_gastos'"
                },
                "colunas": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Lista de nomes das colunas da planilha. Ex: ['Data', 'Descrição', 'Valor', 'Categoria']"
                },
                "descricao": {
                    "type": "string",
                    "description": "Descrição breve do propósito da planilha. Ex: 'Planilha para controle mensal de gastos do escritório'"
                }
            },
            "required": ["nome_arquivo", "colunas"]
        }
    }
}

# Esquema JSON para a ferramenta de criação de documento
FERRAMENTA_CRIAR_DOCUMENTO = {
    "type": "function",
    "function": {
        "name": "criar_documento",
        "description": """Cria um novo documento de texto (Word) com conteúdo narrativo completo, gerado pelo próprio modelo.
Use PARA: textos corridos, cartas, relatórios narrativos, comunicados, memorandos, mensagens formais.
    O campo 'conteudo' deve conter o texto completo e coerente do documento, com parágrafos separados por uma linha em branco (\\n\\n).
Exemplos de frases-gatilho:
- "crie um texto sobre reunião"
- "quero um documento com uma carta de apresentação"
- "preciso de um relatório em formato de texto"
NÃO use para dados estruturados em colunas ou tabelas.""",
        "parameters": {
            "type": "object",
            "properties": {
                "nome_arquivo": {
                    "type": "string",
                    "description": "Nome do arquivo do documento (sem extensão). Ex: 'relatorio_mensal'"
                },
                "titulo": {
                    "type": "string",
                    "description": "Título principal do documento. Ex: 'Relatório de Vendas - Janeiro 2025'"
                },
                "conteudo": {
                    "type": "string",
                    "description": "Texto completo e coerente do documento, com parágrafos separados por uma linha em branco (\\n\\n)."
                }
            },
            "required": ["nome_arquivo", "titulo", "conteudo"]
        }
    }
}

FERRAMENTA_EDITAR_PLANILHA = {
    "type": "function",
    "function": {
        "name": "editar_planilha",
        "description": """Substitui completamente uma planilha existente por uma nova estrutura de colunas e, opcionalmente, linhas de dados. O arquivo original é sobrescrito.
Use PARA: corrigir colunas, adicionar/remover campos ou atualizar dados de uma planilha já criada.
NÃO use se a planilha ainda não existir — nesse caso use criar_planilha.""",
        "parameters": {
            "type": "object",
            "properties": {
                "nome_arquivo": {
                    "type": "string",
                    "description": "Nome exato do arquivo sem extensão a ser sobrescrito."
                },
                "colunas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Nova lista de nomes de colunas."
                },
                "linhas": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Linhas opcionais com chaves iguais aos nomes das colunas."
                },
                "descricao": {
                    "type": "string",
                    "description": "Descrição opcional da planilha."
                }
            },
            "required": ["nome_arquivo", "colunas"]
        }
    }
}

# Lista de todas as ferramentas disponíveis
TOOLS_SCHEMA = [
    FERRAMENTA_CRIAR_PLANILHA,
    FERRAMENTA_CRIAR_DOCUMENTO,
    FERRAMENTA_EDITAR_PLANILHA
]


def simular_execucao_ferramenta(nome_funcao: str, argumentos: dict) -> str:
    """
    Simula a execução de uma ferramenta (utilitário de debug/teste).
    Não faz parte do fluxo principal, que usa executar_ferramenta_real.
    
    Args:
        nome_funcao: Nome da função a ser executada
        argumentos: Dicionário com os argumentos da chamada
        
    Returns:
        String descrevendo a simulação da execução
    """
    logger.debug(f"Chamada de ferramenta detectada: {nome_funcao}({argumentos})")
    
    if nome_funcao == "criar_planilha":
        return f"[SIMULAÇÃO] Planilha '{argumentos.get('nome_arquivo', 'desconhecido')}' seria criada com {len(argumentos.get('colunas', []))} colunas."
    elif nome_funcao == "criar_documento":
        return f"[SIMULAÇÃO] Documento '{argumentos.get('nome_arquivo', 'desconhecido')}' seria criado com o título '{argumentos.get('titulo', 'Sem título')}'."
    else:
        return f"[SIMULAÇÃO] Função '{nome_funcao}' desconhecida."


def executar_ferramenta_real(nome_funcao: str, argumentos: dict) -> str:
    """
    Executa realmente uma ferramenta, criando o arquivo correspondente.
    
    Args:
        nome_funcao: Nome da função a ser executada
        argumentos: Dicionário com os argumentos da chamada
        
    Returns:
        Caminho absoluto do arquivo criado ou mensagem de erro
        
    Raises:
        ValueError: Se a função não for reconhecida
    """
    logger.info(f"Executando ferramenta real: {nome_funcao}({argumentos})")
    
    if nome_funcao == "criar_planilha":
        from excel_handler import criar_planilha_real
        caminho = criar_planilha_real(
            nome_arquivo=argumentos.get("nome_arquivo", "planilha"),
            colunas=argumentos.get("colunas", []),
            descricao=argumentos.get("descricao", "")
        )
        return f"Planilha criada com sucesso: {caminho}"
        
    elif nome_funcao == "criar_documento":
        from word_handler import criar_documento_real
        caminho = criar_documento_real(
            nome_arquivo=argumentos.get("nome_arquivo", "documento"),
            titulo=argumentos.get("titulo", "Sem título"),
            conteudo=argumentos.get("conteudo", "")
        )
        return f"Documento criado com sucesso: {caminho}"

    elif nome_funcao == "editar_planilha":
        from excel_handler import editar_planilha_real
        caminho = editar_planilha_real(
            nome_arquivo=argumentos.get("nome_arquivo", ""),
            colunas=argumentos.get("colunas", []),
            linhas=argumentos.get("linhas"),
            descricao=argumentos.get("descricao", "")
        )
        return f"Planilha atualizada com sucesso: {caminho}"
        
    else:
        raise ValueError(f"Ferramenta desconhecida: {nome_funcao}")
