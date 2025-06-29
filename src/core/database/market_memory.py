import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import logging

from .db_manager import market_memory_db

logger = logging.getLogger(__name__)


class MarketMemory:
    """
    Contextual memory system for MarketMan to track signal patterns and provide continuity.
    """

    def __init__(
        self,
        db_path: str = None,
        max_time_apart: Optional[int] = 3 * 86400,  # default to 3 days in seconds
        confidence_threshold: int = 6,
        volatility_window: int = 7,
        min_consecutive: int = 2,
    ):
        """
        Contextual memory system for MarketMan to track signal patterns and provide continuity.
        """
        # Configurable pattern detection thresholds
        self.max_time_apart = max_time_apart
        self.confidence_threshold = confidence_threshold
        self.volatility_window = volatility_window
        self.min_consecutive = min_consecutive

        # Use the global database instance
        self.db = market_memory_db
        logger.debug("✅ MarketMemory initialized with database abstraction")

    def store_signal(
        self, analysis: Dict, title: str, search_term: str = "", article_url: str = ""
    ):
        """Store a new signal analysis in memory"""
        try:
            current_time = datetime.now(timezone.utc)

            signal_data = {
                "date": current_time.strftime("%Y-%m-%d"),
                "signal_type": analysis.get("signal", "Neutral"),
                "confidence": analysis.get("confidence", 0),
                "etfs": analysis.get("affected_etfs", []),
                "reasoning": analysis.get("reasoning", ""),
                "title": title,
                "search_term": search_term,
                "article_url": article_url,
                "market_impact": analysis.get("market_impact", ""),
                "strategic_advice": analysis.get("strategic_advice", ""),
                "coaching_tone": analysis.get("coaching_tone", ""),
                "risk_factors": analysis.get("risk_factors", ""),
                "opportunity_thesis": analysis.get("opportunity_thesis", ""),
                "price_snapshot": analysis.get("market_snapshot", {}),
            }

            # Store in the database
            signal_id = self.db.store_signal(signal_data)
            logger.debug(f"💾 Stored signal in memory: {analysis.get('signal')} for {title[:50]}...")
            return signal_id

        except Exception as e:
            logger.error(f"❌ Error storing signal in memory: {e}")
            return None

    def get_recent_signals(self, days: int = 7) -> List[Dict]:
        """Get all signals from the last N days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            # Use the database abstraction
            signals = self.db.get_signals(limit=1000)  # Get all recent signals

            # Filter by date and convert to expected format
            recent_signals = []
            for signal in signals:
                if signal["date"] >= cutoff_date:
                    # Convert to expected format
                    signal_dict = {
                        "id": signal["id"],
                        "timestamp": signal["created_at"],
                        "date": signal["date"],
                        "title": signal.get("title", ""),
                        "signal": signal["signal_type"],
                        "confidence": signal["confidence"],
                        "etfs": signal["etfs"].split(",") if signal["etfs"] else [],
                        "reasoning": signal["reasoning"],
                        "market_impact": signal.get("market_impact", ""),
                        "strategic_advice": signal.get("strategic_advice", ""),
                        "coaching_tone": signal.get("coaching_tone", ""),
                        "risk_factors": signal.get("risk_factors", ""),
                        "opportunity_thesis": signal.get("opportunity_thesis", ""),
                        "price_snapshot": signal.get("price_snapshot", {}),
                        "search_term": signal.get("search_term", ""),
                        "article_url": signal.get("article_url", ""),
                    }
                    recent_signals.append(signal_dict)

            # Sort by timestamp descending
            recent_signals.sort(key=lambda x: x["timestamp"], reverse=True)
            return recent_signals

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
                for etf in signal["etfs"]:
                    if etf_symbol and etf != etf_symbol:
                        continue
                    if etf not in etf_signals:
                        etf_signals[etf] = []
                    etf_signals[etf].append(signal)

            # Analyze each ETF for patterns
            for etf, signals in etf_signals.items():
                # Sort by date
                signals.sort(key=lambda x: x["timestamp"])

                # Look for consecutive signals
                consecutive_patterns = self._find_consecutive_patterns(etf, signals)
                patterns.extend(consecutive_patterns)

                # Look for signal reversals
                reversal_patterns = self._find_reversal_patterns(etf, signals)
                patterns.extend(reversal_patterns)

                # Look for volatility patterns
                volatility_patterns = self._find_volatility_patterns(etf, signals)
                patterns.extend(volatility_patterns)

            # Store detected patterns in database
            for pattern in patterns:
                pattern_data = {
                    "start_date": pattern["start_date"],
                    "end_date": pattern["end_date"],
                    "pattern_type": pattern["pattern_type"],
                    "etfs": [pattern["etf_symbol"]],
                    "strength": pattern.get("strength", 0.5),
                }
                self.db.store_pattern(pattern_data)

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
        current_signal = signals[0]["signal"]
        streak_start = signals[0]
        confidences = [signals[0]["confidence"]]

        for i in range(1, len(signals)):
            signal = signals[i]

            # Check if signal is within max_time_apart seconds of previous
            prev_date = self._parse_timestamp_safely(signals[i - 1]["timestamp"])
            curr_date = self._parse_timestamp_safely(signal["timestamp"])
            time_diff = (curr_date - prev_date).total_seconds()

            if signal["signal"] == current_signal and time_diff <= self.max_time_apart:
                current_streak += 1
                confidences.append(signal["confidence"])
            else:
                # End of streak, check if it's significant
                if current_streak >= self.min_consecutive and current_signal in [
                    "Bullish",
                    "Bearish",
                ]:
                    avg_confidence = sum(confidences) / len(confidences)

                    pattern = {
                        "type": "consecutive",
                        "pattern_type": "consecutive",
                        "etf_symbol": etf,
                        "signal_type": current_signal,
                        "consecutive_days": current_streak,
                        "average_confidence": avg_confidence,
                        "start_date": streak_start["date"],
                        "end_date": signals[i - 1]["date"],
                        "description": self._generate_consecutive_description(
                            etf, current_signal, current_streak, avg_confidence
                        ),
                    }
                    patterns.append(pattern)

                # Start new streak
                current_streak = 1
                current_signal = signal["signal"]
                streak_start = signal
                confidences = [signal["confidence"]]

        # Check final streak
        if current_streak >= self.min_consecutive and current_signal in ["Bullish", "Bearish"]:
            avg_confidence = sum(confidences) / len(confidences)
            pattern = {
                "type": "consecutive",
                "pattern_type": "consecutive",
                "etf_symbol": etf,
                "signal_type": current_signal,
                "consecutive_days": current_streak,
                "average_confidence": avg_confidence,
                "start_date": streak_start["date"],
                "end_date": signals[-1]["date"],
                "description": self._generate_consecutive_description(
                    etf, current_signal, current_streak, avg_confidence
                ),
            }
            patterns.append(pattern)

        return patterns

    def _find_reversal_patterns(self, etf: str, signals: List[Dict]) -> List[Dict]:
        """Find signal reversal patterns (bearish to bullish or vice versa)"""
        patterns = []

        if len(signals) < 2:
            return patterns

        for i in range(1, len(signals)):
            prev_signal = signals[i - 1]
            curr_signal = signals[i]

            # Check for significant reversals
            if (prev_signal["signal"] == "Bearish" and curr_signal["signal"] == "Bullish") or (
                prev_signal["signal"] == "Bullish" and curr_signal["signal"] == "Bearish"
            ):
                # Check if both signals have decent confidence
                if (
                    prev_signal["confidence"] >= self.confidence_threshold
                    and curr_signal["confidence"] >= self.confidence_threshold
                ):
                    pattern = {
                        "type": "reversal",
                        "pattern_type": "reversal",
                        "etf_symbol": etf,
                        "from_signal": prev_signal["signal"],
                        "to_signal": curr_signal["signal"],
                        "from_confidence": prev_signal["confidence"],
                        "to_confidence": curr_signal["confidence"],
                        "date": curr_signal["date"],
                        "description": self._generate_reversal_description(
                            etf, prev_signal["signal"], curr_signal["signal"]
                        ),
                    }
                    patterns.append(pattern)

        return patterns

    def _find_volatility_patterns(self, etf: str, signals: List[Dict]) -> List[Dict]:
        """Find high volatility patterns (frequent signal changes)"""
        patterns = []

        if len(signals) < 4:
            return patterns

        # Look for min_consecutive+ signal changes in a volatility_window
        window = self.volatility_window
        recent_window = signals[-window:] if len(signals) >= window else signals
        signal_changes = 0

        for i in range(1, len(recent_window)):
            if recent_window[i]["signal"] != recent_window[i - 1]["signal"]:
                signal_changes += 1

        if signal_changes >= self.min_consecutive:
            pattern = {
                "type": "volatility",
                "pattern_type": "volatility",
                "etf_symbol": etf,
                "signal_changes": signal_changes,
                "period_days": len(recent_window),
                "date": recent_window[-1]["date"],
                "description": f"{etf} showing high volatility with {signal_changes} signal changes in {len(recent_window)} days. Market uncertainty detected.",
            }
            patterns.append(pattern)

        return patterns

    def _generate_consecutive_description(
        self, etf: str, signal: str, streak: int, avg_confidence: float
    ) -> str:
        """Generate contextual description for consecutive patterns"""

        confidence_desc = (
            "high" if avg_confidence >= 8 else "moderate" if avg_confidence >= 6 else "low"
        )

        if signal == "Bearish":
            if streak >= 3:
                return f"{etf} has been in {streak} consecutive bearish alerts with {confidence_desc} confidence. Possible long-term sector drift forming - consider defensive positioning."
            else:
                return f"{etf} showing back-to-back bearish signals with {confidence_desc} confidence. Monitor for trend continuation."

        elif signal == "Bullish":
            if streak >= 3:
                return f"{etf} has sustained {streak} consecutive bullish alerts with {confidence_desc} confidence. Strong momentum building - consider scaling positions."
            else:
                return f"{etf} showing consecutive bullish signals with {confidence_desc} confidence. Positive momentum developing."

        return f"{etf} showing {streak} consecutive {signal.lower()} signals."

    def _generate_reversal_description(self, etf: str, from_signal: str, to_signal: str) -> str:
        """Generate contextual description for reversal patterns"""

        if from_signal == "Bearish" and to_signal == "Bullish":
            return f"{etf} reversed from bearish to bullish - potential bottom formation. Consider entry opportunities."
        elif from_signal == "Bullish" and to_signal == "Bearish":
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
                    if pattern["type"] == "consecutive":
                        # Only add if current signal matches the pattern
                        if pattern["signal_type"] == current_analysis.get("signal"):
                            insights.append(pattern["description"])

                    elif pattern["type"] == "reversal":
                        # Add reversal context
                        insights.append(pattern["description"])

                    elif pattern["type"] == "volatility":
                        insights.append(pattern["description"])

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
                for etf in signal["etfs"]:
                    if etf in etfs:
                        if etf not in etf_performance:
                            etf_performance[etf] = {"bullish": 0, "bearish": 0, "total": 0}

                        etf_performance[etf]["total"] += 1
                        if signal["signal"] == "Bullish":
                            etf_performance[etf]["bullish"] += 1
                        elif signal["signal"] == "Bearish":
                            etf_performance[etf]["bearish"] += 1

            insights = []
            for etf, perf in etf_performance.items():
                if perf["total"] >= 3:  # Only comment if we have enough data
                    bullish_ratio = perf["bullish"] / perf["total"]
                    bearish_ratio = perf["bearish"] / perf["total"]

                    if bullish_ratio >= 0.7:
                        insights.append(
                            f"{etf} has been predominantly bullish this week ({perf['bullish']}/{perf['total']} signals)."
                        )
                    elif bearish_ratio >= 0.7:
                        insights.append(
                            f"{etf} has been predominantly bearish this week ({perf['bearish']}/{perf['total']} signals)."
                        )

            return " ".join(insights) if insights else None

        except Exception as e:
            logger.error(f"❌ Error getting performance context: {e}")
            return None

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to prevent database bloat"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")

            # Delete old signals
            self.db.delete_signals(cutoff_date)
            deleted_signals = self.db.get_signal_count()

            # Delete old patterns
            self.db.delete_patterns(cutoff_date)
            deleted_patterns = self.db.get_pattern_count()

            total_deleted = deleted_signals + deleted_patterns
            if total_deleted > 0:
                logger.info(
                    f"🧹 Cleaned up {deleted_signals} signals and {deleted_patterns} patterns from MarketMemory"
                )
            else:
                logger.info(f"🧹 No records older than {days_to_keep} days found to clean up")

            return {
                "deleted_signals": deleted_signals,
                "deleted_patterns": deleted_patterns,
                "cutoff_date": cutoff_date,
            }

        except Exception as e:
            logger.error(f"❌ Error cleaning up old data: {e}")
            return {"error": str(e)}

    def get_memory_stats(self) -> Dict:
        """Get statistics about stored memory"""
        try:
            total_signals = self.db.get_signal_count()
            signal_counts = self.db.get_signal_breakdown()
            recent_signals = self.db.get_recent_activity()
            date_range = self.db.get_date_range()

            return {
                "total_signals": total_signals,
                "signal_breakdown": signal_counts,
                "recent_activity": recent_signals,
                "date_range": date_range,
                "db_path": self.db.db_path,
            }

        except Exception as e:
            logger.error(f"❌ Error getting memory stats: {e}")
            return {}

    def _clear_memory(self):
        """Utility: clear all entries from signals and patterns tables (for testing)."""
        self.db.clear_all()

    def _parse_timestamp_safely(self, timestamp_str: str) -> datetime:
        """Safely parse timestamp string handling timezone awareness"""
        try:
            # Handle timezone-aware timestamps
            if "T" in timestamp_str and ("+" in timestamp_str or "Z" in timestamp_str):
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str.replace("Z", "+00:00")
                parsed_time = datetime.fromisoformat(timestamp_str)
            else:
                # Handle naive timestamps - assume UTC
                parsed_time = datetime.fromisoformat(timestamp_str)
                if parsed_time.tzinfo is None:
                    parsed_time = parsed_time.replace(tzinfo=timezone.utc)
            logger.debug(
                f"\U0001F570️ Parsed timestamp: raw={timestamp_str} → parsed={parsed_time.isoformat()}"
            )
            return parsed_time
        except Exception as e:
            logger.warning(f"⚠️ Error parsing timestamp {timestamp_str}: {e}")
            # Fallback to current time with UTC timezone
            return datetime.now(timezone.utc)
