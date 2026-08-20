# Integração Frontend (JavaFX) + Backend (Python) — MARIA

## Estrutura do Monorepo

```
maria/
├── .venv/                          ← Ambiente virtual Python (raiz, não backend/venv)
├── .gitignore
├── docs/
│   └── INTEGRACAO_FRONTEND.md      ← Este documento
├── shared/                         ← Banco de dados SQLite compartilhado
│   └── .gitkeep
├── backend/                        ← Backend Python (CLI + modo bridge)
│   ├── main.py                     ← Suporta --bridge (JSON por linha)
│   ├── core/
│   ├── tests/
│   └── requirements.txt
└── frontend/                       ← Frontend JavaFX (Maven)
    ├── pom.xml
    └── src/main/java/com/tristar/maria/
        ├── App.java                ← Janela JavaFX + integração
        └── bridge/
            ├── Requisicao.java
            ├── Resposta.java
            └── PythonBridgeService.java
```

## Protocolo Bridge (JavaFX ↔ Python)

O frontend inicia o backend com:

```
../.venv/Scripts/python.exe ../backend/main.py --bridge
```

O processo Python lê uma linha JSON por vez do stdin e responde JSON por linha no stdout:

**Requisição (Java → Python):**
```json
{"id": "1", "comando": "ping", "payload": null}
{"id": "2", "comando": "chat", "payload": {"mensagem": "Olá"}}
{"id": "3", "comando": "encerrar", "payload": null}
```

**Resposta (Python → Java):**
```json
{"id": "1", "status": "ok", "dados": "pong", "mensagemErro": null}
{"id": "2", "status": "ok", "dados": "texto da resposta", "mensagemErro": null}
{"id": "3", "status": "ok", "dados": "encerrando", "mensagemErro": null}
```

### Comandos suportados

| Comando | Payload | Resposta |
|---------|---------|----------|
| `ping` | — | `{"status": "ok", "dados": "pong"}` |
| `chat` | `{"mensagem": "..."}` | `{"status": "ok", "dados": "resposta"}` |
| `encerrar` | — | `{"status": "ok", "dados": "encerrando"}` e encerra |

## Decisões tomadas (divergências do guia original)

| Item | Guia original | Implementado | Motivo |
|------|--------------|--------------|--------|
| Pacote Java | `com.nyc.maria` | `com.tristar.maria` | Manter consistência com código existente |
| Jackson | `2.17.2` | `2.22.2` | Manter versão já resolvida no Maven (não corrigir, documentar) |
| venv | `backend/venv/` | `.venv/` (raiz) | O venv já existe na raiz do monorepo; nenhuma mudança necessária |
| `database/` | `backend/database/` | não criado | Backend não usa banco próprio; banco compartilhado em `shared/` |
| Classe App | `com.nyc.maria.App` | `com.tristar.maria.App` | Ajustado ao pacote escolhido |

## Como executar

### Frontend (JavaFX)

```
cd frontend
mvn javafx:run
```

A janela é iniciada a partir de `frontend/`, portanto os caminhos relativos no `App.java`:
- Python: `../.venv/Scripts/python.exe`
- Script: `../backend/main.py`

### Backend (CLI interativa — inalterado)

```
.venv\Scripts\python.exe backend\main.py
```

### Backend (modo bridge — usado pelo frontend)

```
.venv\Scripts\python.exe backend\main.py --bridge
```

## Teste manual do bridge

```bash
echo {"id":"1","comando":"ping"} | .venv\Scripts\python.exe backend\main.py --bridge
```

Resposta esperada:

```json
{"id": "1", "status": "ok", "dados": "pong", "mensagemErro": null}
```

## Observações

- O backend `main.py` com `--bridge` inicializa o `MariaController` (exige Ollama rodando para `chat`, mas `ping` responde sem Ollama).
- O modo CLI original (sem `--bridge`) permanece 100% preservado.
- O `main.py` agora insere a raiz do monorepo (`Path(__file__).resolve().parent.parent`) no `sys.path`, garantindo que `from backend.core.config import ...` funcione ao executar como script direto (`python backend/main.py --bridge`).
- `frontend/maria-frontend/` (subpasta antiga) foi movida para `frontend/`. Se ainda houver uma pasta vazia residual presa por um processo, remova manualmente (no Windows, pode ser necessário fechar o Explorer/IntelliJ que esteja com ela aberta).

## Handshake ping/pong — teste manual executado e validado

```bash
echo {"id":"1","comando":"ping"} | .venv\Scripts\python.exe backend\main.py --bridge
```

Resultado obtido:

```json
{"id": "1", "status": "ok", "dados": "pong", "mensagemErro": null}
```
