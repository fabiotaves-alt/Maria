# 📊 PROGRESSO DE DESENVOLVIMENTO — MARIA V1

## 📅 Última alteração: 2026-08-16

## 📈 Percentual Total Concluído: 98%

---

## ✅ Checklist de Funcionalidades

### Fase 1 — Base da MARIA
- [x] Cliente básico de comunicação com Ollama
- [x] Sessão de chat com histórico limitado
- [x] Prompt de sistema em português
- [x] Esquema de function calling para planilhas e documentos
- [x] Interface CLI básica

### Fase 1.1 — Correções e Melhorias
- [x] System prompt enviado ao modelo (correção crítica)
- [x] Python 3.11+ como requisito mínimo
- [x] Configuração centralizada em `config.py`
- [x] `requirements.txt` criado
- [x] Encoding UTF-8 no Windows
- [x] Logging configurável
- [x] 15 testes unitários (Fase 1)

### Fase 2 — Máquina de Estado de Confirmação e Execução Real (v2.0.0)
- [x] Fluxo de confirmação antes de criar arquivos (`acao_pendente`)
- [x] `interpretar_confirmacao()` — afirmativas, negativas e ambíguas
- [x] Cancelamento automático por ambiguidade repetida
- [x] Comandos especiais durante confirmação (`sair`, `exit`, `limpar`, `ajuda`)
- [x] Execução real de arquivos (Excel `.xlsx` e Word `.docx`)
- [x] Exibição do caminho do arquivo gerado (`[SISTEMA]`)
- [x] Tratamento de exceções amigável (`PermissionError`, `OSError`, `ValueError`)
- [x] Geração de nomes únicos (`gerar_nome_unico`)

### Fase 2.1 — Streaming e Ferramentas de Arquivo (v2.1.0)
- [x] Streaming de respostas (`chat_com_tools_stream()`)
- [x] Criação real de documentos Word com conteúdo completo
- [x] Edição de planilhas (`editar_planilha`) com sobrescrita
- [x] Confirmações específicas com prévia do conteúdo
- [x] Histórico de execução de ferramentas na sessão
- [x] Sanitização de nomes de arquivos
- [x] Isolamento de testes (pasta temporária dinâmica)
- [x] Streaming defensivo (tool calls malformadas não derrubam)

### Fase 2.2 — Sistema de Benchmark (v2.2.0)
- [x] Pacote `benchmark/` criado
- [x] 25 casos de benchmark (conversa, arquivos, confirmação, cancelamento, ambiguidade, sanitização)
- [x] `MariaRunner` com streaming real e sessões isoladas
- [x] Métricas de acurácia, confirmação, palavras-chave, execução, latência, conformidade de idioma e erros
- [x] Relatórios Markdown com `log.json`
- [x] CLI com filtros (IDs, quantidade, categoria, diretório, atraso)

### Fase 2.3 — Reorganização de Arquitetura (v2.3.0)
- [x] Módulos centrais movidos para o pacote `core/`
- [x] `test_maria.py` movido para `tests/`
- [x] Imports internos atualizados para `core.<módulo>`
- [x] Pasta duplicada `MARIA/` eliminada
- [x] Código legado `Lia_benchmark/` removido

### Fase 2.4 — Persistência de Sessões (v2.4.0) ✅
- [x] Novo módulo `core/session_storage.py`
- [x] Funções: `garantir_pasta_sessoes`, `salvar_sessao`, `listar_sessoes_salvas`, `carregar_sessao`
- [x] Config `PASTA_SESSOES` em `core/config.py` (padrão `sessoes_salvas`)
- [x] Novo comando `retomar` em `main.py`
- [x] Salvamento automático após mensagens e execução de ferramenta
- [x] Tolerância a falhas de disco (aviso sem interromper o loop)
- [x] Testes: 4 novos (`TestSessionStorage`) — 30 testes no total, todos passando

### Fase 2.5 — Ferramentas de Leitura (v2.5.0) ✅
- [x] Lista branca de pastas (`PASTAS_PERMITIDAS`) com proteção contra path traversal
- [x] `resolver_caminho_permitido()` — validação de caminhos dentro das pastas permitidas
- [x] `listar_arquivos` — nova ferramenta de leitura (sem confirmação)
- [x] `resumir_documento` — nova ferramenta de leitura de `.txt`, `.md`, `.csv`, `.log`, `.docx`
- [x] `FERRAMENTAS_LEITURA` — conjunto de ferramentas executadas sem confirmação
- [x] `TOOLS_SCHEMA` expandido de 3 → 5 ferramentas
- [x] `continuar_com_resultado_ferramenta_stream()` — streaming com `role="tool"`
- [x] Encadeamento de leitura em `main.py` (até `MAX_PASSOS_LEITURA` passos)
- [x] `SYSTEM_PROMPT` atualizado com instruções anti-alucinação para leitura
- [x] Testes: 10 novos (`TestAcessoLeitura` + `TestFerramentasLeitura`) — 40 testes no total, todos passando

### Fase 2.6 — Exibição de Comandos na Tela Inicial (v2.6.0) ✅
- [x] Linha `Comandos: 'ajuda' | 'limpar' | 'retomar' | 'sair'` exibida no banner inicial
- [x] Comando `retomar` visível na inicialização sem necessidade de digitar `ajuda` primeiro
- [x] Logo ASCII, painel de texto e rosto do banner permanecem inalterados
- [x] README.md revisado — tabela de comandos já consistente, sem edição necessária
- [x] Validação manual: `python main.py` + `sair` confirmou o critério de aceite

### Fase 2.7 — Integração das Ferramentas de Leitura no Controller (v2.7.0) ✅
- [x] Encadeamento automático de leitura em `MariaController.enviar_mensagem` (até `MAX_PASSOS_LEITURA`)
- [x] Novo generator `_gerar_resposta_com_encadeamento` — streaming contínuo entre chamadas ao Ollama
- [x] Ferramentas de leitura executadas sem confirmação (`listar_arquivos`, `resumir_documento`)
- [x] Ferramentas de escrita preservadas — confirmação normal ao final (`get_mensagem_confirmacao` intacto)
- [x] Limite de passos respeitado com aviso amigável
- [x] Tratamento de `PermissionError`/`OSError`/`ValueError` em leitura sem derrubar a aplicação
- [x] `ui_terminal.py` intacto — interface continua iterando `(chunk, tool_chunk)` sem alteração
- [x] Validado: 40/40 testes + 3 cenários de encadeamento com mocks (leitura→escrita, leitura simples, limite)

### Fase 2.8 — Correções de Alta Prioridade e Validação de Argumentos (v2.8.0) ✅
- [x] `TOCTOU` corrigido em `core/file_utils.py` e `core/session_storage.py` via `os.makedirs(..., exist_ok=True)`
- [x] Eliminadas ocorrências do padrão perigoso `if not os.path.exists(...): os.makedirs(...)` em `core/`
- [x] Imports não utilizados removidos de `main.py`, `core/word_handler.py` e `tests/test_maria.py`
- [x] `CAMPOS_OBRIGATORIOS` e `validar_argumentos_obrigatorios()` adicionados em `core/tools_schema.py`
- [x] Chamada de validação inserida no início de `executar_ferramenta_real` antes da execução das ferramentas reais
- [x] Testes de regressão adicionados para campo obrigatório ausente e string vazia
- [x] Validado: 42/42 testes passando e compilação dos módulos afetados sem erros

### Fase 2.9 — Correções do Benchmark: Encadeamento de Leitura, Composição de Documentos e Falso Positivo (v2.9.0) ✅
- [x] Módulo compartilhado `core/tool_chaining.py` criado com `encadear_leitura_stream`
- [x] Benchmark (`MariaRunner`) encadeia leitura → escrita, reenviando o resultado ao modelo
- [x] Timeout POR CHAMADA no encadeamento de leitura (não acumulado) via `BENCHMARK_TASK_TIMEOUT`
- [x] `main.py` refatorado para delegar ao módulo compartilhado (imports diretos removidos)
- [x] Reforço de composição de documento sem conteúdo literal em `core/ollama_client.py` (Fix B)
- [x] Exceção de arquivo fictício/inexistente na regra 6 do `SYSTEM_PROMPT` (Fix D)
- [x] Validado: 75/75 testes passando e compilação dos módulos afetados sem erros

### Fase 2.10 — Configuração de Modelo Centralizada e Fallback Textual Desativável (v2.10.0) ✅
- [x] Configuração de comportamento do modelo concentrada em `core/config.py` (`OLLAMA_ENVIAR_THINK_PARAM`, `OLLAMA_THINK_HABILITADO`, `OLLAMA_TEMPERATURE_TOOLS`, `OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL`)
- [x] Novos métodos privados `_montar_options()` e `_montar_payload()` em `core/ollama_client.py`
- [x] Os 5 métodos de construção de payload usam `self._montar_payload`
- [x] Inconsistência de `temperature` corrigida em `continuar_com_resultado_ferramenta_stream`
- [x] Mensagem de erro de `_make_request` usa `self.model`/`self.base_url` dinâmicos
- [x] `model_file.txt` removido do repositório
- [x] Fallback textual de tool call desativável via `OLLAMA_USAR_FALLBACK_TEXTUAL_TOOL_CALL` nos 4 pontos
- [x] Debug scripts (`debug_raw_ollama.py`, `debug_raw_ollama_2systems.py`) usam configurações centralizadas
- [x] Validado: 80/80 testes passando e compilação sem erros

### Funcionalidades Futuras
- [ ] Preferências do usuário persistidas (próxima etapa)
- [ ] Retomada automática de sessão sem comando explícito
- [ ] Exportação de histórico em outros formatos (TXT, PDF)
- [ ] Interface gráfica ou web

---

## 🧪 Status dos Testes

| Versão | Testes | Status |
|--------|--------|--------|
| 1.0.0 | 15 | ✅ Passando |
| 2.0.0 | 22 | ✅ Passando |
| 2.1.0 | 24 | ✅ Passando |
| 2.3.0 | 26 | ✅ Passando |
| 2.4.0 | 30 | ✅ Passando |
| **2.5.0** | **40** | ✅ **Passando** |
| **2.6.0** | **40** | ✅ **Passando (sem alteração de lógica)** |
| **2.7.0** | **40** | ✅ **Passando (integração leitura no controller)** |
| **2.8.0** | **42** | ✅ **Passando (correções de alta prioridade e validação de argumentos)** |
| **2.9.0** | **75** | ✅ **Passando (correções do benchmark: encadeamento de leitura, composição de documentos e falso positivo)** |
| **2.10.0** | **80** | ✅ **Passando (configuração de modelo centralizada e fallback textual desativável)** |

**Comando:** `python -m unittest tests.test_maria -v`

**Última execução (2026-08-16):** 80/80 testes passaram.

---

## 📦 Tabela de Versões

| Versão | Data | Descrição |
|--------|------|-----------|
| 1.0.0 | - | Versão inicial da Fase 1 (cliente Ollama, sessão de chat, CLI) |
| 1.1.0 | - | Correções críticas (system prompt, Python 3.11+, config centralizada) |
| 2.0.0 | - | Máquina de estado de confirmação e execução real de arquivos |
| 2.1.0 | - | Streaming de respostas, criação de documentos Word, edição de planilhas |
| 2.2.0 | - | Sistema de benchmark e validação contínua |
| 2.3.0 | - | Reorganização de arquitetura (pacote `core/`, `tests/`) |
| 2.4.0 | 2026-08-11 | Persistência de sessões (histórico de conversa persistente) |
| **2.5.0** | **2026-08-11** | **Ferramentas de leitura: listagem e resumo de documentos** |
| **2.6.0** | **2026-08-11** | **Exibição de comandos na tela inicial (banner)** |
| **2.7.0** | **2026-08-11** | **Integração das ferramentas de leitura no controller** |
| **2.8.0** | **2026-08-11** | **Correções de alta prioridade e validação de argumentos obrigatórios** |
| **2.9.0** | **2026-08-16** | **Correções do benchmark: encadeamento de leitura, composição de documentos e falso positivo de listar_arquivos** |
| **2.10.0** | **2026-08-16** | **Configuração de modelo centralizada em `core/config.py`, `model_file.txt` removido, fallback textual desativável por modelo** |

---

## 📂 Estrutura do Projeto (v2.5.0)

```
maria/
├── main.py                     # Interface CLI principal
├── core/
│   ├── chat_session.py         # Sessão de chat (histórico, confirmação)
│   ├── config.py               # Configurações centralizadas
│   ├── excel_handler.py        # Criação/edição de planilhas Excel
│   ├── file_utils.py           # Utilitários de arquivos (inclui leitura)
│   ├── ollama_client.py        # Cliente Ollama (chat, streaming, tools)
│   ├── session_storage.py      # Persistência de sessões (v2.4.0)
│   ├── tools_schema.py         # Schemas e execução de ferramentas (5 ferramentas)
│   └── word_handler.py         # Criação de documentos Word
├── tests/
│   └── test_maria.py           # 40 testes unitários
├── benchmark/                  # Sistema de benchmark
├── docs/                       # Documentação
│   └── PROGRESSO_DESENVOLVIMENTO_V1.md  # Este arquivo
├── arquivos_gerados/           # Arquivos gerados pela MARIA
├── sessoes_salvas/             # Sessões de chat persistidas (v2.4.0)
├── ui_terminal/                # Arte de terminal
├── CHANGELOG.md                # Histórico de mudanças
├── README.md                   # Documentação principal
└── requirements.txt            # Dependências

