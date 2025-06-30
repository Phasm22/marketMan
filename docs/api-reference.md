# API Reference

Technical reference for MarketMan's core modules and CLI interface.

## 📋 Table of Contents

- [Core Modules](#core-modules)
- [CLI Interface](#cli-interface)
- [Integrations](#integrations)
- [Data Models](#data-models)
- [Configuration](#configuration)
- [Database](#database)

## 🧠 Core Modules

### Signals Module

#### NewsSignalOrchestrator

Main orchestrator for news-based signal generation.

```python
class NewsSignalOrchestrator:
    """Orchestrates news processing and signal generation."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the orchestrator.
        
        Args:
            config: Configuration dictionary
        """
    
    def process_signals(
        self, 
        tickers: List[str], 
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """Process news and generate signals for specified tickers.
        
        Args:
            tickers: List of ticker symbols to analyze
            hours_back: Hours of historical data to process
            
        Returns:
            Dictionary containing processing results
        """
    
    def generate_signals(
        self, 
        news_items: List[Dict[str, Any]]
    ) -> List[Signal]:
        """Generate trading signals from news items.
        
        Args:
            news_items: List of processed news items
            
        Returns:
            List of generated signals
        """
```

#### Signal Data Model

```python
@dataclass
class Signal:
    """Trading signal data structure."""
    
    signal_type: str              # "bullish", "bearish", "neutral"
    confidence: int               # 1-10 confidence score
    title: str                    # Signal title
    reasoning: str                # Signal reasoning
    etfs: List[str]               # Affected ETFs
    sector: str                   # Market sector
    article_url: Optional[str]    # Source article URL
    timestamp: datetime           # Signal timestamp
    search_term: str              # Original search term
    signal_id: Optional[str] = None
```

### Ingestion Module

#### NewsIngestionOrchestrator

Orchestrates news collection and processing.

```python
class NewsIngestionOrchestrator:
    """Orchestrates multi-source news ingestion."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the orchestrator.
        
        Args:
            config: Configuration dictionary
        """
    
    def process_news_cycle(
        self, 
        tickers: List[str], 
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """Process a complete news cycle.
        
        Args:
            tickers: List of ticker symbols
            hours_back: Hours of historical data
            
        Returns:
            Processing results dictionary
        """
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and statistics.
        
        Returns:
            Status dictionary
        """
```

#### NewsFilter

Filters and validates news items.

```python
class NewsFilter:
    """Intelligent news filtering system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the filter.
        
        Args:
            config: Filter configuration
        """
    
    def filter_news(
        self, 
        news_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter news items based on criteria.
        
        Args:
            news_items: Raw news items
            
        Returns:
            Filtered news items
        """
    
    def calculate_relevance_score(
        self, 
        news_item: Dict[str, Any]
    ) -> float:
        """Calculate relevance score for news item.
        
        Args:
            news_item: News item to score
            
        Returns:
            Relevance score (0.0-1.0)
        """
```

### Risk Module

#### PositionSizer

Calculates position sizes based on risk parameters.

```python
class PositionSizer:
    """Position sizing calculator."""
    
    def __init__(self):
        """Initialize the position sizer."""
    
    def calculate_kelly_size(
        self, 
        win_rate: float, 
        avg_win: float, 
        avg_loss: float, 
        confidence: float = 1.0
    ) -> PositionSizeResult:
        """Calculate position size using Kelly Criterion.
        
        Args:
            win_rate: Historical win rate (0.0-1.0)
            avg_win: Average winning trade amount
            avg_loss: Average losing trade amount
            confidence: Confidence factor (0.0-1.0)
            
        Returns:
            PositionSizeResult with calculated size
        """
    
    def calculate_fixed_percentage(
        self, 
        percentage: float, 
        price: float, 
        confidence: float = 1.0
    ) -> PositionSizeResult:
        """Calculate position size using fixed percentage.
        
        Args:
            percentage: Percentage of account to risk
            price: Current price of asset
            confidence: Confidence factor (0.0-1.0)
            
        Returns:
            PositionSizeResult with calculated size
        """
```

### Journal Module

#### AlertBatcher

Manages alert batching and delivery.

```python
class AlertBatcher:
    """Alert batching and delivery system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the alert batcher.
        
        Args:
            config: Alert configuration
        """
    
    def add_alert(
        self, 
        signal: Signal, 
        priority: int = 0
    ) -> None:
        """Add signal to alert queue.
        
        Args:
            signal: Trading signal
            priority: Alert priority (0-10)
        """
    
    def get_pending_alerts(self) -> List[Alert]:
        """Get pending alerts.
        
        Returns:
            List of pending alerts
        """
    
    def send_batch(self) -> Dict[str, Any]:
        """Send batched alerts.
        
        Returns:
            Delivery results
        """
```

#### PerformanceTracker

Tracks trading performance and analytics.

```python
class PerformanceTracker:
    """Performance tracking and analytics."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the performance tracker.
        
        Args:
            config: Performance configuration
        """
    
    def add_trade(
        self, 
        trade: Trade
    ) -> None:
        """Add trade to performance tracking.
        
        Args:
            trade: Trade data
        """
    
    def get_performance_summary(
        self, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance summary.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance summary
        """
    
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
```

### Options Module

#### OptionsScalpingStrategy

Options scalping strategy implementation.

```python
class OptionsScalpingStrategy:
    """Options scalping strategy."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the strategy.
        
        Args:
            config: Strategy configuration
        """
    
    def scan_for_opportunities(
        self, 
        symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """Scan for scalping opportunities.
        
        Args:
            symbols: List of symbols to scan
            
        Returns:
            List of opportunities
        """
    
    def calculate_greeks(
        self, 
        option_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate option Greeks.
        
        Args:
            option_data: Option contract data
            
        Returns:
            Dictionary of Greeks
        """
```

## 🖥️ CLI Interface

### Main Commands

#### Signals Commands

```bash
# Run signal processing
marketman signals run

# Check signal status
marketman signals status

# Run signal backtest (not implemented)
marketman signals backtest
```

#### Alerts Commands

```bash
# Check for new alerts
marketman alerts check

# Send pending alerts
marketman alerts send

# Check alert status
marketman alerts status
```

#### Performance Commands

```bash
# Show performance dashboard
marketman performance show

# Update performance data
marketman performance update

# Export performance data
marketman performance export
```

#### Options Commands

```bash
# Run options scalping
marketman options scalp

# Analyze options
marketman options analyze

# Run options backtest (not implemented)
marketman options backtest
```

#### Risk Commands

```bash
# Analyze portfolio risk
marketman risk analyze

# Check risk limits
marketman risk limits

# Calculate position size
marketman risk position-size
```

#### News Commands

```bash
# Check news status
marketman news status

# Run news processing cycle
marketman news cycle

# Test news sources
marketman news test

# Generate signals from news
marketman news signals
```

#### Journal Commands

```bash
# List trades
marketman journal list-trades

# Show performance
marketman journal performance

# Show signal analysis
marketman journal signals

# Setup Fidelity integration
marketman journal setup-fidelity

# Import Fidelity trades
marketman journal import-fidelity

# Add manual trade
marketman journal add-trade

# Add manual signal
marketman journal add-signal

# Sync with Notion
marketman journal sync-notion

# Analyze performance
marketman journal analyze
```

#### Configuration Commands

```bash
# Validate configuration
marketman config validate

# Show configuration
marketman config show

# Reload configuration
marketman config reload
```

### Command Options

#### Global Options

```bash
-v, --verbose          # Enable verbose logging
--config PATH          # Path to configuration file
```

#### Journal-Specific Options

```bash
--symbol, -s SYMBOL    # Symbol filter
--days, -d DAYS        # Number of days (default: 30)
--output, -o FILE      # Output file
--action, -a ACTION    # Trade action (Buy/Sell)
--quantity, -q QTY     # Trade quantity
--price, -p PRICE      # Trade price
--date DATE            # Trade date
--confidence, -c CONF  # Signal confidence
--notes, -n NOTES      # Trade notes
--type, -t TYPE        # Signal type
--direction DIR        # Signal direction
--reasoning, -r REASON # Signal reasoning
--source SOURCE        # Signal source
--email, -e EMAIL      # Email for Fidelity setup
--password PASSWORD    # Password for Fidelity setup
```

## 🔌 Integrations

### Pushover Integration

```python
class PushoverClient:
    """Pushover notification client."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the client.
        
        Args:
            config: Pushover configuration
        """
    
    def send_notification(
        self, 
        message: str, 
        title: str = None, 
        priority: int = 0
    ) -> bool:
        """Send notification.
        
        Args:
            message: Notification message
            title: Notification title
            priority: Priority level (0-10)
            
        Returns:
            Success status
        """
```

### Notion Integration

```python
class NotionReporter:
    """Notion reporting integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the reporter.
        
        Args:
            config: Notion configuration
        """
    
    def add_signal(
        self, 
        signal: Signal
    ) -> bool:
        """Add signal to Notion database.
        
        Args:
            signal: Trading signal
            
        Returns:
            Success status
        """
    
    def add_trade(
        self, 
        trade: Trade
    ) -> bool:
        """Add trade to Notion database.
        
        Args:
            trade: Trade data
            
        Returns:
            Success status
        """
```

### Fidelity Integration

```python
class FidelityIntegration:
    """Fidelity trade import integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the integration.
        
        Args:
            config: Fidelity configuration
        """
    
    def import_trades(
        self, 
        days_back: int = 30
    ) -> List[Trade]:
        """Import trades from Fidelity.
        
        Args:
            days_back: Number of days to import
            
        Returns:
            List of imported trades
        """
```

### Gmail Integration

```python
class GmailOrganizer:
    """Gmail organization integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the organizer.
        
        Args:
            config: Gmail configuration
        """
    
    def organize_marketman_emails(
        self, 
        days_back: int = 3, 
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Organize MarketMan emails.
        
        Args:
            days_back: Number of days to process
            dry_run: Run without making changes
            
        Returns:
            Organization results
        """
```

## 📊 Data Models

### Core Data Models

```python
@dataclass
class NewsItem:
    """News item data structure."""
    id: Optional[int]
    title: str
    content: str
    source: str
    url: Optional[str]
    timestamp: datetime
    tickers: List[str]
    relevance_score: float
    sentiment_score: float
    created_at: datetime

@dataclass
class Signal:
    """Trading signal data structure."""
    id: Optional[int]
    signal_type: str
    confidence: int
    title: str
    reasoning: str
    etfs: List[str]
    sector: str
    article_url: Optional[str]
    search_term: str
    timestamp: datetime
    created_at: datetime
    signal_id: Optional[str] = None

@dataclass
class Trade:
    """Trade data structure."""
    id: Optional[int]
    signal_id: Optional[str]
    symbol: str
    action: str  # "Buy" or "Sell"
    quantity: float
    price: float
    timestamp: datetime
    notes: Optional[str]
    created_at: datetime
    realized_pnl: Optional[float] = None
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None

@dataclass
class Alert:
    """Alert data structure."""
    id: Optional[int]
    signal: Signal
    priority: int
    status: str  # "pending", "sent", "failed"
    created_at: datetime
    sent_at: Optional[datetime] = None
```

### Configuration Models

```python
@dataclass
class NewsConfig:
    """News processing configuration."""
    max_daily_headlines: int = 50
    max_daily_ai_calls: int = 75
    min_relevance_score: float = 0.15
    batch_size: int = 10
    sources: List[str] = field(default_factory=list)

@dataclass
class RiskConfig:
    """Risk management configuration."""
    max_daily_loss: float = 0.05
    max_position_size: float = 0.02
    stop_loss_percent: float = 2.0
    max_kelly_fraction: float = 0.25
    max_sector_exposure: float = 0.3

@dataclass
class AlertConfig:
    """Alert configuration."""
    batch_strategy: str = "smart_batch"
    max_daily_alerts: int = 10
    confidence_threshold: int = 7
    pushover_enabled: bool = True
    notion_enabled: bool = False
```

## ⚙️ Configuration

### Configuration Files

#### settings.yaml (Main Configuration)

```yaml
# News Processing
news_ingestion:
  max_daily_headlines: 50
  max_daily_ai_calls: 75
  min_relevance_score: 0.15
  batch_size: 10
  sources:
    - finnhub
    - newsapi
    - newdata

# Risk Management
risk:
  max_daily_loss: 0.05
  max_position_size: 0.02
  stop_loss_percent: 2.0
  max_kelly_fraction: 0.25
  max_sector_exposure: 0.3

# Alerts
alerts:
  batch_strategy: smart_batch
  max_daily_alerts: 10
  confidence_threshold: 7
  pushover_enabled: true
  notion_enabled: false

# Database
database:
  type: sqlite
  path: data/marketman.db
  backup_enabled: true
  backup_interval_hours: 24

# Logging
logging:
  level: INFO
  file: logs/marketman.log
  max_size_mb: 100
  backup_count: 5
```

#### strategies.yaml (Strategy Configuration)

```yaml
# ETF Signal Strategy
etf_signals:
  name: "ETF Momentum Strategy"
  enabled: true
  symbols:
    - "QQQ"
    - "SPY"
    - "IWM"
    - "XLF"
    - "XLE"
  
  technical_indicators:
    rsi_period: 14
    rsi_oversold: 30
    rsi_overbought: 70
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
    sma_short: 20
    sma_long: 50

# Options Scalping Strategy
options_scalping:
  name: "QQQ/SPY Options Scalping"
  enabled: false
  symbols:
    - "QQQ"
    - "SPY"
  
  entry_conditions:
    min_iv_percentile: 30
    max_iv_percentile: 80
    min_dte: 1
    max_dte: 7
    min_bid_ask_spread: 0.05
```

#### brokers.yaml (Broker Configuration)

```yaml
# Paper Trading (Default)
paper_trading:
  enabled: true
  name: "Paper Trading"
  account_type: "paper"
  initial_balance: 25000
  commission_per_trade: 0.0
  margin_enabled: false

# Global Settings
global_settings:
  max_position_size: 2500
  max_daily_trades: 20
  max_daily_loss: 500
  default_quantity: 100
  min_order_size: 1
  max_order_size: 2500
```

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# News APIs
FINNHUB_KEY=your_finnhub_key
NEWS_API=your_newsapi_key
NEWS_DATA_KEY=your_newdata_key

# Notifications
PUSHOVER_TOKEN=your_pushover_token
PUSHOVER_USER=your_pushover_user

# Notion (optional)
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id

# Fidelity (optional)
FIDELITY_EMAIL=your_fidelity_email
FIDELITY_PASSWORD=your_fidelity_password

# Gmail (optional)
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REFRESH_TOKEN=your_gmail_refresh_token
```

## 🗄️ Database

### Database Schema

#### News Items Table

```sql
CREATE TABLE news_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT,
    timestamp DATETIME NOT NULL,
    tickers TEXT,  -- JSON array
    relevance_score REAL NOT NULL,
    sentiment_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_news_timestamp ON news_items(timestamp);
CREATE INDEX idx_news_source ON news_items(source);
CREATE INDEX idx_news_tickers ON news_items(tickers);
```

#### Signals Table

```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    title TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    etfs TEXT NOT NULL,  -- JSON array
    sector TEXT NOT NULL,
    article_url TEXT,
    search_term TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signals_confidence ON signals(confidence);
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_signals_type ON signals(signal_type);
```

#### Trades Table

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id TEXT,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,  -- "Buy" or "Sell"
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    timestamp DATETIME NOT NULL,
    notes TEXT,
    realized_pnl REAL,
    exit_price REAL,
    exit_timestamp DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_signal_id ON trades(signal_id);
```

#### Alerts Table

```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',  -- "pending", "sent", "failed"
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    sent_at DATETIME,
    FOREIGN KEY (signal_id) REFERENCES signals(id)
);

CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_priority ON alerts(priority);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
```

### Database Operations

#### Connection Management

```python
class DatabaseManager:
    """Database connection and operation manager."""
    
    def __init__(self, db_path: str):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.connection = None
    
    def connect(self) -> None:
        """Establish database connection."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
    
    def execute_query(
        self, 
        query: str, 
        params: tuple = None
    ) -> List[Dict]:
        """Execute a query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
        """
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def execute_transaction(
        self, 
        queries: List[tuple]
    ) -> bool:
        """Execute multiple queries in transaction.
        
        Args:
            queries: List of (query, params) tuples
            
        Returns:
            Success status
        """
        try:
            cursor = self.connection.cursor()
            for query, params in queries:
                cursor.execute(query, params)
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            raise e
```

#### Data Access Patterns

```python
class NewsRepository:
    """News data access layer."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository.
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
    
    def add_news_item(self, news_item: NewsItem) -> int:
        """Add news item to database.
        
        Args:
            news_item: News item to add
            
        Returns:
            Inserted item ID
        """
        query = """
        INSERT INTO news_items (title, content, source, url, timestamp, 
                               tickers, relevance_score, sentiment_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            news_item.title,
            news_item.content,
            news_item.source,
            news_item.url,
            news_item.timestamp,
            json.dumps(news_item.tickers),
            news_item.relevance_score,
            news_item.sentiment_score
        )
        
        cursor = self.db.connection.cursor()
        cursor.execute(query, params)
        self.db.connection.commit()
        return cursor.lastrowid
    
    def get_news_by_tickers(
        self, 
        tickers: List[str], 
        hours_back: int = 24
    ) -> List[Dict]:
        """Get news items by tickers.
        
        Args:
            tickers: List of ticker symbols
            hours_back: Hours of historical data
            
        Returns:
            List of news items
        """
        query = """
        SELECT * FROM news_items 
        WHERE timestamp >= datetime('now', '-{} hours')
        AND tickers LIKE ?
        ORDER BY timestamp DESC
        """
        
        results = []
        for ticker in tickers:
            params = (f'%{ticker}%',)
            items = self.db.execute_query(query.format(hours_back), params)
            results.extend(items)
        
        return results
```

---

**Next**: [User Guide](user-guide.md) for usage instructions 