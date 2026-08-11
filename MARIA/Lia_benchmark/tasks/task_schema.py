"""Schema para tarefas do benchmark."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskCategory(Enum):
    BASIC = "basic"
    TRANSFORMATION = "transformation"
    AGGREGATION = "aggregation"
    OPTION_HANDLING = "option_handling"
    RESULT_HANDLING = "result_handling"
    PATTERN_MATCHING = "pattern_matching"
    COMPOSITE = "composite"


class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


@dataclass
class TestCase:
    """Um caso de teste individual."""
    input_data: Any
    expected_output: Any
    description: str = ""


@dataclass
class Task:
    """Uma tarefa do benchmark."""
    id: int
    name: str
    description: str                    # Descrição em linguagem natural
    category: TaskCategory
    difficulty: Difficulty
    test_cases: List[TestCase] = field(default_factory=list)
    
    # Código de referência (para validação)
    reference_lia: Optional[str] = None
    reference_python: Optional[str] = None
    
    # Metadados
    requires_option: bool = False       # Usa Option?
    requires_result: bool = False       # Usa Result?
    requires_match: bool = False        # Usa pattern matching?
    requires_adt: bool = False          # Usa ADT customizado?
    
    # Prompts específicos por superfície
    prompt_lia: Optional[str] = None
    prompt_python: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "test_cases": [
                {
                    "input": tc.input_data,
                    "expected": tc.expected_output,
                    "description": tc.description
                }
                for tc in self.test_cases
            ],
            "requires_option": self.requires_option,
            "requires_result": self.requires_result,
            "requires_match": self.requires_match,
            "requires_adt": self.requires_adt,
        }


def load_all_tasks() -> List[Task]:
    """Carrega todas as tarefas de todos os módulos."""
    from .tasks_01_030 import TASKS_01_030
    from .tasks_031_040 import TASKS_031_040
    from .tasks_041_045 import TASKS_041_045
    from .tasks_046_050 import TASKS_046_050
    
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
