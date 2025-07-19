use auto_launch::AutoLaunchBuilder;
use std::env;

pub struct AutoStartManager {
    auto_launch: auto_launch::AutoLaunch,
}

impl AutoStartManager {
    pub fn new() -> Self {
        let app_name = "Aether AI Companion";
        let app_path = env::current_exe()
            .unwrap_or_else(|_| std::path::PathBuf::from("aether-desktop"));

        let auto_launch = AutoLaunchBuilder::new()
            .set_app_name(app_name)
            .set_app_path(&app_path.to_string_lossy())
            .set_use_launch_agent(true) // Use launch agent on macOS
            .build()
            .expect("Failed to create auto-launch configuration");

        Self { auto_launch }
    }

    pub async fn initialize(&self) -> Result<(), Box<dyn std::error::Error>> {
        log::info!("Initializing auto-start manager");

        // Check if auto-start is already enabled
        match self.is_enabled().await {
            Ok(enabled) => {
                if enabled {
                    log::info!("Auto-start is already enabled");
                } else {
                    log::info!("Auto-start is disabled");
                }
            }
            Err(e) => {
                log::warn!("Failed to check auto-start status: {}", e);
            }
        }

        Ok(())
    }

    pub async fn toggle_autostart(&self, enable: bool) -> Result<bool, Box<dyn std::error::Error>> {
        log::info!("Toggling auto-start: {}", enable);

        if enable {
            self.enable_autostart().await
        } else {
            self.disable_autostart().await
        }
    }

    pub async fn enable_autostart(&self) -> Result<bool, Box<dyn std::error::Error>> {
        log::info!("Enabling auto-start");

        match self.auto_launch.enable() {
            Ok(_) => {
                log::info!("Auto-start enabled successfully");
                Ok(true)
            }
            Err(e) => {
                log::error!("Failed to enable auto-start: {}", e);
                Err(Box::new(e))
            }
        }
    }

    pub async fn disable_autostart(&self) -> Result<bool, Box<dyn std::error::Error>> {
        log::info!("Disabling auto-start");

        match self.auto_launch.disable() {
            Ok(_) => {
                log::info!("Auto-start disabled successfully");
                Ok(false)
            }
            Err(e) => {
                log::error!("Failed to disable auto-start: {}", e);
                Err(Box::new(e))
            }
        }
    }

    pub async fn is_enabled(&self) -> Result<bool, Box<dyn std::error::Error>> {
        match self.auto_launch.is_enabled() {
            Ok(enabled) => {
                log::debug!("Auto-start status: {}", enabled);
                Ok(enabled)
            }
            Err(e) => {
                log::error!("Failed to check auto-start status: {}", e);
                Err(Box::new(e))
            }
        }
    }
}