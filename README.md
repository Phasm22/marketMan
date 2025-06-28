# 🚀 MarketMan

**Enterprise ETF Market Intelligence & Alert System**

MarketMan transforms Google Alerts into actionable ETF trading signals using AI, contextual memory, and intelligent batching. Built for professional and enterprise-level thematic ETF investors who demand precision, reliability, and extensibility.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Architecture](https://img.shields.io/badge/Architecture-Modular-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Phase%202%20Complete-success.svg)

---

## 📚 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Command Line Interface](#command-line-interface)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing & Quality](#testing--quality)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

MarketMan is a modular, extensible platform for transforming unstructured market news into actionable ETF trading signals. It leverages AI, robust data pipelines, and enterprise-grade integrations to deliver timely, high-confidence alerts and performance tracking.

**Current Status**: Phase 2 Complete - Modular architecture implemented with database abstraction, CLI integration, and testing infrastructure.

---

## Architecture

### Core Modules
- **`signals/`** - News analysis and signal generation
- **`risk/`** - Position sizing and risk management
- **`backtest/`** - Strategy backtesting and validation
- **`journal/`** - Trade logging and performance tracking
- **`options/`** - Options trading strategies
- **`database/`** - Data persistence and CRUD operations
- **`ingestion/`** - Data collection and preprocessing
- **`utils/`** - Shared utilities and formatting

### Integrations
- **`integrations/`** - External service connectors (Gmail, Notion, Pushover)
- **`cli/`** - Command-line interface and user interactions

### Infrastructure
- **`config/`** - Configuration management
- **`tests/`** - Comprehensive test suite
- **`docs/`** - Documentation and guides

---

## Features

### ✅ Implemented (Phase 2 Complete)
- **Modular architecture** with clear separation of concerns
- **Database abstraction** with reusable CRUD operations
- **CLI interface** with comprehensive command structure
- **Configuration management** with YAML-based settings
- **Risk management** with position sizing algorithms
- **Options scalping strategy** framework
- **Testing infrastructure** with pytest and linting
- **Code quality tools** (black, flake8, isort, pre-commit)

### 🚧 In Development
- **AI-powered ETF signal extraction** from Google Alerts
- **Contextual memory** for pattern detection
- **Real-time ETF data** and technical analysis
- **Smart alert batching** and notification system
- **Performance dashboard** and trade tracking
- **Enterprise integrations** (Notion, Pushover, Gmail)

---

## Quick Start

### Prerequisites
- Python 3.9+
- Git
- API keys for OpenAI, Notion, etc.

### Installation

```bash
# Clone the repository
git clone <repository>
cd marketMan

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Create and edit configuration files:

```bash
# Main settings
cp config/settings.yaml.example config/settings.yaml

# Trading strategies
cp config/strategies.yaml.example config/strategies.yaml

# Broker configurations
cp config/brokers.yaml.example config/brokers.yaml
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run linting
black src/
flake8 src/
isort src/
```

---

## Configuration

### Environment Variables (.env)
```env
OPENAI_API_KEY=sk-...
NOTION_TOKEN=ntn_...
NOTION_DATABASE_ID=...
PUSHOVER_TOKEN=...
PUSHOVER_USER=...
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

### Settings (config/settings.yaml)
```yaml
database:
  type: sqlite
  path: data/marketman.db

risk:
  max_position_size: 0.02  # 2% of portfolio
  max_daily_loss: 0.05     # 5% daily loss limit

alerts:
  batch_strategy: smart_batch
  notification_channels: [pushover, notion]
```

### Strategies (config/strategies.yaml)
```yaml
options_scalping:
  enabled: true
  max_confidence: 0.8
  min_volume: 1000000

etf_signals:
  min_mentions: 3
  confidence_threshold: 0.7
```

---

## Command Line Interface

MarketMan provides a comprehensive CLI for all operations:

### Core Commands
```bash
# Signal processing
python -m src.cli.main signals run      # Process news signals
python -m src.cli.main signals status   # Check signal status
python -m src.cli.main signals backtest # Run signal backtest

# Alert management
python -m src.cli.main alerts check     # Check for new alerts
python -m src.cli.main alerts send      # Send pending alerts
python -m src.cli.main alerts status    # Alert queue status

# Performance tracking
python -m src.cli.main performance show   # Display dashboard
python -m src.cli.main performance update # Update data
python -m src.cli.main performance export # Export reports

# Options trading
python -m src.cli.main options scalp    # Run scalping strategy
python -m src.cli.main options analyze  # Analyze options data
python -m src.cli.main options backtest # Options backtest

# Risk management
python -m src.cli.main risk analyze       # Portfolio risk analysis
python -m src.cli.main risk limits        # Show position limits
python -m src.cli.main risk position-size # Calculate position sizes
```

### Global Options
```bash
python -m src.cli.main --help           # Show all commands
python -m src.cli.main --verbose        # Enable verbose logging
```

---

## Project Structure

```
marketMan/
├── src/                          # Core source code
│   ├── cli/                      # Command-line interface
│   │   ├── main.py              # CLI entry point
│   │   └── __init__.py
│   ├── core/                     # Core modules
│   │   ├── signals/             # Signal processing
│   │   ├── risk/                # Risk management
│   │   ├── backtest/            # Backtesting engine
│   │   ├── journal/             # Trade logging
│   │   ├── options/             # Options strategies
│   │   ├── database/            # Data persistence
│   │   ├── ingestion/           # Data collection
│   │   └── utils/               # Shared utilities
│   └── integrations/            # External integrations
│       ├── notion/              # Notion API
│       ├── gmail/               # Gmail integration
│       └── pushover/            # Push notifications
├── config/                       # Configuration files
│   ├── settings.yaml            # Main settings
│   ├── strategies.yaml          # Trading strategies
│   └── brokers.yaml             # Broker configurations
├── tests/                        # Test suite
│   ├── test_hello.py            # Basic test
│   └── conftest.py              # Test configuration
├── data/                         # Data storage
├── logs/                         # Log files
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project configuration
├── .pre-commit-config.yaml      # Pre-commit hooks
└── README.md                    # This file
```

---

## Development

### Code Quality
The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **Flake8**: Linting and style checking
- **isort**: Import sorting
- **pre-commit**: Git hooks for quality checks

### Development Workflow
```bash
# Format code
black src/

# Check style
flake8 src/

# Sort imports
isort src/

# Run pre-commit checks
pre-commit run --all-files
```

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement in appropriate module under `src/`
3. Add tests in `tests/`
4. Update configuration if needed
5. Run quality checks
6. Submit pull request

---

## Testing & Quality

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_specific.py

# Run with verbose output
pytest -v
```

### Quality Checks
```bash
# Format code
black src/

# Lint code
flake8 src/

# Sort imports
isort src/

# Type checking (if using mypy)
mypy src/
```

### Pre-commit Hooks
The project includes pre-commit hooks that automatically run quality checks on commit:
- Code formatting (black)
- Import sorting (isort)
- Linting (flake8)
- Basic tests

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all quality checks pass
6. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Roadmap

### Phase 3: Core Implementation
- [ ] Complete signal processing pipeline
- [ ] Implement AI analysis engine
- [ ] Add real-time data ingestion
- [ ] Build performance tracking system

### Phase 4: Integrations
- [ ] Complete Notion integration
- [ ] Add Pushover notifications
- [ ] Implement Gmail integration
- [ ] Add broker API connections

### Phase 5: Advanced Features
- [ ] Machine learning model training
- [ ] Advanced backtesting engine
- [ ] Portfolio optimization
- [ ] Real-time monitoring dashboard

---

**Status**: Phase 2 Complete - Modular architecture with CLI, testing, and quality infrastructure ready for core feature development.