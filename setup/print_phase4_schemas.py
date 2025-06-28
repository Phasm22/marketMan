#!/usr/bin/env python3
"""
Phase 4 Database Schema Printer

This script prints the exact database schemas needed for Phase 4 Notion integration.
Use these schemas to manually create databases in Notion.
"""

def print_trades_database_schema():
    """Print the Phase 4 Trades database schema"""
    print("🗄️ PHASE 4 TRADES DATABASE SCHEMA")
    print("=" * 60)
    print("Create a new database in Notion with these properties:")
    print()
    
    schema = [
        ("Ticker", "Title", "ETF ticker symbol (e.g., BOTZ, ROBO)"),
        ("Action", "Select", "Options: BUY, SELL"),
        ("Quantity", "Number", "Number of shares traded"),
        ("Price", "Number", "Execution price per share"),
        ("Trade Date", "Date", "Date and time of trade (local time)"),
        ("Trade Value", "Number", "Total trade value (Quantity × Price)"),
        ("Notes", "Rich Text", "Manual trade notes and journaling"),
        ("Status", "Select", "Options: Open, Closed, Review"),
    ]
    
    for i, (name, prop_type, description) in enumerate(schema, 1):
        print(f"{i:2}. {name:15} | {prop_type:12} | {description}")
    
    print()
    print("📋 SETUP INSTRUCTIONS:")
    print("1. Go to your Notion workspace")
    print("2. Create a new database (can be a full page or inline)")
    print("3. Add each property above with the exact name and type")
    print("4. For 'Action' select property, add options: BUY, SELL")
    print("5. For 'Status' select property, add options: Open, Closed, Review")
    print("6. Copy the database ID and update TRADES_DATABASE_ID in .env")
    print()

def print_signals_database_schema():
    """Print the Phase 4 Signals database schema"""
    print("📡 PHASE 4 SIGNALS DATABASE SCHEMA")
    print("=" * 60)
    print("Create a new database in Notion with these properties:")
    print()
    
    schema = [
        ("Title", "Title", "Signal title and description"),
        ("Signal", "Select", "Options: Bullish, Bearish, Neutral"),
        ("Confidence", "Number", "Signal confidence score (1-10)"),
        ("ETFs", "Multi-select", "Relevant ETF tickers"),
        ("Sector", "Select", "Market sector classification"),
        ("Timestamp", "Date", "Date and time of signal (local time)"),
        ("Reasoning", "Rich Text", "Signal reasoning and analysis"),
        ("Status", "Select", "Options: New, Reviewed, Acted On, Archived"),
        ("Journal Notes", "Rich Text", "Manual review and journal notes"),
    ]
    
    for i, (name, prop_type, description) in enumerate(schema, 1):
        print(f"{i:2}. {name:15} | {prop_type:12} | {description}")
    
    print()
    print("📋 SETUP INSTRUCTIONS:")
    print("1. Go to your Notion workspace")
    print("2. Create a new database (can be a full page or inline)")
    print("3. Add each property above with the exact name and type")
    print("4. For 'Signal' select property, add options: Bullish, Bearish, Neutral")
    print("5. For 'Status' select property, add options: New, Reviewed, Acted On, Archived")
    print("6. For 'Sector' select property, add options: Defense, AI, CleanTech, Nuclear, Volatility, Energy, Finance, Tech, Market, Mixed")
    print("7. For 'ETFs' multi-select, add all relevant ETF tickers")
    print("8. Copy the database ID and update SIGNALS_DATABASE_ID in .env")
    print()

def print_performance_database_schema():
    """Print the Phase 4 Performance database schema (optional)"""
    print("📈 PHASE 4 PERFORMANCE DATABASE SCHEMA (Optional)")
    print("=" * 60)
    print("Create a database for aggregate performance tracking:")
    print()
    
    schema = [
        ("Period", "Title", "Time period (e.g., '2024-Q4', 'December 2024')"),
        ("Total Trades", "Number", "Number of trades executed"),
        ("Win Rate", "Number", "Percentage of profitable trades"),
        ("Total P&L", "Number", "Total profit/loss in dollars"),
        ("Notes", "Rich Text", "Performance summary and insights"),
    ]
    
    for i, (name, prop_type, description) in enumerate(schema, 1):
        print(f"{i:2}. {name:15} | {prop_type:12} | {description}")
    
    print()
    print("📋 SETUP INSTRUCTIONS:")
    print("1. This database is optional for Phase 4")
    print("2. Create if you want aggregate performance tracking")
    print("3. Add each property above with the exact name and type")
    print("4. Copy the database ID and update PERFORMANCE_DATABASE_ID in .env")
    print()

def print_etf_options():
    """Print the ETF options for the multi-select field"""
    print("📊 ETF OPTIONS FOR MULTI-SELECT FIELD")
    print("=" * 60)
    print("Add these ETFs to the 'ETFs' multi-select property:")
    print()
    
    etf_categories = {
        "AI & Tech": ["BOTZ", "ROBO", "IRBO", "ARKQ", "SMH", "SOXX"],
        "Defense & Aerospace": ["ITA", "XAR", "DFEN", "PPA"],
        "Nuclear & Uranium": ["URNM", "NLR", "URA"],
        "Clean Energy": ["ICLN", "TAN", "QCLN", "PBW", "LIT", "REMX"],
        "Volatility & Inverse": ["VIXY", "VXX", "SQQQ", "SPXS"],
        "Broad Market": ["XLE", "XLF", "XLK", "QQQ", "SPY"]
    }
    
    for category, etfs in etf_categories.items():
        print(f"{category}:")
        for etf in etfs:
            print(f"  • {etf}")
        print()

def print_sector_options():
    """Print the sector options for the select field"""
    print("🏭 SECTOR OPTIONS FOR SELECT FIELD")
    print("=" * 60)
    print("Add these sectors to the 'Sector' select property:")
    print()
    
    sectors = [
        "Defense", "AI", "CleanTech", "Nuclear", "Volatility", 
        "Energy", "Finance", "Tech", "Market", "Mixed"
    ]
    
    for i, sector in enumerate(sectors, 1):
        print(f"{i:2}. {sector}")

def print_database_id_instructions():
    """Print instructions for finding database IDs"""
    print("\n🔍 HOW TO FIND DATABASE IDs")
    print("=" * 60)
    print("1. Open your database in Notion (full page view)")
    print("2. Copy the URL from your browser")
    print("3. The database ID is the long string after the last slash")
    print("4. Example URL: https://notion.so/workspace/DatabaseName-21af3779ff4781f4bd62fe644a7a12ef")
    print("5. Database ID: 21af3779ff4781f4bd62fe644a7a12ef")
    print("6. Format as: 21af3779-ff47-81f4-bd62-fe644a7a12ef (add dashes)")
    print()

def print_env_template():
    """Print the environment variables template"""
    print("\n📝 ENVIRONMENT VARIABLES TEMPLATE")
    print("=" * 60)
    print("Add these to your .env file after creating the databases:")
    print()
    print("# Notion Integration - Phase 4")
    print("NOTION_TOKEN=your_notion_token_here")
    print("TRADES_DATABASE_ID=your_trades_database_id_here")
    print("SIGNALS_DATABASE_ID=your_signals_database_id_here")
    print("PERFORMANCE_DATABASE_ID=your_performance_database_id_here  # Optional")
    print()

def main():
    print("🚀 MarketMan Phase 4 - Streamlined Notion Setup")
    print("=" * 80)
    print()
    print("This script provides the exact database schemas needed for Phase 4.")
    print("Phase 4 focuses on streamlined, essential data only.")
    print()
    
    print_trades_database_schema()
    print()
    print_signals_database_schema()
    print()
    print_performance_database_schema()
    print()
    print_etf_options()
    print()
    print_sector_options()
    print()
    print_database_id_instructions()
    print()
    print_env_template()
    
    print("⚠️  IMPORTANT NOTES:")
    print("• Property names must match exactly (case-sensitive)")
    print("• The 'Ticker' property must be set as the Title property in Trades DB")
    print("• The 'Title' property must be set as the Title property in Signals DB")
    print("• After creating databases, update your .env file with the real IDs")
    print("• Test the integration with: python3 setup/test_phase4_integration.py")
    print()
    print("✅ Once set up, MarketMan will automatically log trades and signals!")
    print("🎯 Phase 4 removes AI metadata and focuses on essential data only.")

if __name__ == "__main__":
    main() 