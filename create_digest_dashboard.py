#!/usr/bin/env python3
"""
Create Daily Signals Digest Dashboard in Notion
A "war room" style dashboard with filtered views of MarketMan signals
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def create_daily_digest_page():
    """Create a Daily Signals Digest page with database views"""
    
    notion_token = os.getenv("NOTION_TOKEN")
    parent_page_id = input("Enter the Notion page ID where you want to create the digest (or press Enter to use database parent): ").strip()
    
    if not notion_token:
        print("❌ NOTION_TOKEN not found in .env file")
        return False
    
    # If no parent page specified, we'll need the database ID to find its parent
    database_id = os.getenv("NOTION_DATABASE_ID")
    if not parent_page_id and not database_id:
        print("❌ Need either parent page ID or NOTION_DATABASE_ID in .env")
        return False
    
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # If no parent specified, get the database parent
    if not parent_page_id:
        try:
            db_response = requests.get(f"https://api.notion.com/v1/databases/{database_id}", headers=headers)
            if db_response.status_code == 200:
                parent_page_id = db_response.json()["parent"]["page_id"]
            else:
                print("❌ Could not find database parent page")
                return False
        except Exception as e:
            print(f"❌ Error getting database info: {e}")
            return False
    
    # Clean up page ID format
    if 'notion.so' in parent_page_id:
        parent_page_id = parent_page_id.split('/')[-1].split('?')[0].split('-')[-1]
    parent_page_id = parent_page_id.replace('-', '')
    if len(parent_page_id) == 32:
        parent_page_id = f"{parent_page_id[:8]}-{parent_page_id[8:12]}-{parent_page_id[12:16]}-{parent_page_id[16:20]}-{parent_page_id[20:32]}"
    
    # Create the digest page
    page_data = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "properties": {
            "title": {
                "title": [{"text": {"content": "📊 Daily Signals Digest - Energy War Room"}}]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": "🚨 High-Priority Signals"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": "Critical signals requiring immediate attention (Confidence ≥8)"}}]
                }
            },
            {
                "object": "block",
                "type": "child_database",
                "child_database": {
                    "title": "🚨 High Priority (≥8)",
                    "parent": {"database_id": database_id},
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📈 Bullish Signals"}}]
                }
            },
            {
                "object": "block",
                "type": "child_database",
                "child_database": {
                    "title": "📈 Strong Bullish",
                    "parent": {"database_id": database_id},
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📉 Bearish Signals"}}]
                }
            },
            {
                "object": "block",
                "type": "child_database",
                "child_database": {
                    "title": "📉 Strong Bearish",
                    "parent": {"database_id": database_id},
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "💬 Needs Review"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": "Medium confidence signals that need manual review"}}]
                }
            },
            {
                "object": "block",
                "type": "child_database",
                "child_database": {
                    "title": "💬 Review Queue",
                    "parent": {"database_id": database_id},
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "💡 "}},
                        {"text": {"content": "Pro Tip", "annotations": {"bold": True}}},
                        {"text": {"content": ": Set up filters on each database view above to focus on:\n• Today's signals only\n• Specific ETFs (XLE, ICLN, TAN)\n• Unreviewed items\n• High confidence threshold"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "🤖 Generated by MarketMan v2.0 - "}},
                        {"text": {"content": "Your AI-powered energy sector monitor", "annotations": {"italic": True}}}
                    ]
                }
            }
        ]
    }
    
    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=page_data
        )
        
        if response.status_code == 200:
            result = response.json()
            page_url = result['url']
            print(f"✅ Daily Signals Digest created successfully!")
            print(f"🔗 Dashboard URL: {page_url}")
            print(f"\n📋 Next Steps:")
            print(f"   1. Visit the dashboard and set up filters on each database view")
            print(f"   2. Configure views to show:")
            print(f"      • High Priority: Confidence ≥ 8")
            print(f"      • Bullish: Signal = Bullish, Confidence ≥ 7")
            print(f"      • Bearish: Signal = Bearish, Confidence ≥ 7")
            print(f"      • Review: Confidence 5-7 or Reviewed = False")
            print(f"   3. Bookmark this page for daily monitoring")
            print(f"\n🎯 You now have your own hedge fund war room dashboard!")
            return True
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ Failed to create dashboard: {error_data}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")
        return False

def main():
    print("📊 Daily Signals Digest Dashboard Creator\n")
    print("This will create a 'war room' style dashboard with filtered views of your MarketMan signals.")
    print("Perfect for daily market analysis and team collaboration.\n")
    
    success = create_daily_digest_page()
    
    if success:
        print("\n🚀 Dashboard ready! Start monitoring your energy sector signals like a pro.")
    else:
        print("\n❌ Dashboard creation failed. Check the errors above.")

if __name__ == "__main__":
    main()
