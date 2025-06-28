#!/usr/bin/env python3
"""
Enhanced Performance Tracker for MarketMan
Integrates with Notion and provides comprehensive performance analytics with automated updates.
"""
import os
import time
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from .trade_journal import TradeJournal, TradeEntry

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    # Basic metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    win_rate: float
    
    # Advanced metrics
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    
    # Risk metrics
    max_consecutive_losses: int
    max_consecutive_wins: int
    avg_holding_period: float
    
    # Signal performance
    signal_accuracy: float
    avg_signal_confidence: float
    
    # Sector performance
    sector_performance: Dict[str, float]
    
    # Time-based metrics
    daily_pnl: Dict[str, float]
    weekly_pnl: Dict[str, float]
    monthly_pnl: Dict[str, float]


class PerformanceTracker:
    """Enhanced performance tracking with Notion integration"""
    
    def __init__(self, notion_token: Optional[str] = None):
        self.notion_token = notion_token or os.getenv("NOTION_TOKEN")
        self.trade_journal = TradeJournal()
        
        # Notion database IDs
        self.trades_db_id = os.getenv("TRADES_DATABASE_ID")
        self.performance_db_id = os.getenv("PERFORMANCE_DATABASE_ID")
        
        # Notion API headers
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
    
    def sync_trades_from_notion(self) -> bool:
        """Sync trades from Notion to local trade journal"""
        try:
            if not self.trades_db_id:
                logger.warning("TRADES_DATABASE_ID not configured")
                return False
            
            url = f"https://api.notion.com/v1/databases/{self.trades_db_id}/query"
            all_trades = []
            next_cursor = None
            
            # Fetch all trades from Notion
            while True:
                payload = {"page_size": 100}
                if next_cursor:
                    payload["start_cursor"] = next_cursor
                
                resp = requests.post(url, headers=self.headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                all_trades.extend(data.get("results", []))
                
                if not data.get("has_more"):
                    break
                next_cursor = data.get("next_cursor")
            
            logger.info(f"📊 Fetched {len(all_trades)} trades from Notion")
            
            # Convert and log trades
            synced_count = 0
            for notion_trade in all_trades:
                trade_entry = self._convert_notion_to_trade_entry(notion_trade)
                if trade_entry:
                    # Check if trade already exists
                    existing_trades = self.trade_journal.get_trades(
                        symbol=trade_entry.symbol,
                        start_date=trade_entry.timestamp,
                        end_date=trade_entry.timestamp
                    )
                    
                    if not existing_trades:
                        self.trade_journal.log_trade(trade_entry)
                        synced_count += 1
            
            logger.info(f"✅ Synced {synced_count} new trades to local journal")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error syncing trades from Notion: {e}")
            return False
    
    def _convert_notion_to_trade_entry(self, notion_trade: Dict) -> Optional[TradeEntry]:
        """Convert Notion trade to TradeEntry"""
        try:
            props = notion_trade["properties"]
            
            # Extract basic trade data
            symbol = props["Ticker"]["title"][0]["plain_text"] if props["Ticker"]["title"] else None
            action = props["Action"]["select"]["name"] if props["Action"]["select"] else None
            quantity = float(props["Quantity"]["number"]) if props["Quantity"]["number"] else 0
            price = float(props["Price"]["number"]) if props["Price"]["number"] else 0
            trade_date = props["Trade Date"]["date"]["start"] if props["Trade Date"]["date"] else None
            
            if not all([symbol, action, quantity, price, trade_date]):
                return None
            
            # Calculate trade value
            trade_value = quantity * price
            
            # Extract optional fields
            signal_confidence = None
            if "Signal Confidence" in props and props["Signal Confidence"]["number"]:
                signal_confidence = float(props["Signal Confidence"]["number"])
            
            signal_reference = None
            if "Signal Reference" in props and props["Signal Reference"]["rich_text"]:
                signal_reference = props["Signal Reference"]["rich_text"][0]["plain_text"]
            
            notes = None
            if "Notes" in props and props["Notes"]["rich_text"]:
                notes = props["Notes"]["rich_text"][0]["plain_text"]
            
            return TradeEntry(
                timestamp=trade_date,
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                trade_value=trade_value,
                signal_confidence=signal_confidence,
                signal_reference=signal_reference,
                notes=notes,
                broker="Fidelity"
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Error converting Notion trade: {e}")
            return None
    
    def calculate_comprehensive_metrics(self, days: int = 30) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get trades for the period
        trades = self.trade_journal.get_trades(start_date=start_date)
        
        if not trades:
            return self._empty_metrics()
        
        # Calculate basic metrics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if (t.get('realized_pnl') or 0) > 0)
        losing_trades = sum(1 for t in trades if (t.get('realized_pnl') or 0) < 0)
        total_pnl = sum((t.get('realized_pnl') or 0) for t in trades)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Calculate advanced metrics
        wins = [(t.get('realized_pnl') or 0) for t in trades if (t.get('realized_pnl') or 0) > 0]
        losses = [(t.get('realized_pnl') or 0) for t in trades if (t.get('realized_pnl') or 0) < 0]
        
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        profit_factor = abs(sum(wins) / sum(losses)) if sum(losses) != 0 else float('inf')
        
        # Calculate drawdown
        cumulative_pnl = 0
        max_drawdown = 0
        peak = 0
        
        for trade in trades:
            cumulative_pnl += (trade.get('realized_pnl') or 0)
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            drawdown = peak - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calculate Sharpe ratio
        returns = [(t.get('realized_pnl') or 0) for t in trades]
        avg_return = sum(returns) / len(returns) if returns else 0
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if returns else 0
        sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        
        # Calculate Sortino ratio (downside deviation)
        downside_returns = [r for r in returns if r < 0]
        downside_std = (sum(r ** 2 for r in downside_returns) / len(downside_returns)) ** 0.5 if downside_returns else 0
        sortino_ratio = avg_return / downside_std if downside_std > 0 else 0
        
        # Calculate consecutive wins/losses
        max_consecutive_wins = self._calculate_max_consecutive(trades, lambda x: (x.get('realized_pnl') or 0) > 0)
        max_consecutive_losses = self._calculate_max_consecutive(trades, lambda x: (x.get('realized_pnl') or 0) < 0)
        
        # Calculate average holding period
        holding_periods = [t.get('holding_days', 0) for t in trades if t.get('holding_days')]
        avg_holding_period = sum(holding_periods) / len(holding_periods) if holding_periods else 0
        
        # Calculate signal performance
        signal_trades = [t for t in trades if t.get('signal_confidence')]
        signal_accuracy = 0
        avg_signal_confidence = 0
        
        if signal_trades:
            correct_signals = sum(1 for t in signal_trades if 
                                (t.get('signal_confidence', 0) > 5 and (t.get('realized_pnl') or 0) > 0) or
                                (t.get('signal_confidence', 0) < 5 and (t.get('realized_pnl') or 0) < 0))
            signal_accuracy = (correct_signals / len(signal_trades)) * 100
            avg_signal_confidence = sum(t.get('signal_confidence', 0) for t in signal_trades) / len(signal_trades)
        
        # Calculate sector performance
        sector_performance = self._calculate_sector_performance(trades)
        
        # Calculate time-based P&L
        daily_pnl = self._calculate_time_based_pnl(trades, 'daily')
        weekly_pnl = self._calculate_time_based_pnl(trades, 'weekly')
        monthly_pnl = self._calculate_time_based_pnl(trades, 'monthly')
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=round(total_pnl, 2),
            win_rate=round(win_rate, 2),
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown=round(max_drawdown, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            sortino_ratio=round(sortino_ratio, 2),
            max_consecutive_losses=max_consecutive_losses,
            max_consecutive_wins=max_consecutive_wins,
            avg_holding_period=round(avg_holding_period, 1),
            signal_accuracy=round(signal_accuracy, 2),
            avg_signal_confidence=round(avg_signal_confidence, 2),
            sector_performance=sector_performance,
            daily_pnl=daily_pnl,
            weekly_pnl=weekly_pnl,
            monthly_pnl=monthly_pnl
        )
    
    def _empty_metrics(self) -> PerformanceMetrics:
        """Return empty metrics structure"""
        return PerformanceMetrics(
            total_trades=0, winning_trades=0, losing_trades=0, total_pnl=0.0,
            win_rate=0.0, avg_win=0.0, avg_loss=0.0, profit_factor=0.0,
            max_drawdown=0.0, sharpe_ratio=0.0, sortino_ratio=0.0,
            max_consecutive_losses=0, max_consecutive_wins=0, avg_holding_period=0.0,
            signal_accuracy=0.0, avg_signal_confidence=0.0,
            sector_performance={}, daily_pnl={}, weekly_pnl={}, monthly_pnl={}
        )
    
    def _calculate_max_consecutive(self, trades: List[Dict], condition) -> int:
        """Calculate maximum consecutive wins or losses"""
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in trades:
            if condition(trade):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _calculate_sector_performance(self, trades: List[Dict]) -> Dict[str, float]:
        """Calculate performance by sector"""
        sector_pnl = {}
        
        for trade in trades:
            sector = trade.get('sector', 'Unknown')
            pnl = trade.get('realized_pnl') or 0
            
            if sector not in sector_pnl:
                sector_pnl[sector] = 0
            sector_pnl[sector] += pnl
        
        return {sector: round(pnl, 2) for sector, pnl in sector_pnl.items()}
    
    def _calculate_time_based_pnl(self, trades: List[Dict], period: str) -> Dict[str, float]:
        """Calculate P&L by time period"""
        period_pnl = {}
        
        for trade in trades:
            try:
                trade_date = datetime.fromisoformat(trade['timestamp'])
                pnl = trade.get('realized_pnl', 0)
                
                if period == 'daily':
                    key = trade_date.strftime('%Y-%m-%d')
                elif period == 'weekly':
                    key = trade_date.strftime('%Y-W%U')
                elif period == 'monthly':
                    key = trade_date.strftime('%Y-%m')
                else:
                    continue
                
                if key not in period_pnl:
                    period_pnl[key] = 0
                period_pnl[key] += pnl
                
            except Exception:
                continue
        
        return {period: round(pnl, 2) for period, pnl in period_pnl.items()}
    
    def update_notion_performance(self, metrics: PerformanceMetrics) -> bool:
        """Update Notion performance database with calculated metrics"""
        try:
            if not self.performance_db_id:
                logger.warning("PERFORMANCE_DATABASE_ID not configured")
                return False
            
            url = "https://api.notion.com/v1/pages"
            
            # Create performance summary
            properties = {
                "Date": {"date": {"start": datetime.now().isoformat()}},
                "Total Trades": {"number": metrics.total_trades},
                "Winning Trades": {"number": metrics.winning_trades},
                "Losing Trades": {"number": metrics.losing_trades},
                "Total P&L": {"number": metrics.total_pnl},
                "Win Rate": {"number": metrics.win_rate},
                "Avg Win": {"number": metrics.avg_win},
                "Avg Loss": {"number": metrics.avg_loss},
                "Profit Factor": {"number": metrics.profit_factor},
                "Max Drawdown": {"number": metrics.max_drawdown},
                "Sharpe Ratio": {"number": metrics.sharpe_ratio},
                "Sortino Ratio": {"number": metrics.sortino_ratio},
                "Signal Accuracy": {"number": metrics.signal_accuracy},
                "Avg Signal Confidence": {"number": metrics.avg_signal_confidence},
                "Sector Performance": {"rich_text": [{"text": {"content": json.dumps(metrics.sector_performance)}}]},
                "Status": {"select": {"name": "Updated"}}
            }
            
            payload = {
                "parent": {"database_id": self.performance_db_id},
                "properties": properties
            }
            
            resp = requests.post(url, headers=self.headers, json=payload)
            resp.raise_for_status()
            
            logger.info(f"✅ Updated Notion performance database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating Notion performance: {e}")
            return False
    
    def generate_performance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        # Sync latest trades
        self.sync_trades_from_notion()
        
        # Calculate metrics
        metrics = self.calculate_comprehensive_metrics(days)
        
        # Update Notion
        self.update_notion_performance(metrics)
        
        # Generate report
        report = {
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "metrics": {
                "total_trades": metrics.total_trades,
                "winning_trades": metrics.winning_trades,
                "losing_trades": metrics.losing_trades,
                "total_pnl": metrics.total_pnl,
                "win_rate": f"{metrics.win_rate}%",
                "profit_factor": metrics.profit_factor,
                "max_drawdown": metrics.max_drawdown,
                "sharpe_ratio": metrics.sharpe_ratio,
                "signal_accuracy": f"{metrics.signal_accuracy}%"
            },
            "sector_performance": metrics.sector_performance,
            "risk_metrics": {
                "max_consecutive_wins": metrics.max_consecutive_wins,
                "max_consecutive_losses": metrics.max_consecutive_losses,
                "avg_holding_period": f"{metrics.avg_holding_period} days"
            }
        }
        
        return report


# Convenience functions
def create_performance_tracker() -> PerformanceTracker:
    """Create and return a performance tracker instance"""
    return PerformanceTracker()


def generate_performance_report(days: int = 30) -> Dict[str, Any]:
    """Generate performance report for the specified period"""
    tracker = create_performance_tracker()
    return tracker.generate_performance_report(days) 