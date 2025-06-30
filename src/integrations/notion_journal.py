#!/usr/bin/env python3
"""
Notion Journal Integration - Trade and Signal Management

This module provides Notion integration for trade journaling and signal management,
focusing on manual trade tracking and signal review capabilities.
"""

import os
import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class NotionJournalIntegration:
    """Notion integration for trade journaling and signal management"""
    
    def __init__(self):
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.trades_db_id = os.getenv("TRADES_DATABASE_ID")
        self.signals_db_id = os.getenv("SIGNALS_DATABASE_ID")
        self.performance_db_id = os.getenv("PERFORMANCE_DATABASE_ID")
        
        if not self.notion_token:
            logger.warning("NOTION_TOKEN not configured - Notion integration disabled")
            return
        
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
    
    def log_trade(self, trade_data: Dict[str, Any]) -> bool:
        """
        Log a trade to the Phase 4 Trades database
        
        Args:
            trade_data: Dictionary containing:
                - ticker (str): ETF ticker symbol
                - action (str): 'BUY' or 'SELL'
                - quantity (int): Number of shares
                - price (float): Execution price
                - trade_date (str): Trade date (ISO format)
                - notes (str): Optional trade notes
                - status (str): Trade status (Open, Closed, Review)
        
        Returns:
            bool: True if successfully logged, False otherwise
        """
        if not self.trades_db_id:
            logger.warning("TRADES_DATABASE_ID not configured")
            return False
        
        try:
            # Calculate trade value
            trade_value = trade_data.get("quantity", 0) * trade_data.get("price", 0)
            
            # Build properties
            properties = {
                "Ticker": {"title": [{"text": {"content": trade_data.get("ticker", "UNKNOWN")}}]},
                "Action": {"select": {"name": trade_data.get("action", "BUY")}},
                "Quantity": {"number": trade_data.get("quantity", 0)},
                "Price": {"number": trade_data.get("price", 0.0)},
                "Trade Date": {"date": {"start": trade_data.get("trade_date", datetime.now().isoformat())}},
                "Trade Value": {"number": trade_value},
                "Status": {"select": {"name": trade_data.get("status", "Open")}},
            }
            
            # Add optional notes
            if trade_data.get("notes"):
                properties["Notes"] = {"rich_text": [{"text": {"content": trade_data["notes"]}}]}
            
            payload = {
                "parent": {"database_id": self.trades_db_id},
                "properties": properties
            }
            
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Logged trade: {trade_data.get('ticker')} {trade_data.get('action')} {trade_data.get('quantity')} @ ${trade_data.get('price')}")
                return True
            else:
                logger.error(f"❌ Failed to log trade: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error logging trade: {e}")
            return False
    
    def log_signal(self, signal_data: Dict[str, Any]) -> bool:
        """
        Log a signal to the Phase 4 Signals database
        
        Args:
            signal_data: Dictionary containing:
                - title (str): Signal title
                - signal (str): 'Bullish', 'Bearish', or 'Neutral'
                - confidence (float): Signal confidence (1-10)
                - etfs (List[str]): List of relevant ETF tickers
                - sector (str): Market sector
                - reasoning (str): Signal reasoning
                - journal_notes (str): Optional journal notes
        
        Returns:
            bool: True if successfully logged, False otherwise
        """
        if not self.signals_db_id:
            logger.warning("SIGNALS_DATABASE_ID not configured")
            return False
        
        try:
            # Build properties
            properties = {
                "Title": {"title": [{"text": {"content": signal_data.get("title", "Signal")}}]},
                "Signal": {"select": {"name": signal_data.get("signal", "Neutral")}},
                "Confidence": {"number": signal_data.get("confidence", 5.0)},
                "Sector": {"select": {"name": signal_data.get("sector", "Mixed")}},
                "Timestamp": {"date": {"start": signal_data.get("timestamp", datetime.now().isoformat())}},
                "Reasoning": {"rich_text": [{"text": {"content": signal_data.get("reasoning", "")}}]},
                "Status": {"select": {"name": "New"}},
            }
            
            # Add ETFs multi-select
            etfs = signal_data.get("etfs", [])
            if etfs:
                properties["ETFs"] = {"multi_select": [{"name": etf} for etf in etfs]}
            
            # Add optional journal notes
            if signal_data.get("journal_notes"):
                properties["Journal Notes"] = {"rich_text": [{"text": {"content": signal_data["journal_notes"]}}]}
            
            payload = {
                "parent": {"database_id": self.signals_db_id},
                "properties": properties
            }
            
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Logged signal: {signal_data.get('title')} - {signal_data.get('signal')}")
                return True
            else:
                logger.error(f"❌ Failed to log signal: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error logging signal: {e}")
            return False
    
    def update_signal_status(self, signal_id: str, status: str, journal_notes: Optional[str] = None) -> bool:
        """
        Update a signal's status and add journal notes
        
        Args:
            signal_id (str): Notion page ID of the signal
            status (str): New status (New, Reviewed, Acted On, Archived)
            journal_notes (str): Optional journal notes to add
        
        Returns:
            bool: True if successfully updated, False otherwise
        """
        try:
            properties = {
                "Status": {"select": {"name": status}}
            }
            
            if journal_notes:
                properties["Journal Notes"] = {"rich_text": [{"text": {"content": journal_notes}}]}
            
            payload = {"properties": properties}
            
            response = requests.patch(
                f"https://api.notion.com/v1/pages/{signal_id}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Updated signal status: {signal_id} -> {status}")
                return True
            else:
                logger.error(f"❌ Failed to update signal: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating signal: {e}")
            return False
    
    def update_trade_status(self, trade_id: str, status: str, notes: Optional[str] = None) -> bool:
        """
        Update a trade's status and add notes
        
        Args:
            trade_id (str): Notion page ID of the trade
            status (str): New status (Open, Closed, Review)
            notes (str): Optional notes to add
        
        Returns:
            bool: True if successfully updated, False otherwise
        """
        try:
            properties = {
                "Status": {"select": {"name": status}}
            }
            
            if notes:
                properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
            
            payload = {"properties": properties}
            
            response = requests.patch(
                f"https://api.notion.com/v1/pages/{trade_id}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Updated trade status: {trade_id} -> {status}")
                return True
            else:
                logger.error(f"❌ Failed to update trade: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating trade: {e}")
            return False
    
    def get_recent_trades(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get recent trades from Notion
        
        Args:
            days (int): Number of days to look back
        
        Returns:
            List[Dict]: List of trade data
        """
        if not self.trades_db_id:
            logger.warning("TRADES_DATABASE_ID not configured")
            return []
        
        try:
            # Calculate date filter
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            filter_obj = {
                "property": "Trade Date",
                "date": {
                    "on_or_after": cutoff_date
                }
            }
            
            payload = {
                "filter": filter_obj,
                "sorts": [{"property": "Trade Date", "direction": "descending"}],
                "page_size": 100
            }
            
            response = requests.post(
                f"https://api.notion.com/v1/databases/{self.trades_db_id}/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                trades = []
                
                for result in data.get("results", []):
                    props = result["properties"]
                    trade = {
                        "id": result["id"],
                        "ticker": props["Ticker"]["title"][0]["plain_text"] if props["Ticker"]["title"] else None,
                        "action": props["Action"]["select"]["name"] if props["Action"]["select"] else None,
                        "quantity": props["Quantity"]["number"] if props["Quantity"]["number"] else 0,
                        "price": props["Price"]["number"] if props["Price"]["number"] else 0,
                        "trade_date": props["Trade Date"]["date"]["start"] if props["Trade Date"]["date"] else None,
                        "status": props["Status"]["select"]["name"] if props["Status"]["select"] else None,
                        "notes": props["Notes"]["rich_text"][0]["plain_text"] if props["Notes"]["rich_text"] else None,
                    }
                    trades.append(trade)
                
                logger.info(f"📊 Retrieved {len(trades)} recent trades from Notion")
                return trades
            else:
                logger.error(f"❌ Failed to get trades: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting trades: {e}")
            return []
    
    def get_recent_signals(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get recent signals from Notion
        
        Args:
            days (int): Number of days to look back
        
        Returns:
            List[Dict]: List of signal data
        """
        if not self.signals_db_id:
            logger.warning("SIGNALS_DATABASE_ID not configured")
            return []
        
        try:
            # Calculate date filter
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            filter_obj = {
                "property": "Timestamp",
                "date": {
                    "on_or_after": cutoff_date
                }
            }
            
            payload = {
                "filter": filter_obj,
                "sorts": [{"property": "Timestamp", "direction": "descending"}],
                "page_size": 100
            }
            
            response = requests.post(
                f"https://api.notion.com/v1/databases/{self.signals_db_id}/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                signals = []
                
                for result in data.get("results", []):
                    props = result["properties"]
                    
                    # Extract ETFs
                    etfs = []
                    if "ETFs" in props and props["ETFs"]["multi_select"]:
                        etfs = [etf["name"] for etf in props["ETFs"]["multi_select"]]
                    
                    signal = {
                        "id": result["id"],
                        "title": props["Title"]["title"][0]["plain_text"] if props["Title"]["title"] else None,
                        "signal": props["Signal"]["select"]["name"] if props["Signal"]["select"] else None,
                        "confidence": props["Confidence"]["number"] if props["Confidence"]["number"] else 0,
                        "etfs": etfs,
                        "sector": props["Sector"]["select"]["name"] if props["Sector"]["select"] else None,
                        "timestamp": props["Timestamp"]["date"]["start"] if props["Timestamp"]["date"] else None,
                        "reasoning": props["Reasoning"]["rich_text"][0]["plain_text"] if props["Reasoning"]["rich_text"] else None,
                        "status": props["Status"]["select"]["name"] if props["Status"]["select"] else None,
                        "journal_notes": props["Journal Notes"]["rich_text"][0]["plain_text"] if props["Journal Notes"]["rich_text"] else None,
                    }
                    signals.append(signal)
                
                logger.info(f"📊 Retrieved {len(signals)} recent signals from Notion")
                return signals
            else:
                logger.error(f"❌ Failed to get signals: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting signals: {e}")
            return []
    
    def log_performance_summary(self, performance_data: Dict[str, Any]) -> bool:
        """
        Log performance summary to the Performance database (optional)
        
        Args:
            performance_data: Dictionary containing:
                - period (str): Time period (e.g., '2024-Q4')
                - total_trades (int): Number of trades
                - win_rate (float): Win rate percentage
                - total_pnl (float): Total P&L
                - notes (str): Performance notes
        
        Returns:
            bool: True if successfully logged, False otherwise
        """
        if not self.performance_db_id:
            logger.warning("PERFORMANCE_DATABASE_ID not configured")
            return False
        
        try:
            properties = {
                "Period": {"title": [{"text": {"content": performance_data.get("period", "Unknown")}}]},
                "Total Trades": {"number": performance_data.get("total_trades", 0)},
                "Win Rate": {"number": performance_data.get("win_rate", 0.0)},
                "Total P&L": {"number": performance_data.get("total_pnl", 0.0)},
            }
            
            if performance_data.get("notes"):
                properties["Notes"] = {"rich_text": [{"text": {"content": performance_data["notes"]}}]}
            
            payload = {
                "parent": {"database_id": self.performance_db_id},
                "properties": properties
            }
            
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Logged performance summary: {performance_data.get('period')}")
                return True
            else:
                logger.error(f"❌ Failed to log performance: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error logging performance: {e}")
            return False

# Global instance for easy access
notion_journal = NotionJournalIntegration() 