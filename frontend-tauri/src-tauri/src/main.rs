#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            commands::chat::send_message,
            commands::chat::ping,
            commands::files::read_file,
            commands::files::save_file,
            commands::system::get_status,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
