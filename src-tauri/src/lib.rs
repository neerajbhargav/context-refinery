// ContextRefinery — Tauri Core Library
//
// Contains:
//   - Sidecar lifecycle management (spawn, health-check, kill)
//   - IPC commands for the Vue frontend
//   - Native file dialog integration

use tauri::Manager;
use std::sync::Mutex;

// Store the sidecar child process for cleanup
struct SidecarState {
    child: Option<tauri_plugin_shell::process::CommandChild>,
}

/// Open a native folder picker dialog and return the selected path.
#[tauri::command]
async fn open_folder_dialog(app: tauri::AppHandle) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;
    
    let folder = app.dialog()
        .file()
        .blocking_pick_folder();
    
    Ok(folder.map(|f| f.to_string()))
}

/// Get the sidecar API base URL.
#[tauri::command]
fn get_api_url() -> String {
    "http://127.0.0.1:8741".to_string()
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .manage(Mutex::new(SidecarState { child: None }))
        .setup(|app| {
            #[allow(unused_variables)]
            let app_handle = app.handle().clone();

            // Spawn the FastAPI sidecar
            #[cfg(not(debug_assertions))]
            {
                use tauri_plugin_shell::ShellExt;

                let sidecar_command = app_handle
                    .shell()
                    .sidecar("binaries/context-refinery-api")
                    .expect("Failed to create sidecar command")
                    .args(["--port", "8741"]);

                let (mut _rx, child) = sidecar_command
                    .spawn()
                    .expect("Failed to spawn sidecar");

                // Store the child process for cleanup
                let state = app_handle.state::<Mutex<SidecarState>>();
                let mut state = state.lock().unwrap();
                state.child = Some(child);

                println!("✅ Sidecar spawned on port 8741");
            }

            #[cfg(debug_assertions)]
            {
                println!("⚠️  Dev mode: sidecar not auto-spawned.");
                println!("   Run manually: cd src-backend && python main.py");
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                // Kill the sidecar when the window is closed
                let state = window.state::<Mutex<SidecarState>>();
                let mut state = state.lock().unwrap();
                if let Some(child) = state.child.take() {
                    let _ = child.kill();
                    println!("🛑 Sidecar process killed");
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            open_folder_dialog,
            get_api_url,
        ])
        .run(tauri::generate_context!())
        .expect("Error while running ContextRefinery");
}
