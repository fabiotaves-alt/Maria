# Relatório de Melhorias - Projeto MARIA

## Sumário Executivo

Este relatório apresenta sugestões de melhoria para o projeto MARIA, organizadas por prioridade e área de impacto. Cada sugestão inclui exemplos de código práticos para implementação.

---

## 1. Performance e Gerenciamento de Memória (CRÍTICO)

### 1.1 Garbage Collection Explícito

**Problema:** Vazamentos de memória durante execução de benchmarks prolongados.

**Solução:** Implementar GC explícito após cada tarefa do benchmark.

```python
# backend/src/core/benchmark/executor.py
import gc
import tracemalloc
from typing import Optional

class BenchmarkExecutor:
    def __init__(self, enable_memory_profiling: bool = False):
        self.enable_memory_profiling = enable_memory_profiling
        if enable_memory_profiling:
            tracemalloc.start()
    
    def execute_task(self, task: dict) -> dict:
        """Executa uma tarefa do benchmark com gerenciamento de memória."""
        try:
            # Snapshot inicial de memória
            if self.enable_memory_profiling:
                snapshot_before = tracemalloc.take_snapshot()
            
            # Execução da tarefa
            result = self._run_task(task)
            
            # Snapshot após execução
            if self.enable_memory_profiling:
                snapshot_after = tracemalloc.take_snapshot()
                
                # Calcular diferença de memória
                top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
                memory_diff = sum(stat.size_diff for stat in top_stats[:10])
                
                if memory_diff > 10 * 1024 * 1024:  # 10MB threshold
                    logger.warning(f"Alto uso de memória detectado: {memory_diff / 1024 / 1024:.2f}MB")
            
            return result
            
        finally:
            # Limpeza explícita
            gc.collect()
            
            # Fechar sessões HTTP pendentes
            self._cleanup_http_sessions()
    
    def _cleanup_http_sessions(self):
        """Fecha todas as sessões HTTP abertas."""
        import aiohttp
        for session in self._http_sessions:
            if not session.closed:
                asyncio.create_task(session.close())
        self._http_sessions.clear()
```

### 1.2 Limitação de Histórico por Tokens

**Problema:** Histórico de conversas cresce indefinidamente, consumindo memória.

**Solução:** Implementar limite baseado em tokens totais.

```python
# backend/src/core/chat/history_manager.py
from typing import List, Dict
import tiktoken

class HistoryManager:
    def __init__(self, max_tokens: int = 4000, model: str = "gpt-4"):
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model(model)
    
    def truncate_history(self, messages: List[Dict]) -> List[Dict]:
        """Trunca histórico mantendo dentro do limite de tokens."""
        if not messages:
            return messages
        
        # Contar tokens de cada mensagem
        message_tokens = []
        for msg in messages:
            content = f"{msg['role']}: {msg.get('content', '')}"
            tool_calls = msg.get('tool_calls', [])
            if tool_calls:
                content += f" [tool_calls: {len(tool_calls)}]"
            token_count = len(self.encoding.encode(content))
            message_tokens.append((msg, token_count))
        
        # Somar tokens totais
        total_tokens = sum(tokens for _, tokens in message_tokens)
        
        if total_tokens <= self.max_tokens:
            return messages
        
        # Manter primeira mensagem (system prompt) e truncar do meio
        system_message = message_tokens[0] if message_tokens[0][0]['role'] == 'system' else None
        remaining_messages = message_tokens[1:] if system_message else message_tokens
        
        # Remover mensagens do início até atingir limite
        while remaining_messages and total_tokens > self.max_tokens:
            _, tokens = remaining_messages.pop(0)
            total_tokens -= tokens
        
        # Reconstruir histórico
        result = []
        if system_message:
            result.append(system_message[0])
        result.extend([msg for msg, _ in remaining_messages])
        
        logger.info(f"Histórico truncado: {len(messages)} -> {len(result)} mensagens")
        return result
    
    def add_message_with_limit(self, messages: List[Dict], new_message: Dict) -> List[Dict]:
        """Adiciona mensagem aplicando limite de tokens."""
        updated_messages = messages + [new_message]
        return self.truncate_history(updated_messages)
```

### 1.3 Reutilização de Sessões HTTP

**Problema:** Sessões HTTP não são reutilizadas ou fechadas corretamente.

**Solução:** Pool de sessões com gerenciamento automático.

```python
# backend/src/core/http/session_pool.py
import aiohttp
import asyncio
from typing import Optional, Dict
from contextlib import asynccontextmanager

class HTTPSessionPool:
    def __init__(self, max_pool_size: int = 10, timeout: int = 30):
        self.max_pool_size = max_pool_size
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_pool_size)
        self._created_sessions = 0
        self._lock = asyncio.Lock()
    
    @asynccontextmanager
    async def get_session(self, base_url: Optional[str] = None):
        """Obtém sessão do pool ou cria nova se necessário."""
        session = None
        
        # Tentar obter sessão existente
        try:
            session = self._pool.get_nowait()
            if session.closed:
                session = None
                self._created_sessions -= 1
        except asyncio.QueueEmpty:
            pass
        
        # Criar nova sessão se necessário
        if session is None:
            async with self._lock:
                if self._created_sessions < self.max_pool_size:
                    session = aiohttp.ClientSession(
                        base_url=base_url,
                        timeout=self.timeout,
                        headers={"User-Agent": "MARIA-Bot/1.0"}
                    )
                    self._created_sessions += 1
                else:
                    # Aguardar sessão disponível
                    session = await self._pool.get()
        
        try:
            yield session
        finally:
            # Retornar sessão ao pool se não estiver fechada
            if session and not session.closed:
                await self._pool.put(session)
    
    async def close_all(self):
        """Fecha todas as sessões do pool."""
        while not self._pool.empty():
            session = await self._pool.get()
            if not session.closed:
                await session.close()
        self._created_sessions = 0

# Uso no MariaController
class MariaController:
    def __init__(self):
        self.http_pool = HTTPSessionPool()
    
    async def make_request(self, url: str, **kwargs):
        async with self.http_pool.get_session() as session:
            async with session.get(url, **kwargs) as response:
                return await response.json()
```

---

## 2. Tool Calling e Confiabilidade (ALTA PRIORIDADE)

### 2.1 Prompt de Sistema com Few-Shot Examples

**Problema:** Modelo não entende formato correto de tool calls.

**Solução:** Adicionar exemplos few-shot no system prompt.

```python
# backend/src/core/prompts/system_prompt.py
from typing import List, Dict

TOOL_CALL_EXAMPLES = """
## Exemplos de Tool Calls Corretos

### Exemplo 1: Consulta Simples
Usuário: "Qual a temperatura em São Paulo?"
Resposta esperada:
{
  "tool_calls": [{
    "name": "get_weather",
    "arguments": {"city": "São Paulo", "unit": "celsius"}
  }]
}

### Exemplo 2: Múltiplas Ferramentas
Usuário: "Compare a população de Rio e Brasília"
Resposta esperada:
{
  "tool_calls": [
    {"name": "get_population", "arguments": {"city": "Rio de Janeiro"}},
    {"name": "get_population", "arguments": {"city": "Brasília"}}
  ]
}

### Exemplo 3: Resposta Direta (sem ferramentas)
Usuário: "Olá, como você está?"
Resposta esperada:
{
  "content": "Olá! Estou bem, obrigado por perguntar. Como posso ajudar você hoje?"
}

### Exemplo 4: Correção de Tool Call Inválido
Se o modelo retornar argumentos inválidos, ele deve auto-corrigir:
Tool call inválido detectado: {"name": "get_weather", "arguments": {"cidade": "SP"}}
Correção automática: {"name": "get_weather", "arguments": {"city": "São Paulo", "unit": "celsius"}}
"""

def build_system_prompt(tools: List[Dict], custom_instructions: str = "") -> str:
    """Constrói system prompt com exemplos few-shot."""
    
    tools_description = "\n".join([
        f"- {tool['name']}: {tool['description']}\n  Parâmetros: {tool.get('parameters', {})}"
        for tool in tools
    ])
    
    system_prompt = f"""Você é MARIA, assistente virtual especializada em documentos oficiais brasileiros.

## Ferramentas Disponíveis
{tools_description}

## Regras para Tool Calls
1. Sempre valide os parâmetros antes de chamar ferramentas
2. Use nomes exatos das ferramentas conforme listado acima
3. Se não tiver certeza dos parâmetros, peça esclarecimento ao usuário
4. Para múltiplas consultas independentes, use tool calls paralelos

{TOOL_CALL_EXAMPLES}

{custom_instructions}

Lembre-se: Sua resposta deve ser sempre um JSON válido com 'content' e/ou 'tool_calls'.
"""
    return system_prompt
```

### 2.2 Retry com Backoff Exponencial

**Problema:** Tool calls falham temporariamente sem retry.

**Solução:** Implementar retry inteligente.

```python
# backend/src/core/tools/retry_handler.py
import asyncio
import random
from typing import Callable, Any, Optional
from functools import wraps

class RetryHandler:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcula delay com backoff exponencial."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Adicionar jitter de até 25%
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retryable_exceptions: tuple = (Exception,),
        on_retry: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """Executa função com retry exponencial."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    break
                
                delay = self.calculate_delay(attempt)
                
                if on_retry:
                    await on_retry(attempt, e, delay)
                
                logger.warning(
                    f"Tentativa {attempt + 1}/{self.max_retries} falhou: {e}. "
                    f"Próxima tentativa em {delay:.2f}s"
                )
                
                await asyncio.sleep(delay)
        
        raise last_exception

# Decorator para uso fácil
def retry_on_failure(
    max_retries: int = 3,
    retryable_exceptions: tuple = (Exception,)
):
    def decorator(func: Callable):
        handler = RetryHandler(max_retries=max_retries)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def on_retry(attempt, error, delay):
                logger.info(f"Retry {attempt + 1} após erro: {error}")
            
            return await handler.execute_with_retry(
                func,
                *args,
                retryable_exceptions=retryable_exceptions,
                on_retry=on_retry,
                **kwargs
            )
        return wrapper
    return decorator

# Uso em ferramentas
class WeatherTool:
    @retry_on_failure(max_retries=3, retryable_exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def get_weather(self, city: str) -> dict:
        async with session.get(f"https://api.weather.com/{city}") as response:
            return await response.json()
```

### 2.3 Validação de Schema Antes da Execução

**Problema:** Tool calls com parâmetros inválidos causam erros em runtime.

**Solução:** Validar schema antes de executar ferramenta.

```python
# backend/src/core/tools/schema_validator.py
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, ValidationError, create_model
import jsonschema

class ToolSchemaValidator:
    def __init__(self):
        self._schemas: Dict[str, dict] = {}
    
    def register_tool(self, name: str, schema: dict):
        """Registra schema de uma ferramenta."""
        self._schemas[name] = schema
    
    def validate_tool_call(self, tool_name: str, arguments: dict) -> tuple[bool, Optional[str]]:
        """Valida argumentos de tool call contra schema registrado."""
        if tool_name not in self._schemas:
            return False, f"Ferramenta '{tool_name}' não registrada"
        
        schema = self._schemas[tool_name]
        
        try:
            jsonschema.validate(instance=arguments, schema=schema)
            return True, None
        except jsonschema.ValidationError as e:
            error_msg = f"Validação falhou para '{tool_name}': {e.message}"
            
            # Sugerir correções
            suggestions = self._generate_correction_suggestions(arguments, schema, e)
            if suggestions:
                error_msg += f". Sugestões: {suggestions}"
            
            return False, error_msg
    
    def _generate_correction_suggestions(
        self,
        arguments: dict,
        schema: dict,
        error: jsonschema.ValidationError
    ) -> str:
        """Gera sugestões de correção baseadas no erro."""
        suggestions = []
        
        if error.validator == 'required':
            missing_params = error.validator_value
            suggestions.append(f"Parâmetros faltando: {missing_params}")
        
        elif error.validator == 'type':
            param_name = '.'.join(str(p) for p in error.absolute_path)
            expected_type = error.validator_value
            actual_value = arguments.get(param_name)
            suggestions.append(f"Tipo incorreto para '{param_name}': esperado {expected_type}, got {type(actual_value).__name__}")
        
        elif error.validator == 'enum':
            allowed_values = error.validator_value
            suggestions.append(f"Valor deve ser um de: {allowed_values}")
        
        return "; ".join(suggestions) if suggestions else ""
    
    def auto_correct_tool_call(
        self,
        tool_name: str,
        arguments: dict,
        error_message: str
    ) -> Optional[dict]:
        """Tenta corrigir automaticamente tool call inválido."""
        corrected = arguments.copy()
        
        # Correções automáticas comuns
        if "tipo incorreto" in error_message.lower():
            # Tentar converter tipos
            schema = self._schemas.get(tool_name, {})
            properties = schema.get('properties', {})
            
            for param, value in corrected.items():
                if param in properties:
                    expected_type = properties[param].get('type')
                    
                    if expected_type == 'integer' and isinstance(value, str):
                        try:
                            corrected[param] = int(value)
                        except ValueError:
                            pass
                    
                    elif expected_type == 'number' and isinstance(value, str):
                        try:
                            corrected[param] = float(value)
                        except ValueError:
                            pass
        
        # Validar correção
        is_valid, _ = self.validate_tool_call(tool_name, corrected)
        return corrected if is_valid else None

# Integração no executor de ferramentas
class ToolExecutor:
    def __init__(self):
        self.validator = ToolSchemaValidator()
        self.retry_handler = RetryHandler()
    
    async def execute_tool_call(self, tool_call: dict) -> dict:
        tool_name = tool_call['name']
        arguments = tool_call.get('arguments', {})
        
        # Validar schema
        is_valid, error_msg = self.validator.validate_tool_call(tool_name, arguments)
        
        if not is_valid:
            logger.warning(f"Tool call inválido: {error_msg}")
            
            # Tentar auto-correção
            corrected_args = self.validator.auto_correct_tool_call(
                tool_name, arguments, error_msg
            )
            
            if corrected_args:
                logger.info(f"Auto-correção aplicada: {corrected_args}")
                arguments = corrected_args
            else:
                return {
                    "success": False,
                    "error": error_msg,
                    "suggestion": "Por favor, verifique os parâmetros da ferramenta"
                }
        
        # Executar com retry
        tool_func = getattr(self, tool_name, None)
        if not tool_func:
            return {"success": False, "error": f"Ferramenta '{tool_name}' não encontrada"}
        
        try:
            result = await self.retry_handler.execute_with_retry(
                tool_func,
                **arguments
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

## 3. Benchmark e Observabilidade (ALTA PRIORIDADE)

### 3.1 Captura de Output "Thinking"

**Problema:** Não é possível depurar raciocínio do modelo.

**Solução:** Capturar e logar pensamento intermediário.

```python
# backend/src/core/benchmark/thinking_tracker.py
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ThinkingStep:
    timestamp: str
    step_number: int
    content: str
    duration_ms: float
    tokens_used: Optional[int] = None

@dataclass
class TaskExecutionRecord:
    task_id: str
    start_time: str
    end_time: str
    total_duration_ms: float
    thinking_steps: List[ThinkingStep]
    tool_calls: List[Dict]
    final_answer: str
    success: bool
    error_message: Optional[str] = None
    memory_usage_mb: Optional[float] = None

class ThinkingTracker:
    def __init__(self, output_dir: str = "./benchmark_logs"):
        self.output_dir = output_dir
        self.records: List[TaskExecutionRecord] = []
        self._current_thinking_steps: List[ThinkingStep] = []
        self._start_time: Optional[float] = None
    
    def start_task(self, task_id: str):
        """Inicia rastreamento de uma tarefa."""
        self._start_time = time.time()
        self._current_thinking_steps = []
        logger.info(f"Iniciando tarefa {task_id}")
    
    def log_thinking_step(self, content: str, tokens_used: Optional[int] = None):
        """Registra passo de pensamento."""
        if self._start_time is None:
            return
        
        step = ThinkingStep(
            timestamp=datetime.now().isoformat(),
            step_number=len(self._current_thinking_steps) + 1,
            content=content,
            duration_ms=(time.time() - self._start_time) * 1000,
            tokens_used=tokens_used
        )
        
        self._current_thinking_steps.append(step)
        logger.debug(f"Thinking step {step.step_number}: {content[:100]}...")
    
    def complete_task(
        self,
        task_id: str,
        final_answer: str,
        tool_calls: List[Dict],
        success: bool,
        error_message: Optional[str] = None,
        memory_usage_mb: Optional[float] = None
    ):
        """Completa rastreamento da tarefa."""
        end_time = time.time()
        
        record = TaskExecutionRecord(
            task_id=task_id,
            start_time=datetime.fromtimestamp(self._start_time).isoformat() if self._start_time else "",
            end_time=datetime.now().isoformat(),
            total_duration_ms=(end_time - self._start_time) * 1000 if self._start_time else 0,
            thinking_steps=self._current_thinking_steps,
            tool_calls=tool_calls,
            final_answer=final_answer,
            success=success,
            error_message=error_message,
            memory_usage_mb=memory_usage_mb
        )
        
        self.records.append(record)
        self._save_record(record)
        
        logger.info(f"Tarefa {task_id} completada: {'SUCESSO' if success else 'FALHA'}")
    
    def _save_record(self, record: TaskExecutionRecord):
        """Salva registro em arquivo JSON."""
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        
        filename = f"{self.output_dir}/task_{record.task_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(record), f, indent=2, ensure_ascii=False)
    
    def generate_summary_report(self) -> Dict:
        """Gera relatório resumido de todas as tarefas."""
        if not self.records:
            return {}
        
        successful = sum(1 for r in self.records if r.success)
        total = len(self.records)
        
        avg_duration = sum(r.total_duration_ms for r in self.records) / total
        avg_thinking_steps = sum(len(r.thinking_steps) for r in self.records) / total
        
        return {
            "total_tasks": total,
            "successful_tasks": successful,
            "success_rate": successful / total if total > 0 else 0,
            "average_duration_ms": avg_duration,
            "average_thinking_steps": avg_thinking_steps,
            "total_errors": sum(1 for r in self.records if r.error_message),
            "common_errors": self._analyze_common_errors()
        }
    
    def _analyze_common_errors(self) -> List[Dict]:
        """Analisa erros mais comuns."""
        from collections import Counter
        
        errors = [r.error_message for r in self.records if r.error_message]
        error_counts = Counter(errors)
        
        return [
            {"error": error, "count": count}
            for error, count in error_counts.most_common(5)
        ]
    
    def export_to_csv(self, filename: str = "benchmark_results.csv"):
        """Exporta resultados para CSV."""
        import csv
        
        if not self.records:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'task_id', 'success', 'duration_ms', 'thinking_steps_count',
                'tool_calls_count', 'memory_mb', 'error_message'
            ])
            
            for record in self.records:
                writer.writerow([
                    record.task_id,
                    record.success,
                    record.total_duration_ms,
                    len(record.thinking_steps),
                    len(record.tool_calls),
                    record.memory_usage_mb,
                    record.error_message
                ])
```

### 3.2 Dashboard de Métricas em Tempo Real

**Problema:** Não há visibilidade durante execução do benchmark.

**Solução:** Dashboard web com métricas em tempo real.

```python
# backend/src/core/benchmark/dashboard.py
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
from typing import Set
from datetime import datetime

app = FastAPI(title="MARIA Benchmark Dashboard")

class DashboardMetrics:
    def __init__(self):
        self.websocket_connections: Set[WebSocket] = set()
        self.metrics = {
            "tasks_total": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "current_task": None,
            "success_rate": 0.0,
            "avg_response_time_ms": 0.0,
            "avg_tool_calls_per_task": 0.0,
            "memory_usage_mb": 0.0,
            "tokens_used_total": 0,
            "errors_last_hour": []
        }
        self._response_times = []
        self._tool_calls_count = []
    
    async def broadcast_update(self):
        """Envia atualização para todos os clientes WebSocket."""
        if not self.websocket_connections:
            return
        
        message = json.dumps(self.metrics)
        disconnected = set()
        
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except:
                disconnected.add(websocket)
        
        self.websocket_connections -= disconnected
    
    def update_task_start(self, task_id: str):
        self.metrics["current_task"] = task_id
        self.metrics["tasks_total"] += 1
        asyncio.create_task(self.broadcast_update())
    
    def update_task_complete(
        self,
        success: bool,
        response_time_ms: float,
        tool_calls_count: int,
        memory_mb: float,
        tokens_used: int,
        error_message: Optional[str] = None
    ):
        self.metrics["tasks_completed" if success else "tasks_failed"] += 1
        self.metrics["current_task"] = None
        self.metrics["memory_usage_mb"] = memory_mb
        self.metrics["tokens_used_total"] += tokens_used
        
        self._response_times.append(response_time_ms)
        self._tool_calls_count.append(tool_calls_count)
        
        # Calcular médias móveis (últimos 100 tasks)
        if len(self._response_times) > 100:
            self._response_times.pop(0)
            self._tool_calls_count.pop(0)
        
        self.metrics["avg_response_time_ms"] = sum(self._response_times) / len(self._response_times)
        self.metrics["avg_tool_calls_per_task"] = sum(self._tool_calls_count) / len(self._tool_calls_count)
        self.metrics["success_rate"] = (
            self.metrics["tasks_completed"] / self.metrics["tasks_total"]
            if self.metrics["tasks_total"] > 0 else 0
        )
        
        if error_message:
            self.metrics["errors_last_hour"].append({
                "timestamp": datetime.now().isoformat(),
                "error": error_message
            })
            # Manter apenas última hora
            cutoff = datetime.now().timestamp() - 3600
            self.metrics["errors_last_hour"] = [
                e for e in self.metrics["errors_last_hour"]
                if datetime.fromisoformat(e["timestamp"]).timestamp() > cutoff
            ]
        
        asyncio.create_task(self.broadcast_update())

metrics = DashboardMetrics()

@app.get("/", response_class=HTMLResponse)
async def dashboard_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MARIA Benchmark Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-value { font-size: 2em; font-weight: bold; color: #2196F3; }
            .metric-label { color: #666; margin-top: 5px; }
            .chart-container { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
            .status-running { background: #4CAF50; }
            .status-idle { background: #9E9E9E; }
            #currentTask { font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 MARIA Benchmark Dashboard</h1>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value"><span id="tasksTotal">0</span></div>
                    <div class="metric-label">Total Tasks</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value"><span id="successRate">0%</span></div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value"><span id="avgResponseTime">0</span>ms</div>
                    <div class="metric-label">Avg Response Time</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value"><span id="memoryUsage">0</span>MB</div>
                    <div class="metric-label">Memory Usage</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value"><span id="tokensUsed">0</span></div>
                    <div class="metric-label">Total Tokens</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">
                        <span class="status-indicator" id="statusIndicator"></span>
                        <span id="currentTask">Idle</span>
                    </div>
                    <div class="metric-label">Current Task</div>
                </div>
            </div>
            
            <div class="chart-container">
                <canvas id="responseTimeChart"></canvas>
            </div>
            
            <div class="chart-container">
                <canvas id="successRateChart"></canvas>
            </div>
        </div>
        
        <script>
            let responseTimeData = [];
            let successRateData = [];
            let labels = [];
            
            const ws = new WebSocket(`ws://${window.location.host}/ws/metrics`);
            
            ws.onmessage = (event) => {
                const metrics = JSON.parse(event.data);
                
                document.getElementById('tasksTotal').textContent = metrics.tasks_total;
                document.getElementById('successRate').textContent = (metrics.success_rate * 100).toFixed(1) + '%';
                document.getElementById('avgResponseTime').textContent = metrics.avg_response_time_ms.toFixed(0);
                document.getElementById('memoryUsage').textContent = metrics.memory_usage_mb.toFixed(1);
                document.getElementById('tokensUsed').textContent = metrics.tokens_used_total;
                
                const currentTaskEl = document.getElementById('currentTask');
                const statusIndicator = document.getElementById('statusIndicator');
                
                if (metrics.current_task) {
                    currentTaskEl.textContent = metrics.current_task;
                    statusIndicator.className = 'status-indicator status-running';
                } else {
                    currentTaskEl.textContent = 'Idle';
                    statusIndicator.className = 'status-indicator status-idle';
                }
                
                // Update charts
                if (labels.length > 100) {
                    labels.shift();
                    responseTimeData.shift();
                    successRateData.shift();
                }
                
                labels.push(new Date().toLocaleTimeString());
                responseTimeData.push(metrics.avg_response_time_ms);
                successRateData.push(metrics.success_rate * 100);
                
                updateCharts();
            };
            
            function updateCharts() {
                responseTimeChart.update();
                successRateChart.update();
            }
            
            // Response Time Chart
            const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
            const responseTimeChart = new Chart(responseTimeCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Average Response Time (ms)',
                        data: responseTimeData,
                        borderColor: '#2196F3',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    animation: false
                }
            });
            
            // Success Rate Chart
            const successRateCtx = document.getElementById('successRateChart').getContext('2d');
            const successRateChart = new Chart(successRateCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Success Rate (%)',
                        data: successRateData,
                        borderColor: '#4CAF50',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    animation: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        </script>
    </body>
    </html>
    """

@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    metrics.websocket_connections.add(websocket)
    
    # Enviar estado atual imediatamente
    await websocket.send_text(json.dumps(metrics.metrics))
    
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except:
        metrics.websocket_connections.remove(websocket)

# Integração no benchmark executor
class BenchmarkExecutorWithDashboard:
    def __init__(self):
        self.dashboard = metrics
    
    async def run_benchmark(self, tasks: List[Dict]):
        for i, task in enumerate(tasks):
            task_id = f"task_{i}"
            self.dashboard.update_task_start(task_id)
            
            start_time = time.time()
            try:
                result = await self.execute_task(task)
                response_time = (time.time() - start_time) * 1000
                
                self.dashboard.update_task_complete(
                    success=True,
                    response_time_ms=response_time,
                    tool_calls_count=len(result.get('tool_calls', [])),
                    memory_mb=get_memory_usage(),
                    tokens_used=result.get('tokens_used', 0)
                )
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                
                self.dashboard.update_task_complete(
                    success=False,
                    response_time_ms=response_time,
                    tool_calls_count=0,
                    memory_mb=get_memory_usage(),
                    tokens_used=0,
                    error_message=str(e)
                )
```

---

## 4. Segurança (ALTA PRIORIDADE)

### 4.1 Validação de Caminhos de Arquivos

**Problema:** Vulnerabilidade a directory traversal attacks.

**Solução:** Validar e sanitizar caminhos de arquivos.

```python
# backend/src/security/file_validator.py
import os
from pathlib import Path
from typing import Optional, Tuple

class FileSecurityValidator:
    def __init__(self, allowed_base_dirs: list[str]):
        self.allowed_base_dirs = [Path(d).resolve() for d in allowed_base_dirs]
    
    def validate_path(self, requested_path: str) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Valida caminho de arquivo prevenindo directory traversal.
        
        Returns:
            (is_valid, resolved_path, error_message)
        """
        try:
            # Converter para Path absoluto
            requested = Path(requested_path)
            
            # Prevenir null bytes
            if '\x00' in requested_path:
                return False, None, "Caminho contém caracteres nulos"
            
            # Resolver symlinks e normalizar
            resolved = requested.resolve(strict=False)
            
            # Verificar se está dentro de diretórios permitidos
            is_allowed = any(
                self._is_subdirectory(resolved, base_dir)
                for base_dir in self.allowed_base_dirs
            )
            
            if not is_allowed:
                return False, None, f"Acesso negado: caminho fora dos diretórios permitidos"
            
            # Verificar extensão do arquivo (se aplicável)
            if resolved.is_file():
                if not self._is_safe_extension(resolved.suffix):
                    return False, None, f"Extensão de arquivo não permitida: {resolved.suffix}"
            
            return True, resolved, None
            
        except Exception as e:
            return False, None, f"Erro ao validar caminho: {str(e)}"
    
    def _is_subdirectory(self, path: Path, parent: Path) -> bool:
        """Verifica se path é subdiretório de parent."""
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False
    
    def _is_safe_extension(self, extension: str) -> bool:
        """Verifica se extensão de arquivo é segura."""
        safe_extensions = {
            '.txt', '.md', '.pdf', '.doc', '.docx',
            '.jpg', '.jpeg', '.png', '.gif',
            '.json', '.yaml', '.yml', '.xml',
            '.csv', '.xlsx'
        }
        return extension.lower() in safe_extensions
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitiza nome de arquivo removendo caracteres perigosos."""
        # Remover caracteres especiais
        sanitized = "".join(c for c in filename if c.isalnum() or c in '._- ')
        
        # Remover paths relativos
        sanitized = os.path.basename(sanitized)
        
        # Limitar tamanho
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        return sanitized.strip()

# Uso no controller
class FileController:
    def __init__(self):
        self.validator = FileSecurityValidator(
            allowed_base_dirs=['./uploads', './documents', './temp']
        )
    
    async def read_file(self, filepath: str) -> dict:
        is_valid, resolved_path, error = self.validator.validate_path(filepath)
        
        if not is_valid:
            logger.warning(f"Tentativa de acesso inválido: {filepath} - {error}")
            return {"success": False, "error": error}
        
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### 4.2 Rate Limiting

**Problema:** API vulnerável a abuso e DoS.

**Solução:** Implementar rate limiting por IP/usuário.

```python
# backend/src/security/rate_limiter.py
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional
import asyncio

class RateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        
        self._minute_buckets: Dict[str, list] = defaultdict(list)
        self._hour_buckets: Dict[str, list] = defaultdict(list)
        self._burst_counters: Dict[str, int] = defaultdict(int)
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    def _get_client_id(self, request: Request) -> str:
        """Identifica cliente por IP ou token."""
        # Tentar obter token primeiro
        auth_header = request.headers.get("Authorization")
        if auth_header:
            return f"token:{auth_header}"
        
        # Fallback para IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def check_rate_limit(self, request: Request) -> bool:
        """Verifica se requisição está dentro dos limites."""
        client_id = self._get_client_id(request)
        
        async with self._locks[client_id]:
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            
            # Limpar buckets antigos
            self._minute_buckets[client_id] = [
                ts for ts in self._minute_buckets[client_id]
                if ts > minute_ago
            ]
            self._hour_buckets[client_id] = [
                ts for ts in self._hour_buckets[client_id]
                if ts > hour_ago
            ]
            
            # Verificar limites
            if len(self._minute_buckets[client_id]) >= self.requests_per_minute:
                return False
            
            if len(self._hour_buckets[client_id]) >= self.requests_per_hour:
                return False
            
            # Burst limit (para prevenir picos súbitos)
            if self._burst_counters[client_id] >= self.burst_limit:
                # Reset burst counter após 1 segundo
                asyncio.create_task(self._reset_burst(client_id))
                return False
            
            # Registrar requisição
            self._minute_buckets[client_id].append(now)
            self._hour_buckets[client_id].append(now)
            self._burst_counters[client_id] += 1
            
            return True
    
    async def _reset_burst(self, client_id: str):
        await asyncio.sleep(1)
        self._burst_counters[client_id] = 0
    
    def get_remaining_limits(self, request: Request) -> Dict:
        """Retorna limites restantes para o cliente."""
        client_id = self._get_client_id(request)
        now = datetime.now()
        
        minute_count = len([
            ts for ts in self._minute_buckets[client_id]
            if ts > now - timedelta(minutes=1)
        ])
        hour_count = len([
            ts for ts in self._hour_buckets[client_id]
            if ts > now - timedelta(hours=1)
        ])
        
        return {
            "requests_per_minute_remaining": max(0, self.requests_per_minute - minute_count),
            "requests_per_hour_remaining": max(0, self.requests_per_hour - hour_count),
            "burst_remaining": max(0, self.burst_limit - self._burst_counters[client_id])
        }

# Middleware para FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RateLimiter):
        super().__init__(app)
        self.limiter = limiter
    
    async def dispatch(self, request, call_next):
        if not await self.limiter.check_rate_limit(request):
            limits = self.limiter.get_remaining_limits(request)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after_seconds": 60
                },
                headers={
                    "X-RateLimit-Minute-Remaining": str(limits["requests_per_minute_remaining"]),
                    "X-RateLimit-Hour-Remaining": str(limits["requests_per_hour_remaining"])
                }
            )
        
        response = await call_next(request)
        
        # Adicionar headers de rate limit
        limits = self.limiter.get_remaining_limits(request)
        response.headers["X-RateLimit-Minute-Remaining"] = str(limits["requests_per_minute_remaining"])
        response.headers["X-RateLimit-Hour-Remaining"] = str(limits["requests_per_hour_remaining"])
        
        return response

# Uso na aplicação FastAPI
app = FastAPI()
limiter = RateLimiter(requests_per_minute=60, requests_per_hour=1000)
app.add_middleware(RateLimitMiddleware, limiter=limiter)
```

---

## 5. Integração com Manual de Redação Oficial (MÉDIA PRIORIDADE)

### 5.1 Busca no Manual de Redação

**Problema:** Dificuldade em encontrar normas específicas no manual.

**Solução:** Implementar busca full-text no manual.

```python
# backend/src/integrations/manual_redacao/search_engine.py
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import re
from rank_bm25 import BM25Okapi

@dataclass
class ManualSection:
    id: str
    title: str
    content: str
    category: str
    subsections: List['ManualSection']
    keywords: List[str]

class ManualSearchEngine:
    def __init__(self, manual_path: str = "./data/manual_redacao"):
        self.manual_path = Path(manual_path)
        self.sections: List[ManualSection] = []
        self.bm25_index = None
        self.section_texts: List[str] = []
        self._load_manual()
    
    def _load_manual(self):
        """Carrega manual de redação oficial."""
        # Estrutura esperada: manual_redacao/{categoria}/{secao}.md
        if not self.manual_path.exists():
            logger.warning(f"Manual não encontrado em {self.manual_path}")
            return
        
        for category_dir in self.manual_path.iterdir():
            if not category_dir.is_dir():
                continue
            
            category = category_dir.name
            
            for section_file in category_dir.glob("*.md"):
                section = self._parse_section_file(section_file, category)
                if section:
                    self.sections.append(section)
                    self.section_texts.append(f"{section.title} {section.content}")
        
        # Construir índice BM25
        if self.section_texts:
            tokenized_docs = [self._tokenize(text) for text in self.section_texts]
            self.bm25_index = BM25Okapi(tokenized_docs)
            logger.info(f"Índice BM25 criado com {len(self.sections)} seções")
    
    def _parse_section_file(self, filepath: Path, category: str) -> Optional[ManualSection]:
        """Parse arquivo Markdown do manual."""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Extrair título (primeira linha #)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else filepath.stem
            
            # Extrair palavras-chave (se houver frontmatter YAML)
            keywords = []
            yaml_match = re.search(r'^---\n(.+?)\n---', content, re.DOTALL)
            if yaml_match:
                import yaml
                frontmatter = yaml.safe_load(yaml_match.group(1))
                keywords = frontmatter.get('keywords', [])
            
            # Remover frontmatter do conteúdo
            content = re.sub(r'^---\n.+?\n---', '', content, flags=re.DOTALL)
            
            return ManualSection(
                id=f"{category}/{filepath.stem}",
                title=title,
                content=content,
                category=category,
                subsections=[],
                keywords=keywords
            )
        except Exception as e:
            logger.error(f"Erro ao parsear {filepath}: {e}")
            return None
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokeniza texto para busca."""
        # Normalizar e tokenizar
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Busca seções relevantes no manual."""
        if not self.bm25_index:
            return []
        
        tokenized_query = self._tokenize(query)
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Obter top-k resultados
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Apenas resultados relevantes
                section = self.sections[idx]
                results.append({
                    "id": section.id,
                    "title": section.title,
                    "category": section.category,
                    "score": float(scores[idx]),
                    "snippet": self._extract_snippet(section.content, query),
                    "full_content": section.content
                })
        
        return results
    
    def _extract_snippet(self, content: str, query: str, context_size: int = 100) -> str:
        """Extrai snippet relevante do conteúdo."""
        # Encontrar primeira ocorrência de termo da query
        query_terms = query.lower().split()
        
        for term in query_terms:
            if len(term) < 3:
                continue
            
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            match = pattern.search(content)
            
            if match:
                start = max(0, match.start() - context_size)
                end = min(len(content), match.end() + context_size)
                snippet = content[start:end]
                
                # Adicionar elipses se truncado
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                
                return snippet
        
        # Fallback: primeiros caracteres
        return content[:context_size * 2] + "..." if len(content) > context_size * 2 else content
    
    def get_section_by_id(self, section_id: str) -> Optional[ManualSection]:
        """Obtém seção específica por ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

# Ferramenta para o modelo usar
class ManualRedacaoTool:
    def __init__(self):
        self.search_engine = ManualSearchEngine()
    
    async def search_manual(self, query: str, category: Optional[str] = None) -> dict:
        """Busca no manual de redação oficial."""
        results = self.search_engine.search(query)
        
        if category:
            results = [r for r in results if r['category'] == category]
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results[:5]  # Top 5
        }
    
    async def get_section(self, section_id: str) -> dict:
        """Obtém seção completa do manual."""
        section = self.search_engine.get_section_by_id(section_id)
        
        if not section:
            return {"error": f"Seção {section_id} não encontrada"}
        
        return {
            "id": section.id,
            "title": section.title,
            "category": section.category,
            "content": section.content,
            "keywords": section.keywords
        }

# Template para criação de documentos oficiais
OFFICIAL_DOCUMENT_TEMPLATES = {
    "oficio": """
OFÍCIO Nº {numero}/{ano}

{local}, {data}

Assunto: {assunto}

A(o) {destinatario_cargo},
{destinatario_nome}

{texto_principal}

Atenciosamente,

{remetente_nome}
{remetente_cargo}
{remetente_orgao}
""",
    
    "memorando": """
MEMORANDO Nº {numero}/{ano}

De: {de_parte}
Para: {para_parte}
Assunto: {assunto}
Data: {data}

{texto_principal}

{assinatura}
""",
    
    "despacho": """
DESPACHO

Processo nº: {processo_numero}
Interessado: {interessado}
Assunto: {assunto}

{decisão}

{local}, {data}

{nome_autoridade}
{cargo}
"""
}

def generate_official_document(
    doc_type: str,
    template_vars: dict,
    follow_manual: bool = True
) -> str:
    """Gera documento oficial seguindo manual de redação."""
    if doc_type not in OFFICIAL_DOCUMENT_TEMPLATES:
        raise ValueError(f"Tipo de documento não suportado: {doc_type}")
    
    template = OFFICIAL_DOCUMENT_TEMPLATES[doc_type]
    
    # Preencher template
    document = template.format(**template_vars)
    
    if follow_manual:
        # Validar conformidade com manual (implementar validações específicas)
        document = validate_manual_compliance(document, doc_type)
    
    return document

def validate_manual_compliance(document: str, doc_type: str) -> str:
    """Valida e corrige documento conforme manual de redação."""
    # Implementar validações específicas:
    # - Concordância verbal e nominal
    # - Uso correto de pronomes de tratamento
    # - Formatação de datas e números
    # - Estrutura padrão do tipo documental
    
    # Exemplo simples: padronizar datas
    import re
    date_pattern = r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b'
    document = re.sub(
        date_pattern,
        lambda m: f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{m.group(3)}",
        document
    )
    
    return document
```

---

## 6. Modo Visão - OCR e Análise de Imagens (MÉDIA PRIORIDADE)

### 6.1 Integração com Tesseract OCR

**Problema:** Não há suporte a PDFs escaneados ou imagens com texto.

**Solução:** Implementar pipeline de OCR.

```python
# backend/src/vision/ocr_processor.py
import pytesseract
from PIL import Image
import pdf2image
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class OCRResult:
    text: str
    confidence: float
    language: str
    bounding_boxes: List[Dict]
    processing_time_ms: float
    preprocessing_applied: List[str]

class OCRProcessor:
    def __init__(
        self,
        tesseract_cmd: str = '/usr/bin/tesseract',
        default_lang: str = 'por',
        enable_preprocessing: bool = True
    ):
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.default_lang = default_lang
        self.enable_preprocessing = enable_preprocessing
    
    def process_image(
        self,
        image_path: str,
        language: Optional[str] = None,
        preprocess: bool = True
    ) -> OCRResult:
        """Processa imagem com OCR."""
        import time
        start_time = time.time()
        
        # Carregar imagem
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Não foi possível carregar imagem: {image_path}")
        
        preprocessing_applied = []
        
        # Pré-processamento
        if preprocess and self.enable_preprocessing:
            img, preprocessing_applied = self._preprocess_image(img)
        
        # Converter para PIL
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # Configurar OCR
        lang = language or self.default_lang
        custom_config = r'--oem 3 --psm 6'
        
        # Extrair texto com detalhes
        data = pytesseract.image_to_data(
            img_pil,
            lang=lang,
            config=custom_config,
            output_type=pytesseract.Output.DICT
        )
        
        # Extrair texto completo
        text = pytesseract.image_to_string(
            img_pil,
            lang=lang,
            config=custom_config
        )
        
        # Calcular confiança média
        confidences = [c for c in data['conf'] if c != -1]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Extrair bounding boxes
        bounding_boxes = []
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0:
                bounding_boxes.append({
                    'text': data['text'][i],
                    'confidence': data['conf'][i],
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i]
                })
        
        processing_time = (time.time() - start_time) * 1000
        
        return OCRResult(
            text=text.strip(),
            confidence=avg_confidence,
            language=lang,
            bounding_boxes=bounding_boxes,
            processing_time_ms=processing_time,
            preprocessing_applied=preprocessing_applied
        )
    
    def _preprocess_image(self, img: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """Aplica pré-processamento para melhorar OCR."""
        preprocessing_applied = []
        
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        preprocessing_applied.append("grayscale")
        
        # Aplicar denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
        preprocessing_applied.append("denoising")
        
        # Binarização adaptativa
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        preprocessing_applied.append("adaptive_threshold")
        
        # Correção de inclinação (deskew)
        coords = np.column_stack(np.where(binary > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        if abs(angle) > 0.5:  # Apenas se inclinação significativa
            (h, w) = binary.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            binary = cv2.warpAffine(
                binary,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            preprocessing_applied.append(f"deskew_{angle:.2f}deg")
        
        # Converter de volta para BGR
        result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        
        return result, preprocessing_applied
    
    def process_pdf(
        self,
        pdf_path: str,
        pages: Optional[List[int]] = None,
        dpi: int = 300
    ) -> List[OCRResult]:
        """Processa PDF escaneado página por página."""
        # Converter PDF para imagens
        images = pdf2image.convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=pages[0] if pages else 1,
            last_page=pages[-1] if pages else None
        )
        
        results = []
        for i, img in enumerate(images):
            page_num = (pages[0] if pages else 1) + i
            
            # Salvar imagem temporária
            temp_path = f"/tmp/pdf_page_{page_num}.png"
            img.save(temp_path)
            
            try:
                result = self.process_image(temp_path)
                result.text = f"[Página {page_num}]\n{result.text}"
                results.append(result)
            finally:
                Path(temp_path).unlink(missing_ok=True)
        
        return results
    
    def detect_tables(self, image_path: str) -> List[Dict]:
        """Detecta tabelas em imagens."""
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detectar linhas horizontais e verticais
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        # Detectar linhas horizontais
        horizontal_lines = cv2.morphologyEx(
            gray,
            cv2.MORPH_OPEN,
            horizontal_kernel,
            iterations=2
        )
        
        # Detectar linhas verticais
        vertical_lines = cv2.morphologyEx(
            gray,
            cv2.MORPH_OPEN,
            vertical_kernel,
            iterations=2
        )
        
        # Combinar linhas
        table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0)
        _, table_mask = cv2.threshold(table_mask, 0, 255, cv2.THRESH_BINARY)
        
        # Encontrar contornos (tabelas)
        contours, _ = cv2.findContours(
            table_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        tables = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filtrar por tamanho mínimo
            if w > 100 and h > 50:
                tables.append({
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'confidence': 0.8  # Simplificado
                })
        
        return tables

# Cache de resultados OCR
class OCRCache:
    def __init__(self, cache_dir: str = "./cache/ocr"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, file_path: str) -> str:
        """Gera chave de cache baseada no hash do arquivo."""
        import hashlib
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    
    def get(self, file_path: str) -> Optional[OCRResult]:
        """Obtém resultado do cache."""
        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            import json
            data = json.loads(cache_file.read_text())
            return OCRResult(**data)
        
        return None
    
    def set(self, file_path: str, result: OCRResult):
        """Salva resultado no cache."""
        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        import json
        from dataclasses import asdict
        cache_file.write_text(json.dumps(asdict(result), indent=2))

# Integração como ferramenta
class VisionTool:
    def __init__(self):
        self.ocr_processor = OCRProcessor()
        self.cache = OCRCache()
    
    async def extract_text_from_image(self, image_path: str, use_cache: bool = True) -> dict:
        """Extrai texto de imagem usando OCR."""
        # Verificar cache
        if use_cache:
            cached_result = self.cache.get(image_path)
            if cached_result:
                return {
                    "source": "cache",
                    "text": cached_result.text,
                    "confidence": cached_result.confidence
                }
        
        # Processar com OCR
        result = self.ocr_processor.process_image(image_path)
        
        # Salvar no cache
        if result.confidence > 50:  # Apenas se confiança razoável
            self.cache.set(image_path, result)
        
        return {
            "source": "ocr",
            "text": result.text,
            "confidence": result.confidence,
            "language": result.language,
            "processing_time_ms": result.processing_time_ms,
            "preprocessing": result.preprocessing_applied
        }
    
    async def extract_text_from_pdf(self, pdf_path: str, pages: Optional[List[int]] = None) -> dict:
        """Extrai texto de PDF escaneado."""
        results = self.ocr_processor.process_pdf(pdf_path, pages)
        
        full_text = "\n\n".join(r.text for r in results)
        avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0
        
        return {
            "total_pages": len(results),
            "text": full_text,
            "average_confidence": avg_confidence,
            "pages": [
                {
                    "page_num": i + 1,
                    "text": r.text,
                    "confidence": r.confidence
                }
                for i, r in enumerate(results)
            ]
        }
    
    async def detect_tables_in_image(self, image_path: str) -> dict:
        """Detecta tabelas em imagem."""
        tables = self.ocr_processor.detect_tables(image_path)
        
        return {
            "tables_found": len(tables),
            "tables": tables
        }
```

---

## 7. Arquitetura e Refatoração de Código (MÉDIA PRIORIDADE)

### 7.1 Refatorar MariaController em Classes Menores

**Problema:** MariaController muito grande e difícil de manter.

**Solução:** Separar responsabilidades em classes especializadas.

```python
# backend/src/core/controller/__init__.py
from .session_manager import SessionManager
from .tool_orchestrator import ToolOrchestrator
from .response_handler import ResponseHandler
from .maria_controller import MariaController

__all__ = ['MariaController', 'SessionManager', 'ToolOrchestrator', 'ResponseHandler']

# backend/src/core/controller/session_manager.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid

class SessionManager:
    """Gerencia sessões de conversa e histórico."""
    
    def __init__(self, max_sessions: int = 100, session_timeout_minutes: int = 30):
        self.max_sessions = max_sessions
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._sessions: Dict[str, SessionData] = {}
    
    def create_session(self, user_id: str, initial_messages: Optional[List[Dict]] = None) -> str:
        """Cria nova sessão."""
        session_id = str(uuid.uuid4())
        
        self._sessions[session_id] = SessionData(
            session_id=session_id,
            user_id=user_id,
            messages=initial_messages or [],
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self._cleanup_old_sessions()
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Obtém sessão por ID."""
        session = self._sessions.get(session_id)
        
        if session and self._is_session_expired(session):
            self.delete_session(session_id)
            return None
        
        if session:
            session.last_activity = datetime.now()
        
        return session
    
    def update_session_messages(self, session_id: str, messages: List[Dict]):
        """Atualiza mensagens da sessão."""
        session = self.get_session(session_id)
        if session:
            session.messages = messages
    
    def delete_session(self, session_id: str):
        """Remove sessão."""
        self._sessions.pop(session_id, None)
    
    def _is_session_expired(self, session: SessionData) -> bool:
        """Verifica se sessão expirou."""
        return datetime.now() - session.last_activity > self.session_timeout
    
    def _cleanup_old_sessions(self):
        """Remove sessões antigas ou expiradas."""
        expired = [
            sid for sid, session in self._sessions.items()
            if self._is_session_expired(session)
        ]
        
        for sid in expired:
            self.delete_session(sid)
        
        # Se ainda exceder limite, remover mais antigas
        if len(self._sessions) > self.max_sessions:
            sorted_sessions = sorted(
                self._sessions.items(),
                key=lambda x: x[1].last_activity
            )
            
            to_remove = len(self._sessions) - self.max_sessions
            for sid, _ in sorted_sessions[:to_remove]:
                self.delete_session(sid)

# backend/src/core/controller/tool_orchestrator.py
from typing import Dict, List, Any, Optional
from ..tools.registry import ToolRegistry
from ..tools.validator import ToolSchemaValidator
from ..tools.retry_handler import RetryHandler

class ToolOrchestrator:
    """Orquestra execução de tool calls."""
    
    def __init__(self):
        self.registry = ToolRegistry()
        self.validator = ToolSchemaValidator()
        self.retry_handler = RetryHandler()
    
    def register_tools(self, tools: List[Dict]):
        """Registra ferramentas disponíveis."""
        for tool in tools:
            self.registry.register(tool)
            self.validator.register_tool(tool['name'], tool.get('parameters', {}))
    
    async def execute_tool_calls(
        self,
        tool_calls: List[Dict],
        parallel: bool = True
    ) -> List[Dict]:
        """Executa múltiplos tool calls."""
        if parallel:
            return await self._execute_parallel(tool_calls)
        else:
            return await self._execute_sequential(tool_calls)
    
    async def _execute_parallel(self, tool_calls: List[Dict]) -> List[Dict]:
        """Executa tool calls em paralelo."""
        import asyncio
        
        tasks = [
            self._execute_single_tool_call(tc)
            for tc in tool_calls
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    async def _execute_sequential(self, tool_calls: List[Dict]) -> List[Dict]:
        """Executa tool calls sequencialmente."""
        results = []
        for tool_call in tool_calls:
            result = await self._execute_single_tool_call(tool_call)
            results.append(result)
        return results
    
    async def _execute_single_tool_call(self, tool_call: Dict) -> Dict:
        """Executa único tool call com validação e retry."""
        tool_name = tool_call['name']
        arguments = tool_call.get('arguments', {})
        
        # Validar schema
        is_valid, error_msg = self.validator.validate_tool_call(tool_name, arguments)
        
        if not is_valid:
            # Tentar auto-correção
            corrected = self.validator.auto_correct_tool_call(
                tool_name, arguments, error_msg
            )
            if corrected:
                arguments = corrected
            else:
                return {
                    "tool_name": tool_name,
                    "success": False,
                    "error": error_msg
                }
        
        # Obter função da ferramenta
        tool_func = self.registry.get_tool(tool_name)
        if not tool_func:
            return {
                "tool_name": tool_name,
                "success": False,
                "error": f"Ferramenta '{tool_name}' não encontrada"
            }
        
        # Executar com retry
        try:
            result = await self.retry_handler.execute_with_retry(
                tool_func,
                **arguments
            )
            return {
                "tool_name": tool_name,
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "tool_name": tool_name,
                "success": False,
                "error": str(e)
            }

# backend/src/core/controller/response_handler.py
from typing import Dict, List, Optional
from ..prompts.system_prompt import build_system_prompt
from ..chat.history_manager import HistoryManager

class ResponseHandler:
    """Gerencia construção e formatação de respostas."""
    
    def __init__(self, history_manager: HistoryManager):
        self.history_manager = history_manager
    
    def build_request_payload(
        self,
        session_messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        custom_instructions: str = ""
    ) -> Dict:
        """Constrói payload para API do modelo."""
        # Build system prompt
        system_prompt = build_system_prompt(
            tools=tools or [],
            custom_instructions=custom_instructions
        )
        
        # Adicionar/atualizar system message
        messages = session_messages.copy()
        if messages and messages[0].get('role') == 'system':
            messages[0]['content'] = system_prompt
        else:
            messages.insert(0, {"role": "system", "content": system_prompt})
        
        # Truncar histórico se necessário
        messages = self.history_manager.truncate_history(messages)
        
        return {
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto" if tools else None
        }
    
    def parse_model_response(self, response: Dict) -> Dict:
        """Parse resposta do modelo."""
        message = response.get('choices', [{}])[0].get('message', {})
        
        content = message.get('content')
        tool_calls = message.get('tool_calls', [])
        
        # Parse tool calls se vierem como string JSON
        if isinstance(tool_calls, str):
            import json
            try:
                tool_calls = json.loads(tool_calls)
            except:
                tool_calls = []
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "finish_reason": response.get('choices', [{}])[0].get('finish_reason'),
            "usage": response.get('usage', {})
        }
    
    def format_final_response(
        self,
        content: Optional[str],
        tool_results: List[Dict],
        include_tool_outputs: bool = False
    ) -> str:
        """Formata resposta final combinando conteúdo e resultados de ferramentas."""
        if not tool_results:
            return content or ""
        
        if not include_tool_outputs:
            # Apenas mencionar que ferramentas foram usadas
            tool_names = [tr.get('tool_name', 'unknown') for tr in tool_results if tr.get('success')]
            if tool_names:
                content = f"{content}\n\n[Informações obtidas através de: {', '.join(tool_names)}]"
            return content or ""
        
        # Incluir outputs detalhados
        formatted = content or ""
        formatted += "\n\n## Resultados das Ferramentas\n"
        
        for result in tool_results:
            tool_name = result.get('tool_name', 'unknown')
            if result.get('success'):
                formatted += f"\n### {tool_name}\n"
                formatted += f"```\n{result.get('result', '')}\n```\n"
            else:
                formatted += f"\n### {tool_name} (falha)\n"
                formatted += f"Erro: {result.get('error', 'Desconhecido')}\n"
        
        return formatted

# backend/src/core/controller/maria_controller.py
from typing import Dict, List, Optional
from .session_manager import SessionManager
from .tool_orchestrator import ToolOrchestrator
from .response_handler import ResponseHandler
from ..chat.history_manager import HistoryManager
from ...llm.api_client import LLMAPIClient

class MariaController:
    """Controller principal - agora apenas orquestra componentes."""
    
    def __init__(self, llm_api_key: str, model: str = "gpt-4"):
        self.llm_client = LLMAPIClient(api_key=llm_api_key, model=model)
        self.session_manager = SessionManager()
        self.history_manager = HistoryManager()
        self.tool_orchestrator = ToolOrchestrator()
        self.response_handler = ResponseHandler(self.history_manager)
    
    def register_tools(self, tools: List[Dict]):
        """Registra ferramentas disponíveis."""
        self.tool_orchestrator.register_tools(tools)
    
    async def chat(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        tools_enabled: bool = True
    ) -> Dict:
        """Processa mensagem do usuário."""
        # Obter/criar sessão
        if not session_id:
            session_id = self.session_manager.create_session(user_id)
        
        session = self.session_manager.get_session(session_id)
        if not session:
            session_id = self.session_manager.create_session(user_id)
            session = self.session_manager.get_session(session_id)
        
        # Adicionar mensagem do usuário
        session.messages.append({"role": "user", "content": message})
        
        # Obter ferramentas disponíveis
        tools = self._get_available_tools() if tools_enabled else None
        
        # Construir request
        payload = self.response_handler.build_request_payload(
            session_messages=session.messages,
            tools=tools
        )
        
        # Chamar LLM
        response = await self.llm_client.chat_completion(payload)
        parsed = self.response_handler.parse_model_response(response)
        
        # Executar tool calls se presentes
        tool_results = []
        if parsed['tool_calls'] and tools_enabled:
            tool_results = await self.tool_orchestrator.execute_tool_calls(
                parsed['tool_calls']
            )
            
            # Adicionar tool calls e resultados ao histórico
            session.messages.append({
                "role": "assistant",
                "tool_calls": parsed['tool_calls']
            })
            
            for result in tool_results:
                session.messages.append({
                    "role": "tool",
                    "tool_call_id": result.get('tool_name'),
                    "content": str(result.get('result', result.get('error')))
                })
            
            # Obter resposta final após tool calls
            if tool_results:
                follow_up_payload = self.response_handler.build_request_payload(
                    session_messages=session.messages,
                    tools=None  # Sem ferramentas na segunda chamada
                )
                follow_up_response = await self.llm_client.chat_completion(follow_up_payload)
                parsed = self.response_handler.parse_model_response(follow_up_response)
        
        # Formatar resposta final
        final_content = self.response_handler.format_final_response(
            content=parsed['content'],
            tool_results=tool_results
        )
        
        # Adicionar resposta ao histórico
        session.messages.append({
            "role": "assistant",
            "content": final_content
        })
        
        # Salvar sessão
        self.session_manager.update_session_messages(session_id, session.messages)
        
        return {
            "session_id": session_id,
            "response": final_content,
            "tool_calls_executed": len(tool_results),
            "usage": parsed.get('usage', {})
        }
    
    def _get_available_tools(self) -> List[Dict]:
        """Obtém lista de ferramentas disponíveis."""
        return self.tool_orchestrator.registry.list_tools()
```

### 7.2 Type Hints Completos

**Problema:** Falta de type hints dificulta manutenção.

**Solução:** Adicionar type annotations em todo o código.

```python
# Exemplo de módulo com type hints completos
# backend/src/types/common.py
from typing import TypedDict, Literal, Optional, List, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime

# Types básicos
Role = Literal["system", "user", "assistant", "tool"]
FinishReason = Literal["stop", "length", "tool_calls", "error"]

class Message(TypedDict, total=False):
    role: Role
    content: Optional[str]
    tool_calls: Optional[List[Dict[str, Any]]]
    tool_call_id: Optional[str]
    name: Optional[str]

class ToolCall(TypedDict):
    id: str
    type: Literal["function"]
    function: Dict[str, Any]

class ToolDefinition(TypedDict):
    type: Literal["function"]
    function: Dict[str, Any]

class UsageInfo(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionChoice(TypedDict):
    index: int
    message: Message
    finish_reason: FinishReason

class ChatCompletionResponse(TypedDict):
    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: UsageInfo

@dataclass
class ConversationContext:
    session_id: str
    user_id: str
    messages: List[Message]
    created_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any]

@dataclass
class ToolExecutionResult:
    tool_name: str
    success: bool
    result: Any
    error: Optional[str]
    execution_time_ms: float

# backend/src/llm/api_client.py
from typing import AsyncIterator, Optional, List
import aiohttp

class LLMAPIClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 60
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=self.timeout
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def chat_completion(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> ChatCompletionResponse:
        session = await self._get_session()
        
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if stream:
            payload["stream"] = True
        
        async with session.post(
            f"{self.base_url}/chat/completions",
            json=payload
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def chat_completion_stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None
    ) -> AsyncIterator[str]:
        """Stream de resposta do modelo."""
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        if tools:
            payload["tools"] = tools
        
        async with session.post(
            f"{self.base_url}/chat/completions",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    yield data
```

---

## 8. Configuração e Deploy (MÉDIA PRIORIDADE)

### 8.1 Dockerfile para Backend

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src/ ./src/
COPY data/ ./data/

# Variáveis de ambiente
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expor porta
EXPOSE 8000

# Comando
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.2 Health Check Endpoint

```python
# backend/src/api/health.py
from fastapi import APIRouter
from datetime import datetime
import psutil
import asyncio

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check básico."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Health check detalhado com métricas."""
    # Verificar uso de recursos
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Verificar conectividade com serviços externos
    services_status = await check_external_services()
    
    # Determinar status geral
    status = "healthy"
    if cpu_percent > 90 or memory.percent > 90:
        status = "degraded"
    if not all(s['healthy'] for s in services_status.values()):
        status = "unhealthy"
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "resources": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / 1024 / 1024,
            "disk_percent": disk.percent
        },
        "services": services_status
    }

async def check_external_services() -> Dict:
    """Verifica status de serviços externos."""
    import aiohttp
    
    services = {
        "llm_api": {"healthy": False, "latency_ms": None},
        "database": {"healthy": False, "latency_ms": None}
    }
    
    timeout = aiohttp.ClientTimeout(total=5)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Verificar LLM API
        try:
            start = asyncio.get_event_loop().time()
            async with session.get("https://api.openai.com/v1/models") as resp:
                latency = (asyncio.get_event_loop().time() - start) * 1000
                services["llm_api"] = {
                    "healthy": resp.status == 200,
                    "latency_ms": latency
                }
        except:
            pass
        
        # Verificar banco de dados
        try:
            start = asyncio.get_event_loop().time()
            # Implementar ping ao banco
            latency = (asyncio.get_event_loop().time() - start) * 1000
            services["database"] = {
                "healthy": True,
                "latency_ms": latency
            }
        except:
            services["database"]["healthy"] = False
    
    return services
```

---

## 9. Frontend Tauri v4 (BAIXA PRIORIDADE)

### 9.1 Optimistic UI

```typescript
// frontend/src/stores/chatStore.ts
import { writable, derived } from 'svelte/store';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  status: 'pending' | 'sent' | 'error';
}

class ChatStore {
  private messages = writable<Message[]>([]);
  private isLoading = writable(false);
  
  async sendMessage(content: string) {
    const messageId = crypto.randomUUID();
    const timestamp = Date.now();
    
    // Optimistic update - adicionar mensagem imediatamente
    this.messages.update(msgs => [
      ...msgs,
      {
        id: messageId,
        role: 'user',
        content,
        timestamp,
        status: 'pending'
      }
    ]);
    
    this.isLoading.set(true);
    
    try {
      // Enviar para backend
      const response = await fetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: content })
      });
      
      const data = await response.json();
      
      // Atualizar status para sent
      this.messages.update(msgs =>
        msgs.map(m =>
          m.id === messageId ? { ...m, status: 'sent' } : m
        )
      );
      
      // Adicionar resposta do assistente
      this.messages.update(msgs => [
        ...msgs,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.response,
          timestamp: Date.now(),
          status: 'sent'
        }
      ]);
    } catch (error) {
      // Rollback em caso de erro
      this.messages.update(msgs =>
        msgs.map(m =>
          m.id === messageId ? { ...m, status: 'error' } : m
        )
      );
      
      throw error;
    } finally {
      this.isLoading.set(false);
    }
  }
}

export const chatStore = new ChatStore();
```

### 9.2 Acessibilidade (a11y)

```typescript
// frontend/src/lib/accessibility.ts
export function setupAccessibility() {
  // Gerenciar foco
  export function manageFocus(elementId: string) {
    const element = document.getElementById(elementId);
    if (element) {
      element.setAttribute('tabindex', '-1');
      element.focus();
    }
  }
  
  // Anunciar mudanças para screen readers
  export function announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite') {
    const announcer = document.getElementById('sr-announcer') || createAnnouncer();
    announcer.setAttribute('aria-live', priority);
    announcer.textContent = message;
  }
  
  function createAnnouncer() {
    const div = document.createElement('div');
    div.id = 'sr-announcer';
    div.setAttribute('role', 'status');
    div.setAttribute('aria-live', 'polite');
    div.setAttribute('aria-atomic', 'true');
    div.className = 'sr-only';
    document.body.appendChild(div);
    return div;
  }
}

// Componente acessível
// <button
//   aria-label="Enviar mensagem"
//   aria-disabled={isLoading}
//   on:click={sendMessage}
// >
//   {isLoading ? 'Enviando...' : 'Enviar'}
// </button>
```

---

## 10. Documentação e Onboarding (BAIXA PRIORIDADE)

### 10.1 README Interativo

```markdown
# MARIA - Assistente Virtual para Documentos Oficiais

## 🚀 Quick Start

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- Tesseract OCR (opcional, para modo visão)

### Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/seu-org/maria.git
cd maria

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install

# Executar
cd ../backend
python -m uvicorn src.main:app --reload

# Em outro terminal
cd ../frontend
npm run tauri dev
```

## 📚 Documentação

- [Guia de Instalação Detalhado](docs/installation.md)
- [Configuração de Ferramentas](docs/tools.md)
- [Manual de Redação Oficial](docs/manual-redacao.md)
- [API Reference](docs/api.md)

## 🛠️ Troubleshooting

### Erro Comum: "Tesseract não encontrado"
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-por

# macOS
brew install tesseract

# Windows
# Baixar em: https://github.com/UB-Mannheim/tesseract/wiki
```

### Erro: "ModuleNotFoundError: No module named 'pytesseract'"
```bash
pip install pytesseract pillow
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie branch para feature (`git checkout -b feature/AmazingFeature`)
3. Commit mudanças (`git commit -m 'Add AmazingFeature'`)
4. Push para branch (`git push origin feature/AmazingFeature`)
5. Abra Pull Request

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes.

## 📊 Roadmap

- [x] Core functionality
- [x] Tool calling
- [ ] OCR integration
- [ ] Manual de redação integration
- [ ] Dashboard em tempo real
- [ ] PWA support

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
```

---

## Conclusão

Este relatório apresentou 10 áreas principais de melhoria para o projeto MARIA, com exemplos de código práticos para implementação imediata. As prioridades recomendadas são:

1. **Crítico**: Gerenciamento de memória e segurança
2. **Alta**: Confiabilidade de tool calling e observabilidade
3. **Média**: Integração com manual de redação e modo visão
4. **Baixa**: Refatoração de código e melhorias de frontend

A implementação gradual destas melhorias resultará em um sistema mais robusto, performático e fácil de manter.
