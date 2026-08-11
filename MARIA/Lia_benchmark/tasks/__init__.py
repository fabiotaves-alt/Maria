"""Tasks module for Lia benchmark."""
from .task_schema import Task, TestCase, TaskCategory, Difficulty
from .tasks_01_030 import TASKS_01_030
from .tasks_031_040 import TASKS_031_040
from .tasks_041_045 import TASKS_041_045
from .tasks_046_050 import TASKS_046_050


def load_all_tasks():
    """Carrega todas as tarefas de todos os módulos."""
    all_tasks = (
        TASKS_01_030 + 
        TASKS_031_040 + 
        TASKS_041_045 + 
        TASKS_046_050
    )
    
    # Ordena por ID e valida unicidade
    all_tasks.sort(key=lambda t: t.id)
    ids = [t.id for t in all_tasks]
    assert len(ids) == len(set(ids)), "IDs de tarefas duplicados!"
    
    return all_tasks