# Architecture

System architecture and design patterns for MarketMan.

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Data Flow](#data-flow)
- [Component Design](#component-design)
- [Database Design](#database-design)
- [Security](#security)
- [Performance](#performance)
- [Scalability](#scalability)

## 🎯 Overview

MarketMan is built as a modular, event-driven system with clear separation of concerns. The architecture follows these principles:

- **Modularity**: Each component has a single responsibility
- **Testability**: All components are easily testable
- **Configuration**: External configuration for all settings
- **Error Handling**: Graceful error handling and logging
- **Performance**: Efficient processing and memory usage

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   News Sources  │    │   Data Storage  │    │   Notifications │
│                 │    │                 │    │                 │
│ • Finnhub       │    │ • SQLite        │    │ • Pushover      │
│ • NewsAPI       │    │ • JSON Files    │    │ • Notion        │
│ • NewData       │    │ • Memory Cache  │    │ • Email         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Processing Engine                       │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Ingestion  │  │   Signals   │  │    Risk     │            │
│  │             │  │             │  │             │            │
│  │ • Filtering │  │ • Analysis  │  │ • Position  │            │
│  │ • Batching  │  │ • Scoring   │  │   Sizing    │            │
│  │ • Validation│  │ • Generation│  │ • Kelly     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Journal   │  │   Options   │  │   Utils     │            │
│  │             │  │             │  │             │            │
│  │ • Tracking  │  │ • Scalping  │  │ • Config    │            │
│  │ • Performance│  │ • Strategy  │  │ • Formatting│            │
│  │ • Analytics │  │ • Greeks    │  │ • Validation│            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Interface │    │   Monitoring    │    │   External      │
│                 │    │                 │    │   Integrations  │
│ • Commands      │    │ • Health Checks │    │ • Fidelity      │
│ • Status        │    │ • System Status │    │ • Gmail         │
│ • Configuration │    │ • Alerts        │    │ • Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Architecture

#### Core Components

1. **Ingestion Layer** ✅ **IMPLEMENTED**
   - Multi-source news collection (Finnhub, NewsAPI, NewData)
   - Intelligent filtering with relevance scoring
   - Batch processing for efficiency
   - Quality scoring and validation

2. **Signal Generation Layer** ✅ **IMPLEMENTED**
   - AI-powered analysis using GPT-4
   - Technical indicators and pattern recognition
   - Multi-source validation
   - Confidence scoring (1-10 scale)

3. **Risk Management Layer** ✅ **IMPLEMENTED**
   - Position sizing using Kelly Criterion
   - Portfolio risk management
   - Stop loss calculations
   - Risk limits enforcement

4. **Journal Layer** ✅ **IMPLEMENTED**
   - Trade tracking and logging
   - Performance analytics and reporting
   - Signal logging and analysis
   - Fidelity integration for trade import

5. **Integration Layer** ✅ **IMPLEMENTED**
   - Pushover notifications
   - Notion integration for reporting
   - Gmail organization
   - Fidelity trade import

6. **Options Trading Layer** ✅ **IMPLEMENTED**
   - Options scalping strategy
   - Greeks calculations
   - Position management

7. **CLI Interface** ✅ **IMPLEMENTED**
   - Command-line interface for all operations
   - Status monitoring
   - Configuration management

8. **Monitoring Layer** ✅ **IMPLEMENTED**
   - System health monitoring
   - Host availability checks
   - Automated alerts

## 🔄 Data Flow

### News Processing Pipeline

```
1. Collection
   ┌─────────────┐
   │ News Sources│ → Raw news items
   └─────────────┘
           │
           ▼
2. Filtering
   ┌─────────────┐
   │ News Filter │ → Filtered items
   └─────────────┘
           │
           ▼
3. Batching
   ┌─────────────┐
   │ News Batcher│ → Batched items
   └─────────────┘
           │
           ▼
4. AI Analysis
   ┌─────────────┐
   │ GPT-4 API   │ → Analyzed items
   └─────────────┘
           │
           ▼
5. Signal Generation
   ┌─────────────┐
   │ Signal Gen  │ → Trading signals
   └─────────────┘
           │
           ▼
6. Validation
   ┌─────────────┐
   │ Multi-Source│ → Validated signals
   │ Validation  │
   └─────────────┘
           │
           ▼
7. Output
   ┌─────────────┐
   │ Alerts      │ → Notifications
   │ Database    │ → Storage
   │ Reports     │ → Analytics
   └─────────────┘
```

### Signal Generation Flow

```
News Item → Sentiment Analysis → Technical Analysis → Risk Assessment → Signal
    │              │                    │                    │
    ▼              ▼                    ▼                    ▼
Content        Sentiment Score      Technical Score      Risk Score
Source         Confidence Level     Pattern Match        Position Size
Tickers        Market Impact        Volume Analysis      Portfolio Limits
Timestamp      Reasoning            Indicators           Stop Loss
```

### Alert Processing Flow

```
Signal → Alert Batcher → Batching Strategy → Notification → Delivery
  │           │              │                    │
  ▼           ▼              ▼                    ▼
High Conf    Queue          Smart Batch         Pushover
Medium Conf  Priority       Time Window         Notion
Low Conf     Rate Limit     Daily Digest        Email
```

## 🧩 Component Design

### Orchestrator Pattern

Each major component uses an orchestrator pattern:

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
            'analyzer': NewsAnalyzer(self.config),
            'validator': SignalValidator(self.config)
        }
    
    def process(self, input_data: Any) -> Any:
        """Process data through the pipeline."""
        try:
            # Step 1: Filter
            filtered_data = self.subcomponents['filter'].process(input_data)
            
            # Step 2: Batch
            batched_data = self.subcomponents['batcher'].process(filtered_data)
            
            # Step 3: Analyze
            analyzed_data = self.subcomponents['analyzer'].process(batched_data)
            
            # Step 4: Validate
            validated_data = self.subcomponents['validator'].process(analyzed_data)
            
            return validated_data
            
        except Exception as e:
            self._handle_error(e)
            return None
```

### Strategy Pattern

Used for different processing strategies:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

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

class ImmediateBatchingStrategy(BatchingStrategy):
    """Immediate processing without batching."""
    
    def should_batch(self, items: List[Any]) -> bool:
        return True  # Always process immediately
    
    def create_batch(self, items: List[Any]) -> Dict[str, Any]:
        return {
            'items': items,
            'batch_type': 'immediate',
            'created_at': datetime.now()
        }
```

### Factory Pattern

Used for creating different types of components:

```python
class ComponentFactory:
    """Factory for creating components."""
    
    @staticmethod
    def create_news_source(source_type: str, config: Dict[str, Any]):
        """Create news source based on type."""
        if source_type == 'finnhub':
            return FinnhubNewsSource(config)
        elif source_type == 'newsapi':
            return NewsAPISource(config)
        elif source_type == 'newdata':
            return NewDataSource(config)
        else:
            raise ValueError(f"Unknown source type: {source_type}")
    
    @staticmethod
    def create_notifier(notifier_type: str, config: Dict[str, Any]):
        """Create notifier based on type."""
        if notifier_type == 'pushover':
            return PushoverNotifier(config)
        elif notifier_type == 'notion':
            return NotionNotifier(config)
        elif notifier_type == 'email':
            return EmailNotifier(config)
        else:
            raise ValueError(f"Unknown notifier type: {notifier_type}")
```

### Observer Pattern

Used for event handling and notifications:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class EventObserver(ABC):
    """Abstract event observer."""
    
    @abstractmethod
    def update(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle event update."""
        pass

class SignalObserver(EventObserver):
    """Observer for signal events."""
    
    def __init__(self, notifiers: List[Any]):
        self.notifiers = notifiers
    
    def update(self, event_type: str, data: Dict[str, Any]) -> None:
        if event_type == 'signal_generated':
            self._handle_signal(data)
        elif event_type == 'signal_validated':
            self._handle_validated_signal(data)
    
    def _handle_signal(self, signal_data: Dict[str, Any]) -> None:
        """Handle new signal."""
        for notifier in self.notifiers:
            notifier.send_signal_alert(signal_data)
    
    def _handle_validated_signal(self, signal_data: Dict[str, Any]) -> None:
        """Handle validated signal."""
        # Additional processing for validated signals
        pass

class EventManager:
    """Manages event observers."""
    
    def __init__(self):
        self.observers: Dict[str, List[EventObserver]] = {}
    
    def subscribe(self, event_type: str, observer: EventObserver) -> None:
        """Subscribe observer to event type."""
        if event_type not in self.observers:
            self.observers[event_type] = []
        self.observers[event_type].append(observer)
    
    def notify(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notify all observers of event."""
        if event_type in self.observers:
            for observer in self.observers[event_type]:
                observer.update(event_type, data)
```

## 🗄️ Database Design

### Database Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                           │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Market      │  │ Alert       │  │ Trade       │        │
│  │ Memory      │  │ Batching    │  │ Journal     │        │
│  │ Database    │  │ Database    │  │ Database    │        │
│  │             │  │             │  │             │        │
│  │ • News      │  │ • Alerts    │  │ • Trades    │        │
│  │ • Signals   │  │ • Batches   │  │ • P&L       │        │
│  │ • Patterns  │  │ • History   │  │ • Analytics │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Performance │  │ User        │  │ System      │        │
│  │ Tracking    │  │ Settings    │  │ Logs        │        │
│  │ Database    │  │ Database    │  │ Database    │        │
│  │             │  │             │  │             │        │
│  │ • Metrics   │  │ • Config    │  │ • Events    │        │
│  │ • Reports   │  │ • Preferences│  │ • Errors    │        │
│  │ • History   │  │ • Profiles   │  │ • Debug     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Database Abstraction

```python
class DatabaseManager:
    """Abstract database manager."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
    
    def connect(self) -> None:
        """Establish database connection."""
        pass
    
    def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query."""
        pass
    
    def execute_transaction(self, queries: List[tuple]) -> bool:
        """Execute multiple queries in transaction."""
        pass

class SQLiteManager(DatabaseManager):
    """SQLite implementation."""
    
    def connect(self) -> None:
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
```

### Data Models

```python
@dataclass
class NewsItem:
    """News item data model."""
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
    """Signal data model."""
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

@dataclass
class Trade:
    """Trade data model."""
    id: Optional[int]
    signal_id: str
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    entry_timestamp: datetime
    exit_timestamp: Optional[datetime]
    realized_pnl: Optional[float]
    created_at: datetime
```

## 🔒 Security

### Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layer                           │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ API Key     │  │ Rate        │  │ Input       │        │
│  │ Management  │  │ Limiting    │  │ Validation  │        │
│  │             │  │             │  │             │        │
│  │ • Encryption│  │ • Per API   │  │ • Sanitize  │        │
│  │ • Rotation  │  │ • Per User  │  │ • Validate  │        │
│  │ • Storage   │  │ • Per Hour  │  │ • Escape    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Access      │  │ Data        │  │ Audit       │        │
│  │ Control     │  │ Protection  │  │ Logging     │        │
│  │             │  │             │  │             │        │
│  │ • Auth      │  │ • Encryption│  │ • Events    │        │
│  │ • Authz     │  │ • Backup    │  │ • Changes   │        │
│  │ • Sessions  │  │ • Recovery  │  │ • Access    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Security Measures

1. **API Key Management**
   - Encrypted storage in credentials files
   - Environment variable support
   - Access logging

2. **Rate Limiting**
   - Per-API limits implemented
   - Time-based throttling
   - Request queuing

3. **Input Validation**
   - Data sanitization
   - Type checking
   - Length limits

4. **Access Control**
   - File-based configuration
   - Environment-based secrets
   - Secure credential storage

## ⚡ Performance

### Performance Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Performance Layer                        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Caching     │  │ Async       │  │ Batch       │        │
│  │             │  │ Processing  │  │ Processing  │        │
│  │ • Memory    │  │             │  │             │        │
│  │ • Files     │  │ • Threads   │  │ • Groups    │        │
│  │ • Database  │  │ • Coroutines│  │ • Batches   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Database    │  │ Memory      │  │ Monitoring  │        │
│  │ Optimization│  │ Management  │  │             │        │
│  │             │  │             │  │             │        │
│  │ • Indexes   │  │ • Pooling   │  │ • Metrics   │        │
│  │ • Queries   │  │ • Garbage   │  │ • Alerts    │        │
│  │ • Connection│  │   Collection│  │ • Profiling │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Performance Optimizations

1. **Caching Strategy**
   ```python
   class CacheManager:
       """Multi-level caching."""
       
       def __init__(self):
           self.memory_cache = {}
           self.file_cache = FileCache()
       
       def get(self, key: str) -> Any:
           # Check memory first
           if key in self.memory_cache:
               return self.memory_cache[key]
           
           # Check file cache
           value = self.file_cache.get(key)
           if value:
               self.memory_cache[key] = value
               return value
           
           return None
   ```

2. **Batch Processing**
   ```python
   class BatchProcessor:
       """Batch processing for efficiency."""
       
       def __init__(self, batch_size: int = 10):
           self.batch_size = batch_size
           self.queue = []
       
       def add_item(self, item: Any) -> None:
           """Add item to batch queue."""
           self.queue.append(item)
           
           if len(self.queue) >= self.batch_size:
               self.process_batch()
       
       def process_batch(self) -> None:
           """Process current batch."""
           if self.queue:
               # Process all items in batch
               self._process_items(self.queue)
               self.queue.clear()
   ```

3. **Database Optimization**
   ```sql
   -- Indexes for performance
   CREATE INDEX idx_news_timestamp ON news_items(timestamp);
   CREATE INDEX idx_news_source ON news_items(source);
   CREATE INDEX idx_signals_confidence ON signals(confidence);
   CREATE INDEX idx_trades_symbol ON trades(symbol);
   ```

## 📈 Scalability

### Scalability Patterns

1. **Horizontal Scaling**
   - Multiple instances support
   - Database sharding ready
   - Load balancing compatible

2. **Vertical Scaling**
   - Resource optimization
   - Memory management
   - CPU utilization

3. **Modular Architecture**
   ```python
   # Service decomposition
   services = {
       'news-ingestion': NewsIngestionOrchestrator(),
       'signal-generation': NewsSignalOrchestrator(),
       'risk-management': PositionSizer(),
       'notification': AlertBatcher(),
       'analytics': PerformanceTracker()
   }
   ```

4. **Event-Driven Architecture**
   ```python
   class EventBus:
       """Event bus for service communication."""
       
       def __init__(self):
           self.subscribers = {}
       
       def publish(self, event_type: str, data: Dict) -> None:
           """Publish event to subscribers."""
           if event_type in self.subscribers:
               for subscriber in self.subscribers[event_type]:
                   subscriber.handle_event(event_type, data)
       
       def subscribe(self, event_type: str, subscriber: Any) -> None:
           """Subscribe to event type."""
           if event_type not in self.subscribers:
               self.subscribers[event_type] = []
           self.subscribers[event_type].append(subscriber)
   ```

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                   │
│                                                             │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │ Application │  │ Database        │  │ Monitoring      ││
│  │ Instance    │  │                 │  │ & Logging       ││
│  │             │  │                 │  │                 ││
│  │ • MarketMan │  │ • SQLite        │  │ • System        ││
│  │ • CLI       │  │ • JSON Files    │  │   Monitoring    ││
│  │ • Cron Jobs │  │ • Memory Cache  │  │ • Alerts        ││
│  └─────────────┘  └─────────────────┘  └─────────────────┘│
│                                                             │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │ External    │  │ Configuration   │  │ Backup          ││
│  │ Services    │  │                 │  │ & Recovery      ││
│  │             │  │                 │  │                 ││
│  │ • APIs      │  │ • YAML Files    │  │ • Automated     ││
│  │ • Notions   │  │ • Environment   │  │ • Manual        ││
│  │ • Pushover  │  │   Variables     │  │ • Testing       ││
│  └─────────────┘  └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 🚫 Not Implemented

The following features mentioned in previous documentation are **NOT YET IMPLEMENTED**:

1. **RESTful API** - No web API endpoints
2. **Backtesting Engine** - Empty module, no implementation
3. **Advanced Authentication** - No user authentication system
4. **Redis Caching** - Only file and memory caching implemented
5. **Microservices Architecture** - Monolithic design
6. **Load Balancing** - Single instance only
7. **Advanced Database Features** - No partitioning or sharding
8. **Web Dashboard** - CLI-only interface
9. **Real-time Trading** - Paper trading only
10. **Advanced Risk Models** - Basic Kelly Criterion only

---

**Next**: [User Guide](user-guide.md) for usage instructions 

Batching now uses a hybrid approach:
- Batches are finalized and processed immediately if they reach the maximum batch size.
- Batches are also finalized if they have at least the minimum batch size and have been waiting longer than the configured max wait time.
- At the end of each news cycle, any remaining pending batches that meet the minimum batch size are finalized and processed, ensuring no news is left unprocessed. This is handled by the `finalize_all_pending_batches` method in the batcher and called by the orchestrator. 