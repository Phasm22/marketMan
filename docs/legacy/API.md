# MarketMan API Documentation

## Overview

This document provides comprehensive API documentation for the MarketMan trading system. All modules follow a consistent interface pattern and include proper error handling and logging.

## Core Modules

### 1. News Ingestion (`src/core/ingestion/`)

#### NewsIngestionOrchestrator

The main orchestrator for news ingestion that coordinates multiple news sources.

```python
from src.core.ingestion.news_ingestion_orchestrator import NewsIngestionOrchestrator

# Initialize orchestrator
orchestrator = NewsIngestionOrchestrator()

# Run a complete ingestion cycle
news_items = orchestrator.run_ingestion_cycle()

# Get ingestion statistics
stats = orchestrator.get_ingestion_stats()
```

**Methods:**
- `run_ingestion_cycle()` → `List[Dict]`: Run complete news ingestion cycle
- `get_ingestion_stats()` → `Dict`: Get ingestion statistics
- `test_news_sources()` → `Dict`: Test all configured news sources

#### News Sources

Individual news source classes for different APIs:

```python
from src.core.ingestion.news_sources.finnhub_news import FinnhubNewsSource
from src.core.ingestion.news_sources.newsapi_news import NewsAPINewsSource
from src.core.ingestion.news_sources.newdata_news import NewDataNewsSource

# Initialize sources
finnhub = FinnhubNewsSource()
newsapi = NewsAPINewsSource()
newdata = NewDataNewsSource()

# Fetch news
news = finnhub.fetch_news()
```

**Common Methods:**
- `fetch_news()` → `List[Dict]`: Fetch latest news
- `test_connection()` → `bool`: Test API connection
- `get_rate_limit_status()` → `Dict`: Get rate limit information

#### News Filtering

```python
from src.core.ingestion.news_filtering import NewsFilter

filter = NewsFilter()
filtered_news = filter.filter_news(news_items)
```

**Methods:**
- `filter_news(news_items: List[Dict])` → `List[Dict]`: Filter news by keywords
- `add_keyword(keyword: str)`: Add keyword to include list
- `add_exclusion(exclusion: str)`: Add keyword to exclusion list

#### News Batching

```python
from src.core.ingestion.news_batching import NewsBatcher

batcher = NewsBatcher()
batches = batcher.create_batches(news_items, batch_size=5)
```

**Methods:**
- `create_batches(news_items: List[Dict], batch_size: int)` → `List[List[Dict]]`: Create batches
- `score_batch_quality(batch: List[Dict])` → `float`: Score batch quality

### 2. Signal Generation (`src/core/signals/`)

#### NewsSignalOrchestrator

Main orchestrator for signal generation from news data.

```python
from src.core.signals.news_signal_orchestrator import NewsSignalOrchestrator

orchestrator = NewsSignalOrchestrator()
signals = orchestrator.generate_signals(news_items)
```

**Methods:**
- `generate_signals(news_items: List[Dict])` → `List[Dict]`: Generate trading signals
- `validate_signals(signals: List[Dict])` → `List[Dict]`: Validate signal quality
- `get_signal_stats()` → `Dict`: Get signal generation statistics

#### NewsGPTAnalyzer

AI-powered news analysis using GPT-4.

```python
from src.core.signals.news_gpt_analyzer import NewsGPTAnalyzer

analyzer = NewsGPTAnalyzer()

# Analyze single news item
result = analyzer.analyze_news_item(news_item)

# Analyze batch of news items
results = analyzer.analyze_news_batch(news_batch)
```

**Methods:**
- `analyze_news_item(news_item: Dict)` → `Dict`: Analyze single news item
- `analyze_news_batch(news_batch: List[Dict])` → `List[Dict]`: Analyze batch of news
- `get_analysis_stats()` → `Dict`: Get analysis statistics

#### ETFSignalEngine

ETF-specific signal generation.

```python
from src.core.signals.etf_signal_engine import ETFSignalEngine

engine = ETFSignalEngine()
signal = engine.generate_etf_signal(symbol, context)
```

**Methods:**
- `generate_etf_signal(symbol: str, context: str)` → `Dict`: Generate ETF signal
- `validate_etf_signal(signal: Dict)` → `bool`: Validate ETF signal

### 3. Technical Analysis (`src/core/technicals/`)

#### TechnicalIndicators

Technical analysis indicators and calculations.

```python
from src.core.technicals.technical_indicators import TechnicalIndicators

indicators = TechnicalIndicators()

# Calculate RSI
rsi = indicators.calculate_rsi(prices, period=14)

# Calculate moving averages
sma = indicators.calculate_sma(prices, period=20)
ema = indicators.calculate_ema(prices, period=20)

# Calculate Bollinger Bands
bb_upper, bb_middle, bb_lower = indicators.calculate_bollinger_bands(prices, period=20)
```

**Methods:**
- `calculate_rsi(prices: List[float], period: int)` → `List[float]`: Calculate RSI
- `calculate_sma(prices: List[float], period: int)` → `List[float]`: Calculate Simple Moving Average
- `calculate_ema(prices: List[float], period: int)` → `List[float]`: Calculate Exponential Moving Average
- `calculate_bollinger_bands(prices: List[float], period: int)` → `Tuple[List[float], List[float], List[float]]`: Calculate Bollinger Bands

#### PatternRecognition

Pattern recognition for technical analysis.

```python
from src.core.signals.pattern_recognition import PatternRecognition

patterns = PatternRecognition()

# Detect patterns
detected_patterns = patterns.detect_patterns(price_data)
```

**Methods:**
- `detect_patterns(price_data: Dict)` → `List[Dict]`: Detect technical patterns
- `validate_pattern(pattern: Dict)` → `bool`: Validate detected pattern

### 4. Database Management (`src/core/database/`)

#### DatabaseManager

Database operations and CRUD functions.

```python
from src.core.database.database_manager import DatabaseManager

db = DatabaseManager('path/to/database.db')

# News operations
db.save_news(news_item)
news_items = db.get_all_news()
recent_news = db.get_recent_news(hours=24)

# Signal operations
db.save_signal(signal)
signals = db.get_all_signals()
recent_signals = db.get_recent_signals(hours=24)

# Performance operations
db.save_performance(performance_data)
performance = db.get_performance_summary()
```

**Methods:**
- `save_news(news_item: Dict)`: Save news item to database
- `get_all_news()` → `List[Dict]`: Get all news items
- `get_recent_news(hours: int)` → `List[Dict]`: Get recent news items
- `save_signal(signal: Dict)`: Save signal to database
- `get_all_signals()` → `List[Dict]`: Get all signals
- `get_recent_signals(hours: int)` → `List[Dict]`: Get recent signals
- `save_performance(performance_data: Dict)`: Save performance data
- `get_performance_summary()` → `Dict`: Get performance summary

### 5. Risk Management (`src/core/risk/`)

#### PositionSizer

Position sizing calculations based on risk parameters.

```python
from src.core.risk.position_sizer import PositionSizer

sizer = PositionSizer()

# Calculate position size
position_size = sizer.calculate_position_size(
    portfolio_value=100000,
    risk_per_trade=0.02,
    entry_price=150.0,
    stop_loss=145.0
)
```

**Methods:**
- `calculate_position_size(portfolio_value: float, risk_per_trade: float, entry_price: float, stop_loss: float)` → `float`: Calculate position size
- `validate_position_size(position_size: float, max_position_size: float)` → `bool`: Validate position size

### 6. Utilities (`src/core/utils/`)

#### ConfigLoader

Configuration management and loading.

```python
from src.core.utils.config_loader import ConfigLoader

config_loader = ConfigLoader()
config = config_loader.load_config()
```

**Methods:**
- `load_config()` → `Dict`: Load configuration from files
- `get_setting(key: str, default=None)`: Get specific setting
- `update_config(updates: Dict)`: Update configuration

#### Formatting Utilities

```python
from src.core.utils.formatting import format_currency, format_percentage, format_datetime

# Format values
formatted_price = format_currency(150.50)
formatted_percent = format_percentage(0.025)
formatted_time = format_datetime(datetime.now())
```

**Functions:**
- `format_currency(value: float)` → `str`: Format as currency
- `format_percentage(value: float)` → `str`: Format as percentage
- `format_datetime(dt: datetime)` → `str`: Format datetime

#### Validation Utilities

```python
from src.core.utils.validation import validate_news_item, validate_signal

# Validate data
is_valid_news = validate_news_item(news_item)
is_valid_signal = validate_signal(signal)
```

**Functions:**
- `validate_news_item(news_item: Dict)` → `bool`: Validate news item structure
- `validate_signal(signal: Dict)` → `bool`: Validate signal structure

## CLI Interface (`src/cli/`)

### Main CLI

```bash
# News ingestion
python -m src.cli.main ingest

# Signal generation
python -m src.cli.main signals

# System status
python -m src.cli.main status

# Help
python -m src.cli.main --help
```

**Commands:**
- `ingest`: Run news ingestion cycle
- `signals`: Generate trading signals
- `backtest`: Run backtesting
- `status`: Show system status
- `test`: Run system tests

## Error Handling

All modules include comprehensive error handling:

```python
try:
    result = module.method()
except ModuleError as e:
    logger.error(f"Module error: {e}")
    # Handle specific module error
except ValidationError as e:
    logger.error(f"Validation error: {e}")
    # Handle validation error
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle unexpected error
```

## Logging

All modules use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Operation completed successfully")
logger.warning("Rate limit approaching")
logger.error("API connection failed")
logger.debug("Processing item 1 of 10")
```

## Configuration

Configuration is managed through YAML files:

```yaml
# config/settings.yaml
ingestion:
  max_news_per_cycle: 100
  max_ai_calls_per_cycle: 20
  keywords: [AAPL, TSLA, SPY, QQQ]
  exclude_keywords: [crypto, bitcoin]
  batch_size: 10

ai:
  openai_api_key: ${OPENAI_API_KEY}
  max_tokens: 500
  temperature: 0.7
  rate_limit_per_minute: 60

database:
  path: data/marketman.db
```

## Testing

All modules include comprehensive tests:

```bash
# Run all tests
pytest tests/

# Run specific module tests
pytest tests/test_ingestion.py

# Run with coverage
pytest --cov=src tests/

# Run performance tests
pytest tests/test_performance.py
```

## Performance Considerations

- **Rate Limiting**: All API calls include rate limiting
- **Batch Processing**: News items are processed in batches for efficiency
- **Caching**: Database caching for frequently accessed data
- **Memory Management**: Efficient memory usage for large datasets
- **Concurrency**: Thread-safe operations where appropriate

## Best Practices

1. **Error Handling**: Always handle exceptions appropriately
2. **Logging**: Use structured logging for debugging
3. **Validation**: Validate all input data
4. **Configuration**: Use configuration files for settings
5. **Testing**: Write comprehensive tests for all functionality
6. **Documentation**: Keep documentation up to date
7. **Performance**: Monitor and optimize performance-critical operations 