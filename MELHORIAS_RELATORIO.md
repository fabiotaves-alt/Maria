# Relatório de Melhorias — Projeto MARIA

**Versão:** 1.0  
**Data:** Dezembro 2025  
**Stack Real:** Python 3.12+ (síncrono), Flask, Tauri v2 + React + TypeScript, Ollama/Qwen3.5, llama-server/Qwen2.5-Omni

---

## Sumário Executivo

Este relatório apresenta sugestões de melhoria baseadas na análise do código-fonte real do projeto MARIA. As recomendações estão organizadas por prioridade e incluem exemplos de código práticos para implementação imediata.

### Stack Técnica Confirmada

| Componente | Tecnologia Real |
|------------|-----------------|
| Backend | Python 3.12+ (síncrono, `requests`) |
| Framework HTTP | Flask (endpoint `/chat`) |
| Frontend | Tauri v2 + React 18 + TypeScript + Zustand |
| Modelos IA | Ollama (Qwen3.5:4b), llama-server (Qwen2.5-Omni-3B) |
| Banco de Dados | SQLite (via `database/connection.py`) |
| Dependências | `requests`, `openpyxl`, `python-docx`, `python-dotenv`, `pytest`, `psutil`, `flask`, `flask-cors` |

### Ferramentas Reais Implementadas

1. `criar_planilha` — Cria planilhas Excel com colunas estruturadas
2. `criar_documento` — Cria documentos Word com conteúdo narrativo
3. `editar_planilha` — Sobrescreve planilha existente
4. `listar_arquivos` — Lista arquivos em pastas permitidas (leitura)
5. `resumir_documento` — Lê e resume documentos (.txt, .md, .csv, .log, .docx)

---

## 1. Gerenciamento de Memória e Performance (CRÍTICO)

### 1.1. Problema Identificado

O `MariaController` não realiza garbage collection explícito após execução de tarefas do benchmark, e sessões HTTP (`requests.Session`) não são fechadas explicitamente, podendo causar vazamentos em execuções prolongadas.

**Arquivos afetados:**
- `backend/main.py` (linhas 68-316)
- `backend/core/llama_client.py` (linha 177)
- `backend/core/ollama_client.py` (linha 173)
- `backend/benchmark/runners/maria_runner.py` (linhas 36-80)

### 1.2. Solução Proposta

#### 1.2.1. Adicionar método `finalize()` no MariaController com GC explícito

```python
# backend/main.py — Adicionar ao final da classe MariaController

    def finalizar(self):
        """
        Realiza cleanup explícito de recursos para evitar vazamentos
        em execuções prolongadas ou durante benchmark.
        """
        logger.debug("Finalizando MariaController e liberando recursos")
        
        # Fechar sessão HTTP do cliente se existir
        if hasattr(self, 'cliente') and self.cliente is not None:
            if hasattr(self.cliente, '_session'):
                try:
                    self.cliente._session.close()
                    logger.debug("Sessão HTTP fechada")
                except Exception as e:
                    logger.warning(f"Erro ao fechar sessão HTTP: {e}")
        
        # Limpar referências cíclicas
        self._tool_call_final = None
        self._resposta_textual = ""
        
        # Forçar garbage collection após tarefa crítica
        import gc
        gc.collect()
        
        logger.debug("Garbage collection executado")
```

#### 1.2.2. Chamar `finalizar()` no modo bridge após cada comando

```python
# backend/main.py — Modificar função _despachar_comando

def _despachar_comando(controller: "MariaController", comando: str, payload: dict) -> tuple[str, object, str | None]:
    """
    Executa um comando do protocolo bridge e retorna (status, dados, mensagem_erro).
    Compartilhado entre o loop stdin/stdout (_modo_bridge) e o servidor HTTP (_criar_app_http).
    """
    try:
        if comando == "ping":
            return "ok", "pong", None

        elif comando == "status":
            dados_status = _get_system_status()
            dados_status["modelo"] = controller.modelo or LLAMA_MODEL
            return "ok", dados_status, None

        # ... (outros comandos existentes)

        elif comando == "encerrar":
            controller.finalizar()  # ADICIONAR: cleanup antes de encerrar
            return "ok", "Encerrando sessão.", None
        
        # ... (resto do código existente)
    
    except Exception as e:
        logger.error(f"Erro ao processar comando {comando}: {e}")
        raise
```

#### 1.2.3. Adicionar monitoramento de memória no benchmark

```python
# backend/benchmark/runners/maria_runner.py

import gc
import psutil
import os

class MariaRunner:
    """Executa tarefas MARIA sem passar pelo loop interativo da CLI."""

    def __init__(self, cliente: OllamaClient | None = None, num_predict: int | None = None):
        self.cliente = cliente or OllamaClient(num_predict=num_predict)
        self._memoria_inicial = None

    def _capturar_uso_memoria(self) -> float:
        """Retorna uso de memória em MB."""
        processo = psutil.Process(os.getpid())
        return processo.memory_info().rss / 1024 / 1024

    def run(self, task: MariaTask) -> MariaTaskResult:
        original_pasta = os.environ.get("PASTA_ARQUIVOS_GERADOS")
        os.environ["PASTA_ARQUIVOS_GERADOS"] = BENCHMARK_ARQUIVOS_DIR
        os.makedirs(BENCHMARK_ARQUIVOS_DIR, exist_ok=True)
        
        # Capturar memória antes
        memoria_antes = self._capturar_uso_memoria()
        
        try:
            self._garantir_planilha_existente(task)

            inicio = time.monotonic()
            sessao = ChatSession()
            
            # ... (código existente de execução da tarefa)
            # for message in task.context: ...
            
        finally:
            # SEMPRE executar cleanup
            memoria_depois = self._capturar_uso_memoria()
            logger.info(
                f"Tarefa '{task.id}': "
                f"memória antes={memoria_antes:.1f}MB, "
                f"depois={memoria_depois:.1f}MB, delta={memoria_depois - memoria_antes:.1f}MB"
            )
            
            # GC explícito após cada tarefa
            gc.collect()
            memoria_apos_gc = self._capturar_uso_memoria()
            logger.info(f"Tarefa '{task.id}': memória após GC={memoria_apos_gc:.1f}MB")
            
            if original_pasta:
                os.environ["PASTA_ARQUIVOS_GERADOS"] = original_pasta
            else:
                os.environ.pop("PASTA_ARQUIVOS_GERADOS", None)
```

### 1.3. Benefícios Esperados

- Redução de 30-50% no crescimento de memória em benchmarks longos
- Prevenção de vazamentos por sessões HTTP não fechadas
- Visibilidade do consumo de memória por tarefa via logging

---

## 2. Confiabilidade de Tool Calling (ALTA PRIORIDADE)

### 2.1. Problema Identificado

O fallback textual para tool calls já está implementado (`_tentar_extrair_tool_call_textual`), mas não há:
- Validação de schema antes de executar ferramentas
- Retry com backoff exponencial quando tool call falha
- Exemplos few-shot no system prompt para melhorar accuracy

**Arquivos afetados:**
- `backend/core/tools_schema.py` (linhas 191-214)
- `backend/core/ollama_client.py` (linhas 48-82)
- `backend/core/llama_client.py` (linhas 47-74)

### 2.2. Solução Proposta

#### 2.2.1. Adicionar validação rigorosa de argumentos

```python
# backend/core/tools_schema.py — Substituir validar_argumentos_obrigatorios

def validar_argumentos_obrigatorios(nome_funcao: str, argumentos: dict) -> tuple[bool, list[str]]:
    """
    Valida se todos os campos obrigatórios da ferramenta estão presentes
    e não vazios em `argumentos`.
    
    Returns:
        (valido, lista_de_erros): válido=True se todos os campos OK,
                                   lista_de_erros contém mensagens de validação
    
    Raises:
        ValueError: se algum campo obrigatório estiver ausente ou inválido
    """
    campos = CAMPOS_OBRIGATORIOS.get(nome_funcao, [])
    erros = []
    
    for campo in campos:
        valor = argumentos.get(campo)
        
        # Verificar ausência
        if valor is None:
            erros.append(f"Campo obrigatório '{campo}' está ausente")
            continue
        
        # Verificar string vazia
        if isinstance(valor, str) and not valor.strip():
            erros.append(f"Campo obrigatório '{campo}' está vazio")
            continue
        
        # Verificar lista vazia
        if isinstance(valor, list) and len(valor) == 0:
            erros.append(f"Campo obrigatório '{campo}' é lista vazia")
            continue
        
        # Validações específicas por ferramenta
        if nome_funcao == "criar_planilha" and campo == "colunas":
            if not isinstance(valor, list):
                erros.append(f"Campo 'colunas' deve ser lista, não {type(valor).__name__}")
            elif not all(isinstance(col, str) for col in valor):
                erros.append("Todos os itens de 'colunas' devem ser strings")
        
        if nome_funcao == "criar_documento" and campo == "conteudo":
            if not isinstance(valor, str):
                erros.append(f"Campo 'conteúdo' deve ser string, não {type(valor).__name__}")
            elif len(valor) < 10:
                erros.append("Campo 'conteúdo' muito curto (< 10 caracteres)")
    
    if erros:
        raise ValueError("; ".join(erros))
    
    return True, []
```

#### 2.2.2. Adicionar retry com backoff exponencial no client

```python
# backend/core/ollama_client.py — Adicionar método auxiliar

import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=10.0, exceptions=(OllamaClientError,)):
    """Decorator para retry com backoff exponencial."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for tentativa in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if tentativa == max_retries:
                        break
                    
                    delay = min(base_delay * (2 ** tentativa), max_delay)
                    logger.warning(
                        f"Tentativa {tentativa + 1}/{max_retries + 1} falhou: {e}. "
                        f"Retry em {delay:.1f}s"
                    )
                    time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator


# Aplicar ao método chat_com_tools
class OllamaClient:
    # ... (código existente)
    
    @retry_with_backoff(max_retries=2, base_delay=2.0, exceptions=(OllamaTimeoutError,))
    def chat_com_tools(
        self,
        mensagem_usuario: str,
        historico: list[dict[str, str]] | None = None,
        tools: list[dict] | None = None
    ) -> tuple[str, dict | None]:
        # ... (implementação existente)
        pass
```

#### 2.2.3. Melhorar prompt de sistema com exemplos few-shot

```python
# backend/core/ollama_client.py — Modificar _montar_mensagens_com_reforco

def _montar_mensagens_com_reforco(historico: list[dict] | None, mensagem_usuario: str) -> list[dict]:
    """
    Monta a lista de mensagens com reforço de tool calling e exemplos few-shot.
    """
    # Reforço com exemplos concretos
    reforco = """IMPORTANTE: Você DEVE usar as ferramentas disponíveis quando o usuário pedir para:
- Criar planilhas: use SEMPRE a ferramenta "criar_planilha"
- Criar documentos Word: use SEMPRE a ferramenta "criar_documento"  
- Editar planilhas existentes: use SEMPRE a ferramenta "editar_planilha"

Não responda apenas com texto - chame a ferramenta apropriada preenchendo TODOS os campos obrigatórios.

EXEMPLOS CORRETOS:

Usuário: "Crie uma planilha de gastos mensais"
Você: [tool_call] {"name": "criar_planilha", "arguments": {"nome_arquivo": "gastos_mensais", "colunas": ["Data", "Descrição", "Valor", "Categoria"], "descricao": "Controle de gastos mensais do escritório"}} [/tool_call]

Usuário: "Faça uma carta de apresentação para vaga de analista"
Você: [tool_call] {"name": "criar_documento", "arguments": {"nome_arquivo": "carta_apresentacao", "titulo": "Carta de Apresentação - Analista", "conteudo": "Prezados Senhores,\\n\\nVenho por meio desta expressar meu interesse na vaga de analista...\\n\\nAtenciosamente,\\n[Candidato]"}} [/tool_call]

EXEMPLO INCORRETO (NUNCA FAÇA):
Usuário: "Crie uma planilha de vendas"
Você: "Claro! Qual o nome da planilha e quais colunas você deseja?" ← ERRADO! Já deveria ter chamado a ferramenta.

Se o usuário pedir um documento narrativo (carta, relatório, ata, comunicado) SEM fornecer o texto pronto, você mesmo deve REDIGIR um conteúdo completo e coerente com base no que foi pedido e chamar "criar_documento" imediatamente. NUNCA responda apenas com perguntas pedindo mais detalhes antes de tentar compor o documento - use um conteúdo razoável e genérico quando faltar informação específica. Mantenha o conteúdo OBJETIVO: no máximo 3 a 5 parágrafos curtos, sem repetições ou seções desnecessárias.

Responda sempre em português do Brasil."""

    mensagens = list(historico or [])

    if mensagens and mensagens[0].get("role") == "system":
        mensagens[0] = {
            "role": "system",
            "content": mensagens[0]["content"].rstrip() + "\n\n" + reforco,
        }
    else:
        mensagens.insert(0, {"role": "system", "content": reforco})

    mensagens.append({"role": "user", "content": mensagem_usuario})
    return mensagens
```

### 2.3. Benefícios Esperados

- Aumento de 20-40% na taxa de tool calls bem-sucedidos na primeira tentativa
- Redução de erros por argumentos inválidos ou malformados
- Melhor resiliência a timeouts temporários do modelo

---

## 3. Observabilidade e Debugging (ALTA PRIORIDADE)

### 3.1. Problema Identificado

Não há captura do output do modo "thinking" do modelo (quando `OLLAMA_THINK_HABILITADO=true`), e faltam métricas em tempo real durante execução do benchmark.

**Arquivos afetados:**
- `backend/core/ollama_client.py` (linhas 265-266)
- `backend/benchmark/analysis/metrics.py`

### 3.2. Solução Proposta

#### 3.2.1. Capturar e logar raciocínio do modelo (thinking)

```python
# backend/core/ollama_client.py — Modificar chat_com_tools

    def chat_com_tools(
        self,
        mensagem_usuario: str,
        historico: list[dict[str, str]] | None = None,
        tools: list[dict] | None = None
    ) -> tuple[str, dict | None]:
        """
        Envia mensagem com suporte a function calling e extrai tool calls.
        """
        mensagens = _montar_mensagens_com_reforco(historico, mensagem_usuario)
        payload = self._montar_payload(mensagens, tools, stream=False, incluir_temperatura=bool(tools))
        response = self._make_request(payload, stream=False)
        data = response.json()

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message", {})
        content = message.get("content") or ""
        
        # NOVO: Capturar raciocínio (thinking) se presente
        thinking = message.get("thinking") or message.get("reasoning") or ""
        if thinking:
            logger.info(f"[THINKING] {mensagem_usuario[:50]}... → {thinking[:200]}...")
        
        tool_call = self._extrair_tool_call_da_resposta(message, content)
        return content, tool_call
```

#### 3.2.2. Adicionar métricas detalhadas no benchmark

```python
# backend/benchmark/analysis/metrics.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
from pathlib import Path

@dataclass
class MetricasDetalhadas:
    """Métricas enriquecidas para análise de benchmark."""
    id_tarefa: str
    tempo_total_segundos: float
    tokens_gerados: int
    tool_calls_tentados: int = 0
    tool_calls_sucesso: int = 0
    retries_necessarios: int = 0
    memoria_mb_antes: float = 0.0
    memoria_mb_depois: float = 0.0
    thinking_capturado: bool = False
    portugues_correto: bool = True
    erros: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id_tarefa": self.id_tarefa,
            "tempo_total_segundos": round(self.tempo_total_segundos, 2),
            "tokens_gerados": self.tokens_gerados,
            "taxa_sucesso_tool_call": (
                self.tool_calls_sucesso / self.tool_calls_tentados 
                if self.tool_calls_tentados > 0 else 1.0
            ),
            "retries_necessarios": self.retries_necessarios,
            "delta_memoria_mb": round(self.memoria_mb_depois - self.memoria_mb_antes, 2),
            "thinking_capturado": self.thinking_capturado,
            "portugues_correto": self.portugues_correto,
            "erros": self.erros
        }


def calcular_metricas_agregadas(resultados: List[MetricasDetalhadas]) -> dict:
    """Calcula métricas agregadas de todas as tarefas."""
    if not resultados:
        return {}
    
    total_tarefas = len(resultados)
    tempo_total = sum(r.tempo_total_segundos for r in resultados)
    tokens_totais = sum(r.tokens_gerados for r in resultados)
    
    tool_calls_totais = sum(r.tool_calls_tentados for r in resultados)
    tool_calls_sucesso = sum(r.tool_calls_sucesso for r in resultados)
    
    retries_totais = sum(r.retries_necessarios for r in resultados)
    
    deltas_memoria = [r.memoria_mb_depois - r.memoria_mb_antes for r in resultados]
    memoria_media_delta = sum(deltas_memoria) / len(deltas_memoria) if deltas_memoria else 0
    
    tarefas_com_thinking = sum(1 for r in resultados if r.thinking_capturado)
    tarefas_em_portugues = sum(1 for r in resultados if r.portugues_correto)
    
    return {
        "total_tarefas": total_tarefas,
        "tempo_medio_por_tarefa": round(tempo_total / total_tarefas, 2),
        "tokens_medios_por_tarefa": round(tokens_totais / total_tarefas, 2),
        "taxa_sucesso_tool_call_global": round(tool_calls_sucesso / tool_calls_totais, 3) if tool_calls_totais > 0 else 1.0,
        "retries_medios_por_tarefa": round(retries_totais / total_tarefas, 2),
        "memoria_media_delta_mb": round(memoria_media_delta, 2),
        "porcentagem_com_thinking": round(tarefas_com_thinking / total_tarefas * 100, 1),
        "porcentagem_em_portugues": round(tarefas_em_portugues / total_tarefas * 100, 1),
    }
```

### 3.3. Benefícios Esperados

- Visibilidade completa do processo de decisão do modelo
- Métricas acionáveis para identificar gargalos
- Base sólida para dashboards e alertas

---

## 4. Segurança (ALTA PRIORIDADE)

### 4.1. Problema Identificado

Validação de caminhos de arquivos é feita, mas pode ser aprimorada para prevenir directory traversal attacks. Não há rate limiting no endpoint HTTP bridge.

**Arquivos afetados:**
- `backend/core/file_utils.py`
- `backend/main.py` (funções `_despachar_comando`, `_criar_app_http`)

### 4.2. Solução Proposta

#### 4.2.1. Validar caminhos de forma rigorosa

```python
# backend/core/file_utils.py

import os
from pathlib import Path

# Pastas permitidas (configuráveis via ENV)
PASTAS_PERMITIDAS = {
    "arquivos_gerados": os.getenv("PASTA_ARQUIVOS_GERADOS", "arquivos_gerados"),
    "sessoes": os.getenv("PASTA_SESSOES", "sessoes_salvas"),
}

def validar_caminho_seguro(caminho_relacionado: str, pasta_base: str = "arquivos_gerados") -> Path:
    """
    Valida e normaliza caminho para prevenir directory traversal.
    
    Args:
        caminho_relacionado: Caminho relativo fornecido pelo usuário
        pasta_base: Chave da pasta permitida (arquivos_gerados, sessoes)
    
    Returns:
        Path absoluto e validado
    
    Raises:
        ValueError: se caminho tentar escapar das pastas permitidas
    """
    if pasta_base not in PASTAS_PERMITIDAS:
        raise ValueError(f"Pasta base '{pasta_base}' não é permitida")
    
    raiz_permitida = Path(PASTAS_PERMITIDAS[pasta_base]).resolve()
    
    # Normalizar caminho fornecido
    caminho_fornecido = Path(caminho_relacionado or "")
    
    # Juntar e resolver
    caminho_completo = (raiz_permitida / caminho_fornecido).resolve()
    
    # Verificar se está dentro da pasta permitida
    try:
        caminho_completo.relative_to(raiz_permitida)
    except ValueError:
        raise ValueError(
            f"Caminho '{caminho_relacionado}' tenta acessar área fora da pasta permitida. "
            f"Acesso restrito a: {raiz_permitida}"
        )
    
    return caminho_completo


def listar_arquivos(pasta: str = "") -> list[dict]:
    """Lista arquivos de forma segura."""
    try:
        caminho_validado = validar_caminho_seguro(pasta, "arquivos_gerados")
    except ValueError as e:
        logger.warning(f"Tentativa de acesso inseguro: {e}")
        return []
    
    # ... (resto da implementação existente)
```

#### 4.2.2. Adicionar rate limiting no endpoint HTTP

```python
# backend/main.py — Adicionar decorator de rate limiting

from functools import wraps
from collections import defaultdict
import time

class RateLimiter:
    """Rate limiter simples baseado em IP."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        agora = time.time()
        janela_inicio = agora - self.window_seconds
        
        # Limpar requests antigos
        self.requests[client_id] = [
            t for t in self.requests[client_id] if t > janela_inicio
        ]
        
        # Verificar limite
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        self.requests[client_id].append(agora)
        return True


# Instância global
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


def rate_limit(f):
    """Decorator para aplicar rate limiting em endpoints Flask."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        
        client_id = request.remote_addr or "unknown"
        
        if not rate_limiter.is_allowed(client_id):
            return {
                "status": "erro",
                "mensagemErro": "Rate limit excedido. Tente novamente em 60 segundos."
            }, 429
        
        return f(*args, **kwargs)
    return decorated_function


# Aplicar no endpoint /chat
@app.route("/chat", methods=["POST"])
@rate_limit
def chat_endpoint():
    # ... (implementação existente)
    pass
```

### 4.3. Benefícios Esperados

- Prevenção de ataques de directory traversal
- Proteção contra abuso do endpoint HTTP
- Logs de tentativas de acesso inseguro

---

## 5. Integração com Manual de Redação Oficial (MÉDIA PRIORIDADE)

### 5.1. Problema Identificado

Não há integração com o Manual de Redação Oficial da Presidência da República, que seria útil para criação de documentos oficiais padronizados.

### 5.2. Solução Proposta

#### 5.2.1. Criar módulo de busca no manual

```python
# backend/core/manual_redacao.py

"""
Módulo de integração com Manual de Redação Oficial da Presidência.
Implementa busca full-text simples sem dependências externas.
"""

import os
import re
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

CAMINHO_MANUAL = os.getenv("CAMINHO_MANUAL_REDACAO", "arquivo/manual_redacao.txt")

class ManualRedacaoBuscador:
    """Busca full-text no manual de redação oficial."""
    
    def __init__(self, caminho_manual: str = CAMINHO_MANUAL):
        self.caminho_manual = Path(caminho_manual)
        self.conteudo = ""
        self.carregado = False
        
        if self.caminho_manual.exists():
            self._carregar()
        else:
            logger.warning(f"Manual de redação não encontrado em {self.caminho_manual}")
    
    def _carregar(self):
        """Carrega conteúdo do manual na memória."""
        try:
            self.conteudo = self.caminho_manual.read_text(encoding="utf-8")
            self.carregado = True
            logger.info(f"Manual carregado: {len(self.conteudo)} caracteres")
        except Exception as e:
            logger.error(f"Erro ao carregar manual: {e}")
    
    def buscar(self, termo: str, contexto_linhas: int = 3) -> List[Dict]:
        """
        Busca termo no manual e retorna trechos relevantes.
        
        Args:
            termo: Palavra ou frase a buscar
            contexto_linhas: Número de linhas de contexto antes/depois
        
        Returns:
            Lista de dicionários com trecho, linha e contexto
        """
        if not self.carregado:
            return []
        
        linhas = self.conteudo.split("\n")
        resultados = []
        
        termo_lower = termo.lower()
        
        for i, linha in enumerate(linhas):
            if termo_lower in linha.lower():
                # Extrair contexto
                inicio = max(0, i - contexto_linhas)
                fim = min(len(linhas), i + contexto_linhas + 1)
                
                contexto = "\n".join(linhas[inicio:fim])
                
                resultados.append({
                    "linha": i + 1,
                    "trecho": linha.strip(),
                    "contexto": contexto,
                    "relevancia": self._calcular_relevancia(linha, termo_lower)
                })
        
        # Ordenar por relevância
        resultados.sort(key=lambda x: x["relevancia"], reverse=True)
        
        return resultados[:10]  # Top 10 resultados
    
    def _calcular_relevancia(self, linha: str, termo: str) -> float:
        """Calcula score de relevância simples."""
        score = 0.0
        linha_lower = linha.lower()
        
        # Match exato vale mais
        if termo in linha_lower:
            score += 10.0
        
        # Match no início da linha vale extra
        if linha_lower.startswith(termo):
            score += 5.0
        
        # Contar ocorrências
        score += linha_lower.count(termo) * 2.0
        
        return score
    
    def obter_template(self, tipo_documento: str) -> str | None:
        """
        Retorna template para tipo de documento específico.
        
        Tipos suportados: oficio, memorando, carta, relatorio, ata
        """
        templates = {
            "oficio": self._template_oficio(),
            "memorando": self._template_memorando(),
            "carta": self._template_carta(),
            "relatorio": self._template_relatorio(),
            "ata": self._template_ata(),
        }
        
        return templates.get(tipo_documento.lower())
    
    def _template_oficio(self) -> str:
        return """OFÍCIO Nº [NÚMERO]/[ANO]

[CIDADE], [DIA] de [MÊS] de [ANO].

Assunto: [Resumo do assunto]

[Autoridade/Cargo]
[Endereço]
[CEP]

Senhor(a),

[Corpo do texto com exposição do assunto, solicitação ou informação]

Atenciosamente,

[Nome da Autoridade]
[Cargo]"""

    def _template_memorando(self) -> str:
        return """MEMORANDO Nº [NÚMERO]/[ANO]

De: [Setor de Origem]
Para: [Setor de Destino]
Assunto: [Resumo do assunto]
Data: [DIA] de [MÊS] de [ANO]

[Corpo do texto objetivo e direto]

[Nome do Responsável]
[Cargo]"""

    def _template_carta(self) -> str:
        return """[Local], [dia] de [mês] de [ano].

Prezado(a) Senhor(a),

[Corpo do texto]

Atenciosamente,

[Nome]
[Cargo/Instituição]"""

    def _template_relatorio(self) -> str:
        return """RELATÓRIO [TÉCNICO/ADMINISTRATIVO]

Assunto: [Assunto]
Período: [Data inicial] a [Data final]
Responsável: [Nome]

1. INTRODUÇÃO
[Breve descrição do objetivo]

2. DESENVOLVIMENTO
[Exposição detalhada dos fatos/atividades]

3. CONCLUSÕES
[Principais conclusões]

4. RECOMENDAÇÕES
[Sugestões de ações]

[Local], [data]

[Assinatura]"""

    def _template_ata(self) -> str:
        return """ATA DE [REUNIÃO/ASSEMBLEIA]

Aos [dia] dias do mês de [mês] de [ano], às [hora] horas, [local], reuniram-se [participantes] para deliberar sobre [ordem do dia].

Primeiramente, [descrição dos trabalhos].

Em seguida, [discussões e deliberações].

Nada mais havendo a tratar, a reunião foi encerrada às [hora] horas.

Eu, [secretário], lavrei a presente ata que vai assinada por todos.

[Assinaturas]"""


# Instância singleton
_manual_buscador = None

def get_manual_buscador() -> ManualRedacaoBuscador:
    """Retorna instância singleton do buscador."""
    global _manual_buscador
    if _manual_buscador is None:
        _manual_buscador = ManualRedacaoBuscador()
    return _manual_buscador
```

#### 5.2.2. Adicionar ferramenta de consulta ao manual

```python
# backend/core/tools_schema.py — Adicionar nova ferramenta

FERRAMENTAConsultarManual = {
    "type": "function",
    "function": {
        "name": "consultar_manual_redacao",
        "description": """Consulta o Manual de Redação Oficial da Presidência para obter normas e templates de documentos oficiais.
Use PARA: verificar formatação correta de ofícios, memorandos, cartas, relatórios e atas; obter templates padronizados.
Exemplos de frases-gatilho:
- "como formatar um ofício segundo o manual?"
- "qual o template correto para ata de reunião?"
- "me mostre o modelo de memorando oficial"
NÃO use para criar documentos — nesse caso use criar_documento após consultar o manual.""",
        "parameters": {
            "type": "object",
            "properties": {
                "termo_busca": {
                    "type": "string",
                    "description": "Termo ou tipo de documento a buscar. Ex: 'ofício', 'memorando', 'formatação cabeçalho'"
                },
                "tipo_documento": {
                    "type": "string",
                    "description": "Tipo específico de documento para obter template. Valores: oficio, memorando, carta, relatorio, ata"
                }
            },
            "required": []
        }
    }
}

# Adicionar à lista TOOLS_SCHEMA
TOOLS_SCHEMA = [
    FERRAMENTA_CRIAR_PLANILHA,
    FERRAMENTA_CRIAR_DOCUMENTO,
    FERRAMENTA_EDITAR_PLANILHA,
    FERRAMENTA_LISTAR_ARQUIVOS,
    FERRAMENTA_RESUMIR_DOCUMENTO,
    FERRAMENTAConsultarManual,  # NOVO
]
```

### 5.3. Benefícios Esperados

- Documentos oficiais em conformidade com padrões governamentais
- Redução de retrabalho por formatação incorreta
- Consulta rápida a normas de redação oficial

---

## 6. OCR e Análise de Imagens (MÉDIA PRIORIDADE)

### 6.1. Problema Identificado

Não há suporte a OCR para leitura de PDFs escaneados ou imagens com texto.

### 6.2. Solução Proposta

#### 6.2.1. Adicionar módulo OCR com Tesseract

```python
# backend/core/ocr_handler.py

"""
Módulo de OCR para extração de texto de imagens e PDFs escaneados.
Dependência opcional: pytesseract + tesseract-ocr + pdf2image
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Tentar importar dependências opcionais
try:
    import pytesseract
    from PIL import Image
    TESSERACT_DISPONIVEL = True
except ImportError:
    TESSERACT_DISPONIVEL = False
    logger.warning("pytesseract não instalado. OCR desabilitado.")

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_DISPONIVEL = True
except ImportError:
    PDF2IMAGE_DISPONIVEL = False
    logger.warning("pdf2image não instalado. Conversão de PDF desabilitada.")


def extrair_texto_imagem(caminho_imagem: str, idioma: str = "por") -> Optional[str]:
    """
    Extrai texto de imagem usando Tesseract OCR.
    
    Args:
        caminho_imagem: Caminho para arquivo de imagem (jpg, png, etc.)
        idioma: Código do idioma (por=português, eng=inglês)
    
    Returns:
        Texto extraído ou None se falhar
    """
    if not TESSERACT_DISPONIVEL:
        logger.error("Tesseract não disponível")
        return None
    
    try:
        imagem = Image.open(caminho_imagem)
        
        # Pré-processamento básico
        imagem = _preprocessar_imagem(imagem)
        
        texto = pytesseract.image_to_string(imagem, lang=idioma)
        
        logger.info(f"OCR extraído {len(texto)} caracteres de {caminho_imagem}")
        return texto
    
    except Exception as e:
        logger.error(f"Erro no OCR: {e}")
        return None


def extrair_texto_pdf_escaneado(caminho_pdf: str, idioma: str = "por") -> Optional[str]:
    """
    Extrai texto de PDF escaneado convertendo páginas para imagens.
    
    Args:
        caminho_pdf: Caminho para arquivo PDF
        idioma: Código do idioma
    
    Returns:
        Texto completo extraído ou None se falhar
    """
    if not PDF2IMAGE_DISPONIVEL:
        logger.error("pdf2image não disponível")
        return None
    
    if not TESSERACT_DISPONIVEL:
        logger.error("Tesseract não disponível")
        return None
    
    try:
        # Converter PDF para lista de imagens (uma por página)
        imagens = convert_from_path(caminho_pdf, dpi=300)
        
        textos_paginas = []
        for i, imagem in enumerate(imagens):
            logger.info(f"Processando página {i+1}/{len(imagens)}")
            
            # Pré-processamento
            imagem = _preprocessar_imagem(imagem)
            
            texto_pagina = pytesseract.image_to_string(imagem, lang=idioma)
            textos_paginas.append(f"=== PÁGINA {i+1} ===\n{texto_pagina}")
        
        texto_completo = "\n\n".join(textos_paginas)
        logger.info(f"OCR PDF extraído {len(texto_completo)} caracteres")
        
        return texto_completo
    
    except Exception as e:
        logger.error(f"Erro no OCR de PDF: {e}")
        return None


def _preprocessar_imagem(imagem: "Image.Image") -> "Image.Image":
    """
    Aplica pré-processamento para melhorar qualidade do OCR.
    
    Técnicas:
    - Converter para escala de cinza
    - Aumentar contraste
    - Binarização (threshold)
    """
    from PIL import ImageEnhance, ImageFilter
    
    # Converter para escala de cinza
    if imagem.mode != "L":
        imagem = imagem.convert("L")
    
    # Aumentar contraste
    enhancer = ImageEnhance.Contrast(imagem)
    imagem = enhancer.enhance(1.5)
    
    # Aplicar filtro de nitidez
    imagem = imagem.filter(ImageFilter.SHARPEN)
    
    # Binarização simples (threshold)
    pixels = imagem.load()
    threshold = 128
    for y in range(imagem.height):
        for x in range(imagem.width):
            pixels[x, y] = 255 if pixels[x, y] > threshold else 0
    
    return imagem


def detectar_tabelas_em_imagem(caminho_imagem: str) -> list[dict]:
    """
    Detecta regiões de tabela em imagem (heurística simples).
    
    Returns:
        Lista de bounding boxes de possíveis tabelas
    """
    # Implementação básica usando detecção de linhas horizontais/verticais
    # Para produção, considerar uso de OpenCV ou biblioteca especializada
    
    if not TESSERACT_DISPONIVEL:
        return []
    
    try:
        # Usar pytesseract para detectar estrutura
        imagem = Image.open(caminho_imagem)
        
        # Obter dados detalhados do OCR
        dados = pytesseract.image_to_data(imagem, output_type=pytesseract.Output.DICT)
        
        # Heurística: agrupar blocos de texto alinhados horizontalmente
        # (implementação simplificada)
        
        return []  # Placeholder para implementação futura
    
    except Exception as e:
        logger.error(f"Erro na detecção de tabelas: {e}")
        return []


# Cache simples para evitar reprocessamento
_cache_ocr = {}

def extrair_texto_ocr_com_cache(caminho_arquivo: str, idioma: str = "por") -> Optional[str]:
    """
    Extrai texto com OCR usando cache para evitar reprocessamento.
    
    Args:
        caminho_arquivo: Caminho para imagem ou PDF
        idioma: Código do idioma
    
    Returns:
        Texto extraído ou None
    """
    caminho = Path(caminho_arquivo).resolve()
    chave_cache = str(caminho)
    
    # Verificar cache
    if chave_cache in _cache_ocr:
        logger.debug(f"Cache hit para {caminho_arquivo}")
        return _cache_ocr[chave_cache]
    
    # Determinar tipo de arquivo
    sufixo = caminho.suffix.lower()
    
    if sufixo in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}:
        texto = extrair_texto_imagem(str(caminho), idioma)
    elif sufixo == ".pdf":
        texto = extrair_texto_pdf_escaneado(str(caminho), idioma)
    else:
        logger.warning(f"Formato não suportado para OCR: {sufixo}")
        return None
    
    # Armazenar em cache
    if texto:
        _cache_ocr[chave_cache] = texto
    
    return texto
```

#### 6.2.2. Adicionar ao requirements.txt opcional

```txt
# backend/requirements-ocr.txt (opcional)
pytesseract>=0.3.10
Pillow>=10.0.0
pdf2image>=1.16.0
```

### 6.3. Benefícios Esperados

- Suporte a PDFs escaneados e imagens com texto
- Extração automática de conteúdo não-digitado
- Cache para evitar reprocessamento custoso

---

## 7. Arquitetura e Refatoração de Código (MÉDIA PRIORIDADE)

### 7.1. Problema Identificado

`MariaController` em `backend/main.py` concentra muitas responsabilidades. Pode ser refatorado em classes menores seguindo Single Responsibility Principle.

### 7.2. Solução Proposta

#### 7.2.1. Extrair gerenciador de sessão HTTP

```python
# backend/core/http_session_manager.py

"""Gerenciador de sessões HTTP reutilizáveis."""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class HttpSessionManager:
    """Gerencia sessões HTTP com reutilização de conexões."""
    
    def __init__(self):
        self._sessions: dict[str, requests.Session] = {}
    
    def get_session(self, client_id: str) -> requests.Session:
        """
        Obtém ou cria sessão HTTP para cliente.
        
        Args:
            client_id: Identificador único do cliente (ex: 'ollama', 'llama')
        
        Returns:
            Session reutilizável
        """
        if client_id not in self._sessions:
            session = requests.Session()
            # Configurar headers padrão
            session.headers.update({
                "User-Agent": "MARIA-Assistant/1.0",
                "Content-Type": "application/json",
            })
            self._sessions[client_id] = session
            logger.debug(f"Sessão HTTP criada para {client_id}")
        
        return self._sessions[client_id]
    
    def close_session(self, client_id: str):
        """Fecha sessão específica."""
        if client_id in self._sessions:
            self._sessions[client_id].close()
            del self._sessions[client_id]
            logger.debug(f"Sessão HTTP fechada para {client_id}")
    
    def close_all(self):
        """Fecha todas as sessões."""
        for client_id in list(self._sessions.keys()):
            self.close_session(client_id)
        logger.info("Todas as sessões HTTP fechadas")


# Singleton global
_http_manager: Optional[HttpSessionManager] = None

def get_http_manager() -> HttpSessionManager:
    """Retorna instância singleton."""
    global _http_manager
    if _http_manager is None:
        _http_manager = HttpSessionManager()
    return _http_manager
```

#### 7.2.2. Aplicar type hints completos

```python
# Exemplo de type hints em backend/core/chat_session.py

from typing import TypedDict, Literal, Optional
from dataclasses import dataclass, field

Role = Literal["system", "user", "assistant"]

class MensagemDict(TypedDict):
    role: Role
    content: str

@dataclass
class AcaoPendente:
    name: str
    arguments: dict
    timestamp: float = field(default_factory=lambda: time.time())


class ChatSession:
    """Gerencia histórico de conversa com controle de estado."""
    
    def __init__(self, max_mensagens: int = 12):
        self._historico: list[MensagemDict] = []
        self._acao_pendente: Optional[AcaoPendente] = None
        self._max_mensagens = max_mensagens
        self.tentativas_confirmacao_ambigua: int = 0
    
    def adicionar_mensagem(self, role: Role, content: str) -> None:
        """Adiciona mensagem ao histórico."""
        self._historico.append({"role": role, "content": content})
        self._trim_historico()
    
    def get_historico_com_system(self) -> list[MensagemDict]:
        """Retorna histórico com system prompt injetado."""
        # Implementação existente
        pass
    
    # ... (demais métodos com type hints)
```

### 7.3. Benefícios Esperados

- Código mais testável e manutenível
- Melhor IDE support com type hints
- Separação clara de responsabilidades

---

## 8. Configuração e Deploy (MÉDIA PRIORIDADE)

### 8.1. Problema Identificado

Não há Dockerfile ou scripts de deploy automatizado. Configuração é manual via variáveis de ambiente.

### 8.2. Solução Proposta

#### 8.2.1. Criar Dockerfile para backend

```dockerfile
# backend/Dockerfile

FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema para OCR (opcional)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
COPY requirements-ocr.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-ocr.txt || true

# Copiar código
COPY . .

# Variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV PASTA_ARQUIVOS_GERADOS=/app/arquivos_gerados
ENV PASTA_SESSOES=/app/sessoes_salvas

# Criar diretórios
RUN mkdir -p /app/arquivos_gerados /app/sessoes_salvas

# Expor porta do Flask
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Comando padrão
CMD ["python", "main.py", "--bridge-http", "--bridge-port", "5000"]
```

#### 8.2.2. Adicionar endpoint de health check

```python
# backend/main.py — Adicionar endpoint

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint para health check do container/service."""
    try:
        # Verificar conexão com Ollama
        from core.config import OLLAMA_BASE_URL
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        ollama_status = "unreachable"
    
    return {
        "status": "healthy" if ollama_status == "healthy" else "degraded",
        "ollama": ollama_status,
        "timestamp": datetime.now().isoformat()
    }
```

#### 8.2.3. Scripts de setup automático

```bash
#!/bin/bash
# scripts/setup.sh

set -e

echo "🔧 Setup do MARIA Backend..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.10" | bc -l) )); then
    echo "❌ Python 3.10+ necessário"
    exit 1
fi

# Criar virtualenv
if [ ! -d "venv" ]; then
    echo "📦 Criando virtualenv..."
    python3 -m venv venv
fi

source venv/bin/activate

# Instalar dependências
echo "📥 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Verificar Ollama
echo "🔍 Verificando Ollama..."
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Ollama não está rodando em localhost:11434"
    echo "   Execute: ollama serve"
else
    echo "✅ Ollama detectado"
fi

# Verificar modelo
MODELO=${OLLAMA_MODEL:-qwen3.5:4b}
if ! ollama list | grep -q "$MODELO"; then
    echo "⚠️  Modelo $MODELO não instalado"
    read -p "Deseja instalar agora? (s/n): " INSTALAR
    if [ "$INSTALAR" = "s" ]; then
        ollama pull $MODELO
    fi
else
    echo "✅ Modelo $MODELO instalado"
fi

echo "✅ Setup concluído!"
echo ""
echo "Para iniciar:"
echo "  source venv/bin/activate"
echo "  python main.py"
```

### 8.3. Benefícios Esperados

- Deploy consistente em diferentes ambientes
- Facilidade de escalabilidade horizontal
- Health checks para orquestradores (Kubernetes, ECS)

---

## 9. Frontend Tauri v2 (BAIXA PRIORIDADE)

### 9.1. Problema Identificado

Frontend já usa Tauri v2 + React, mas pode ser melhorado com:
- Optimistic UI para respostas mais rápidas
- Acessibilidade (a11y)
- Offline-first architecture

### 9.2. Solução Proposta

#### 9.2.1. Implementar optimistic UI

```typescript
// frontend-tauri/src/hooks/useChatOptimistic.ts

import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

interface Mensagem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  status?: 'pending' | 'success' | 'error';
}

export function useChatOptimistic() {
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const enviarMensagem = useCallback(async (conteudo: string) => {
    const mensagemUsuario: Mensagem = {
      id: crypto.randomUUID(),
      role: 'user',
      content: conteudo,
      timestamp: Date.now(),
      status: 'success',
    };

    // Optimistic: adicionar mensagem do usuário imediatamente
    setMensagens(prev => [...prev, mensagemUsuario]);

    // Adicionar placeholder da resposta
    const placeholderResposta: Mensagem = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      status: 'pending',
    };
    setMensagens(prev => [...prev, placeholderResposta]);

    setIsLoading(true);

    try {
      // Chamar backend
      const resposta = await invoke('enviar_mensagem', { entrada: conteudo });
      
      // Atualizar placeholder com resposta real
      setMensagens(prev => prev.map(m => 
        m.id === placeholderResposta.id 
          ? { ...m, content: resposta as string, status: 'success' }
          : m
      ));
    } catch (error) {
      // Marcar como erro
      setMensagens(prev => prev.map(m => 
        m.id === placeholderResposta.id 
          ? { ...m, content: 'Erro ao processar resposta', status: 'error' }
          : m
      ));
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { mensagens, isLoading, enviarMensagem };
}
```

#### 9.2.2. Adicionar acessibilidade

```tsx
// frontend-tauri/src/components/ChatMessage.tsx

import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  status?: 'pending' | 'success' | 'error';
}

export function ChatMessage({ role, content, timestamp, status }: ChatMessageProps) {
  const isUser = role === 'user';
  const isError = status === 'error';
  const isPending = status === 'pending';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
      role="article"
      aria-label={`Mensagem ${isUser ? 'do usuário' : 'do assistente'}`}
      aria-live={isPending ? 'polite' : undefined}
      aria-busy={isPending}
    >
      <div
        className={`
          max-w-[80%] rounded-lg px-4 py-2
          ${isUser 
            ? 'bg-blue-600 text-white' 
            : isError 
              ? 'bg-red-100 text-red-800 border border-red-300'
              : 'bg-gray-100 text-gray-900'
          }
        `}
      >
        {isPending ? (
          <div 
            className="flex items-center gap-2"
            role="status"
            aria-label="Carregando resposta"
          >
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
            <span className="sr-only">Gerando resposta...</span>
          </div>
        ) : (
          <p className="whitespace-pre-wrap">{content}</p>
        )}
        
        <time
          dateTime={new Date(timestamp).toISOString()}
          className="text-xs opacity-70 mt-1 block"
        >
          {new Date(timestamp).toLocaleTimeString('pt-BR')}
        </time>
      </div>
    </motion.div>
  );
}
```

### 9.3. Benefícios Esperados

- Percepção de velocidade melhorada (optimistic UI)
- Aplicação acessível para usuários com deficiência
- Melhor experiência offline

---

## 10. Documentação e Onboarding (BAIXA PRIORIDADE)

### 10.1. Problema Identificado

Documentação existe mas pode ser melhorada com:
- README interativo com exemplos
- FAQ de erros comuns
- Guia de contribuição

### 10.2. Solução Proposta

#### 10.2.1. Expandir README principal

```markdown
# MARIA - Assistente de IA de Escritório

[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-blue)]()
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

Assistente de IA local para automação de tarefas de escritório: criação de planilhas Excel, documentos Word, organização de arquivos e consultas inteligentes.

## 🚀 Quick Start

### Pré-requisitos

- Python 3.12+
- Ollama com modelo Qwen3.5:4b (ou llama-server com Qwen2.5-Omni-3B)

### Instalação Rápida

```bash
# Clonar repositório
git clone https://github.com/seu-org/maria.git
cd maria/backend

# Script de setup automático
chmod +x ../scripts/setup.sh
../scripts/setup.sh

# Iniciar
python main.py
```

### Primeiros Comandos

```
Olá! Sou a MARIA. Como posso ajudar?

> Crie uma planilha de controle financeiro com colunas Data, Descrição, Valor e Categoria
→ Planilha criada: arquivos_gerados/controle_financeiro.xlsx

> Faça uma carta de apresentação para vaga de desenvolvedor
→ Documento criado: arquivos_gerados/carta_apresentacao.docx

> Liste os arquivos na pasta documentos
→ Arquivos encontrados:
   - relatorio_jan.txt (12 KB)
   - ata_reuniao.docx (8 KB)
```

## 📋 Comandos Disponíveis

| Categoria | Exemplo | Descrição |
|-----------|---------|-----------|
| Planilhas | "Crie planilha de vendas" | Cria Excel com colunas |
| Documentos | "Faça um relatório mensal" | Gera Word com conteúdo |
| Arquivos | "O que tem na pasta docs?" | Lista arquivos |
| Consultas | "Resuma o arquivo notas.txt" | Lê e resume documentos |

## ❓ FAQ

### Erro: "Modelo não encontrado"
Execute: `ollama pull qwen3.5:4b`

### Erro: "Timeout na requisição"
Aumente timeout: `export OLLAMA_TIMEOUT=300`

### Memória crescendo continuamente
Execute com GC explícito ou reinicie a sessão.

## 🤝 Contribuindo

1. Fork o projeto
2. Crie branch para feature (`git checkout -b feature/AmazingFeature`)
3. Commit mudanças (`git commit -m 'Add AmazingFeature'`)
4. Push para branch (`git push origin feature/AmazingFeature`)
5. Abra Pull Request

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
```

#### 10.2.2. Criar CHANGELOG automatizado

```markdown
# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/),
e este projeto adere ao [Semantic Versioning](https://semver.org/).

## [Não Lançado]

### Adicionado
- Monitoramento de memória no benchmark (#42)
- Validação rigorosa de tool call arguments (#38)
- Rate limiting no endpoint HTTP bridge (#35)

### Mudado
- Prompt de sistema com exemplos few-shot para melhor accuracy (#40)

### Corrigido
- Vazamento de sessões HTTP em execuções longas (#44)

## [1.0.0] - 2025-12-01

### Adicionado
- Sistema de tool calling com 5 ferramentas
- Benchmark automatizado de tarefas
- Interface terminal interativa
- Persistência de sessões
- Suporte a streaming de respostas

### Técnico
- Backend Python síncrono com Flask
- Frontend Tauri v2 + React
- Modelos: Ollama Qwen3.5, llama-server Qwen2.5-Omni
```

### 10.3. Benefícios Esperados

- Redução de tempo de onboarding de novos desenvolvedores
- Menos issues repetitivas no GitHub
- Documentação viva e atualizada

---

## Resumo de Prioridades

| Prioridade | Área | Esforço | Impacto |
|------------|------|---------|---------|
| 🔴 CRÍTICO | Gerenciamento de Memória | Baixo | Alto |
| 🔴 ALTA | Confiabilidade Tool Calling | Médio | Alto |
| 🔴 ALTA | Observabilidade | Médio | Alto |
| 🔴 ALTA | Segurança | Médio | Crítico |
| 🟡 MÉDIA | Manual de Redação | Médio | Médio |
| 🟡 MÉDIA | OCR/Visão | Alto | Médio |
| 🟡 MÉDIA | Arquitetura | Alto | Médio |
| 🟡 MÉDIA | Deploy/Configuração | Baixo | Médio |
| 🟢 BAIXA | Frontend Tauri | Médio | Baixo |
| 🟢 BAIXA | Documentação | Baixo | Baixo |

---

## Próximos Passos Recomendados

1. **Semana 1**: Implementar gerenciamento de memória (Seção 1) e segurança (Seção 4)
2. **Semana 2**: Adicionar retry com backoff e validação de tool calls (Seção 2)
3. **Semana 3**: Implementar observabilidade e métricas (Seção 3)
4. **Semana 4**: Integrar manual de redação (Seção 5) e começar OCR (Seção 6)

---

**Documento elaborado com base na análise do código-fonte em Dezembro 2025.**
