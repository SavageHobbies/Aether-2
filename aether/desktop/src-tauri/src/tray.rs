use tauri::{AppHandle, Manager, SystemTrayEvent};

pub struct TrayManager;

impl TrayManager {
    pub fn handle_tray_event(app: &AppHandle, event: SystemTrayEvent) {
        match event {
            SystemTrayEvent::LeftClick {
                position: _,
                size: _,
                ..
            } => {
                log::info!("System tray left clicked");
                Self::show_main_window(app);
            }
            SystemTrayEvent::RightClick {
                position: _,
                size: _,
                ..
            } => {
                log::info!("System tray right clicked");
                // Context menu is handled automatically by Tauri
            }
            SystemTrayEvent::DoubleClick {
                position: _,
                size: _,
                ..
            } => {
                log::info!("System tray double clicked");
                Self::show_main_window(app);
            }
            SystemTrayEvent::MenuItemClick { id, .. } => {
                log::info!("System tray menu item clicked: {}", id);
                Self::handle_menu_item_click(app, &id);
            }
            _ => {}
        }
    }

    fn handle_menu_item_click(app: &AppHandle, menu_id: &str) {
        match menu_id {
            "show" => {
                Self::show_main_window(app);
            }
            "capture" => {
                Self::show_quick_capture(app);
            }
            "dashboard" => {
                Self::show_dashboard(app);
            }
            "settings" => {
                Self::show_settings(app);
            }
            "quit" => {
                log::info!("Quitting application from system tray");
                app.exit(0);
            }
            _ => {
                log::warn!("Unknown menu item clicked: {}", menu_id);
            }
        }
    }

    fn show_main_window(app: &AppHandle) {
        if let Some(window) = app.get_window("main") {
            let _ = window.show();
            let _ = window.set_focus();
            let _ = window.unminimize();
            let _ = window.center();
            log::info!("Main window shown and focused");
        } else {
            log::error!("Main window not found");
        }
    }

    fn show_quick_capture(app: &AppHandle) {
        // Try to show existing quick capture window or create new one
        if let Some(window) = app.get_window("quick-capture") {
            let _ = window.show();
            let _ = window.set_focus();
            let _ = window.center();
        } else {
            // Create quick capture window
            let window_result = tauri::WindowBuilder::new(
                app,
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
                    log::info!("Quick capture window created and shown");
                }
                Err(e) => {
                    log::error!("Failed to create quick capture window: {}", e);
                }
            }
        }
    }

    fn show_dashboard(app: &AppHandle) {
        // Navigate main window to dashboard or show it
        if let Some(window) = app.get_window("main") {
            let _ = window.show();
            let _ = window.set_focus();
            let _ = window.unminimize();
            
            // Emit event to frontend to navigate to dashboard
            let _ = window.emit("navigate", "dashboard");
            log::info!("Navigated to dashboard");
        }
    }

    fn show_settings(app: &AppHandle) {
        // Navigate main window to settings or show it
        if let Some(window) = app.get_window("main") {
            let _ = window.show();
            let _ = window.set_focus();
            let _ = window.unminimize();
            
            // Emit event to frontend to navigate to settings
            let _ = window.emit("navigate", "settings");
            log::info!("Navigated to settings");
        }
    }
}