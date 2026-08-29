# Arquitetura do Sistema — MARIA

**Versão:** v4.0.0  
**Última atualização:** 2026-08-29  
**Status da Fase:** 🔄 Em Migração para v4.0 (Tauri + React) - Frontend JavaFX é legado

Este documento descreve a arquitetura atual do sistema MARIA. O projeto está em transição ativa da arquitetura JavaFX (v3.x - legado) para uma arquitetura moderna com **Tauri v2 + React + TypeScript**.

---

## 1. Visão Geral

**MARIA** ("Modelo Assistente de Raciocínio e Inferência Aumentada") é uma assistente de IA de escritório que roda **100% localmente**, sem depender de internet após a instalação do modelo. 

### Arquitetura Atual (v4.0 - Tauri + React)

O sistema consiste em:

- **Frontend**: Tauri v2 + React + TypeScript (interface visual moderna com navegação por abas)
- **Backend**: Python 3.11+ (LLM local via llama.cpp, lógica de negócio, ferramentas)
- **Banco de Dados**: SQLite compartilhado (`shared/maria.db`) com schema canônico em `shared/schema.sql`

### Diagrama de Arquitetura (v4.0)

```
┌─────────────────────────────────────┐   HTTP/Tauri IPC   ┌──────────────────────────────────┐
│  Frontend Tauri + React             │ ◄────────────────► │  Backend Python                  │
│  (React + TypeScript + Tailwind)    │    localhost:8081  │  (llama.cpp + ferramentas)       │
│  Tauri v2 / Rust                    │                    │  Python 3.11+                    │
│                                     │                    │                                  │
│  • App.tsx (entry point)            │                    │  • main.py (--bridge / CLI)      │
│  • TopBar (barra superior nativa)   │                    │  • llama_client.py               │
│  • Sidebar (navegação)              │◄──────────────────►│  • tools_schema.py               │
│  • ChatPanel (chat)                 │                    │  • excel_handler.py              │
│  • CenterStage (hero)               │                    │  • word_handler.py               │
│  • Hooks (useTheme, useMariaBridge) │                    │  • session_storage.py            │
│                                     │                    │  • database/schema.py            │
└────────────┬────────────────────────┘                    └────────────────┬─────────────────┘
             │ Rust IPC (sidecar)                                          │ HTTP localhost
             ▼                                                       ┌─────▼──────┐
┌─────────────────────────────────────┐                                │  llama-    │
│  SQLite (shared/maria.db)           │◄───────────────────────────────│  server    │
│  - conversas                        │     Shared Database            │  :8080     │
│  - mensagens (ON DELETE CASCADE)    │       (WAL mode)               └────────────┘
│  - memoria                          │
│  - arquivos_indexados               │
│  - automacoes                       │
│  - configuracoes                    │
└─────────────────────────────────────┘
```

### Nota sobre JavaFX (Legado v3.x)

> ⚠️ **Atenção:** O frontend JavaFX foi descontinuado e está sendo mantido apenas como referência histórica. Todo o desenvolvimento ativo está focado na nova arquitetura Tauri + React. Consulte [`docs/arquivo/FRONTEND_JAVAFX_LEGADO.md`](arquivo/FRONTEND_JAVAFX_LEGADO.md) para documentação completa do frontend JavaFX.

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
