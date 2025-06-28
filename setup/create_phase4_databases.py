#!/usr/bin/env python3
"""
Phase 4 Database Creation Script

This script creates the streamlined Phase 4 Notion databases automatically.
It creates databases with only essential fields, removing AI metadata.
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Phase4DatabaseCreator:
    def __init__(self):
        self.notion_token = os.getenv("NOTION_TOKEN")
        if not self.notion_token:
            raise ValueError("NOTION_TOKEN not found in environment variables")
        
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
    
    def get_parent_page_id(self):
        """Get parent page ID from user input"""
        print("📝 To create databases, we need a parent page ID.")
        print("This is the page where your databases will be created.")
        print()
        print("To find your page ID:")
        print("1. Go to the Notion page where you want to create databases")
        print("2. Copy the URL from your browser")
        print("3. The page ID is the long string after the last slash")
        print("4. Example: https://notion.so/workspace/PageName-21af3779ff4781f4bd62fe644a7a12ef")
        print("5. Page ID: 21af3779-ff47-81f4-bd62-fe644a7a12ef")
        print()
        
        parent_page_id = input("Enter your parent page ID: ").strip()
        if not parent_page_id:
            raise ValueError("Parent page ID is required")
        
        # Validate page ID format
        if len(parent_page_id.replace("-", "")) != 32:
            print("⚠️ Warning: Page ID format looks unusual. Make sure it's correct.")
        
        return parent_page_id
    
    def create_trades_database(self, parent_page_id):
        """Create the Phase 4 Trades database"""
        print("🗄️ Creating Trades Database...")
        
        database_properties = {
            "Ticker": {"title": {}},
            "Action": {
                "select": {
                    "options": [
                        {"name": "BUY", "color": "green"},
                        {"name": "SELL", "color": "red"},
                    ]
                }
            },
            "Quantity": {"number": {"format": "number"}},
            "Price": {"number": {"format": "dollar"}},
            "Trade Date": {"date": {}},
            "Trade Value": {"number": {"format": "dollar"}},
            "Notes": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Open", "color": "blue"},
                        {"name": "Closed", "color": "green"},
                        {"name": "Review", "color": "yellow"},
                    ]
                }
            },
        }
        
        create_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "MarketMan Trades - Phase 4"}}],
            "properties": database_properties,
        }
        
        response = requests.post(
            "https://api.notion.com/v1/databases",
            headers=self.headers,
            json=create_data
        )
        
        if response.status_code == 200:
            database_data = response.json()
            database_id = database_data["id"]
            print(f"✅ Created Trades Database: {database_id}")
            print(f"🔗 URL: {database_data['url']}")
            return database_id
        else:
            print(f"❌ Failed to create Trades Database: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    
    def create_signals_database(self, parent_page_id):
        """Create the Phase 4 Signals database"""
        print("📡 Creating Signals Database...")
        
        # ETF options for multi-select
        etf_options = [
            # AI & Tech
            {"name": "BOTZ", "color": "blue"}, {"name": "ROBO", "color": "blue"},
            {"name": "IRBO", "color": "blue"}, {"name": "ARKQ", "color": "blue"},
            {"name": "SMH", "color": "blue"}, {"name": "SOXX", "color": "blue"},
            # Defense & Aerospace
            {"name": "ITA", "color": "red"}, {"name": "XAR", "color": "red"},
            {"name": "DFEN", "color": "red"}, {"name": "PPA", "color": "red"},
            # Nuclear & Uranium
            {"name": "URNM", "color": "yellow"}, {"name": "NLR", "color": "yellow"},
            {"name": "URA", "color": "yellow"},
            # Clean Energy
            {"name": "ICLN", "color": "green"}, {"name": "TAN", "color": "green"},
            {"name": "QCLN", "color": "green"}, {"name": "PBW", "color": "green"},
            {"name": "LIT", "color": "green"}, {"name": "REMX", "color": "green"},
            # Volatility & Inverse
            {"name": "VIXY", "color": "purple"}, {"name": "VXX", "color": "purple"},
            {"name": "SQQQ", "color": "purple"}, {"name": "SPXS", "color": "purple"},
            # Broad Market
            {"name": "XLE", "color": "orange"}, {"name": "XLF", "color": "orange"},
            {"name": "XLK", "color": "orange"}, {"name": "QQQ", "color": "orange"},
            {"name": "SPY", "color": "orange"}
        ]
        
        database_properties = {
            "Title": {"title": {}},
            "Signal": {
                "select": {
                    "options": [
                        {"name": "Bullish", "color": "green"},
                        {"name": "Bearish", "color": "red"},
                        {"name": "Neutral", "color": "gray"},
                    ]
                }
            },
            "Confidence": {"number": {"format": "number"}},
            "ETFs": {"multi_select": {"options": etf_options}},
            "Sector": {
                "select": {
                    "options": [
                        {"name": "Defense", "color": "red"},
                        {"name": "AI", "color": "blue"},
                        {"name": "CleanTech", "color": "green"},
                        {"name": "Nuclear", "color": "yellow"},
                        {"name": "Volatility", "color": "gray"},
                        {"name": "Energy", "color": "orange"},
                        {"name": "Finance", "color": "brown"},
                        {"name": "Tech", "color": "purple"},
                        {"name": "Market", "color": "default"},
                        {"name": "Mixed", "color": "default"},
                    ]
                }
            },
            "Timestamp": {"date": {}},
            "Reasoning": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "New", "color": "blue"},
                        {"name": "Reviewed", "color": "green"},
                        {"name": "Acted On", "color": "purple"},
                        {"name": "Archived", "color": "gray"},
                    ]
                }
            },
            "Journal Notes": {"rich_text": {}},
        }
        
        create_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "MarketMan Signals - Phase 4"}}],
            "properties": database_properties,
        }
        
        response = requests.post(
            "https://api.notion.com/v1/databases",
            headers=self.headers,
            json=create_data
        )
        
        if response.status_code == 200:
            database_data = response.json()
            database_id = database_data["id"]
            print(f"✅ Created Signals Database: {database_id}")
            print(f"🔗 URL: {database_data['url']}")
            return database_id
        else:
            print(f"❌ Failed to create Signals Database: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    
    def create_performance_database(self, parent_page_id):
        """Create the Phase 4 Performance database (optional)"""
        print("📈 Creating Performance Database (Optional)...")
        
        database_properties = {
            "Period": {"title": {}},
            "Total Trades": {"number": {"format": "number"}},
            "Win Rate": {"number": {"format": "percent"}},
            "Total P&L": {"number": {"format": "dollar"}},
            "Notes": {"rich_text": {}},
        }
        
        create_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "MarketMan Performance - Phase 4"}}],
            "properties": database_properties,
        }
        
        response = requests.post(
            "https://api.notion.com/v1/databases",
            headers=self.headers,
            json=create_data
        )
        
        if response.status_code == 200:
            database_data = response.json()
            database_id = database_data["id"]
            print(f"✅ Created Performance Database: {database_id}")
            print(f"🔗 URL: {database_data['url']}")
            return database_id
        else:
            print(f"❌ Failed to create Performance Database: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    
    def create_all_databases(self):
        """Create all Phase 4 databases"""
        print("🚀 MarketMan Phase 4 - Database Creation")
        print("=" * 60)
        print()
        print("This script will create streamlined Phase 4 databases.")
        print("Phase 4 removes AI metadata and focuses on essential data only.")
        print()
        
        # Get parent page ID
        parent_page_id = self.get_parent_page_id()
        
        # Create databases
        databases = {}
        
        # Create Trades database
        trades_db_id = self.create_trades_database(parent_page_id)
        if trades_db_id:
            databases["TRADES_DATABASE_ID"] = trades_db_id
        
        print()
        
        # Create Signals database
        signals_db_id = self.create_signals_database(parent_page_id)
        if signals_db_id:
            databases["SIGNALS_DATABASE_ID"] = signals_db_id
        
        print()
        
        # Ask about Performance database
        create_perf = input("Create Performance Database? (y/N): ").strip().lower()
        if create_perf in ['y', 'yes']:
            perf_db_id = self.create_performance_database(parent_page_id)
            if perf_db_id:
                databases["PERFORMANCE_DATABASE_ID"] = perf_db_id
        
        print()
        print("📝 ENVIRONMENT VARIABLES TO ADD TO .env:")
        print("=" * 60)
        for key, value in databases.items():
            print(f"{key}={value}")
        
        print()
        print("✅ Database creation complete!")
        print("🎯 Phase 4 databases are streamlined and ready for use.")
        print("📊 No AI metadata - only essential trade and signal data.")
        
        return databases

def main():
    try:
        creator = Phase4DatabaseCreator()
        databases = creator.create_all_databases()
        
        print()
        print("🔧 Next Steps:")
        print("1. Add the environment variables above to your .env file")
        print("2. Test the integration: python3 setup/test_phase4_integration.py")
        print("3. Start using Phase 4: python3 src/cli/main.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure NOTION_TOKEN is set in your .env file")

if __name__ == "__main__":
    main() 