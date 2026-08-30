# Implementação de DAOs e Integração com Banco de Dados

## ✅ Implementado na Fase 3 (Schema Unificado)

### 1. Camada de Persistência (DAOs)

Foram criados e padronizados os arquivos Java no pacote `com.tristar.maria.dao`:

| Arquivo | Responsabilidade |
|---------|-----------------|
| `DatabaseManager.java` | Singleton para gerenciar conexão JDBC SQLite com `shared/maria.db`, aplicar WAL/FKs e inicializar o schema unificado |
| `ConversaDAO.java` | CRUD de sessões (`conversas`) e mensagens (`mensagens`) com `ON DELETE CASCADE` |
| `MemoriaDAO.java` | CRUD de fatos persistentes do usuário (`memoria` para RAG) |
| `AutomacaoDAO.java` | CRUD de automações (`automacoes`) |
| `ConfiguracaoDAO.java` | Gerenciamento de configurações chave-valor (`configuracoes`) |

### 2. Schema Unificado do Banco de Dados

O `DatabaseManager` e o backend Python compartilham exatamente o mesmo schema definido em `shared/schema.sql`:

```sql
- conversas (id, titulo, criado_em, atualizado_em)
- mensagens (id, conversa_id, role, conteudo, anexos, criado_em) [FK -> conversas ON DELETE CASCADE]
- memoria (id, fato, categoria, relevancia, fonte, criado_em)
- arquivos_indexados (id, caminho, tipo, tamanho_bytes, hash_checksum, indexado_em, ultima_leitura)
- automacoes (id, nome, descricao, gatilho, acao, parametros, passos_json, ativo, execucoes_count, criado_em, ultima_execucao)
- configuracoes (chave PK, valor, descricao, atualizado_em)
```

### 3. Integração no App.java

- Inicialização do banco de dados no `start()` com resolução dinâmica de caminho
- Detecção automática de ambiente Python por sistema operacional (Windows/Linux/macOS)
- Fechamento da conexão no `encerrar()`
- Tratamento resiliente de erros

### 4. Controllers Integrados

#### ConversarController
- Gerencia sessão ativa via `conversaDAO.obterOuCriarConversaAtiva()`
- Persiste mensagens de usuário e respostas da assistente
- Suporta limpeza de histórico com remoção em cascata

#### MemoriaController
- Carrega memórias do banco ao iniciar (`fato`, `categoria`)
- Adiciona novos fatos persistentes via `MemoriaDAO`
- Busca por termos e exclusão de memórias

#### AutomacoesController
- Lista todas as automações com status ativo/inativo
- Criação e toggle de execução

### 5. Testes Unitários

O arquivo `DatabaseManagerTest.java` valida:
- Inicialização do banco e conexão ativa
- CRUD de memórias com filtro e busca por termos
- CRUD de configurações com upsert e deleção
- CRUD de automações com toggle de estado ativo
- Cascata `ON DELETE CASCADE` entre conversas e mensagens

## Nota sobre Modelos LLM

- **Modelo padrão em produção:** `qwen2.5-omni-3b` via **llama-server** (`backend/core/llama_client.py`).
- **Modelo legado/opcional:** `qwen3.5:4b` via **Ollama** (`backend/core/ollama_client.py`) — mantido apenas como caminho alternativo.
- **Fonte da verdade:** `backend/core/config.py` — as constantes `LLAMA_MODEL` e `OLLAMA_MODEL` controlam o roteamento.
