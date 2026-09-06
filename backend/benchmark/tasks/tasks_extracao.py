"""
Tarefas de extração, transformação e resumo — benchmark MARIA.

Validam o uso das ferramentas de leitura do sistema:
    - extrair_dados_planilha (com paginação por offset)
    - resumir_documento
    - listar_arquivos

Numeração a partir de 26 (tasks_core: 1-15, tasks_edges: 16-25).
"""
from .task_schema import MariaTask, MariaTaskCategory


TASKS_EXTRACAO = [

    # ------------------------------------------------------------------
    # Task 26 — Tradução de planilha real (Mandarim → Inglês)
    # Cenário real de escritório de importação: planilha com produtos em
    # Mandarim, coluna 'english description' vazia. Modelo deve ler com
    # extrair_dados_planilha, traduzir e criar nova planilha com a coluna
    # preenchida.
    # ------------------------------------------------------------------
    MariaTask(
        id=26,
        name="Tradução de planilha (Mandarim → Inglês)",
        description=(
            "Planilha real de escritório com produtos em Mandarim. "
            "Modelo deve extrair os dados, traduzir a coluna 'product' "
            "para inglês e salvar o resultado como nova planilha."
        ),
        user_message=(
            "Tenho uma planilha chamada 'produtos_mandarim' com produtos "
            "descritos em Mandarim. Preencha a coluna 'english description' "
            "traduzindo a coluna 'product' para inglês e salve o resultado "
            "como 'produtos_traduzidos'."
        ),
        expected_tool="criar_planilha",
        expected_keywords=["traduzida", "traduzidos", "criada", "sucesso", "english"],
        confirm_sequence=["sim"],
        category=MariaTaskCategory.CRIAR_PLANILHA,
        fixtures=["produtos_mandarim"],
        tools_obrigatorios=["extrair_dados_planilha", "criar_planilha"],
        expected_args_subset={
            "nome_arquivo": "produtos_traduzidos",
            "colunas": ["model", "product", "english description", "NCM"],
        },
        context=[{
            "role": "assistant",
            "content": "A planilha produtos_mandarim.xlsx está disponível na pasta de arquivos.",
        }],
    ),

    # ------------------------------------------------------------------
    # Task 27 — Resumo de planilha existente
    # Modelo deve extrair dados e responder com resumo textual.
    # Sem ferramenta de escrita — termina em texto.
    # ------------------------------------------------------------------
    MariaTask(
        id=27,
        name="Resumo de planilha",
        description=(
            "Modelo deve extrair dados da planilha e responder com resumo "
            "textual sem criar arquivo novo."
        ),
        user_message=(
            "Me dê um resumo do conteúdo da planilha 'produtos_mandarim': "
            "quantos produtos há, quais os códigos NCM presentes e "
            "quantos produtos têm a descrição em inglês preenchida."
        ),
        expected_tool=None,
        expected_keywords=["produto", "ncm", "descri"],
        confirm_sequence=[],
        category=MariaTaskCategory.CONVERSA,
        fixtures=["produtos_mandarim"],
        tools_obrigatorios=["extrair_dados_planilha"],
        context=[{
            "role": "assistant",
            "content": "A planilha produtos_mandarim.xlsx está disponível na pasta de arquivos.",
        }],
    ),

    # ------------------------------------------------------------------
    # Task 28 — Listar arquivos disponíveis
    # Valida listar_arquivos sem ferramenta de escrita subsequente.
    # ------------------------------------------------------------------
    MariaTask(
        id=28,
        name="Listar arquivos disponíveis",
        description=(
            "Modelo deve listar os arquivos da pasta e informar "
            "quais estão disponíveis para trabalho."
        ),
        user_message="Quais arquivos estão disponíveis na pasta de arquivos gerados?",
        expected_tool=None,
        expected_keywords=["arquivo", "planilha", "xlsx"],
        confirm_sequence=[],
        category=MariaTaskCategory.CONVERSA,
        fixtures=["produtos_mandarim"],
        tools_obrigatorios=["listar_arquivos"],
    ),
]