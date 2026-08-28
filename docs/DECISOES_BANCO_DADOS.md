# Decisões de Implementação — Banco de Dados (maria.db)

**Status:** ✅ Implementado — v3.1.0  
**Data Implementação:** 2026-08-27  
**Local do Banco:** `shared/maria.db` (compartilhado backend/frontend)

## Resumo da Implementação

O banco de dados SQLite compartilhado foi implementado na Fase 3 com as seguintes características:

### 1. Quem usa o banco?
**Ambos** — Backend Python e Frontend Java acessam o mesmo arquivo `shared/maria.db`:
- **Backend Python**: Escreve em `conversas`, `mensagens`, `memoria`, `arquivos_indexados`; lê todas
- **Frontend Java**: Lê/escreve em todas as tabelas via DAOs
- **Controle de Concorrência**: WAL mode ativo em `connection.py` para permitir leituras simultâneas

### 2. Schema das 6 Tabelas Implementadas

| Tabela | Colunas Principais | Responsável |
|--------|-------------------|-------------|
| `conversas` | id, sessao_id, titulo, data_inicio, data_fim | Ambos |
| `mensagens` | id, conversa_id, role, conteudo, timestamp, anexos | Ambos |
| `memoria` | id, categoria, conteudo, relevancia, data_criacao | Ambos |
| `arquivos_indexados` | id, caminho, tipo, metadata, data_indexacao | Ambos |
| `automacoes` | id, nome, gatilho, acao, parametros, ativo | Ambos |
| `configuracoes` | chave, valor, data_atualizacao | Ambos |

### 3. Unificação com "Memória entre sessões"
✅ **Unificado** — A tabela `memoria` implementa a persistência de fatos sobre o usuário conforme documentação da Fase 2. O frontend acessa via `MemoriaDAO.java`.

### 4. Indexação de Arquivos
✅ **Parcialmente implementado** — `arquivos_indexados` armazena metadados de arquivos processados. A indexação automática é futura.

## Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `backend/database/schema.py` | DDL das 6 tabelas + índices |
| `backend/database/connection.py` | Singleton SQLite com WAL |
| `frontend/src/main/java/com/tristar/maria/dao/DatabaseManager.java` | Singleton JDBC com schema unificado |
| `frontend/src/main/java/com/tristar/maria/dao/ConversaDAO.java` | CRUD conversas |
| `frontend/src/main/java/com/tristar/maria/dao/MemoriaDAO.java` | CRUD memórias |
| `frontend/src/main/java/com/tristar/maria/dao/AutomacaoDAO.java` | CRUD automações |
| `frontend/src/main/java/com/tristar/maria/dao/ConfiguracaoDAO.java` | CRUD configurações |

## Comandos Bridge Relacionados

| Comando | Tabela | Status |
|---------|--------|--------|
| `salvar_memoria` | memoria | ✅ |
| `listar_memoria` | memoria | ✅ |
| `deletar_memoria` | memoria | ✅ |
| `limpar_memorias` | memoria | ✅ |
| `criar_automacao` | automacoes | ✅ |
| `listar_automacoes` | automacoes | ✅ |
| `deletar_automacao` | automacoes | ✅ |
| `toggle_automacao` | automacoes | ✅ |

## Testes

- **Backend**: 86 testes unitários passando
- **Frontend**: 6 testes JUnit no `DatabaseManagerTest`

## Próximas Melhorias

1. Sincronização automática de schema entre backend/frontend ✅ Concluído (v3.1.0)
2. Migração do frontend para usar apenas `shared/maria.db` ✅ Concluído (v3.1.0)
3. Indexação automática de arquivos ao upload
