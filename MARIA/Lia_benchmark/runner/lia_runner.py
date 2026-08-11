"""Runner para avaliar código Lia no benchmark."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from parser import parse
from core.infer import infer, TypeContext, PRIMITIVE_TYPES, BUILTIN_CONSTRUCTORS
from eval.interpreter import eval_expr, make_global_env, LiaRuntimeError, ADTValue

# Alias para compatibilidade
ConstructorValue = ADTValue


class LiaRunner:
    """Avalia código Lia e retorna resultados estruturados."""

    def __init__(self):
        self.type_env = dict(PRIMITIVE_TYPES)
        self.type_env.update(BUILTIN_CONSTRUCTORS)

    def run(self, code, input_data=None, expected_output=None):
        """Executa código Lia e compara com output esperado."""
        result = {
            "parse_ok": False,
            "type_ok": False,
            "runtime_ok": False,
            "passed": False,
            "actual_output": None,
            "error": None
        }

        # 1. Parse
        try:
            ast = parse(code)
            result["parse_ok"] = True
        except SyntaxError as e:
            result["error"] = {"stage": "parse", "kind": "SyntaxError", "message": str(e)}
            return result

        # 2. Type check
        try:
            ctx = TypeContext()
            _, inferred_type = infer(self.type_env, ast, ctx)
            result["type_ok"] = True
            result["inferred_type"] = str(inferred_type)
        except Exception as e:
            result["error"] = {"stage": "type", "kind": type(e).__name__, "message": str(e)}
            return result

        # 3. Execução
        try:
            env = make_global_env()
            value = eval_expr(ast, env)
            result["runtime_ok"] = True
            result["actual_output"] = self._serialize_value(value)
        except LiaRuntimeError as e:
            result["error"] = {"stage": "runtime", "kind": e.kind, "message": e.message}
            return result
        except Exception as e:
            result["error"] = {"stage": "runtime", "kind": "InternalError", "message": str(e)}
            return result

        # 4. Comparação
        if expected_output is not None:
            result["passed"] = self._compare(result["actual_output"], expected_output)
        else:
            result["passed"] = result["runtime_ok"]
        return result

    def _serialize_value(self, value):
        """Converte valor Lia para formato JSON-serializável."""
        if isinstance(value, ADTValue):
            # Nota: ADTValue usa 'constructor' e 'fields', não 'constructor_name' e 'args'
            if value.constructor == "Some" and len(value.fields) == 1:
                return {"Some": self._serialize_value(value.fields[0])}
            if value.constructor == "None":
                return "None"
            if value.constructor == "Ok" and len(value.fields) == 1:
                return {"Ok": self._serialize_value(value.fields[0])}
            if value.constructor == "Err" and len(value.fields) == 1:
                return {"Err": self._serialize_value(value.fields[0])}
            if not value.fields:
                return value.constructor
            return {value.constructor: [self._serialize_value(f) for f in value.fields]}
        if isinstance(value, tuple):
            return [self._serialize_value(v) for v in value]
        return value

    def _compare(self, actual, expected):
        """Compara output real com esperado."""
        if actual == expected:
            return True
        # Comparação numérica com tolerância para floats
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            return abs(actual - expected) < 0.001
        # Comparação de listas
        if isinstance(actual, list) and isinstance(expected, (list, tuple)):
            if len(actual) != len(expected):
                return False
            return all(self._compare(a, e) for a, e in zip(actual, expected))
        return False
