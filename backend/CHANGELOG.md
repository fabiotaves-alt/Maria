# CHANGELOG - Projeto MARIA

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

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

## [2.14.0] — Desmockagem e Funcionalidades Reais

### ✅ Backend (Python)

- **Novo comando `status`**: Retorna métricas reais de CPU, RAM e GPU via `psutil`. Inclui modelo atual (`qwen3.5:4b`) na resposta.
- **Handler `analisar_arquivo`**: Lê documentos (.docx, .txt, .md, .csv, .log) e planilhas (.xlsx), retornando conteúdo ou resumo.
- **Handler `analisar_dados`**: Gera sumário de planilhas Excel (linhas, colunas, cabeçalhos, amostra de dados).
- **Handler `upload_arquivo`**: Copia arquivos para `backend/arquivos_gerados/` com nome único.
- **Handler `transcrever_audio`**: Integração com whisper.cpp (binário externo) para transcrição de áudio WAV. Fallback informativo se não instalado.
- **Nova dependência**: `psutil>=5.9.0` adicionada ao `requirements.txt`.
- **Função `ler_planilha_resumo()`**: Criada em `core/excel_handler.py` para leitura eficiente de planilhas.

### ✅ Frontend (JavaFX)

- **Sidebar com dados reais**: Barras de progresso (CPU/RAM/GPU) atualizadas a cada 5 segundos via comando `status`. Labels exibem porcentagem em tempo real.
- **Modelo dinâmico**: Texto do modelo na topbar é atualizado automaticamente via backend (agora exibe `qwen3.5:4b · via Ollama`).
- **Dropdown do chat funcional**: Menu "⋯" no header com opções "Limpar Conversa" e "Exportar Conversa (.txt)".
- **Botão anexar (📎) habilitado**: Abre FileChooser, envia arquivo via `upload_arquivo` e exibe confirmação no chat.
- **Botão de voz (🎤) habilitado**: Grava áudio via `javax.sound.sampled`, salva como WAV temporário e envia para transcrição. Indicador visual durante gravação.
- **Ações rápidas do Hero**: Botões agora preenchem o campo de mensagem com prompts contextuais prontos para envio.

### ⚠️ Notas

- **GPU**: Exibida como 0% se não houver GPU NVIDIA ou `pynvml` não estiver instalado.
- **Whisper.cpp**: Requer instalação manual do binário `whisper-main`. Sem fallback de transcrição se não disponível.
- **Avatar real**: Imagem `avatar.png` já carregada no hero. Pendente aplicação nas bolhas de mensagem.

## [2.13.0] - Redesign da Interface (3 colunas + barras)

### ✅ Interface JavaFX

- **Novo layout em `main-view.fxml`**: topbar (logo, pill MODO LOCAL, modelo **qwen3.5:4b**, botão de tema ☀/☾), sidebar expandida (260px), coluna central com hero + painel de chat permanente (380px), status bar inferior.
- **`theme-dark.css` e `theme-light.css` reescritos** (~70 regras cada): novas paletas (dark: fundo `#0e0e16`, accent rosa `#e05d8a`; light: fundo `#f7f3ec`, accent terracota `#c47b54`), com classes `.topbar`, `.pill-modo`, `.sidebar-card`, `.resource-bar-*`, `.card-feature`, `.quick-action`, `.bubble-user`, `.bubble-maria`, `.chat-panel`, `.avatar-hero`, `.menu-item-selected`, `.status-bar`.
- **`hero-view.fxml` + `HeroController.java` criados**: tela inicial central com título, subtítulo, avatar placeholder (gradiente + letra "M"), 3 cards de funcionalidades e 4 ações rápidas.
- **`ConversarController` reescrito** para painel de chat permanente: bolhas alinhadas (usuário à direita, Maria à esquerda com avatar), timestamps, header "CONVERSA ATUAL", input com 📎/🎤 desabilitados e botão enviar. Handshake `ping` + comando `chat` preservados.
- **`MainController` reescrito**: navegação troca apenas a coluna central; opção "Conversar" exibe o hero; alternância de tema em runtime (`alternarTema`); ações rápidas preenchem o campo do chat; `setCena` conectado pelo `App`.
- **`MenuItemsController`**: novo `destacar(...)` para realçar a aba ativa (`.menu-item-selected`).
- **`App.java`**: janela 1280×800, carga de `theme-dark.css` e `setCena` no controller.
- **`Image folder criada**: `resources/.../images/` para receber `avatar.png`.
- **Modelo LLM atualizado**: interface agora reflete o modelo real `qwen3.5:4b` (substituindo referências mockadas ao Llama 3.1 8B).

### ⚠️ Elementos mockados nesta fase
Recursos do sistema (CPU/RAM/GPU), ações rápidas (preenchem o input), anexar/voz (desabilitados) e dropdown "⋯" sem ação. Ver `docs/PENDENCIAS_INTERFACE.md`.

### ✅ Validação
- Estática: handlers `onAction`/`onMouseClicked` de todos os FXMLs mapeados aos controllers; zero typos de cor no CSS.
- Compilação/visual pendente de execução no IntelliJ (Maven/JDK não presentes na CLI).

## [2.12.0] - Integração do Frontend JavaFX e Organização da Documentação

### ✅ Frontend (Fase 1 do guia de próximos passos)

- **`BridgeManager.java` criado**: singleton estático para o `PythonBridgeService`, compartilhado entre `App.java` e os controllers das abas (`iniciar()`, `getInstance()` com `IllegalStateException` se não iniciado, `encerrar()`).
- **`App.java` reescrito**: chat standalone removido; agora carrega `main-view.fxml` (sidebar + navegação das 8 abas), aplica `theme-dark.css`, inicia a bridge via `BridgeManager` e encerra o processo Python ao fechar.
- **Injeção do menu corrigida**: `<fx:include fx:id="menuItems">` em `main-view.fxml`; `MainController` injeta-se no `MenuItemsController` no `initialize()` e carrega a aba "conversar" por padrão — os 8 botões do menu agora funcionam.
- **`ConversarController` integrado à bridge**: handshake `ping` automático ao abrir a aba; envio real via comando `chat`; respostas do Ollama exibidas na área de mensagens; `exceptionally` tratado também no envio.
- **Enter envia mensagem**: `onAction="#enviarMensagem"` adicionado ao TextField em `conversar-view.fxml`.

### ✅ Documentação (Fase 0 do guia)

- **`backend/README.md`**: modelo divergente corrigido (`qwen3.5:4b`, alinhado a `core/config.py`).
- **Documentos obsoletos arquivados** em `docs/archive/` com aviso de obsolescência: `RELATORIO_ACOMPANHAMENTO.md` e `ARQUITETURA_REAL_SISTEMA.md`.
- **`README.md` (raiz)**: tabela de documentação atualizada e modelo LLM atualizado para `qwen3.5:4b`.
- **`docs/DECISOES_BANCO_DADOS.md` criado**: registra as 4 perguntas pendentes antes da implementação de `database/schema.py` (Fase 2 bloqueada por decisão, não por código).

### ⚠️ Validação

- Validação estática concluída: zero referências residuais, pacotes/FXML/controllers consistentes.
- Compilação/execução real **pendente** de JDK 21 + Maven (não instalados na máquina): rodar `cd frontend && mvn clean compile && mvn javafx:run`.

## [2.11.1] - Correção dos Testes Quebrados (Namespace dos Patches)

### ✅ Correções aplicadas

- **Causa raiz**: os decoradores `@patch` usavam o namespace `core.ollama_client.*`, mas o módulo é importado como `backend.core.ollama_client`. Como o pytest adiciona `backend/` ao `sys.path`, o Python registrava dois módulos distintos e o patch era aplicado na instância errada — os flags (`OLLAMA_ENVIAR_THINK_PARAM`, `OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL`) nunca mudavam no código em execução.
- **Fix**: alvos de patch corrigidos para `backend.core.ollama_client.*` em `tests/test_maria.py` (linhas 1397, 1437–1438), incluindo `requests.Session` por consistência.
- **Observação**: o comando legado `cd backend && python -m unittest tests.test_maria` está quebrado por design (o arquivo importa `backend.*`). Comando correto a partir da raiz: `python -m unittest backend.tests.test_maria`.

### ✅ Status dos Testes

- **86/86 testes passaram** + 33 subtestes via pytest (raiz do monorepo)
- **86/86 passaram** via `python -m unittest backend.tests.test_maria` (raiz)

## [2.11.0] - Unificação de Pacotes Java e Documentação do Monorepo

### ✅ Alterações aplicadas

- **Unificação dos pacotes Java em `com.tristar.maria`**: os 10 controllers movidos de `com/nyc/maria/ui/` para `com/tristar/maria/ui/`, com declaração `package` corrigida.
- **Resources movidos**: 10 FXMLs + 2 CSS de `resources/com/nyc/maria/` para `resources/com/tristar/maria/`; atributos `fx:controller` atualizados nos 10 FXMLs.
- **`MainController` corrigido**: caminho dinâmico das views atualizado para `/com/tristar/maria/...`; bloco de reflexão morto (`setMainController`) removido.
- **`pom.xml` alinhado**: groupId alterado para `com.tristar.maria` (mainClass já era `com.tristar.maria.App`).
- **Pastas `com/nyc/` removidas**; varredura confirma zero referências residuais no código.
- **Documentação atualizada**: menções a `com.nyc` substituídas em `docs/ARQUITETURA_REAL_SISTEMA.md`, `docs/INTEGRACAO_FRONTEND.md` e `docs/RELATORIO_ACOMPANHAMENTO.md`.
- **Novos documentos na raiz**: `README.md` do monorepo (arquitetura, pré-requisitos, execução CLI/frontend/bridge) e `requirements.txt` consolidado.
- **Novo relatório**: `docs/RELATORIO_ESTADO_ATUAL.md` com análise de bugs, erros e inconsistências, percentuais por camada e roadmap priorizado para a GUI ficar funcional.

### ✅ Status dos Testes

- **84/86 testes passaram** (`pytest backend/tests/test_maria.py`) + 33 subtestes
- 2 falhas **pré-existentes** (não relacionadas a esta tarefa): `test_montar_payload_omite_think_quando_desabilitado` e `test_fallback_desativado_nao_extrai_tool_call`
- Validação do frontend foi estática (Maven/JDK 21 não instalados na máquina) — pendente `mvn clean compile`

### 📊 Cobertura de Código

- Frontend: estrutura de pacotes 100% consistente (Java + FXML + pom.xml)
- Backend: sem alterações de lógica nesta versão

## [2.10.0] - Configuração de Modelo Centralizada e Fallback Textual Desativável

### ✅ Alterações aplicadas

- **Configuração de comportamento do modelo concentrada em `core/config.py`**: 4 novas variáveis ajustáveis via ENV — `OLLAMA_ENVIAR_THINK_PARAM` (envio do campo "think"), `OLLAMA_THINK_HABILITADO` (valor do campo "think"), `OLLAMA_TEMPERATURE_TOOLS` (temperatura para tool calling) e `OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL` (fallback textual desativável).
- **Novos métodos privados em `OllamaClient`**: `_montar_options()` e `_montar_payload()` centralizam a construção do payload, eliminando 5 blocos duplicados de montagem manual.
- **Os 5 métodos de payload agora usam `self._montar_payload`**: `enviar_mensagem`, `chat_com_tools`, `chat_com_tools_stream_com_metricas`, `chat_com_tools_stream` e `continuar_com_resultado_ferramenta_stream`.
- **Inconsistência de `temperature` corrigida**: `continuar_com_resultado_ferramenta_stream` agora envia `temperature` (antes era o único dos 5 que não aplicava).
- **Mensagem de erro dinâmica em `_make_request`**: a mensagem de conexão agora reflete `self.model`/`self.base_url` reais em vez de literais fixos `qwen3.5:4b`/`localhost:11434`.
- **`model_file.txt` removido** do repositório (sem referências em código Python).
- **Fallback textual de tool call desativável**: os 4 pontos em `core/ollama_client.py` que extraem tool call vazada como texto (comportamento do Qwen3.5) agora respeitam `OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL`.
- **Debug scripts atualizados**: `debug_raw_ollama.py` e `debug_raw_ollama_2systems.py` usam `OLLAMA_TEMPERATURE_TOOLS`, `OLLAMA_ENVIAR_THINK_PARAM` e `OLLAMA_THINK_HABILITADO` em vez de literais hardcoded.

### ✅ Status dos Testes

- **80/80 testes passaram** (`python -m unittest tests.test_maria -v`)
- 5 testes novos: `TestConfiguracaoDeModeloCentralizada` (4) + `TestFallbackTextualDesativavel` (1)
- **Compilação sem erros** (`python -m py_compile core/config.py core/ollama_client.py debug_raw_ollama.py debug_raw_ollama_2systems.py tests/test_maria.py`)

### 📊 Cobertura de Código

- Payload centralizado: inclusão/omissão de `think`, temperatura condicional, mensagem de erro com model/base_url dinâmicos.
- Fallback textual: desativado não extrai tool call; testes existentes continuam passando com o default `True`.

## [2.9.0] - Correções do Benchmark: Encadeamento de Leitura, Composição de Documentos e Falso Positivo de listar_arquivos

### ✅ Correções aplicadas

- **Encadeamento de leitura compartilhado (Fix A)**: criado o módulo `core/tool_chaining.py` com `encadear_leitura_stream`, usado tanto pela aplicação interativa (`main.py`) quanto pelo benchmark (`benchmark/runners/maria_runner.py`). O benchmark agora reenvia o resultado de `listar_arquivos`/`resumir_documento` ao modelo e captura a ferramenta de escrita seguinte, em vez de marcar `tool_correct=False` na primeira chamada.
- **Timeout POR CHAMADA no encadeamento**: cada chamada de continuação do encadeamento de leitura no benchmark tem seu próprio orçamento de `BENCHMARK_TASK_TIMEOUT` segundos, medido do início ao fim daquela chamada específica (não acumulado), resolvendo o item em aberto da seção 1.1 de `docs/guia_fase_2.md`.
- **`main.py` refatorado**: `_gerar_resposta_com_encadeamento` agora delega ao módulo compartilhado; removidos os imports diretos de `MAX_PASSOS_LEITURA`, `FERRAMENTAS_LEITURA` e `executar_ferramenta_leitura`.
- **Composição de documentos sem conteúdo literal (Fix B)**: o reforço em `core/ollama_client.py` (`_montar_mensagens_com_reforco`) agora instrui o modelo a REDIGIR conteúdo completo para documentos narrativos (carta, relatório, ata, comunicado) sem pedir mais detalhes ao usuário.
- **Falso positivo de `listar_arquivos` corrigido (Fix D)**: a regra 6 do `SYSTEM_PROMPT` em `core/chat_session.py` agora distingue arquivo incerto de arquivo declaradamente inexistente — responde em texto SEM chamar `listar_arquivos` nem outra ferramenta.

### ✅ Status dos Testes

- **75/75 testes passaram** (`python -m unittest tests.test_maria -v`)
- **Compilação sem erros** (`python -m py_compile main.py core/tool_chaining.py core/ollama_client.py core/chat_session.py benchmark/runners/maria_runner.py tests/test_maria.py`)

### 📊 Cobertura de Código

- Encadeamento de leitura: avanço até ferramenta de escrita, limite de passos, propagação de timeout por chamada e integração no `MariaRunner`.
- Reforço de composição de documento e exceção de arquivo fictício no `SYSTEM_PROMPT`.

## [2.8.0] - Correções de Alta Prioridade e Validação de Argumentos

### ✅ Correções aplicadas

- **TOCTOU em criação de pastas corrigido**: substituído o padrão de `exists()` + `makedirs()` por `os.makedirs(..., exist_ok=True)` em `core/file_utils.py` e `core/session_storage.py`, eliminando a condição de corrida entre checagem e criação da pasta.
- **Imports não utilizados removidos**: limpeza dirigida em `main.py`, `core/word_handler.py` e `tests/test_maria.py`, sempre com confirmação textual da ausência de referências antes da remoção.
- **Validação de argumentos obrigatórios implementada**: adicionado `CAMPOS_OBRIGATORIOS` e `validar_argumentos_obrigatorios()` em `core/tools_schema.py`, com chamada no início de `executar_ferramenta_real` antes da execução de cada ferramenta real.
- **Tratamento de erro reforçado**: campos obrigatórios ausentes ou vazios agora geram `ValueError` claro, evitando execução de ferramentas com arquivos vazios ou incompletos.
- **Cobertura de regressão expandida**: novos testes cobrindo ausência de campo obrigatório e string vazia em campos obrigatórios.
- **Documentação de benchmark atualizada**: README geral e `benchmark/README.md` agora mencionam a taxa de conformidade de idioma gerada pelo relatório.

### ✅ Status dos Testes

- **42/42 testes passaram** (`python -m unittest tests.test_maria -v`)
- **Compilação sem erros** (`python -m py_compile main.py core/config.py core/file_utils.py core/tools_schema.py core/ollama_client.py core/chat_session.py core/session_storage.py core/excel_handler.py core/word_handler.py tests/test_maria.py`)

### 📊 Cobertura de Código

- Validação de argumentos antes da execução real de ferramentas, tratamento de TOCTOU em criação de diretórios, remoção segura de imports e regressões em testes de execução real.

## [2.7.0] - Integração das Ferramentas de Leitura no Controller

### ✅ Funcionalidades implementadas

- **Encadeamento automático de leitura**: O método `enviar_mensagem` em `main.py` (classe `MariaController`) agora encadeia automaticamente ferramentas de **leitura** (`listar_arquivos`, `resumir_documento`) sem pedir confirmação, até `MAX_PASSOS_LEITURA` vezes.
- **Novo generator `_gerar_resposta_com_encadeamento`**: Chama o modelo via `chat_com_tools_stream` e, enquanto a tool call for de leitura, executa via `executar_ferramenta_leitura` e reenvia o resultado via `continuar_com_resultado_ferramenta_stream` — mantendo o efeito de streaming contínuo.
- **Ferramentas de escrita preservadas**: Quando o encadeamento chega a uma ferramenta de **escrita** (`criar_planilha`, `criar_documento`, `editar_planilha`), o fluxo de confirmação normal é acionado ao final — `get_mensagem_confirmacao` e `processar_confirmacao` permanecem intactos.
- **Limite de passos respeitado**: Se `MAX_PASSOS_LEITURA` for atingido sem resposta final, um aviso amigável é exibido e o encadeamento é encerrado com segurança.
- **Tratamento de erros de leitura**: `PermissionError`, `OSError` e `ValueError` ao executar ferramentas de leitura são capturados e devolvidos ao modelo como texto, sem derrubar a aplicação.
- **`ui_terminal.py` intacto**: A interface continua iterando `(chunk, tool_chunk)` como antes — nenhuma alteração foi necessária.

### ✅ Status dos Testes

- **40/40 testes passaram** (`python -m unittest tests.test_maria -v`)
- **Compilação sem erros** (`python -m py_compile main.py`)
- **Validação com mocks**: 3 cenários de encadeamento validados (leitura→escrita, leitura simples, limite de passos)

### 📊 Cobertura de Código

- Encadeamento de leitura: execução sem confirmação, propagação de tool de escrita, limite de passos, tratamento de erros.

## [2.6.0] - Exibição de Comandos na Tela Inicial

### ✅ Funcionalidades implementadas

- **Linha de comandos no banner inicial**: A função `exibir_banner` em `ui_terminal.py` agora exibe diretamente a linha `Comandos: 'ajuda' | 'limpar' | 'retomar' | 'sair'` na inicialização, eliminando a necessidade de digitar `ajuda` primeiro.
- **Comando `retomar` visível na inicialização**: O comando `retomar` (introduzido na v2.4.0) agora aparece diretamente no banner junto dos comandos básicos (`ajuda`, `limpar`, `sair`).
- **README.md revisado**: Confirmado que a tabela "Comandos Disponíveis" permanece consistente com a nova linha do banner; nenhuma edição foi necessária (o README não reproduz a tela inicial literalmente).

### ✅ Status dos Testes

- **Nenhuma alteração de lógica testável** — a mudança é apenas de texto de interface (`print` de uma nova linha no banner).
- **Validação manual**: `python main.py` confirmou a exibição da linha `Comandos: 'ajuda' | 'limpar' | 'retomar' | 'sair'` antes do prompt `maria@assistente:~$`, seguida de `sair` para encerrar.

### 📊 Cobertura de Código

- Mudança puramente de interface (texto de tela); sem lógica testável adicionada.

## [2.5.0] - Ferramentas de Leitura: Listagem e Resumo de Documentos

### ✅ Funcionalidades implementadas

- **Lista branca de pastas (`PASTAS_PERMITIDAS`)**: nova variável de ambiente que restringe onde a MARIA pode ler arquivos; resolução de caminho protegida contra path traversal (`resolver_caminho_permitido`).
- **`listar_arquivos`**: nova ferramenta que lista nome e tamanho dos arquivos de uma pasta permitida.
- **`resumir_documento`**: nova ferramenta que lê `.txt`, `.md`, `.csv`, `.log` e `.docx` (com truncamento seguro via `MAX_CHARS_LEITURA`) para que o modelo resuma ou analise o conteúdo.
- **Ferramentas de leitura não pedem confirmação**: por serem somente leitura, `listar_arquivos` e `resumir_documento` são executadas imediatamente, diferente das ferramentas de escrita.
- **Encadeamento de chamadas**: `main.py` processa até `MAX_PASSOS_LEITURA` ferramentas de leitura em sequência (ex.: listar → ler → resumir) antes de responder ou pedir confirmação de escrita.
- **Streaming mantido na continuação**: novo método `continuar_com_resultado_ferramenta_stream` em `OllamaClient` devolve o resultado da leitura ao modelo e transmite a resposta em streaming.

### 🔒 Segurança e confiabilidade

- Todo acesso de leitura é validado contra `PASTAS_PERMITIDAS`; caminhos fora da lista branca são rejeitados com `ValueError`.
- Extensões de leitura restritas a uma lista branca (`EXTENSOES_LEITURA`).
- Limites de tamanho de arquivo (`MAX_TAMANHO_ARQUIVO_MB`) e de caracteres lidos (`MAX_CHARS_LEITURA`).
- `PermissionError`/`OSError` tratados com mensagens amigáveis, no mesmo padrão de `excel_handler.py`/`word_handler.py`.

### 🧪 Testes

- Novas classes `TestAcessoLeitura` e `TestFerramentasLeitura` cobrindo path traversal, listagem, truncamento, extensão não suportada e arquivo inexistente.

### ✅ Status dos Testes

- **40/40 testes passaram** (`python -m unittest tests.test_maria -v`)
- **Compilação sem erros** (`python -m py_compile main.py core/config.py core/file_utils.py core/tools_schema.py core/ollama_client.py core/chat_session.py tests/test_maria.py`)

### 📊 Cobertura de Código

- Ferramentas de leitura: path traversal, listagem de arquivos, truncamento, extensão não suportada, arquivo inexistente, resumo de documento e ferramenta desconhecida.

## [2.4.0] - Persistência de Sessões (Histórico de Conversa)

- **Novo módulo `core/session_storage.py`**: Persistência de sessões de chat em disco, com 4 funções públicas (`garantir_pasta_sessoes`, `salvar_sessao`, `listar_sessoes_salvas`, `carregar_sessao`) e leitura dinâmica de `PASTA_SESSOES` por chamada (isolamento em testes).
- **Nova config `PASTA_SESSOES`** em `core/config.py`: Configurável via variável de ambiente, padrão `sessoes_salvas`, seguindo o mesmo padrão de `PASTA_ARQUIVOS_GERADOS`.
- **Novo comando `retomar`** em `main.py`: Lista sessões salvas (mais recentes primeiro) e retoma a sessão escolhida de uma execução anterior. Funciona mesmo sem sessões salvas (mensagem clara, sem crash).
- **Salvamento automático**: A sessão é salva em disco após cada troca normal de mensagens e após a execução confirmada de uma ferramenta.
- **Arquivos de sessão**: Cada execução gera um arquivo `sessao_<timestamp>.json` na pasta `sessoes_salvas/`; ao retomar, a conversa continua salvando no mesmo arquivo.
- **Tolerância a falhas de disco**: Falhas ao salvar (`PermissionError`/`OSError`) exibem aviso mas não interrompem o loop de chat.
- **Sessões em disco**: Sessão salva anteriormente nesta execução (`sessoes_salvas/sessao_20260811_123004.json`) é ignorada pela funcionalidade de retomada apenas se corrompida ou ilegível.

### 🧪 Testes

- Suíte ampliada para **30 testes** (26 existentes + 4 novos).
- Nova classe `TestSessionStorage` cobrindo: salvar/carregar com mesmo histórico, ordenação por timestamp (mais recentes primeiro), arquivo corrompido ignorado e `ValueError` para sessão inexistente.
- Todos os testes isolados em diretório temporário via `tempfile.TemporaryDirectory`.

### ✅ Status dos Testes

- **30/30 testes passaram** (`python -m unittest tests.test_maria -v`)
- **Compilação sem erros** (`python -m py_compile main.py core/session_storage.py core/config.py tests/test_maria.py`)

### 📊 Cobertura de Código

- Persistência de sessões: salvar, carregar, listar (ordenação + arquivo corrompido), erro de arquivo inexistente.

## [2.3.0] - Reorganização de Arquitetura

- Eliminada a pasta duplicada `MARIA/` que estava aninhada dentro da raiz do projeto.
- Módulos centrais (`chat_session.py`, `config.py`, `excel_handler.py`, `file_utils.py`, `ollama_client.py`, `tools_schema.py`, `word_handler.py`) movidos para o novo pacote `core/`.
- `test_maria.py` movido para a pasta `tests/`.
- Pasta `Lia_benchmark/` removida (código legado não utilizado).
- Todos os imports internos — de `main.py`, dos testes e do pacote `benchmark/` — atualizados para referenciar `core.<módulo>`.
- Comando de execução dos testes atualizado para `python -m unittest tests.test_maria -v`.
- `PASTA_ARQUIVOS_GERADOS` continua relativa ao diretório de execução (cwd); nenhuma mudança de comportamento nesse ponto.

## [2.2.0] - Sistema de Benchmark e Validação Contínua

- Criado o pacote `benchmark/` para avaliação live do tool calling da MARIA.
- Adicionados 25 casos de benchmark cobrindo conversa, criação/edição de arquivos, confirmação, cancelamento, ambiguidade e sanitização.
- Implementado `MariaRunner` com streaming real, sessões isoladas, retry do Ollama e diretório de arquivos separado.
- Adicionadas métricas de acurácia de ferramentas, confirmação, palavras-chave, execução, latência e distribuição de erros.
- Criados relatórios Markdown com `log.json` e comparação Antes vs Depois em pontos percentuais.
- Adicionada CLI com filtros por IDs, quantidade, categoria, diretório de saída e atraso entre tarefas.
- Documentado o uso em [benchmark/README.md](benchmark/README.md); o benchmark exige Ollama local e não possui modo `--reference-only`.

## [2.1.0] - Fase 2: Streaming e Ferramentas de Arquivo

### ✅ Funcionalidades implementadas

- **Streaming de respostas**: `chat_com_tools_stream()` exibe o texto progressivamente e preserva tool calls ao final da resposta.
- **Criação real de documentos Word**: `criar_documento` agora recebe `conteudo` completo e cria parágrafos reais separados por linhas em branco.
- **Edição de planilhas**: adicionada a ferramenta `editar_planilha`, que substitui a estrutura e os dados de uma planilha Excel existente após confirmação.
- **Confirmações específicas**: a edição informa explicitamente que o arquivo será sobrescrito e documentos exibem uma prévia do conteúdo.
- **Histórico de execução**: o resultado de uma ferramenta confirmada é registrado como mensagem `assistant` na sessão.

### 🔒 Segurança e confiabilidade

- **Sanitização de nomes**: nomes de arquivos removem componentes de caminho e caracteres inseguros antes da escrita.
- **Isolamento de testes**: a pasta `PASTA_ARQUIVOS_GERADOS` é lida dinamicamente, permitindo diretórios temporários por teste.
- **Streaming defensivo**: chunks com `tool_calls: []`, tool calls malformadas e JSON inválido não derrubam o cliente.
- **Modelo padrão**: documentação, mensagens e testes alinhados ao `qwen3.5:4b`.
- **Limpeza de histórico**: removido o parâmetro sem efeito `manter_system` de `ChatSession.limpar_historico()`.

### 🧪 Testes

- Suíte ampliada para **24 testes**.
- Cobertura de criação e edição de `.xlsx`, conteúdo real em `.docx`, sanitização, isolamento de pasta e regressão de streaming.

## [2.0.0] - Máquina de Estado de Confirmação e Execução Real

### ✅ IMPLEMENTADO - Máquina de Estado de Confirmação

- **Fluxo de confirmação antes de criar arquivos**: Implementado estado `acao_pendente` em `ChatSession` para armazenar tool calls aguardando confirmação do usuário.
- **`interpretar_confirmacao()`**: Nova função que interpreta respostas afirmativas ("sim", "pode", "confirmo", "ok", "vai", "isso") e negativas ("não", "nao", "cancela", "para", "esquece"), retornando `None` para respostas ambíguas.
- **Cancelamento automático por ambiguidade**: Após 2 respostas ambíguas consecutivas, a ação é cancelada automaticamente com mensagem de segurança.
- **Comandos especiais durante confirmação**: Comandos `sair`, `exit`, `limpar` e `ajuda` funcionam normalmente mesmo com ação pendente; `limpar` também cancela qualquer ação pendente.

### ✅ IMPLEMENTADO - Execução Real de Arquivos

- **Integração com `excel_handler.py` e `word_handler.py`**: Método `executar_ferramenta_real` em `tools_schema.py` agora cria arquivos `.xlsx` e `.docx` reais.
- **Exibição do caminho do arquivo gerado**: Após confirmação, o terminal exibe `[SISTEMA] Arquivo criado: {caminho_completo}`.
- **Tratamento de exceções amigável**: `PermissionError`, `OSError` e `ValueError` são tratados com mensagens claras via `logger.error` + `print`, sem stack trace cru.
- **Geração de nomes únicos**: Função `gerar_nome_unico` em `file_utils.py` adiciona sufixo `_1`, `_2`, etc. para evitar sobrescrita.

### 🧪 Testes Automatizados Adicionados

Total de testes: **22 testes** (acréscimo de 8 novos testes)

Novos grupos de teste:
- `TestInterpretarConfirmacao`: 3 testes cobrindo casos afirmativo, negativo e ambíguo
- `TestExecucaoReal`: 2 testes para criação real de planilha e documento em pasta temporária
- `TestGerarNomeUnico`: 1 teste para conflito de nome com sufixo `_1`
- `TestFluxoConfirmacao`: 2 testes para cancelamento automático por ambiguidade repetida
- `TestRegressao`: 2 testes para `chat_com_tools` com tool_calls malformado e string de simulação sem `\"` literal

---

## [1.1.0] - Correções e Melhorias da Fase 1

### 🔴 CRÍTICO - Corrigido

- **System prompt agora é enviado ao modelo**: Alterado `main.py` para usar `sessao.get_historico_com_system()` em vez de `get_historico_sem_system()`, garantindo que o system prompt seja sempre incluído na primeira posição da lista de mensagens enviada ao Ollama.
- **Python 3.11+ como requisito mínimo**: Atualizado README.md declarando Python 3.11+ como requisito. Todos os módulos foram atualizados para usar sintaxe moderna de tipos (`list[...]`, `dict[...]`, `X | Y`).
- **Exceções tratadas durante streaming**: Método `_process_stream` em `ollama_client.py` agora envolve a iteração com tratamento de erro, convertendo exceções de rede em `OllamaClientError` também durante o consumo do generator.

### 🟠 IMPORTANTE - Corrigido

- **Duplicação de lógica removida**: Métodos `enviar_mensagem` e `chat_com_tools` agora reutilizam o método privado `_make_request`, eliminando código duplicado.
- **Método `chat()` removido**: Método morto/incompleto foi removido de `ollama_client.py`.
- **Mensagens de erro padronizadas**: Ambos os métodos agora incluem status code e corpo da resposta (`response.text`) nas mensagens de erro.
- **Resultado de simulação de ferramenta não polui histórico**: Tool calls são exibidas como `[SISTEMA]` no console e não são adicionadas ao histórico de conversa.
- **Verificação de conexão otimizada**: `_check_connection()` agora verifica apenas uma vez por sessão (primeira chamada), tratando falhas diretamente no `try/except` da requisição principal.

### 🟡 MELHORIAS - Implementadas

- **`.gitignore` corrigido**: Arquivo agora contém apenas os padrões sem marcação Markdown.
- **`requirements.txt` criado**: Dependência `requests>=2.31.0` fixada para reprodução do ambiente.
- **Configuração centralizada**: Criado módulo `config.py` com todas as configurações (URL, modelo, timeout, histórico, logging).
- **Logging configurável**: Substituído `print()` de debug em `tools_schema.py` por `logging` com nível configurável.
- **Encoding UTF-8 no Windows**: Adicionado `sys.stdout.reconfigure(encoding="utf-8")` em `main.py` com fallback silencioso.
- **Testes unitários adicionados**: 15 testes cobrindo `ChatSession` (limite de histórico, system prompt) e `tools_schema` (simulação de ferramentas).

### Estrutura de Arquivos

Novos arquivos:
- `config.py` - Configurações centralizadas
- `requirements.txt` - Dependências Python
- `test_maria.py` - Testes unitários
- `CHANGELOG.md` - Histórico de mudanças

Arquivos modificados:
- `.gitignore` - Corrigido formato
- `README.md` - Atualizado com Python 3.11+, nova estrutura e documentação de correções
- `ollama_client.py` - Refatorado com tipos modernos, _make_request, tratamento de streaming
- `chat_session.py` - Atualizado com tipos modernos
- `tools_schema.py` - Logging em vez de print, tipos modernos
- `main.py` - Usa get_historico_com_system, config centralizado, encoding UTF-8, logging

---

## [1.0.0] - Versão Inicial da Fase 1

### Implementado

- Cliente básico de comunicação com Ollama
- Sessão de chat com histórico limitado
- Prompt de sistema em português
- Esquema de function calling para planilhas e documentos
- Interface CLI básica
