# CHANGELOG - Projeto MARIA

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [3.1.1] — Unificação de Schema e Correções Críticas Monorepo

### ✅ Banco de Dados e DAOs
- **Schema SQLite canônico (`shared/schema.sql`)**: 6 tabelas unificadas em português (`conversas`, `mensagens`, `memoria`, `arquivos_indexados`, `automacoes`, `configuracoes`) compartilhadas entre Python e Java em `shared/maria.db`.
- **Integridade referencial**: Ativação de `PRAGMA foreign_keys = ON` com `ON DELETE CASCADE` entre `conversas` e `mensagens`, e `PRAGMA journal_mode = WAL`.
- **DAOs Java padronizados**: `ConversaDAO.java`, `MemoriaDAO.java`, `AutomacaoDAO.java` e `ConfiguracaoDAO.java` totalmente alinhados ao schema unificado.
- **Migração preventiva**: `DatabaseManager.java` com verificação dinâmica de colunas para garantir compatibilidade com bases SQLite existentes.
- **Suíte de Testes JUnit 5**: Expandida para 8 testes (`DatabaseManagerTest.java`), cobrindo conexão, todos os DAOs e exclusão em cascata (100% passando).

### ✅ Configuração, Build e Dependências
- **Consolidação de dependências**: Inclusão de `psutil>=5.9.0` no `requirements.txt` da raiz e exclusão do `backend/requirements.txt` redundante.
- **Detecção de SO no `App.java`**: Resolução automática do executável Python em Windows (`.venv/Scripts/python.exe`), Linux/macOS (`.venv/bin/python`) e `PATH`.
- **Maven / Java 21**: Configuração de `<maven.compiler.release>21</maven.compiler.release>` em `frontend/pom.xml`.
- **Limpeza do Git**: Remoção e desindexação de arquivos de build (`target/`), caches de Python (`__pycache__`) e bancos locais antigos do controle de versão via `.gitignore` aprimorado.

### ✅ Identidade Visual
- **Adaptação do Tema Escuro (`theme-dark.css`)**: Efeito de aura e destaques rosa (`#e05d8a` / `#f2a2bb`) nos botões de ação rápida, botão de envio, menus e avatares, mantendo conformidade com o parser JavaFX Modena.

## [3.1.0] — Fase 3: Integração Backend-Frontend Completa

### ✅ Backend (Python)

- **Comandos Bridge expandidos**: 14 → 20 comandos suportados
  - `deletar_memoria`: Remove memória por ID
  - `limpar_memorias`: Limpa todas as memórias
  - `listar_automacoes`: Lista automações com status ativo/inativo
  - `deletar_automacao`: Remove automação por ID
  - `toggle_automacao`: Ativa/desativa automação
  - `listar_sessoes`: Lista sessões de conversa salvas
  - `carregar_sessao`: Carrega sessão de conversa por ID
  - `salvar_memoria`: Salva nova memória (alias para adicionar_memoria)
  - `listar_memoria`: Lista memórias com filtro opcional
  - `criar_automacao`: Cria nova automação
  - `analisar_arquivo`: Lê documentos e planilhas
  - `analisar_dados`: Gera sumário de planilhas Excel
  - `upload_arquivo`: Copia arquivos para pasta de geração
  - `transcrever_audio`: Transcrição via whisper.cpp
  - `status`: Métricas de CPU, RAM e GPU
  - `exportar_conversa`: Exporta conversa em TXT
  - `limpar_conversa`: Limpa mensagens da sessão atual
  - `chat`: Envio de mensagens com contexto
  - `encerrar`: Finaliza conexão bridge
  - `ping`: Handshake de conectividade
- **Schema SQLite unificado**: 6 tabelas em `shared/maria.db`
  - `conversas`, `mensagens`, `memoria`, `arquivos_indexados`, `automacoes`, `configuracoes`
- **Inicialização automática**: `database/schema.py` cria tabelas no startup
- **Testes**: 86 testes unitários passando

### ✅ Frontend (JavaFX)

- **DAOs de persistência**: 5 classes implementadas
  - `DatabaseManager.java`: Singleton JDBC com schema unificado
  - `ConversaDAO.java`: CRUD de conversas e mensagens
  - `MemoriaDAO.java`: CRUD de memórias com busca por categoria
  - `AutomacaoDAO.java`: CRUD de automações com toggle
  - `ConfiguracaoDAO.java`: Chave-valor com UPSERT
- **Schema unificado**: Frontend agora usa `../shared/maria.db` (mesmo banco do backend)
- **Controllers integrados**:
  - `ConversarController`: Salva mensagens no banco, limpar cria nova sessão
  - `MemoriaController`: Carrega/gerencia memórias do banco
  - `AutomacoesController`: Lista com status ✓/✗, toggle ativo/inativo
- **Testes JUnit**: 6 testes no `DatabaseManagerTest` (100% passing)

### 🔧 Correções Técnicas

- **Java version**: Maven atualizado para Java 17 (compatível)
- **Imports corrigidos**: `Optional` em `ConfiguracaoDAO.java`, `sqlite3` em `schema.py`
- **Banco compartilhado**: Eliminado `frontend/maria.db` separado; agora ambos usam `shared/maria.db`

### 📊 Métricas da Versão

| Categoria | Antes (v2.14.0) | Depois (v3.1.0) | Progresso |
|-----------|-----------------|-----------------|-----------|
| Comandos Bridge | 14 | 20 | +43% |
| DAOs Java | 0 | 5 | +500% |
| Tabelas Banco | 0 | 6 | Schema completo |
| Controllers Integrados | 1 | 3 | +200% |
| Testes Unitários | 86 | 92 | +6 testes |
