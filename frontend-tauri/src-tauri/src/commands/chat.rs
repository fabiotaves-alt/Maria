use reqwest::Client;
use serde::{Deserialize, Serialize};
use tauri::command;

#[derive(Serialize)]
struct ChatRequest {
    id: String,
    comando: String,
    dados: serde_json::Value,
}

#[derive(Deserialize)]
struct ChatResponse {
    id: String,
    status: String,
    dados: Option<String>,
    mensagemErro: Option<String>,
}

#[command]
pub async fn ping() -> Result<String, String> {
    Ok("pong".to_string())
}

#[command]
pub async fn send_message(message: String) -> Result<String, String> {
    let client = Client::new();
    
    let request = ChatRequest {
        id: uuid::Uuid::new_v4().to_string(),
        comando: "chat".to_string(),
        dados: serde_json::json!({ "mensagem": message }),
    };

    let response = client
        .post("http://localhost:8081/chat")
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("Erro de conexao com backend: {}", e))?;

    let result: ChatResponse = response
        .json()
        .await
        .map_err(|e| format!("Erro ao processar resposta: {}", e))?;

    if result.status == "ok" {
        Ok(result.dados.unwrap_or_default())
    } else {
        Err(result.mensagemErro.unwrap_or("Erro desconhecido".to_string()))
    }
}
