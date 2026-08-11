"""Tarefas 31-40: Option e tratamento de ausência."""
from .task_schema import Task, TestCase, TaskCategory, Difficulty

TASKS_031_040 = [
    Task(id=31, name="safe_parse_int", description="Parse string para int com Option.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.EASY, requires_option=True,
         test_cases=[TestCase({"s": "42"}, {"Some": 42}), TestCase({"s": "abc"}, "None")],
         reference_lia='(parse_int "42")',
         reference_python='int("42") if "42".isdigit() else None'),

    Task(id=32, name="option_map_double", description="Dobre valor em Option.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.MEDIUM, requires_option=True, requires_match=True,
         test_cases=[TestCase({"opt": {"Some": 21}}, {"Some": 42}), TestCase({"opt": "None"}, "None")],
         reference_lia='(match (Some 21) ((Some x) (Some (* x 2))) (None None))',
         reference_python='{"Some": 21 * 2} if 21 != None else None'),

    Task(id=33, name="option_default", description="Extraia Option com default.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.EASY, requires_option=True, requires_match=True,
         test_cases=[TestCase({"opt": {"Some": 42}, "default": 0}, 42), TestCase({"opt": "None", "default": 0}, 0)],
         reference_lia='(match (Some 42) ((Some x) x) (None 0))',
         reference_python='42 if 42 != None else 0'),

    Task(id=34, name="chain_option_positive", description="Se Option positivo, triplique.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.MEDIUM, requires_option=True, requires_match=True,
         test_cases=[TestCase({"opt": {"Some": 5}}, {"Some": 15}), TestCase({"opt": {"Some": -3}}, "None"), TestCase({"opt": "None"}, "None")],
         reference_lia='(match (Some 5) ((Some x) (Some (* x 3))) (None None))',
         reference_python='{"Some": 5 * 3} if 5 > 0 else None'),

    Task(id=35, name="safe_divide_opt", description="Divisão segura com Option.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.EASY, requires_option=True,
         test_cases=[TestCase({"a": 10, "b": 2}, {"Some": 5}), TestCase({"a": 10, "b": 0}, "None")],
         reference_lia='(if (= 2 0) None (Some (/ 10 2)))',
         reference_python='{"Some": 10 // 2} if 2 != 0 else None'),

    Task(id=36, name="head_option", description="Primeiro elemento como Option.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.EASY, requires_option=True,
         test_cases=[TestCase({"list": [1, 2, 3]}, {"Some": 1}), TestCase({"list": []}, "None")],
         reference_lia='(head (list 1 2 3))',
         reference_python='{"Some": [1, 2, 3][0]} if [1, 2, 3] else None'),

    Task(id=37, name="nth_option", description="N-ésimo elemento como Option.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.MEDIUM, requires_option=True,
         test_cases=[TestCase({"list": [10, 20, 30], "n": 1}, {"Some": 20}), TestCase({"list": [10, 20, 30], "n": 5}, "None")],
         reference_lia='(nth (list 10 20 30) 1)',
         reference_python='{"Some": [10, 20, 30][1]} if 0 <= 1 < len([10, 20, 30]) else None'),

    Task(id=38, name="find_even", description="Primeiro par como Option.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.HARD, requires_option=True, requires_match=True,
         test_cases=[TestCase({"list": [1, 3, 4, 6]}, {"Some": 4}), TestCase({"list": [1, 3, 5]}, "None")],
         reference_lia='(filter (lambda (x) (= (mod x 2) 0)) (list 1 3 4 6))',
         reference_python='[x for x in [1, 3, 4, 6] if x % 2 == 0]'),

    Task(id=39, name="option_to_result_conv", description="Option para Result.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.MEDIUM, requires_option=True, requires_result=True, requires_match=True,
         test_cases=[TestCase({"opt": {"Some": 42}}, {"Ok": 42}), TestCase({"opt": "None"}, {"Err": "not found"})],
         reference_lia='(match (Some 42) ((Some x) (Ok x)) (None (Err "not found")))',
         reference_python='{"Ok": 42} if 42 != None else {"Err": "not found"}'),

    Task(id=40, name="parse_and_double_opt", description="Parse e dobre com Option.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.MEDIUM, requires_option=True, requires_match=True,
         test_cases=[TestCase({"s": "21"}, {"Some": 42}), TestCase({"s": "abc"}, "None")],
         reference_lia='(match (parse_int "21") ((Some n) (Some (* n 2))) (None None))',
         reference_python='{"Some": int("21") * 2} if "21".isdigit() else None'),
]