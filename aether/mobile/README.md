# Aether Mobile Application

A cross-platform mobile application for the Aether AI Companion, built with React Native.

## Features

- **Cross-Platform**: Runs on both iOS and Android
- **Voice Integration**: Speech-to-text and text-to-speech capabilities
- **Secure Storage**: Encrypted local storage for sensitive data
- **Background Processing**: Idea capture and sync in background
- **Push Notifications**: Real-time reminders and updates
- **Offline Support**: Core functionality available offline
- **Biometric Security**: Fingerprint and face recognition support

## Prerequisites

- Node.js 16 or higher
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development, macOS only)

## Installation

1. Install dependencies:
```bash
npm install
```

2. Install iOS dependencies (macOS only):
```bash
cd ios && pod install
```

3. Start Metro bundler:
```bash
npm start
```

4. Run on Android:
```bash
npm run android
```

5. Run on iOS:
```bash
npm run ios
```

## Project Structure

```
src/
├── components/          # Reusable UI components
├── screens/            # Screen components
├── navigation/         # Navigation configuration
├── services/           # API and business logic
├── utils/              # Utility functions
├── hooks/              # Custom React hooks
├── types/              # TypeScript type definitions
├── constants/          # App constants
└── assets/             # Images, fonts, etc.
```

## Development

### Running Tests
```bash
npm test
```

### Linting
```bash
npm run lint
```

### Building for Production

#### Android
```bash
npm run build:android
```

#### iOS
```bash
npm run build:ios
```

## Configuration

The app uses environment-specific configuration files:
- `config/development.js`
- `config/production.js`

## Security

- All sensitive data is encrypted using `react-native-encrypted-storage`
- API keys are stored securely using `react-native-keychain`
- Biometric authentication is available where supported

## Background Processing

The app supports background idea capture and synchronization using:
- Background tasks for iOS
- Foreground services for Android
- Push notifications for real-time updates

## Voice Features

- Speech recognition using native platform APIs
- Text-to-speech with customizable voices
- Voice command processing
- Noise cancellation and audio preprocessing

## Offline Support

- Local SQLite database for offline data storage
- Automatic sync when connection is restored
- Conflict resolution for concurrent edits
- Cached responses for common queries

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details