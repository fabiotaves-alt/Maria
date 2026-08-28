# MARIA — Assistente de IA Pessoal 100% Local

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo. Usa LLM local via **Ollama** para conversa, function calling (criação/edição de planilhas Excel e documentos Word) e leitura de arquivos.

---

## Arquitetura

Monorepo com dois processos independentes que se comunicam via IPC (stdin/stdout, protocolo JSON por linha):

```
┌─────────────────────────┐   JSON-lines    ┌──────────────────────────┐
│  Frontend JavaFX        │ ◄────────────► │  Backend Python          │
│  (com.tristar.maria)    │   stdin/stdout │  (Ollama + ferramentas)  │
│  Java 17 / Maven        │                │  Python 3.11+            │
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
    ├── pom.xml                ← Maven (Java 17, JavaFX 17)
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
| Modelo LLM | ver `OLLAMA_MODEL` em `backend/core/config.py` | ex.: `ollama pull qwen3.5:4b` |
| JDK | 21 | OpenJDK/Temurin |
| Maven | 3.9+ | ou wrapper da IDE |

### Instalação

```bash
# 1. Ambiente Python (na raiz do monorepo)
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 2. Ollama + modelo
ollama serve
ollama pull qwen3.5:4b
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

### Documentos Ativos

| Documento | Conteúdo | Versão |
|-----------|----------|--------|
| [docs/ARQUITETURA_SISTEMA.md](docs/ARQUITETURA_SISTEMA.md) | Arquitetura real do sistema | v3.1.0 |
| [docs/GUIA_DESENVOLVIMENTO.md](docs/GUIA_DESENVOLVIMENTO.md) | Guia prático para desenvolvedores | Fase 2 |
| [docs/GUIA_DESENVOLVIMENTO_FASE3.md](docs/GUIA_DESENVOLVIMENTO_FASE3.md) | Guia da Fase 3: Integração e Ferramentas | v3.0.0 |
| [docs/RELATORIO_ESTADO_ATUAL.md](docs/RELATORIO_ESTADO_ATUAL.md) | Estado atual, bugs e roadmap | v3.1.0 |
| [docs/RELATORIO_IMPLEMENTACAO_FASE3.md](docs/RELATORIO_IMPLEMENTACAO_FASE3.md) | **Implementações da Fase 3 (DAOs, Bridge, DB)** | **v3.1.0** |
| [docs/PENDENCIAS_INTERFACE.md](docs/PENDENCIAS_INTERFACE.md) | Elementos mockados da interface + avatar | v2.13.0 |
| [docs/DECISOES_BANCO_DADOS.md](docs/DECISOES_BANCO_DADOS.md) | Decisões sobre schema do banco | v3.1.0 |
| [docs/INSTALACAO_WHISPER.md](docs/INSTALACAO_WHISPER.md) | Instalação e uso do whisper.cpp | v3.0.0 |
| [docs/IMPLEMENTACAO_DAO.md](docs/IMPLEMENTACAO_DAO.md) | **Guia técnico dos DAOs Java** | **v3.1.0** |

### Documentos Legados

Documentos obsoletos foram movidos para [`docs/archive/`](docs/archive/):
- `ARQUITETURA_REAL_SISTEMA.md` (estado anterior à v2.11.0)
- `RELATORIO_ACOMPANHAMENTO.md` (acompanhamento Fase 0)

### Backend

| Documento | Conteúdo | Versão |
|-----------|----------|--------|
| [backend/README.md](backend/README.md) | Documentação completa do backend/CLI | v3.1.0 |
| [backend/CHANGELOG.md](backend/CHANGELOG.md) | Histórico de mudanças do backend | v3.1.0 |
| [backend/database/schema.py](backend/database/schema.py) | Schema SQLite com 6 tabelas | v3.1.0 |

### Frontend

| Documento | Conteúdo | Versão |
|-----------|----------|--------|
| [frontend/pom.xml](frontend/pom.xml) | Configuração Maven (Java 17, JavaFX, JUnit) | v3.1.0 |

## Licença

Projeto em desenvolvimento. Todos os direitos reservados.
