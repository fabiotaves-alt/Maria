> ⚠️ **Documento obsoleto.** Descreve um estado do projeto anterior à unificação de pacotes Java (v2.11.0) e não reflete o estado atual. Consulte `docs/RELATORIO_ESTADO_ATUAL.md`.


# Arquitetura Real do Sistema Maria — Documento Técnico

**Data de geração:** Dezembro 2024  
**Status do projeto:** Fase 0 (Esqueleto) em andamento — ~75% completado

---

## 1. Visão Geral

**Maria** é uma assistente de IA pessoal e privada com processamento 100% local. O sistema consiste em dois processos independentes que se comunicam via IPC (stdin/stdout com protocolo JSON-lines):

- **Frontend**: JavaFX (interface visual com navegação por abas)
- **Backend**: Python (LLM local via Ollama, lógica de negócio, banco de dados)

---

## 2. Estrutura de Diretórios Real (Implementada)

```
/workspace/
├── frontend/                          # Projeto Maven JavaFX
│   ├── pom.xml                        # Configuração Maven (Java 21, JavaFX 21)
│   └── src/main/
│       ├── java/
│       │   ├── com/tristar/maria/
│       │   │   ├── App.java           # Ponto de entrada JavaFX (Fase 0 — demo standalone)
│       │   │   └── bridge/
│       │   │       ├── PythonBridgeService.java   # Gerencia processo Python (start/stop/restart)
│       │   │       ├── Requisicao.java            # POJO para requisições JSON
│       │   │       └── Resposta.java              # POJO para respostas JSON
│       │   │
│       │   └── com/tristar/maria/
│       │       └── ui/
│       │           ├── MainController.java        # Shell principal: sidebar + área dinâmica
│       │           ├── MenuItemsController.java   # Botões das 8 abas do menu lateral
│       │           ├── ConversarController.java   # Controller da aba Conversar (esqueleto)
│       │           ├── ArquivosController.java    # Controller da aba Arquivos (esqueleto)
│       │           ├── AnaliseDadosController.java # Controller da aba Análise de Dados
│       │           ├── VisaoController.java       # Controller da aba Visão
│       │           ├── VozController.java         # Controller da aba Voz
│       │           ├── MemoriaController.java     # Controller da aba Memória
│       │           ├── AutomacoesController.java  # Controller da aba Automações
│       │           └── ConfiguracoesController.java # Controller da aba Configurações
│       │
│       └── resources/com/tristar/maria/
│           ├── main-view.fxml         # Layout principal (sidebar + conteúdo dinâmico)
│           ├── menu-items.fxml        # Definição dos 8 botões do menu lateral
│           ├── conversar-view.fxml    # UI da aba Conversar
│           ├── arquivos-view.fxml     # UI da aba Arquivos
│           ├── analise-dados-view.fxml # UI da aba Análise de Dados
│           ├── visao-view.fxml        # UI da aba Visão
│           ├── voz-view.fxml          # UI da aba Voz
│           ├── memoria-view.fxml      # UI da aba Memória
│           ├── automacoes-view.fxml   # UI da aba Automações
│           ├── configuracoes-view.fxml # UI da aba Configurações
│           ├── theme-dark.css         # Tema escuro (identidade visual)
│           └── theme-light.css        # Tema claro (identidade visual)
│
├── backend/                           # Processo Python
│   ├── main.py                        # Loop de leitura stdin / escrita stdout (modo --bridge)
│   │                                  # Comandos suportados: ping, chat, encerrar
│   │
│   ├── core/                          # Lógica de negócio (reaproveitado do NYC Analista)
│   │   ├── __init__.py
│   │   ├── ollama_client.py           # Cliente HTTP para API local do Ollama
│   │   ├── chat_session.py            # Gerenciamento de histórico de mensagens
│   │   ├── tools_schema.py            # Definição de ferramentas (tools) para o LLM
│   │   ├── tool_chaining.py           # Encadeamento de chamadas de ferramentas
│   │   ├── session_storage.py         # Persistência de sessões em disco
│   │   ├── config.py                  # Configurações do sistema (URL, modelo, timeouts)
│   │   ├── excel_handler.py           # Leitura de planilhas Excel (pandas/openpyxl)
│   │   ├── word_handler.py            # Leitura de documentos Word
│   │   └── file_utils.py              # Utilitários de manipulação de arquivos
│   │
│   ├── database/                      # Camada de acesso ao banco de dados
│   │   ├── __init__.py
│   │   └── connection.py              # Padrão singleton: init_db, get_connection, close_connection
│   │                                  # PRAGMAs: foreign_keys=ON, journal_mode=WAL
│   │
│   ├── modulos/                       # Módulos específicos por aba (ESQUELETO VAZIO — pendente)
│   │   └── (vazio)                    # A ser implementado nas Fases 1-7
│   │
│   ├── tests/                         # Testes unitários (pytest)
│   │   ├── __init__.py
│   │   └── test_maria.py              # Testes básicos do backend
│   │
│   ├── benchmark/                     # Suite de benchmarks (não essencial para Fase 0)
│   │   ├── run_benchmark.py
│   │   ├── benchmark_config.py
│   │   ├── compare_runs.py
│   │   ├── runners/
│   │   ├── tasks/
│   │   └── analysis/
│   │
│   ├── arquivo/                       # Scripts experimentais/legados (não essenciais)
│   │   └── ui_terminal/               # Interface terminal (alternativa à JavaFX)
│   │       ├── init.py
│   │       ├── maria_terminal_art.py
│   │       └── ...
│   │
│   ├── sessoes_salvas/                # Diretório para sessões de chat persistidas
│   ├── arquivos_gerados/              # Diretório para arquivos gerados pelo sistema
│   ├── requirements.txt               # Dependências Python
│   ├── CHANGELOG.md                   # Histórico de mudanças
│   └── README.md                      # Documentação geral do backend
│
└── shared/                            # Recursos compartilhados
    └── .gitkeep                       # Banco maria.db será criado aqui (ainda não existe)
```

---

## 3. Funcionalidades Implementadas (Fase 0)

### 3.1. Frontend (JavaFX)

| Componente | Status | Descrição |
|---|---|---|
| **App.java (tristar)** | ✅ Implementado | Janela standalone com chat básico, inicia backend Python, realiza handshake ping/pong |
| **MainController (nyc)** | ✅ Implementado | Shell principal com sidebar e área de conteúdo dinâmica |
| **MenuItemsController** | ✅ Implementado | 8 botões funcionais no menu lateral, navegação entre abas via `carregarAba()` |
| **ConversarController** | ✅ Esqueleto | UI de chat com área de mensagens, campo de entrada, botão enviar (sem integração backend) |
| **ArquivosController** | ✅ Esqueleto | UI com botão "Selecionar Arquivo" e ListView (lógica pendente) |
| **AnaliseDadosController** | ✅ Esqueleto | UI com TextArea para resultados (lógica pendente) |
| **VisaoController** | ✅ Esqueleto | UI com ImageView e botão "Carregar Imagem" (lógica pendente) |
| **VozController** | ✅ Esqueleto | UI com botão "Gravar Áudio" e TextArea para transcrição (lógica pendente) |
| **MemoriaController** | ✅ Esqueleto | UI com ListView de fatos e campo para adicionar novos (lógica pendente) |
| **AutomacoesController** | ✅ Esqueleto | UI com ListView de automações e botão "Nova Automação" (lógica pendente) |
| **ConfiguracoesController** | ✅ Esqueleto | UI com TitledPanes para Tema, Modelo LLM e Banco de Dados (lógica pendente) |
| **PythonBridgeService** | ✅ Implementado | Inicia processo Python, envia requisições JSON, associa respostas por ID, thread de leitura assíncrona |
| **Requisicao/Resposta** | ✅ Implementado | POJOs para serialização JSON do protocolo de comunicação |
| **FXMLs (9 arquivos)** | ✅ Implementado | Todos os layouts das 8 abas + main-view + menu-items.fxml definidos |
| **CSS (temas)** | ✅ Implementado | theme-dark.css e theme-light.css criados (conteúdo a definir) |

**Observação:** Existem duas entradas principais no frontend:
1. `com.tristar.maria.App` — Demo standalone da Fase 0 (chat simples com bridge funcional)
2. `com.tristar.maria.ui.MainController` — Estrutura completa das 8 abas (ainda sem ponto de entrada JavaFX integrado)

---

### 3.2. Backend (Python)

| Componente | Status | Descrição |
|---|---|---|
| **main.py (modo --bridge)** | ✅ Implementado | Lê JSON do stdin, processa comandos `ping`, `chat`, `encerrar`, responde JSON no stdout |
| **MariaController** | ✅ Implementado | Encapsula lógica de negócio: inicialização, envio de mensagens, processamento de chunks, tool chaining |
| **OllamaClient** | ✅ Implementado | Cliente HTTP para API local do Ollama, suporte a streaming, tratamento de erros, fallback textual para tool calls |
| **ChatSession** | ✅ Implementado | Gerencia histórico de mensagens (máximo configurável), formatação para contexto do LLM |
| **Tools Schema** | ✅ Implementado | Definição de ferramentas disponíveis para o LLM (análise de arquivos, busca, etc.) |
| **Tool Chaining** | ✅ Implementado | Processa chamadas de ferramentas em sequência, confirmação antes de executar ações |
| **Session Storage** | ✅ Implementado | Salva/carrega sessões de chat em disco (JSON), lista sessões salvas |
| **Excel Handler** | ✅ Implementado | Leitura de planilhas Excel via pandas/openpyxl, extração de dados estruturados |
| **Word Handler** | ✅ Implementado | Leitura de documentos Word (.docx) |
| **File Utils** | ✅ Implementado | Utilitários para manipulação de caminhos, validação de arquivos |
| **Config** | ✅ Implementado | Configurações centralizadas: URL do Ollama, modelo, timeouts, parâmetros de geração |
| **Database Connection** | ✅ Implementado | Singleton de conexão SQLite, PRAGMAs WAL e foreign_keys, caminho padrão em `/shared/maria.db` |
| **Módulos por aba** | ❌ Pendente | Diretório `modulos/` existe mas está vazio — será implementado nas Fases 1-7 |

**Comandos suportados no modo bridge:**
- `ping` → Responde `{"status": "ok", "dados": "pong"}`
- `chat` → Envia mensagem ao LLM, processa resposta (com tool chaining se necessário), retorna texto final
- `encerrar` → Finaliza o loop e encerra o processo

---

### 3.3. Banco de Dados

| Item | Status | Descrição |
|---|---|---|
| **maria.db** | ❌ Não existe | Arquivo SQLite ainda não foi criado |
| **Schema** | ❌ Pendente | Tabelas conceituais definidas no guia (conversas, mensagens, memoria, arquivos_indexados, automacoes, configuracoes), DDL não implementado |
| **Connection Module** | ✅ Implementado | `database/connection.py` com funções `init_db()`, `get_connection()`, `close_connection()` |
| **DAOs** | ❌ Pendentes | Classes de acesso a dados para cada tabela (serão criadas nas Fases 1-7) |

---

## 4. Protocolo de Comunicação (Implementado)

### Formato das Mensagens

**Requisição (JavaFX → Python):**
```json
{"id": "1", "comando": "ping", "payload": null}
{"id": "2", "comando": "chat", "payload": {"mensagem": "Olá, Maria!"}}
{"id": "3", "comando": "encerrar", "payload": null}
```

**Resposta (Python → JavaFX):**
```json
{"id": "1", "status": "ok", "dados": "pong", "mensagemErro": null}
{"id": "2", "status": "ok", "dados": "Olá! Como posso ajudar você hoje?", "mensagemErro": null}
{"id": "3", "status": "erro", "dados": null, "mensagemErro": "Comando desconhecido: invalido"}
```

### Fluxo de Comunicação

1. **Inicialização**: `PythonBridgeService.iniciar()` executa `python main.py --bridge`
2. **Handshake**: Envia `{"id": "1", "comando": "ping"}` → aguarda `{"dados": "pong"}`
3. **Operação normal**: Cada comando gera um `CompletableFuture` armazenado em mapa `ConcurrentHashMap`
4. **Leitura assíncrona**: Thread dedicada lê stdout do Python, completa futures quando respostas chegam
5. **Encerramento**: `PythonBridgeService.encerrar()` destrói o processo Python

---

## 5. Comparação: Guia vs. Implementação Real

| Seção do Guia | Previsto | Implementado | Gap |
|---|---|---|---|
| **Estrutura frontend/** | `com/tristar/maria/` com App.java, bridge/, ui/, model/, dao/ | `com/tristar/maria/` (App + bridge) + `com/tristar/maria/ui/` (controllers) | Pacote `model/` e `dao/` não existem; dois pacotes raiz diferentes (`tristar` vs `nyc`) |
| **Estrutura backend/** | `core/`, `modulos/`, `database/`, `tests/` | `core/` ✅, `modulos/` (vazio) ❌, `database/` ✅, `tests/` ✅ | `modulos/` vazio; diretórios extras (`benchmark/`, `arquivo/`) não previstos |
| **Protocolo JSON** | `id`, `comando`, `payload` / `id`, `status`, `dados`, `mensagemErro` | ✅ Exatamente como previsto | Nenhum |
| **Comandos bridge** | `ping`, `chat`, `encerrar` | ✅ Implementados | Nenhum |
| **Banco de dados** | `maria.db` em `shared/` com 6 tabelas | `connection.py` ✅, schema ❌, DB file ❌ | Schema DDL e tables não criados |
| **8 abas UI** | Controllers + FXMLs para todas as 8 abas | ✅ Todos os 8 controllers + FXMLs existentes | Controllers são esqueletos sem lógica de negócio |
| **Integração bridge** | JavaFX usa bridge para comunicar com Python | ✅ `App.java` (tristar) usa `PythonBridgeService` | `MainController` (nyc) não está integrado com bridge |

---

## 6. Issues Críticos para Completar Fase 0

### Prioridade Alta 🔴

1. **Unificar ponto de entrada JavaFX**
   - Problema: Existem dois apps separados (`App.java` da tristar e estrutura `nyc` sem entry point)
   - Solução: Criar novo `App.java` em `com/tristar/maria/` que usa `MainController` + integra `PythonBridgeService`

2. **Criar schema do banco de dados**
   - Problema: `maria.db` não existe, tabelas não foram criadas
   - Solução: Implementar `database/schema.py` com DDL das 6 tabelas conceituais

3. **Integrar bridge com MainController**
   - Problema: `PythonBridgeService` está isolado em `App.java` (tristar), não acessível pelos controllers das abas
   - Solução: Mover bridge para serviço singleton injetável nos controllers ou criar `BridgeManager` compartilhado

### Prioridade Média 🟡

4. **Limpar diretórios não essenciais**
   - Problema: `benchmark/`, `arquivo/`, `ui_terminal.py` não fazem parte do escopo Fase 0
   - Solução: Mover para `/workspace/experimental/` ou remover

5. **Padronizar pacotes Java**
   - Problema: Mistura de `com.tristar.maria` e `com.tristar.maria`
   - Solução: Unificar tudo sob `com.tristar.maria`

6. **Implementar módulo database/schema.py**
   - Problema: Connection existe, mas não há criação de tabelas
   - Solução: Seguir padrão do NYC Analista com `init_db()` executando DDL

### Prioridade Baixa 🟢

7. **Preencher CSS dos temas**
   - Problema: `theme-dark.css` e `theme-light.css` podem estar vazios ou incompletos
   - Solução: Definir estilos base para sidebar, botões, labels, áreas de conteúdo

8. **Adicionar DAOs básicos**
   - Problema: Sem acesso typed ao banco (apenas conexão bruta)
   - Solução: Criar DAOs para `configuracoes` (primeira tabela a ser usada)

---

## 7. Próximos Passos Recomendados

Para completar a **Fase 0 (Esqueleto Executável)**:

1. **Criar `backend/database/schema.py`** com DDL das 6 tabelas
2. **Modificar `backend/main.py`** para chamar `init_db()` e `schema.criar_tabelas()` no startup
3. **Refatorar frontend** para unificar `App.java` sob `com/tristar/maria/` integrando bridge + MainController
4. **Testar fluxo completo**: Iniciar JavaFX → Handshake ping/pong → Navegar entre abas → Comando chat funcional
5. **Criar `maria.db`** automaticamente no primeiro boot em `/workspace/shared/`

Após Fase 0 completa, prosseguir para **Fase 1 (Conversar)**: integrar `ConversarController` com bridge para chat real via Ollama.

---

## 8. Resumo do Status Atual

| Área | Progresso | Observações |
|---|---|---|
| **Frontend UI (abas)** | 100% | Todas as 8 abas têm controller + FXML |
| **Frontend Bridge** | 100% | PythonBridgeService funcional com handshake |
| **Frontend Integração** | 50% | Bridge isolado em demo app, não integrado com navegação principal |
| **Backend Core** | 100% | OllamaClient, ChatSession, Tools, Tool Chaining operacionais |
| **Backend Bridge** | 100% | Modo `--bridge` com comandos ping/chat/encerrar |
| **Backend Módulos** | 0% | Diretório `modulos/` vazio |
| **Database Connection** | 100% | Singleton com PRAGMAs configurados |
| **Database Schema** | 0% | Nenhuma tabela criada |
| **Estrutura Direórios** | 75% | Pastas principais existem, mas com arquivos extras não previstos |

**Progresso total da Fase 0: ~75%**

---

*Documento gerado automaticamente a partir da análise do código-fonte em `/workspace`.*

