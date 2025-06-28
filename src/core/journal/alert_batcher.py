"""
Alert Batching System for MarketMan
Handles different notification strategies to prevent alert fatigue and rate limiting
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

@dataclass
class PendingAlert:
    """Structure for a pending alert"""
    signal: str
    confidence: int
    title: str
    reasoning: str
    etfs: List[str]
    sector: str
    article_url: str
    timestamp: datetime
    search_term: str
    alert_id: str = None
    
    def __post_init__(self):
        if not self.alert_id:
            # Generate unique ID based on content
            content = f"{self.title}{self.reasoning}{self.timestamp.isoformat()}"
            self.alert_id = hashlib.md5(content.encode()).hexdigest()[:12]

class BatchStrategy(Enum):
    """Different batching strategies"""
    IMMEDIATE = "immediate"        # Send immediately (current behavior)
    TIME_WINDOW = "time_window"    # Batch alerts within time windows
    DAILY_DIGEST = "daily_digest"  # Single daily summary
    SMART_BATCH = "smart_batch"    # Intelligent batching based on content

class AlertBatcher:
    """Manages alert batching and delivery strategies"""
    
    def __init__(self, db_path="/root/marketMan/alert_batch.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize the alert batching database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_alerts (
                    alert_id TEXT PRIMARY KEY,
                    signal TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    etfs TEXT NOT NULL,  -- JSON array
                    sector TEXT NOT NULL,
                    article_url TEXT,
                    search_term TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    batch_strategy TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sent_batches (
                    batch_id TEXT PRIMARY KEY,
                    strategy TEXT NOT NULL,
                    alert_ids TEXT NOT NULL,  -- JSON array
                    summary TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    notification_success BOOLEAN NOT NULL
                )
            """)

    def add_alert(self, alert: PendingAlert, strategy: BatchStrategy = BatchStrategy.SMART_BATCH):
        """Add an alert to the batching queue"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO pending_alerts 
                (alert_id, signal, confidence, title, reasoning, etfs, sector, 
                 article_url, search_term, timestamp, created_at, batch_strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.signal,
                alert.confidence,
                alert.title,
                alert.reasoning,
                json.dumps(alert.etfs),
                alert.sector,
                alert.article_url,
                alert.search_term,
                alert.timestamp.isoformat(),
                datetime.now().isoformat(),
                strategy.value
            ))

    def get_pending_alerts(self, strategy: Optional[BatchStrategy] = None) -> List[PendingAlert]:
        """Get pending alerts, optionally filtered by strategy"""
        with sqlite3.connect(self.db_path) as conn:
            if strategy:
                cursor = conn.execute("""
                    SELECT * FROM pending_alerts 
                    WHERE batch_strategy = ? 
                    ORDER BY timestamp DESC
                """, (strategy.value,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM pending_alerts 
                    ORDER BY timestamp DESC
                """)
            
            alerts = []
            for row in cursor.fetchall():
                alert = PendingAlert(
                    alert_id=row[0],
                    signal=row[1],
                    confidence=row[2],
                    title=row[3],
                    reasoning=row[4],
                    etfs=json.loads(row[5]),
                    sector=row[6],
                    article_url=row[7],
                    search_term=row[8],
                    timestamp=datetime.fromisoformat(row[9])
                )
                alerts.append(alert)
            
            return alerts

    def should_send_batch(self, strategy: BatchStrategy) -> bool:
        """Determine if a batch should be sent based on strategy"""
        pending = self.get_pending_alerts(strategy)
        
        if not pending:
            return False
            
        if strategy == BatchStrategy.IMMEDIATE:
            return True
            
        elif strategy == BatchStrategy.TIME_WINDOW:
            # Send if oldest alert is > 30 minutes old or we have 3+ alerts
            oldest = min(pending, key=lambda a: a.timestamp)
            time_threshold = datetime.now() - timedelta(minutes=30)
            return oldest.timestamp < time_threshold or len(pending) >= 3
            
        elif strategy == BatchStrategy.DAILY_DIGEST:
            # Send once per day if we have alerts
            last_batch = self._get_last_batch_time(strategy)
            if last_batch:
                return datetime.now() - last_batch > timedelta(hours=20)  # Allow some flexibility
            return len(pending) > 0
            
        elif strategy == BatchStrategy.SMART_BATCH:
            # Smart logic: immediate for high confidence, batch for lower
            high_conf_alerts = [a for a in pending if a.confidence >= 9]
            if high_conf_alerts:
                return True
                
            # Batch medium confidence alerts
            medium_conf_alerts = [a for a in pending if 7 <= a.confidence < 9]
            if len(medium_conf_alerts) >= 2:
                return True
                
            # Time-based for single medium confidence alerts
            if medium_conf_alerts:
                oldest = min(medium_conf_alerts, key=lambda a: a.timestamp)
                return datetime.now() - oldest.timestamp > timedelta(minutes=45)
                
        return False

    def _get_last_batch_time(self, strategy: BatchStrategy) -> Optional[datetime]:
        """Get the timestamp of the last batch sent for a strategy"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT sent_at FROM sent_batches 
                WHERE strategy = ? 
                ORDER BY sent_at DESC 
                LIMIT 1
            """, (strategy.value,))
            
            row = cursor.fetchone()
            if row:
                return datetime.fromisoformat(row[0])
            return None

    def create_batch_summary(self, alerts: List[PendingAlert], strategy: BatchStrategy) -> str:
        """Create a summary message for a batch of alerts"""
        if not alerts:
            return ""
            
        if len(alerts) == 1 and strategy == BatchStrategy.IMMEDIATE:
            # Single alert - use existing format
            alert = alerts[0]
            signal_indicator = {
                "Bullish": "↗ BULLISH",
                "Bearish": "↘ BEARISH", 
                "Neutral": "→ NEUTRAL"
            }.get(alert.signal, "→ UNKNOWN")
            
            return f"""{signal_indicator} Signal ({alert.confidence}/10)

{alert.title[:80]}{'...' if len(alert.title) > 80 else ''}

Reason: {alert.reasoning}

ETFs: {', '.join(alert.etfs[:4])}{'...' if len(alert.etfs) > 4 else ''}"""

        # Multi-alert batch summary
        sectors = {}
        total_signals = {"Bullish": 0, "Bearish": 0, "Neutral": 0}
        high_conf_alerts = []
        
        for alert in alerts:
            # Group by sector
            if alert.sector not in sectors:
                sectors[alert.sector] = []
            sectors[alert.sector].append(alert)
            
            # Count signals
            total_signals[alert.signal] = total_signals.get(alert.signal, 0) + 1
            
            # Track high confidence
            if alert.confidence >= 8:
                high_conf_alerts.append(alert)
        
        # Build summary
        if strategy == BatchStrategy.DAILY_DIGEST:
            summary = f"📊 Daily Market Summary ({len(alerts)} signals)\n\n"
        else:
            summary = f"🎯 Market Batch Update ({len(alerts)} signals)\n\n"
        
        # Signal breakdown
        signal_parts = []
        for signal, count in total_signals.items():
            if count > 0:
                # Handle mixed signals
                if '|' in signal:
                    primary_signal = signal.split('|')[0]  # Take first signal
                else:
                    primary_signal = signal
                
                emoji = {"Bullish": "↗", "Bearish": "↘", "Neutral": "→"}.get(primary_signal, "→")
                signal_parts.append(f"{emoji} {count} {signal}")
        summary += f"Signals: {' | '.join(signal_parts)}\n\n"
        
        # High confidence highlights
        if high_conf_alerts:
            summary += "🔥 High Confidence Alerts:\n"
            for alert in high_conf_alerts[:3]:  # Top 3
                summary += f"• {alert.signal} {alert.sector}: {alert.title}\n"
            if len(high_conf_alerts) > 3:
                summary += f"• +{len(high_conf_alerts)-3} more high confidence signals\n"
            summary += "\n"
        
        # Sector breakdown
        if len(sectors) > 1:
            summary += "📈 Sectors Active:\n"
            for sector, sector_alerts in sorted(sectors.items(), key=lambda x: len(x[1]), reverse=True):
                etfs = set()
                for alert in sector_alerts:
                    etfs.update(alert.etfs[:2])  # Top 2 ETFs per alert
                summary += f"• {sector}: {', '.join(list(etfs)[:3])}\n"
        
        return summary.strip()

    def send_batch(self, strategy: BatchStrategy) -> bool:
        """Send a batch of alerts using the specified strategy"""
        import sys
        import os
        
        # Add project root to path for imports
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from src.integrations.pushover_utils import send_pushover_notification
        
        alerts = self.get_pending_alerts(strategy)
        if not alerts:
            return False
            
        # Create batch summary
        summary = self.create_batch_summary(alerts, strategy)
        
        # Determine title and priority
        high_conf_count = len([a for a in alerts if a.confidence >= 9])
        if strategy == BatchStrategy.DAILY_DIGEST:
            title = "MarketMan Daily Digest"
            priority = 0
        elif high_conf_count > 0:
            title = f"MarketMan HIGH ({high_conf_count} critical)"
            priority = 0  # Keep normal priority as per user feedback
        else:
            title = f"MarketMan Update ({len(alerts)} signals)"
            priority = 0
        
        # Find best Notion URL (highest confidence alert)
        best_alert = max(alerts, key=lambda a: a.confidence)
        notion_url = best_alert.article_url if best_alert.article_url else None
        
        # Send notification
        success = send_pushover_notification(
            message=summary,
            title=title,
            priority=priority,
            url=notion_url,
            url_title="View Analysis" if notion_url else None
        )
        
        if success:
            # Mark batch as sent
            batch_id = hashlib.md5(f"{datetime.now().isoformat()}{strategy.value}".encode()).hexdigest()[:12]
            alert_ids = [alert.alert_id for alert in alerts]
            
            with sqlite3.connect(self.db_path) as conn:
                # Record the sent batch
                conn.execute("""
                    INSERT INTO sent_batches 
                    (batch_id, strategy, alert_ids, summary, sent_at, notification_success)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    batch_id,
                    strategy.value,
                    json.dumps(alert_ids),
                    summary,
                    datetime.now().isoformat(),
                    success
                ))
                
                # Remove sent alerts from pending
                placeholders = ','.join(['?' for _ in alert_ids])
                conn.execute(f"""
                    DELETE FROM pending_alerts 
                    WHERE alert_id IN ({placeholders})
                """, alert_ids)
        
        return success

    def process_pending(self) -> Dict[str, bool]:
        """Process all pending alerts based on their strategies"""
        results = {}
        
        for strategy in BatchStrategy:
            if self.should_send_batch(strategy):
                success = self.send_batch(strategy)
                results[strategy.value] = success
                
        return results

    def cleanup_old_batches(self, days_old: int = 7):
        """Clean up old batch records"""
        cutoff = datetime.now() - timedelta(days=days_old)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM sent_batches 
                WHERE sent_at < ?
            """, (cutoff.isoformat(),))
            
            # Also clean up any orphaned pending alerts
            conn.execute("""
                DELETE FROM pending_alerts 
                WHERE created_at < ?
            """, (cutoff.isoformat(),))

    def get_batch_stats(self) -> Dict:
        """Get statistics about batching performance"""
        with sqlite3.connect(self.db_path) as conn:
            # Pending alerts by strategy
            pending_stats = {}
            for strategy in BatchStrategy:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM pending_alerts 
                    WHERE batch_strategy = ?
                """, (strategy.value,))
                pending_stats[strategy.value] = cursor.fetchone()[0]
            
            # Recent batches (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor = conn.execute("""
                SELECT strategy, COUNT(*), 
                       SUM(CASE WHEN notification_success THEN 1 ELSE 0 END) as successful
                FROM sent_batches 
                WHERE sent_at > ? 
                GROUP BY strategy
            """, (week_ago,))
            
            recent_batches = {}
            for row in cursor.fetchall():
                recent_batches[row[0]] = {
                    'total_batches': row[1],
                    'successful': row[2],
                    'success_rate': row[2] / row[1] if row[1] > 0 else 0
                }
            
            return {
                'pending_by_strategy': pending_stats,
                'recent_batches': recent_batches,
                'total_pending': sum(pending_stats.values())
            }


# Convenience functions for integration
def queue_alert(signal: str, confidence: int, title: str, reasoning: str, 
                etfs: List[str], sector: str, article_url: str = None, 
                search_term: str = "", strategy: BatchStrategy = BatchStrategy.SMART_BATCH) -> str:
    """
    Queue an alert for batching
    Returns the alert_id
    """
    batcher = AlertBatcher()
    alert = PendingAlert(
        signal=signal,
        confidence=confidence,
        title=title,
        reasoning=reasoning,
        etfs=etfs,
        sector=sector,
        article_url=article_url,
        search_term=search_term,
        timestamp=datetime.now()
    )
    
    batcher.add_alert(alert, strategy)
    return alert.alert_id

def process_alert_queue() -> Dict[str, bool]:
    """Process the alert queue and send any ready batches"""
    batcher = AlertBatcher()
    return batcher.process_pending()

def get_queue_stats() -> Dict:
    """Get current queue statistics"""
    batcher = AlertBatcher()
    return batcher.get_batch_stats()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        batcher = AlertBatcher()
        
        if command == "stats":
            stats = batcher.get_batch_stats()
            print("📊 Alert Batching Statistics")
            print("="*40)
            print(f"Total Pending: {stats['total_pending']}")
            print("\nPending by Strategy:")
            for strategy, count in stats['pending_by_strategy'].items():
                print(f"  {strategy}: {count}")
            
            if stats['recent_batches']:
                print("\nRecent Batches (7 days):")
                for strategy, data in stats['recent_batches'].items():
                    rate = data['success_rate'] * 100
                    print(f"  {strategy}: {data['total_batches']} batches, {rate:.1f}% success")
        
        elif command == "process":
            print("🚀 Processing alert queue...")
            results = batcher.process_pending()
            if results:
                for strategy, success in results.items():
                    status = "✅" if success else "❌"
                    print(f"{status} {strategy}: {'Sent' if success else 'Failed'}")
            else:
                print("📭 No batches ready to send")
        
        elif command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            batcher.cleanup_old_batches(days)
            print(f"🧹 Cleaned up batches older than {days} days")
        
        elif command == "test":
            print("🧪 Testing alert batching...")
            # Add some test alerts
            test_alerts = [
                ("Bullish", 9, "Major Clean Energy Bill Passes", "Legislation unlocks $50B investment", ["ICLN", "TAN"], "Clean Energy"),
                ("Bearish", 7, "Oil Supply Concerns Rise", "OPEC+ production cuts announced", ["XLE", "USO"], "Traditional Energy"),
                ("Bullish", 8, "EV Sales Surge Continues", "Tesla reports record deliveries", ["LIT", "DRIV"], "Electric Vehicles")
            ]
            
            for signal, conf, title, reason, etfs, sector in test_alerts:
                alert_id = queue_alert(signal, conf, title, reason, etfs, sector, strategy=BatchStrategy.SMART_BATCH)
                print(f"✅ Queued: {alert_id[:8]} - {title[:30]}...")
            
            print("\n🚀 Processing test batch...")
            results = batcher.process_pending()
            for strategy, success in results.items():
                print(f"{'✅' if success else '❌'} {strategy}")
    
    else:
        print("Alert Batcher Commands:")
        print("  stats    - Show queue statistics")
        print("  process  - Process pending alerts")
        print("  cleanup  - Clean old batch records")
        print("  test     - Run test alerts")
