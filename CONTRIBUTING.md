# Contributing to Aether AI Companion

Thank you for your interest in contributing to Aether! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Git
- Basic understanding of AI/ML concepts
- Familiarity with FastAPI, SQLAlchemy, and async Python

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Aether-2.git
   cd Aether-2
   ```

2. **Set up development environment**
   ```bash
   cd aether
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-windows.txt
   ```

3. **Set up pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Run tests to ensure everything works**
   ```bash
   python test_conversation_system.py
   python test_memory_system.py
   ```

## 🎯 How to Contribute

### Types of Contributions

We welcome several types of contributions:

- 🐛 **Bug fixes** - Fix issues and improve stability
- ✨ **New features** - Implement new functionality
- 📚 **Documentation** - Improve docs, examples, and guides
- 🧪 **Tests** - Add or improve test coverage
- 🔧 **Refactoring** - Improve code quality and structure
- 🎨 **UI/UX** - Enhance user interfaces and experience

### Contribution Process

1. **Check existing issues** - Look for existing issues or create a new one
2. **Discuss your idea** - Comment on the issue to discuss your approach
3. **Create a branch** - Use a descriptive branch name
4. **Make your changes** - Follow our coding standards
5. **Add tests** - Ensure your changes are well-tested
6. **Update documentation** - Update relevant docs and comments
7. **Submit a pull request** - Provide a clear description of your changes

## 📋 Development Guidelines

### Code Style

**Python Code:**
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Use meaningful variable and function names
- Keep functions focused and small (ideally < 50 lines)

**Example:**
```python
async def process_idea(
    idea_text: str, 
    user_id: str, 
    context: Optional[Dict[str, Any]] = None
) -> IdeaProcessingResult:
    """
    Process a user's idea and extract relevant information.
    
    Args:
        idea_text: The raw idea text from the user
        user_id: Unique identifier for the user
        context: Optional context information
    
    Returns:
        IdeaProcessingResult containing processed idea data
    
    Raises:
        ValidationError: If idea_text is invalid
        ProcessingError: If idea processing fails
    """
    # Implementation here
```

**Database Code:**
- Use async/await for all database operations
- Implement proper error handling and rollbacks
- Use database transactions for multi-step operations
- Follow SQLAlchemy best practices

**API Code:**
- Use Pydantic models for request/response validation
- Implement proper HTTP status codes
- Add comprehensive error handling
- Include rate limiting for public endpoints

### Testing Standards

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows

**Test Structure:**
```python
import pytest
from unittest.mock import AsyncMock, patch

class TestIdeaProcessor:
    """Test suite for idea processing functionality."""
    
    @pytest.fixture
    async def idea_processor(self):
        """Create a test idea processor instance."""
        return IdeaProcessor()
    
    async def test_process_simple_idea(self, idea_processor):
        """Test processing a simple idea."""
        # Arrange
        idea_text = "Build a mobile app for task management"
        
        # Act
        result = await idea_processor.process_idea(idea_text, "user123")
        
        # Assert
        assert result.success is True
        assert "mobile app" in result.keywords
        assert result.category == IdeaCategory.TECHNOLOGY
```

### Commit Message Format

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(tasks): add automatic task priority detection
fix(calendar): resolve Google Calendar sync conflict
docs(api): update REST API documentation
test(memory): add tests for memory consolidation
```

## 🏗️ Architecture Guidelines

### Core Principles

1. **Modularity** - Keep components loosely coupled
2. **Async First** - Use async/await for I/O operations
3. **Type Safety** - Use type hints throughout
4. **Error Handling** - Implement comprehensive error handling
5. **Testing** - Maintain high test coverage
6. **Documentation** - Document all public APIs

### Adding New Features

When adding new features:

1. **Design First** - Create or update design documents
2. **API Design** - Define clear interfaces
3. **Database Schema** - Plan database changes
4. **Implementation** - Write the core logic
5. **Testing** - Add comprehensive tests
6. **Documentation** - Update relevant documentation
7. **Integration** - Ensure proper integration with existing systems

### External Integrations

When adding new external service integrations:

1. **Create Types** - Define data models in `types.py`
2. **Implement Client** - Create service client class
3. **Add Configuration** - Update configuration system
4. **Error Handling** - Implement retry logic and error handling
5. **Testing** - Add both unit and integration tests
6. **Documentation** - Document setup and usage

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python test_conversation_system.py

# Run with coverage
python -m pytest --cov=core --cov-report=html
```

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   - Test individual functions and classes
   - Mock external dependencies
   - Fast execution

2. **Integration Tests** (`tests/integration/`)
   - Test component interactions
   - Use test databases
   - Test external API integrations

3. **End-to-End Tests**
   - Test complete user workflows
   - Use real or staging environments
   - Validate user experience

### Writing Good Tests

- **Arrange, Act, Assert** - Structure tests clearly
- **Descriptive Names** - Use clear test method names
- **Independent Tests** - Tests should not depend on each other
- **Mock External Services** - Don't rely on external APIs in unit tests
- **Test Edge Cases** - Include error conditions and boundary cases

## 📚 Documentation

### Types of Documentation

1. **Code Documentation**
   - Docstrings for all public functions
   - Inline comments for complex logic
   - Type hints for all parameters

2. **API Documentation**
   - OpenAPI/Swagger specs
   - Request/response examples
   - Error code documentation

3. **User Documentation**
   - Setup and installation guides
   - Feature usage examples
   - Troubleshooting guides

4. **Developer Documentation**
   - Architecture overviews
   - Contributing guidelines
   - Development setup

## 🚨 Issue Reporting

### Bug Reports

When reporting bugs, please include:

- **Environment**: OS, Python version, dependencies
- **Steps to Reproduce**: Clear, step-by-step instructions
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Error Messages**: Full error messages and stack traces
- **Additional Context**: Screenshots, logs, etc.

### Feature Requests

When requesting features, please include:

- **Problem Statement**: What problem does this solve?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other solutions you've considered
- **Use Cases**: Specific scenarios where this would be useful
- **Priority**: How important is this feature?

## 🔒 Security

### Reporting Security Issues

**DO NOT** create public issues for security vulnerabilities.

Instead, email security concerns to: [security@aether-ai.com](mailto:security@aether-ai.com)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Security Guidelines

- Never commit API keys, passwords, or secrets
- Use environment variables for configuration
- Implement proper input validation
- Follow secure coding practices
- Keep dependencies updated

## 🎉 Recognition

Contributors will be recognized in:

- **README.md** - Major contributors listed
- **CHANGELOG.md** - Contributions noted in releases
- **GitHub Releases** - Contributors thanked in release notes

## 📞 Getting Help

- **GitHub Discussions** - General questions and discussions
- **GitHub Issues** - Bug reports and feature requests
- **Discord** - Real-time chat with the community (coming soon)
- **Email** - [support@aether-ai.com](mailto:support@aether-ai.com)

## 📄 License

By contributing to Aether, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Aether AI Companion! Together, we're building the future of AI-assisted productivity. 🚀