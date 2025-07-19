# Aether Desktop Application

## Overview

The Aether Desktop Application provides a persistent, easily accessible interface for the Aether AI Companion system. Built with Tauri for cross-platform compatibility and optimal performance.

## Features

- **System Tray Integration**: Always accessible from the system tray
- **Global Hotkeys**: Instant idea capture with configurable keyboard shortcuts
- **Auto-Start**: Automatically starts with the system and runs in background
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Local-First**: Operates with local data storage and offline capabilities

## Architecture

```
aether/desktop/
├── src-tauri/          # Rust backend (Tauri)
│   ├── src/
│   │   ├── main.rs     # Main application entry
│   │   ├── tray.rs     # System tray management
│   │   ├── hotkeys.rs  # Global hotkey handling
│   │   └── autostart.rs # Auto-start functionality
│   ├── Cargo.toml      # Rust dependencies
│   └── tauri.conf.json # Tauri configuration
├── src/                # Frontend (HTML/CSS/JS)
│   ├── index.html      # Main application window
│   ├── styles/         # CSS styles
│   ├── scripts/        # JavaScript logic
│   └── components/     # UI components
└── package.json        # Node.js dependencies
```

## Development Setup

1. Install Tauri prerequisites
2. Install Node.js dependencies: `npm install`
3. Run in development mode: `npm run tauri dev`
4. Build for production: `npm run tauri build`

## Integration

The desktop app communicates with the Aether Python backend through:
- HTTP API calls to localhost
- WebSocket connections for real-time updates
- Local file system for offline storage
- System notifications for reminders