"""Tarefas 46-50: Pattern matching e composição."""
from .task_schema import Task, TestCase, TaskCategory, Difficulty

TASKS_046_050 = [
    Task(id=46, name="match_literal", description="Match com literais.", category=TaskCategory.PATTERN_MATCHING, difficulty=Difficulty.EASY, requires_match=True,
         test_cases=[TestCase({"n": 0}, "zero"), TestCase({"n": 1}, "one"), TestCase({"n": 99}, "other")],
         reference_lia='(match 0 0 "zero" 1 "one" _ "other")',
         reference_python='"zero" if 0 == 0 else ("one" if 0 == 1 else "other")'),

    Task(id=47, name="nested_option_match", description="Extraia Option aninhado.", category=TaskCategory.PATTERN_MATCHING, difficulty=Difficulty.HARD, requires_option=True, requires_match=True,
         test_cases=[TestCase({"opt": {"Some": {"Some": 5}}}, 5), TestCase({"opt": {"Some": "None"}}, 0), TestCase({"opt": "None"}, -1)],
         reference_lia='(match (Some (Some 5)) ((Some (Some x)) x) ((Some None) 0) (None (- 0 1)))',
         reference_python='5 if 5 != None else (0 if 5 != None else -1)'),

    Task(id=48, name="pipeline_transform", description="Filtre positivos, dobre, some.", category=TaskCategory.COMPOSITE, difficulty=Difficulty.HARD,
         test_cases=[TestCase({"list": [-1, 2, -3, 4, 5]}, 22)],
         reference_lia='(fold (lambda (acc) (lambda (x) (+ acc x))) 0 (map (lambda (x) (* x 2)) (filter (lambda (x) (> x 0)) (list (- 0 1) 2 (- 0 3) 4 5))))',
         reference_python='sum([x * 2 for x in [-1, 2, -3, 4, 5] if x > 0])'),

    Task(id=49, name="safe_pipeline_parse", description="Parse string, se sucesso multiplique por 3.", category=TaskCategory.COMPOSITE, difficulty=Difficulty.HARD, requires_option=True, requires_match=True,
         test_cases=[TestCase({"s": "7"}, 21), TestCase({"s": "abc"}, 0)],
         reference_lia='(match (parse_int "7") ((Some n) (* n 3)) (None 0))',
         reference_python='int("7") * 3 if "7".isdigit() else 0'),

    Task(id=50, name="list_reverse_take_double", description="Reverta, pegue pares, dobre.", category=TaskCategory.COMPOSITE, difficulty=Difficulty.HARD,
         test_cases=[TestCase({"list": [1, 2, 3, 4, 5]}, [10, 8, 4])],
         reference_lia='(map (lambda (x) (* x 2)) (filter (lambda (x) (= (mod x 2) 0)) (reverse (list 1 2 3 4 5))))',
         reference_python='[x * 2 for x in reversed([1, 2, 3, 4, 5]) if x % 2 == 0]'),
]