"""
Módulo que define o esquema das ferramentas (function calling) para a MARIA.
Estas ferramentas serão usadas pelo modelo Qwen2.5-3B via Ollama para identificar
intenções do usuário relacionadas a planilhas e documentos.

As ferramentas são executadas após confirmação explícita do usuário.
"""

import logging

# Configurar logger do módulo
logger = logging.getLogger(__name__)

CAMPOS_OBRIGATORIOS = {
    "criar_planilha": ["nome_arquivo", "colunas"],
    "criar_documento": ["nome_arquivo", "titulo", "conteudo"],
    "editar_planilha": ["nome_arquivo", "colunas"],
}

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
                    "description": "Título principal do documento. Campo obrigatório: se o usuário não indicar um título explícito, gere um título curto e apropriado com base no conteúdo. Ex: 'Relatório de Vendas - Janeiro 2025', ou 'Carta de Apresentação' para uma carta sem título informado."
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

FERRAMENTA_LISTAR_ARQUIVOS = {
    "type": "function",
    "function": {
        "name": "listar_arquivos",
        "description": """Lista os arquivos existentes em uma pasta permitida (somente leitura, não modifica nada).
Use PARA: responder o que existe em uma pasta ou diretório.
Exemplos de frases-gatilho:
- "que arquivos tem na pasta docs?"
- "o que já foi criado na pasta de arquivos gerados?"
NÃO use para criar, editar ou apagar arquivos.""",
        "parameters": {
            "type": "object",
            "properties": {
                "pasta": {
                    "type": "string",
                    "description": "Nome ou caminho relativo da pasta dentro das permitidas. Deixe vazio para a pasta padrão."
                }
            },
            "required": []
        }
    }
}

FERRAMENTA_RESUMIR_DOCUMENTO = {
    "type": "function",
    "function": {
        "name": "resumir_documento",
        "description": """Lê um documento de texto (.txt, .md, .csv, .log, .docx) de uma pasta permitida e disponibiliza o conteúdo para você resumir, analisar ou extrair informações. Somente leitura, não modifica nada.
Use PARA: resumir, analisar ou extrair trechos de um documento já existente.
Exemplos de frases-gatilho:
- "resuma o arquivo notas_reuniao.txt"
- "do que trata o documento ata.docx?"
NÃO use para criar um documento novo — nesse caso use criar_documento.""",
        "parameters": {
            "type": "object",
            "properties": {
                "nome_arquivo": {
                    "type": "string",
                    "description": "Nome do arquivo a ler. Ex.: 'relatorio.txt', 'ata.docx'"
                },
                "instrucoes": {
                    "type": "string",
                    "description": "O que fazer com o conteúdo. Ex.: 'resuma em 5 tópicos'"
                }
            },
            "required": ["nome_arquivo"]
        }
    }
}

# Ferramentas de leitura: executadas sem confirmação (não modificam nada)
FERRAMENTAS_LEITURA = {"listar_arquivos", "resumir_documento"}

# Lista de todas as ferramentas disponíveis
TOOLS_SCHEMA = [
    FERRAMENTA_CRIAR_PLANILHA,
    FERRAMENTA_CRIAR_DOCUMENTO,
    FERRAMENTA_EDITAR_PLANILHA,
    FERRAMENTA_LISTAR_ARQUIVOS,
    FERRAMENTA_RESUMIR_DOCUMENTO,
]


def validar_argumentos_obrigatorios(nome_funcao: str, argumentos: dict) -> None:
    """
    Valida se todos os campos obrigatórios da ferramenta estão presentes
    e não vazios em `argumentos`.

    Raises:
        ValueError: se algum campo obrigatório estiver ausente, None,
            string vazia/só espaços, ou lista vazia.
    """
    campos = CAMPOS_OBRIGATORIOS.get(nome_funcao, [])
    faltando = []
    for campo in campos:
        valor = argumentos.get(campo)
        if valor is None:
            faltando.append(campo)
        elif isinstance(valor, str) and not valor.strip():
            faltando.append(campo)
        elif isinstance(valor, list) and len(valor) == 0:
            faltando.append(campo)
    if faltando:
        raise ValueError(
            f"Não foi possível executar '{nome_funcao}': "
            f"campo(s) obrigatório(s) ausente(s) ou vazio(s): {', '.join(faltando)}."
        )


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
    validar_argumentos_obrigatorios(nome_funcao, argumentos)
    
    if nome_funcao == "criar_planilha":
        from core.excel_handler import criar_planilha_real
        caminho = criar_planilha_real(
            nome_arquivo=argumentos.get("nome_arquivo", "planilha"),
            colunas=argumentos.get("colunas", []),
            descricao=argumentos.get("descricao", "")
        )
        return f"Planilha criada com sucesso: {caminho}"
        
    elif nome_funcao == "criar_documento":
        from core.word_handler import criar_documento_real
        caminho = criar_documento_real(
            nome_arquivo=argumentos.get("nome_arquivo", "documento"),
            titulo=argumentos.get("titulo", "Sem título"),
            conteudo=argumentos.get("conteudo", "")
        )
        return f"Documento criado com sucesso: {caminho}"

    elif nome_funcao == "editar_planilha":
        from core.excel_handler import editar_planilha_real
        caminho = editar_planilha_real(
            nome_arquivo=argumentos.get("nome_arquivo", ""),
            colunas=argumentos.get("colunas", []),
            linhas=argumentos.get("linhas"),
            descricao=argumentos.get("descricao", "")
        )
        return f"Planilha atualizada com sucesso: {caminho}"
        
    else:
        raise ValueError(f"Ferramenta desconhecida: {nome_funcao}")


def executar_ferramenta_leitura(nome_funcao: str, argumentos: dict) -> str:
    """
    Executa uma ferramenta de LEITURA (não modifica arquivos) e retorna o
    resultado como texto, pronto para ser devolvido ao modelo.

    Args:
        nome_funcao: "listar_arquivos" ou "resumir_documento"
        argumentos: argumentos da tool call

    Returns:
        Texto com o resultado da leitura.

    Raises:
        ValueError: se a ferramenta não for reconhecida (propaga ValueError/
            PermissionError/OSError vindos de core.file_utils para os demais casos).
    """
    logger.info(f"Executando ferramenta de leitura: {nome_funcao}({argumentos})")

    if nome_funcao == "listar_arquivos":
        from core.file_utils import listar_arquivos
        itens = listar_arquivos(argumentos.get("pasta", ""))
        if not itens:
            return "A pasta está vazia (nenhum arquivo encontrado)."
        linhas = "\n".join(f"- {i['nome']} ({i['tamanho_kb']} KB)" for i in itens)
        return f"Arquivos encontrados:\n{linhas}"

    elif nome_funcao == "resumir_documento":
        from core.file_utils import ler_documento
        doc = ler_documento(argumentos.get("nome_arquivo", ""))
        aviso = ""
        if doc["truncado"]:
            aviso = (f"\n[Atenção: conteúdo truncado em {len(doc['texto'])} de "
                     f"{doc['total_chars']} caracteres; considere apenas a parte inicial.]")
        cabecalho = f"Conteúdo do arquivo {doc['nome']}:"
        instrucoes = argumentos.get("instrucoes", "")
        if instrucoes:
            cabecalho += f"\nPedido do usuário: {instrucoes}"
        return f"{cabecalho}{aviso}\n\n{doc['texto']}"

    else:
        raise ValueError(f"Ferramenta de leitura desconhecida: {nome_funcao}")
