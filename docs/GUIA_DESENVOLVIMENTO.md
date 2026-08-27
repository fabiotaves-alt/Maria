# Guia de Desenvolvimento — MARIA

**Versão:** v2.13.0  
**Última atualização:** 2026-08-24

Este documento serve como guia prático para novos desenvolvedores e para as próximas fases de desenvolvimento do projeto MARIA.

---

## 1. Configuração do Ambiente

### Pré-requisitos

| Requisito | Versão | Observação |
|-----------|--------|------------|
| Python | 3.11+ | Ambiente virtual na raiz (`.venv/`) |
| Ollama | atual | [ollama.com](https://ollama.com) |
| **Modelo LLM** | **qwen3.5:4b** | `ollama pull qwen3.5:4b` |
| JDK | 21 | OpenJDK/Temurin |
| Maven | 3.9+ | ou wrapper da IDE |

### Instalação Passo a Passo

```bash
# 1. Clonar o repositório
git clone <repo-url>
cd maria

# 2. Ambiente Python (na raiz do monorepo)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Ollama + modelo
ollama serve
ollama pull qwen3.5:4b

# 5. Configurar variáveis de ambiente (opcional)
# Copie backend/.env.example para backend/.env e ajuste se necessário
```

### Execução do Projeto

#### Backend (Python)

```bash
# Modo bridge (usado pelo frontend JavaFX)
.venv\Scripts\python.exe backend\main.py --bridge

# Modo CLI (terminal interativo)
.venv\Scripts\python.exe backend\main.py
```

#### Frontend (JavaFX)

```bash
cd frontend
mvn clean compile
mvn javafx:run
```

> ⚠️ **Nota:** A compilação/execução real requer JDK 21 + Maven instalados. Alternativamente, use IntelliJ IDEA com Maven integrado.

#### Testes

```bash
# Da raiz do monorepo
.venv\Scripts\python.exe -m pytest backend/tests/test_maria.py -v

# Ou via unittest
.venv\Scripts\python.exe -m unittest backend.tests.test_maria
```

---

## 2. Arquitetura do Sistema

Para detalhes completos da arquitetura, consulte [`docs/ARQUITETURA_SISTEMA.md`](ARQUITETURA_SISTEMA.md).

Resumo:

```
┌─────────────────────────┐   JSON-lines    ┌──────────────────────────┐
│  Frontend JavaFX        │ ◄────────────► │  Backend Python          │
│  (com.tristar.maria)    │   stdin/stdout │  (Ollama + ferramentas)  │
│  Java 21 / Maven        │                │  Python 3.11+            │
└─────────────────────────┘                └──────────┬───────────────┘
                                                      │ HTTP localhost
                                                ┌─────▼─────┐
                                                │  Ollama   │
                                                │ qwen3.5:4b│
                                                └───────────┘
```

---

## 3. Roadmap de Médio Prazo

### Ação 1: Fine-tuning (Opcional, mas Recomendado)

**Descrição:** Realizar fine-tuning LoRA do `qwen3.5:4b` com dados em português para tarefas de escritório (planilhas, documentos) para aumentar a precisão e reduzir alucinações.

**Ferramentas sugeridas:**
- PEFT (Parameter-Efficient Fine-Tuning)
- Transformers (Hugging Face)
- Datasets em português (criar corpus próprio ou usar datasets públicos)

**Passos gerais:**
1. Coletar/criar dataset de instruções em pt-BR para tarefas de escritório
2. Configurar ambiente com `peft`, `transformers`, `accelerate`
3. Treinar adapter LoRA no modelo base `qwen3.5:4b`
4. Avaliar resultados e integrar ao backend (carregar adapter junto com o modelo)

**Prioridade:** Média  
**Esforço estimado:** 2–4 semanas

---

### Ação 2: Implementação de Funcionalidades Reais (Substituir Mockups)

Atualmente, vários elementos da interface estão mockados. Esta ação visa conectar a interface a dados e funcionalidades reais.

#### 2.1 Recursos do Sistema (CPU/RAM/GPU)

**Onde:** Sidebar → card "RECURSOS DO SISTEMA"  
**Situação atual:** Valores fixos de exemplo (42/61/18%)

**Implementação:**
- **Java (frontend):** Usar `com.sun.management.OperatingSystemMXBean` para CPU e RAM
- **GPU:** Não é exposta de forma portátil pelo JDK; considerar:
  - Comando bridge `status` no backend Python para coletar via `pynvml` (NVIDIA) ou `pyamdsmi` (AMD)
  - Ou manter mockado se não for crítico

**Arquivos envolvidos:**
- `frontend/src/main/java/com/tristar/maria/ui/MainController.java`
- `backend/main.py` (adicionar comando `status`)

#### 2.2 Ações Rápidas (Hero Central)

**Onde:** 4 botões no hero central ("Analisar Documento", "Analisar Dados", etc.)  
**Situação atual:** Ao clicar, preenchem o campo de mensagem do chat com prompt pré-definido

**Implementação real:**
1. Abrir seletor de arquivos (`FileChooser` do JavaFX)
2. Ler arquivo selecionado
3. Enviar para o backend via bridge (comando `chat` com anexo ou comando específico)
4. Backend processa via tools (excel_handler, word_handler, etc.)

**Arquivos envolvidos:**
- `frontend/src/main/java/com/tristar/maria/ui/HeroController.java`
- `frontend/src/main/resources/com/tristar/maria/hero-view.fxml`
- `backend/core/tools_schema.py` (se necessário novo tool)

#### 2.3 Voz (Whisper.cpp)

**Onde:** Botão 🎤 no input do chat  
**Situação atual:** Desabilitado (opacidade 0.4, mouseTransparent)

**Implementação:**
1. Integrar Whisper.cpp (ou biblioteca Java equivalente) no frontend ou backend
2. Capturar áudio do microfone
3. Transcrever para texto
4. Inserir texto transcrito no campo de mensagem

**Arquivos envolvidos:**
- `frontend/src/main/resources/com/tristar/maria/conversar-view.fxml`
- `frontend/src/main/java/com/tristar/maria/ui/ConversarController.java`
- Possível novo módulo `backend/core/speech_to_text.py`

**Prioridade:** Alta (Ação 2)  
**Esforço estimado:** 3–5 semanas

---

### Ação 3: Integração com Banco de Dados

**Descrição:** Implementar schema do banco de dados SQLite com 6 tabelas e camada de persistência.

**Tabelas previstas:**
1. `conversas` — sessões de conversa
2. `mensagens` — mensagens individuais (vinculadas a conversas)
3. `memoria` — memória de longo prazo / RAG
4. `arquivos_indexados` — metadados de arquivos processados
5. `automacoes` — automações salvas
6. `configuracoes` — preferências do usuário

**Passos:**

1. **Backend: Criar `database/schema.py`**
   ```python
   # backend/database/schema.py
   def init_db():
       """Cria as tabelas se não existirem."""
       # DDL das 6 tabelas
   ```

2. **Backend: Chamar `init_db()` no startup**
   ```python
   # backend/main.py
   from database.schema import init_db
   
   if __name__ == "__main__":
       init_db()
       # ... resto do código
   ```

3. **Frontend: Criar camadas DAO em Java**
   - Classes modelo: `Conversa`, `Mensagem`, `Memoria`, etc.
   - DAOs: `ConversaDAO`, `MensagemDAO`, etc.
   - Integration com `BridgeManager` ou serviço dedicado

4. **Decisões pendentes:** Consulte [`docs/DECISOES_BANCO_DADOS.md`](DECISOES_BANCO_DADOS.md) antes de implementar.

**Prioridade:** Alta (bloqueada por decisões)  
**Esforço estimado:** 2–3 semanas

---

## 4. Estrutura de Pastas (Atualizada)

```
maria/
├── README.md                  ← este arquivo (documentação geral)
├── requirements.txt           ← dependências Python consolidadas
├── .venv/                     ← ambiente virtual Python (raiz)
├── docs/                      ← documentação técnica
│   ├── ARQUITETURA_SISTEMA.md      ← arquitetura real (ATIVO)
│   ├── GUIA_DESENVOLVIMENTO.md     ← este arquivo (ATIVO)
│   ├── RELATORIO_ESTADO_ATUAL.md   ← estado atual (ATIVO)
│   ├── PENDENCIAS_INTERFACE.md     ← pendências de UI (ATIVO)
│   ├── DECISOES_BANCO_DADOS.md     ← decisões pendentes de DB (ATIVO)
│   └── archive/                    ← documentos legados
│       ├── ARQUITETURA_REAL_SISTEMA.md
│       └── RELATORIO_ACOMPANHAMENTO.md
├── shared/                    ← banco SQLite compartilhado (maria.db)
├── backend/
│   ├── main.py                ← CLI + modo --bridge
│   ├── ui_terminal.py         ← interface de terminal legada
│   ├── core/                  ← ollama_client, tools_schema, handlers
│   ├── database/              ← connection.py, schema.py (futuro)
│   ├── tests/test_maria.py    ← suíte de testes
│   ├── CHANGELOG.md           ← changelog do backend
│   └── README.md              ← documentação do backend
└── frontend/
    ├── pom.xml                ← Maven (Java 21, JavaFX 21)
    └── src/main/
        ├── java/com/tristar/maria/
        │   ├── App.java             ← entry point JavaFX
        │   ├── bridge/              ← PythonBridgeService
        │   └── ui/                  ← controllers das 8 abas
        └── resources/com/tristar/maria/
            ├── *.fxml               ← views
            └── theme-*.css          ← temas
```

---

## 5. Contribuição

### Padrões de Código

- **Python:** PEP 8, type hints quando aplicável
- **Java:** Convenções Oracle Java, JavaFX best practices
- **Commits:** Mensagens claras e descritivas (preferencialmente em português)

### Fluxo de Trabalho Sugerido

1. Criar branch feature (`feature/nome-da-feature`)
2. Implementar mudanças
3. Rodar testes (`pytest` + compilar frontend)
4. Commit com mensagem descritiva
5. Pull Request para review

---

## 6. Links Úteis

- [Documentação Ollama](https://ollama.com/)
- [JavaFX Documentation](https://openjfx.io/)
- [PEFT Library](https://huggingface.co/docs/peft)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)

---

**Dúvidas?** Consulte a documentação ativa em `docs/` ou abra uma issue no repositório.
