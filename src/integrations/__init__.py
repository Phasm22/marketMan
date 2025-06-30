"""
Integrations module for MarketMan.

This module provides external service integrations including Notion, email, and broker APIs.
"""

from .notion_reporter import NotionReporter
from .gmail_organizer import GmailOrganizer
from .gmail_poller import GmailPoller
from .pushover_utils import send_energy_alert, send_system_alert
from .pushover_client import PushoverNotifier, pushover_notifier, send_trading_signal, send_risk_warning, test_pushover

# Phase 3 components
from .fidelity_integration import FidelityIntegration, FidelityTrade, create_fidelity_integration, auto_import_fidelity_trades, setup_fidelity_email_monitoring

# Phase 4 components
from .notion_journal import NotionJournalIntegration, notion_journal

__all__ = [
    # Existing components
    "NotionReporter",
    "GmailOrganizer",
    "GmailPoller",
    "send_energy_alert",
    "send_system_alert",
    
    # Enhanced Pushover components
    "PushoverNotifier",
    "pushover_notifier",
    "send_trading_signal",
    "send_risk_warning",
    "test_pushover",
    
    # Phase 3 components
    "FidelityIntegration",
    "FidelityTrade",
    "create_fidelity_integration",
    "auto_import_fidelity_trades",
    "setup_fidelity_email_monitoring",
    
    # Phase 4 components
    "NotionJournalIntegration",
    "notion_journal"
]
