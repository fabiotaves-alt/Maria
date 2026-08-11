"""Catálogo de tarefas do benchmark MARIA."""
from .task_schema import MariaTask, MariaTaskResult, MariaTaskCategory
from .tasks_core import TASKS_CORE
from .tasks_edges import TASKS_EDGES


def load_all_maria_tasks() -> list[MariaTask]:
    all_tasks = TASKS_CORE + TASKS_EDGES
    all_tasks.sort(key=lambda task: task.id)
    ids = [task.id for task in all_tasks]
    assert len(ids) == len(set(ids)), "IDs de tarefas duplicados no benchmark MARIA!"
    return all_tasks
