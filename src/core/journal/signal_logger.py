#!/usr/bin/env python3
"""
Signal Logger for MarketMan
Comprehensive signal tracking and analysis with CSV logging and performance correlation.
"""
import os
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

from .trade_journal import TradeJournal, log_signal_from_dict

logger = logging.getLogger(__name__)


@dataclass
class SignalEntry:
    """Signal entry with comprehensive tracking"""
    timestamp: str
    symbol: str
    signal_type: str  # news, technical, pattern, sentiment, etc.
    direction: str  # bullish, bearish, neutral
    confidence: float  # 1-10 scale
    reasoning: str
    source: str  # news source, technical indicator, etc.
    
    # Market context
    market_sentiment: Optional[str] = None
    sector: Optional[str] = None
    current_price: Optional[float] = None
    volume: Optional[int] = None
    
    # Signal metadata
    signal_id: Optional[str] = None
    batch_id: Optional[str] = None
    analysis_session: Optional[str] = None
    
    # Action tracking
    action_taken: Optional[str] = None  # buy, sell, hold, watch
    trade_executed: Optional[bool] = None
    trade_reference: Optional[str] = None
    
    # Performance tracking
    price_at_signal: Optional[float] = None
    price_after_24h: Optional[float] = None
    price_after_1w: Optional[float] = None
    price_after_1m: Optional[float] = None
    
    # Additional context
    keywords: Optional[List[str]] = None
    news_articles: Optional[List[str]] = None
    technical_indicators: Optional[Dict[str, Any]] = None


class SignalLogger:
    """Comprehensive signal logging system"""
    
    def __init__(self, 
                 csv_path: str = "data/signals.csv",
                 detailed_csv_path: str = "data/signals_detailed.csv"):
        self.csv_path = csv_path
        self.detailed_csv_path = detailed_csv_path
        self.trade_journal = TradeJournal()
        
        # Create directories
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        os.makedirs(os.path.dirname(detailed_csv_path), exist_ok=True)
        
        self._init_csv_files()
    
    def _init_csv_files(self):
        """Initialize CSV files for signal logging"""
        # Simple signal log
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'timestamp', 'symbol', 'signal_type', 'direction', 'confidence',
                    'reasoning', 'source', 'action_taken', 'trade_executed'
                ])
        
        # Detailed signal log
        if not os.path.exists(self.detailed_csv_path):
            with open(self.detailed_csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'timestamp', 'symbol', 'signal_type', 'direction', 'confidence',
                    'reasoning', 'source', 'market_sentiment', 'sector', 'current_price',
                    'volume', 'signal_id', 'batch_id', 'analysis_session', 'action_taken',
                    'trade_executed', 'trade_reference', 'price_at_signal', 'price_after_24h',
                    'price_after_1w', 'price_after_1m', 'keywords', 'news_articles',
                    'technical_indicators'
                ])
    
    def log_signal(self, signal: SignalEntry) -> bool:
        """Log a signal to both database and CSV files"""
        try:
            # Log to trade journal database
            signal_data = asdict(signal)
            self.trade_journal.log_signal(signal_data)
            
            # Log to simple CSV
            with open(self.csv_path, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    signal.timestamp,
                    signal.symbol,
                    signal.signal_type,
                    signal.direction,
                    signal.confidence,
                    signal.reasoning[:100],  # Truncate long reasoning
                    signal.source,
                    signal.action_taken or '',
                    signal.trade_executed or False
                ])
            
            # Log to detailed CSV
            with open(self.detailed_csv_path, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    signal.timestamp,
                    signal.symbol,
                    signal.signal_type,
                    signal.direction,
                    signal.confidence,
                    signal.reasoning,
                    signal.source,
                    signal.market_sentiment or '',
                    signal.sector or '',
                    signal.current_price or '',
                    signal.volume or '',
                    signal.signal_id or '',
                    signal.batch_id or '',
                    signal.analysis_session or '',
                    signal.action_taken or '',
                    signal.trade_executed or '',
                    signal.trade_reference or '',
                    signal.price_at_signal or '',
                    signal.price_after_24h or '',
                    signal.price_after_1w or '',
                    signal.price_after_1m or '',
                    json.dumps(signal.keywords or []),
                    json.dumps(signal.news_articles or []),
                    json.dumps(signal.technical_indicators or {})
                ])
            
            logger.info(f"📊 Signal logged: {signal.symbol} {signal.direction} {signal.confidence}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging signal: {e}")
            return False
    
    def log_signal_batch(self, signals: List[SignalEntry]) -> int:
        """Log a batch of signals"""
        logged_count = 0
        
        for signal in signals:
            if self.log_signal(signal):
                logged_count += 1
        
        logger.info(f"📊 Logged {logged_count}/{len(signals)} signals from batch")
        return logged_count
    
    def log_news_signal(self, 
                       symbol: str,
                       direction: str,
                       confidence: float,
                       reasoning: str,
                       source: str,
                       news_articles: Optional[List[str]] = None,
                       keywords: Optional[List[str]] = None,
                       market_context: Optional[Dict[str, Any]] = None) -> bool:
        """Log a news-based signal"""
        signal = SignalEntry(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal_type="news",
            direction=direction,
            confidence=confidence,
            reasoning=reasoning,
            source=source,
            news_articles=news_articles,
            keywords=keywords,
            market_sentiment=market_context.get('sentiment') if market_context else None,
            sector=market_context.get('sector') if market_context else None,
            current_price=market_context.get('current_price') if market_context else None,
            volume=market_context.get('volume') if market_context else None
        )
        
        return self.log_signal(signal)
    
    def log_technical_signal(self,
                           symbol: str,
                           direction: str,
                           confidence: float,
                           reasoning: str,
                           technical_indicators: Dict[str, Any],
                           current_price: Optional[float] = None) -> bool:
        """Log a technical analysis signal"""
        signal = SignalEntry(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal_type="technical",
            direction=direction,
            confidence=confidence,
            reasoning=reasoning,
            source="technical_analysis",
            technical_indicators=technical_indicators,
            current_price=current_price
        )
        
        return self.log_signal(signal)
    
    def log_pattern_signal(self,
                          symbol: str,
                          direction: str,
                          confidence: float,
                          reasoning: str,
                          pattern_type: str,
                          current_price: Optional[float] = None) -> bool:
        """Log a pattern recognition signal"""
        signal = SignalEntry(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal_type="pattern",
            direction=direction,
            confidence=confidence,
            reasoning=reasoning,
            source=f"pattern_{pattern_type}",
            current_price=current_price
        )
        
        return self.log_signal(signal)
    
    def update_signal_with_trade(self, 
                                signal_id: str,
                                action_taken: str,
                                trade_executed: bool,
                                trade_reference: Optional[str] = None) -> bool:
        """Update signal with trade execution information"""
        try:
            # This would update the database record
            # For now, we'll just log the update
            logger.info(f"📝 Updated signal {signal_id}: {action_taken}, executed: {trade_executed}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating signal: {e}")
            return False
    
    def get_signals(self, 
                   symbol: Optional[str] = None,
                   signal_type: Optional[str] = None,
                   direction: Optional[str] = None,
                   days_back: int = 30) -> List[Dict]:
        """Retrieve signals with filtering"""
        return self.trade_journal.get_signals(symbol, signal_type, days_back)
    
    def analyze_signal_performance(self, days: int = 30) -> Dict[str, Any]:
        """Analyze signal performance and accuracy"""
        signals = self.get_signals(days_back=days)
        
        if not signals:
            return {
                'total_signals': 0,
                'signal_accuracy': 0.0,
                'avg_confidence': 0.0,
                'performance_by_type': {},
                'performance_by_direction': {}
            }
        
        # Calculate basic metrics
        total_signals = len(signals)
        executed_signals = [s for s in signals if s.get('trade_executed')]
        executed_count = len(executed_signals)
        
        # Calculate accuracy (simplified - would need price data for real accuracy)
        correct_signals = sum(1 for s in executed_signals if 
                            (s.get('direction') == 'bullish' and s.get('confidence', 0) > 5) or
                            (s.get('direction') == 'bearish' and s.get('confidence', 0) < 5))
        
        signal_accuracy = (correct_signals / executed_count * 100) if executed_count > 0 else 0
        avg_confidence = sum(s.get('confidence', 0) for s in signals) / total_signals
        
        # Performance by signal type
        performance_by_type = {}
        for signal_type in set(s.get('signal_type') for s in signals):
            type_signals = [s for s in signals if s.get('signal_type') == signal_type]
            type_executed = [s for s in type_signals if s.get('trade_executed')]
            
            if type_executed:
                type_correct = sum(1 for s in type_executed if 
                                 (s.get('direction') == 'bullish' and s.get('confidence', 0) > 5) or
                                 (s.get('direction') == 'bearish' and s.get('confidence', 0) < 5))
                type_accuracy = (type_correct / len(type_executed)) * 100
                performance_by_type[signal_type] = {
                    'total': len(type_signals),
                    'executed': len(type_executed),
                    'accuracy': round(type_accuracy, 2)
                }
        
        # Performance by direction
        performance_by_direction = {}
        for direction in set(s.get('direction') for s in signals):
            dir_signals = [s for s in signals if s.get('direction') == direction]
            dir_executed = [s for s in dir_signals if s.get('trade_executed')]
            
            if dir_executed:
                dir_correct = sum(1 for s in dir_executed if 
                                (s.get('direction') == 'bullish' and s.get('confidence', 0) > 5) or
                                (s.get('direction') == 'bearish' and s.get('confidence', 0) < 5))
                dir_accuracy = (dir_correct / len(dir_executed)) * 100
                performance_by_direction[direction] = {
                    'total': len(dir_signals),
                    'executed': len(dir_executed),
                    'accuracy': round(dir_accuracy, 2)
                }
        
        return {
            'total_signals': total_signals,
            'executed_signals': executed_count,
            'signal_accuracy': round(signal_accuracy, 2),
            'avg_confidence': round(avg_confidence, 2),
            'performance_by_type': performance_by_type,
            'performance_by_direction': performance_by_direction
        }
    
    def export_signals_to_csv(self, 
                             output_path: str,
                             symbol: Optional[str] = None,
                             signal_type: Optional[str] = None,
                             days_back: int = 30) -> bool:
        """Export signals to CSV file"""
        try:
            signals = self.get_signals(symbol, signal_type, days_back)
            
            if not signals:
                logger.warning("No signals found for export")
                return False
            
            with open(output_path, 'w', newline='') as csvfile:
                if signals:
                    fieldnames = signals[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(signals)
            
            logger.info(f"📊 Exported {len(signals)} signals to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exporting signals: {e}")
            return False
    
    def generate_signal_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive signal analysis report"""
        performance = self.analyze_signal_performance(days)
        signals = self.get_signals(days_back=days)
        
        # Get recent signals
        recent_signals = signals[:10] if signals else []
        
        # Calculate signal frequency
        signal_frequency = {}
        for signal in signals:
            signal_type = signal.get('signal_type', 'unknown')
            signal_frequency[signal_type] = signal_frequency.get(signal_type, 0) + 1
        
        report = {
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_signals": performance['total_signals'],
                "executed_signals": performance['executed_signals'],
                "signal_accuracy": f"{performance['signal_accuracy']}%",
                "avg_confidence": performance['avg_confidence']
            },
            "performance_by_type": performance['performance_by_type'],
            "performance_by_direction": performance['performance_by_direction'],
            "signal_frequency": signal_frequency,
            "recent_signals": [
                {
                    "timestamp": s.get('timestamp'),
                    "symbol": s.get('symbol'),
                    "signal_type": s.get('signal_type'),
                    "direction": s.get('direction'),
                    "confidence": s.get('confidence'),
                    "action_taken": s.get('action_taken')
                }
                for s in recent_signals
            ]
        }
        
        return report


# Convenience functions
def create_signal_logger() -> SignalLogger:
    """Create and return a signal logger instance"""
    return SignalLogger()


def log_news_signal(symbol: str, direction: str, confidence: float, reasoning: str, source: str, **kwargs) -> bool:
    """Log a news-based signal"""
    logger = create_signal_logger()
    return logger.log_news_signal(symbol, direction, confidence, reasoning, source, **kwargs)


def log_technical_signal(symbol: str, direction: str, confidence: float, reasoning: str, technical_indicators: Dict[str, Any], **kwargs) -> bool:
    """Log a technical analysis signal"""
    logger = create_signal_logger()
    return logger.log_technical_signal(symbol, direction, confidence, reasoning, technical_indicators, **kwargs)


def generate_signal_report(days: int = 30) -> Dict[str, Any]:
    """Generate signal analysis report"""
    logger = create_signal_logger()
    return logger.generate_signal_report(days) 