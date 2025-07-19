// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{
    AppHandle, CustomMenuItem, Manager, SystemTray, SystemTrayEvent, SystemTrayMenu,
    SystemTrayMenuItem, Window, WindowEvent,
};
use std::sync::Arc;
use tokio::sync::Mutex;

mod tray;
mod hotkeys;
mod autostart;
mod api;

use tray::TrayManager;
use hotkeys::HotkeyManager;
use autostart::AutoStartManager;
use api::ApiClient;

#[derive(Clone, serde::Serialize)]
struct Payload {
    args: Vec<String>,
    cwd: String,
}

// Tauri commands that can be called from the frontend
#[tauri::command]
async fn capture_idea(idea: String) -> Result<String, String> {
    log::info!("Capturing idea: {}", idea);
    
    // Send idea to Aether backend
    match ApiClient::new().capture_idea(&idea).await {
        Ok(response) => {
            log::info!("Idea captured successfully: {}", response);
            Ok(response)
        }
        Err(e) => {
            log::error!("Failed to capture idea: {}", e);
            Err(format!("Failed to capture idea: {}", e))
        }
    }
}

#[tauri::command]
async fn get_dashboard_data() -> Result<serde_json::Value, String> {
    log::info!("Fetching dashboard data");
    
    match ApiClient::new().get_dashboard_data().await {
        Ok(data) => Ok(data),
        Err(e) => {
            log::error!("Failed to fetch dashboard data: {}", e);
            Err(format!("Failed to fetch dashboard data: {}", e))
        }
    }
}

#[tauri::command]
async fn get_notifications() -> Result<serde_json::Value, String> {
    log::info!("Fetching notifications");
    
    match ApiClient::new().get_notifications().await {
        Ok(data) => Ok(data),
        Err(e) => {
            log::error!("Failed to fetch notifications: {}", e);
            Err(format!("Failed to fetch notifications: {}", e))
        }
    }
}

#[tauri::command]
async fn create_task(title: String, description: String, priority: String) -> Result<String, String> {
    log::info!("Creating task: {}", title);
    
    // This would integrate with the task creation API
    // For now, return success
    Ok(format!("Task '{}' created successfully", title))
}

#[tauri::command]
async fn search_memory(query: String) -> Result<serde_json::Value, String> {
    log::info!("Searching memory for: {}", query);
    
    // This would integrate with the memory search API
    // For now, return mock results
    Ok(serde_json::json!({
        "results": [
            {
                "id": "1",
                "content": "Related memory about project planning",
                "relevance": 0.85,
                "timestamp": "2025-07-18T15:30:00Z"
            }
        ],
        "total": 1
    }))
}

#[tauri::command]
async fn send_notification(title: String, message: String) -> Result<(), String> {
    log::info!("Sending notification: {} - {}", title, message);
    
    // This would integrate with the notification system
    // For now, we'll use Tauri's built-in notifications
    Ok(())
}

#[tauri::command]
fn show_main_window(app_handle: AppHandle) {
    if let Some(window) = app_handle.get_window("main") {
        let _ = window.show();
        let _ = window.set_focus();
        let _ = window.unminimize();
    }
}

#[tauri::command]
fn hide_main_window(app_handle: AppHandle) {
    if let Some(window) = app_handle.get_window("main") {
        let _ = window.hide();
    }
}

#[tauri::command]
async fn toggle_autostart(enable: bool) -> Result<bool, String> {
    match AutoStartManager::new().toggle_autostart(enable).await {
        Ok(enabled) => Ok(enabled),
        Err(e) => Err(format!("Failed to toggle autostart: {}", e))
    }
}

#[tauri::command]
async fn is_autostart_enabled() -> Result<bool, String> {
    match AutoStartManager::new().is_enabled().await {
        Ok(enabled) => Ok(enabled),
        Err(e) => Err(format!("Failed to check autostart status: {}", e))
    }
}

fn main() {
    // Initialize logging
    env_logger::init();
    
    log::info!("Starting Aether Desktop Application");

    // Create system tray
    let tray_menu = SystemTrayMenu::new()
        .add_item(CustomMenuItem::new("show".to_string(), "Show Aether"))
        .add_item(CustomMenuItem::new("capture".to_string(), "Quick Capture"))
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(CustomMenuItem::new("dashboard".to_string(), "Dashboard"))
        .add_item(CustomMenuItem::new("settings".to_string(), "Settings"))
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(CustomMenuItem::new("quit".to_string(), "Quit"));

    let system_tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .system_tray(system_tray)
        .on_system_tray_event(|app, event| {
            TrayManager::handle_tray_event(app, event);
        })
        .setup(|app| {
            // Initialize hotkey manager
            let app_handle = app.handle();
            tokio::spawn(async move {
                if let Err(e) = HotkeyManager::new().setup_hotkeys(app_handle).await {
                    log::error!("Failed to setup hotkeys: {}", e);
                }
            });

            // Initialize auto-start if enabled
            let app_handle = app.handle();
            tokio::spawn(async move {
                if let Err(e) = AutoStartManager::new().initialize().await {
                    log::error!("Failed to initialize autostart: {}", e);
                }
            });

            // Hide main window on startup (run in background)
            if let Some(window) = app.get_window("main") {
                let _ = window.hide();
            }

            log::info!("Aether Desktop Application initialized successfully");
            Ok(())
        })
        .on_window_event(|event| {
            match event.event() {
                WindowEvent::CloseRequested { api, .. } => {
                    // Hide window instead of closing when user clicks X
                    event.window().hide().unwrap();
                    api.prevent_close();
                }
                _ => {}
            }
        })
        .invoke_handler(tauri::generate_handler![
            capture_idea,
            get_dashboard_data,
            get_notifications,
            create_task,
            search_memory,
            send_notification,
            show_main_window,
            hide_main_window,
            toggle_autostart,
            is_autostart_enabled
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}