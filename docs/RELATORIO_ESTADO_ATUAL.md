# Relatório do Estado Atual do Sistema — MARIA

**Data:** 2026-08-28  
**Versão:** v3.1.0  
**Escopo da análise:** código-fonte, testes executados ao vivo (pytest + JUnit 5) e documentação.

---

## 1. Resumo Executivo

O sistema MARIA é um monorepo com frontend JavaFX 21 (Maven) e backend Python 3.11+ (Ollama local), comunicando-se via bridge stdin/stdout JSON-lines e acessando um banco de dados SQLite unificado compartilhado (`shared/maria.db`).

**Modelo LLM configurado:** `qwen3.5:4b` (centralizado em `backend/core/config.py`).

**Testes executados nesta análise:** 86/86 backend (pytest) + 8/8 frontend (JUnit 5) = **94 testes passando**.

| Camada | Estado | % |
|---|---|---|
| Backend core (Ollama, tools, sessões) | ✅ Funcional | 100% |
| Backend CLI (`ui_terminal.py`) | ✅ Funcional | 100% |
| Bridge Python (`--bridge`) | ✅ Funcional (19 comandos) | 100% |
| Bridge Java (`PythonBridgeService`) | ✅ Funcional | 100% |
| Frontend UI (FXML/CSS/controllers das 8 abas) | ✅ Funcional (navegação + chat integrado) | ~95% |
| Database (schema unificado compartilhado) | ✅ 100% Funcional (shared/maria.db + WAL) | 100% |
| Documentação | ✅ Atualizada | 100% |

---

## 2. Ações Concluídas

### 2.1 Unificação do Schema de Banco de Dados
- Criado arquivo canônico [`shared/schema.sql`](../shared/schema.sql) com 6 tabelas estruturadas em português.
- Alinhamento de DDL entre `backend/database/schema.py` e `DatabaseManager.java`.
- Ativação de `PRAGMA journal_mode = WAL` e `PRAGMA foreign_keys = ON` com `ON DELETE CASCADE`.
- Implementação de migração preventiva de colunas em `DatabaseManager.java`.

### 2.2 DAOs e Persistência Java
- Atualização completa de `ConversaDAO.java`, `MemoriaDAO.java`, `AutomacaoDAO.java` e `ConfiguracaoDAO.java`.
- Criação de suíte de testes JUnit 5 em `DatabaseManagerTest.java` com **8 testes passando sem erros**.

### 2.3 Consolidação de Dependências
- Inclusão de `psutil>=5.9.0` no `requirements.txt` da raiz.
- Remoção do arquivo duplicado `backend/requirements.txt`.
- Configuração do Maven Compiler Release 21 no `pom.xml`.

### 2.4 Detecção de Ambiente Multiplataforma
- `App.java` detecta dinamicamente executáveis Python em Windows (`.venv/Scripts/python.exe`), Linux/macOS (`.venv/bin/python`) e PATH do sistema.

### 2.5 Identidade Visual
- `theme-dark.css` atualizado com aura rosa (`#e05d8a` / `#f2a2bb`), gradientes e brilhos nos botões, mantendo 100% de compatibilidade com o motor JavaFX 21 (Modena).

---

## 3. Conclusão

Todas as pendências críticas entre camadas foram resolvidas, e o sistema encontra-se estável, com banco de dados unificado e 94 testes automatizados verdes.
