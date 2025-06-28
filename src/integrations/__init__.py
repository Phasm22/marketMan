"""
Integrations module for MarketMan.

This module contains all external integrations including:
- Notion API integration
- Gmail integration
- Pushover notifications
- DeepSeek integration
"""

from .gmail_organizer import GmailOrganizer
from .pushover_utils import send_energy_alert, send_system_alert
from .gmail_poller import GmailPoller
from .notion_reporter import NotionReporter

__all__ = [
    "GmailOrganizer",
    "send_energy_alert",
    "send_system_alert",
    "GmailPoller",
    "NotionReporter",
]
