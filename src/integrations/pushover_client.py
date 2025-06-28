"""
Pushover Notifier for MarketMan

Enhanced notification system with configurable confidence thresholds,
risk warnings, and rate limiting for trading signals.
"""

import os
import time
import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    from ..core.utils.config_loader import get_config
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.core.utils.config_loader import get_config

logger = logging.getLogger(__name__)


@dataclass
class PushoverMessage:
    """Structure for a Pushover message"""
    message: str
    title: str
    priority: int = 0
    url: Optional[str] = None
    url_title: Optional[str] = None
    timestamp: Optional[int] = None


class PushoverNotifier:
    """Enhanced Pushover notification client with rate limiting and configurable thresholds"""

    def __init__(self):
        """Initialize the Pushover notifier with configuration"""
        self.config = get_config()
        self.api_token = self.config.get_setting("integrations.pushover.api_token")
        self.user_token = self.config.get_setting("integrations.pushover.user_token")
        self.enabled = self.config.get_setting("integrations.pushover.enabled", False)
        self.confidence_threshold = self.config.get_setting("integrations.pushover.confidence_threshold", 7)
        self.risk_warnings_enabled = self.config.get_setting("integrations.pushover.risk_warnings_enabled", True)
        self.rate_limit_per_hour = self.config.get_setting("integrations.pushover.rate_limit_per_hour", 10)
        
        # Priority settings
        self.priority_settings = self.config.get_setting("integrations.pushover.priority_settings", {})
        
        # Rate limiting
        self._notification_history: List[datetime] = []
        self._last_cleanup = datetime.now()
        
        if not self.enabled:
            logger.warning("Pushover notifications are disabled in configuration")
        elif not self.api_token or not self.user_token:
            logger.warning("Pushover API token or user token not configured")

    def _is_rate_limited(self) -> bool:
        """Check if we're currently rate limited"""
        now = datetime.now()
        
        # Clean up old entries (older than 1 hour)
        if (now - self._last_cleanup).seconds > 3600:
            cutoff = now - timedelta(hours=1)
            self._notification_history = [t for t in self._notification_history if t > cutoff]
            self._last_cleanup = now
        
        return len(self._notification_history) >= self.rate_limit_per_hour

    def _record_notification(self) -> None:
        """Record a notification for rate limiting"""
        self._notification_history.append(datetime.now())

    def send_notification(self, message: str, title: str, priority: int = 0, 
                         url: Optional[str] = None, url_title: Optional[str] = None) -> bool:
        """
        Send a basic Pushover notification
        
        Args:
            message: The notification message
            title: The notification title
            priority: Priority level (-2 to 2)
            url: Optional URL to include
            url_title: Optional title for the URL
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Pushover notifications disabled")
            return False
            
        if not self.api_token or not self.user_token:
            logger.error("Pushover credentials not configured")
            return False
            
        if self._is_rate_limited():
            logger.warning("Rate limit exceeded for Pushover notifications")
            return False

        data = {
            "token": self.api_token,
            "user": self.user_token,
            "message": message,
            "title": title,
            "priority": priority,
        }

        if url:
            data["url"] = url
        if url_title:
            data["url_title"] = url_title

        try:
            response = requests.post("https://api.pushover.net/1/messages.json", data=data, timeout=10)
            if response.status_code == 200:
                self._record_notification()
                logger.info(f"✅ Pushover notification sent: {title}")
                return True
            else:
                logger.error(f"❌ Pushover API error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"🔥 Error sending Pushover notification: {e}")
            return False

    def send_trading_signal(self, signal: str, confidence: int, title: str, 
                           reasoning: str, etfs: Optional[List[str]] = None,
                           article_url: Optional[str] = None, 
                           risk_factors: Optional[List[str]] = None) -> bool:
        """
        Send a trading signal notification with confidence-based filtering
        
        Args:
            signal: Bullish/Bearish/Neutral
            confidence: Confidence score 1-10
            title: Article title
            reasoning: Brief reasoning
            etfs: Affected ETFs
            article_url: Link to full analysis
            risk_factors: Optional risk factors to include
            
        Returns:
            True if sent successfully, False otherwise
        """
        if confidence < self.confidence_threshold:
            logger.debug(f"Signal confidence {confidence} below threshold {self.confidence_threshold}")
            return False

        # Determine priority based on confidence
        if confidence >= 9:
            priority = self.priority_settings.get("high_confidence", 0)
            alert_level = "CRITICAL"
        elif confidence >= 8:
            priority = self.priority_settings.get("medium_confidence", 0)
            alert_level = "HIGH"
        elif confidence >= 7:
            priority = self.priority_settings.get("medium_confidence", 0)
            alert_level = "STANDARD"
        else:
            priority = self.priority_settings.get("low_confidence", -1)
            alert_level = "LOW"

        # Build message
        signal_indicator = {
            "Bullish": "↗ BULLISH", 
            "Bearish": "↘ BEARISH", 
            "Neutral": "→ NEUTRAL"
        }.get(signal, "? UNKNOWN")

        message = f"""{signal_indicator} Signal ({confidence}/10)

{title[:80]}{'...' if len(title) > 80 else ''}

Reason: {reasoning}"""

        # Add affected ETFs
        if etfs and len(etfs) > 0:
            etf_list = ", ".join(etfs[:4])
            if len(etfs) > 4:
                etf_list += f" +{len(etfs)-4} more"
            message += f"\n\nETFs: {etf_list}"

        # Add risk warnings if enabled
        if self.risk_warnings_enabled and risk_factors:
            message += f"\n\n⚠️ Risk Factors:\n"
            for risk in risk_factors[:3]:  # Limit to 3 risk factors
                message += f"• {risk}\n"

        alert_title = f"MarketMan {alert_level}"

        return self.send_notification(
            message=message.strip(),
            title=alert_title,
            priority=priority,
            url=article_url,
            url_title="Full Analysis" if article_url else None,
        )

    def send_risk_warning(self, warning_type: str, message: str, 
                         affected_symbols: Optional[List[str]] = None,
                         severity: str = "medium") -> bool:
        """
        Send a risk warning notification
        
        Args:
            warning_type: Type of risk warning
            message: Warning message
            affected_symbols: Affected symbols
            severity: low/medium/high/critical
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.risk_warnings_enabled:
            logger.debug("Risk warnings disabled")
            return False

        priority = self.priority_settings.get("risk_warnings", 1)
        
        title = f"Risk Warning: {warning_type}"
        
        full_message = f"⚠️ {message}"
        
        if affected_symbols:
            symbols_str = ", ".join(affected_symbols[:5])
            if len(affected_symbols) > 5:
                symbols_str += f" +{len(affected_symbols)-5} more"
            full_message += f"\n\nAffected: {symbols_str}"

        return self.send_notification(
            message=full_message,
            title=title,
            priority=priority
        )

    def send_system_alert(self, service_name: str, status: str, 
                         details: Optional[str] = None) -> bool:
        """
        Send a system monitoring alert
        
        Args:
            service_name: Name of the service
            status: UP/DOWN/WARNING
            details: Additional details
            
        Returns:
            True if sent successfully, False otherwise
        """
        priority = self.priority_settings.get("system_alerts", 1)
        
        status_emoji = {"UP": "✅", "DOWN": "❌", "WARNING": "⚠️"}.get(status, "❓")
        
        message = f"{status_emoji} {service_name} is {status}"
        if details:
            message += f"\n\n{details}"

        return self.send_notification(
            message=message,
            title=f"System Alert: {service_name}",
            priority=priority
        )

    def test_connection(self) -> bool:
        """Test Pushover connectivity"""
        return self.send_notification(
            message="Test notification from MarketMan system",
            title="🧪 MarketMan Test",
            priority=0
        )

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        recent_notifications = [t for t in self._notification_history if t > cutoff]
        
        return {
            "enabled": self.enabled,
            "configured": bool(self.api_token and self.user_token),
            "notifications_this_hour": len(recent_notifications),
            "rate_limit": self.rate_limit_per_hour,
            "rate_limited": self._is_rate_limited(),
            "confidence_threshold": self.confidence_threshold,
            "risk_warnings_enabled": self.risk_warnings_enabled
        }


# Global instance
pushover_notifier = PushoverNotifier()


def send_trading_signal(signal: str, confidence: int, title: str, reasoning: str,
                       etfs: Optional[List[str]] = None, article_url: Optional[str] = None,
                       risk_factors: Optional[List[str]] = None) -> bool:
    """Convenience function to send trading signals"""
    return pushover_notifier.send_trading_signal(
        signal, confidence, title, reasoning, etfs, article_url, risk_factors
    )


def send_risk_warning(warning_type: str, message: str, 
                     affected_symbols: Optional[List[str]] = None,
                     severity: str = "medium") -> bool:
    """Convenience function to send risk warnings"""
    return pushover_notifier.send_risk_warning(
        warning_type, message, affected_symbols, severity
    )


def send_system_alert(service_name: str, status: str, details: Optional[str] = None) -> bool:
    """Convenience function to send system alerts"""
    return pushover_notifier.send_system_alert(service_name, status, details)


def test_pushover() -> bool:
    """Convenience function to test Pushover connectivity"""
    return pushover_notifier.test_connection() 