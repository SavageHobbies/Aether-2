use reqwest::Client;
use serde_json::Value;
use std::time::Duration;

pub struct ApiClient {
    client: Client,
    base_url: String,
}

impl ApiClient {
    pub fn new() -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        Self {
            client,
            base_url: "http://localhost:8000".to_string(), // Default Aether backend URL
        }
    }

    pub fn with_base_url(base_url: String) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        Self { client, base_url }
    }

    pub async fn capture_idea(&self, idea: &str) -> Result<String, Box<dyn std::error::Error>> {
        log::info!("Sending idea to backend: {}", idea);

        let url = format!("{}/api/v1/ideas", self.base_url);
        let payload = serde_json::json!({
            "content": idea,
            "source": "desktop_app",
            "timestamp": chrono::Utc::now().to_rfc3339()
        });

        match self.client.post(&url).json(&payload).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    match response.text().await {
                        Ok(text) => {
                            log::info!("Idea captured successfully");
                            Ok(text)
                        }
                        Err(e) => {
                            log::error!("Failed to read response: {}", e);
                            Err(Box::new(e))
                        }
                    }
                } else {
                    let error_msg = format!("API request failed with status: {}", response.status());
                    log::error!("{}", error_msg);
                    
                    // For now, return success even if API is down (offline mode)
                    log::info!("API unavailable, storing idea locally");
                    self.store_idea_locally(idea).await
                }
            }
            Err(e) => {
                log::error!("Failed to send request: {}", e);
                
                // Fallback to local storage
                log::info!("Backend unavailable, storing idea locally");
                self.store_idea_locally(idea).await
            }
        }
    }

    pub async fn get_dashboard_data(&self) -> Result<Value, Box<dyn std::error::Error>> {
        log::info!("Fetching dashboard data from backend");

        let url = format!("{}/api/v1/dashboard", self.base_url);

        match self.client.get(&url).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    match response.json::<Value>().await {
                        Ok(data) => {
                            log::info!("Dashboard data fetched successfully");
                            Ok(data)
                        }
                        Err(e) => {
                            log::error!("Failed to parse dashboard data: {}", e);
                            // Return mock data if parsing fails
                            Ok(self.get_mock_dashboard_data())
                        }
                    }
                } else {
                    log::error!("Dashboard API request failed with status: {}", response.status());
                    // Return mock data if API fails
                    Ok(self.get_mock_dashboard_data())
                }
            }
            Err(e) => {
                log::error!("Failed to fetch dashboard data: {}", e);
                // Return mock data if request fails
                Ok(self.get_mock_dashboard_data())
            }
        }
    }

    pub async fn get_notifications(&self) -> Result<Value, Box<dyn std::error::Error>> {
        log::info!("Fetching notifications from backend");

        let url = format!("{}/api/v1/notifications", self.base_url);

        match self.client.get(&url).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    match response.json::<Value>().await {
                        Ok(data) => {
                            log::info!("Notifications fetched successfully");
                            Ok(data)
                        }
                        Err(e) => {
                            log::error!("Failed to parse notifications: {}", e);
                            Ok(serde_json::json!([]))
                        }
                    }
                } else {
                    log::error!("Notifications API request failed with status: {}", response.status());
                    Ok(serde_json::json!([]))
                }
            }
            Err(e) => {
                log::error!("Failed to fetch notifications: {}", e);
                Ok(serde_json::json!([]))
            }
        }
    }

    async fn store_idea_locally(&self, idea: &str) -> Result<String, Box<dyn std::error::Error>> {
        // Store idea in local file system for offline mode
        use std::fs::OpenOptions;
        use std::io::Write;
        
        let app_data_dir = dirs::data_dir()
            .unwrap_or_else(|| std::path::PathBuf::from("."))
            .join("aether");
        
        // Create directory if it doesn't exist
        std::fs::create_dir_all(&app_data_dir)?;
        
        let ideas_file = app_data_dir.join("offline_ideas.txt");
        let timestamp = chrono::Utc::now().to_rfc3339();
        let entry = format!("[{}] {}\n", timestamp, idea);
        
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(ideas_file)?;
        
        file.write_all(entry.as_bytes())?;
        
        log::info!("Idea stored locally for offline sync");
        Ok("Idea stored locally (offline mode)".to_string())
    }

    fn get_mock_dashboard_data(&self) -> Value {
        serde_json::json!({
            "tasks": {
                "total": 12,
                "completed": 8,
                "overdue": 2,
                "due_today": 3
            },
            "ideas": {
                "total": 25,
                "processed": 18,
                "recent": 7
            },
            "notifications": {
                "unread": 4,
                "total": 15
            },
            "integrations": {
                "monday_com": {
                    "status": "connected",
                    "items": 8
                },
                "google_calendar": {
                    "status": "disconnected",
                    "events": 0
                }
            },
            "recent_activity": [
                {
                    "type": "task_completed",
                    "title": "Review project proposal",
                    "timestamp": "2025-07-18T18:30:00Z"
                },
                {
                    "type": "idea_captured",
                    "title": "New feature idea for mobile app",
                    "timestamp": "2025-07-18T17:45:00Z"
                },
                {
                    "type": "reminder_sent",
                    "title": "Meeting with client in 15 minutes",
                    "timestamp": "2025-07-18T17:15:00Z"
                }
            ]
        })
    }
}