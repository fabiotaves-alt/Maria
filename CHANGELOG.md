# CHANGELOG - Projeto MARIA

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

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
- **Modelo padrão**: documentação, mensagens e testes alinhados ao `qwen2.5:7b`.
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
