# Arquitetura do Sistema — MARIA

**Versão:** v2.13.0  
**Última atualização:** 2026-08-24

Este documento descreve a arquitetura real e atual do sistema MARIA, refletindo o modelo LLM configurado (`qwen3.5:4b`) e a estrutura implementada no monorepo.

---

## 1. Visão Geral

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo. O sistema consiste em dois processos independentes que se comunicam via IPC (stdin/stdout com protocolo JSON-lines):

- **Frontend**: JavaFX (interface visual com navegação por 8 abas)
- **Backend**: Python (LLM local via Ollama, lógica de negócio, ferramentas)

### Diagrama de Arquitetura

```
┌─────────────────────────────────────┐   JSON-lines    ┌──────────────────────────────────┐
│  Frontend JavaFX                    │ ◄────────────► │  Backend Python                  │
│  (com.tristar.maria)                │   stdin/stdout │  (Ollama + ferramentas)          │
│  Java 21 / Maven                    │                │  Python 3.11+                    │
│                                     │                │                                  │
│  • App.java (entry point)           │                │  • main.py (--bridge / CLI)      │
│  • MainController (navegação)       │                │  • ollama_client.py              │
│  • ConversarController (chat)       │◄──────────────►│  • tools_schema.py               │
│  • PythonBridgeService (comunicação)│                │  • excel_handler.py              │
│  • HeroController (tela inicial)    │                │  • word_handler.py               │
│  • 8 controllers de abas            │                │  • session_storage.py            │
└─────────────────────────────────────┘                └──────────┬───────────────────────┘
                                                                  │ HTTP localhost
                                                            ┌─────▼──────┐
                                                            │  Ollama    │
                                                            │ qwen3.5:4b │
                                                            └────────────┘
```

---

## 2. Componentes do Sistema

### 2.1 Frontend (JavaFX)

**Tecnologias:** Java 21, JavaFX 21, Maven

**Estrutura de Pacotes:** `com.tristar.maria`

#### Componentes Principais

| Classe | Responsabilidade |
|--------|------------------|
| `App.java` | Entry point da aplicação; carrega `main-view.fxml`, inicia bridge, gerencia ciclo de vida |
| `MainController.java` | Controller principal; gerencia navegação das 8 abas, alternância de tema, injeção de controllers |
| `ConversarController.java` | Painel de chat permanente; envio/recebimento de mensagens via bridge, exibição de bolhas |
| `HeroController.java` | Tela inicial (hero); cards de funcionalidades, ações rápidas |
| `MenuItemsController.java` | Sidebar de navegação; destaque de aba ativa |
| `PythonBridgeService.java` | Serviço de comunicação com backend Python (stdin/stdout JSON-lines) |
| `BridgeManager.java` | Singleton estático para compartilhar instância da bridge entre controllers |
| `Requisicao.java` / `Resposta.java` | Modelos de dados para protocolo bridge |

#### Views (FXML)

| Arquivo | Descrição |
|---------|-----------|
| `main-view.fxml` | Layout principal: topbar, sidebar, coluna central (dinâmica), painel de chat permanente, status bar |
| `conversar-view.fxml` | Painel de chat: área de mensagens, input com botões anexar/voz/enviar |
| `hero-view.fxml` | Tela inicial: título, avatar, cards de funcionalidades, ações rápidas |
| `menu-items.fxml` | Sidebar: logo, 8 botões de navegação, cards de status/recursos |
| `*.fxml` (6 arquivos) | Views das demais abas (Arquivos, Análise de Dados, Visão, Voz, Memória, Automações, Configurações) |

#### Estilização (CSS)

| Arquivo | Descrição |
|---------|-----------|
| `theme-dark.css` | Tema escuro: fundo `#0e0e16`, accent rosa `#e05d8a` |
| `theme-light.css` | Tema claro: fundo `#f7f3ec`, accent terracota `#c47b54` |

---

### 2.2 Backend (Python)

**Tecnologias:** Python 3.11+, Ollama API, SQLite

**Estrutura de Módulos:** `backend.core`, `backend.database`, `backend.tests`

#### Componentes Principais

| Módulo | Responsabilidade |
|--------|------------------|
| `main.py` | Entry point; modo CLI interativo ou modo `--bridge` para frontend |
| `ui_terminal.py` | Interface de terminal legada (loop de conversa CLI) |
| `core/ollama_client.py` | Cliente HTTP para Ollama; envio de mensagens, tool calling, streaming |
| `core/tools_schema.py` | Definição de tools (criar_planilha, editar_planilha, criar_documento, etc.) |
| `core/excel_handler.py` | Geração e edição de planilhas Excel (.xlsx) |
| `core/word_handler.py` | Geração e edição de documentos Word (.docx) |
| `core/file_utils.py` | Utilitários de leitura/escrita de arquivos |
| `core/session_storage.py` | Persistência de sessões de conversa (JSON em `sessoes_salvas/`) |
| `core/tool_chaining.py` | Orquestração de múltiplas ferramentas em sequência |
| `core/config.py` | Configurações centralizadas (modelo, timeout, parâmetros de geração) |
| `database/connection.py` | Singleton de conexão SQLite (maria.db) |
| `tests/test_maria.py` | Suíte de testes unitários (86 testes) |

#### Modelo LLM Configurado

| Parâmetro | Valor |
|-----------|-------|
| Modelo | `qwen3.5:4b` |
| Base URL | `http://localhost:11434` |
| Timeout | 240 segundos |
| Context Window | 2048 tokens |
| Max Predict | 400 tokens |
| Threads | 2 |
| Keep Alive | 30 minutos |

**Configuração via variáveis de ambiente:** Consulte `backend/core/config.py` para overrides.

---

## 3. Protocolo de Comunicação (Bridge)

A comunicação entre frontend e backend utiliza um protocolo simples baseado em JSON-lines via stdin/stdout.

### Formato da Mensagem

**Requisição (Java → Python):**
```json
{
  "id": "1",
  "comando": "ping",
  "dados": null
}
```

**Resposta (Python → Java):**
```json
{
  "id": "1",
  "status": "ok",
  "dados": "pong",
  "mensagemErro": null
}
```

### Comandos Suportados

| Comando | Descrição | Payload (dados) | Resposta |
|---------|-----------|-----------------|----------|
| `ping` | Handshake/health check | `null` | `"pong"` |
| `chat` | Enviar mensagem para o LLM | `{ "mensagem": "...", "historico": [...] }` | `{ "resposta": "...", "pensamento": "..." }` |
| `encerrar` | Encerrar processo backend | `null` | `"encerrado"` |

### Fluxo de Inicialização

1. Frontend inicia processo Python: `python backend/main.py --bridge`
2. Frontend envia `ping` para validar conexão
3. Backend responde `pong`
4. Bridge estabelecida; comandos `chat` podem ser enviados

---

## 4. Estrutura de Pastas (Monorepo)

```
maria/
├── README.md                      ← documentação geral
├── requirements.txt               ← dependências Python
├── .venv/                         ← ambiente virtual Python
├── docs/                          ← documentação técnica
│   ├── ARQUITETURA_SISTEMA.md     ← este arquivo (ATIVO)
│   ├── GUIA_DESENVOLVIMENTO.md    ← guia prático (ATIVO)
│   ├── RELATORIO_ESTADO_ATUAL.md  ← estado atual (ATIVO)
│   ├── PENDENCIAS_INTERFACE.md    ← pendências de UI (ATIVO)
│   ├── DECISOES_BANCO_DADOS.md    ← decisões de DB (ATIVO)
│   └── archive/                   ← documentos legados
├── shared/                        ← banco SQLite (maria.db)
├── backend/
│   ├── main.py                    ← entry point Python
│   ├── ui_terminal.py             ← CLI legada
│   ├── core/                      ← módulos principais
│   ├── database/                  ← conexão SQLite
│   ├── tests/                     ← testes unitários
│   ├── CHANGELOG.md               ← histórico de mudanças
│   └── README.md                  ← docs do backend
└── frontend/
    ├── pom.xml                    ← Maven config
    └── src/main/
        ├── java/com/tristar/maria/
        │   ├── App.java           ← entry point JavaFX
        │   ├── bridge/            ← PythonBridgeService
        │   └── ui/                ← controllers
        └── resources/com/tristar/maria/
            ├── *.fxml             ← views
            └── theme-*.css        ← temas
```

---

## 5. Estado Atual por Camada

| Camada | Estado | Observações |
|--------|--------|-------------|
| Backend core (Ollama, tools) | ✅ Funcional | MVP Fase 2 completo |
| Backend CLI | ✅ Funcional | `main.py` modo CLI |
| Bridge Python | ✅ Funcional | Comandos ping/chat/encerrar |
| Bridge Java | ✅ Funcional | `PythonBridgeService` + `BridgeManager` |
| Frontend navegação | ✅ Funcional | 8 abas implementadas |
| Frontend chat | ✅ Funcional | Painel permanente integrado |
| Frontend design | ✅ Implementado | Elementos mockados listados em `PENDENCIAS_INTERFACE.md` |
| Database schema | ❌ Não iniciado | Aguardando decisões em `DECISOES_BANCO_DADOS.md` |

---

## 6. Próximas Evoluções de Arquitetura

1. **Banco de Dados:** Implementar `database/schema.py` com 6 tabelas e camada DAO no frontend
2. **Comando `status`:** Adicionar à bridge para popular recursos do sistema (CPU/RAM/GPU) em tempo real
3. **Speech-to-Text:** Integrar Whisper.cpp para funcionalidade de voz
4. **Fine-tuning:** Adapter LoRA para `qwen3.5:4b` com dados em português

---

## 7. Referências

- [Guia de Desenvolvimento](GUIA_DESENVOLVIMENTO.md) — setup, roadmap e contribuição
- [Relatório de Estado Atual](RELATORIO_ESTADO_ATUAL.md) — status detalhado por camada
- [Pendências de Interface](PENDENCIAS_INTERFACE.md) — elementos mockados e como implementar
- [Decisões de Banco de Dados](DECISOES_BANCO_DADOS.md) — questões pendentes antes da implementação

---

**Dúvidas sobre a arquitetura?** Consulte os documentos ativos em `docs/` ou abra uma issue no repositório.
