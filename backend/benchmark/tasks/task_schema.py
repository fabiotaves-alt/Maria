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
    fixtures: list[str] = field(default_factory=list)
    category: MariaTaskCategory = MariaTaskCategory.CONVERSA
    tools_aceitos: list[str | None] | None = None
    expected_args_subset: dict | None = None


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
    args_correct: bool = True
    ttft_ms: float | None = None
    # Prompt enviado ao modelo nesta execução (mensagens completas: system
    # reforçado + histórico + user). Vazio quando a execução falhou antes do envio.
    prompt_enviado: list[dict] = field(default_factory=list)
    # Resposta crua gerada pelo modelo, ANTES de qualquer sobrescrita por
    # confirmação/ferramenta/continuação (final_message é a versão pós-processo).
    resposta_bruta_modelo: str = ""
    # Snapshot dos parâmetros de sampler efetivos usados na execução.
    sampler_params: dict = field(default_factory=dict)
    # False se houve erro de contexto (prompt > ctx_size do servidor).
    contexto_ok: bool = True
    # Número de tentativas de correção de tool call inválida (schema) usadas
    # nesta execução. 0 quando a tool call já veio válida ou quando não havia
    # ferramenta de escrita a validar.
    correction_attempts: int = 0
    # True quando a tarefa possui confirm_sequence — ou seja, a confirmação
    # efetivamente precisou ser exercitada. Permite medir a taxa de confirmação
    # SOMENTE sobre as tarefas elegíveis, eliminando o efeito cascata de
    # falhas de parser (que impedem a confirmação de ser sequer oferecida).
    confirmacao_elegivel: bool = False
    # True quando nenhuma tool call foi detectada MAS a resposta bruta contém
    # um padrão de chamada de ferramenta conhecida — indica falha provável do
    # parser textual, não "o modelo não chamou". Diagnóstico do benchmark.
    parse_suspeito: bool = False
    # finish_reason do último chunk do streaming ("stop", "tool_calls",
    # "length" ou None quando não capturado). "length" evidencia truncamento
    # por max_tokens.
    finish_reason: str | None = None


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