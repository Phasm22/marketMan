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
import logging
import time

from ..database.db_manager import alert_batch_db
from src.core.utils.config_loader import get_config
import pytz

try:
    from ...integrations.pushover_utils import send_pushover_notification
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.integrations.pushover_utils import send_pushover_notification

logger = logging.getLogger(__name__)


@dataclass
class PendingAlert:
    """Structure for a pending alert"""

    signal: str
    confidence: int
    title: str
    reasoning: str
    etfs: List[str]
    sector: str
    article_url: str = ""
    timestamp: datetime = datetime.now()
    search_term: str = ""
    alert_id: str = ""
    # New actionable fields (schema v3+)
    if_then_scenario: str = ""
    contradictory_signals: str = ""
    uncertainty_metric: str = ""
    price_anchors: Dict = None
    position_risk_bracket: str = ""

    def __post_init__(self):
        if self.article_url is None:
            self.article_url = ""
        if self.search_term is None:
            self.search_term = ""
        if self.alert_id is None:
            self.alert_id = ""
        if self.price_anchors is None:
            self.price_anchors = {}
        if not self.alert_id:
            # Generate unique ID based on content
            content = f"{self.title}{self.reasoning}{self.timestamp.isoformat()}"
            self.alert_id = hashlib.md5(content.encode()).hexdigest()[:12]


class BatchStrategy(Enum):
    """Different batching strategies"""

    IMMEDIATE = "immediate"  # Send immediately (current behavior)
    TIME_WINDOW = "time_window"  # Batch alerts within time windows
    DAILY_DIGEST = "daily_digest"  # Single daily summary
    SMART_BATCH = "smart_batch"  # Intelligent batching based on content


class AlertBatcher:
    """Manages alert batching and delivery strategies"""

    def __init__(self, db_path: str = None):
        """Initialize the alert batcher with database abstraction."""
        self.db = alert_batch_db
        logger.info("AlertBatcher initialized with database abstraction")

    def add_alert(self, alert: PendingAlert, strategy: BatchStrategy = BatchStrategy.SMART_BATCH):
        """Add an alert to the batching queue"""
        try:
            alert_data = {
                "timestamp": alert.timestamp.isoformat(),
                "alert_type": "signal",
                "content": json.dumps(
                    {
                        "alert_id": alert.alert_id,
                        "signal": alert.signal,
                        "confidence": alert.confidence,
                        "title": alert.title,
                        "reasoning": alert.reasoning,
                        "etfs": alert.etfs,
                        "sector": alert.sector,
                        "article_url": alert.article_url,
                        "search_term": alert.search_term,
                        "strategy": strategy.value,
                        "if_then_scenario": alert.if_then_scenario,
                        "contradictory_signals": alert.contradictory_signals,
                        "uncertainty_metric": alert.uncertainty_metric,
                        "price_anchors": alert.price_anchors,
                        "position_risk_bracket": alert.position_risk_bracket,
                    }
                ),
                "batch_id": None,  # Will be set when batched
            }

            self.db.store_alert(alert_data)
            logger.debug(f"Added alert to queue: {alert.alert_id}")

        except Exception as e:
            logger.error(f"Error adding alert to queue: {e}")

    def get_pending_alerts(self, strategy: Optional[BatchStrategy] = None) -> List[PendingAlert]:
        """Get pending alerts, optionally filtered by strategy"""
        try:
            # Get pending alerts from database
            db_alerts = self.db.get_pending_alerts()

            alerts = []
            for db_alert in db_alerts:
                try:
                    content = json.loads(db_alert["content"])

                    # Filter by strategy if specified
                    if strategy and content.get("strategy") != strategy.value:
                        continue

                    alert = PendingAlert(
                        alert_id=str(content.get("alert_id", "") or ""),
                        signal=content["signal"],
                        confidence=content["confidence"],
                        title=content["title"],
                        reasoning=content["reasoning"],
                        etfs=content["etfs"],
                        sector=content["sector"],
                        article_url=str(content.get("article_url", "") or ""),
                        search_term=str(content.get("search_term", "") or ""),
                        timestamp=datetime.fromisoformat(db_alert["timestamp"]),
                        if_then_scenario=content.get("if_then_scenario", ""),
                        contradictory_signals=content.get("contradictory_signals", ""),
                        uncertainty_metric=content.get("uncertainty_metric", ""),
                        price_anchors=content.get("price_anchors", {}),
                        position_risk_bracket=content.get("position_risk_bracket", ""),
                    )
                    alerts.append(alert)

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Error parsing alert data: {e}")
                    continue

            return alerts

        except Exception as e:
            logger.error(f"Error getting pending alerts: {e}")
            return []

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
        try:
            # Query the database for last batch time
            query = """
            SELECT processed_at FROM batches 
            WHERE strategy = ? AND status = 'sent'
            ORDER BY processed_at DESC 
            LIMIT 1
            """
            result = self.db.execute_query(query, (strategy.value,))

            if result and result[0]["processed_at"]:
                return datetime.fromisoformat(result[0]["processed_at"])
            return None

        except Exception as e:
            logger.error(f"Error getting last batch time: {e}")
            return None

    def create_batch_summary(self, alerts: List[PendingAlert], strategy: BatchStrategy) -> str:
        """Create a summary message for a batch of alerts with actionable fields"""
        if not alerts:
            return ""

        config = get_config().config if callable(get_config) else {}
        sector_map = config.get('sector_mappings', {})
        conviction_tiers = config.get('conviction_tiers', {'high': 9, 'moderate': 7, 'low': 5})
        include_moderate = config.get('reporting', {}).get('include_moderate_positions', True)
        timezone = pytz.timezone(config.get('default_timezone', 'America/New_York'))

        if len(alerts) == 1 and strategy == BatchStrategy.IMMEDIATE:
            alert = alerts[0]
            signal_indicator = {
                "Bullish": "↗ BULLISH",
                "Bearish": "↘ BEARISH",
                "Neutral": "→ NEUTRAL",
            }.get(alert.signal, "→ UNKNOWN")
            sector_display = sector_map.get(alert.sector, alert.sector)
            ts = alert.timestamp.astimezone(timezone).strftime('%Y-%m-%d %H:%M %Z')
            
            # Build enhanced single alert summary with actionable fields
            summary = f"""{signal_indicator} Signal ({alert.confidence}/10)\n\n{alert.title[:80]}{'...' if len(alert.title) > 80 else ''}\n\n"""
            
            # Add reasoning (now contains bullet points)
            if alert.reasoning:
                summary += f"📊 {alert.reasoning}\n\n"
            
            # Add if-then scenario if available
            if alert.if_then_scenario:
                summary += f"🎯 Validation: {alert.if_then_scenario}\n\n"
            
            # Add uncertainty metric if available
            if alert.uncertainty_metric:
                summary += f"⚠️ {alert.uncertainty_metric}\n\n"
            
            # Add contradictory signals if available
            if alert.contradictory_signals:
                summary += f"🔄 Risks: {alert.contradictory_signals}\n\n"
            
            # Add position risk bracket if available
            if alert.position_risk_bracket:
                summary += f"💰 {alert.position_risk_bracket}\n\n"
            
            # Add price anchors if available
            if alert.price_anchors:
                summary += "📈 Price Context:\n"
                for etf, data in list(alert.price_anchors.items())[:3]:  # Top 3 ETFs
                    prev_close = data.get('prev_close', 'N/A')
                    pre_market = data.get('pre_market', 'N/A')
                    trend = data.get('5d_trend', 'N/A')
                    summary += f"• {etf}: ${prev_close} → ${pre_market} ({trend})\n"
                summary += "\n"
            
            summary += f"Sector: {sector_display}\nTime: {ts}\nETFs: {', '.join(alert.etfs[:4])}{'...' if len(alert.etfs) > 4 else ''}"
            return summary

        # Multi-alert batch summary
        sectors = {}
        total_signals = {"Bullish": 0, "Bearish": 0, "Neutral": 0}
        high_conf_alerts = []
        moderate_conf_alerts = []

        for alert in alerts:
            # Group by sector
            if alert.sector not in sectors:
                sectors[alert.sector] = []
            sectors[alert.sector].append(alert)

            # Count signals
            total_signals[alert.signal] = total_signals.get(alert.signal, 0) + 1

            # Track high/moderate confidence
            if alert.confidence >= conviction_tiers.get('high', 9):
                high_conf_alerts.append(alert)
            elif alert.confidence >= conviction_tiers.get('moderate', 7):
                moderate_conf_alerts.append(alert)

        # Build summary
        if strategy == BatchStrategy.DAILY_DIGEST:
            summary = f"📊 Daily Market Summary ({len(alerts)} signals)\n\n"
        else:
            summary = f"🎯 Market Batch Update ({len(alerts)} signals)\n\n"

        # Signal breakdown
        signal_parts = []
        for signal, count in total_signals.items():
            if count > 0:
                emoji = {"Bullish": "↗", "Bearish": "↘", "Neutral": "→"}.get(signal, "→")
                signal_parts.append(f"{emoji} {count} {signal}")
        summary += f"Signals: {' | '.join(signal_parts)}\n\n"

        # High confidence with actionable fields
        if high_conf_alerts:
            summary += "🔥 High Confidence Alerts:\n"
            for alert in high_conf_alerts[:3]:  # Top 3
                sector_display = sector_map.get(alert.sector, alert.sector)
                summary += f"• {alert.signal} {sector_display}: {alert.title[:60]}...\n"
                
                # Add key actionable info for high confidence alerts
                if alert.uncertainty_metric:
                    summary += f"  ⚠️ {alert.uncertainty_metric}\n"
                if alert.position_risk_bracket:
                    summary += f"  💰 {alert.position_risk_bracket}\n"
                if alert.if_then_scenario:
                    summary += f"  🎯 {alert.if_then_scenario[:80]}...\n"
                summary += "\n"
                
            if len(high_conf_alerts) > 3:
                summary += f"• +{len(high_conf_alerts)-3} more high confidence signals\n"
            summary += "\n"

        # Moderate confidence (optional)
        if include_moderate and moderate_conf_alerts:
            summary += "🟡 Moderate Confidence Alerts:\n"
            for alert in moderate_conf_alerts[:3]:
                sector_display = sector_map.get(alert.sector, alert.sector)
                summary += f"• {alert.signal} {sector_display}: {alert.title[:60]}...\n"
                
                # Add key actionable info for moderate confidence alerts
                if alert.uncertainty_metric:
                    summary += f"  ⚠️ {alert.uncertainty_metric}\n"
                if alert.position_risk_bracket:
                    summary += f"  💰 {alert.position_risk_bracket}\n"
                summary += "\n"
                
            if len(moderate_conf_alerts) > 3:
                summary += f"• +{len(moderate_conf_alerts)-3} more moderate confidence signals\n"
            summary += "\n"

        # Sector breakdown
        if len(sectors) > 0:
            if len(sectors) == 1:
                summary += "📈 Sector Active:\n"
            elif len(sectors) > 1:
                summary += "📈 Sectors Active:\n"
            for sector, sector_alerts in sorted(
                sectors.items(), key=lambda x: len(x[1]), reverse=True
            ):
                etfs = set()
                for alert in sector_alerts:
                    etfs.update(alert.etfs[:2])  # Top 2 ETFs per alert
                sector_display = sector_map.get(sector, sector)
                summary += f"• {sector_display}: {', '.join(list(etfs)[:3])}\n"

        return summary.strip()

    def send_batch(self, strategy: BatchStrategy, fallback_warning: str = None) -> bool:
        """Send a batch of alerts using the specified strategy. If fallback_warning is provided, append it to the Pushover message."""
        alerts = self.get_pending_alerts(strategy)
        if not alerts:
            return False

        # Create batch summary
        summary = self.create_batch_summary(alerts, strategy)
        if fallback_warning:
            summary += f"\n\n⚠️ [Market Data Warning]\n{fallback_warning}"

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

        # Send notification with retry logic
        max_retries = 3
        retry_delay = 2  # seconds
        for attempt in range(1, max_retries + 1):
            success = send_pushover_notification(
                message=summary,
                title=title,
                priority=priority,
                url=notion_url,
                url_title="View Analysis" if notion_url else None,
            )
            if success:
                break
            else:
                logger.warning(f"Pushover notification failed (attempt {attempt}/{max_retries}). Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
        else:
            logger.error("Pushover notification failed after all retries.")

        if success:
            # Mark batch as sent using database abstraction
            batch_id = hashlib.md5(
                f"{datetime.now().isoformat()}{strategy.value}".encode()
            ).hexdigest()[:12]
            alert_ids = [str(alert.alert_id or "") for alert in alerts]

            # Record the sent batch
            batch_data = {
                "batch_id": batch_id,
                "strategy": strategy.value,
                "alert_ids": json.dumps(alert_ids),
                "summary": summary,
                "sent_at": datetime.now().isoformat(),
                "notification_success": success,
            }
            
            try:
                self.db.store_batch(batch_data)
                
                # Remove sent alerts from pending
                for alert_id in alert_ids:
                    if alert_id:
                        self.db.delete_alert(str(alert_id))
                
            except Exception as e:
                logger.error(f"Error recording batch: {e}")

        return success

    def process_pending(self, fallback_warning: str = None) -> Dict[str, bool]:
        """Process all pending alerts based on their strategies, passing fallback_warning if present"""
        results = {}

        for strategy in BatchStrategy:
            if self.should_send_batch(strategy):
                success = self.send_batch(strategy, fallback_warning=fallback_warning)
                results[strategy.value] = success

        return results

    def cleanup_old_batches(self, days_old: int = 7):
        """Clean up old batch records"""
        cutoff = datetime.now() - timedelta(days=days_old)
        
        try:
            # Clean up old batches and orphaned alerts
            self.db.cleanup_old_data(cutoff.isoformat())
        except Exception as e:
            logger.error(f"Error cleaning up old batches: {e}")

    def get_batch_stats(self) -> Dict:
        """Get statistics about batching performance"""
        try:
            # Get stats from database abstraction
            stats = self.db.get_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting batch stats: {e}")
            return {
                "pending_by_strategy": {},
                "recent_batches": {},
                "total_pending": 0,
            }


# Convenience functions for integration
def queue_alert(
    signal: str,
    confidence: int,
    title: str,
    reasoning: str,
    etfs: List[str],
    sector: str,
    article_url: str = "",
    search_term: str = "",
    strategy: BatchStrategy = BatchStrategy.SMART_BATCH,
    if_then_scenario: str = "",
    contradictory_signals: str = "",
    uncertainty_metric: str = "",
    price_anchors: Dict = None,
    position_risk_bracket: str = "",
) -> str:
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
        article_url=str(article_url or ""),
        search_term=str(search_term or ""),
        timestamp=datetime.now(),
        if_then_scenario=if_then_scenario,
        contradictory_signals=contradictory_signals,
        uncertainty_metric=uncertainty_metric,
        price_anchors=price_anchors or {},
        position_risk_bracket=position_risk_bracket,
    )

    batcher.add_alert(alert, strategy)
    return str(alert.alert_id or "")


def process_alert_queue(fallback_warning: str = None) -> Dict[str, bool]:
    """Process the alert queue and send any ready batches, passing fallback_warning if present"""
    batcher = AlertBatcher()
    return batcher.process_pending(fallback_warning=fallback_warning)


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
            print("=" * 40)
            print(f"Total Pending: {stats['total_pending']}")
            print("\nPending by Strategy:")
            for strategy, count in stats["pending_by_strategy"].items():
                print(f"  {strategy}: {count}")

            if stats["recent_batches"]:
                print("\nRecent Batches (7 days):")
                for strategy, data in stats["recent_batches"].items():
                    rate = data["success_rate"] * 100
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
                (
                    "Bullish",
                    9,
                    "Major Clean Energy Bill Passes",
                    "Legislation unlocks $50B investment",
                    ["ICLN", "TAN"],
                    "Clean Energy",
                ),
                (
                    "Bearish",
                    7,
                    "Oil Supply Concerns Rise",
                    "OPEC+ production cuts announced",
                    ["XLE", "USO"],
                    "Traditional Energy",
                ),
                (
                    "Bullish",
                    8,
                    "EV Sales Surge Continues",
                    "Tesla reports record deliveries",
                    ["LIT", "DRIV"],
                    "Electric Vehicles",
                ),
            ]

            for signal, conf, title, reason, etfs, sector in test_alerts:
                alert_id = queue_alert(
                    signal, conf, title, reason, etfs, sector, strategy=BatchStrategy.SMART_BATCH
                )
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
