"""Casos de borda do benchmark MARIA."""
from .task_schema import MariaTask, MariaTaskCategory


TASKS_EDGES = [
    MariaTask(16, "Ambiguidade planilha", "Duas confirmações ambíguas", "Crie uma planilha de projetos com Projeto e Status.", "criar_planilha", ["cancelada"], ["talvez", "hummm"], expected_final_message="cancelada", category=MariaTaskCategory.AMBIGUIDADE),
    MariaTask(17, "Ambiguidade documento", "Duas confirmações ambíguas", "Crie um documento sobre a reunião do projeto.", "criar_documento", ["cancelada"], ["talvez", "hummm"], expected_final_message="cancelada", category=MariaTaskCategory.AMBIGUIDADE),
    MariaTask(18, "Ambiguidade edição", "Duas confirmações ambíguas", "Edite a planilha existente projetos com Projeto e Status.", "editar_planilha", ["cancelada"], ["talvez", "hummm"], expected_final_message="cancelada", category=MariaTaskCategory.AMBIGUIDADE, context=[{"role": "assistant", "content": "A planilha projetos.xlsx já foi criada."}]),
    MariaTask(19, "Negação planilha", "Usuário recusa criação", "Crie uma planilha simples de tarefas.", "criar_planilha", ["cancelada"], ["não"], expected_final_message="cancelada", category=MariaTaskCategory.CANCELAMENTO),
    MariaTask(20, "Negação documento", "Usuário recusa documento", "Crie um documento com um aviso formal.", "criar_documento", ["cancelada"], ["não"], expected_final_message="cancelada", category=MariaTaskCategory.CANCELAMENTO),
    MariaTask(21, "Negação edição", "Usuário recusa sobrescrita", "Edite a planilha inexistente_futura com a coluna A.", None, ["não encontrado", "existir"], [], category=MariaTaskCategory.EDITAR_PLANILHA),
    MariaTask(22, "Edição inexistente A", "Arquivo não existe", "Edite a planilha arquivo_ausente_a com a coluna A.", None, ["não encontrado", "existir"], [], category=MariaTaskCategory.EDITAR_PLANILHA),
    MariaTask(23, "Edição inexistente B", "Arquivo não existe", "Atualize a planilha arquivo_ausente_b com as colunas X e Y.", None, ["não encontrado", "existir"], [], category=MariaTaskCategory.EDITAR_PLANILHA),
    MariaTask(24, "Nome com caminho relativo", "Nome precisa ser sanitizado", "Crie uma planilha chamada ../../teste_seguro com a coluna Nome.", "criar_planilha", ["planilha"], ["sim"], category=MariaTaskCategory.CRIAR_PLANILHA),
    MariaTask(25, "Nome com caracteres inseguros", "Nome precisa ser sanitizado", "Crie um documento chamado ../relatório*seguro com conteúdo de teste.", "criar_documento", ["documento"], ["sim"], category=MariaTaskCategory.CRIAR_DOCUMENTO),
]
