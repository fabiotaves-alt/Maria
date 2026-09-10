"""LLM-as-judge experimental para o benchmark MARIA (fase B6).

ATENCAO: este modulo e EXPERIMENTAL e NAO CALIBRADO. O veredito produzido
aqui nao deve ser tratado como metrica oficial ate que uma rodada de
calibracao real (rotulagem manual + script de concordancia, ver
calibracao_judge.py) confirme concordancia >= 80% com avaliacao humana.
Nenhuma linha deste modulo afirma essa concordancia -- ela so pode ser
confirmada por um humano rodando calibracao_judge.py sobre uma amostra
rotulada.
"""
import json
import logging

from backend.infrastructure.llm.llama_client import LlamaClient

logger = logging.getLogger(__name__)

EIXOS_RUBRICA = ["tool_correta", "args_completos", "conteudo_coerente", "idioma"]

_PROMPT_TEMPLATE = """Voce e um avaliador tecnico de um assistente de IA de escritorio.
Avalie a execucao abaixo em 4 eixos, respondendo SOMENTE em JSON, sem texto
adicional, sem crases de codigo.

Mensagem do usuario: {user_message}
Ferramenta esperada: {expected_tool}
Ferramenta detectada: {tool_detected}
Argumentos obtidos: {raw_tool_args}
Mensagem final do assistente: {final_message}

Responda EXATAMENTE neste formato JSON:
{{
  "tool_correta": "ok" ou "falha",
  "args_completos": "ok" ou "falha",
  "conteudo_coerente": "ok" ou "falha",
  "idioma": "ok" ou "falha",
  "justificativa": "uma frase curta explicando o veredito geral"
}}
"""


def _montar_prompt(task, resultado) -> str:
    def _campo(obj, nome, default=""):
        if isinstance(obj, dict):
            return obj.get(nome, default)
        return getattr(obj, nome, default)

    return _PROMPT_TEMPLATE.format(
        user_message=_campo(task, "user_message"),
        expected_tool=_campo(task, "expected_tool"),
        tool_detected=_campo(resultado, "tool_detected"),
        raw_tool_args=json.dumps(_campo(resultado, "raw_tool_args", {}), ensure_ascii=False),
        final_message=_campo(resultado, "final_message"),
    )


def avaliar_execucao(task, resultado, cliente: LlamaClient | None = None) -> dict:
    """Retorna um dict com o veredito do judge, ou um veredito de erro se a
    chamada falhar. NUNCA levanta excecao -- falha do judge nao deve
    derrubar o benchmark (mesmo padrao de outras checagens auxiliares)."""
    cliente = cliente or LlamaClient(temperature=0.0)
    prompt = _montar_prompt(task, resultado)

    try:
        conteudo, _ = cliente.chat(messages=[{"role": "user", "content": prompt}])
    except Exception as exc:
        logger.warning("Falha ao chamar o judge: %s", exc)
        return _veredito_erro(f"falha_chamada_llm: {exc}")

    try:
        texto = conteudo.strip()
        if texto.startswith("```"):
            texto = texto.strip("`").lstrip("json").strip()
        veredito = json.loads(texto)
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("Falha ao parsear resposta do judge: %s | conteudo=%r", exc, conteudo)
        return _veredito_erro(f"falha_parse_json: {exc}")

    for eixo in EIXOS_RUBRICA:
        if veredito.get(eixo) not in ("ok", "falha"):
            return _veredito_erro(f"eixo_invalido_ou_ausente: {eixo}")

    veredito["experimental"] = True
    veredito["calibrado"] = False
    return veredito


def _veredito_erro(motivo: str) -> dict:
    veredito = {eixo: "erro" for eixo in EIXOS_RUBRICA}
    veredito["justificativa"] = motivo
    veredito["experimental"] = True
    veredito["calibrado"] = False
    return veredito

