#!/usr/bin/env python3
"""
Notion v3 Schema Setup Script

This script helps you set up your Notion database with the correct v3 schema fields
for MarketMan signal tracking. It provides instructions and validates your setup.
"""

import os
import sys
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class NotionV3Setup:
    """Helper class for setting up Notion v3 schema"""
    
    def __init__(self):
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.signals_db_id = os.getenv("SIGNALS_DATABASE_ID")
        
        if not self.notion_token:
            print("❌ NOTION_TOKEN not found in environment variables")
            print("Please add NOTION_TOKEN=secret_your_token_here to your .env file")
            sys.exit(1)
            
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
    
    def print_setup_instructions(self):
        """Print step-by-step setup instructions"""
        print("🚀 MarketMan Notion v3 Schema Setup")
        print("=" * 50)
        print()
        print("Follow these steps to set up your Notion database:")
        print()
        print("1. Create a new page in Notion")
        print("2. Add a database with these properties:")
        print()
        
        properties = [
            ("Title", "Title", "Signal title"),
            ("Signal", "Select", "Bullish, Bearish, Neutral"),
            ("Confidence", "Number", "1-10 confidence score"),
            ("ETFs", "Multi-select", "Affected ETF tickers"),
            ("Sector", "Select", "Market sector"),
            ("Timestamp", "Date", "Signal timestamp"),
            ("Reasoning", "Text", "Signal reasoning (bullet-pointed)"),
            ("Status", "Select", "New, Reviewed, Acted On, Archived"),
            ("Journal Notes", "Text", "Optional manual notes"),
            ("If-Then Scenario", "Text", "Validation logic for signal"),
            ("Contradictory Signals", "Text", "Opposing signals/risks"),
            ("Uncertainty Metric", "Text", "Confidence with context"),
            ("Position Risk Bracket", "Text", "Position sizing guidance"),
            ("Price Anchors", "Text", "ETF price context"),
        ]
        
        for i, (name, prop_type, description) in enumerate(properties, 1):
            print(f"   {i:2d}. {name:<20} ({prop_type:<12}) - {description}")
        
        print()
        print("3. Copy the database URL and extract the database ID")
        print("4. Add SIGNALS_DATABASE_ID=your_database_id to your .env file")
        print()
        print("5. Run this script again to validate your setup:")
        print("   python scripts/setup_notion_v3.py --validate")
        print()
    
    def validate_database_schema(self) -> bool:
        """Validate that the database has the correct v3 schema"""
        if not self.signals_db_id:
            print("❌ SIGNALS_DATABASE_ID not found in environment variables")
            print("Please add SIGNALS_DATABASE_ID=your_database_id to your .env file")
            return False
        
        try:
            # Get database schema
            response = requests.get(
                f"https://api.notion.com/v1/databases/{self.signals_db_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to access database: {response.status_code}")
                print(f"Error: {response.text}")
                return False
            
            database = response.json()
            properties = database.get("properties", {})
            
            # Required v3 fields
            required_fields = {
                "Title": "title",
                "Signal": "select",
                "Confidence": "number",
                "ETFs": "multi_select",
                "Sector": "select",
                "Timestamp": "date",
                "Reasoning": "rich_text",
                "Status": "select",
                "If-Then Scenario": "rich_text",
                "Contradictory Signals": "rich_text",
                "Uncertainty Metric": "rich_text",
                "Position Risk Bracket": "rich_text",
                "Price Anchors": "rich_text",
            }
            
            missing_fields = []
            incorrect_types = []
            
            for field_name, expected_type in required_fields.items():
                if field_name not in properties:
                    missing_fields.append(field_name)
                elif properties[field_name]["type"] != expected_type:
                    actual_type = properties[field_name]["type"]
                    incorrect_types.append(f"{field_name} (expected {expected_type}, got {actual_type})")
            
            print("🔍 Validating Notion Database Schema")
            print("=" * 40)
            
            if missing_fields:
                print(f"❌ Missing required fields: {', '.join(missing_fields)}")
                print("Please add these fields to your database.")
                return False
            
            if incorrect_types:
                print(f"❌ Incorrect field types: {', '.join(incorrect_types)}")
                print("Please fix the field types in your database.")
                return False
            
            print("✅ All required v3 fields are present and correctly typed!")
            print()
            print("Optional fields that can be added:")
            print("• Journal Notes (Text) - For manual notes and review")
            print()
            print("🎉 Your Notion database is ready for MarketMan v3 signals!")
            return True
            
        except Exception as e:
            print(f"❌ Error validating database: {e}")
            return False
    
    def test_signal_creation(self) -> bool:
        """Test creating a sample signal to verify the setup"""
        if not self.signals_db_id:
            return False
        
        try:
            # Create a test signal
            test_signal = {
                "parent": {"database_id": self.signals_db_id},
                "properties": {
                    "Title": {"title": [{"text": {"content": "Test Signal - MarketMan v3 Setup"}}]},
                    "Signal": {"select": {"name": "Bullish"}},
                    "Confidence": {"number": 8},
                    "ETFs": {"multi_select": [{"name": "TSLA"}, {"name": "LIT"}]},
                    "Sector": {"select": {"name": "Electric Vehicles"}},
                    "Timestamp": {"date": {"start": "2024-01-01T10:00:00.000Z"}},
                    "Reasoning": {"rich_text": [{"text": {"content": "• Test signal for v3 schema validation\n• This signal will be deleted automatically"}}]},
                    "Status": {"select": {"name": "New"}},
                    "If-Then Scenario": {"rich_text": [{"text": {"content": "If test passes, then schema is correctly configured"}}]},
                    "Contradictory Signals": {"rich_text": [{"text": {"content": "This is a test signal - no real risks"}}]},
                    "Uncertainty Metric": {"rich_text": [{"text": {"content": "Confidence 8, but this is a test signal"}}]},
                    "Position Risk Bracket": {"rich_text": [{"text": {"content": "Position sizing: test (not for real trading)"}}]},
                    "Price Anchors": {"rich_text": [{"text": {"content": "TSLA: $250.00 → $255.00 (+2.0%) | 1.5M (1.2x avg)"}}]},
                }
            }
            
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=test_signal,
                timeout=30
            )
            
            if response.status_code == 200:
                page_id = response.json()["id"]
                print("✅ Test signal created successfully!")
                print(f"📝 Test signal ID: {page_id}")
                print()
                print("🗑️  Cleaning up test signal...")
                
                # Delete the test signal
                delete_response = requests.delete(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    headers=self.headers,
                    timeout=30
                )
                
                if delete_response.status_code == 200:
                    print("✅ Test signal cleaned up successfully!")
                else:
                    print(f"⚠️  Warning: Could not delete test signal: {delete_response.status_code}")
                
                return True
            else:
                print(f"❌ Failed to create test signal: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing signal creation: {e}")
            return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MarketMan Notion v3 Schema Setup")
    parser.add_argument("--validate", action="store_true", help="Validate existing database schema")
    parser.add_argument("--test", action="store_true", help="Test signal creation")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions")
    
    args = parser.parse_args()
    
    setup = NotionV3Setup()
    
    if args.validate:
        if setup.validate_database_schema():
            if args.test:
                setup.test_signal_creation()
    elif args.test:
        if setup.validate_database_schema():
            setup.test_signal_creation()
    else:
        setup.print_setup_instructions()

if __name__ == "__main__":
    main() 