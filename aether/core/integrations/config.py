"""
Configuration management for external integrations.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from .calendar_types import CalendarAuthConfig, CalendarPreferences


@dataclass
class IntegrationConfig:
    """Configuration for all external integrations."""
    google_calendar: Optional[CalendarAuthConfig] = None
    calendar_preferences: Optional[CalendarPreferences] = None
    
    # Future integrations
    monday_com_api_key: Optional[str] = None
    slack_webhook_url: Optional[str] = None


class ConfigManager:
    """Manages configuration for external integrations."""
    
    def __init__(self, config_dir: str = ".aether"):
        """Initialize configuration manager."""
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "integrations_config.json"
        self.config_dir.mkdir(exist_ok=True)
    
    def load_config(self) -> IntegrationConfig:
        """Load configuration from file."""
        if not self.config_file.exists():
            return IntegrationConfig()
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            config = IntegrationConfig()
            
            # Load Google Calendar config
            if 'google_calendar' in data:
                gc_data = data['google_calendar']
                config.google_calendar = CalendarAuthConfig(**gc_data)
            
            # Load calendar preferences
            if 'calendar_preferences' in data:
                pref_data = data['calendar_preferences']
                config.calendar_preferences = CalendarPreferences(**pref_data)
            
            # Load other integration configs
            config.monday_com_api_key = data.get('monday_com_api_key')
            config.slack_webhook_url = data.get('slack_webhook_url')
            
            return config
            
        except Exception as e:
            print(f"Error loading config: {e}")
            return IntegrationConfig()
    
    def save_config(self, config: IntegrationConfig):
        """Save configuration to file."""
        try:
            data = {}
            
            if config.google_calendar:
                data['google_calendar'] = asdict(config.google_calendar)
            
            if config.calendar_preferences:
                data['calendar_preferences'] = asdict(config.calendar_preferences)
            
            if config.monday_com_api_key:
                data['monday_com_api_key'] = config.monday_com_api_key
            
            if config.slack_webhook_url:
                data['slack_webhook_url'] = config.slack_webhook_url
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            print(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_google_calendar(
        self, 
        client_id: str, 
        client_secret: str,
        redirect_uri: str = "http://localhost:8080/oauth/callback"
    ):
        """Set up Google Calendar integration."""
        config = self.load_config()
        
        config.google_calendar = CalendarAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )
        
        # Set default preferences if not already configured
        if not config.calendar_preferences:
            config.calendar_preferences = CalendarPreferences()
        
        self.save_config(config)
        
        print("Google Calendar integration configured successfully!")
        print("Next steps:")
        print("1. Enable the Google Calendar API in your Google Cloud Console")
        print("2. Create OAuth 2.0 credentials")
        print("3. Run the authentication flow")
    
    def get_google_calendar_setup_instructions(self) -> str:
        """Get setup instructions for Google Calendar integration."""
        return """
Google Calendar Integration Setup Instructions:

1. Go to the Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the credentials JSON file

5. Configure Aether with your credentials:
   - Use the client_id and client_secret from the downloaded file
   - Run: python -c "from core.integrations.config import ConfigManager; ConfigManager().setup_google_calendar('YOUR_CLIENT_ID', 'YOUR_CLIENT_SECRET')"

6. Install required dependencies:
   - pip install google-auth google-auth-oauthlib google-api-python-client

7. Test the integration:
   - python test_google_calendar.py
"""


def create_sample_config():
    """Create a sample configuration file."""
    config_manager = ConfigManager()
    
    sample_config = IntegrationConfig(
        google_calendar=CalendarAuthConfig(
            client_id="your_google_client_id_here",
            client_secret="your_google_client_secret_here",
            redirect_uri="http://localhost:8080/oauth/callback"
        ),
        calendar_preferences=CalendarPreferences(
            default_event_duration_minutes=60,
            default_reminder_minutes=[15, 60],
            auto_create_events_from_tasks=True,
            conflict_detection_enabled=True,
            work_start_hour=9,
            work_end_hour=17,
            timezone="UTC"
        )
    )
    
    # Save as sample file
    sample_file = config_manager.config_dir / "integrations_config.sample.json"
    
    with open(sample_file, 'w') as f:
        json.dump(asdict(sample_config), f, indent=2, default=str)
    
    print(f"Sample configuration created at {sample_file}")
    print("Copy this to integrations_config.json and update with your credentials")


if __name__ == "__main__":
    # Create sample configuration
    create_sample_config()
    
    # Show setup instructions
    config_manager = ConfigManager()
    print(config_manager.get_google_calendar_setup_instructions())