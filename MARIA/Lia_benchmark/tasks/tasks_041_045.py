"""Tarefas 41-45: Result e tratamento de erro."""
from .task_schema import Task, TestCase, TaskCategory, Difficulty

TASKS_041_045 = [
    Task(id=41, name="ok_value", description="Crie Result Ok.", category=TaskCategory.RESULT_HANDLING, difficulty=Difficulty.EASY, requires_result=True,
         test_cases=[TestCase({"x": 42}, {"Ok": 42})],
         reference_lia='(Ok 42)',
         reference_python='{"Ok": 42}'),

    Task(id=42, name="err_value", description="Crie Result Err.", category=TaskCategory.RESULT_HANDLING, difficulty=Difficulty.EASY, requires_result=True,
         test_cases=[TestCase({"msg": "fail"}, {"Err": "fail"})],
         reference_lia='(Err "fail")',
         reference_python='{"Err": "fail"}'),

    Task(id=43, name="result_map_double", description="Dobre valor em Result.", category=TaskCategory.RESULT_HANDLING, difficulty=Difficulty.MEDIUM, requires_result=True, requires_match=True,
         test_cases=[TestCase({"res": {"Ok": 21}}, {"Ok": 42}), TestCase({"res": {"Err": "erro"}}, {"Err": "erro"})],
         reference_lia='(match (Ok 21) ((Ok x) (Ok (* x 2))) ((Err e) (Err e)))',
         reference_python='{"Ok": 21 * 2} if 21 != None else {"Err": "erro"}'),

    Task(id=44, name="validate_positive_res", description="Se positivo, Ok; senão Err.", category=TaskCategory.RESULT_HANDLING, difficulty=Difficulty.MEDIUM, requires_result=True,
         test_cases=[TestCase({"n": 5}, {"Ok": 5}), TestCase({"n": -3}, {"Err": "negative"})],
         reference_lia='(if (> 5 0) (Ok 5) (Err "negative"))',
         reference_python='{"Ok": 5} if 5 > 0 else {"Err": "negative"}'),

    Task(id=45, name="result_to_option_conv", description="Result para Option.", category=TaskCategory.RESULT_HANDLING, difficulty=Difficulty.MEDIUM, requires_result=True, requires_option=True, requires_match=True,
         test_cases=[TestCase({"res": {"Ok": 42}}, {"Some": 42}), TestCase({"res": {"Err": "fail"}}, "None")],
         reference_lia='(match (Ok 42) ((Ok x) (Some x)) ((Err e) None))',
         reference_python='{"Some": 42} if 42 != None else None'),
]