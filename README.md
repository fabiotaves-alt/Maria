# MARIA — Assistente de IA Pessoal 100% Local

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo. Usa LLM local via **Ollama** para conversa, function calling (criação/edição de planilhas Excel e documentos Word) e leitura de arquivos.

---

## Arquitetura

Monorepo com dois processos independentes que se comunicam via IPC (stdin/stdout, protocolo JSON por linha) e banco SQLite compartilhado:

```
┌─────────────────────────┐   JSON-lines    ┌──────────────────────────┐
│  Frontend JavaFX        │ ◄─────────────► │  Backend Python          │
│  (com.tristar.maria)    │   stdin/stdout  │  (Ollama + ferramentas)  │
│  Java 21 / JavaFX 21    │                 │  Python 3.11+            │
└────────────┬────────────┘                 └───────────┬──────────────┘
             │                                          │ HTTP localhost
             │ JDBC (WAL)                         ┌─────▼─────┐
             ▼                                    │  Ollama   │
    ┌─────────────────┐                           └───────────┘
    │ shared/maria.db │ ◄───────────────────────────────┘
    └─────────────────┘
```

- **Frontend**: interface JavaFX 21 com 8 abas (Conversar, Arquivos, Análise de Dados, Visão, Voz, Memória, Automações, Configurações), tema claro/escuro dinâmico e bridge para o backend.
- **Backend**: cliente Ollama com histórico de contexto, prompt de sistema em pt-BR anti-alucinação, function calling com confirmação, geração de arquivos reais e persistência de sessões.
- **Banco de Dados**: SQLite compartilhado em `shared/maria.db` com schema canônico definido em `shared/schema.sql` (WAL mode e integridade referencial com ON DELETE CASCADE).

## Estrutura de Pastas

```
maria/
├── README.md                  ← este arquivo
├── requirements.txt           ← dependências Python consolidadas (inclui psutil)
├── .venv/                     ← ambiente virtual Python (raiz do monorepo)
├── docs/                      ← documentação técnica e relatórios
│   ├── ARQUITETURA_SISTEMA.md
│   ├── DECISOES_BANCO_DADOS.md
│   ├── GUIA_DESENVOLVIMENTO.md
│   ├── GUIA_DESENVOLVIMENTO_FASE3.md
│   ├── IMPLEMENTACAO_DAO.md
│   ├── INSTALACAO_WHISPER.md
│   ├── INTEGRACAO_FRONTEND.md
│   ├── PENDENCIAS_INTERFACE.md
│   ├── RELATORIO_ESTADO_ATUAL.md
│   └── RELATORIO_IMPLEMENTACAO_FASE3.md
├── shared/                    ← banco SQLite compartilhado e DDL
│   ├── schema.sql             ← schema canônico unificado em português
│   └── maria.db               ← arquivo de banco de dados SQLite
├── backend/
│   ├── main.py                ← CLI interativa + modo --bridge (frontend)
│   ├── ui_terminal.py         ← interface de terminal legada
│   ├── core/                  ← ollama_client, chat_session, tools_schema,
│   │                            excel_handler, word_handler, file_utils,
│   │                            session_storage, tool_chaining, config
│   ├── database/              ← connection.py (SQLite singleton) e schema.py
│   ├── tests/test_maria.py    ← suíte de 86 testes unitários (pytest)
│   └── benchmark/             ← sistema de benchmark live (opcional)
└── frontend/
    ├── pom.xml                ← Maven (Java 21, JavaFX 21, SQLite JDBC, JUnit 5)
    └── src/
        ├── main/
        │   ├── java/com/tristar/maria/
        │   │   ├── App.java       ← ponto de entrada JavaFX com detecção de SO
        │   │   ├── bridge/        ← PythonBridgeService, Requisicao, Resposta, BridgeManager
        │   │   ├── dao/           ← DatabaseManager, ConversaDAO, MemoriaDAO, AutomacaoDAO, ConfiguracaoDAO
        │   │   └── ui/            ← MainController + controllers das 8 abas
        │   └── resources/com/tristar/maria/
        │       ├── *.fxml         ← views das abas
        │       └── theme-*.css    ← temas escuro (pink aura) / claro
        └── test/java/com/tristar/maria/
            └── dao/DatabaseManagerTest.java ← 8 testes JUnit 5 de persistência
```

## Pré-requisitos

| Requisito | Versão | Observação |
|-----------|--------|------------|
| Python | 3.11+ | venv na raiz (`.venv/`) |
| Ollama | atual | [ollama.com](https://ollama.com) |
| Modelo LLM | ver `OLLAMA_MODEL` em `backend/core/config.py` | ex.: `ollama pull qwen3.5:4b` |
| JDK | 21 | OpenJDK / Temurin / Oracle JDK 21 |
| Maven | 3.9+ | ou wrapper integrado da IDE |

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

O frontend detecta o SO e inicia automaticamente o processo Python (`backend/main.py --bridge`) e valida a conexão com handshake ping/pong.

### Backend via CLI (terminal)

```bash
.venv\Scripts\python.exe backend\main.py
```

Comandos da CLI: `ajuda`, `limpar`, `retomar` (retoma sessão salva), `sair`.

### Backend modo bridge (usado pelo frontend)

```bash
.venv\Scripts\python.exe backend\main.py --bridge
```

Protocolo: `{"id": "1", "comando": "ping"}` → `{"id": "1", "status": "ok", "dados": "pong", "mensagemErro": null}`. Comandos suportados: `ping`, `chat`, `encerrar`, `salvar_memoria`, `listar_memoria`, `deletar_memoria`, `limpar_memorias`, `criar_automacao`, `listar_automacoes`, `deletar_automacao`, `toggle_automacao`, etc.

### Testes

```bash
# Testes do Backend (86 testes)
.venv\Scripts\python.exe -m pytest backend/tests/test_maria.py -v

# Testes do Frontend (8 testes JUnit 5)
cd frontend
mvn test
```

## Licença

Projeto em desenvolvimento. Todos os direitos reservados.
