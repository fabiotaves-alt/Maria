# Decisões de Implementação — Banco de Dados (maria.db)

**Status:** ✅ Unificado e Padronizado — v3.1.0  
**Data Implementação:** 2026-08-28  
**Local do Banco:** `shared/maria.db` (compartilhado backend/frontend)  
**Schema Central:** `shared/schema.sql`

## Resumo da Implementação

O banco de dados SQLite compartilhado segue um contrato unificado e idêntico em Python e Java:

### 1. Concorrência e Integridade
- **Modo WAL (`PRAGMA journal_mode = WAL`)**: Ativado tanto em `connection.py` (Python) quanto em `DatabaseManager.java` (Java) para suportar leituras concorrentes sem bloqueio de escrita.
- **Chaves Estrangeiras (`PRAGMA foreign_keys = ON`)**: Habilitado em ambos os lados, com `ON DELETE CASCADE` garantindo que a exclusão de conversas remova automaticamente as mensagens associadas.
- **Nomenclatura**: Padronizada integralmente em português do Brasil (`conversas`, `mensagens`, `memoria`, `arquivos_indexados`, `automacoes`, `configuracoes`).

### 2. Schema das 6 Tabelas Unificadas

| Tabela | Colunas | Propósito |
|--------|---------|-----------|
| `conversas` | `id`, `titulo`, `criado_em`, `atualizado_em` | Sessões de bate-papo |
| `mensagens` | `id`, `conversa_id`, `role`, `conteudo`, `anexos`, `criado_em` | Mensagens trocadas (FK -> conversas ON DELETE CASCADE) |
| `memoria` | `id`, `fato`, `categoria`, `relevancia`, `fonte`, `criado_em` | Fatos persistentes do usuário para RAG |
| `arquivos_indexados` | `id`, `caminho`, `tipo`, `tamanho_bytes`, `hash_checksum`, `indexado_em`, `ultima_leitura` | Metadados de documentos e áudios |
| `automacoes` | `id`, `nome`, `descricao`, `gatilho`, `acao`, `parametros`, `passos_json`, `ativo`, `execucoes_count`, `criado_em`, `ultima_execucao` | Fluxos de automação agendados ou disparados por eventos |
| `configuracoes` | `chave`, `valor`, `descricao`, `atualizado_em` | Preferências de sistema, temas e modelos |

## Arquivos Centrais

| Arquivo | Descrição |
|---------|-----------|
| `shared/schema.sql` | DDL canônico de referência |
| `backend/database/schema.py` | Inicializador DDL em Python |
| `backend/database/connection.py` | Conexão SQLite Python com WAL e FKs |
| `frontend/src/main/java/com/tristar/maria/dao/DatabaseManager.java` | Gerenciador JDBC Java com inicialização do schema |
| `frontend/src/main/java/com/tristar/maria/dao/*.java` | Camada DAO (Conversa, Memoria, Automacao, Configuracao) |

## Nota sobre Modelos LLM

- **Modelo padrão em produção:** `qwen2.5-omni-3b` via **llama-server** (`backend/core/llama_client.py`).
- **Modelo legado/opcional:** `qwen3.5:4b` via **Ollama** (`backend/core/ollama_client.py`) — mantido apenas como caminho alternativo.
- **Fonte da verdade:** `backend/core/config.py` — as constantes `LLAMA_MODEL` e `OLLAMA_MODEL` controlam o roteamento.
