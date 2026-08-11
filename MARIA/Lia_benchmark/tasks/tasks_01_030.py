"""Tarefas 01-30: Benchmark principal com sintaxe válida Lia."""
from .task_schema import Task, TestCase, TaskCategory, Difficulty

TASKS_01_030 = [
    # === ARITMÉTICA BÁSICA (1-5) ===
    Task(id=1, name="addition", description="Some dois números.", category=TaskCategory.BASIC, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"a": 3, "b": 4}, 7), TestCase({"a": 0, "b": 0}, 0)],
         reference_lia='((lambda (a) ((lambda (b) (+ a b)) 3)) 4)',
         reference_python='3 + 4'),

    Task(id=2, name="multiplication", description="Multiplique dois números.", category=TaskCategory.BASIC, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"a": 6, "b": 7}, 42)],
         reference_lia='(* 6 7)',
         reference_python='6 * 7'),

    Task(id=3, name="integer_division", description="Divisão inteira.", category=TaskCategory.BASIC, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"a": 10, "b": 3}, 3)],
         reference_lia='(/ 10 3)',
         reference_python='10 // 3'),

    Task(id=4, name="absolute_value", description="Valor absoluto.", category=TaskCategory.BASIC, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"n": -5}, 5), TestCase({"n": 3}, 3)],
         reference_lia='(abs (- 0 5))',
         reference_python='abs(-5)'),

    Task(id=5, name="max_of_two", description="Maior de dois números.", category=TaskCategory.BASIC, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"a": 3, "b": 7}, 7)],
         reference_lia='(max 3 7)',
         reference_python='max(3, 7)'),

    # === CONDICIONAIS (6-10) ===
    Task(id=6, name="classify_sign", description="Retorne 1 se positivo, -1 se negativo, 0 se zero.", category=TaskCategory.BASIC, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"n": 42}, 1), TestCase({"n": -7}, -1), TestCase({"n": 0}, 0)],
         reference_lia='(if (> 42 0) 1 (if (< 42 0) (- 0 1) 0))',
         reference_python='1 if 42 > 0 else (-1 if 42 < 0 else 0)'),

    Task(id=7, name="is_even", description="Verifique se é par.", category=TaskCategory.BASIC, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"n": 4}, True), TestCase({"n": 7}, False)],
         reference_lia='(= (mod 4 2) 0)',
         reference_python='4 % 2 == 0'),

    Task(id=8, name="clamp", description="Restrinja valor a [min, max].", category=TaskCategory.BASIC, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"v": 15, "lo": 0, "hi": 10}, 10), TestCase({"v": -5, "lo": 0, "hi": 10}, 0)],
         reference_lia='(let ((v 15)) (let ((lo 0)) (let ((hi 10)) (if (< v lo) lo (if (> v hi) hi v)))))',
         reference_python='v = 15; lo = 0; hi = 10; lo if v < lo else (hi if v > hi else v)'),

    Task(id=9, name="fizzbuzz_single", description="fizz/buzz/fizzbuzz/número.", category=TaskCategory.BASIC, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"n": 15}, "fizzbuzz"), TestCase({"n": 3}, "fizz"), TestCase({"n": 7}, "7")],
         reference_lia='(let ((n 15)) (if (= (mod n 15) 0) "fizzbuzz" (if (= (mod n 3) 0) "fizz" (if (= (mod n 5) 0) "buzz" (str_of n)))))',
         reference_python='n = 15; "fizzbuzz" if n % 15 == 0 else ("fizz" if n % 3 == 0 else ("buzz" if n % 5 == 0 else str(n)))'),

    Task(id=10, name="nested_if", description="Classifique idade: child/teenager/adult/senior.", category=TaskCategory.BASIC, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"age": 8}, "child"), TestCase({"age": 15}, "teenager"), TestCase({"age": 30}, "adult"), TestCase({"age": 70}, "senior")],
         reference_lia='(let ((age 30)) (if (< age 13) "child" (if (< age 20) "teenager" (if (< age 65) "adult" "senior"))))',
         reference_python='age = 30; "child" if age < 13 else ("teenager" if age < 20 else ("adult" if age < 65 else "senior"))'),

    # === RECURSÃO (11-15) ===
    Task(id=11, name="factorial", description="Fatorial.", category=TaskCategory.BASIC, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"n": 5}, 120), TestCase({"n": 0}, 1)],
         reference_lia='(letrec ((fact (lambda (n) (if (<= n 1) 1 (* n (fact (- n 1))))))) (fact 5))',
         reference_python='def fact(n):\n    return 1 if n <= 1 else n * fact(n - 1)\nfact(5)'),

    Task(id=12, name="fibonacci", description="Fibonacci.", category=TaskCategory.BASIC, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"n": 10}, 55), TestCase({"n": 0}, 0)],
         reference_lia='(letrec ((fib (lambda (n) (if (< n 2) n (+ (fib (- n 1)) (fib (- n 2))))))) (fib 10))',
         reference_python='def fib(n):\n    return n if n < 2 else fib(n - 1) + fib(n - 2)\nfib(10)'),

    Task(id=13, name="sum_to_n", description="Soma de 1 a n.", category=TaskCategory.BASIC, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"n": 10}, 55), TestCase({"n": 100}, 5050)],
         reference_lia='(letrec ((sum (lambda (n) (if (= n 0) 0 (+ n (sum (- n 1))))))) (sum 10))',
         reference_python='def sum_to(n):\n    return 0 if n == 0 else n + sum_to(n - 1)\nsum_to(10)'),

    Task(id=14, name="power", description="base^exp.", category=TaskCategory.BASIC, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"base": 2, "exp": 10}, 1024)],
         reference_lia='(letrec ((pow (lambda (b) (lambda (e) (if (= e 0) 1 (* b ((pow b) (- e 1)))))))) ((pow 2) 10))',
         reference_python='def pow(b, e):\n    return 1 if e == 0 else b * pow(b, e - 1)\npow(2, 10)'),

    Task(id=15, name="gcd", description="MDC via Euclides.", category=TaskCategory.BASIC, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"a": 12, "b": 8}, 4), TestCase({"a": 100, "b": 75}, 25)],
         reference_lia='(letrec ((gcd (lambda (a) (lambda (b) (if (= b 0) a ((gcd b) (mod a b))))))) ((gcd 12) 8))',
         reference_python='def gcd(a, b):\n    return a if b == 0 else gcd(b, a % b)\ngcd(12, 8)'),

    # === LISTAS (16-20) ===
    Task(id=16, name="sum_list", description="Some elementos de uma lista.", category=TaskCategory.TRANSFORMATION, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"list": [1, 2, 3, 4, 5]}, 15), TestCase({"list": []}, 0)],
         reference_lia='(fold (lambda (acc) (lambda (x) (+ acc x))) 0 (list 1 2 3 4 5))',
         reference_python='sum([1, 2, 3, 4, 5])'),

    Task(id=17, name="double_list", description="Dobre cada elemento.", category=TaskCategory.TRANSFORMATION, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"list": [1, 2, 3]}, [2, 4, 6])],
         reference_lia='(map (lambda (x) (* x 2)) (list 1 2 3))',
         reference_python='[x * 2 for x in [1, 2, 3]]'),

    Task(id=18, name="filter_positive", description="Filtre positivos.", category=TaskCategory.TRANSFORMATION, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"list": [-2, 3, -1, 5, 0, 7]}, [3, 5, 7])],
         reference_lia='(filter (lambda (x) (> x 0)) (list (- 0 2) 3 (- 0 1) 5 0 7))',
         reference_python='[x for x in [-2, 3, -1, 5, 0, 7] if x > 0]'),

    Task(id=19, name="list_length", description="Comprimento da lista.", category=TaskCategory.BASIC, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"list": [1, 2, 3]}, 3), TestCase({"list": []}, 0)],
         reference_lia='(length (list 1 2 3))',
         reference_python='len([1, 2, 3])'),

    Task(id=20, name="reverse_list", description="Reverta lista.", category=TaskCategory.TRANSFORMATION, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"list": [1, 2, 3]}, [3, 2, 1])],
         reference_lia='(reverse (list 1 2 3))',
         reference_python='list(reversed([1, 2, 3]))'),

    # === OPTION / AUSÊNCIA (21-25) ===
    Task(id=21, name="safe_parse_int", description="Parse int com Option.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.MEDIUM,
         requires_option=True,
         test_cases=[TestCase({"s": "42"}, {"Some": 42}), TestCase({"s": "abc"}, "None")],
         reference_lia='(parse_int "42")',
         reference_python='int("42") if "42".isdigit() else None'),

    Task(id=22, name="option_map", description="Dobre valor dentro de Option.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.MEDIUM,
         requires_option=True, requires_match=True,
         test_cases=[TestCase({"opt": {"Some": 21}}, {"Some": 42}), TestCase({"opt": "None"}, "None")],
         reference_lia='(match (Some 21) ((Some x) (Some (* x 2))) (None None))',
         reference_python='{"Some": 21 * 2} if 21 != None else None'),

    Task(id=23, name="option_default", description="Extraia Option com default.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.EASY,
         requires_option=True, requires_match=True,
         test_cases=[TestCase({"opt": {"Some": 42}, "default": 0}, 42), TestCase({"opt": "None", "default": 0}, 0)],
         reference_lia='(match (Some 42) ((Some x) x) (None 0))',
         reference_python='42 if 42 != None else 0'),

    Task(id=24, name="chain_option", description="Option: se positivo, triplique; senão None.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.MEDIUM,
         requires_option=True, requires_match=True,
         test_cases=[TestCase({"opt": {"Some": 5}}, {"Some": 15}), TestCase({"opt": {"Some": -3}}, "None")],
         reference_lia='(match (Some 5) ((Some x) (Some (* x 3))) (None None))',
         reference_python='{"Some": 5 * 3} if 5 > 0 else None'),

    Task(id=25, name="safe_divide", description="Divisão segura com Option.", category=TaskCategory.OPTION_HANDLING, difficulty=Difficulty.EASY,
         requires_option=True,
         test_cases=[TestCase({"a": 10, "b": 2}, {"Some": 5}), TestCase({"a": 10, "b": 0}, "None")],
         reference_lia='(if (= 2 0) None (Some (/ 10 2)))',
         reference_python='{"Some": 10 // 2} if 2 != 0 else None'),

    # === COMPOSIÇÃO / TRANSFORMAÇÃO (26-30) ===
    Task(id=26, name="compose", description="Dobre e depois incremente.", category=TaskCategory.TRANSFORMATION, difficulty=Difficulty.EASY,
         test_cases=[TestCase({"x": 5}, 11)],
         reference_lia='(let ((double (lambda (x) (* x 2))) (inc (lambda (x) (+ x 1)))) (inc (double 5)))',
         reference_python='double = lambda x: x * 2; inc = lambda x: x + 1; inc(double(5))'),

    Task(id=27, name="conditional_transform", description="Par: divida por 2. Ímpar: 3n+1.", category=TaskCategory.TRANSFORMATION, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"n": 10}, 5), TestCase({"n": 7}, 22)],
         reference_lia='(let ((f (lambda (n) (if (= (mod n 2) 0) (/ n 2) (+ (* n 3) 1))))) (f 10))',
         reference_python='f = lambda n: n // 2 if n % 2 == 0 else n * 3 + 1; f(10)'),

    Task(id=28, name="product_list", description="Produto dos elementos.", category=TaskCategory.TRANSFORMATION, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"list": [1, 2, 3, 4]}, 24), TestCase({"list": []}, 1)],
         reference_lia='(fold (lambda (acc) (lambda (x) (* acc x))) 1 (list 1 2 3 4))',
         reference_python='from functools import reduce; reduce(lambda acc, x: acc * x, [1, 2, 3, 4], 1)'),

    Task(id=29, name="map_and_filter", description="Dobre e filtre > 10.", category=TaskCategory.COMPOSITE, difficulty=Difficulty.HARD,
         test_cases=[TestCase({"list": [1, 3, 6, 8, 2]}, [12, 16])],
         reference_lia='(filter (lambda (x) (> x 10)) (map (lambda (x) (* x 2)) (list 1 3 6 8 2)))',
         reference_python='[x * 2 for x in [1, 3, 6, 8, 2] if x * 2 > 10]'),

    Task(id=30, name="count_evens", description="Conte pares em lista.", category=TaskCategory.COMPOSITE, difficulty=Difficulty.MEDIUM,
         test_cases=[TestCase({"list": [1, 2, 3, 4, 5, 6]}, 3)],
         reference_lia='(length (filter (lambda (x) (= (mod x 2) 0)) (list 1 2 3 4 5 6)))',
         reference_python='len([x for x in [1, 2, 3, 4, 5, 6] if x % 2 == 0])'),
]