# MARIA — Assistente de IA Pessoal 100% Local

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo. Usa LLM local via **Ollama** para conversa, function calling (criação/edição de planilhas Excel e documentos Word) e leitura de arquivos.

---

## Arquitetura

Monorepo com dois processos independentes que se comunicam via IPC (stdin/stdout, protocolo JSON por linha):

```
┌─────────────────────────┐   JSON-lines    ┌──────────────────────────┐
│  Frontend JavaFX        │ ◄────────────► │  Backend Python          │
│  (com.tristar.maria)    │   stdin/stdout │  (Ollama + ferramentas)  │
│  Java 21 / Maven        │                │  Python 3.11+            │
└─────────────────────────┘                └──────────┬───────────────┘
                                                      │ HTTP localhost
                                                ┌─────▼─────┐
                                                │  Ollama   │
                                                └───────────┘
```

- **Frontend**: interface JavaFX com 8 abas (Conversar, Arquivos, Análise de Dados, Visão, Voz, Memória, Automações, Configurações), tema claro/escuro e bridge para o backend.
- **Backend**: cliente Ollama com histórico de contexto, prompt de sistema em pt-BR anti-alucinação, function calling com confirmação, geração de arquivos reais e persistência de sessões.

## Estrutura de Pastas

```
maria/
├── README.md                  ← este arquivo
├── requirements.txt           ← dependências Python consolidadas
├── .venv/                     ← ambiente virtual Python (raiz do monorepo)
├── docs/                      ← documentação técnica e relatórios
│   ├── ARQUITETURA_REAL_SISTEMA.md
│   ├── INTEGRACAO_FRONTEND.md
│   ├── RELATORIO_ACOMPANHAMENTO.md
│   └── RELATORIO_ESTADO_ATUAL.md
├── shared/                    ← banco SQLite compartilhado (maria.db)
├── backend/
│   ├── main.py                ← CLI interativa + modo --bridge (frontend)
│   ├── ui_terminal.py         ← interface de terminal legada
│   ├── core/                  ← ollama_client, chat_session, tools_schema,
│   │                            excel_handler, word_handler, file_utils,
│   │                            session_storage, tool_chaining, config
│   ├── database/              ← connection.py (SQLite singleton)
│   ├── tests/test_maria.py    ← suíte de testes unitários
│   └── benchmark/             ← sistema de benchmark live (opcional)
└── frontend/
    ├── pom.xml                ← Maven (Java 21, JavaFX 21)
    └── src/main/
        ├── java/com/tristar/maria/
        │   ├── App.java       ← ponto de entrada JavaFX
        │   ├── bridge/        ← PythonBridgeService, Requisicao, Resposta
        │   └── ui/            ← MainController + controllers das 8 abas
        └── resources/com/tristar/maria/
            ├── *.fxml         ← views das abas
            └── theme-*.css    ← temas escuro/claro
```

## Pré-requisitos

| Requisito | Versão | Observação |
|-----------|--------|------------|
| Python | 3.11+ | venv na raiz (`.venv/`) |
| Ollama | atual | [ollama.com](https://ollama.com) |
| Modelo LLM | ver `OLLAMA_MODEL` em `backend/core/config.py` | ex.: `ollama pull qwen2.5:7b` |
| JDK | 21 | OpenJDK/Temurin |
| Maven | 3.9+ | ou wrapper da IDE |

### Instalação

```bash
# 1. Ambiente Python (na raiz do monorepo)
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 2. Ollama + modelo
ollama serve
ollama pull qwen2.5:7b
```

## Como Executar

### Frontend JavaFX (interface gráfica)

```bash
cd frontend
mvn javafx:run
```

O frontend inicia automaticamente o processo Python (`../.venv/Scripts/python.exe ../backend/main.py --bridge`) e valida a conexão com handshake ping/pong.

### Backend via CLI (terminal)

```bash
.venv\Scripts\python.exe backend\main.py
```

Comandos da CLI: `ajuda`, `limpar`, `retomar` (retoma sessão salva), `sair`.

### Backend modo bridge (usado pelo frontend)

```bash
.venv\Scripts\python.exe backend\main.py --bridge
```

Protocolo: `{"id": "1", "comando": "ping"}` → `{"id": "1", "status": "ok", "dados": "pong", "mensagemErro": null}`. Comandos suportados: `ping`, `chat`, `encerrar`. Detalhes em [docs/INTEGRACAO_FRONTEND.md](docs/INTEGRACAO_FRONTEND.md).

### Testes

```bash
.venv\Scripts\python.exe -m pytest backend/tests/test_maria.py -v
```

### Configuração

Todas as configurações ficam centralizadas em [`backend/core/config.py`](backend/core/config.py) e podem ser sobrescritas por variáveis de ambiente ou arquivo `backend/.env` (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`, pastas de saída etc.). **Nunca versione chaves de API no `.env`.**

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [docs/INTEGRACAO_FRONTEND.md](docs/INTEGRACAO_FRONTEND.md) | Protocolo bridge Java↔Python |
| [docs/PENDENCIAS_INTERFACE.md](docs/PENDENCIAS_INTERFACE.md) | Elementos mockados da interface + como adicionar o avatar |
| [docs/RELATORIO_ESTADO_ATUAL.md](docs/RELATORIO_ESTADO_ATUAL.md) | Estado atual, bugs e roadmap |
| [backend/README.md](backend/README.md) | Documentação completa do backend/CLI |

## Licença

Projeto em desenvolvimento. Todos os direitos reservados.
