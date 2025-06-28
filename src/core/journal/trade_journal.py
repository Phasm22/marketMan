#!/usr/bin/env python3
"""
Trade Journal System for MarketMan
Comprehensive trade tracking with signal correlation, performance metrics, and detailed logging.
"""
import os
import csv
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradeEntry:
    """Trade entry with comprehensive tracking"""
    # Core trade data
    timestamp: str
    symbol: str
    action: str  # Buy/Sell
    quantity: float
    price: float
    trade_value: float
    
    # Signal correlation
    signal_confidence: Optional[float] = None
    signal_reference: Optional[str] = None
    signal_type: Optional[str] = None  # news, technical, pattern, etc.
    
    # Performance tracking
    realized_pnl: Optional[float] = None
    holding_days: Optional[int] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    
    # Market context
    market_sentiment: Optional[str] = None
    sector: Optional[str] = None
    volume: Optional[int] = None
    
    # Notes and metadata
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    broker: str = "Fidelity"
    
    # Risk metrics
    position_size_pct: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class TradeJournal:
    """Comprehensive trade journaling system"""
    
    def __init__(self, db_path: str = "data/trade_journal.db", csv_path: str = "data/trades.csv"):
        self.db_path = db_path
        self.csv_path = csv_path
        self._init_database()
        self._init_csv()
    
    def _init_database(self):
        """Initialize SQLite database for trade journaling"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                trade_value REAL NOT NULL,
                signal_confidence REAL,
                signal_reference TEXT,
                signal_type TEXT,
                realized_pnl REAL,
                holding_days INTEGER,
                entry_price REAL,
                exit_price REAL,
                market_sentiment TEXT,
                sector TEXT,
                volume INTEGER,
                notes TEXT,
                tags TEXT,
                broker TEXT DEFAULT 'Fidelity',
                position_size_pct REAL,
                stop_loss REAL,
                take_profit REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create signals table for signal tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT,
                source TEXT,
                market_context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create performance summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                total_pnl REAL,
                win_rate REAL,
                avg_win REAL,
                avg_loss REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_csv(self):
        """Initialize CSV file for simple signal logging"""
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'timestamp', 'symbol', 'signal_type', 'direction', 'confidence',
                    'reasoning', 'source', 'market_context', 'action_taken'
                ])
    
    def log_trade(self, trade: TradeEntry) -> bool:
        """Log a trade entry to both database and CSV"""
        try:
            # Add to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (
                    timestamp, symbol, action, quantity, price, trade_value,
                    signal_confidence, signal_reference, signal_type, realized_pnl,
                    holding_days, entry_price, exit_price, market_sentiment,
                    sector, volume, notes, tags, broker, position_size_pct,
                    stop_loss, take_profit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.timestamp, trade.symbol, trade.action, trade.quantity,
                trade.price, trade.trade_value, trade.signal_confidence,
                trade.signal_reference, trade.signal_type, trade.realized_pnl,
                trade.holding_days, trade.entry_price, trade.exit_price,
                trade.market_sentiment, trade.sector, trade.volume, trade.notes,
                json.dumps(trade.tags) if trade.tags else None, trade.broker,
                trade.position_size_pct, trade.stop_loss, trade.take_profit
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📝 Trade logged: {trade.symbol} {trade.action} {trade.quantity} @ {trade.price}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging trade: {e}")
            return False
    
    def log_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Log a signal to both database and CSV"""
        try:
            # Add to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO signals (
                    timestamp, symbol, signal_type, direction, confidence,
                    reasoning, source, market_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_data.get('timestamp', datetime.now().isoformat()),
                signal_data.get('symbol'),
                signal_data.get('signal_type'),
                signal_data.get('direction'),
                signal_data.get('confidence'),
                signal_data.get('reasoning'),
                signal_data.get('source'),
                json.dumps(signal_data.get('market_context', {}))
            ))
            
            conn.commit()
            conn.close()
            
            # Add to CSV for simple tracking
            with open(self.csv_path, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    signal_data.get('timestamp', datetime.now().isoformat()),
                    signal_data.get('symbol'),
                    signal_data.get('signal_type'),
                    signal_data.get('direction'),
                    signal_data.get('confidence'),
                    signal_data.get('reasoning', '')[:100],  # Truncate long reasoning
                    signal_data.get('source'),
                    json.dumps(signal_data.get('market_context', {})),
                    signal_data.get('action_taken', '')
                ])
            
            logger.info(f"📊 Signal logged: {signal_data.get('symbol')} {signal_data.get('direction')} {signal_data.get('confidence')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging signal: {e}")
            return False
    
    def get_trades(self, symbol: Optional[str] = None, 
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> List[Dict]:
        """Retrieve trades with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts
        columns = [description[0] for description in cursor.description]
        trades = []
        for row in rows:
            trade_dict = dict(zip(columns, row))
            if trade_dict.get('tags'):
                trade_dict['tags'] = json.loads(trade_dict['tags'])
            trades.append(trade_dict)
        
        return trades
    
    def get_signals(self, symbol: Optional[str] = None,
                    signal_type: Optional[str] = None,
                    days_back: int = 30) -> List[Dict]:
        """Retrieve signals with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM signals WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if signal_type:
            query += " AND signal_type = ?"
            params.append(signal_type)
        
        # Default to last 30 days
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        query += " AND timestamp >= ?"
        params.append(start_date)
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts
        columns = [description[0] for description in cursor.description]
        signals = []
        for row in rows:
            signal_dict = dict(zip(columns, row))
            if signal_dict.get('market_context'):
                signal_dict['market_context'] = json.loads(signal_dict['market_context'])
            signals.append(signal_dict)
        
        return signals
    
    def calculate_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Calculate performance summary for the specified period"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all completed trades (with realized P&L)
        cursor.execute('''
            SELECT realized_pnl, trade_value, holding_days
            FROM trades 
            WHERE realized_pnl IS NOT NULL 
            AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (start_date,))
        
        trades = cursor.fetchall()
        conn.close()
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        
        # Calculate metrics
        total_trades = len(trades)
        winning_trades = sum(1 for trade in trades if trade[0] > 0)
        losing_trades = sum(1 for trade in trades if trade[0] < 0)
        total_pnl = sum(trade[0] for trade in trades)
        
        wins = [trade[0] for trade in trades if trade[0] > 0]
        losses = [trade[0] for trade in trades if trade[0] < 0]
        
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
        
        # Calculate max drawdown (simplified)
        cumulative_pnl = 0
        max_drawdown = 0
        peak = 0
        
        for trade in trades:
            cumulative_pnl += trade[0]
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            drawdown = peak - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calculate Sharpe ratio (simplified, assuming risk-free rate of 0)
        returns = [trade[0] for trade in trades]
        avg_return = sum(returns) / len(returns) if returns else 0.0
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if returns else 0.0
        sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_pnl': round(total_pnl, 2),
            'win_rate': round(win_rate, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2)
        }
    
    def export_trades_to_csv(self, output_path: str, 
                           symbol: Optional[str] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> bool:
        """Export trades to CSV file"""
        try:
            trades = self.get_trades(symbol, start_date, end_date)
            
            if not trades:
                logger.warning("No trades found for export")
                return False
            
            with open(output_path, 'w', newline='') as csvfile:
                if trades:
                    fieldnames = trades[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(trades)
            
            logger.info(f"📊 Exported {len(trades)} trades to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exporting trades: {e}")
            return False


# Convenience functions
def create_trade_journal() -> TradeJournal:
    """Create and return a trade journal instance"""
    return TradeJournal()


def log_trade_from_dict(trade_data: Dict[str, Any]) -> bool:
    """Log a trade from dictionary data"""
    journal = create_trade_journal()
    trade = TradeEntry(**trade_data)
    return journal.log_trade(trade)


def log_signal_from_dict(signal_data: Dict[str, Any]) -> bool:
    """Log a signal from dictionary data"""
    journal = create_trade_journal()
    return journal.log_signal(signal_data) 