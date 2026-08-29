#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use serde::Serialize;
#[cfg(debug_assertions)]
use serde::Deserialize;
use serde_json::Value;
use tauri::command;
#[cfg(not(debug_assertions))]
use tokio::process::Command;
#[cfg(not(debug_assertions))]
use std::process::Stdio;

use chrono;
#[cfg(debug_assertions)]
use uuid;
use rusqlite::{params, Connection, Result as SqliteResult};

// ─────────────────────────────────────────────────────────────
// Tipos de dados para comunicação com o backend Python
// ─────────────────────────────────────────────────────────────

#[cfg(debug_assertions)]
#[derive(Serialize, Deserialize, Debug)]
struct PythonRequest {
    id: String,
    comando: String,
    dados: Value,
}

#[cfg(debug_assertions)]
#[derive(Serialize, Deserialize, Debug)]
#[allow(non_snake_case)]
struct PythonResponse {
    id: String,
    status: String,
    dados: Option<String>,
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
    // Em desenvolvimento, chama HTTP diretamente
    // Em produção, usará sidecar Python
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

/// Obtém histórico de chat do banco de dados SQLite (acesso direto via Rust)
#[command]
fn get_chat_history(conversation_id: i64) -> Result<Vec<Message>, String> {
    let db_path = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .join("../shared/maria.db");
    
    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Erro ao abrir banco de dados: {}", e))?;

    let mut stmt = conn.prepare(
        "SELECT id, role, content, timestamp FROM messages 
         WHERE conversation_id = ? ORDER BY timestamp ASC"
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

    let timestamp = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?1, ?2, ?3, ?4)",
        params![conversation_id, role, content, timestamp],
    ).map_err(|e| format!("Erro ao inserir mensagem: {}", e))?;

    Ok(conn.last_insert_rowid())
}

// ─────────────────────────────────────────────────────────────
// Funções auxiliares para comunicação com Python
// ─────────────────────────────────────────────────────────────

/// Chama o backend Python via HTTP (desenvolvimento) ou sidecar (produção)
async fn call_python_backend(comando: &str, dados: Value) -> Result<String, String> {
    #[cfg(debug_assertions)]
    {
        // Modo desenvolvimento: chama HTTP diretamente
        call_python_http(comando, dados).await
    }
    
    #[cfg(not(debug_assertions))]
    {
        // Modo produção: usa sidecar
        call_python_sidecar(comando, dados).await
    }
}

/// Chama backend Python via HTTP (localhost:8081) — somente em desenvolvimento
#[cfg(debug_assertions)]
async fn call_python_http(comando: &str, dados: Value) -> Result<String, String> {
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
        .map_err(|e| format!("Erro de conexao com backend: {}", e))?;

    let result: PythonResponse = response
        .json()
        .await
        .map_err(|e| format!("Erro ao processar resposta: {}", e))?;

    if result.status == "ok" {
        Ok(result.dados.unwrap_or_default())
    } else {
        Err(result.mensagemErro.unwrap_or("Erro desconhecido".to_string()))
    }
}

/// Chama backend Python como processo sidecar (somente em produção)
#[cfg(not(debug_assertions))]
async fn call_python_sidecar(comando: &str, dados: Value) -> Result<String, String> {
    let output = Command::new("python3")
        .args([
            "backend/main.py",
            "--bridge",
            "--comando",
            comando,
            "--payload",
            &dados.to_string(),
        ])
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await
        .map_err(|e| format!("Erro ao executar Python: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Erro no Python: {}", stderr))
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
        .plugin(tauri_plugin_window::init())
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
