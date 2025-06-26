#!/usr/bin/env python3
"""
Notion Database Schema Setup for Performance Dashboard

This script helps you create the correct database schema for the MarketMan performance dashboard.
Since Notion doesn't allow creating databases via API, this script provides the exact schema
you need to manually create in your Notion workspace.
"""

def print_trades_database_schema():
    """Print the required schema for the Trades database"""
    print("🗄️ TRADES DATABASE SCHEMA")
    print("=" * 50)
    print("Create a new database in Notion with these properties:")
    print()
    
    schema = [
        ("Ticker", "Title", "ETF ticker symbol (e.g., BOTZ, ROBO)"),
        ("Action", "Select", "Options: BUY, SELL"),
        ("Quantity", "Number", "Number of shares traded"),
        ("Price", "Number", "Execution price per share"),
        ("Trade Value", "Number", "Total trade value (Quantity × Price)"),
        ("Trade Date", "Date", "Date and time of trade execution"),
        ("Signal Confidence", "Number", "Original signal confidence score (0-10)"),
        ("Signal Reference", "Relation", "Link to original MarketMan signal page"),
        ("Notes", "Rich Text", "Additional notes about the trade"),
    ]
    
    for i, (name, prop_type, description) in enumerate(schema, 1):
        print(f"{i:2}. {name:17} | {prop_type:12} | {description}")
    
    print()
    print("📋 SETUP INSTRUCTIONS:")
    print("1. Go to your Notion workspace")
    print("2. Create a new database (can be a full page or inline)")
    print("3. Add each property above with the exact name and type")
    print("4. For 'Action' select property, add options: BUY, SELL")
    print("5. For 'Signal Reference' relation, link to your main signals database")
    print("6. Copy the database ID and update TRADES_DATABASE_ID in .env")
    print()

def print_performance_database_schema():
    """Print the suggested schema for the Performance database"""
    print("📈 PERFORMANCE DATABASE SCHEMA (Optional)")
    print("=" * 50)
    print("Create a database for aggregate performance tracking:")
    print()
    
    schema = [
        ("Period", "Title", "Time period (e.g., '2024-Q4', 'December 2024')"),
        ("Total Trades", "Number", "Number of trades executed"),
        ("Win Rate", "Number", "Percentage of profitable trades"),
        ("Total P&L", "Number", "Total profit/loss in dollars"),
        ("Total P&L %", "Number", "Total return percentage"),
        ("Best Trade", "Number", "Largest single gain"),
        ("Worst Trade", "Number", "Largest single loss"),
        ("Avg Trade Size", "Number", "Average trade value"),
        ("Notes", "Rich Text", "Performance summary and insights"),
    ]
    
    for i, (name, prop_type, description) in enumerate(schema, 1):
        print(f"{i:2}. {name:15} | {prop_type:12} | {description}")
    
    print()

def print_database_id_instructions():
    """Print instructions for finding database IDs"""
    print("🔍 HOW TO FIND DATABASE IDs")
    print("=" * 50)
    print("1. Open your database in Notion (full page view)")
    print("2. Copy the URL from your browser")
    print("3. The database ID is the long string after the last slash")
    print("4. Example URL: https://notion.so/workspace/DatabaseName-21af3779ff4781f4bd62fe644a7a12ef")
    print("5. Database ID: 21af3779ff4781f4bd62fe644a7a12ef")
    print("6. Format as: 21af3779-ff47-81f4-bd62-fe644a7a12ef (add dashes)")
    print()

def main():
    print("🚀 MarketMan Performance Dashboard Setup")
    print("=" * 60)
    print()
    
    print_trades_database_schema()
    print()
    print_performance_database_schema()
    print()
    print_database_id_instructions()
    
    print("⚠️  IMPORTANT NOTES:")
    print("• Property names must match exactly (case-sensitive)")
    print("• The 'Ticker' property must be set as the Title property")
    print("• After creating databases, update your .env file with the real IDs")
    print("• Test the integration with: python3 test_performance_dashboard.py")
    print()
    print("✅ Once set up, MarketMan will automatically log trades to your dashboard!")

if __name__ == "__main__":
    main()
