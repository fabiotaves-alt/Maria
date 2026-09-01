# Decisões de Implementação — Banco de Dados (maria.db)

**Versão:** v4.1.1  
**Última atualização:** 2026-08-31  
**Status:** ✅ Unificado e Padronizado (Python + Rust / SQLite FTS5)  
**Local do Banco:** `shared/maria.db` (compartilhado entre backend Python e frontend Tauri)  
**Schema Central:** `shared/schema.sql`

---

## 1. Resumo da Arquitetura de Dados

O banco de dados SQLite compartilhado segue um contrato unificado e rigorosamente compartilhado entre o backend Python (`sqlite3`) e a camada nativa do frontend Tauri em Rust (`rusqlite`):

### 1.1. Concorrência e Integridade
- **Modo WAL (`PRAGMA journal_mode = WAL`)**: Ativado tanto em `connection.py` (Python) quanto no `main.rs` (Rust), permitindo múltiplas leituras concorrentes simultâneas com operações de escrita.
- **Chaves Estrangeiras (`PRAGMA foreign_keys = ON`)**: Habilitado em ambos os lados, com `ON DELETE CASCADE` garantindo que a exclusão de conversas remova atomicamente as mensagens associadas.
- **Tolerância a Concorrência (`PRAGMA busy_timeout = 5000`)**: Configurado para que transações aguardem até 5 segundos em caso de contenção de escrita de threads simultâneas, evitando falhas de `sqlite3.OperationalError: database is locked`.
- **Thread-Safety no Backend**: Em `backend/database/connection.py`, a conexão utiliza `check_same_thread=False` e é instanciada com proteção de `threading.Lock()` (*double-checked locking*), suportando com segurança o modelo multi-thread do servidor Flask (`threaded=True`).
- **Nomenclatura Canônica**: Padronizada integralmente em português do Brasil no singular/plural semântico.

---

## 2. Schema das Tabelas Unificadas

Definido no arquivo canônico [`shared/schema.sql`](../shared/schema.sql):

| Tabela | Tipo | Colunas Principais | Propósito |
|--------|------|--------------------|-----------|
| `conversas` | Relacional | `id`, `titulo`, `criado_em`, `atualizado_em` | Sessões de chat do usuário |
| `mensagens` | Relacional | `id`, `conversa_id`, `role`, `conteudo`, `anexos`, `criado_em` | Histórico de mensagens (FK -> `conversas` com `ON DELETE CASCADE`) |
| `memoria` | Relacional | `id`, `fato`, `categoria`, `relevancia`, `fonte`, `criado_em` | Fatos persistentes aprendidos sobre o usuário (RAG pessoal) |
| `arquivos_indexados` | Relacional | `id`, `caminho`, `tipo`, `tamanho_bytes`, `hash_checksum`, `indexado_em`, `ultima_leitura` | Metadados e integridade de documentos e áudios processados |
| `automacoes` | Relacional | `id`, `nome`, `descricao`, `gatilho`, `acao`, `parametros`, `passos_json`, `ativo`, `execucoes_count`, `criado_em`, `ultima_execucao` | Rotinas de automação agendadas ou disparadas por gatilhos |
| `configuracoes` | Relacional | `chave`, `valor`, `descricao`, `atualizado_em` | Preferências de sistema, temas, áudio e modelos |
| `manual_redacao_fts` | Virtual (FTS5) | `tipo_documento` (unindexed), `secao`, `conteudo` | Tabela FTS5 para busca textual das normas do Manual de Redação da Presidência da República (tokenizer `unicode61 remove_diacritics 2`) |

---

## 3. Arquivos Centrais de Persistência

| Arquivo | Tecnologia | Responsabilidade |
|---------|------------|------------------|
| `shared/schema.sql` | SQL (DDL) | Schema canônico de referência do monorepo |
| `backend/database/connection.py` | Python (`sqlite3`) | Conexão singleton thread-safe compartilhada com PRAGMAs e locks |
| `backend/database/schema.py` | Python | Inicializador DDL e gerenciamento de migrations/tabelas |
| `backend/database/ingest_manual_redacao.py` | Python | Script idempotente de ingestão dos 255 trechos no FTS5 |
| `frontend-tauri/src-tauri/src/main.rs` | Rust (`rusqlite`) | Conexão nativa e comandos IPC do Tauri compartilhando `shared/maria.db` |

---

> **Histórico:** A implementação original da era JavaFX (DAOs em Java com JDBC) foi arquivada em [`docs/arquivo/IMPLEMENTACAO_DAO.md`](arquivo/IMPLEMENTACAO_DAO.md).

