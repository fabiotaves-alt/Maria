"""Schema de tarefas do benchmark MARIA."""
from dataclasses import dataclass, field
from enum import Enum


class MariaTaskCategory(Enum):
    CONVERSA = "conversa"
    CRIAR_PLANILHA = "criar_planilha"
    CRIAR_DOCUMENTO = "criar_documento"
    EDITAR_PLANILHA = "editar_planilha"
    CONFIRMACAO = "confirmacao"
    CANCELAMENTO = "cancelamento"
    AMBIGUIDADE = "ambiguidade"


@dataclass
class MariaTask:
    id: int
    name: str
    description: str
    user_message: str
    expected_tool: str | None = None
    expected_keywords: list[str] = field(default_factory=list)
    confirm_sequence: list[str] = field(default_factory=list)
    expected_final_message: str | None = None
    context: list[dict] = field(default_factory=list)
    category: MariaTaskCategory = MariaTaskCategory.CONVERSA


@dataclass
class MariaTaskResult:
    task_id: int
    task_name: str
    category: str
    model: str
    tool_detected: str | None
    tool_correct: bool
    confirmation_completed: bool
    keyword_match: bool
    runtime_ok: bool
    final_message: str
    latency_ms: float
    errors: list[dict] = field(default_factory=list)
    raw_tool_args: dict = field(default_factory=dict)
    language_ok: bool = True
    tokens_gerados: int = 0
    tokens_por_segundo: float = 0.0


@dataclass
class MariaTaskAggregateResult:
    task_id: int
    task_name: str
    category: str
    execucoes: int
    tool_accuracy: float
    confirmation_success_rate: float
    keyword_match_rate: float
    runtime_success_rate: float
    avg_latency_ms: float
    stddev_latency_ms: float
    avg_tokens_por_segundo: float = 0.0
    avg_tokens_gerados: float = 0.0