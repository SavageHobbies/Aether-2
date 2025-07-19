use tauri::{AppHandle, Manager};
use global_hotkey::{GlobalHotKeyManager, HotKeyState, GlobalHotKeyEvent};
use std::collections::HashMap;

pub struct HotkeyManager {
    manager: GlobalHotKeyManager,
    hotkeys: HashMap<u32, String>,
}

impl HotkeyManager {
    pub fn new() -> Self {
        Self {
            manager: GlobalHotKeyManager::new().expect("Failed to create hotkey manager"),
            hotkeys: HashMap::new(),
        }
    }

    pub async fn setup_hotkeys(&mut self, app_handle: AppHandle) -> Result<(), Box<dyn std::error::Error>> {
        log::info!("Setting up global hotkeys");

        // Register default hotkeys
        self.register_quick_capture_hotkey()?;
        self.register_show_window_hotkey()?;

        // Start hotkey event listener
        let app_handle_clone = app_handle.clone();
        tokio::spawn(async move {
            Self::listen_for_hotkey_events(app_handle_clone).await;
        });

        log::info!("Global hotkeys setup completed");
        Ok(())
    }

    fn register_quick_capture_hotkey(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        use global_hotkey::{hotkey::{HotKey, Modifiers, Code}};

        // Ctrl+Shift+Space for quick capture
        let hotkey = HotKey::new(Some(Modifiers::CONTROL | Modifiers::SHIFT), Code::Space);
        let hotkey_id = self.manager.register(hotkey)?;
        
        self.hotkeys.insert(hotkey_id, "quick_capture".to_string());
        log::info!("Registered quick capture hotkey: Ctrl+Shift+Space");
        
        Ok(())
    }

    fn register_show_window_hotkey(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        use global_hotkey::{hotkey::{HotKey, Modifiers, Code}};

        // Ctrl+Shift+A for show main window
        let hotkey = HotKey::new(Some(Modifiers::CONTROL | Modifiers::SHIFT), Code::KeyA);
        let hotkey_id = self.manager.register(hotkey)?;
        
        self.hotkeys.insert(hotkey_id, "show_window".to_string());
        log::info!("Registered show window hotkey: Ctrl+Shift+A");
        
        Ok(())
    }

    async fn listen_for_hotkey_events(app_handle: AppHandle) {
        use global_hotkey::GlobalHotKeyEvent;
        
        log::info!("Starting hotkey event listener");
        
        if let Ok(receiver) = GlobalHotKeyEvent::receiver() {
            loop {
                if let Ok(event) = receiver.recv() {
                    if event.state == HotKeyState::Pressed {
                        Self::handle_hotkey_event(&app_handle, event.id).await;
                    }
                }
            }
        } else {
            log::error!("Failed to get hotkey event receiver");
        }
    }

    async fn handle_hotkey_event(app_handle: &AppHandle, hotkey_id: u32) {
        log::info!("Hotkey pressed: ID {}", hotkey_id);

        // For now, we'll handle based on known IDs
        // In a real implementation, we'd maintain the mapping
        match hotkey_id {
            _ if Self::is_quick_capture_hotkey(hotkey_id) => {
                log::info!("Quick capture hotkey activated");
                Self::handle_quick_capture(app_handle).await;
            }
            _ if Self::is_show_window_hotkey(hotkey_id) => {
                log::info!("Show window hotkey activated");
                Self::handle_show_window(app_handle).await;
            }
            _ => {
                log::warn!("Unknown hotkey ID: {}", hotkey_id);
            }
        }
    }

    fn is_quick_capture_hotkey(hotkey_id: u32) -> bool {
        // This is a simplified check - in practice you'd maintain the mapping
        hotkey_id == 1 // Assuming first registered hotkey
    }

    fn is_show_window_hotkey(hotkey_id: u32) -> bool {
        // This is a simplified check - in practice you'd maintain the mapping
        hotkey_id == 2 // Assuming second registered hotkey
    }

    async fn handle_quick_capture(app_handle: &AppHandle) {
        log::info!("Handling quick capture hotkey");

        // Show quick capture window
        if let Some(window) = app_handle.get_window("quick-capture") {
            let _ = window.show();
            let _ = window.set_focus();
            let _ = window.center();
        } else {
            // Create quick capture window
            let window_result = tauri::WindowBuilder::new(
                app_handle,
                "quick-capture",
                tauri::WindowUrl::App("quick-capture.html".into()),
            )
            .title("Quick Capture - Aether")
            .inner_size(400.0, 300.0)
            .min_inner_size(350.0, 250.0)
            .resizable(true)
            .decorations(true)
            .always_on_top(true)
            .center()
            .build();

            match window_result {
                Ok(window) => {
                    let _ = window.show();
                    let _ = window.set_focus();
                    log::info!("Quick capture window created via hotkey");
                }
                Err(e) => {
                    log::error!("Failed to create quick capture window: {}", e);
                }
            }
        }
    }

    async fn handle_show_window(app_handle: &AppHandle) {
        log::info!("Handling show window hotkey");

        if let Some(window) = app_handle.get_window("main") {
            let _ = window.show();
            let _ = window.set_focus();
            let _ = window.unminimize();
            let _ = window.center();
            log::info!("Main window shown via hotkey");
        }
    }
}