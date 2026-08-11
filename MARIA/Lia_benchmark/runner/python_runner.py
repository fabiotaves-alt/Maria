"""Runner para avaliar código Python no benchmark."""
import sys
import os
import io
import contextlib
import re
from typing import Any, Dict, Tuple
import json


class PythonRunner:
    """Avalia código Python e retorna resultados estruturados."""

    def _extract_lambda_params_and_body(self, code):
        """Extrai parâmetros e corpo de uma lambda."""
        code = code.strip()
        match = re.match(r'lambda\s+([^(]*):(.+)', code, re.DOTALL)
        if match:
            params_str = match.group(1).strip()
            body = match.group(2).strip()
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            return params, body
        return None, None

    def _is_pure_lambda(self, code):
        """Verifica se o código é apenas uma lambda pura (sem aplicação)."""
        code = code.strip()
        # Lambda pura: começa com 'lambda' e não tem parênteses externos de chamada
        if not code.startswith('lambda'):
            return False
        # Conta parênteses para ver se é só a definição
        paren_count = 0
        for i, char in enumerate(code):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                # Se chegou a zero antes do final, tem chamada
                if paren_count == 0 and i < len(code) - 1:
                    return False
        return paren_count == 0

    def run(self, code, input_data=None, expected_output=None):
        """Executa código Python e compara com output esperado."""
        result = {
            "parse_ok": False,
            "runtime_ok": False,
            "passed": False,
            "actual_output": None,
            "error": None
        }

        # 1. Parse
        try:
            compile(code, "<string>", "exec")
            result["parse_ok"] = True
        except SyntaxError:
            try:
                compile(code, "<string>", "eval")
                result["parse_ok"] = True
            except SyntaxError as e:
                result["error"] = {"stage": "parse", "message": str(e)}
                return result

        # 2. Execução
        try:
            namespace = {}
            value = None
            
            # Tenta detectar se é uma lambda pura (não aplicada)
            params, body = self._extract_lambda_params_and_body(code)
            if params and body and input_data is not None:
                # É uma lambda - cria e aplica automaticamente
                full_code = f"_func = {code}"
                namespace = {}
                exec(full_code, namespace)
                func = namespace.get('_func')
                if func and callable(func):
                    if isinstance(input_data, dict):
                        value = func(**input_data)
                    elif isinstance(input_data, (list, tuple)):
                        value = func(*input_data)
                    else:
                        value = func(input_data)
                    result["runtime_ok"] = True
                    result["actual_output"] = self._serialize(value)
                else:
                    raise Exception("Lambda detection failed")
            else:
                # Tenta avaliar como expressão simples (eval)
                try:
                    value = eval(code, namespace)
                    result["runtime_ok"] = True
                    result["actual_output"] = self._serialize(value)
                except SyntaxError:
                    # Se não for uma expressão simples, executa como código multi-statement
                    stdout_capture = io.StringIO()
                    with contextlib.redirect_stdout(stdout_capture):
                        exec(code, namespace)
                    
                    if 'solve' in namespace:
                        func = namespace['solve']
                        if isinstance(input_data, dict):
                            value = func(**input_data)
                        else:
                            value = func(input_data)
                    elif 'result' in namespace:
                        value = namespace['result']
                    else:
                        value = None
                        for k, v in namespace.items():
                            if k.startswith('__') and k.endswith('__'):
                                continue
                            if not callable(v) and v is not None:
                                value = v
                    
                    if value is None:
                        printed = stdout_capture.getvalue().strip()
                        if printed:
                            try:
                                value = eval(printed, {"__builtins__": {}})
                            except Exception:
                                value = printed
                    
                    result["runtime_ok"] = True
                    result["actual_output"] = self._serialize(value)
        except Exception as e:
            result["error"] = {"stage": "runtime", "kind": type(e).__name__, "message": str(e)}
            return result

        # 3. Comparação
        if expected_output is not None:
            result["passed"] = self._compare(result["actual_output"], expected_output)
        else:
            result["passed"] = result["runtime_ok"]
        return result

    def _serialize(self, value):
        if value is None:
            return "None"
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            return [self._serialize(v) for v in value]
        return str(value)

    def _compare(self, actual, expected):
        if actual == expected:
            return True
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            return abs(actual - expected) < 0.001
        return False
