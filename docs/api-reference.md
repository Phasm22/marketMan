# API Reference

Technical reference for MarketMan's core APIs and interfaces.

## 📋 Table of Contents

- [Core Modules](#core-modules)
- [Integrations](#integrations)
- [CLI Interface](#cli-interface)
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
            price: Price per unit
            confidence: Confidence factor
            
        Returns:
            PositionSizeResult with calculated size
        """
```

#### PositionSizeResult

```python
@dataclass
class PositionSizeResult:
    """Result of position sizing calculation."""
    
    quantity: int                 # Number of units
    dollar_amount: float          # Total dollar amount
    risk_amount: float            # Amount at risk
    method: str                   # Method used
    confidence: float             # Confidence level
```

### Journal Module

#### TradeJournal

Manages trade recording and performance tracking.

```python
class TradeJournal:
    """Trade journal and performance tracker."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the trade journal.
        
        Args:
            db_path: Database path
        """
    
    def add_trade(
        self, 
        signal_id: str, 
        symbol: str, 
        entry_price: float, 
        quantity: int, 
        timestamp: datetime
    ) -> str:
        """Add a new trade entry.
        
        Args:
            signal_id: Associated signal ID
            symbol: Trading symbol
            entry_price: Entry price
            quantity: Number of shares
            timestamp: Trade timestamp
            
        Returns:
            Trade ID
        """
    
    def close_trade(
        self, 
        trade_id: str, 
        exit_price: float, 
        timestamp: datetime
    ) -> float:
        """Close a trade and calculate P&L.
        
        Args:
            trade_id: Trade ID to close
            exit_price: Exit price
            timestamp: Exit timestamp
            
        Returns:
            Realized P&L
        """
    
    def calculate_performance_summary(
        self, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Calculate performance summary.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance metrics dictionary
        """
```

#### AlertBatcher

Manages alert batching and delivery.

```python
class AlertBatcher:
    """Manages alert batching and delivery strategies."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the alert batcher."""
    
    def add_alert(
        self, 
        alert: PendingAlert, 
        strategy: BatchStrategy = BatchStrategy.SMART_BATCH
    ) -> None:
        """Add an alert to the batching queue.
        
        Args:
            alert: Alert to add
            strategy: Batching strategy
        """
    
    def process_pending(
        self, 
        fallback_warning: Optional[str] = None
    ) -> Dict[str, bool]:
        """Process pending alert batches.
        
        Args:
            fallback_warning: Warning message for fallback
            
        Returns:
            Dictionary of strategy results
        """
    
    def get_pending_alerts(
        self, 
        strategy: Optional[BatchStrategy] = None
    ) -> List[PendingAlert]:
        """Get pending alerts.
        
        Args:
            strategy: Filter by strategy
            
        Returns:
            List of pending alerts
        """
```

## 🔌 Integrations

### Pushover Integration

#### PushoverNotifier

```python
class PushoverNotifier:
    """Pushover notification client."""
    
    def __init__(self):
        """Initialize the notifier."""
    
    def send_signal_alert(
        self, 
        signal: Signal, 
        priority: int = 0
    ) -> bool:
        """Send signal alert notification.
        
        Args:
            signal: Signal to send
            priority: Notification priority
            
        Returns:
            True if sent successfully
        """
    
    def send_risk_warning(
        self, 
        warning_type: str, 
        message: str, 
        affected_symbols: Optional[List[str]] = None,
        severity: str = "medium"
    ) -> bool:
        """Send risk warning notification.
        
        Args:
            warning_type: Type of warning
            message: Warning message
            affected_symbols: Affected symbols
            severity: Warning severity
            
        Returns:
            True if sent successfully
        """
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get rate limit status.
        
        Returns:
            Rate limit information
        """
```

### Notion Integration

#### NotionReporter

```python
class NotionReporter:
    """Notion database integration."""
    
    def __init__(self, token: str, database_id: str):
        """Initialize the reporter.
        
        Args:
            token: Notion API token
            database_id: Database ID
        """
    
    def add_signal(
        self, 
        signal: Signal
    ) -> str:
        """Add signal to Notion database.
        
        Args:
            signal: Signal to add
            
        Returns:
            Notion page ID
        """
    
    def add_trade(
        self, 
        trade: TradeEntry
    ) -> str:
        """Add trade to Notion database.
        
        Args:
            trade: Trade to add
            
        Returns:
            Notion page ID
        """
    
    def update_performance(
        self, 
        metrics: Dict[str, Any]
    ) -> str:
        """Update performance metrics.
        
        Args:
            metrics: Performance metrics
            
        Returns:
            Notion page ID
        """
```

### Gmail Integration

#### GmailPoller

```python
class GmailPoller:
    """Gmail polling for Google Alerts."""
    
    def __init__(self, credentials_path: str, token_path: str):
        """Initialize the poller.
        
        Args:
            credentials_path: Path to credentials file
            token_path: Path to token file
        """
    
    def get_google_alerts(self) -> List[Dict[str, Any]]:
        """Get Google Alerts from Gmail.
        
        Returns:
            List of alert data
        """
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            True if successful
        """
```

## 🖥️ CLI Interface

### Main CLI

```python
def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code
    """
```

### Available Commands

#### News Commands
```bash
python marketman news cycle          # Process news cycle
python marketman news status          # Show news system status
python marketman news filter          # Test news filtering
```

#### Signal Commands
```bash
python marketman signals run          # Generate signals
python marketman signals status        # Show signal status
python marketman signals backtest      # Run signal backtest
```

#### Alert Commands
```bash
python marketman alerts check          # Check for alerts
python marketman alerts send           # Send pending alerts
python marketman alerts status         # Show alert status
```

#### Performance Commands
```bash
python marketman performance show      # Show performance dashboard
python marketman performance export    # Export performance data
```

#### Configuration Commands
```bash
python marketman config validate       # Validate configuration
python marketman config show           # Show current config
python marketman config reload         # Reload configuration
```

#### System Commands
```bash
python marketman status                # System status
python marketman test                  # Run tests
python marketman lint                  # Code quality checks
```

## 📊 Data Models

### Core Data Structures

#### NewsItem
```python
@dataclass
class NewsItem:
    """News item data structure."""
    
    title: str                       # News title
    content: str                     # News content
    source: str                      # News source
    url: Optional[str]               # Article URL
    timestamp: datetime              # Publication timestamp
    tickers: List[str]               # Mentioned tickers
    relevance_score: float           # Relevance score (0.0-1.0)
    sentiment_score: float           # Sentiment score (-1.0 to 1.0)
    news_id: Optional[str] = None
```

#### TradeEntry
```python
@dataclass
class TradeEntry:
    """Trade entry data structure."""
    
    signal_id: str                   # Associated signal ID
    symbol: str                      # Trading symbol
    entry_price: float               # Entry price
    exit_price: Optional[float]      # Exit price
    quantity: int                    # Number of shares
    entry_timestamp: datetime        # Entry timestamp
    exit_timestamp: Optional[datetime] = None
    realized_pnl: Optional[float] = None
    trade_id: Optional[str] = None
```

#### PerformanceMetrics
```python
@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    
    total_trades: int                # Total number of trades
    winning_trades: int              # Number of winning trades
    losing_trades: int               # Number of losing trades
    total_pnl: float                 # Total P&L
    win_rate: float                  # Win rate percentage
    avg_win: float                   # Average winning trade
    avg_loss: float                  # Average losing trade
    profit_factor: float             # Profit factor
    max_drawdown: float              # Maximum drawdown
    sharpe_ratio: float              # Sharpe ratio
    sortino_ratio: float             # Sortino ratio
    max_consecutive_losses: int      # Max consecutive losses
    max_consecutive_wins: int        # Max consecutive wins
    avg_holding_period: float        # Average holding period
    signal_accuracy: float           # Signal accuracy percentage
    avg_signal_confidence: float     # Average signal confidence
    sector_performance: Dict[str, float]  # Performance by sector
    daily_pnl: Dict[str, float]      # Daily P&L
    weekly_pnl: Dict[str, float]     # Weekly P&L
    monthly_pnl: Dict[str, float]    # Monthly P&L
```

## ⚙️ Configuration

### Configuration Loader

```python
class ConfigLoader:
    """Centralized configuration loader."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize the loader.
        
        Args:
            config_dir: Configuration directory
        """
    
    def load_settings(self) -> Dict[str, Any]:
        """Load main settings configuration.
        
        Returns:
            Settings dictionary
        """
    
    def load_strategies(self) -> Dict[str, Any]:
        """Load strategy configuration.
        
        Returns:
            Strategies dictionary
        """
    
    def load_brokers(self) -> Dict[str, Any]:
        """Load broker configuration.
        
        Returns:
            Brokers dictionary
        """
    
    def get_setting(
        self, 
        key_path: str, 
        default: Any = None
    ) -> Any:
        """Get a specific setting value.
        
        Args:
            key_path: Dot-separated path to setting
            default: Default value if not found
            
        Returns:
            Setting value
        """
    
    def is_feature_enabled(self, feature_path: str) -> bool:
        """Check if a feature is enabled.
        
        Args:
            feature_path: Feature path
            
        Returns:
            True if enabled
        """
```

### Configuration Functions

```python
def get_config() -> ConfigLoader:
    """Get global configuration loader.
    
    Returns:
        Global ConfigLoader instance
    """

def get_setting(key_path: str, default: Any = None) -> Any:
    """Get setting value.
    
    Args:
        key_path: Setting path
        default: Default value
        
    Returns:
        Setting value
    """

def is_feature_enabled(feature_path: str) -> bool:
    """Check if feature is enabled.
    
    Args:
        feature_path: Feature path
        
    Returns:
        True if enabled
    """
```

## 🗄️ Database

### Database Manager

```python
class DatabaseManager:
    """Database abstraction layer."""
    
    def __init__(self, db_path: str):
        """Initialize the manager.
        
        Args:
            db_path: Database file path
        """
    
    def init_database(self) -> None:
        """Initialize database tables."""
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute a database query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Query results
        """
    
    def execute_transaction(
        self, 
        queries: List[Tuple[str, Optional[Tuple]]]
    ) -> bool:
        """Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples
            
        Returns:
            True if successful
        """
```

### Database Instances

```python
# Global database instances
market_memory_db = DatabaseManager("data/marketman_memory.db")
alert_batch_db = DatabaseManager("data/alert_batch.db")
trade_journal_db = DatabaseManager("data/trade_journal.db")
```

### Database Schema

#### News Items Table
```sql
CREATE TABLE news_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    source TEXT,
    url TEXT,
    timestamp DATETIME NOT NULL,
    tickers TEXT,  -- JSON array
    relevance_score REAL,
    sentiment_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Signals Table
```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    title TEXT NOT NULL,
    reasoning TEXT,
    etfs TEXT,  -- JSON array
    sector TEXT,
    article_url TEXT,
    search_term TEXT,
    timestamp DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Trades Table
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id TEXT,
    symbol TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    quantity INTEGER NOT NULL,
    entry_timestamp DATETIME NOT NULL,
    exit_timestamp DATETIME,
    realized_pnl REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Alert Batches Table
```sql
CREATE TABLE alert_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy TEXT NOT NULL,
    alerts TEXT,  -- JSON array
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME
);
```

## 🔧 Utility Functions

### Formatting Utilities

```python
def format_price_context(price: float, change: float) -> str:
    """Format price with context.
    
    Args:
        price: Current price
        change: Price change
        
    Returns:
        Formatted price string
    """

def format_volume_with_liquidity(volume: int) -> str:
    """Format volume with liquidity context.
    
    Args:
        volume: Trading volume
        
    Returns:
        Formatted volume string
    """

def format_conviction_tier(confidence: int) -> str:
    """Format confidence as conviction tier.
    
    Args:
        confidence: Confidence score (1-10)
        
    Returns:
        Conviction tier string
    """

def format_signal_summary(signal: Signal) -> str:
    """Format signal as summary string.
    
    Args:
        signal: Signal to format
        
    Returns:
        Formatted summary
    """
```

### Validation Utilities

```python
def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol.
    
    Args:
        symbol: Symbol to validate
        
    Returns:
        True if valid
    """

def validate_percentage(value: float) -> bool:
    """Validate percentage value.
    
    Args:
        value: Percentage to validate
        
    Returns:
        True if valid
    """

def validate_confidence_score(score: int) -> bool:
    """Validate confidence score.
    
    Args:
        score: Score to validate
        
    Returns:
        True if valid
    """

def validate_signal_data(data: Dict[str, Any]) -> bool:
    """Validate signal data structure.
    
    Args:
        data: Signal data to validate
        
    Returns:
        True if valid
    """
```

---

**Next**: [Architecture](architecture.md) for system design details 