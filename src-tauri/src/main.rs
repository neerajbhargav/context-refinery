// ContextRefinery — Tauri Desktop Entry Point
//
// Manages the FastAPI sidecar lifecycle:
//   1. Spawns the Python sidecar on app startup
//   2. Polls /api/health until the sidecar is ready
//   3. Kills the sidecar on app close

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    context_refinery_lib::run()
}
