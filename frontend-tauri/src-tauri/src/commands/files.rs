use tauri::command;
use std::fs;

#[command]
pub async fn read_file(path: String) -> Result<String, String> {
    fs::read_to_string(&path)
        .map_err(|e| format!("Erro ao ler arquivo: {}", e))
}

#[command]
pub async fn save_file(path: String, content: String) -> Result<(), String> {
    fs::write(&path, &content)
        .map_err(|e| format!("Erro ao salvar arquivo: {}", e))
}
