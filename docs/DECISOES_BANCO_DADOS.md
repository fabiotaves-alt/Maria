# Decisões Pendentes — Banco de Dados (maria.db)

**Status:** 🔒 Bloqueado para implementação — aguardando respostas abaixo.
**Contexto:** `backend/database/connection.py` existe (singleton SQLite, WAL configurado), mas não há schema e `init_db()` nunca é chamado. As 6 tabelas conceituais (`conversas`, `mensagens`, `memoria`, `arquivos_indexados`, `automacoes`, `configuracoes`) aparecem apenas em documentação histórica (`docs/archive/RELATORIO_ACOMPANHAMENTO.md`), sem DDL nem uso real no código atual.

## Perguntas a responder antes de criar `backend/database/schema.py`

### 1. Quem usa o banco?
O SQLite compartilhado (`shared/maria.db`) é para uso pelo **frontend Java**, pelo **backend Python**, ou ambos simultaneamente? Se ambos, como evitar escrita concorrente? (WAL já está ativo em `connection.py`, mas falta definir dono de cada tabela.)

### 2. As 6 tabelas ainda refletem a necessidade real?
Ou o escopo mudou desde a documentação histórica? Ex.: `automacoes` é funcionalidade futura sem requisito hoje; `voz` idem.

### 3. Unificação com "Memória entre sessões"?
A tabela `memoria` (fatos persistentes sobre o usuário) se sobrepõe à questão já registrada em `backend/docs/guia_fase_2.md`, seção 3.1 ("Memória entre sessões"). As duas iniciativas devem ser unificadas em uma única definição de schema?

### 4. O que alimenta `arquivos_indexados`?
A tabela pressupõe indexação dos arquivos gerados. Isso já existe parcialmente (`listar_arquivos` lê pastas permitidas) ou exige nova funcionalidade de indexação?

## Ação recomendada

Responder às 4 perguntas e só então abrir tarefa de implementação de `backend/database/schema.py` + chamada de `init_db()` no startup do backend (`main.py`). **Não criar tabelas especulativas.**
