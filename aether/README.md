# 🤖 Aether AI Companion

> An intelligent personal AI companion designed to serve as a comprehensive knowledge hub and proactive assistant for business management.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-In%20Development-orange.svg)]()

## 🌟 Features

### ✅ **Currently Implemented**
- 🧠 **Conversational AI with Long-Term Memory** - Persistent context across sessions
- 💡 **Idea Stream Processing** - Rapid capture, categorization, and connection suggestions
- 📋 **Intelligent Task Extraction** - Automatic task identification from conversations
- 📅 **Google Calendar Integration** - OAuth, event creation, conflict detection
- 🔄 **Real-Time Synchronization** - WebSocket-based live updates
- 🗄️ **Vector Database** - Semantic search and memory retrieval
- 🔐 **Secure API Gateway** - JWT authentication, rate limiting

### 🚧 **In Development**
- 📊 **Monday.com Integration** - Project management and workflow automation
- 🔔 **Proactive Reminder System** - Intelligent notification prioritization
- 🖥️ **Desktop Application** - Electron/Tauri with system tray integration
- 📱 **Mobile Applications** - React Native/Flutter for iOS and Android

### 📋 **Planned Features**
- 🎤 **Voice Interface** - Speech-to-text and text-to-speech capabilities
- 🔌 **Plugin Architecture** - Extensible system for community contributions
- 🛡️ **Advanced Security** - End-to-end encryption and privacy controls
- 📈 **Analytics Dashboard** - Usage insights and productivity metrics

## 🏗️ Architecture

```
Aether AI Companion
├── 🐍 Core Engine (Python/FastAPI)
│   ├── AI Conversation System
│   ├── Memory Management
│   ├── Idea Processing
│   ├── Task Extraction
│   └── External Integrations
├── 🌐 API Gateway
│   ├── REST Endpoints
│   ├── WebSocket Real-time
│   └── Authentication
├── 🖥️ Desktop Client (Electron/Tauri)
│   ├── System Tray Integration
│   ├── Global Hotkeys
│   └── Dashboard Interface
├── 📱 Mobile Client (React Native/Flutter)
│   ├── Quick Capture
│   ├── Offline Sync
│   └── Push Notifications
└── 🎤 Voice Interface
    ├── Speech-to-Text (Whisper)
    ├── Text-to-Speech (Coqui)
    └── Voice Commands
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** - Core backend engine
- **Node.js 16+** - Client applications
- **PostgreSQL/SQLite** - Database storage
- **Git** - Version control

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SavageHobbies/Aether-2.git
   cd Aether-2
   ```

2. **Set up Python environment**
   ```bash
   cd aether
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-windows.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize database**
   ```bash
   python -m alembic upgrade head
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

### Development Setup

For development with auto-reload:
```bash
python simple_main.py  # Simple development server
# or
python flask_main.py   # Flask development server
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Core system tests
python test_conversation_system.py
python test_memory_system.py
python test_idea_system.py

# Integration tests
python test_google_calendar.py
python test_task_extraction.py
python test_api_complete.py

# Database tests
python test_complete_database_system.py
```

## 📁 Project Structure

```
aether/
├── 🏗️ core/                    # Core business logic
│   ├── ai/                     # AI providers and prompts
│   ├── conversation/           # Conversation management
│   ├── memory/                 # Memory and context systems
│   ├── ideas/                  # Idea processing and connections
│   ├── tasks/                  # Task extraction and management
│   ├── integrations/           # External service integrations
│   ├── notifications/          # Reminder and notification systems
│   ├── api/                    # REST API and WebSocket handlers
│   └── database/               # Database models and connections
├── 🔧 shared/                  # Shared utilities and schemas
│   ├── config/                 # Configuration management
│   ├── utils/                  # Common utilities
│   ├── schemas/                # Pydantic data models
│   └── models/                 # Base data models
├── 🧪 tests/                   # Test suites
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── 📋 .kiro/specs/             # Project specifications
│   ├── requirements.md         # Detailed requirements
│   ├── design.md              # System design
│   └── tasks.md               # Implementation tasks
└── 📄 Various test files       # Development and validation scripts
```

## 🔧 Configuration

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=sqlite:///aether.db

# AI Provider
AI_PROVIDER=simple  # or openai, anthropic
OPENAI_API_KEY=your_key_here

# External Integrations
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MONDAY_API_KEY=your_monday_api_key

# Security
JWT_SECRET_KEY=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `python -m pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Style

- **Python**: Follow PEP 8, use `black` for formatting
- **TypeScript**: Follow standard conventions, use `prettier`
- **Documentation**: Update README and docstrings for new features

## 📊 Current Status

### ✅ Completed (Major Milestones)
- [x] Core AI conversation engine with memory
- [x] Idea stream processing and connections
- [x] Task extraction from conversations
- [x] Google Calendar integration
- [x] REST API with real-time WebSocket sync
- [x] Vector database for semantic search
- [x] Comprehensive test coverage

### 🚧 In Progress
- [ ] Monday.com integration (Task 5.3)
- [ ] Proactive reminder system (Task 5.4)
- [ ] Desktop application foundation

### 📅 Roadmap
See [PROJECT_PLAN.md](PROJECT_PLAN.md) for detailed development roadmap.

## 📖 Documentation

- **[Requirements](/.kiro/specs/aether-ai-companion/requirements.md)** - Detailed system requirements
- **[Design](/.kiro/specs/aether-ai-companion/design.md)** - Architecture and design decisions
- **[Tasks](/.kiro/specs/aether-ai-companion/tasks.md)** - Implementation task breakdown
- **[Project Plan](PROJECT_PLAN.md)** - Development roadmap and milestones

## 🛡️ Security

Aether takes security seriously:

- 🔐 JWT-based authentication
- 🔒 Input validation and sanitization
- 🛡️ Rate limiting and request validation
- 🔑 Secure credential management
- 📊 Privacy-compliant analytics

Report security issues to: [security@aether-ai.com](mailto:security@aether-ai.com)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** - For advancing AI accessibility
- **FastAPI** - For the excellent Python web framework
- **SQLAlchemy** - For robust database ORM
- **ChromaDB** - For vector database capabilities
- **Open Source Community** - For the tools and libraries that make this possible

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/SavageHobbies/Aether-2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SavageHobbies/Aether-2/discussions)
- **Email**: [support@aether-ai.com](mailto:support@aether-ai.com)

---

<div align="center">

**Built with ❤️ for the future of AI-assisted productivity**

[⭐ Star this repo](https://github.com/SavageHobbies/Aether-2) | [🐛 Report Bug](https://github.com/SavageHobbies/Aether-2/issues) | [💡 Request Feature](https://github.com/SavageHobbies/Aether-2/issues)

</div>