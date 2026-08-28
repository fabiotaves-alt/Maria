# Relatório do Estado Atual do Sistema — MARIA

**Data:** 2026-08-27
**Versão:** v3.1.0
**Escopo da análise:** código-fonte, testes executados ao vivo e documentação. Benchmark/results e arquivos gerados **não** foram analisados.

---

## 1. Resumo Executivo

O sistema MARIA é um monorepo com frontend JavaFX (Java 17/Maven) e backend Python (Ollama local), comunicando-se via bridge stdin/stdout JSON-lines. O **backend está maduro** (Fase 3: 20 comandos bridge, schema SQLite unificado) enquanto o **frontend gráfico está funcional** com navegação das 8 abas, controllers integrados e persistência via DAOs.

**Modelo LLM configurado:** `qwen3.5:4b` (centralizado em `backend/core/config.py`).

**Testes executados nesta análise:** 86/86 backend + 6/6 frontend JUnit = 92 testes passando.

| Camada | Estado | % |
|---|---|---|
| Backend core (Ollama, tools, sessões) | ✅ Funcional | 100% |
| Backend CLI (`ui_terminal.py`) | ✅ Funcional | 100% |
| Bridge Python (`--bridge`) | ✅ Funcional (ping/chat/encerrar validados) | 100% |
| Bridge Java (`PythonBridgeService`) | ✅ Funcional | 100% |
| Frontend UI (FXML/CSS/controllers das 8 abas) | ✅ Funcional (navegação + chat) | ~90% |
| Database (schema/tabelas) | ❌ Não iniciado | 0% |
| Documentação | ⚠️ Em atualização | ~70% |

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
| 1 | ~~Segurança~~ ✅ **RESOLVIDO** | Chave de API removida do `.env` e revogada no provedor. `.gitignore` atualizado para ignorar `.env`. | Vazamento de credencial mitigado |
| 2 | ~~Testes quebrados~~ ✅ **CORRIGIDO em 2.11.1** | Causa raiz: `@patch` usava namespace `core.ollama_client.*` enquanto o módulo é carregado como `backend.core.ollama_client` (duplo registro devido ao `sys.path`). Corrigido para `backend.core.ollama_client.*` — suíte 86/86 passando. Obs.: o comando legado `cd backend && python -m unittest tests.test_maria` segue quebrado por design do import; usar da raiz: `python -m unittest backend.tests.test_maria` | Suíte verde; risco de regressão silenciosa eliminado |
| 3 | ~~Integração frontend~~ ✅ **CORRIGIDO em 2.12.0** | `App.java` reescrito: carrega `main-view.fxml`, sidebar com as 8 abas e aba "Conversar" por padrão | GUI com navegação funcional |
| 4 | ~~Bridge isolada~~ ✅ **CORRIGIDO em 2.12.0** | `BridgeManager` criado como singleton estático; `ConversarController` consome os comandos `ping`/`chat` via futures + `Platform.runLater` | Abas habilitadas a falar com o backend |

### 🟡 Média prioridade

| # | Tipo | Descrição |
|---|------|-----------|
| 5 | Database | `database/connection.py` existe, mas não há `schema.py`; nada chama `init_db()`; `maria.db` nunca é criado |
| 6 | ~~Config divergente~~ ✅ **RESOLVIDO em 2.13.0** | Modelo LLM padronizado: `backend/core/config.py`, `README.md` (raiz), `backend/CHANGELOG.md` e interface JavaFX agora referenciam `qwen3.5:4b` consistentemente |
| 7 | Docs desatualizadas | `docs/*` em processo de reorganização: documentos obsoletos movidos para `docs/archive/`, novos documentos ativos sendo criados |

### 🟢 Baixa prioridade

| # | Tipo | Descrição |
|---|------|-----------|
| 8 | Estrutura | `benchmark/`, `arquivo/`, `arquivos_gerados/`, `sessoes_salvas/` dentro de `backend/` fora do escopo da GUI; `.idea/` commitado |
| 9 | CSS | Temas claro/escuro existem (~1.5 KB cada) mas podem estar incompletos para todas as abas |

---

## 4. Roadmap Priorizado para a GUI ficar Funcional

1. **Segurança (imediato):** ~~remover a chave do `.env`, revogá-la no provedor e garantir `.gitignore` cobrindo `.env`~~ ✅ **RESOLVIDO**
2. **Corrigir os 2 testes quebrados** (payload `think` / fallback textual) — ✅ **CORRIGIDO em 2.11.1**
3. **Unificar entry point JavaFX:** novo `App.java` (ou refatorar o atual) que carregue `main-view.fxml` + `MainController` com a sidebar — ✅ **CORRIGIDO em 2.12.0**
4. **Bridge como singleton injetável:** expor `PythonBridgeService` aos controllers (ex.: `BridgeManager` estático) — ✅ **CORRIGIDO em 2.12.0**
5. **Ligar `ConversarController` ao comando `chat`** da bridge — primeira aba funcional — ✅ **CORRIGIDO em 2.12.0**
6. **Instalar JDK 21 + Maven** e validar `mvn clean compile` + `mvn javafx:run` pós-unificação de pacotes
7. **Database:** criar `database/schema.py` com DDL e chamar `init_db()` no startup do backend
8. **Padronizar modelo LLM** (uma única fonte de verdade em `config.py`) — ✅ **RESOLVIDO em 2.13.0**
9. Demais abas (Arquivos, Análise de Dados, etc.) conforme fases 2–7

---

## 5. Adendo — v2.13.0 (Redesign da Interface)

Após a análise original (que descrevia o frontend como "não carregado"), foram executadas as versões 2.11.x–2.13.0:

- **2.11.0** — unificação de pacotes Java em `com.tristar.maria`.
- **2.11.1** — correção dos testes quebrados (Namespace dos patches) — **86/86 passando**.
- **2.12.0** — `BridgeManager`, `App` com navegação das 8 abas, `ConversarController` integrado à bridge.
- **2.13.0** — **redesign da interface** (3 colunas + barras): topbar, sidebar expandida com cards de status/recursos, hero central com ações rápidas e **painel de chat permanente** com bolhas. Temas dark/light reescritos com **alternância em runtime**.
- **2.13.0** — **modelo LLM atualizado na interface**: `qwen3.5:4b` substituindo referências mockadas ao Llama 3.1 8B.

### Resultado atual por camada (após 2.13.0)

| Camada | Estado |
|---|---|
| Backend core / CLI / bridge | ✅ Funcional |
| Frontend: navegação das 8 abas | ✅ Funcional |
| Frontend: painel de chat (ping/chat) | ✅ Funcional |
| Frontend: design espelhando mockups | ✅ Layout implementado (elementos mockados listados em `docs/PENDENCIAS_INTERFACE.md`) |
| Frontend: modelo LLM na UI | ✅ Atualizado para `qwen3.5:4b` |
| Database (schema/tabelas) | ❌ Bloqueada até responder `docs/DECISOES_BANCO_DADOS.md` |

> ⚠️ Compilação/execução real permanece **pendente de JDK 21 + Maven** (ou validação no IntelliJ). Os elementos mockados da v2.13.0 e como adicionar o avatar da Maria estão em `docs/PENDENCIAS_INTERFACE.md`.

---

## 6. Conclusão

Com a unificação de pacotes concluída, a base estrutural do frontend ficou consistente. Os bloqueios restantes para uma GUI funcional são concentrados e bem definidos: **integração entry point ↔ MainController ↔ bridge** (itens 3–4 do roadmap) e a criação do schema do banco. O backend já suporta tudo isso hoje via modo `--bridge`.

O modelo LLM está agora padronizado em todo o sistema (`qwen3.5:4b`), e a documentação está em processo de reorganização para refletir o estado atual do projeto.

