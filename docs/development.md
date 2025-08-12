# Development Guide

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [Deployment](#deployment)

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- Virtual environment (recommended)
- API keys for development testing

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
   # Create settings.yaml with your API keys
   cp config/settings.yaml.example config/settings.yaml
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
│   │   │   ├── news_signal_orchestrator.py
│   │   │   ├── etf_signal_engine.py
│   │   │   └── pattern_recognizer.py
│   │   ├── ingestion/            # Data ingestion
│   │   │   ├── news_orchestrator.py
│   │   │   ├── news_filter.py
│   │   │   ├── news_batcher.py
│   │   │   └── news_sources/     # News sources: Finnhub, NewsAPI, NewData
│   │   ├── database/             # Database management
│   │   │   ├── db_manager.py
│   │   │   └── market_memory.py
│   │   ├── risk/                 # Risk management
│   │   │   └── position_sizing.py
│   │   ├── journal/              # Trading journal
│   │   │   ├── trade_journal.py
│   │   │   ├── performance_tracker.py
│   │   │   ├── alert_batcher.py
│   │   │   └── signal_logger.py
│   │   ├── options/              # Options trading
│   │   │   └── scalping_strategy.py
│   │   ├── utils/                # Shared utilities
│   │   └── __init__.py
│   ├── integrations/             # External integrations
│   │   ├── pushover_client.py
│   │   ├── notion_reporter.py
│   │   ├── fidelity_integration.py
│   │   ├── gmail_organizer.py
│   │   └── notion_journal.py
│   ├── cli/                      # Command-line interface
│   │   ├── main.py
│   │   └── commands/
│   ├── monitoring/               # System monitoring
│   │   └── marketman_monitor.py
│   └── __init__.py
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── fixtures/                 # Test data
├── config/                       # Configuration files
│   ├── settings.yaml             # Main configuration
│   ├── strategies.yaml           # Strategy configuration
│   ├── brokers.yaml              # Broker configuration
│   └── credentials/              # API credentials
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── bin/                          # Executable scripts
├── data/                         # Database files
└── logs/                         # Log files
```

### Key Modules

#### Core Modules
- **`signals/`** - Signal generation and analysis
- **`ingestion/`** - News and data ingestion
- **`database/`** - Database abstraction and management
- **`risk/`** - Risk management and position sizing
- **`journal/`** - Trade journaling and performance tracking
- **`options/`** - Options trading strategies

#### Integration Modules
- **`integrations/`** - External service integrations
- **`cli/`** - Command-line interface
- **`monitoring/`** - System monitoring
- **`utils/`** - Shared utilities and helpers

## 🔧 Development Setup

### Environment Variables

Create `config/settings.yaml` for development:

```yaml
# Development settings
app:
  debug: true
  log_level: DEBUG

# API Keys (use test keys for development)
openai:
  api_key: sk-test-...
finnhub:
  api_key: test-key
newsapi:
  api_key: test-key
newdata:
  api_key: test-key

# Test database
database:
  type: sqlite
  path: data/test_marketman.db
```

### Database Setup

For development, use SQLite:

```bash
# Initialize test database
python -c "from src.core.database.db_manager import DatabaseManager; db = DatabaseManager('data/test_marketman.db'); db.init_database()"
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
        ValueError: If risk_percentage is not between 0 and 1
    """
    if not 0 <= risk_percentage <= 1:
        raise ValueError("Risk percentage must be between 0 and 1")
    
    return account_size * risk_percentage
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                         # Unit tests
│   ├── test_signals.py
│   ├── test_ingestion.py
│   ├── test_risk.py
│   └── test_journal.py
├── integration/                  # Integration tests
│   ├── test_news_cycle.py
│   ├── test_signal_generation.py
│   └── test_database.py
└── fixtures/                     # Test data
    ├── sample_news.json
    ├── sample_signals.json
    └── sample_trades.json
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_signals.py

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/
```

### Test Examples

#### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch
from src.core.signals.news_signal_orchestrator import NewsSignalOrchestrator

class TestNewsSignalOrchestrator:
    """Test NewsSignalOrchestrator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'openai': {'api_key': 'test-key'},
            'news_ingestion': {'max_daily_ai_calls': 10}
        }
        self.orchestrator = NewsSignalOrchestrator(self.config)
    
    def test_process_signals_empty_input(self):
        """Test processing signals with empty input."""
        result = self.orchestrator.process_signals([], 24)
        assert result['signals'] == []
        assert result['processed_count'] == 0
    
    @patch('src.core.signals.news_signal_orchestrator.OpenAI')
    def test_process_signals_with_news(self, mock_openai):
        """Test processing signals with news items."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices[0].message.content = '{"signal_type": "bullish", "confidence": 8}'
        
        news_items = [
            {
                'title': 'Test News',
                'content': 'Test content',
                'source': 'test',
                'timestamp': '2024-01-01T10:00:00Z'
            }
        ]
        
        result = self.orchestrator.process_signals(news_items, 24)
        assert len(result['signals']) > 0
        assert result['processed_count'] == 1
```

#### Integration Test Example

```python
import pytest
from src.core.ingestion.news_orchestrator import NewsIngestionOrchestrator
from src.core.database.db_manager import DatabaseManager

class TestNewsCycle:
    """Test complete news processing cycle."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = DatabaseManager(':memory:')
        self.db.init_database()
        
        self.config = {
            'finnhub': {'api_key': 'test-key'},
            'newsapi': {'api_key': 'test-key'},
            'newdata': {'api_key': 'test-key'}
        }
        self.orchestrator = NewsIngestionOrchestrator(self.config)
    
    @patch('src.core.ingestion.news_sources.finnhub.FinnhubNewsSource.fetch_news')
    def test_news_cycle(self, mock_fetch):
        """Test complete news processing cycle."""
        # Mock news source response
        mock_fetch.return_value = [
            {
                'title': 'Test News',
                'content': 'Test content',
                'source': 'finnhub',
                'timestamp': '2024-01-01T10:00:00Z'
            }
        ]
        
        result = self.orchestrator.process_news_cycle(['AAPL'], 24)
        assert result['processed_count'] > 0
        assert result['filtered_count'] >= 0
```

### Test Data

Create test fixtures in `tests/fixtures/`:

```python
# tests/fixtures/sample_news.json
{
    "news_items": [
        {
            "title": "Apple Reports Strong Earnings",
            "content": "Apple Inc. reported better-than-expected quarterly earnings...",
            "source": "reuters",
            "timestamp": "2024-01-01T10:00:00Z",
            "tickers": ["AAPL"],
            "relevance_score": 0.85,
            "sentiment_score": 0.7
        }
    ]
}
```

## 🏗️ Architecture

### Design Patterns

#### Orchestrator Pattern

Used throughout the application:

```python
class ComponentOrchestrator:
    """Orchestrates component operations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.subcomponents = self._initialize_subcomponents()
    
    def _initialize_subcomponents(self) -> Dict[str, Any]:
        """Initialize subcomponents."""
        return {
            'filter': NewsFilter(self.config),
            'batcher': NewsBatcher(self.config),
            'analyzer': NewsAnalyzer(self.config)
        }
    
    def process(self, input_data: Any) -> Any:
        """Process data through the pipeline."""
        try:
            filtered_data = self.subcomponents['filter'].process(input_data)
            batched_data = self.subcomponents['batcher'].process(filtered_data)
            analyzed_data = self.subcomponents['analyzer'].process(batched_data)
            return analyzed_data
        except Exception as e:
            self._handle_error(e)
            return None
```

#### Strategy Pattern

Used for different processing strategies:

```python
from abc import ABC, abstractmethod

class BatchingStrategy(ABC):
    """Abstract batching strategy."""
    
    @abstractmethod
    def should_batch(self, items: List[Any]) -> bool:
        """Determine if items should be batched."""
        pass
    
    @abstractmethod
    def create_batch(self, items: List[Any]) -> Dict[str, Any]:
        """Create a batch from items."""
        pass

class SmartBatchingStrategy(BatchingStrategy):
    """Smart batching based on content and timing."""
    
    def should_batch(self, items: List[Any]) -> bool:
        return len(items) >= 3 or self._time_threshold_reached(items)
    
    def create_batch(self, items: List[Any]) -> Dict[str, Any]:
        return {
            'items': items,
            'batch_type': 'smart',
            'created_at': datetime.now(),
            'summary': self._create_summary(items)
        }
```

### Error Handling

Consistent error handling throughout:

```python
class MarketManError(Exception):
    """Base exception for MarketMan."""
    pass

class ConfigurationError(MarketManError):
    """Configuration-related errors."""
    pass

class APIError(MarketManError):
    """API-related errors."""
    pass

def safe_api_call(func):
    """Decorator for safe API calls."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.RequestException as e:
            raise APIError(f"API call failed: {e}")
        except Exception as e:
            raise MarketManError(f"Unexpected error: {e}")
    return wrapper
```

## 🤝 Contributing

### Development Workflow

1. **Create feature branch**:
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make changes**:
   - Follow code standards
   - Add tests for new functionality
   - Update documentation

3. **Run tests**:
   ```bash
   pytest tests/ -v
   pre-commit run --all-files
   ```

4. **Create pull request**:
   - Describe changes clearly
   - Include test results
   - Update relevant documentation

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No security issues
- [ ] Performance considerations
- [ ] Error handling implemented

### Commit Message Format

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
```
feat(signals): add new signal confidence algorithm
fix(api): resolve rate limiting issue
docs(readme): update installation instructions
test(journal): add performance tracking tests
```

## 🚀 Deployment

### Production Setup

1. **Environment preparation**:
   ```bash
   # Create production environment
   python -m venv venv_prod
   source venv_prod/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**:
   ```bash
   # Create production config
   cp config/settings.yaml config/settings.prod.yaml
   # Edit with production API keys
   ```

3. **Database setup**:
   ```bash
   # Initialize production database
   python -c "from src.core.database.db_manager import DatabaseManager; db = DatabaseManager('data/marketman.db'); db.init_database()"
   ```

4. **Service setup**:
   ```bash
   # Copy systemd service
   sudo cp config/marketman.service /etc/systemd/system/
   sudo systemctl enable marketman
   sudo systemctl start marketman
   ```

### Monitoring

Set up monitoring for production:

```bash
# Check service status
sudo systemctl status marketman

# View logs
sudo journalctl -u marketman -f

# Monitor system resources
htop
df -h
```

### Backup Strategy

```bash
# Database backup
cp data/marketman.db data/backup/marketman_$(date +%Y%m%d_%H%M%S).db

# Configuration backup
cp config/settings.yaml config/backup/settings_$(date +%Y%m%d_%H%M%S).yaml

# Log rotation
logrotate /etc/logrotate.d/marketman
```

## 🚫 Not Implemented

The following development features are **NOT YET IMPLEMENTED**:

1. **Automated Testing Pipeline** - No CI/CD setup
2. **Code Coverage Reports** - No coverage tracking
3. **Performance Benchmarking** - No performance tests
4. **Security Scanning** - No security analysis
5. **Docker Containerization** - No container support
6. **Database Migrations** - No migration system
7. **API Documentation** - No OpenAPI/Swagger docs
8. **Load Testing** - No load testing framework

---

**Next**: [API Reference](api-reference.md) for technical details 