import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class MarketMemory:
    """
    Contextual memory system for MarketMan to track signal patterns and provide continuity
    """
    
    def __init__(self, db_path: str = "marketman_memory.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create signals table to track all analysis results
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    etfs TEXT NOT NULL,  -- JSON array of affected ETFs
                    reasoning TEXT NOT NULL,
                    market_impact TEXT,
                    strategic_advice TEXT,
                    coaching_tone TEXT,
                    risk_factors TEXT,
                    opportunity_thesis TEXT,
                    price_snapshot TEXT,  -- JSON of ETF prices at time
                    search_term TEXT,
                    article_url TEXT
                )
            ''')
            
            # Create patterns table to track detected patterns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    etf_symbol TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    consecutive_days INTEGER NOT NULL,
                    signal_type TEXT NOT NULL,
                    average_confidence REAL NOT NULL,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_signals_date_etf 
                ON signals (date, etfs)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_signals_timestamp 
                ON signals (timestamp)
            ''')
            
            conn.commit()
            conn.close()
            logger.debug("✅ MarketMemory database initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing MarketMemory database: {e}")
    
    def store_signal(self, analysis: Dict, title: str, search_term: str = "", article_url: str = ""):
        """Store a new signal analysis in memory"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now()
            
            cursor.execute('''
                INSERT INTO signals (
                    timestamp, date, title, signal, confidence, etfs, reasoning,
                    market_impact, strategic_advice, coaching_tone, risk_factors,
                    opportunity_thesis, price_snapshot, search_term, article_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                current_time.isoformat(),
                current_time.strftime('%Y-%m-%d'),
                title,
                analysis.get('signal', 'Neutral'),
                analysis.get('confidence', 0),
                json.dumps(analysis.get('affected_etfs', [])),
                analysis.get('reasoning', ''),
                analysis.get('market_impact', ''),
                analysis.get('strategic_advice', ''),
                analysis.get('coaching_tone', ''),
                analysis.get('risk_factors', ''),
                analysis.get('opportunity_thesis', ''),
                json.dumps(analysis.get('market_snapshot', {})),
                search_term,
                article_url
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"💾 Stored signal in memory: {analysis.get('signal')} for {title[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Error storing signal in memory: {e}")
    
    def get_recent_signals(self, days: int = 7) -> List[Dict]:
        """Get all signals from the last N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT * FROM signals 
                WHERE date >= ? 
                ORDER BY timestamp DESC
            ''', (cutoff_date,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            columns = [desc[0] for desc in cursor.description]
            signals = []
            for row in rows:
                signal_dict = dict(zip(columns, row))
                signal_dict['etfs'] = json.loads(signal_dict['etfs'])
                signal_dict['price_snapshot'] = json.loads(signal_dict['price_snapshot'])
                signals.append(signal_dict)
            
            return signals
            
        except Exception as e:
            logger.error(f"❌ Error retrieving recent signals: {e}")
            return []
    
    def detect_patterns(self, etf_symbol: str = None) -> List[Dict]:
        """Detect patterns like consecutive bearish/bullish signals"""
        patterns = []
        
        try:
            recent_signals = self.get_recent_signals(days=14)  # Look back 2 weeks
            
            # Group signals by ETF and analyze patterns
            etf_signals = {}
            for signal in recent_signals:
                for etf in signal['etfs']:
                    if etf_symbol and etf != etf_symbol:
                        continue
                    if etf not in etf_signals:
                        etf_signals[etf] = []
                    etf_signals[etf].append(signal)
            
            # Analyze each ETF for patterns
            for etf, signals in etf_signals.items():
                # Sort by date
                signals.sort(key=lambda x: x['timestamp'])
                
                # Look for consecutive signals
                consecutive_patterns = self._find_consecutive_patterns(etf, signals)
                patterns.extend(consecutive_patterns)
                
                # Look for signal reversals
                reversal_patterns = self._find_reversal_patterns(etf, signals)
                patterns.extend(reversal_patterns)
                
                # Look for volatility patterns
                volatility_patterns = self._find_volatility_patterns(etf, signals)
                patterns.extend(volatility_patterns)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Error detecting patterns: {e}")
            return []
    
    def _find_consecutive_patterns(self, etf: str, signals: List[Dict]) -> List[Dict]:
        """Find consecutive same-signal patterns"""
        patterns = []
        
        if len(signals) < 2:
            return patterns
        
        current_streak = 1
        current_signal = signals[0]['signal']
        streak_start = signals[0]
        confidences = [signals[0]['confidence']]
        
        for i in range(1, len(signals)):
            signal = signals[i]
            
            # Check if signal is within 3 days of previous
            prev_date = datetime.fromisoformat(signals[i-1]['timestamp'])
            curr_date = datetime.fromisoformat(signal['timestamp'])
            days_apart = (curr_date - prev_date).days
            
            if signal['signal'] == current_signal and days_apart <= 3:
                current_streak += 1
                confidences.append(signal['confidence'])
            else:
                # End of streak, check if it's significant
                if current_streak >= 2 and current_signal in ['Bullish', 'Bearish']:
                    avg_confidence = sum(confidences) / len(confidences)
                    
                    pattern = {
                        'type': 'consecutive',
                        'etf': etf,
                        'signal': current_signal,
                        'streak': current_streak,
                        'avg_confidence': avg_confidence,
                        'start_date': streak_start['date'],
                        'end_date': signals[i-1]['date'],
                        'description': self._generate_consecutive_description(etf, current_signal, current_streak, avg_confidence)
                    }
                    patterns.append(pattern)
                
                # Start new streak
                current_streak = 1
                current_signal = signal['signal']
                streak_start = signal
                confidences = [signal['confidence']]
        
        # Check final streak
        if current_streak >= 2 and current_signal in ['Bullish', 'Bearish']:
            avg_confidence = sum(confidences) / len(confidences)
            pattern = {
                'type': 'consecutive',
                'etf': etf,
                'signal': current_signal,
                'streak': current_streak,
                'avg_confidence': avg_confidence,
                'start_date': streak_start['date'],
                'end_date': signals[-1]['date'],
                'description': self._generate_consecutive_description(etf, current_signal, current_streak, avg_confidence)
            }
            patterns.append(pattern)
        
        return patterns
    
    def _find_reversal_patterns(self, etf: str, signals: List[Dict]) -> List[Dict]:
        """Find signal reversal patterns (bearish to bullish or vice versa)"""
        patterns = []
        
        if len(signals) < 2:
            return patterns
        
        for i in range(1, len(signals)):
            prev_signal = signals[i-1]
            curr_signal = signals[i]
            
            # Check for significant reversals
            if ((prev_signal['signal'] == 'Bearish' and curr_signal['signal'] == 'Bullish') or
                (prev_signal['signal'] == 'Bullish' and curr_signal['signal'] == 'Bearish')):
                
                # Check if both signals have decent confidence
                if prev_signal['confidence'] >= 6 and curr_signal['confidence'] >= 6:
                    pattern = {
                        'type': 'reversal',
                        'etf': etf,
                        'from_signal': prev_signal['signal'],
                        'to_signal': curr_signal['signal'],
                        'from_confidence': prev_signal['confidence'],
                        'to_confidence': curr_signal['confidence'],
                        'date': curr_signal['date'],
                        'description': self._generate_reversal_description(etf, prev_signal['signal'], curr_signal['signal'])
                    }
                    patterns.append(pattern)
        
        return patterns
    
    def _find_volatility_patterns(self, etf: str, signals: List[Dict]) -> List[Dict]:
        """Find high volatility patterns (frequent signal changes)"""
        patterns = []
        
        if len(signals) < 4:
            return patterns
        
        # Look for 3+ signal changes in a week
        recent_week = signals[-7:] if len(signals) >= 7 else signals
        signal_changes = 0
        
        for i in range(1, len(recent_week)):
            if recent_week[i]['signal'] != recent_week[i-1]['signal']:
                signal_changes += 1
        
        if signal_changes >= 2:
            pattern = {
                'type': 'volatility',
                'etf': etf,
                'signal_changes': signal_changes,
                'period_days': len(recent_week),
                'date': recent_week[-1]['date'],
                'description': f"{etf} showing high volatility with {signal_changes} signal changes in {len(recent_week)} days. Market uncertainty detected."
            }
            patterns.append(pattern)
        
        return patterns
    
    def _generate_consecutive_description(self, etf: str, signal: str, streak: int, avg_confidence: float) -> str:
        """Generate contextual description for consecutive patterns"""
        
        confidence_desc = "high" if avg_confidence >= 8 else "moderate" if avg_confidence >= 6 else "low"
        
        if signal == 'Bearish':
            if streak >= 3:
                return f"{etf} has been in {streak} consecutive bearish alerts with {confidence_desc} confidence. Possible long-term sector drift forming - consider defensive positioning."
            else:
                return f"{etf} showing back-to-back bearish signals with {confidence_desc} confidence. Monitor for trend continuation."
        
        elif signal == 'Bullish':
            if streak >= 3:
                return f"{etf} has sustained {streak} consecutive bullish alerts with {confidence_desc} confidence. Strong momentum building - consider scaling positions."
            else:
                return f"{etf} showing consecutive bullish signals with {confidence_desc} confidence. Positive momentum developing."
        
        return f"{etf} showing {streak} consecutive {signal.lower()} signals."
    
    def _generate_reversal_description(self, etf: str, from_signal: str, to_signal: str) -> str:
        """Generate contextual description for reversal patterns"""
        
        if from_signal == 'Bearish' and to_signal == 'Bullish':
            return f"{etf} reversed from bearish to bullish - potential bottom formation. Consider entry opportunities."
        elif from_signal == 'Bullish' and to_signal == 'Bearish':
            return f"{etf} reversed from bullish to bearish - possible trend change. Review position sizing."
        
        return f"{etf} signal reversal detected: {from_signal} → {to_signal}"
    
    def get_contextual_insight(self, current_analysis: Dict, etfs: List[str]) -> Optional[str]:
        """Generate contextual insight based on memory patterns"""
        try:
            insights = []
            
            # Check for patterns in the affected ETFs
            for etf in etfs:
                patterns = self.detect_patterns(etf_symbol=etf)
                
                for pattern in patterns:
                    if pattern['type'] == 'consecutive':
                        # Only add if current signal matches the pattern
                        if pattern['signal'] == current_analysis.get('signal'):
                            insights.append(pattern['description'])
                    
                    elif pattern['type'] == 'reversal':
                        # Add reversal context
                        insights.append(pattern['description'])
                    
                    elif pattern['type'] == 'volatility':
                        insights.append(pattern['description'])
            
            # Get recent performance context
            performance_insight = self._get_performance_context(etfs)
            if performance_insight:
                insights.append(performance_insight)
            
            return " ".join(insights) if insights else None
            
        except Exception as e:
            logger.error(f"❌ Error generating contextual insight: {e}")
            return None
    
    def _get_performance_context(self, etfs: List[str]) -> Optional[str]:
        """Get recent performance context for ETFs"""
        try:
            recent_signals = self.get_recent_signals(days=7)
            
            etf_performance = {}
            for signal in recent_signals:
                for etf in signal['etfs']:
                    if etf in etfs:
                        if etf not in etf_performance:
                            etf_performance[etf] = {'bullish': 0, 'bearish': 0, 'total': 0}
                        
                        etf_performance[etf]['total'] += 1
                        if signal['signal'] == 'Bullish':
                            etf_performance[etf]['bullish'] += 1
                        elif signal['signal'] == 'Bearish':
                            etf_performance[etf]['bearish'] += 1
            
            insights = []
            for etf, perf in etf_performance.items():
                if perf['total'] >= 3:  # Only comment if we have enough data
                    bullish_ratio = perf['bullish'] / perf['total']
                    bearish_ratio = perf['bearish'] / perf['total']
                    
                    if bullish_ratio >= 0.7:
                        insights.append(f"{etf} has been predominantly bullish this week ({perf['bullish']}/{perf['total']} signals).")
                    elif bearish_ratio >= 0.7:
                        insights.append(f"{etf} has been predominantly bearish this week ({perf['bearish']}/{perf['total']} signals).")
            
            return " ".join(insights) if insights else None
            
        except Exception as e:
            logger.error(f"❌ Error getting performance context: {e}")
            return None
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to prevent database bloat"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
            
            cursor.execute('DELETE FROM signals WHERE date < ?', (cutoff_date,))
            cursor.execute('DELETE FROM patterns WHERE start_date < ?', (cutoff_date,))
            
            deleted_signals = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_signals > 0:
                logger.info(f"🧹 Cleaned up {deleted_signals} old records from MarketMemory")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up old data: {e}")
    
    def get_memory_stats(self) -> Dict:
        """Get statistics about stored memory"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total signals
            cursor.execute('SELECT COUNT(*) FROM signals')
            total_signals = cursor.fetchone()[0]
            
            # Get signals by type
            cursor.execute('''
                SELECT signal, COUNT(*) 
                FROM signals 
                GROUP BY signal
            ''')
            signal_counts = dict(cursor.fetchall())
            
            # Get recent activity (last 7 days)
            cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*) FROM signals WHERE date >= ?', (cutoff_date,))
            recent_signals = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute('SELECT MIN(date), MAX(date) FROM signals')
            date_range = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_signals': total_signals,
                'signal_breakdown': signal_counts,
                'recent_activity': recent_signals,
                'date_range': date_range,
                'db_path': self.db_path
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting memory stats: {e}")
            return {}
