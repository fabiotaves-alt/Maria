# MARIA - Assistente de IA de Escritório (MVP Fase 2)
"Modelo Assistente de Raciocínio e Infêrencia Aumentada" - Proposta 
**MARIA** é uma assistente de IA de escritório que roda 100% localmente no seu computador, sem depender de conexão com a internet após a instalação do modelo.

## Visão Geral

A MARIA é uma assistente de escritório local que usa o Ollama e o modelo `qwen2.5:7b`. A versão atual implementa:

- ✅ Cliente de conexão com Ollama (API local)
- ✅ Loop de chat com histórico de contexto (últimas 12 mensagens)
- ✅ Prompt de sistema em português do Brasil com instrução anti-alucinação
- ✅ Function calling com confirmação antes da execução
- ✅ Streaming de respostas no terminal
- ✅ Criação de planilhas Excel e documentos Word reais
- ✅ Edição de planilhas existentes com sobrescrita explícita
- ✅ Sanitização de nomes para manter arquivos dentro da pasta de saída
- ✅ Listagem de arquivos e leitura/resumo de documentos de texto em pastas permitidas
- ✅ Persistência de sessões com retomada via comando `retomar`
- ✅ Testes unitários automatizados

## Pré-requisitos

Antes de rodar o projeto, certifique-se de ter:

1. **Python 3.11+** instalado
2. **Ollama** instalado e rodando
3. **Modelo Qwen2.5:7b** baixado

### Instalação do Ollama

Siga as instruções em [ollama.com](https://ollama.com) para instalar o Ollama no seu sistema.

### Instalar o Modelo

```bash
# Iniciar o servidor Ollama
ollama serve

# Em outro terminal, baixar o modelo
ollama pull qwen2.5:7b
```

### Instalar Dependências Python

```bash
pip install -r requirements.txt
```

## Estrutura do Projeto

```
maria/
├── .venv/
├── .vscode/
├── .gitignore
├── README.md
├── CHANGELOG.md
├── requirements.txt
├── main.py
├── core/
│   ├── __init__.py
│   ├── chat_session.py
│   ├── config.py
│   ├── excel_handler.py
│   ├── file_utils.py
│   ├── ollama_client.py
│   ├── session_storage.py
│   ├── tools_schema.py
│   └── word_handler.py
├── arquivos_gerados/
├── sessoes_salvas/
├── docs/
├── benchmark/
│   ├── __init__.py
│   ├── benchmark_config.py
│   ├── run_benchmark.py
│   ├── compare_runs.py
│   ├── README.md
│   ├── tasks/
│   ├── runners/
│   ├── analysis/
│   └── results/
└── tests/
    ├── __init__.py
    └── test_maria.py
```

## Como Usar

### Iniciar a Aplicação

```bash
python main.py
```

### Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `ajuda` | Mostra a lista de comandos disponíveis |
| `limpar` | Limpa o histórico da conversa atual |
| `retomar` | Retoma uma conversa salva de uma execução anterior |
| `sair` ou `exit` | Encerra a aplicação |

### Exemplos de Uso

**Conversa normal:**
```
Você: Olá, como você pode me ajudar?

MARIA: Olá! Sou a MARIA, sua assistente de escritório. Posso ajudar com tarefas administrativas, organização, redação de textos e análise de dados. Como posso ser útil hoje?
```

**Criação de arquivo com confirmação:**
```
Você: Crie uma planilha de controle de gastos

MARIA: Entendi! Vou criar uma planilha chamada "controle_gastos"...
Posso seguir com a criação? (responda sim ou não)

Você: sim

[SISTEMA] Planilha criada com sucesso: .../arquivos_gerados/controle_gastos.xlsx
```

## Funcionalidades Implementadas

### 1. Cliente Ollama (`ollama_client.py`)

- Conexão com API local do Ollama (`http://localhost:11434`)
- Verificação de conexão otimizada (apenas na primeira chamada)
- Tratamento de erros com mensagens claras para o usuário
- Suporte a function calling (tools)
- Timeout configurável para requisições
- Streaming de respostas e tool calls com tratamento de erro durante iteração
- Tipos modernos do Python 3.11+

### 2. Sessão de Chat (`chat_session.py`)

- Histórico de conversação em memória
- Limite de 12 mensagens para evitar degradação de performance (otimizado)
- System prompt fixo definindo a identidade da MARIA com instrução anti-alucinação
- **Correção crítica**: system prompt agora é enviado em toda chamada via `get_historico_com_system()`
- Métodos para limpar, serializar e restaurar sessões

### 3. Prompt de Sistema

O system prompt define que a MARIA:

- Responde sempre em português do Brasil
- É objetiva e focada em produtividade de escritório
- **Nunca inventa informações sobre o usuário** (instrução anti-alucinação)
- Usa as ferramentas de planilha e documento disponíveis após confirmação do usuário
- Não depende de internet para funcionar

### 4. Function Calling (`tools_schema.py`)

Cinco ferramentas disponíveis. As três de **escrita** são executadas somente após confirmação explícita; as duas de **leitura** são executadas imediatamente (somente leitura, não modificam nada):

| Ferramenta | Descrição |
|------------|-----------|
| `criar_planilha` | Cria planilha Excel com dados tabulares estruturados em colunas (ex: controle financeiro, inventários) |
| `editar_planilha` | Sobrescreve uma planilha existente com novas colunas e linhas opcionais |
| `criar_documento` | Cria documento Word com título e conteúdo narrativo em parágrafos |
| `listar_arquivos` | Lista os arquivos de uma pasta permitida (somente leitura) |
| `resumir_documento` | Lê um documento de texto existente para resumo/análise (somente leitura) |

### 5. Interface CLI (`main.py`)

- Loop de chat interativo no terminal
- Detecção de tool calls e confirmação antes da execução
- Registro do resultado de ações confirmadas no histórico
- Comandos especiais (ajuda, limpar, retomar, sair/exit)
- Retomada de sessões salvas de execuções anteriores via comando `retomar`
- Mensagens de erro amigáveis
- Tratamento de encoding UTF-8 para Windows

### 6. Configuração Centralizada (`config.py`)

- URL base do Ollama
- Nome do modelo
- Timeout das requisições
- Máximo de mensagens no histórico
- Nível de logging
- Pasta de saída via `PASTA_ARQUIVOS_GERADOS` (padrão: `arquivos_gerados`)
- Pasta de sessões salvas via `PASTA_SESSOES` (padrão: `sessoes_salvas`)
- Lista de pastas permitidas para leitura via `PASTAS_PERMITIDAS` (padrão: mesma pasta de `PASTA_ARQUIVOS_GERADOS`)

### 7. Testes Unitários (`tests/test_maria.py`)

- 40 testes cobrindo sessão, ferramentas, arquivos reais, sanitização, streaming, persistência de sessões e leitura de documentos
- Executar com: `python -m unittest tests.test_maria -v`

## Critérios de Aceite

- [x] Sistema roda sem chamadas de rede externas (exceto localhost/Ollama)
- [x] Histórico de conversa mantido corretamente entre turnos
- [x] Modelo responde consistentemente em português (via system prompt)
- [x] Intenção de function calling é identificada (ex: "crie uma planilha...")
- [x] Erros de conexão com Ollama tratados com mensagens claras
- [x] System prompt enviado em toda chamada ao modelo
- [x] Código compatível com Python 3.11+ com tipos modernos
- [x] Testes unitários passando

## Próximos Passos

Integração de voz com Whisper.cpp permanece como recurso futuro. A execução atual é feita por texto na interface CLI.

## Solução de Problemas

### Erro: "Não foi possível conectar ao Ollama"

1. Verifique se o Ollama está rodando:
   ```bash
   ollama serve
   ```

2. Verifique se o modelo está instalado:
   ```bash
   ollama list
   # Se não aparecer qwen2.5:7b, execute:
   ollama pull qwen2.5:7b
   ```

3. Teste a conexão manualmente:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Erro: "requests não está instalada"

```bash
pip install -r requirements.txt
```

### Erro de encoding no Windows

O projeto já inclui tratamento para UTF-8 no `main.py` com `sys.stdout.reconfigure(encoding="utf-8")` e fallback silencioso para versões antigas do Python. Se persistir, execute em um terminal com encoding UTF-8:

```cmd
chcp 65001
python main.py
```

### Respostas lentas do modelo

Isso é normal para modelos rodando localmente. O tempo de resposta depende:
- Hardware do seu computador (CPU/GPU)
- Quantidade de RAM disponível
- Complexidade da pergunta

## Executar Testes

```bash
python -m unittest tests.test_maria -v
```

### Benchmark

O sistema de benchmark live mede tool calling, confirmação, execução, erros, latência e conformidade de idioma usando o Ollama local. O relatório gerado inclui a taxa de conformidade de idioma (`language_compliance_rate`) nas respostas finais.

```bash
python -m benchmark.run_benchmark --tasks 25
python -m benchmark.run_benchmark --task-ids 1 2 3
python -m benchmark.run_benchmark --category criar_planilha
```

Consulte o [README do benchmark](benchmark/README.md) para comparar execuções e adicionar tarefas. O benchmark exige `ollama serve` e o modelo `qwen2.5:7b` instalado.

## Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para o histórico completo de mudanças.

## Licença

Projeto em desenvolvimento. Todos os direitos reservados.

---

**MARIA** - Sua assistente de escritório com IA local, segura e em português do Brasil.
