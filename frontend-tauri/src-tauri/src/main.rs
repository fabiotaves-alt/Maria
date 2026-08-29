#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use serde::{Deserialize, Serialize};
use serde_json::Value;
use tauri::command;
#[cfg(not(debug_assertions))]
use tauri::Manager;
#[cfg(not(debug_assertions))]
use tauri_plugin_shell::{process::CommandEvent, ShellExt};
use uuid;
use rusqlite::{params, Connection, Result as SqliteResult};

// ─────────────────────────────────────────────────────────────
// Tipos de dados para comunicação com o backend Python
// ─────────────────────────────────────────────────────────────

#[derive(Serialize, Deserialize, Debug)]
struct PythonRequest {
    id: String,
    comando: String,
    dados: Value,
}

#[derive(Serialize, Deserialize, Debug)]
#[allow(non_snake_case)]
struct PythonResponse {
    id: String,
    status: String,
    dados: Option<Value>,
    mensagemErro: Option<String>,
}

#[derive(Serialize, Debug, Clone)]
struct Message {
    id: i64,
    role: String,
    content: String,
    timestamp: String,
}

// ─────────────────────────────────────────────────────────────
// Comandos expostos ao frontend via invoke()
// ─────────────────────────────────────────────────────────────

/// Comando ping simples para verificar conectividade
#[command]
async fn ping() -> Result<String, String> {
    Ok("pong".to_string())
}

/// Envia uma mensagem para o backend Python e retorna a resposta
#[command]
async fn send_message(message: String) -> Result<String, String> {
    // Sempre via HTTP: em dev o backend é iniciado manualmente
    // (`python backend/main.py --bridge-http`); em produção o sidecar
    // maria-backend é spawnado automaticamente no setup() (ver main()).
    call_python_backend("chat", serde_json::json!({ "mensagem": message })).await
}

/// Obtém status do sistema (CPU, RAM, GPU, modelo ativo)
#[command]
async fn get_status() -> Result<Value, String> {
    // Chama o backend Python para obter status real
    match call_python_backend("status", serde_json::json!({})).await {
        Ok(response) => {
            // Tenta parsear a resposta como JSON
            match serde_json::from_str::<Value>(&response) {
                Ok(status) => Ok(status),
                Err(_) => {
                    // Se não for JSON válido, retorna status mockado
                    Ok(serde_json::json!({
                        "cpu": 18.0,
                        "ram": 42.0,
                        "gpu": 11.0,
                        "modelo": "Qwen 2.5 3B"
                    }))
                }
            }
        }
        Err(_) => {
            // Backend offline, retorna valores padrão
            Ok(serde_json::json!({
                "cpu": 0.0,
                "ram": 0.0,
                "gpu": 0.0,
                "modelo": "Qwen 2.5 3B"
            }))
        }
    }
}

/// Lê um arquivo do sistema
#[command]
async fn read_file(path: String) -> Result<String, String> {
    tokio::fs::read_to_string(&path)
        .await
        .map_err(|e| format!("Erro ao ler arquivo: {}", e))
}

/// Salva conteúdo em um arquivo
#[command]
async fn save_file(path: String, content: String) -> Result<(), String> {
    tokio::fs::write(&path, content)
        .await
        .map_err(|e| format!("Erro ao salvar arquivo: {}", e))
}

/// Garante que existe uma linha em `conversas` para o ID informado,
/// evitando inserir mensagens órfãs em `mensagens`.
fn garantir_conversa(conn: &Connection, conversation_id: i64) -> SqliteResult<()> {
    conn.execute(
        "INSERT OR IGNORE INTO conversas (id, titulo) VALUES (?1, 'Conversa Tauri')",
        params![conversation_id],
    )?;
    Ok(())
}

/// Obtém histórico de chat do banco de dados SQLite (acesso direto via Rust)
#[command]
fn get_chat_history(conversation_id: i64) -> Result<Vec<Message>, String> {
    let db_path = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .join("../shared/maria.db");

    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Erro ao abrir banco de dados: {}", e))?;

    conn.execute("PRAGMA foreign_keys = ON", [])
        .map_err(|e| e.to_string())?;

    let mut stmt = conn.prepare(
        "SELECT id, role, conteudo AS content, criado_em AS timestamp \
         FROM mensagens WHERE conversa_id = ?1 ORDER BY criado_em ASC"
    ).map_err(|e| e.to_string())?;

    let messages = stmt.query_map(params![conversation_id], |row| {
        Ok(Message {
            id: row.get(0)?,
            role: row.get(1)?,
            content: row.get(2)?,
            timestamp: row.get(3)?,
        })
    }).map_err(|e| e.to_string())?;

    messages.collect::<SqliteResult<Vec<_>, _>>()
        .map_err(|e| format!("Erro ao ler mensagens: {}", e))
}

/// Salva uma nova mensagem no banco de dados
#[command]
fn save_message(conversation_id: i64, role: String, content: String) -> Result<i64, String> {
    let db_path = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .join("../shared/maria.db");

    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Erro ao abrir banco de dados: {}", e))?;
    conn.execute("PRAGMA foreign_keys = ON", [])
        .map_err(|e| e.to_string())?;

    garantir_conversa(&conn, conversation_id).map_err(|e| e.to_string())?;

    conn.execute(
        "INSERT INTO mensagens (conversa_id, role, conteudo) VALUES (?1, ?2, ?3)",
        params![conversation_id, role, content],
    ).map_err(|e| format!("Erro ao inserir mensagem: {}", e))?;

    Ok(conn.last_insert_rowid())
}

// ─────────────────────────────────────────────────────────────
// Funções auxiliares para comunicação com Python
// ─────────────────────────────────────────────────────────────

/// Chama o backend MARIA via HTTP. Em desenvolvimento, o backend é iniciado
/// manualmente pelo desenvolvedor (`python backend/main.py --bridge-http`).
/// Em produção, o sidecar é iniciado automaticamente no setup() do app (ver main()).
async fn call_python_backend(comando: &str, dados: Value) -> Result<String, String> {
    let client = reqwest::Client::new();

    let request = PythonRequest {
        id: uuid::Uuid::new_v4().to_string(),
        comando: comando.to_string(),
        dados,
    };

    let response = client
        .post("http://localhost:8081/chat")
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("Erro de conexão com o backend MARIA: {}", e))?;

    let result: PythonResponse = response
        .json()
        .await
        .map_err(|e| format!("Erro ao processar resposta do backend: {}", e))?;

    if result.status == "ok" {
        // O backend retorna `dados` como string (ping, chat, ...) ou como
        // objeto/array JSON (status, listagem de memórias, ...). Para
        // strings, devolve o conteúdo direto; para JSON, serializa.
        Ok(match result.dados {
            Some(Value::String(s)) => s,
            Some(valor) => valor.to_string(),
            None => String::new(),
        })
    } else {
        Err(result.mensagemErro.unwrap_or_else(|| "Erro desconhecido no backend".to_string()))
    }
}

// ─────────────────────────────────────────────────────────────
// Ponto de entrada principal
// ─────────────────────────────────────────────────────────────

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|_app| {
            #[cfg(not(debug_assertions))]
            {
                let shell = _app.handle().shell();
                let (mut receptor, filho) = shell
                    .sidecar("maria-backend")
                    .expect("Sidecar 'maria-backend' não encontrado — rode build_sidecar.py antes do build.")
                    .args(["--bridge-http", "--porta", "8081"])
                    .spawn()
                    .expect("Falha ao iniciar o sidecar maria-backend");

                _app.manage(std::sync::Mutex::new(Some(filho)));

                tauri::async_runtime::spawn(async move {
                    while let Some(evento) = receptor.recv().await {
                        match evento {
                            CommandEvent::Stdout(linha) => {
                                eprintln!("[maria-backend] {}", String::from_utf8_lossy(&linha));
                            }
                            CommandEvent::Stderr(linha) => {
                                eprintln!("[maria-backend][erro] {}", String::from_utf8_lossy(&linha));
                            }
                            CommandEvent::Error(mensagem) => {
                                eprintln!("[maria-backend][falha] {}", mensagem);
                            }
                            CommandEvent::Terminated(status) => {
                                eprintln!("[maria-backend] processo encerrado: {:?}", status);
                            }
                            _ => {}
                        }
                    }
                });
            }
            Ok(())
        })
        .on_window_event(|_window, _event| {
            #[cfg(not(debug_assertions))]
            if let tauri::WindowEvent::CloseRequested { .. } = _event {
                if let Some(estado) = _window
                    .app_handle()
                    .try_state::<std::sync::Mutex<Option<tauri_plugin_shell::process::CommandChild>>>()
                {
                    if let Ok(mut guarda) = estado.lock() {
                        if let Some(filho) = guarda.take() {
                            let _ = filho.kill();
                        }
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            send_message,
            ping,
            read_file,
            save_file,
            get_status,
            get_chat_history,
            save_message,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use super::*;
    use rusqlite::Connection;

    fn criar_banco_teste() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch(
            "CREATE TABLE conversas (id INTEGER PRIMARY KEY, titulo TEXT);
             CREATE TABLE mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversa_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                anexos TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
             );"
        ).unwrap();
        conn
    }

    #[test]
    fn test_garantir_conversa_e_insercao_de_mensagem() {
        let conn = criar_banco_teste();
        garantir_conversa(&conn, 1).unwrap();
        conn.execute(
            "INSERT INTO mensagens (conversa_id, role, conteudo) VALUES (?1, ?2, ?3)",
            params![1, "user", "Olá"],
        ).unwrap();

        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM mensagens WHERE conversa_id = 1", [], |r| r.get(0)
        ).unwrap();
        assert_eq!(count, 1);
    }
}

