# MarketMan Trading System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A sophisticated, AI-powered trading system that combines real-time news analysis, sentiment detection, and technical analysis to generate actionable trading signals for ETFs and options.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- API keys for OpenAI, Finnhub, NewsAPI, and NewData
- Pushover account (optional, for notifications)

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd marketMan
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Install pre-commit hooks
pre-commit install
```

### First Run
```bash
# Validate configuration
python marketman config validate

# Run news processing cycle
python marketman news cycle

# Check system status
python marketman status
```

## 📚 Documentation

- **[User Guide](docs/user-guide.md)** - Complete usage instructions
- **[API Reference](docs/api-reference.md)** - Technical API documentation
- **[Configuration Guide](docs/configuration.md)** - Setup and configuration
- **[Development Guide](docs/development.md)** - Contributing and development
- **[Architecture](docs/architecture.md)** - System design and components

## 🎯 Key Features

- **Multi-Source News Analysis** - Real-time news from 3+ sources
- **AI-Powered Signal Generation** - GPT-4 sentiment analysis
- **Risk Management** - Position sizing and stop-loss controls
- **Technical Analysis** - Pattern recognition and indicators
- **Smart Notifications** - Configurable alerts via Pushover
- **Performance Tracking** - Comprehensive trade journaling
- **Modular Architecture** - Clean, maintainable codebase

## 🛠️ Core Commands

```bash
# News and signals
python marketman news cycle          # Process news and generate signals
python marketman signals run         # Run signal analysis
python marketman alerts check        # Check for new alerts

# System management
python marketman status              # System status and health
python marketman config validate     # Validate configuration
python marketman performance show    # Performance dashboard

# Development
python marketman test                # Run test suite
python marketman lint                # Code quality checks
```

## 📊 System Status

- **Phase 3**: ✅ Core implementation complete
- **Phase 4**: 🔄 Advanced integrations (Notion, enhanced alerts)
- **Phase 5**: 📋 Production deployment (planned)

## 🤝 Contributing

See [Development Guide](docs/development.md) for contribution guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- 📖 [Documentation](docs/)
- 🐛 [Issues](https://github.com/your-repo/issues)
- 💬 [Discussions](https://github.com/your-repo/discussions)

---

**⚠️ Disclaimer**: This is experimental software for educational purposes. Use at your own risk. Not financial advice.