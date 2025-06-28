# MarketMan Trading System

A sophisticated, modular trading system that combines real-time news analysis, AI-powered signal generation, and technical analysis to provide actionable trading insights.

## 🚀 Features

### Core Capabilities
- **Multi-Source News Ingestion**: Real-time news from Finnhub, NewsAPI, and NewData
- **AI-Powered Analysis**: GPT-4 integration for sentiment analysis and signal generation
- **Technical Analysis**: Technical indicators and pattern recognition
- **Risk Management**: Position sizing and risk controls
- **Database Integration**: Persistent storage with SQLite
- **Modular Architecture**: Clean, maintainable codebase

### Advanced Features
- **Smart Filtering**: Keyword-based news filtering with exclusion lists
- **Batch Processing**: Efficient batch processing with quality scoring
- **Rate Limiting**: API rate limiting and cost controls
- **Multi-Source Validation**: Cross-reference news from multiple sources
- **Real-time Pipeline**: Streaming news processing pipeline
- **Performance Monitoring**: Built-in performance and scalability tests

## 📁 Project Structure

```
marketMan/
├── src/
│   ├── core/
│   │   ├── signals/           # Signal generation and analysis
│   │   ├── ingestion/         # Data ingestion modules
│   │   ├── database/          # Database management
│   │   ├── risk/              # Risk management
│   │   ├── backtest/          # Backtesting engine
│   │   ├── journal/           # Trading journal
│   │   ├── options/           # Options trading
│   │   ├── technicals/        # Technical indicators
│   │   └── utils/             # Shared utilities
│   ├── integrations/          # External integrations
│   ├── cli/                   # Command-line interface
│   └── config/                # Configuration files
├── tests/                     # Comprehensive test suite
├── config/                    # Configuration files
└── docs/                      # Documentation
```

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd marketMan
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## ⚙️ Configuration

### API Keys Required
- **OpenAI API Key**: For AI analysis and signal generation
- **Finnhub API Key**: For financial news and market data
- **NewsAPI Key**: For general news coverage
- **NewData API Key**: For additional news sources

### Configuration Files
- `config/settings.yaml`: General system settings
- `config/strategies.yaml`: Trading strategy configurations
- `config/brokers.yaml`: Broker integration settings

## 🚀 Usage

### Command Line Interface

The system provides a comprehensive CLI for all operations:

```bash
# Run news ingestion cycle
python -m src.cli.main ingest

# Generate trading signals
python -m src.cli.main signals

# Run backtesting
python -m src.cli.main backtest

# View system status
python -m src.cli.main status

# Get help
python -m src.cli.main --help
```

### Programmatic Usage

```python
from src.core.ingestion.news_ingestion_orchestrator import NewsIngestionOrchestrator
from src.core.signals.news_signal_orchestrator import NewsSignalOrchestrator

# Initialize orchestrators
ingestion_orchestrator = NewsIngestionOrchestrator()
signal_orchestrator = NewsSignalOrchestrator()

# Run news ingestion
news_items = ingestion_orchestrator.run_ingestion_cycle()

# Generate signals
signals = signal_orchestrator.generate_signals(news_items)
```

## 🧪 Testing

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Categories
```bash
# Integration tests
pytest tests/test_integration.py

# Performance tests
pytest tests/test_performance.py

# Unit tests
pytest tests/test_unit/
```

### Test Coverage
```bash
pytest --cov=src tests/
```

## 📊 Performance

The system is designed for high performance and scalability:

- **News Processing**: Handles 500+ news items in under 30 seconds
- **AI Analysis**: Batch processing with rate limiting and cost controls
- **Memory Efficiency**: Optimized memory usage for large datasets
- **Concurrent Processing**: Thread-safe operations for high throughput

## 🔧 Development

### Code Quality
- **Black**: Code formatting
- **Flake8**: Linting
- **isort**: Import sorting
- **pre-commit**: Automated quality checks

### Running Quality Checks
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Sort imports
isort src/ tests/

# Run all checks
pre-commit run --all-files
```

## 📈 Architecture Overview

### News Ingestion Pipeline
1. **Multi-Source Collection**: Fetch news from Finnhub, NewsAPI, and NewData
2. **Smart Filtering**: Filter by keywords and exclude unwanted content
3. **Batch Processing**: Group news items for efficient processing
4. **Quality Scoring**: Score news items based on relevance and source quality
5. **Database Storage**: Store processed news items

### Signal Generation Pipeline
1. **AI Analysis**: GPT-4 powered sentiment and signal analysis
2. **Technical Analysis**: Technical indicators and pattern recognition
3. **Multi-Source Validation**: Cross-reference signals across sources
4. **Risk Assessment**: Apply risk management rules
5. **Signal Output**: Generate actionable trading signals

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in the `docs/` folder
- Review the test examples for usage patterns

## 🔄 Roadmap

### Phase 3: Core Implementation ✅
- [x] Multi-source news ingestion
- [x] AI-powered signal generation
- [x] Technical analysis integration
- [x] Performance optimization
- [x] Comprehensive testing

### Phase 4: Advanced Features (Next)
- [ ] Real-time streaming data
- [ ] Advanced backtesting engine
- [ ] Machine learning models
- [ ] Web dashboard
- [ ] Mobile notifications

### Phase 5: Production Deployment
- [ ] Docker containerization
- [ ] Cloud deployment
- [ ] Monitoring and alerting
- [ ] Performance analytics
- [ ] User management system