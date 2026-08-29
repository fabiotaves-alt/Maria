# Arquitetura do Sistema — MARIA

**Versão:** v3.1.0  
**Última atualização:** 2026-08-28  
**Status da Fase:** ✅ Fase 3 Concluída (Integração Backend-Frontend & Schema Unificado)

Este documento descreve a arquitetura real e atual do sistema MARIA, refletindo o modelo LLM configurado (`qwen2.5-omni-3b` via llama-server como padrão em produção; `qwen3.5:4b` via Ollama mantido como caminho legado/opcional) e a estrutura implementada no monorepo. Consulte `backend/core/config.py` como fonte da verdade para configurações de modelo.

---

## 1. Visão Geral

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo. O sistema consiste em dois processos independentes que se comunicam via IPC (stdin/stdout com protocolo JSON-lines) e banco SQLite compartilhado:

- **Frontend**: JavaFX 21 (interface visual com navegação por 8 abas)
- **Backend**: Python 3.11+ (LLM local via Ollama, lógica de negócio, ferramentas)
- **Banco de Dados**: SQLite compartilhado (`shared/maria.db`) com schema canônico em `shared/schema.sql`

### Diagrama de Arquitetura

```
┌─────────────────────────────────────┐   JSON-lines    ┌──────────────────────────────────┐
│  Frontend JavaFX                    │ ◄─────────────► │  Backend Python                  │
│  (com.tristar.maria)                │   stdin/stdout  │  (Ollama + ferramentas)          │
│  Java 21 / JavaFX 21                │                 │  Python 3.11+                    │
│                                     │                 │                                  │
│  • App.java (entry point)           │                 │  • main.py (--bridge / CLI)      │
│  • MainController (navegação)       │                 │  • ollama_client.py              │
│  • ConversarController (chat)       │◄───────────────►│  • tools_schema.py               │
│  • PythonBridgeService (comunicação)│                 │  • excel_handler.py              │
│  • HeroController (tela inicial)    │                 │  • word_handler.py               │
│  • 8 controllers de abas            │                 │  • session_storage.py            │
│  • 5 DAOs (persistência)            │                 │  • database/schema.py            │
└──────────────────┬──────────────────┘                 └────────────────┬─────────────────┘
                   │                                                     │ HTTP localhost
                   │ JDBC (WAL)                                          │
                   ▼                                              ┌──────▼──────┐
┌─────────────────────────────────────┐                           │   Ollama    │
│  SQLite (shared/maria.db)           │◄──────────────────────────┤ qwen3.5:4b (legado)│
│  - conversas                        │     Shared Database       └─────────────┘
│  - mensagens (ON DELETE CASCADE)    │       (WAL mode)
│  - memoria                          │
│  - arquivos_indexados               │
│  - automacoes                       │
│  - configuracoes                    │
└─────────────────────────────────────┘
```

---

## 2. Componentes do Sistema

### 2.1 Frontend (JavaFX)

**Tecnologias:** Java 21, JavaFX 21, Maven, SQLite JDBC, JUnit 5

**Estrutura de Pacotes:** `com.tristar.maria`

#### Componentes Principais

| Classe | Responsabilidade |
|--------|------------------|
| `App.java` | Entry point da aplicação; detecta SO dinamicamente, inicializa banco SQLite, inicia bridge Python |
| `MainController.java` | Controller principal; gerencia navegação das 8 abas, alternância de tema claro/escuro |
| `ConversarController.java` | Painel de chat permanente; envio/recebimento de mensagens via bridge, persistência no banco |
| `HeroController.java` | Tela inicial (hero); cards de funcionalidades, ações rápidas |
| `MenuItemsController.java` | Sidebar de navegação; destaque de aba ativa |
| `PythonBridgeService.java` | Serviço de comunicação com backend Python (stdin/stdout JSON-lines) |
| `BridgeManager.java` | Singleton estático para compartilhar instância da bridge entre controllers |
| `Requisicao.java` / `Resposta.java` | Modelos de dados para protocolo bridge |
| **DAOs (Persistência)** | |
| `DatabaseManager.java` | Singleton JDBC; gerencia conexão com `shared/maria.db`, aplica WAL mode e FKs |
| `ConversaDAO.java` | CRUD de conversas e mensagens com integridade referencial em cascata |
| `MemoriaDAO.java` | CRUD de memórias de longo prazo (RAG) com busca textual e por categoria |
| `AutomacaoDAO.java` | CRUD de automações com toggle ativo/inativo |
| `ConfiguracaoDAO.java` | CRUD de configurações chave-valor com upsert |

#### Estilização (CSS)

| Arquivo | Descrição |
|---------|-----------|
| `theme-dark.css` | Tema escuro: fundo `#0a0a12`, aura e destaques rosa `#e05d8a` / `#f2a2bb` |
| `theme-light.css` | Tema claro: fundo `#f7f3ec`, accent terracota `#c47b54` |

---

## 3. Protocolo de Comunicação (Bridge)

A comunicação entre frontend e backend utiliza um protocolo baseado em JSON-lines via stdin/stdout com 19 comandos mapeados.

---

## 4. Banco de Dados Compartilhado

### Schema Canônico Unificado (6 Tabelas em Português)

Definido no arquivo [`shared/schema.sql`](../shared/schema.sql):

| Tabela | Colunas Principais | Responsável Escrita |
|--------|-------------------|---------------------|
| `conversas` | `id`, `titulo`, `criado_em`, `atualizado_em` | Ambos |
| `mensagens` | `id`, `conversa_id`, `role`, `conteudo`, `anexos`, `criado_em` (FK -> conversas CASCADE) | Ambos |
| `memoria` | `id`, `fato`, `categoria`, `relevancia`, `fonte`, `criado_em` | Ambos |
| `arquivos_indexados` | `id`, `caminho`, `tipo`, `tamanho_bytes`, `hash_checksum`, `indexado_em`, `ultima_leitura` | Ambos |
| `automacoes` | `id`, `nome`, `descricao`, `gatilho`, `acao`, `parametros`, `passos_json`, `ativo`, `execucoes_count`, `criado_em`, `ultima_execucao` | Ambos |
| `configuracoes` | `chave`, `valor`, `descricao`, `atualizado_em` | Ambos |

### Concorrência e Integridade
- **WAL Mode**: Ativado tanto no Python quanto no Java para concorrência de leitura/escrita sem locks.
- **Foreign Keys**: `ON DELETE CASCADE` configurado para mensagens vinculadas a conversas.

---

## 5. Estado Atual por Camada

| Camada | Estado | Observações |
|--------|--------|-------------|
| Backend core (Ollama, tools) | ✅ Funcional | MVP Fase 2 completo |
| Backend CLI | ✅ Funcional | `main.py` modo CLI |
| Backend Bridge | ✅ 19 comandos | Todos mapeados e testados |
| Backend Database | ✅ Schema unificado | 6 tabelas + índices + WAL |
| Bridge Java | ✅ Funcional | `PythonBridgeService` + `BridgeManager` |
| Frontend navegação | ✅ Funcional | 8 abas implementadas |
| Frontend chat | ✅ Funcional | Painel permanente integrado ao banco |
| Frontend DAOs | ✅ 5 classes | Persistência unificada com `shared/maria.db` |
| Frontend design | ✅ Implementado | Tema escuro com efeitos rosa e transições |
| Testes Backend | ✅ 86/86 | pytest passando em 5.6s |
| Testes Frontend | ✅ 8/8 | JUnit 5 passando |

---

## Nota sobre Modelos LLM

- **Modelo padrão em produção:** `qwen2.5-omni-3b` via **llama-server** (`backend/core/llama_client.py`).
- **Modelo legado/opcional:** `qwen3.5:4b` via **Ollama** (`backend/core/ollama_client.py`) — mantido apenas como caminho alternativo.
- **Fonte da verdade:** `backend/core/config.py` — as constantes `LLAMA_MODEL` e `OLLAMA_MODEL` controlam o roteamento.
