#!/usr/bin/env python3
"""
Enhanced Notion Database Setup for MarketMan with Contextual Memory
This script sets up the Notion database with all required properties including the new Action field
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()


def create_enhanced_notion_database():
    """Create or update Notion database with enhanced properties for contextual insights"""

    notion_token = os.getenv("NOTION_TOKEN")

    if not notion_token:
        print("❌ NOTION_TOKEN not found in environment variables")
        return False

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # Database properties with enhanced fields
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
        "ETFs": {
            "multi_select": {
                "options": [
                    # AI & Tech
                    {"name": "BOTZ", "color": "blue"},
                    {"name": "ROBO", "color": "blue"},
                    {"name": "IRBO", "color": "blue"},
                    {"name": "ARKQ", "color": "blue"},
                    {"name": "SMH", "color": "blue"},
                    {"name": "SOXX", "color": "blue"},
                    # Defense & Aerospace
                    {"name": "ITA", "color": "red"},
                    {"name": "XAR", "color": "red"},
                    {"name": "DFEN", "color": "red"},
                    {"name": "PPA", "color": "red"},
                    # Nuclear & Uranium
                    {"name": "URNM", "color": "yellow"},
                    {"name": "NLR", "color": "yellow"},
                    {"name": "URA", "color": "yellow"},
                    # Clean Energy
                    {"name": "ICLN", "color": "green"},
                    {"name": "TAN", "color": "green"},
                    {"name": "QCLN", "color": "green"},
                    {"name": "PBW", "color": "green"},
                    {"name": "LIT", "color": "green"},
                    {"name": "REMX", "color": "green"},
                    # Volatility & Inverse
                    {"name": "VIXY", "color": "purple"},
                    {"name": "VXX", "color": "purple"},
                    {"name": "SQQQ", "color": "purple"},
                    {"name": "SPXS", "color": "purple"},
                    # Broad Market
                    {"name": "XLE", "color": "orange"},
                    {"name": "XLF", "color": "orange"},
                    {"name": "XLK", "color": "orange"},
                    {"name": "QQQ", "color": "orange"},
                    {"name": "SPY", "color": "orange"},
                ]
            }
        },
        "Action": {
            "select": {
                "options": [
                    {"name": "BUY", "color": "green"},
                    {"name": "SELL", "color": "red"},
                    {"name": "HOLD", "color": "yellow"},
                ]
            }
        },
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
        "Reasoning": {"rich_text": {}},
        "Timestamp": {"date": {}},
        "Link": {"url": {}},
        "Search Term": {"rich_text": {}},
    }

    # Try to find existing MarketMan database first
    search_response = requests.post(
        "https://api.notion.com/v1/search",
        headers=headers,
        json={
            "query": "MarketMan Energy Analysis",
            "filter": {"property": "object", "value": "database"},
        },
    )

    if search_response.status_code == 200:
        results = search_response.json().get("results", [])
        existing_db = None

        for result in results:
            if result.get("title", [{}])[0].get("plain_text", "") == "MarketMan Energy Analysis":
                existing_db = result
                break

        if existing_db:
            print(f"✅ Found existing MarketMan database: {existing_db['id']}")
            print(f"🔗 Database URL: {existing_db['url']}")
            print("\n📝 To use this database, add this to your .env file:")
            print(f"NOTION_DATABASE_ID={existing_db['id']}")
            return existing_db["id"]

    # Create new database if not found
    print("📝 Creating new MarketMan database...")

    # You'll need to specify a parent page - this is a placeholder
    parent_page_id = input(
        "Enter your Notion page ID where you want to create the database (or press Enter to skip): "
    ).strip()

    if not parent_page_id:
        print(
            "⚠️ No parent page ID provided. Please create the database manually or provide a page ID."
        )
        return False

    create_data = {
        "parent": {"page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "MarketMan Energy Analysis"}}],
        "properties": database_properties,
    }

    response = requests.post(
        "https://api.notion.com/v1/databases", headers=headers, json=create_data
    )

    if response.status_code == 200:
        database_data = response.json()
        database_id = database_data["id"]
        print(f"✅ Created MarketMan database successfully!")
        print(f"🆔 Database ID: {database_id}")
        print(f"🔗 Database URL: {database_data['url']}")
        print("\n📝 Add this to your .env file:")
        print(f"NOTION_DATABASE_ID={database_id}")
        return database_id
    else:
        print(f"❌ Failed to create database: {response.status_code}")
        print(f"Error: {response.text}")
        return False


def test_database_access():
    """Test access to the configured database"""
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_token or not database_id:
        print("❌ Missing NOTION_TOKEN or NOTION_DATABASE_ID in .env file")
        return False

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # Test by retrieving database info
    response = requests.get(f"https://api.notion.com/v1/databases/{database_id}", headers=headers)

    if response.status_code == 200:
        db_data = response.json()
        title = db_data.get("title", [{}])[0].get("plain_text", "Unknown")
        print(f"✅ Successfully connected to database: {title}")

        # Check for required properties
        properties = db_data.get("properties", {})
        required_props = [
            "Title",
            "Signal",
            "Confidence",
            "ETFs",
            "Action",
            "Reasoning",
            "Timestamp",
            "Link",
        ]

        print("\n📋 Database Properties:")
        for prop in required_props:
            if prop in properties:
                print(f"  ✅ {prop}")
            else:
                print(f"  ❌ {prop} (missing)")

        return True
    else:
        print(f"❌ Failed to access database: {response.status_code}")
        print(f"Error: {response.text}")
        return False


def create_test_entry():
    """Create a test entry to verify everything works"""
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_token or not database_id:
        print("❌ Missing NOTION_TOKEN or NOTION_DATABASE_ID")
        return False

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    test_data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Title": {
                "title": [
                    {"text": {"content": "🧪 MarketMan Test Entry - AI ETF Momentum Analysis"}}
                ]
            },
            "Signal": {"select": {"name": "Bullish"}},
            "Confidence": {"number": 8},
            "ETFs": {"multi_select": [{"name": "BOTZ"}, {"name": "ROBO"}, {"name": "ARKQ"}]},
            "Sector": {"select": {"name": "AI"}},
            "Action": {"select": {"name": "BUY"}},
            "Reasoning": {
                "rich_text": [
                    {
                        "text": {
                            "content": "Test analysis with enhanced thematic ETF coverage and contextual memory integration.\n\n🧠 MARKET MEMORY INSIGHTS:\nBOTZ has shown consecutive bullish signals over the past 3 days, indicating strong momentum building in AI/robotics sector. Institutional inflows accelerating."
                        }
                    }
                ]
            },
            "Timestamp": {"date": {"start": "2025-06-21T10:00:00.000Z"}},
            "Link": {"url": "https://example.com"},
        },
    }

    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=test_data)

    if response.status_code == 200:
        page_data = response.json()
        print(f"✅ Test entry created successfully!")
        print(f"🔗 Page URL: {page_data.get('url', 'N/A')}")
        return True
    else:
        print(f"❌ Failed to create test entry: {response.status_code}")
        print(f"Error: {response.text}")
        return False


if __name__ == "__main__":
    import sys

    print("🚀 MarketMan Enhanced Notion Setup")
    print("=" * 50)

    if "--create" in sys.argv:
        create_enhanced_notion_database()
    elif "--test" in sys.argv:
        if test_database_access():
            create_test_entry()
    else:
        print("Available commands:")
        print("  --create    Create new enhanced database")
        print("  --test      Test existing database and create sample entry")
        print("\nMake sure your .env file contains:")
        print("  NOTION_TOKEN=your_integration_token")
        print("  NOTION_DATABASE_ID=your_database_id")
