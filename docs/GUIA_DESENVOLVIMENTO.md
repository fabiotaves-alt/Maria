# Guia de Desenvolvimento e Referencial Teórico — Projeto MARIA

**Versão:** 2.0 (fusão canônica)
**Data:** 2026-09-08
**Status:** ✅ Aprovado para uso — documento único e canônico
**Substitui:** `docs/GUIA_DESENVOLVIMENTO.md` (v1.1.1) e a proposta avulsa "Referencial Teórico e Guia de Desenvolvimento" (v1.0)
**Aplicabilidade:** Todos os desenvolvedores do projeto MARIA (backend, frontend, infraestrutura)

---

## 0. Como usar este documento

Este é o documento canônico único de desenvolvimento do MARIA. Toda mudança/proposta deve ser validada contra ele antes do merge (checklist na Seção 8). Ele combina:

- **Parte I** — guia prático (ambiente, execução, arquitetura atual, estrutura de pastas): "como o projeto funciona hoje".
- **Parte II** — referencial teórico (fundamentação acadêmica/indústria, diretrizes de código, padrões): "por que fazemos assim e o que ainda vamos adotar".

**Regra de precedência:** em caso de conflito entre este documento e o estado real do código, o código e o `CHANGELOG.md` prevalecem — abra uma issue para corrigir o documento. Em caso de conflito entre este documento e o `plano_mestre_v5.md`, o plano mestre prevalece para o que está em execução ativa (fases B0–B7).

---

# PARTE I — Guia Prático

## 1. Configuração do Ambiente

| Requisito | Versão | Observação |
|-----------|--------|------------|
| Python | 3.11+ | `.venv/` na raiz; `uv` como gerenciador (ver `pyproject.toml`) |
| Node.js + npm | 18 LTS+ | Frontend Tauri/React |
| Rust | estável | `rustup`, compilação da camada nativa Tauri |
| llama.cpp / llama-server | atual | Servidor LLM local (produção) |
| Modelo LLM (produção) | `qwen2.5-omni-3b` | via `llama-server`, porta 8080 |

```bash
git clone <repo-url>
cd maria
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv sync --extra dev
cd frontend-tauri && npm install && cd ..
```

Variáveis de ambiente opcionais (`.env` na raiz): `LLAMA_BASE_URL`, `LLAMA_MODEL`, `LLAMA_NUM_CTX`, `MARIA_ENV=development` (libera CORS do Vite dev server).

## 2. Execução

```bash
# Backend — CLI interativo
uv run python backend/main.py

# Backend — bridge HTTP (usado pelo frontend Tauri em dev, porta 8081)
uv run python backend/main.py --bridge-http

# Backend — bridge stdin/stdout (sidecar em produção)
uv run python backend/main.py --bridge

# Frontend — dev
cd frontend-tauri && npm run tauri dev

# Frontend — build de produção
cd frontend-tauri/src-tauri && python build_sidecar.py
cd .. && npm run tauri build
```

## 3. Testes

```bash
uv run pytest                                            # suíte completa (backend)
uv run python backend/tests/validate_llama_server.py     # smoke-test ao vivo (porta 8080)
cd frontend-tauri && npm run build                        # type-check + build Vite
cd frontend-tauri && npm test                              # Vitest
cd frontend-tauri/src-tauri && cargo test                  # Rust
```

## 4. Estado da Migração e Fontes Vivas de Verdade

> **Leia isto antes de assumir que qualquer estrutura de pastas ou padrão de validação descrito na Parte II já existe no código.** O projeto está em migração ativa para arquitetura hexagonal (plano `plano_mestre_v5.md`, fases B0–B7). A Parte II descreve tanto o que **já está implementado** quanto o que é **arquitetura-alvo ainda não construída** — cada afirmação é marcada explicitamente.

Fontes vivas de verdade, em ordem de precedência para "o que existe agora":

1. `CHANGELOG.md` — o que foi de fato implementado, versão a versão.
2. `docs/ARQUITETURA_SISTEMA.md` — estado por camada, atualizado a cada versão MINOR/MAJOR.
3. `plano_mestre_v5.md` (e execuções `execucao_*.md`) — o que está em progresso e o que é meta futura.
4. Este documento — diretrizes e fundamentação; não é fonte de estado de implementação.

## 5. Arquitetura — Estado Atual (backend)

Estrutura real hoje (Python 3.11+, Flask + flask-cors, llama-server via HTTP, SQLite com FTS5), após a migração hexagonal (Fases B0–B1):

```
backend/
├── main.py                    ← entry point fino (CLI / --bridge / --bridge-http)
├── bridge/                    ← transporte (servidores.py) + protocolo (comandos.py)
├── domain/                    ← entidades/validação pura: chat_session.py, confirmacao.py, validacao_tool_call.py
├── interfaces/                ← ports (typing.Protocol): client_protocol.py, interfaces.py, session_storage.py
├── application/               ← casos de uso: maria_controller.py, tool_chaining.py, router.py, manual_redacao.py
├── infrastructure/            ← implementações: llm/llama_client.py, tools/ (tools_schema, excel_handler, ...)
├── core/                      ← config.py + system_prompt.txt + re-exports de compatibilidade (transição)
├── ui_terminal.py
├── database/                  ← connection.py, schema.py, migrations/
├── tests/                     ← suíte pytest (269 testes)
└── benchmarks/maria_bench/    ← framework de avaliação de tool calling
```

**Nota:** a migração hexagonal (Fases B0–B1) já está aplicada no tronco — `domain/`, `interfaces/`, `application/` e `infrastructure/` são a fonte real; `core/` mantém apenas `config.py`, `system_prompt.txt` e re-exports de compatibilidade (esvaziamento definitivo na Fase B7a). Ver `execucao_b0_6_b1_re_exports.md`.

## 6. Arquitetura — Frontend (Tauri v2 + React)

Sem alterações desta revisão: Tauri v2 (Rust) + React 18 + TypeScript + Tailwind + Framer Motion + Zustand, comunicação HTTP local (porta 8081, dev) ou stdin/stdout sidecar (produção). Detalhes completos em `docs/ARQUITETURA_SISTEMA.md`.

## 7. Backlog Ativo

Consulte `plano_mestre_v5.md` como fonte única do backlog técnico priorizado (fases B0–B7, incluindo B4.5/B4.6 — intent classification e roteamento de tradução, ambas planejadas como fases próprias após B4).

---

# PARTE II — Referencial Teórico

## 1. Princípios Fundamentais

| Princípio | Descrição |
|---|---|
| Local-first | Dados e processamento rodam 100% localmente, sem dependência de nuvem |
| Defesa em profundidade | Múltiplas camadas de validação, fallback e correção |
| Arquitetura hexagonal | Separação entre domain, application e infrastructure — **arquitetura-alvo (Fase B1)**, não estado atual |
| Design para falhas | O modelo LLM é um componente imperfeito; o sistema compensa suas limitações |
| Validação determinística | Saídas do modelo são validadas por regras fora do LLM |
| Evolução incremental | Mudanças são testadas empiricamente antes de produção |

## 2. Arquitetura de Software

### 2.1 Arquitetura Hexagonal (Ports & Adapters) — **arquitetura-alvo**

Proposta por Alistair Cockburn (2005): isola a lógica de negócio (`domain`/`application`) de frameworks externos (`infrastructure`), facilitando testes e substituição de implementações.

**Estrutura-alvo** (ver Fase B1 do `plano_mestre_v5.md` para o mapeamento arquivo a arquivo):

```
backend/
├── domain/           # Entidades, value objects — stdlib apenas
├── application/       # Casos de uso, regras de negócio
├── infrastructure/    # Implementações concretas (Flask, SQLite, requests)
├── interfaces/         # Protocols (typing.Protocol) — ports abstratos
```

**Regra de dependência entre camadas** (já formalizada no `plano_mestre_v5.md`, Seção 4 — aplicá-la desde já ao avaliar onde um novo módulo deve ficar, mesmo antes de B1 estar concluído):

```
domain/         → stdlib apenas; ZERO import de application/, infrastructure/, benchmark/
application/    → domain/, interfaces/
interfaces/     → domain/ (tipos), stdlib
infrastructure/ → domain/, interfaces/; NUNCA application/
benchmark/      → somente via interfaces/ (ports públicos)
```

**Validação antes de implementar:**
1. Esta lógica pertence a `domain`, `application` ou `infrastructure`?
2. Estou importando frameworks (Flask, SQLite) em `domain`/`application`?
3. Posso substituir esta implementação por um mock sem alterar o caso de uso?

Referência: COCKBURN, A. *Hexagonal Architecture*. 2005.

### 2.2 Clean Architecture

Extensão da Arquitetura Hexagonal por Robert C. Martin: independência de frameworks, testabilidade, independência de UI/DB/agentes externos.

Referência: MARTIN, R. C. *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall, 2017.

### 2.3 Domain-Driven Design (DDD)

Proposta por Eric Evans (2003): entidades, value objects, aggregates, repositories, com a lógica de negócio no centro do design.

| Conceito DDD | Implementação MARIA | Camada |
|---|---|---|
| Entity | `Conversa`, `Mensagem`, `Memoria`, `Arquivo` (ID único) | `domain/` (alvo) |
| Value Object | `ToolCall`, `ToolResult`, `HealthStatus` (imutáveis, sem ID) | `domain/` (alvo) |
| Aggregate | `Conversa` + `Mensagens` (`ON DELETE CASCADE`) | `domain/` (alvo) |
| Repository | `ConversaRepository`, `MemoriaRepository` | `infrastructure/database` (alvo) |
| **Application Service** | `MariaController` (orquestra ferramentas, sessão, persistência via protocolos injetados) | `application/` (alvo) |

> **Correção aplicada:** `MariaController` é um **Application Service**, não um Domain Service — depende de I/O via `LLMClientProtocol`/`ToolExecutorProtocol` injetados e orquestra casos de uso; Domain Services em DDD estrito são lógica pura sem dependência de infraestrutura. O próprio `plano_mestre_v5.md` já classifica `maria_controller.py` como destino `application/`.

Referências: EVANS, E. *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Addison-Wesley, 2003. VERNON, V. *Implementing Domain-Driven Design*. Addison-Wesley, 2013.

### 2.4 Princípios de Engenharia Aplicados ao MARIA

> Referência completa (genérica, reutilizável fora do MARIA): `docs/PRINCIPIOS_DE_ENGENHARIA_DE_SOFTWARE.md`.
> Esta seção traz apenas a aplicação concreta de cada princípio ao estado real do projeto.

Estes princípios se somam à Arquitetura Hexagonal e ao DDD (Seções 2.1–2.3) como uma camada
de disciplina de código do dia a dia. Quando dois princípios entrarem em tensão (ex.: OCP
pede abstração antecipada, YAGNI pede esperar), a decisão é resolvida por evidência empírica
(frequência real de mudança, dados de benchmark), não por preferência.

| Princípio | Aplicação concreta no MARIA |
|---|---|
| **KISS** | A Task 26 (tradução de planilha) deve ser resolvida com parser JSON corrigido + 1 exemplo de `linhas` no prompt + validação de colunas — não com um classificador de intenção baseado em ML. Isso resolve a maior parte do problema com esforço muito menor. Evoluir para um classificador (Fase B4.5) só se os dados do benchmark mostrarem que a heurística simples falha de forma sistemática. |
| **YAGNI** | Reforça — não substitui — a decisão já registrada (Seção 5.2, Parte II) de manter Pydantic como diretriz proposta, pendente de decisão formal em B6, e não uma adoção antecipada. Da mesma forma, qualquer automação especulativa (ex.: agente auto-atualizável) fica fora do escopo até haver demanda real registrada. |
| **DRY** | Ponte direta com a Oportunidade O1 do `plano_mestre_v5.md`: gerar `system_prompt.txt`, validação (`validacao_tool_call.py`, B0.3) e `response_format` (B6) a partir de uma única fonte (`TOOLS_SCHEMA`/`CAMPOS_OBRIGATORIOS`). Hoje, mudar o nome de uma ferramenta exige tocar em múltiplos arquivos manualmente — isso é o problema que o DRY aponta para corrigir. |
| **SoC** | Fundamenta a própria migração hexagonal (Fase B1): separar `domain/` (regras de negócio, validação de tool call), `application/` (orquestração, `MariaController`) e `infrastructure/` (`llama_client`, `excel_handler`, banco). Não é complexidade especulativa — é resposta a um problema real e já documentado (emaranhado em `core/` causando quebras de importação durante a migração, ver `execucao_etapa_1_2_destravar_suite.md`). |
| **SRP** | **Correção de precisão:** `MariaController` já delega para implementações injetáveis desde a Fase 1 do B1 (`core/interfaces.py`: `LLMClientProtocol`, `ToolExecutorProtocol`, `SessionStorageProtocol`; `maria_controller.py.__init__(cliente=None, tool_executor=None)`) — portanto o DIP já está satisfeito neste ponto. A violação de SRP remanescente é distinta: mesmo com dependências abstraídas, `MariaController` continua sendo o único ponto que muda por múltiplos motivos independentes (fluxo de confirmação, formato de sessão, encadeamento de ferramentas). SRP e DIP são eixos ortogonais — corrigir um não corrige o outro automaticamente. A separação completa (`ToolOrchestrator`, `SessionManager` como classes próprias) é o objetivo da Fase B1, não algo já resolvido. |
| **OCP** | Adicionar uma nova ferramenta hoje exige tocar em `tools_schema.py` e no despacho de execução (`if/elif`). Um Registry Pattern resolveria isso, mas **a decisão de aplicá-lo antecipadamente deve ser justificada por frequência real de adição de ferramentas** (ver histórico de versões no `CHANGELOG.md` como fonte de dado) — não por precaução genérica. Tratar como candidato a avaliar dentro da Fase B1/B4, não como correção obrigatória imediata. |
| **LSP** | Toda implementação de `LLMClientProtocol`/`ToolExecutorProtocol`/`SessionStorageProtocol` (via `typing.Protocol`, tipagem estrutural) deve ser verdadeiramente substituível — mesmas exceções esperadas, mesmos efeitos colaterais, não só a mesma assinatura de método. Isso é especialmente relevante para mocks de teste: um mock que "engana" o tipo mas se comporta de forma incompatível com a implementação real (`LlamaClient`) viola LSP silenciosamente e produz testes que passam sem proteger contra regressão — o próprio `CHANGELOG.md` já registrou esse tipo de problema (mocks que não implementavam `continuar_com_resultado_ferramenta_stream` corretamente). |
| **DIP** | Já em aplicação — `LLMClientProtocol`, `ToolExecutorProtocol`, `SessionStorageProtocol` — desde a Fase 1 do B1. A Fase B2 deve estender o mesmo princípio ao benchmark, forçando-o a depender apenas dessas interfaces (hoje ele importa `_montar_mensagens_com_reforco`, símbolo privado — ver Lei de Demeter abaixo). |
| **Lei de Demeter** | O benchmark (`maria_runner.py`) importar diretamente `_montar_mensagens_com_reforco` (função privada de `llama_client.py`) é uma violação direta: o benchmark não deveria conhecer os detalhes internos do cliente LLM. Correção prevista na Fase B2 do `plano_mestre_v5.md`: expor uma função pública (`montar_mensagens_com_reforco`) como fachada. |
| **EAFP vs. LBYL** | Já aplicado corretamente: a correção do TOCTOU em `file_utils.py`/`session_storage.py` (`os.makedirs(..., exist_ok=True)` + tratamento de exceção, ver `CHANGELOG.md` v2.8.0) segue EAFP. Manter esse padrão em todo novo handler de arquivo/pasta. |
| **Regra do Escoteiro** | Ao implementar `tool_call_json_parser.py` (B0.2), aproveitar para remover os imports mortos de `tool_call_textual_parser.py` (B0.6) no mesmo ciclo — já é o que o plano mestre prevê na ordem B0.2 → B0.6, e deve continuar sendo prática padrão em qualquer PR que toque em código adjacente a débito técnico conhecido. |
| **Otimização Prematura** | O roteamento entre modelos (3B vs. 7B, Fase B4.6/roadmap de `router.py`) não deve ser implementado antes de o benchmark (B3, com SQLite) produzir dados mostrando que o 3B é insuficiente para uma fração relevante de tarefas. Até lá, a fase permanece de baixa prioridade e sem cronograma fixo. |

## 3. Sistemas de IA com LLMs

### 3.1 Agentic Workflows

O LLM é um componente do sistema, não o sistema inteiro: parser, validador e executor de ferramentas envolvem o modelo. Padrão já aplicado no MARIA via `tool_chaining.py`.

- Validação determinística: saídas do modelo validadas por regras fora do LLM (`tools_schema.py::validar_argumentos_obrigatorios`, hoje; `validacao_tool_call.py`, planejado em B0.3).
- Fallback hierárquico: hoje, delta nativo → parser textual → correção dirigida (`tool_chaining.py::validar_e_corrigir_tool_call_stream`).
- Roteamento por intenção (classificador heurístico → embedding → LLM catch-all): **planejado, Fase B4.5** — ainda não implementado.

### 3.2 Tool Calling sem Suporte Nativo

Quando o modelo não suporta tool calling nativo (caso do Qwen2.5-Omni), o sistema implementa parsing textual com fallbacks múltiplos. Padrão real hoje (ver `llama_client.py::_resolver_tool_call_final`): delta nativo → parser JSON/posicional → fallback textual → pedir correção ao modelo (nunca "revise sua resposta" genérico — sempre aponta o campo específico, ver 3.4).

### 3.3 Intent Classification e Entity Extraction — **Planejado, Fase B4.5**

Cascade recomendado pela literatura (Tian Pan, 2026; FutureAGI, 2026): keyword filter (<1ms) → embedding router (16–100ms) → classificador fine-tuned (50–200ms) → LLM catch-all (1–5s). Ainda não implementado no MARIA; ver `plano_mestre_v5.md` Fase B4.5 para escopo, dependências (B0.3) e critérios de aceite.

**Roteamento para modelo especializado de tradução (NLLB-200):** também **planejado, Fase B4.6**, independente de B4.5.

### 3.4 Self-Correction e Validação

Correção deve apontar o campo exato, não instrução genérica:

```python
# ✅ Correto: aponta campo exato (padrão real do projeto)
erro = "Campo 'linhas': esperado lista de listas, recebeu string"

# ❌ Incorreto: instrução genérica
erro = "Sua resposta tem erros. Revise e corrija."
```

Implementação real de referência: `tool_chaining.py::validar_e_corrigir_tool_call_stream`.

### 3.5 Small Language Models (SLMs) — Limitações Conhecidas

| Limitação | Mitigação | Status no MARIA |
|---|---|---|
| Case sensitivity em chaves de controle | Normalizar apenas chaves de controle (`ferramenta`, `nome_arquivo`, etc.) | Implementado parcialmente; **não normalizar chaves internas de `linhas`** — normalizar tudo (incluindo `linhas[*]`) é o próprio BUG-4 identificado, não uma mitigação (ver `senior_longcat_tools.md`, `plano_mestre_v5.md` B0.2/B0.3) |
| Tradução de idiomas distantes | Roteamento para modelo especializado (NLLB-200) | Planejado, B4.6 |
| JSON mal-formado | Parser com repair + retry | Implementado (`tool_call_textual_parser.py`, em substituição por `tool_call_json_parser.py` em B0) |
| Campos ausentes | Validação + pedir regeneração | Implementado (`validar_argumentos_obrigatorios`) |

## 4. Banco de Dados e Persistência

### 4.1 SQLite — Configurações Obrigatórias (já implementado)

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
```
Referência de implementação real: `backend/database/connection.py`.

### 4.2 Migrations de Schema (já implementado)

Padrão: scripts SQL numerados (`NNN_nome.sql`), aplicados atomicamente (`BEGIN`/`COMMIT`), com tabela `schema_migrations`. Referência de implementação real: `backend/database/migration_runner.py`, `backend/database/migrations/001_initial.sql`.

Regras: nunca renomear colunas (apenas `ADD COLUMN` com `DEFAULT`); transação por migration; idempotência (`CREATE TABLE IF NOT EXISTS`).

## 5. Segurança

### 5.1 Defesa em Profundidade (já implementado)

| Camada | Implementação real |
|---|---|
| Autenticação | Token de 64 hex chars por sessão, escrita atômica (`.tmp` + `os.replace()`) |
| CORS | Restrito a `tauri://localhost` em produção; `MARIA_ENV=development` libera Vite |
| Path traversal | `resolver_caminho_permitido()` com whitelist de pastas |
| PATH hijacking | `WHISPER_ALLOWED_DIR` valida binários externos via `shutil.which()` |
| Thread-safety | SQLite `check_same_thread=False`, `busy_timeout=5000` |
| Bind local | Flask escuta apenas em `127.0.0.1` |

### 5.2 Validação de Entrada — **Pydantic: diretriz proposta, não adotada**

> **Status:** proposta, pendente de decisão formal (Fase B6 do `plano_mestre_v5.md`). O padrão real de validação hoje é manual: `ValueError` + `tools_schema.py::validar_argumentos_obrigatorios`. Uma revisão sênior anterior (`senior_arquitetura_hexagonal.md`, DEFEITO-2) recomendou explicitamente adiar a adoção de Pydantic até a base hexagonal (B1–B5) estar consolidada. **Não implementar Pydantic fora do escopo formal de B6 sem decisão registrada.**

Exemplo do padrão **real e atual**:

```python
# Padrão hoje em tools_schema.py — manter até decisão formal sobre Pydantic
def validar_argumentos_obrigatorios(ferramenta: str, argumentos: dict) -> None:
    campos = CAMPOS_OBRIGATORIOS.get(ferramenta, [])
    for campo in campos:
        valor = argumentos.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            raise ValueError(f"Campo obrigatório ausente ou vazio: '{campo}'")
```

Exemplo de como ficaria **se e quando B6 aprovar Pydantic** (ilustrativo, não vinculante):

```python
# Proposta — NÃO implementar sem decisão formal em B6
from pydantic import BaseModel, Field, ValidationError

class CriarPlanilhaPayload(BaseModel):
    nome_arquivo: str = Field(min_length=1, max_length=255)
    colunas: list[str] = Field(min_length=1)
    linhas: list[list] | None = None
```

## 6. Testes e Qualidade

### 6.1 Pirâmide de Testes

Distribuição-alvo (não medida formalmente até o momento — `pytest-cov` ainda não executado; ver notas recorrentes "Cobertura não re-medida" no `CHANGELOG.md`):

| Tipo | Meta de cobertura |
|---|---|
| Unitários | `domain/` + `application/` ≥ 85% (meta, a validar quando `pytest-cov` for executado como critério de aceite de fase) |
| Integração | `tool_chaining`, `manual_redacao` |
| E2E (benchmark) | `tool_correct`, `args_correct`, `dados_arquivo_validos` |

### 6.2 Benchmark de Tool Calling

Sistema próprio de avaliação (`backend/benchmarks/maria_bench/` — movido em B2; referências antigas a `backend/benchmark/` são legadas). O número de tasks **não deve ser fixado neste documento** — consulte `backend/benchmarks/maria_bench/tasks/` como fonte viva (a Task 26 está sendo redesenhada e novas tasks 29–32 estão previstas na Fase B4.5).

| Métrica | Definição | Meta |
|---|---|---|
| `tool_correct` | % de tool calls com ferramenta correta | ≥90% |
| `args_correct` | % de argumentos corretos (schema, tipos) | ≥85% |
| `keyword_match` | % de keywords esperadas na resposta | ≥80% |
| `language_compliance_rate` | % de respostas em português | ≥95% |
| `dados_arquivo_validos` | % de arquivos com dados corretos | ≥90% |

## 7. Padrões de Código

### 7.1 Python — PEP 8 + type hints + docstrings

```python
def criar_planilha(
    nome_arquivo: str,
    colunas: list[str],
    linhas: list[list] | None = None
) -> str:
    """
    Cria uma planilha Excel com os dados fornecidos.

    Args:
        nome_arquivo: Nome do arquivo (sem extensão)
        colunas: Lista de nomes de colunas
        linhas: Dados tabulares (opcional)

    Returns:
        Caminho absoluto do arquivo criado

    Raises:
        ValueError: Se colunas estiver vazio
    """
    if not colunas:
        raise ValueError("colunas não pode ser vazio")
```

### 7.2 TypeScript/React — ESLint + Prettier, componentes funcionais com hooks

```typescript
interface ChatPanelProps {
  mensagens: Mensagem[];
  onEnviarMensagem: (texto: string) => void;
}

export function ChatPanel({ mensagens, onEnviarMensagem }: ChatPanelProps) {
  const [texto, setTexto] = useState('');
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (texto.trim()) { onEnviarMensagem(texto); setTexto(''); }
  };
  return <form onSubmit={handleSubmit}>{/* ... */}</form>;
}
```

### 7.3 Rust (Tauri) — `cargo fmt` + `cargo clippy` sem warnings

```rust
// Sem "pub" nos comandos Tauri v2 — evita E0255 (macros __cmd__ duplicadas)
#[tauri::command]
async fn criar_planilha(
    nome_arquivo: String,
    colunas: Vec<String>,
    linhas: Option<Vec<Vec<serde_json::Value>>>,
) -> Result<String, String> {
    if colunas.is_empty() {
        return Err("colunas não pode ser vazio".to_string());
    }
    Ok(caminho_arquivo)
}
```

## 8. Checklist de Validação de Mudanças

### 8.1 Antes de Implementar
- [ ] A mudança está alinhada com os princípios do projeto (Seção 1)?
- [ ] A lógica pertence a `domain`, `application` ou `infrastructure` (mesmo que a pasta-alvo ainda não exista fisicamente)?
- [ ] Não importa Flask/SQLite/requests em código que seria `domain`/`application`?
- [ ] É possível substituir a implementação por um mock sem alterar o caso de uso?
- [ ] Há testes unitários previstos para esta feature?
- [ ] Se envolve validação de entrada/saída: usa o padrão atual (`validar_argumentos_obrigatorios`), não Pydantic, salvo decisão formal em B6?

### 8.2 Após Implementar
- [ ] Todos os testes unitários passam?
- [ ] Validação de entrada e de saída (LLM) implementadas com mensagem de erro específica por campo?
- [ ] `CHANGELOG.md` atualizado?
- [ ] Mensagens de commit em português, claras e objetivas?

### 8.3 Antes de Fazer Merge
- [ ] Suíte completa passa (`uv run pytest`)?
- [ ] Benchmark de tool calling não regrediu?
- [ ] Frontend compila sem erros (`npm run build`)?
- [ ] Rust compila sem warnings (`cargo clippy`)?
- [ ] Mudança está de acordo com a fase ativa do `plano_mestre_v5.md` (não adianta nem contradiz fases futuras sem decisão registrada)?

## 9. Governança deste Documento

- **Gatilho de revisão obrigatória:** ao fechar cada fase B do `plano_mestre_v5.md` (mover item de "planejado" para "implementado" nesta Parte II) e a cada versão MAJOR/MINOR do `CHANGELOG.md`.
- **Aprovação de mudanças:** decisões que alterem diretrizes desta Parte II (ex.: adoção de Pydantic em B6) exigem registro explícito equivalente às decisões D1–D6 do `plano_mestre_v5.md`, não bastando um PR isolado.
- **Precedência:** ver Seção 0.
- Mudanças em `docs/PRINCIPIOS_DE_ENGENHARIA_DE_SOFTWARE.md` (documento genérico) que afetem
  exemplos já referenciados na Seção 2.4 devem disparar revisão da tabela de aplicação ao MARIA.

---

## 10. Referências Bibliográficas

> Citações verificadas nesta revisão estão marcadas `[verificado]`. As demais não foram checadas individualmente nesta rodada — checar pontualmente antes de citar em contexto formal.

- COCKBURN, A. *Hexagonal Architecture*. 2005. Disponível em: https://alistair.cockburn.us/hexagonal-architecture/.
- MARTIN, R. C. *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall, 2017.
- MARTIN, R. C. *Clean Code: A Handbook of Agile Software Craftsmanship*. Prentice Hall, 2008.
- MARTIN, R. C. *Agile Software Development: Principles, Patterns, and Practices*. Prentice Hall, 2002.
- EVANS, E. *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Addison-Wesley, 2003.
- VERNON, V. *Implementing Domain-Driven Design*. Addison-Wesley, 2013.
- BECK, K. *Test-Driven Development: By Example*. Addison-Wesley, 2002.
- KLEPPMANN, M.; RICCOMINI, C. *Designing Data-Intensive Applications*. 2nd ed. O'Reilly Media, 2026. **[verificado — correção: coautoria de Chris Riccomini e ano 2026, não "2024" como constava na versão anterior]**
- RICHARDS, M.; FORD, N. *Fundamentals of Software Architecture: A Modern Engineering Approach*. 2nd ed. O'Reilly Media, 2025. **[verificado — correção: subtítulo correto é "A Modern Engineering Approach" (2ª ed.), não "An Engineering Approach" (título da 1ª ed., 2020)]**
- KLEPPMANN, M.; WIGGINS, A.; VAN HARDENBERG, P.; MCGRANAGHAN, M. *Local-first software: you own your data, in spite of the cloud*. Ink & Switch / ACM SIGPLAN Onward!, 2019. **[correção: substitui a referência fabricada "NEWTON, C. Building Local-First Software. Local-First Software Collective, 2025", que não foi localizada em nenhuma fonte — este é o artigo seminal real sobre local-first software]**
- FOWLER, M. *Single Responsibility Principle*. martinfowler.com. Disponível em: https://martinfowler.com/bliki/SingleResponsibilityPrinciple.html.
- OWASP. *Input Validation Cheat Sheet*. Disponível em: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html.
- PYTHON SOFTWARE FOUNDATION. *PEP 8 — Style Guide for Python Code*. Disponível em: https://peps.python.org/pep-0008/.
- PYTHON SOFTWARE FOUNDATION. *PEP 484 — Type Hints*. Disponível em: https://peps.python.org/pep-0484/.
- SQLITE DOCUMENTATION. *Query Planner*. Disponível em: https://www.sqlite.org/queryplanner.html.
- TIAN PAN. *The Intent Classification Layer Most Agent Routers Skip*. 2026. Disponível em: https://tianpan.co/blog/2026/04/16/intent-classification-agent-routers.
- FUTUREAGI. *Intent Classification LLM Pipeline: 2026 Best Practices*. 2026. Disponível em: https://futureagi.com/blog/intent-classification-llm-pipeline-2026/.
- APP-LAB. *Entity Extraction with LLMs: spaCy, GLiNER, and LLM Structured Output*. 2026. Disponível em: https://app-lab.ai/blog/entity-extraction-llm/.
- MAKEEV, I. *Designing AI Systems Around LLM Limitations*. 2026. Disponível em: https://makeev.dev/notes/designing-ai-systems-around-llm-limitations/.
- NYGARD, M. *Release It!: Design and Deploy Production-Ready Software*. 3rd ed. Pragmatic Bookshelf, 2025.

> As demais referências da proposta original (RICHARDS/FORD já corrigido acima; CRISPIN/GREGORY *Agile Testing*; ANDERSON *Defense in Depth*; SHOSTACK *Threat Modeling*; MCGRAW *Software Security*; edições específicas de artigos de blog de 2026 citados na Parte II §3) não foram reverificadas individualmente nesta rodada — sinalizar para checagem caso venham a ser citadas em material formal/externo.

---

*Fim do documento canônico.*
