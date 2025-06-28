#!/usr/bin/env python3
"""
Fidelity Integration for MarketMan
Low-friction trade import automation using email parsing and CSV processing.
"""
import os
import csv
import re
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path

from src.core.journal.trade_journal import TradeJournal, TradeEntry, log_trade_from_dict

logger = logging.getLogger(__name__)


@dataclass
class FidelityTrade:
    """Fidelity trade data structure"""
    trade_date: str
    symbol: str
    action: str  # Buy/Sell
    quantity: float
    price: float
    trade_value: float
    commission: float = 0.0
    fees: float = 0.0
    account: str = ""
    order_id: str = ""
    execution_time: str = ""
    
    # Additional fields
    market_center: str = ""
    order_type: str = ""
    time_in_force: str = ""


class FidelityIntegration:
    """Fidelity trade import automation"""
    
    def __init__(self, 
                 email_folder: str = "data/fidelity_emails",
                 csv_folder: str = "data/fidelity_csv",
                 processed_folder: str = "data/processed"):
        self.email_folder = Path(email_folder)
        self.csv_folder = Path(csv_folder)
        self.processed_folder = Path(processed_folder)
        
        # Create directories
        self.email_folder.mkdir(parents=True, exist_ok=True)
        self.csv_folder.mkdir(parents=True, exist_ok=True)
        self.processed_folder.mkdir(parents=True, exist_ok=True)
        
        self.trade_journal = TradeJournal()
        
        # Fidelity-specific patterns
        self.trade_patterns = {
            'email_subject': [
                r'Order Executed',
                r'Trade Confirmation',
                r'Order Fill',
                r'Execution Report'
            ],
            'csv_headers': [
                ['Run Date', 'Action', 'Symbol', 'Quantity', 'Price'],
                ['Trade Date', 'Action', 'Symbol', 'Quantity', 'Price'],
                ['Date', 'Type', 'Symbol', 'Shares', 'Price'],
                ['Execution Date', 'Side', 'Symbol', 'Quantity', 'Price']
            ]
        }
    
    def process_fidelity_emails(self) -> List[FidelityTrade]:
        """Process Fidelity trade confirmation emails"""
        trades = []
        
        # Look for email files in the email folder
        for email_file in self.email_folder.glob("*.eml"):
            try:
                email_trades = self._parse_fidelity_email(email_file)
                trades.extend(email_trades)
                
                # Move to processed folder
                processed_path = self.processed_folder / f"email_{email_file.name}"
                email_file.rename(processed_path)
                
                logger.info(f"📧 Processed email: {email_file.name} -> {len(email_trades)} trades")
                
            except Exception as e:
                logger.error(f"❌ Error processing email {email_file.name}: {e}")
        
        return trades
    
    def _parse_fidelity_email(self, email_file: Path) -> List[FidelityTrade]:
        """Parse individual Fidelity email for trade data"""
        trades = []
        
        with open(email_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract trade information using regex patterns
        # This is a simplified parser - you may need to adjust based on actual email format
        
        # Look for trade confirmation patterns
        trade_blocks = re.findall(
            r'(?:Order|Trade|Execution).*?(?:Symbol|Ticker).*?(?:Quantity|Shares).*?(?:Price|Amount)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        for block in trade_blocks:
            try:
                # Extract symbol
                symbol_match = re.search(r'(?:Symbol|Ticker)[:\s]+([A-Z]{1,5})', block, re.IGNORECASE)
                symbol = symbol_match.group(1) if symbol_match else None
                
                # Extract action (Buy/Sell)
                action_match = re.search(r'(Buy|Sell|Bought|Sold)', block, re.IGNORECASE)
                action = action_match.group(1) if action_match else None
                if action:
                    action = "Buy" if action.lower() in ['buy', 'bought'] else "Sell"
                
                # Extract quantity
                qty_match = re.search(r'(?:Quantity|Shares)[:\s]+([\d,]+)', block, re.IGNORECASE)
                quantity = float(qty_match.group(1).replace(',', '')) if qty_match else None
                
                # Extract price
                price_match = re.search(r'(?:Price|Amount)[:\s]+\$?([\d,]+\.?\d*)', block, re.IGNORECASE)
                price = float(price_match.group(1).replace(',', '')) if price_match else None
                
                # Extract date
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', block)
                trade_date = date_match.group(1) if date_match else datetime.now().strftime('%m/%d/%y')
                
                if all([symbol, action, quantity, price]):
                    trade_value = quantity * price
                    
                    trade = FidelityTrade(
                        trade_date=trade_date,
                        symbol=symbol,
                        action=action,
                        quantity=quantity,
                        price=price,
                        trade_value=trade_value
                    )
                    trades.append(trade)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error parsing trade block: {e}")
                continue
        
        return trades
    
    def process_fidelity_csv(self, csv_file: Optional[Path] = None) -> List[FidelityTrade]:
        """Process Fidelity CSV trade files"""
        trades = []
        
        if csv_file:
            csv_files = [csv_file]
        else:
            csv_files = list(self.csv_folder.glob("*.csv"))
        
        for file_path in csv_files:
            try:
                file_trades = self._parse_fidelity_csv(file_path)
                trades.extend(file_trades)
                
                # Move to processed folder
                processed_path = self.processed_folder / f"csv_{file_path.name}"
                file_path.rename(processed_path)
                
                logger.info(f"📊 Processed CSV: {file_path.name} -> {len(file_trades)} trades")
                
            except Exception as e:
                logger.error(f"❌ Error processing CSV {file_path.name}: {e}")
        
        return trades
    
    def _parse_fidelity_csv(self, csv_file: Path) -> List[FidelityTrade]:
        """Parse Fidelity CSV file for trade data"""
        trades = []
        
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            # Try to detect the CSV format
            sample = f.read(1024)
            f.seek(0)
            
            # Try different CSV formats
            for header_pattern in self.trade_patterns['csv_headers']:
                try:
                    reader = csv.DictReader(f)
                    
                    # Check if headers match expected pattern
                    if all(header in reader.fieldnames for header in header_pattern):
                        for row in reader:
                            try:
                                trade = self._parse_csv_row(row, header_pattern)
                                if trade:
                                    trades.append(trade)
                            except Exception as e:
                                logger.warning(f"⚠️ Error parsing CSV row: {e}")
                                continue
                        
                        break  # Found matching format
                    
                    f.seek(0)  # Reset file pointer for next attempt
                    
                except Exception:
                    f.seek(0)  # Reset file pointer for next attempt
                    continue
        
        return trades
    
    def _parse_csv_row(self, row: Dict[str, str], header_pattern: List[str]) -> Optional[FidelityTrade]:
        """Parse individual CSV row based on header pattern"""
        try:
            # Map headers to expected fields
            if header_pattern == ['Run Date', 'Action', 'Symbol', 'Quantity', 'Price']:
                trade_date = row.get('Run Date', '')
                action = row.get('Action', '')
                symbol = row.get('Symbol', '')
                quantity = float(row.get('Quantity', '0').replace(',', ''))
                price = float(row.get('Price', '0').replace('$', '').replace(',', ''))
                
            elif header_pattern == ['Trade Date', 'Action', 'Symbol', 'Quantity', 'Price']:
                trade_date = row.get('Trade Date', '')
                action = row.get('Action', '')
                symbol = row.get('Symbol', '')
                quantity = float(row.get('Quantity', '0').replace(',', ''))
                price = float(row.get('Price', '0').replace('$', '').replace(',', ''))
                
            elif header_pattern == ['Date', 'Type', 'Symbol', 'Shares', 'Price']:
                trade_date = row.get('Date', '')
                action = row.get('Type', '')
                symbol = row.get('Symbol', '')
                quantity = float(row.get('Shares', '0').replace(',', ''))
                price = float(row.get('Price', '0').replace('$', '').replace(',', ''))
                
            elif header_pattern == ['Execution Date', 'Side', 'Symbol', 'Quantity', 'Price']:
                trade_date = row.get('Execution Date', '')
                action = row.get('Side', '')
                symbol = row.get('Symbol', '')
                quantity = float(row.get('Quantity', '0').replace(',', ''))
                price = float(row.get('Price', '0').replace('$', '').replace(',', ''))
                
            else:
                return None
            
            # Normalize action
            if action:
                action = "Buy" if action.lower() in ['buy', 'bought', 'buy to open'] else "Sell"
            
            # Validate required fields
            if not all([trade_date, symbol, action, quantity, price]):
                return None
            
            # Calculate trade value
            trade_value = quantity * price
            
            # Extract additional fields if available
            commission = float(row.get('Commission', '0').replace('$', '').replace(',', ''))
            fees = float(row.get('Fees', '0').replace('$', '').replace(',', ''))
            account = row.get('Account', '')
            order_id = row.get('Order ID', '')
            
            return FidelityTrade(
                trade_date=trade_date,
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                trade_value=trade_value,
                commission=commission,
                fees=fees,
                account=account,
                order_id=order_id
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing CSV row: {e}")
            return None
    
    def import_trades_to_journal(self, trades: List[FidelityTrade]) -> int:
        """Import Fidelity trades to trade journal"""
        imported_count = 0
        
        for trade in trades:
            try:
                # Convert to TradeEntry
                trade_entry = TradeEntry(
                    timestamp=self._normalize_date(trade.trade_date),
                    symbol=trade.symbol,
                    action=trade.action,
                    quantity=trade.quantity,
                    price=trade.price,
                    trade_value=trade.trade_value,
                    notes=f"Fidelity import - Order ID: {trade.order_id}, Account: {trade.account}",
                    broker="Fidelity",
                    tags=["fidelity", "import"]
                )
                
                # Check for duplicates
                existing_trades = self.trade_journal.get_trades(
                    symbol=trade.symbol,
                    start_date=trade_entry.timestamp,
                    end_date=trade_entry.timestamp
                )
                
                if not existing_trades:
                    self.trade_journal.log_trade(trade_entry)
                    imported_count += 1
                    logger.info(f"📝 Imported trade: {trade.symbol} {trade.action} {trade.quantity} @ {trade.price}")
                else:
                    logger.debug(f"⏭️ Skipped duplicate trade: {trade.symbol} {trade.action} {trade.quantity} @ {trade.price}")
                
            except Exception as e:
                logger.error(f"❌ Error importing trade {trade.symbol}: {e}")
        
        return imported_count
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to ISO format"""
        try:
            # Try different date formats
            for fmt in ['%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            
            # If no format matches, return current date
            return datetime.now().date().isoformat()
            
        except Exception:
            return datetime.now().date().isoformat()
    
    def auto_import_trades(self) -> Dict[str, Any]:
        """Automatically import all available Fidelity trades"""
        results = {
            'email_trades': 0,
            'csv_trades': 0,
            'imported_trades': 0,
            'errors': []
        }
        
        try:
            # Process emails
            email_trades = self.process_fidelity_emails()
            results['email_trades'] = len(email_trades)
            
            # Process CSV files
            csv_trades = self.process_fidelity_csv()
            results['csv_trades'] = len(csv_trades)
            
            # Combine all trades
            all_trades = email_trades + csv_trades
            
            # Import to journal
            imported_count = self.import_trades_to_journal(all_trades)
            results['imported_trades'] = imported_count
            
            logger.info(f"✅ Auto-import completed: {imported_count} trades imported from {len(all_trades)} total")
            
        except Exception as e:
            error_msg = f"Auto-import failed: {e}"
            results['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        return results
    
    def setup_email_monitoring(self, email_address: str, password: str) -> bool:
        """Setup email monitoring for Fidelity trade confirmations"""
        try:
            # This would integrate with your existing Gmail poller
            # For now, we'll create a configuration file
            
            config = {
                'fidelity_email': email_address,
                'email_password': password,
                'email_folder': str(self.email_folder),
                'monitoring_enabled': True,
                'check_interval_minutes': 15
            }
            
            config_file = Path('config/fidelity_email_config.json')
            config_file.parent.mkdir(exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"✅ Email monitoring configured for {email_address}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up email monitoring: {e}")
            return False


# Convenience functions
def create_fidelity_integration() -> FidelityIntegration:
    """Create and return a Fidelity integration instance"""
    return FidelityIntegration()


def auto_import_fidelity_trades() -> Dict[str, Any]:
    """Automatically import all available Fidelity trades"""
    integration = create_fidelity_integration()
    return integration.auto_import_trades()


def setup_fidelity_email_monitoring(email_address: str, password: str) -> bool:
    """Setup email monitoring for Fidelity trade confirmations"""
    integration = create_fidelity_integration()
    return integration.setup_email_monitoring(email_address, password) 