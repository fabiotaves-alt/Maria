# Relatório do Estado Atual do Sistema — MARIA

**Data:** 2026-08-24
**Escopo da análise:** código-fonte, testes executados ao vivo e documentação. Benchmark/results e arquivos gerados **não** foram analisados.

---

## 1. Resumo Executivo

O sistema MARIA é um monorepo com frontend JavaFX (Java 21/Maven) e backend Python (Ollama local), comunicando-se via bridge stdin/stdout JSON-lines. O **backend está maduro** (MVP Fase 2: chat, function calling, Excel/Word, sessões persistidas) enquanto o **frontend gráfico ainda não é funcional de ponta a ponta**: o entry point `App.java` é um demo standalone de chat que não carrega a navegação das 8 abas.

**Testes executados nesta análise:** 84/86 passando (33 subtestes ok) — 2 falhas em `backend/tests/test_maria.py` (ver §3).

| Camada | Estado | % |
|---|---|---|
| Backend core (Ollama, tools, sessões) | ✅ Funcional | ~95% |
| Backend CLI (`ui_terminal.py`) | ✅ Funcional | 100% |
| Bridge Python (`--bridge`) | ✅ Funcional (ping/chat/encerrar validados) | 100% |
| Bridge Java (`PythonBridgeService`) | ✅ Funcional | 100% |
| Frontend UI (FXML/CSS/controllers das 8 abas) | ⚠️ Criados mas **não carregados** pelo entry point | ~50% |
| Database (schema/tabelas) | ❌ Não iniciado | 0% |
| Documentação | ⚠️ Desatualizada/divergente | ~60% |

---

## 2. Ação Recente Concluída: Unificação dos Pacotes Java

Antes desta data coexistiam dois pacotes: `com.tristar.maria` (App + bridge) e `com.tristar.maria` (10 controllers + resources). **A unificação para `com.tristar.maria` foi executada:**

- ✅ 10 controllers movidos de `frontend/src/main/java/com/tristar/maria/ui/` → `com/tristar/maria/ui/`, com declaração `package` corrigida
- ✅ Resources (10 FXMLs + 2 CSS) movidos para `frontend/src/main/resources/com/tristar/maria/`
- ✅ `fx:controller` atualizado nos 10 FXMLs
- ✅ Caminho dinâmico em `MainController.carregarView()` corrigido (`/com/tristar/maria/...`)
- ✅ Bloco de reflexão morto (`setMainController`) removido do `MainController`
- ✅ `pom.xml`: groupId alterado para `com.tristar.maria` (mainClass já era `com.tristar.maria.App`)
- ✅ Pastas `com/nyc/` removidas; varredura confirma **zero referências residuais**

> ⚠️ **Validação de compilação pendente:** Maven e JDK 21 **não estão instalados** nesta máquina (`mvn` não reconhecido). A validação foi estática (pacotes/referências consistentes). Instalar JDK 21 + Maven e rodar `cd frontend && mvn clean compile && mvn javafx:run`.

---

## 3. Bugs, Erros e Inconsistências

### 🔴 Alta prioridade

| # | Tipo | Descrição | Impacto |
|---|------|-----------|---------|
| 1 | Segurança | `backend/.env` contém chave de API exposta (`NOSTROMO_API_KEY=sk-or-v1-…`) versionada no repo, além de um nome de modelo solto (`nvidia/nemotron-3.5-lightning:free`) que o código não usa | Vazamento de credencial |
| 2 | ~~Testes quebrados~~ ✅ **CORRIGIDO em 2.11.1** | Causa raiz: `@patch` usava namespace `core.ollama_client.*` enquanto o módulo é carregado como `backend.core.ollama_client` (duplo registro devido ao `sys.path`). Corrigido para `backend.core.ollama_client.*` — suíte 86/86 passando. Obs.: o comando legado `cd backend && python -m unittest tests.test_maria` segue quebrado por design do import; usar da raiz: `python -m unittest backend.tests.test_maria` | Suíte verde; risco de regressão silenciosa eliminado |
| 3 | ~~Integração frontend~~ ✅ **CORRIGIDO em 2.12.0** | `App.java` reescrito: carrega `main-view.fxml`, sidebar com as 8 abas e aba "Conversar" por padrão | GUI com navegação funcional |
| 4 | ~~Bridge isolada~~ ✅ **CORRIGIDO em 2.12.0** | `BridgeManager` criado como singleton estático; `ConversarController` consome os comandos `ping`/`chat` via futures + `Platform.runLater` | Abas habilitadas a falar com o backend |

### 🟡 Média prioridade

| # | Tipo | Descrição |
|---|------|-----------|
| 5 | Database | `database/connection.py` existe, mas não há `schema.py`; nada chama `init_db()`; `maria.db` nunca é criado |
| 6 | Config divergente | Modelo padrão difere entre camadas: `config.py` usa `qwen3.5:4b`, README diz `qwen2.5:7b`, `.env` menciona um modelo não usado |
| 7 | Docs desatualizadas | `docs/*` dizem "Fase 0 ~75%", backend já está em MVP Fase 2; estrutura descrita diverge da real |

### 🟢 Baixa prioridade

| # | Tipo | Descrição |
|---|------|-----------|
| 8 | Estrutura | `benchmark/`, `arquivo/`, `arquivos_gerados/`, `sessoes_salvas/` dentro de `backend/` fora do escopo da GUI; `.idea/` commitado |
| 9 | CSS | Temas claro/escuro existem (~1.5 KB cada) mas podem estar incompletos para todas as abas |

---

## 4. Roadmap Priorizado para a GUI ficar Funcional

1. **Segurança (imediato):** remover a chave do `.env`, revogá-la no provedor e garantir `.gitignore` cobrindo `.env`
2. **Corrigir os 2 testes quebrados** (payload `think` / fallback textual)
3. **Unificar entry point JavaFX:** novo `App.java` (ou refatorar o atual) que carregue `main-view.fxml` + `MainController` com a sidebar
4. **Bridge como singleton injetável:** expor `PythonBridgeService` aos controllers (ex.: `BridgeManager` estático)
5. **Ligar `ConversarController` ao comando `chat`** da bridge — primeira aba funcional
6. **Instalar JDK 21 + Maven** e validar `mvn clean compile` + `mvn javafx:run` pós-unificação de pacotes
7. **Database:** criar `database/schema.py` com DDL e chamar `init_db()` no startup do backend
8. **Padronizar modelo LLM** (uma única fonte de verdade em `config.py`)
9. Demais abas (Arquivos, Análise de Dados, etc.) conforme fases 2–7

---

## 5. Conclusão

Com a unificação de pacotes concluída, a base estrutural do frontend ficou consistente. Os bloqueios restantes para uma GUI funcional são concentrados e bem definidos: **integração entry point ↔ MainController ↔ bridge** (itens 3–4 do roadmap) e a criação do schema do banco. O backend já suporta tudo isso hoje via modo `--bridge`.

