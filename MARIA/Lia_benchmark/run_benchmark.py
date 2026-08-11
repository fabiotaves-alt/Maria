#!/usr/bin/env python3
"""
Script principal para executar o benchmark Lia vs Python.

Uso:
    python run_benchmark.py --reference-only
    
Ou para teste com LLM:
    python run_benchmark.py --provider ollama --model qwen2.5:7b --surfaces lia python
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import List, Dict
from runners.groq_client import GroqClient
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env (Lia/.env ou raiz)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv()  # fallback para .env na raiz

# Adiciona paths corretos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

from tasks.task_schema import load_all_tasks, Task
from runners.lia_runner import LiaRunner
from runners.python_runner import PythonRunner
from runners.llm_client import LLMClient, load_few_shot_examples
from analysis.metrics import calculate_metrics, compare_metrics, _interpret_results as interpret_results, TaskResult
from analysis.report import generate_report
from config import PROMPTS_DIR, OLLAMA_MODEL


def evaluate_lia_task(task_dict):
    """Avalia uma tarefa Lia usando LiaRunner."""
    runner = LiaRunner()
    source = task_dict.get("source", "")
    test_cases = task_dict.get("test_cases", [])
    
    # Avalia apenas o primeiro test case para simplificação
    expected = None
    if test_cases:
        expected = test_cases[0].get("expected")
    
    result = runner.run(source, expected_output=expected)
    
    # Adapta formato
    return {
        "parse_ok": result.get("parse_ok", False),
        "type_ok": result.get("type_ok", False),
        "runtime_ok": result.get("runtime_ok", False),
        "passed": result.get("passed", False),
        "errors": [result.get("error")] if result.get("error") else []
    }


def evaluate_python_task(task_dict):
    """Avalia uma tarefa Python usando PythonRunner."""
    runner = PythonRunner()
    source = task_dict.get("source", "")
    test_cases = task_dict.get("test_cases", [])
    
    # Avalia apenas o primeiro test case para simplificação
    expected = None
    input_data = None
    if test_cases:
        expected = test_cases[0].get("expected")
        input_data = test_cases[0].get("input")
    
    result = runner.run(source, input_data=input_data, expected_output=expected)
    
    # Adapta formato
    return {
        "parse_ok": result.get("parse_ok", False),
        "type_ok": True,  # Python não tem type checking estático
        "runtime_ok": result.get("runtime_ok", False),
        "passed": result.get("passed", False),
        "errors": [result.get("error")] if result.get("error") else []
    }


def run_reference_benchmark(tasks: List[Task]) -> Dict:
    """
    Executa benchmark usando apenas código de referência (sem LLM).
    
    Isso é útil para:
    - Validar que as tarefas estão bem definidas
    - Estabelecer baseline máxima de performance
    - Testar o pipeline sem gastar tokens
    """
    print(f"Executando benchmark de referência com {len(tasks)} tarefas...")
    
    lia_results = []
    python_results = []
    
    for task in tasks:
        # Avalia código de referência Lia
        if task.reference_lia:
            lia_result = evaluate_lia_task({
                "source": task.reference_lia,
                "test_cases": [
                    {"input": tc.input_data, "expected": tc.expected_output}
                    for tc in task.test_cases
                ]
            })
            lia_results.append({
                "task_id": task.id,
                "task_name": task.name,
                "category": task.category.value,
                "difficulty": task.difficulty.value,
                **lia_result
            })
        
        # Avalia código de referência Python
        if task.reference_python:
            python_result = evaluate_python_task({
                "source": task.reference_python,
                "test_cases": [
                    {"input": tc.input_data, "expected": tc.expected_output}
                    for tc in task.test_cases
                ]
            })
            python_results.append({
                "task_id": task.id,
                "task_name": task.name,
                "category": task.category.value,
                "difficulty": task.difficulty.value,
                **python_result
            })
    
    return {
        "lia": lia_results,
        "python": python_results
    }


def run_llm_benchmark(tasks: List[Task], client, surfaces: List[str], delay: float = 0.0) -> Dict:
    """
    Executa benchmark usando LLM para gerar código Lia e Python.
    
    Para cada tarefa e superfície:
    1. Monta prompt com descrição da tarefa
    2. Chama LLM para gerar código
    3. Executa código com runner apropriado
    4. Coleta métricas (parse, type, runtime, match, tokens, latência)
    
    Args:
        tasks: Lista de tarefas a avaliar
        client: Cliente LLM pré-criado (LLMClient ou GroqClient)
        surfaces: Lista de superfícies a testar (ex: ["lia", "python"])
    """
    model_name = getattr(client, "model_name", client.model)
    print(f"Executando benchmark LLM com modelo '{model_name}'...")
    print(f"Superfícies: {', '.join(surfaces)}")
    
    # Configuração por superfície
    surface_config = {
        "lia": {
            "system_prompt_file": os.path.join(PROMPTS_DIR, "lia_system.txt"),
            "few_shot_file": os.path.join(PROMPTS_DIR, "lia_few_shot.txt"),
            "runner": LiaRunner,
        },
        "python": {
            "system_prompt_file": os.path.join(PROMPTS_DIR, "python_system.txt"),
            "few_shot_file": os.path.join(PROMPTS_DIR, "python_few_shot.txt"),
            "runner": PythonRunner,
        },
    }
    
    # Carrega prompts e few-shots
    configs = {}
    for surface in surfaces:
        if surface not in surface_config:
            raise ValueError(f"Superfície desconhecida: {surface}. Use 'lia' ou 'python'.")
        
        cfg = surface_config[surface]
        with open(cfg["system_prompt_file"], "r", encoding="utf-8") as f:
            system_prompt = f.read()
        
        few_shot = load_few_shot_examples(cfg["few_shot_file"])
        
        configs[surface] = {
            "system_prompt": system_prompt,
            "few_shot": few_shot,
            "runner": cfg["runner"](),
        }
    
    results = {surface: [] for surface in surfaces}
    
    for i, task in enumerate(tasks):
        print(f"\n[{i+1}/{len(tasks)}] Tarefa {task.id}: {task.name} ({task.category.value})")
        
        for surface in surfaces:
            cfg = configs[surface]
            
            # Monta prompt do usuário com os valores de entrada do primeiro caso de teste
            first_test = task.test_cases[0]
            if isinstance(first_test.input_data, dict):
                input_str = ", ".join(f"{k}={v}" for k, v in first_test.input_data.items())
                user_prompt = f"Resolva a seguinte tarefa: {task.description}. Use os valores: {input_str}"
            else:
                # Fallback: input_data não-dict (ex: valor simples)
                user_prompt = f"Resolva a seguinte tarefa: {task.description}. Entrada: {first_test.input_data}"
            
            # Gera código com LLM
            try:
                llm_response = client.generate(
                    system_prompt=cfg["system_prompt"],
                    user_prompt=user_prompt,
                    few_shot_examples=cfg["few_shot"],
                    temperature=0.0,
                    max_tokens=2000
                )
                
                # Normaliza resposta (dict do GroqClient ou LLMResponse do LLMClient)
                if isinstance(llm_response, dict):
                    generated_code = llm_response["content"].strip()
                    tokens_prompt = llm_response.get("tokens_prompt", 0)
                    tokens_completion = llm_response.get("tokens_completion", 0)
                    latency_ms = llm_response.get("latency_ms", 0)
                else:
                    generated_code = llm_response.content.strip()
                    tokens_prompt = llm_response.tokens_prompt
                    tokens_completion = llm_response.tokens_completion
                    latency_ms = llm_response.latency_ms
            except Exception as e:
                print(f"  ⚠️  [{surface}] Erro ao gerar código: {e}")
                results[surface].append(TaskResult(
                    task_id=task.id,
                    surface=surface,
                    model=model_name,
                    parse_ok=False,
                    type_ok=False,
                    runtime_ok=False,
                    output_match=False,
                    errors=[{"kind": "LLMError", "message": str(e)}],
                ))
                continue
            
            # Executa código gerado
            test_cases = [
                {"input": tc.input_data, "expected": tc.expected_output}
                for tc in task.test_cases
            ]
            
            if surface == "lia":
                eval_result = evaluate_lia_task({
                    "source": generated_code,
                    "test_cases": test_cases
                })
            else:
                eval_result = evaluate_python_task({
                    "source": generated_code,
                    "test_cases": test_cases
                })
            
            # Cria TaskResult
            result = TaskResult(
                task_id=task.id,
                surface=surface,
                model=model_name,
                parse_ok=eval_result.get("parse_ok", False),
                type_ok=eval_result.get("type_ok", False),
                runtime_ok=eval_result.get("runtime_ok", False),
                output_match=eval_result.get("passed", False),
                errors=eval_result.get("errors", []),
                tokens_prompt=tokens_prompt,
                tokens_completion=tokens_completion,
                latency_ms=latency_ms,
                source=generated_code,
            )
            results[surface].append(result)
            
            status = "✅" if result.output_match else "❌"
            print(f"  {status} [{surface}] parse={result.parse_ok} type={result.type_ok} runtime={result.runtime_ok} match={result.output_match} tokens={result.tokens_prompt + result.tokens_completion} lat={result.latency_ms:.0f}ms")
        
        # Delay entre tarefas para respeitar limites de cota
        if delay > 0 and i < len(tasks) - 1:
            print(f"  ⏳ Aguardando {delay}s antes da próxima tarefa...")
            time.sleep(delay)
    
    return results


def convert_to_task_results(data: List[Dict], surface: str) -> List[TaskResult]:
    """Converte resultados brutos para formato TaskResult."""
    results = []
    for item in data:
        results.append(TaskResult(
            task_id=item["task_id"],
            surface=surface,
            model="reference",
            parse_ok=item.get("parse_ok", False),
            type_ok=item.get("type_ok", False),
            runtime_ok=item.get("runtime_ok", False),
            output_match=item.get("runtime_ok", False),  # Simplificação
            errors=item.get("errors", []),
        ))
    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark Lia vs Python")
    parser.add_argument("--model", type=str, default=None, help="Modelo LLM a usar (default: gpt-4o ou qwen2.5:7b para ollama)")
    parser.add_argument("--provider", type=str, default="openai", choices=["openai", "anthropic", "google", "ollama", "groq"], help="Provider LLM")
    parser.add_argument("--surfaces", type=str, nargs="+", default=["lia", "python"], help="Superfícies a testar (lia, python)")
    parser.add_argument("--tasks", type=int, default=50, help="Número de tarefas (primeiras N)")
    parser.add_argument("--task-ids", type=int, nargs="+", default=None, help="IDs específicos de tarefas, ex: --task-ids 21 22 23 24 25")
    parser.add_argument("--reference-only", action="store_true", help="Usa apenas código de referência")
    parser.add_argument("--output-dir", type=str, default=RESULTS_DIR, help="Diretório para resultados")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay entre tarefas (segundos) para respeitar limites de cota")
    
    args = parser.parse_args()
    
    # Define modelo padrão baseado no provider
    if args.model is None:
        if args.provider == "ollama":
            args.model = OLLAMA_MODEL
        elif args.provider == "google":
            args.model = "gemini-2.0-flash"
        elif args.provider == "groq":
            args.model = "llama-3.3-70b-versatile"
        else:
            args.model = "gpt-4o"

    # Cria o cliente LLM apropriado
    if args.provider == "groq":
        client = GroqClient(model=args.model)
    else:
        client = LLMClient(provider=args.provider, model=args.model)
    
    # Carrega tarefas
    all_tasks = load_all_tasks()
    print(f"Carregadas {len(all_tasks)} tarefas")
    
    # Filtra por IDs específicos se informado (tem prioridade sobre --tasks)
    if args.task_ids:
        task_ids_set = set(args.task_ids)
        all_tasks = [t for t in all_tasks if t.id in task_ids_set]
        missing_ids = sorted(task_ids_set - set(t.id for t in all_tasks))
        if missing_ids:
            print(f"⚠️  Aviso: IDs de tarefas não encontrados: {missing_ids}")
        print(f"Selecionadas {len(all_tasks)} tarefas por --task-ids: {sorted(task_ids_set)}")
    elif args.tasks < len(all_tasks):
        all_tasks = all_tasks[:args.tasks]
    
    # Garante diretório de saída
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.reference_only:
        # Executa benchmark de referência
        raw_results = run_reference_benchmark(all_tasks)
        
        lia_results = convert_to_task_results(raw_results["lia"], "lia")
        python_results = convert_to_task_results(raw_results["python"], "python")
        
        lia_metrics = calculate_metrics(lia_results)
        python_metrics = calculate_metrics(python_results)
        
        report = generate_report(
            raw_results["lia"],
            raw_results["python"],
            lia_metrics,
            python_metrics,
            args.output_dir
        )
        
        print("\n" + "="*60)
        print(report)
        print("="*60)
        print(f"\nRelatório salvo em: {args.output_dir}/benchmark_report.md")
        print(f"Dados salvos em: {args.output_dir}/benchmark_data.json")
        
    else:
        # Executa benchmark com LLM
        print(f"\n🚀 Iniciando benchmark LLM com modelo '{args.model}' via {args.provider}...")
        
        try:
            results = run_llm_benchmark(all_tasks, client, args.surfaces, delay=args.delay)
        except Exception as e:
            print(f"\n❌ Erro ao executar benchmark LLM: {e}")
            if args.provider == "ollama":
                print("\n💡 Dica: Certifique-se de que o Ollama está rodando:")
                print("   ollama serve")
                print("   ollama pull qwen2.5:7b")
            return 1
        
        # Calcula métricas por superfície
        metrics = {}
        for surface in args.surfaces:
            metrics[surface] = calculate_metrics(results[surface])
        
        # Gera relatório
        if "lia" in metrics and "python" in metrics:
            report = generate_report(
                [r.__dict__ for r in results["lia"]],
                [r.__dict__ for r in results["python"]],
                metrics["lia"],
                metrics["python"],
                args.output_dir
            )
        else:
            # Relatório para superfície única
            surface = args.surfaces[0]
            report = f"# Benchmark {surface} com {args.model}\n\n"
            report += f"- Tarefas: {metrics[surface].total_tasks}\n"
            report += f"- Parse: {metrics[surface].parse_success_rate:.1%}\n"
            report += f"- Type: {metrics[surface].type_success_rate:.1%}\n"
            report += f"- Runtime: {metrics[surface].runtime_success_rate:.1%}\n"
            report += f"- Match: {metrics[surface].output_match_rate:.1%}\n"
            report += f"- Tokens médios: {metrics[surface].avg_tokens:.0f}\n"
            report += f"- Latência média: {metrics[surface].avg_latency_ms:.0f}ms\n"
            
            report_path = os.path.join(args.output_dir, "benchmark_report.md")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
        
        # Salva dados JSON
        data_path = os.path.join(args.output_dir, "benchmark_data.json")
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump({
                "model": args.model,
                "provider": args.provider,
                "timestamp": datetime.now().isoformat(),
                "surfaces": args.surfaces,
                "results": {
                    surface: [r.__dict__ for r in results[surface]]
                    for surface in args.surfaces
                }
            }, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*60)
        print(report)
        print("="*60)
        print(f"\nRelatório salvo em: {args.output_dir}/benchmark_report.md")
        print(f"Dados salvos em: {args.output_dir}/benchmark_data.json")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())