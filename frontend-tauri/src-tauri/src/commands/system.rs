use tauri::command;
use serde::Serialize;

#[derive(Serialize)]
pub struct SystemStatus {
    cpu: f64,
    ram: f64,
    plataforma: String,
}

#[command]
pub async fn get_status() -> Result<SystemStatus, String> {
    Ok(SystemStatus {
        cpu: 0.0,
        ram: 0.0,
        plataforma: "linux".to_string(),
    })
}
