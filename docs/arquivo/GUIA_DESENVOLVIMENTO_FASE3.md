# Guia de Desenvolvimento — Fase 3: Integração Backend-Frontend e Ferramentas

**Versão:** v3.0.0  
**Data:** 2026-08-27  
**Status:** 🟢 Pronto para execução  
**Escopo:** Integração completa backend-frontend e implementação das ferramentas pendentes

---

## 1. Visão Geral da Fase 3

Esta fase marca a transição do **MVP funcional** (v2.x) para o **produto completo integrado**. O backend já possui todas as funcionalidades core implementadas e testadas, e o frontend tem a interface completa com navegação e bridge operacional. Agora focamos em:

1. **Integração profunda** entre frontend JavaFX e backend Python
2. **Implementação das ferramentas pendentes** (banco de dados, memória, automações)
3. **Refinamento da experiência do usuário** (avatar, persistência, notificações)

---

## 2. Estado Atual do Sistema (Resumo Executivo)

### ✅ Funcionalidades Completas (v2.14.0)

| Camada | Componente | Status | Observação |
|--------|-----------|--------|------------|
| **Backend Core** | Ollama client, chat session, tools schema | ✅ 100% | 86/86 testes passando |
| **Backend Bridge** | Modo `--bridge`, comandos ping/chat/status | ✅ 100% | Protocolo JSON-lines validado |
| **Backend Tools** | Excel handler, Word handler, file utils | ✅ 100% | Geração real de arquivos |
| **Backend Comandos** | `status`, `upload_arquivo`, `transcrever_audio` | ✅ 100% | Integrados no main.py |
| **Frontend UI** | 8 abas, sidebar, topbar, hero, chat panel | ✅ 100% | Design v2.14.0 implementado |
| **Frontend Bridge** | BridgeManager, PythonBridgeService | ✅ 100% | Singleton injetável |
| **Frontend Chat** | ConversarController integrado | ✅ 100% | Ping/chat/anexar/voz funcionais |
| **Frontend Recursos** | CPU/RAM/GPU via comando status | ✅ 100% | Dados reais do psutil/pynvml |

### 🔒 Bloqueios/Pendências

| # | Pendência | Prioridade | Bloqueio | Ação Necessária |
|---|-----------|-----------|----------|-----------------|
| 1 | **Banco de dados (schema)** | 🔴 Alta | Decisões pendentes | Responder `docs/DECISOES_BANCO_DADOS.md` |
| 2 | **Avatar nas bolhas de chat** | 🟡 Média | Imagem não existe | Criar `maria-avatar-circle.png` |
| 3 | **Whisper.cpp empacotado** | 🟡 Média | Binário externo | Documentar ou empacotar |
| 4 | **Memória entre sessões** | 🟡 Média | Depende do banco | Unificar com tabela `memoria` |
| 5 | **Automações salvas** | 🟢 Baixa | Depende do banco | Implementar após schema |
| 6 | **Persistência de tema** | 🟢 Baixa | Independente | SharedPreferences em Java |

---

## 3. Arquitetura de Integração

### 3.1 Fluxo de Comunicação

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend JavaFX                           │
│  ┌────────────┐    ┌─────────────┐    ┌──────────────────┐  │
│  │ Controllers│───►│ BridgeMgr   │───►│ PythonBridgeSvc  │  │
│  │ (8 abas)   │◄───│ (Singleton) │◄───│ (Processo Python)│  │
│  └────────────┘    └─────────────┘    └─────────┬────────┘  │
└─────────────────────────────────────────────────┼────────────┘
                                                  │ stdin/stdout
                                                  ▼
┌──────────────────────────────────────────────────────────────┐
│                   Backend Python                             │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐  │
│  │ main.py     │───│ MariaCtrl    │───│ OllamaClient     │  │
│  │ (--bridge)  │   │ (Tools, Sess)│   │ (qwen3.5:4b)     │  │
│  └─────────────┘   └──────────────┘   └──────────────────┘  │
│         │                  │                                  │
│         ▼                  ▼                                  │
│  ┌─────────────┐   ┌──────────────┐                          │
│  │ DB Schema   │   │ File Utils   │                          │
│  │ (SQLite)    │   │ (Excel,Word) │                          │
│  └─────────────┘   └──────────────┘                          │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Protocolo Bridge (Comandos Suportados)

| Comando | Direção | Payload | Resposta | Implementado |
|---------|---------|---------|----------|--------------|
| `ping` | Java→Py | `{}` | `{"dados": "pong"}` | ✅ |
| `chat` | Java→Py | `{"mensagem": "..."}` | `{"dados": "resposta"}` | ✅ |
| `encerrar` | Java→Py | `{}` | `{"dados": "encerrando"}` | ✅ |
| `status` | Java→Py | `{}` | `{"cpu": x, "ram": y, "gpu": z, "modelo": "..."}` | ✅ |
| `upload_arquivo` | Java→Py | `{"caminho": "/path"}` | `{"dados": "copiado para: ..."}` | ✅ |
| `transcrever_audio` | Java→Py | `{"caminho": "/path.wav"}` | `{"dados": "texto transcrito"}` | ✅ |
| `analisar_arquivo` | Java→Py | `{"caminho": "/path.xlsx"}` | `{"dados": "resumo"}` | ✅ |
| `analisar_dados` | Java→Py | `{"caminho": "/path.xlsx"}` | `{"dados": "estatísticas"}` | ✅ |
| `limpar_conversa` | Java→Py | `{}` | `{"dados": "ok"}` | ⏳ Pendente |
| `exportar_conversa` | Java→Py | `{"formato": "txt"}` | `{"dados": "arquivo salvo"}` | ⏳ Pendente |
| `listar_sessoes` | Java→Py | `{}` | `{"dados": ["sessao1", ...]}` | ⏳ Pendente |
| `carregar_sessao` | Java→Py | `{"nome": "sessao1"}` | `{"dados": [...]}` | ⏳ Pendente |
| `salvar_memoria` | Java→Py | `{"fato": "..."}` | `{"dados": "ok"}` | ⏳ Pendente (DB) |
| `listar_memoria` | Java→Py | `{}` | `{"dados": [...]}` | ⏳ Pendente (DB) |
| `criar_automacao` | Java→Py | `{"nome": "...", "passos": [...]}` | `{"dados": "ok"}` | ⏳ Pendente (DB) |

---

## 4. Tarefas de Desenvolvimento

### 4.1 Banco de Dados (Prioridade 🔴 Alta)

#### Passo 1: Responder Decisões Pendentes

Antes de codificar, responda às perguntas em `docs/DECISOES_BANCO_DADOS.md`:

```markdown
1. Quem usa o banco? (frontend, backend ou ambos?)
2. As 6 tabelas ainda refletem a necessidade real?
3. Unificação com "Memória entre sessões"?
4. O que alimenta `arquivos_indexados`?
```

#### Passo 2: Criar Schema do Banco

**Arquivo:** `backend/database/schema.py`

```python
"""
Schema do banco de dados MARIA — SQLite compartilhado.

Tabelas:
- conversas: sessões de conversa (histórico)
- mensagens: mensagens individuais (vinculadas a conversas)
- memoria: fatos persistentes sobre o usuário (RAG)
- arquivos_indexados: metadados de arquivos processados
- automacoes: automações salvas pelo usuário
- configuracoes: preferências (tema, modelo, etc.)
"""

from backend.database.connection import get_connection


def init_db():
    """Cria as tabelas se não existirem."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversa_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            conteudo TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversa_id) REFERENCES conversas(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fato TEXT NOT NULL UNIQUE,
            categoria TEXT,
            relevancia REAL DEFAULT 1.0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos_indexados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caminho TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL,
            tamanho_bytes INTEGER,
            indexado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS automacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            descricao TEXT,
            passos_json TEXT NOT NULL,
            ativo BOOLEAN DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("✅ Banco de dados inicializado com sucesso!")
```

#### Passo 3: Chamar `init_db()` no Startup

**Arquivo:** `backend/main.py`

Adicionar no início do `modo_bridge()`:

```python
def _modo_bridge(modelo: str | None = None):
    from backend.database.schema import init_db
    
    # Inicializar banco de dados
    try:
        init_db()
        logger.info("Banco de dados inicializado")
    except Exception as e:
        logger.warning(f"Falha ao inicializar DB: {e}")
    
    controller = MariaController(modelo=modelo)
    # ... resto do código
```

#### Passo 4: Criar DAOs em Java (Frontend)

**Pacote:** `com.tristar.maria.database`

Criar classes:
- `Conversa.java` (modelo)
- `Mensagem.java` (modelo)
- `Memoria.java` (modelo)
- `DatabaseManager.java` (singleton JDBC)
- `ConversaDAO.java`, `MensagemDAO.java`, `MemoriaDAO.java`

Exemplo `DatabaseManager.java`:

```java
package com.tristar.maria.database;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class DatabaseManager {
    private static final String DB_URL = "jdbc:sqlite:../shared/maria.db";
    private static DatabaseManager instance;
    
    private DatabaseManager() {}
    
    public static synchronized DatabaseManager getInstance() {
        if (instance == null) {
            instance = new DatabaseManager();
        }
        return instance;
    }
    
    public Connection getConnection() throws SQLException {
        return DriverManager.getConnection(DB_URL);
    }
}
```

---

### 4.2 Avatar nas Bolhas de Chat (Prioridade 🟡 Média)

#### Passo 1: Criar Imagem do Avatar

**Ação:** Criar arquivo `frontend/src/main/resources/com/tristar/maria/images/maria-avatar-circle.png`

- Tamanho recomendado: 72x72 pixels (para alta resolução)
- Formato: PNG com transparência
- Estilo: Círculo perfeito (ou fornecer máscara CSS)

#### Passo 2: Atualizar `ConversarController.java`

**Método:** `criarAvatarMaria()`

```java
private Node criarAvatarMaria() {
    // Tentar carregar imagem circular
    java.net.URL recurso = getClass().getResource("/com/tristar/maria/images/maria-avatar-circle.png");
    if (recurso != null) {
        ImageView avatar = new ImageView(new Image(recurso.toExternalForm()));
        avatar.setFitWidth(36);
        avatar.setFitHeight(36);
        avatar.setPreserveRatio(true);
        
        // Recortar em círculo
        Circle clip = new Circle(18, 18, 18);
        avatar.setClip(clip);
        
        return avatar;
    }
    
    // Fallback: label "M" estilizado
    Label circ = new Label("M");
    circ.getStyleClass().add("avatar");
    Label nome = new Label("Maria");
    nome.getStyleClass().add("avatar-chat-nome");
    HBox cont = new HBox(6, circ, nome);
    cont.setAlignment(Pos.CENTER_LEFT);
    return cont;
}
```

---

### 4.3 Whisper.cpp Empacotado (Prioridade 🟡 Média)

#### Opção A: Documentar Instalação Manual

**Arquivo:** `docs/INSTALACAO_WHISPER.md`

```markdown
# Instalação do Whisper.cpp para Transcrição de Voz

O MARIA usa whisper.cpp para transcrição local de áudio. Siga os passos:

## Windows

1. Baixe o binário pré-compilado: https://github.com/ggerganov/whisper.cpp/releases
2. Extraia e copie `whisper-main.exe` para `C:\Program Files\maria\bin\`
3. Adicione ao PATH ou defina variável de ambiente:
   ```
   setx WHISPER_BIN "C:\Program Files\maria\bin\whisper-main.exe"
   ```

## Linux/Mac

```bash
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
sudo cp whisper-main /usr/local/bin/
```

## Teste

```bash
whisper-main -f teste.wav -otxt -of saida
cat saida.txt
```
```

#### Opção B: Empacotar Binário com Instalador

- Incluir `whisper-main.exe` no instalador Windows
- Detectar arquitetura (x64/ARM64)
- Copiar para pasta de instalação
- Configurar PATH automaticamente

---

### 4.4 Comandos Bridge Pendentes (Prioridade 🟡 Média)

#### Comando: `limpar_conversa`

**Backend (`main.py`):**

```python
elif comando == "limpar_conversa":
    controller.sessao.limpar_historico()
    _responder_bridge(identificador, "ok", dados="conversa limpa")
```

**Frontend (`ConversarController.java`):**

Já implementado no dropdown (método `limparConversa()`), mas pode chamar o backend para sincronização.

#### Comando: `exportar_conversa`

**Backend (`main.py`):**

```python
elif comando == "exportar_conversa":
    formato = payload.get("formato", "txt")
    from backend.core.session_storage import exportar_sessao
    
    try:
        arquivo_saida = exportar_sessao(controller.sessao, formato=formato)
        _responder_bridge(identificador, "ok", dados=f"Exportado: {arquivo_saida}")
    except Exception as e:
        _responder_bridge(identificador, "erro", mensagem_erro=str(e))
```

#### Comando: `listar_sessoes` / `carregar_sessao`

**Backend (`main.py`):**

```python
elif comando == "listar_sessoes":
    from backend.core.session_storage import listar_sessoes_salvas
    sessoes = listar_sessoes_salvas()
    _responder_bridge(identificador, "ok", dados=sessoes)

elif comando == "carregar_sessao":
    nome = payload.get("nome", "")
    from backend.core.session_storage import carregar_sessao
    
    try:
        sessao = carregar_sessao(nome)
        # Converter sessão para formato serializável
        mensagens = [{"role": m["role"], "conteudo": m["content"]} 
                     for m in sessao.historico]
        _responder_bridge(identificador, "ok", dados=mensagens)
    except Exception as e:
        _responder_bridge(identificador, "erro", mensagem_erro=str(e))
```

**Frontend (`ConversarController.java`):**

Adicionar método `carregarHistorico()`:

```java
@FXML
private void carregarHistorico() {
    try {
        BridgeManager.getInstance().enviar("listar_sessoes", Map.of())
            .thenAccept(resposta -> Platform.runLater(() -> {
                if ("ok".equals(resposta.getStatus())) {
                    List<String> sessoes = (List<String>) resposta.getDados();
                    // Mostrar dropdown com sessões disponíveis
                    mostrarSelecaoSessoes(sessoes);
                }
            }));
    } catch (IOException e) {
        // Tratar erro
    }
}
```

---

### 4.5 Persistência de Tema (Prioridade 🟢 Baixa)

**Frontend (`MainController.java` ou `ConfiguracoesController.java`):**

```java
// Salvar preferência
private void salvarTema(boolean escuro) {
    Preferences prefs = Preferences.userNodeForPackage(App.class);
    prefs.putBoolean("tema_escuro", escuro);
}

// Carregar preferência
private boolean carregarTemaSalvo() {
    Preferences prefs = Preferences.userNodeForPackage(App.class);
    return prefs.getBoolean("tema_escuro", true); // padrão: escuro
}
```

**Backend (`configuracoes` table):**

Sincronizar preferência com banco:

```python
# Salvar no banco
cursor.execute("""
    INSERT OR REPLACE INTO configuracoes (chave, valor, atualizado_em)
    VALUES ('tema_escuro', ?, CURRENT_TIMESTAMP)
""", ("true" if escuro else "false"))
```

---

## 5. Roadmap de Implementação

### Semana 1-2: Banco de Dados
- [ ] Responder decisões pendentes
- [ ] Criar `schema.py` com DDL das 6 tabelas
- [ ] Chamar `init_db()` no startup
- [ ] Criar DAOs em Java
- [ ] Testar CRUD básico

### Semana 3: Integração Chat/Histórico
- [ ] Comando `listar_sessoes`
- [ ] Comando `carregar_sessao`
- [ ] Comando `limpar_conversa`
- [ ] Comando `exportar_conversa`
- [ ] UI de seleção de histórico

### Semana 4: Refinamentos de UI
- [ ] Avatar circular nas bolhas
- [ ] Persistência de tema
- [ ] Notificações nativas (Toast)
- [ ] Animações de transição

### Semana 5: Voz e Áudio
- [ ] Documentar whisper.cpp
- [ ] Testar transcrição com múltiplos formatos
- [ ] Melhorar UX de gravação (timer, visualização)

### Semana 6-8: Automações e Memória
- [ ] Comando `salvar_memoria`
- [ ] Comando `listar_memoria`
- [ ] Comando `criar_automacao`
- [ ] UI de gerenciamento de automações
- [ ] Execução automática de automações

---

## 6. Padrões de Código

### Python (Backend)

```python
# Type hints obrigatórios
def processar_comando(comando: str, payload: dict) -> dict:
    ...

# Docstrings em todas as funções públicas
"""
Descrição da função.

Args:
    arg1: Descrição do argumento
    
Returns:
    Descrição do retorno
"""

# Logging adequado
logger.info("Operação concluída")
logger.error(f"Erro: {error}")
```

### Java (Frontend)

```java
// Javadoc em métodos públicos
/**
 * Envia comando para o backend.
 * 
 * @param comando nome do comando
 * @param payload dados da requisição
 * @return CompletableFuture com resposta
 */
public CompletableFuture<Resposta> enviar(String comando, Map payload) { ... }

//FXML injection com @FXML
@FXML private VBox areaMensagens;

// Thread safety com Platform.runLater
Platform.runLater(() -> atualizarUI());
```

---

## 7. Testes

### Backend (Python)

```bash
# Testes unitários
.venv\Scripts\python.exe -m pytest backend/tests/test_maria.py -v

# Teste manual do bridge
echo {"id":"1","comando":"ping"} | .venv\Scripts\python.exe backend\main.py --bridge
```

### Frontend (Java)

```bash
# Compilação
cd frontend
mvn clean compile

# Execução
mvn javafx:run

# Testes (quando implementados)
mvn test
```

---

## 8. Checklist de Validação

Antes de considerar a Fase 3 completa:

- [ ] Banco de dados criado e populado
- [ ] Todas as 8 abas com funcionalidade real (não mockada)
- [ ] Histórico de conversas persistido e carregável
- [ ] Avatar da Maria visível nas bolhas
- [ ] Transcrição de voz funcional (com whisper.cpp)
- [ ] Tema claro/escuro persistente entre sessões
- [ ] Exportação de conversas em TXT
- [ ] Memória de longo prazo operacional
- [ ] Pelo menos 1 automação criada e executada
- [ ] Documentação atualizada

---

## 9. Links Úteis

- [Documentação Ollama](https://ollama.com/)
- [JavaFX Documentation](https://openjfx.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- [psutil](https://psutil.readthedocs.io/)
- [pynvml](https://pypi.org/project/pynvml/)

---

**Próximos Passos Imediatos:**

1. Responder perguntas em `docs/DECISOES_BANCO_DADOS.md`
2. Criar `backend/database/schema.py`
3. Criar imagem `maria-avatar-circle.png`
4. Documentar instalação do whisper.cpp

**Dúvidas?** Consulte a documentação ativa em `docs/` ou abra uma issue no repositório.
