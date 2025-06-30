# Development Guide

Complete guide for developers contributing to MarketMan.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [Deployment](#deployment)

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Git**
- **Virtual environment** (recommended)
- **API keys** for development testing

### Development Setup

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd marketMan
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   pre-commit install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Add your API keys for testing
   ```

4. **Run initial tests**:
   ```bash
   pytest tests/ -v
   ```

## 📁 Project Structure

```
marketMan/
├── src/                          # Source code
│   ├── core/                     # Core business logic
│   │   ├── signals/              # Signal generation
│   │   ├── ingestion/            # Data ingestion
│   │   ├── database/             # Database management
│   │   ├── risk/                 # Risk management
│   │   ├── journal/              # Trading journal
│   │   ├── options/              # Options trading
│   │   ├── utils/                # Shared utilities
│   │   └── __init__.py
│   ├── integrations/             # External integrations
│   ├── cli/                      # Command-line interface
│   └── __init__.py
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── fixtures/                 # Test data
├── config/                       # Configuration files
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── bin/                          # Executable scripts
└── setup/                        # Setup scripts
```

### Key Modules

#### Core Modules
- **`signals/`** - Signal generation and analysis
- **`ingestion/`** - News and data ingestion
- **`database/`** - Database abstraction and management
- **`risk/`** - Risk management and position sizing
- **`journal/`** - Trade journaling and performance tracking

#### Integration Modules
- **`integrations/`** - External service integrations
- **`cli/`** - Command-line interface
- **`utils/`** - Shared utilities and helpers

## 🔧 Development Setup

### Environment Variables

Create `.env` for development:

```bash
# Development settings
DEBUG=true
LOG_LEVEL=DEBUG

# API Keys (use test keys for development)
OPENAI_API_KEY=sk-test-...
FINNHUB_KEY=test-key
NEWS_API=test-key
NEWS_DATA_KEY=test-key

# Test database
DATABASE_URL=sqlite:///test_marketman.db
```

### Database Setup

For development, use SQLite:

```bash
# Initialize test database
python -c "from src.core.database.db_manager import init_database; init_database()"
```

### Pre-commit Hooks

Install pre-commit hooks for code quality:

```bash
pre-commit install
pre-commit run --all-files
```

## 📝 Code Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 88 characters (Black default)
- **Import sorting**: isort configuration
- **Type hints**: Required for public APIs
- **Docstrings**: Google style

### Code Formatting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/
```

### Type Hints

All public functions should have type hints:

```python
from typing import List, Dict, Optional, Union
from datetime import datetime

def process_news(
    news_items: List[Dict[str, Any]], 
    confidence_threshold: float = 0.7
) -> List[Signal]:
    """Process news items and generate signals.
    
    Args:
        news_items: List of news items to process
        confidence_threshold: Minimum confidence for signals
        
    Returns:
        List of generated signals
    """
    pass
```

### Documentation

Use Google-style docstrings:

```python
def calculate_position_size(
    account_size: float, 
    risk_percentage: float
) -> float:
    """Calculate position size based on account size and risk.
    
    Args:
        account_size: Total account size in dollars
        risk_percentage: Percentage of account to risk (0.0-1.0)
        
    Returns:
        Position size in dollars
        
    Raises:
        ValueError: If risk_percentage is invalid
        
    Example:
        >>> calculate_position_size(10000, 0.02)
        200.0
    """
    if not 0 <= risk_percentage <= 1:
        raise ValueError("Risk percentage must be between 0 and 1")
    
    return account_size * risk_percentage
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_signals.py
│   ├── test_ingestion.py
│   └── test_risk.py
├── integration/             # Integration tests
│   ├── test_api_integration.py
│   └── test_database.py
├── fixtures/                # Test data
│   ├── sample_news.json
│   └── sample_signals.json
└── conftest.py             # Pytest configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_signals.py

# Run with verbose output
pytest -v

# Run only integration tests
pytest tests/integration/
```

### Writing Tests

Follow these patterns:

```python
import pytest
from unittest.mock import Mock, patch
from src.core.signals.news_signal_orchestrator import NewsSignalOrchestrator

class TestNewsSignalOrchestrator:
    """Test cases for NewsSignalOrchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create test orchestrator instance."""
        return NewsSignalOrchestrator()
    
    @pytest.fixture
    def sample_news(self):
        """Sample news data for testing."""
        return [
            {
                "title": "Test news item",
                "content": "Test content",
                "source": "Test Source",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
    
    def test_process_news_generates_signals(self, orchestrator, sample_news):
        """Test that news processing generates signals."""
        with patch('src.core.signals.news_signal_orchestrator.OpenAI') as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"signal": "bullish", "confidence": 8}'))]
            )
            
            signals = orchestrator.process_news(sample_news)
            
            assert len(signals) > 0
            assert signals[0].signal == "bullish"
            assert signals[0].confidence == 8
    
    def test_invalid_news_raises_exception(self, orchestrator):
        """Test that invalid news raises appropriate exception."""
        with pytest.raises(ValueError, match="Invalid news data"):
            orchestrator.process_news([])
```

### Test Data

Use fixtures for test data:

```python
# tests/fixtures/sample_news.json
{
  "news_items": [
    {
      "title": "Tesla Reports Strong Q4 Earnings",
      "content": "Tesla exceeded analyst expectations...",
      "source": "Reuters",
      "timestamp": "2024-01-01T00:00:00Z",
      "tickers": ["TSLA", "LIT", "DRIV"]
    }
  ]
}

# tests/conftest.py
import pytest
import json
from pathlib import Path

@pytest.fixture
def sample_news_data():
    """Load sample news data from fixture file."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_news.json"
    with open(fixture_path) as f:
        return json.load(f)
```

## 🏗️ Architecture

### Design Principles

1. **Modularity** - Each module has a single responsibility
2. **Testability** - All components are easily testable
3. **Configuration** - External configuration for all settings
4. **Error Handling** - Graceful error handling and logging
5. **Performance** - Efficient processing and memory usage

### Core Components

#### News Processing Pipeline

```
News Sources → Filtering → Batching → AI Analysis → Signal Generation → Output
```

#### Signal Generation

```
News Items → Sentiment Analysis → Technical Analysis → Risk Assessment → Signals
```

#### Risk Management

```
Position Sizing → Stop Loss → Portfolio Limits → Execution
```

### Database Schema

```sql
-- News items
CREATE TABLE news_items (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    source TEXT,
    timestamp DATETIME,
    relevance_score REAL,
    sentiment_score REAL
);

-- Signals
CREATE TABLE signals (
    id INTEGER PRIMARY KEY,
    news_item_id INTEGER,
    signal_type TEXT,
    confidence INTEGER,
    etfs TEXT,
    reasoning TEXT,
    timestamp DATETIME,
    FOREIGN KEY (news_item_id) REFERENCES news_items(id)
);

-- Trades
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    signal_id INTEGER,
    symbol TEXT,
    entry_price REAL,
    exit_price REAL,
    quantity INTEGER,
    pnl REAL,
    timestamp DATETIME,
    FOREIGN KEY (signal_id) REFERENCES signals(id)
);
```

## 🤝 Contributing

### Development Workflow

1. **Create feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make changes**:
   - Write code following standards
   - Add tests for new functionality
   - Update documentation

3. **Run quality checks**:
   ```bash
   pre-commit run --all-files
   pytest
   ```

4. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/amazing-feature
   # Create pull request on GitHub
   ```

### Commit Message Format

Use conventional commits:

```
type(scope): description

feat(signals): add new technical indicator
fix(api): handle rate limit errors
docs(readme): update installation instructions
test(risk): add position sizing tests
refactor(database): improve query performance
```

### Pull Request Guidelines

1. **Title**: Clear, descriptive title
2. **Description**: Explain what and why, not how
3. **Tests**: Include tests for new functionality
4. **Documentation**: Update relevant docs
5. **Screenshots**: For UI changes

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No breaking changes (or documented)
- [ ] Performance impact considered
- [ ] Security implications reviewed

## 🚀 Deployment

### Production Setup

1. **Environment**:
   ```bash
   # Production environment variables
   DEBUG=false
   LOG_LEVEL=INFO
   DATABASE_URL=postgresql://user:pass@host/db
   ```

2. **Database**:
   ```bash
   # Use PostgreSQL for production
   pip install psycopg2-binary
   ```

3. **Process Management**:
   ```bash
   # Use systemd or supervisor
   sudo cp config/marketman.service /etc/systemd/system/
   sudo systemctl enable marketman
   sudo systemctl start marketman
   ```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

CMD ["python", "marketman", "news", "cycle"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  marketman:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db/marketman
    depends_on:
      - db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: marketman
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Monitoring

Set up monitoring for production:

```python
# src/core/monitoring/health_check.py
import logging
from typing import Dict, Any

def health_check() -> Dict[str, Any]:
    """Perform system health check."""
    try:
        # Check database connectivity
        # Check API endpoints
        # Check disk space
        # Check memory usage
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": "ok",
                "apis": "ok",
                "disk": "ok",
                "memory": "ok"
            }
        }
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## 🔍 Debugging

### Logging

Configure logging for development:

```python
import logging

# Development logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/marketman.log'),
        logging.StreamHandler()
    ]
)
```

### Debug Mode

Enable debug mode for detailed output:

```bash
export DEBUG=true
python marketman news cycle
```

### Profiling

Profile performance bottlenecks:

```python
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    """Profile a function's performance."""
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return result
```

## 📚 Resources

### Documentation
- [Python Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Pytest Documentation](https://docs.pytest.org/)

### Tools
- [Black](https://black.readthedocs.io/) - Code formatter
- [isort](https://pycqa.github.io/isort/) - Import sorter
- [Flake8](https://flake8.pycqa.org/) - Linter
- [pre-commit](https://pre-commit.com/) - Git hooks

---

**Next**: [API Reference](api-reference.md) for technical API documentation 