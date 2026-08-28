# Arquitetura do Sistema — MARIA

**Versão:** v3.1.0  
**Última atualização:** 2026-08-27  
**Status da Fase:** ✅ Fase 3 Concluída (Integração Backend-Frontend Completa)

Este documento descreve a arquitetura real e atual do sistema MARIA, refletindo o modelo LLM configurado (`qwen3.5:4b`) e a estrutura implementada no monorepo.

---

## 1. Visão Geral

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo. O sistema consiste em dois processos independentes que se comunicam via IPC (stdin/stdout com protocolo JSON-lines):

- **Frontend**: JavaFX (interface visual com navegação por 8 abas)
- **Backend**: Python (LLM local via Ollama, lógica de negócio, ferramentas)
- **Banco de Dados**: SQLite compartilhado (`shared/maria.db`)

### Diagrama de Arquitetura

```
┌─────────────────────────────────────┐   JSON-lines    ┌──────────────────────────────────┐
│  Frontend JavaFX                    │ ◄────────────► │  Backend Python                  │
│  (com.tristar.maria)                │   stdin/stdout │  (Ollama + ferramentas)          │
│  Java 17 / Maven                    │                │  Python 3.11+                    │
│                                     │                │                                  │
│  • App.java (entry point)           │                │  • main.py (--bridge / CLI)      │
│  • MainController (navegação)       │                │  • ollama_client.py              │
│  • ConversarController (chat)       │◄──────────────►│  • tools_schema.py               │
│  • PythonBridgeService (comunicação)│                │  • excel_handler.py              │
│  • HeroController (tela inicial)    │                │  • word_handler.py               │
│  • 8 controllers de abas            │                │  • session_storage.py            │
│  • 5 DAOs (persistência)            │                │  • database/schema.py            │
└─────────────────────────────────────┘                └──────────┬───────────────────────┘
         │                                                        │ HTTP localhost
         │ JDBC                                                   │
         ▼                                                 ┌──────▼──────┐
┌─────────────────────┐                                    │   Ollama    │
│  SQLite (maria.db)  │◄──────────────────────────────────►│ qwen3.5:4b  │
│  - conversas        │     Shared Database (WAL mode)     └─────────────┘
│  - mensagens        │
│  - memoria          │
│  - arquivos_indexados
│  - automacoes       │
│  - configuracoes    │
└─────────────────────┘
```

---

## 2. Componentes do Sistema

### 2.1 Frontend (JavaFX)

**Tecnologias:** Java 17, JavaFX 21, Maven, SQLite JDBC

**Estrutura de Pacotes:** `com.tristar.maria`

#### Componentes Principais

| Classe | Responsabilidade |
|--------|------------------|
| `App.java` | Entry point da aplicação; carrega `main-view.fxml`, inicia bridge, gerencia ciclo de vida |
| `MainController.java` | Controller principal; gerencia navegação das 8 abas, alternância de tema, injeção de controllers |
| `ConversarController.java` | Painel de chat permanente; envio/recebimento de mensagens via bridge, persistência no banco |
| `HeroController.java` | Tela inicial (hero); cards de funcionalidades, ações rápidas |
| `MenuItemsController.java` | Sidebar de navegação; destaque de aba ativa |
| `PythonBridgeService.java` | Serviço de comunicação com backend Python (stdin/stdout JSON-lines) |
| `BridgeManager.java` | Singleton estático para compartilhar instância da bridge entre controllers |
| `Requisicao.java` / `Resposta.java` | Modelos de dados para protocolo bridge |
| **DAOs (Persistência)** | |
| `DatabaseManager.java` | Singleton JDBC; cria tabelas, gerencia conexões |
| `ConversaDAO.java` | CRUD de conversas e mensagens |
| `MemoriaDAO.java` | CRUD de memórias com busca por categoria/termo |
| `AutomacaoDAO.java` | CRUD de automações com toggle ativo/inativo |
| `ConfiguracaoDAO.java` | CRUD de configurações chave-valor |

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
| `main.py` | Entry point; modo CLI interativo ou modo `--bridge` para frontend (19 comandos) |
| `ui_terminal.py` | Interface de terminal legada (loop de conversa CLI) |
| `core/ollama_client.py` | Cliente HTTP para Ollama; envio de mensagens, tool calling, streaming |
| `core/tools_schema.py` | Definição de tools (criar_planilha, editar_planilha, criar_documento, etc.) |
| `core/excel_handler.py` | Geração e edição de planilhas Excel (.xlsx) |
| `core/word_handler.py` | Geração e edição de documentos Word (.docx) |
| `core/file_utils.py` | Utilitários de leitura/escrita de arquivos |
| `core/session_storage.py` | Persistência de sessões de conversa (JSON em `sessoes_salvas/`) |
| `core/tool_chaining.py` | Orquestração de múltiplas ferramentas em sequência |
| `core/config.py` | Configurações centralizadas (modelo, timeout, parâmetros de geração) |
| `database/connection.py` | Singleton de conexão SQLite (WAL mode) |
| `database/schema.py` | DDL das 6 tabelas + índices + seed de configurações padrão |
| `tests/test_maria.py` | Suíte de testes unitários (86 testes passando) |

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

### Comandos Suportados (19 Total)

| # | Comando | Descrição | Payload (dados) | Resposta | Versão |
|---|---------|-----------|-----------------|----------|--------|
| 1 | `ping` | Handshake/health check | `null` | `"pong"` | v2.12.0 |
| 2 | `chat` | Enviar mensagem para o LLM | `{ "mensagem": "...", "historico": [...] }` | `{ "resposta": "...", "pensamento": "..." }` | v2.12.0 |
| 3 | `encerrar` | Encerrar processo backend | `null` | `"encerrado"` | v2.12.0 |
| 4 | `status` | Status do sistema | `null` | `{ "cpu": "...", "ram": "..." }` | v2.13.0 |
| 5 | `listar_arquivos` | Listar arquivos em pasta | `{ "pasta": "..." }` | `[ { "nome": "...", "tipo": "..." } ]` | v2.13.0 |
| 6 | `upload_arquivo` | Upload de arquivo | `{ "caminho": "...", "conteudo": "..." }` | `{ "sucesso": true }` | v2.13.0 |
| 7 | `transcrever_audio` | Transcrição de áudio | `{ "caminho": "..." }` | `{ "texto": "..." }` | v2.13.0 |
| 8 | `salvar_memoria` | Salvar memória | `{ "fato": "...", "categoria": "..." }` | `"memória salva"` | v3.0.0 |
| 9 | `listar_memoria` | Listar memórias | `null` | `[ { "fato": "...", "categoria": "..." } ]` | v3.0.0 |
| 10 | `deletar_memoria` | Deletar memória por ID | `{ "id": 1 }` | `"memória deletada"` | v3.1.0 |
| 11 | `limpar_memorias` | Limpar todas memórias | `null` | `"memórias limpas"` | v3.1.0 |
| 12 | `criar_automacao` | Criar automação | `{ "nome": "...", "passos": [...] }` | `"automação criada"` | v3.0.0 |
| 13 | `listar_automacoes` | Listar automações | `null` | `[ { "id": 1, "nome": "...", "ativa": true } ]` | v3.1.0 |
| 14 | `deletar_automacao` | Deletar automação | `{ "id": 1 }` | `"automação deletada"` | v3.1.0 |
| 15 | `toggle_automacao` | Ativar/desativar automação | `{ "id": 1 }` | `{ "ativa": true }` | v3.1.0 |
| 16 | `limpar_conversa` | Limpar conversa atual | `null` | `"conversa limpa"` | v2.13.0 |
| 17 | `exportar_conversa` | Exportar conversa | `{ "formato": "pdf" }` | `{ "caminho": "..." }` | v2.13.0 |
| 18 | `listar_sessoes` | Listar sessões salvas | `null` | `[ { "id": "...", "titulo": "..." } ]` | v2.13.0 |
| 19 | `carregar_sessao` | Carregar sessão | `{ "id": "..." }` | `{ "historico": [...] }` | v2.13.0 |

### Fluxo de Inicialização

1. Frontend inicia processo Python: `python backend/main.py --bridge`
2. Frontend envia `ping` para validar conexão
3. Backend responde `pong`
4. Bridge estabelecida; comandos podem ser enviados
5. Backend inicializa banco de dados (`init_db()`)

---

## 4. Banco de Dados Compartilhado

### Schema (6 Tabelas)

| Tabela | Colunas Principais | Responsável Escrita |
|--------|-------------------|---------------------|
| `conversas` | id, titulo, criado_em, atualizado_em | Backend |
| `mensagens` | id, conversa_id, role, conteudo, anexos, criado_em | Backend |
| `memoria` | id, fato, categoria, relevancia, fonte, criado_em | Backend |
| `arquivos_indexados` | id, caminho, tipo, tamanho_bytes, hash_checksum, indexado_em | Backend |
| `automacoes` | id, nome, descricao, passos_json, gatilho, ativo, execucoes_count | Ambos |
| `configuracoes` | chave, valor, descricao, atualizado_em | Ambos |

### Controle de Concorrência

- **WAL Mode**: Ativado em `connection.py` para permitir leituras simultâneas
- **Índices**: Criados automaticamente para performance (conversa_id, categoria, etc.)

---

## 5. Estrutura de Pastas (Monorepo)

```
maria/
├── README.md                      ← documentação geral
├── requirements.txt               ← dependências Python
├── .venv/                         ← ambiente virtual Python
├── docs/                          ← documentação técnica
│   ├── ARQUITETURA_SISTEMA.md     ← este arquivo (ATIVO - v3.1.0)
│   ├── GUIA_DESENVOLVIMENTO.md    ← guia prático (ATIVO)
│   ├── RELATORIO_ESTADO_ATUAL.md  ← estado atual (ATIVO)
│   ├── PENDENCIAS_INTERFACE.md    ← pendências de UI (ATIVO)
│   ├── DECISOES_BANCO_DADOS.md    ← decisões de DB (IMPLEMENTADO - v3.1.0)
│   ├── RELATORIO_IMPLEMENTACAO_FASE3.md ← relatório Fase 3 (ATIVO)
│   ├── IMPLEMENTACAO_DAO.md       ← guia DAOs (ATIVO)
│   └── archive/                   ← documentos legados
├── shared/                        ← banco SQLite (maria.db)
├── backend/
│   ├── main.py                    ← entry point Python (19 comandos)
│   ├── ui_terminal.py             ← CLI legada
│   ├── core/                      ← módulos principais
│   ├── database/                  ← conexão + schema SQLite
│   │   ├── connection.py          ← singleton WAL
│   │   └── schema.py              ← DDL 6 tabelas
│   ├── tests/                     ← testes unitários (86 testes)
│   ├── CHANGELOG.md               ← histórico de mudanças
│   └── README.md                  ← docs do backend
└── frontend/
    ├── pom.xml                    ← Maven config (Java 17)
    ├── maria.db                   ← banco SQLite (frontend)
    └── src/main/
        ├── java/com/tristar/maria/
        │   ├── App.java           ← entry point JavaFX
        │   ├── bridge/            ← PythonBridgeService, BridgeManager
        │   ├── dao/               ← camada de persistência
        │   │   ├── DatabaseManager.java
        │   │   ├── ConversaDAO.java
        │   │   ├── MemoriaDAO.java
        │   │   ├── AutomacaoDAO.java
        │   │   └── ConfiguracaoDAO.java
        │   └── ui/                ← controllers (8 abas)
        └── resources/com/tristar/maria/
            ├── *.fxml             ← views
            └── theme-*.css        ← temas
```

---

## 6. Estado Atual por Camada

| Camada | Estado | Observações |
|--------|--------|-------------|
| Backend core (Ollama, tools) | ✅ Funcional | MVP Fase 2 completo |
| Backend CLI | ✅ Funcional | `main.py` modo CLI |
| Backend Bridge | ✅ 19 comandos | Todos mapeados e testados |
| Backend Database | ✅ Schema + init | 6 tabelas + índices |
| Bridge Java | ✅ Funcional | `PythonBridgeService` + `BridgeManager` |
| Frontend navegação | ✅ Funcional | 8 abas implementadas |
| Frontend chat | ✅ Funcional | Painel permanente integrado |
| Frontend DAOs | ✅ 5 classes | Persistência completa |
| Frontend design | ✅ Implementado | Elementos mockados listados em `PENDENCIAS_INTERFACE.md` |
| Testes Backend | ✅ 86/86 | unittest passando |
| Testes Frontend | ✅ 6/6 | JUnit 5 passando |

---

## 7. Próximas Evoluções de Arquitetura

1. **Unificação de Banco**: Migrar frontend para usar apenas `shared/maria.db` (atualmente tem cópia em `frontend/maria.db`)
2. **Sincronização de Schema**: Script automático para garantir schema idêntico em ambos os bancos
3. **Speech-to-Text**: Integrar Whisper.cpp para funcionalidade de voz
4. **Exportação PDF**: Implementar comando `exportar_conversa` com geração de PDF
5. **Fine-tuning**: Adapter LoRA para `qwen3.5:4b` com dados em português

---

## 8. Referências

- [Guia de Desenvolvimento](GUIA_DESENVOLVIMENTO.md) — setup, roadmap e contribuição
- [Relatório de Estado Atual](RELATORIO_ESTADO_ATUAL.md) — status detalhado por camada
- [Relatório Fase 3](RELATORIO_IMPLEMENTACAO_FASE3.md) — implementação completa da integração
- [Pendências de Interface](PENDENCIAS_INTERFACE.md) — elementos mockados e como implementar
- [Decisões de Banco de Dados](DECISOES_BANCO_DADOS.md) — implementação concluída v3.1.0
- [Implementação DAO](IMPLEMENTACAO_DAO.md) — guia de DAOs Java

---

**Dúvidas sobre a arquitetura?** Consulte os documentos ativos em `docs/` ou abra uma issue no repositório.
