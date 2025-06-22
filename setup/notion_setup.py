#!/usr/bin/env python3
"""
Notion Database Setup Helper
Creates the required database structure for MarketMan
"""

import os
import requests
import json
import argparse
import sys
from dotenv import load_dotenv

load_dotenv()

def validate_env():
    """Validate required environment variables early"""
    notion_token = os.getenv("NOTION_TOKEN")
    
    if not notion_token:
        print("❌ NOTION_TOKEN not found in .env file")
        print("\n💡 Setup required:")
        print("   1. Create a Notion integration at https://www.notion.com/my-integrations")
        print("   2. Copy the 'Internal Integration Token'")
        print("   3. Add to .env file: NOTION_TOKEN=your_token_here")
        return False
    
    # Test token validity
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.get("https://api.notion.com/v1/users/me", headers=headers)
        if response.status_code == 200:
            print("✅ NOTION_TOKEN is valid")
            return True
        else:
            print("❌ NOTION_TOKEN is invalid or expired")
            return False
    except Exception as e:
        print(f"❌ Error validating NOTION_TOKEN: {e}")
        return False

def check_existing_databases(notion_token, database_name="MarketMan Energy Alerts"):
    """Check for existing databases with the same name to prevent duplicates"""
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        # Search for databases (this is limited but catches most duplicates)
        response = requests.post(
            "https://api.notion.com/v1/search",
            headers=headers,
            json={
                "query": database_name,
                "filter": {"value": "database", "property": "object"}
            }
        )
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            existing_dbs = []
            
            for result in results:
                if result.get("object") == "database":
                    title = ""
                    if result.get("title") and len(result["title"]) > 0:
                        title = result["title"][0].get("text", {}).get("content", "")
                    
                    if database_name.lower() in title.lower():
                        existing_dbs.append({
                            "id": result["id"],
                            "title": title,
                            "url": result["url"]
                        })
            
            return existing_dbs
        
    except Exception as e:
        print(f"⚠️  Could not check for existing databases: {e}")
    
    return []

def create_notion_database(page_id=None, auto_confirm=False):
    """Create a new Notion database with the required properties"""
    
    notion_token = os.getenv("NOTION_TOKEN")
    
    if not page_id:
        page_id = input("Enter your Notion page ID (where you want to create the database): ").strip()
    
    if not page_id:
        print("❌ Page ID is required")
        return False
    
    # Check for existing databases first
    if not auto_confirm:
        existing_dbs = check_existing_databases(notion_token)
        if existing_dbs:
            print(f"\n⚠️  Found {len(existing_dbs)} existing MarketMan database(s):")
            for i, db in enumerate(existing_dbs, 1):
                print(f"   {i}. {db['title']} (ID: {db['id'][:8]}...)")
                print(f"      URL: {db['url']}")
            
            choice = input(f"\nDo you want to create another database? (y/N): ").strip().lower()
            if choice not in ['y', 'yes']:
                print("❌ Database creation cancelled to prevent duplicates")
                print("💡 Use --test to check existing database or --force to skip this check")
                return False
    
    # Clean up page ID (remove URL parts if pasted)
    if 'notion.so' in page_id:
        # Extract ID from URL like: https://www.notion.so/AI-Market-Bot-217f3779ff47809096c1cd3ef1b1c68e
        page_id = page_id.split('/')[-1].split('?')[0].split('-')[-1]
    
    # Remove all dashes and format properly
    page_id = page_id.replace('-', '')
    
    # Format as proper UUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    if len(page_id) == 32:
        page_id = f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:32]}"
    
    print(f"📝 Using page ID: {page_id}")
    
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    database_data = {
        "parent": {"type": "page_id", "page_id": page_id},
        "title": [{"type": "text", "text": {"content": "MarketMan Energy Alerts"}}],
        "properties": {
            "Title": {"title": {}},
            "Signal": {
                "select": {
                    "options": [
                        {"name": "Bullish", "color": "green"},
                        {"name": "Bearish", "color": "red"},
                        {"name": "Neutral", "color": "yellow"}
                    ]
                }
            },
            "Confidence": {"number": {"format": "number"}},
            "ETFs": {
                "multi_select": {
                    "options": [
                        {"name": "XLE", "color": "blue"},
                        {"name": "ICLN", "color": "green"},
                        {"name": "TAN", "color": "orange"}
                    ]
                }
            },
            "Reasoning": {"rich_text": {}},
            "Timestamp": {"date": {}},
            "Link": {"url": {}},
            "Reviewed": {"checkbox": {}}
        }
        }
        }
    }
    
    try:
        response = requests.post(
            "https://api.notion.com/v1/databases",
            headers=headers,
            json=database_data
        )
        
        if response.status_code == 200:
            result = response.json()
            database_id = result['id']
            print(f"✅ Database created successfully!")
            print(f"📝 Database ID: {database_id}")
            print(f"🔗 Database URL: {result['url']}")
            print(f"\n💡 Add this to your .env file:")
            print(f"NOTION_DATABASE_ID={database_id}")
            
            # Auto-update .env file if possible
            env_path = ".env"
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r') as f:
                        content = f.read()
                    
                    if 'NOTION_DATABASE_ID=' not in content:
                        with open(env_path, 'a') as f:
                            f.write(f"\nNOTION_DATABASE_ID={database_id}\n")
                        print(f"✅ Auto-added NOTION_DATABASE_ID to .env file")
                    else:
                        print(f"⚠️  NOTION_DATABASE_ID already exists in .env file - please update manually")
                except Exception as e:
                    print(f"⚠️  Could not auto-update .env file: {e}")
            
            return database_id
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ Failed to create database: {error_data}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def test_existing_database():
    """Test access to existing database"""
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not notion_token or not database_id:
        print("❌ NOTION_TOKEN or NOTION_DATABASE_ID not found in .env file")
        return False
    
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.get(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Database access successful!")
            print(f"📝 Database title: {result['title'][0]['text']['content']}")
            print(f"🔗 Database URL: {result['url']}")
            return True
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ Cannot access database: {error_data}")
            
            if "object_not_found" in str(error_data):
                print("\n💡 This usually means:")
                print("   1. Database ID is incorrect")
                print("   2. Database is not shared with your integration")
                print("   3. Integration doesn't have access permissions")
                print("\n🔧 To fix:")
                print("   1. Go to your Notion database")
                print("   2. Click 'Share' in the top right")
                print("   3. Add your integration by name")
                print("   4. Or create a new database with this script")
            
            return False
            
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Notion Database Setup Helper for MarketMan")
    parser.add_argument("--test", action="store_true", help="Test existing database connection")
    parser.add_argument("--create", action="store_true", help="Create new database")
    parser.add_argument("--page-id", type=str, help="Notion page ID for database creation")
    parser.add_argument("--force", action="store_true", help="Skip duplicate database check")
    parser.add_argument("--auto", action="store_true", help="Auto-confirm actions (for automation)")
    
    args = parser.parse_args()
    
    print("🗄️  Notion Database Setup Helper\n")
    
    # Early validation of environment
    if not validate_env():
        sys.exit(1)
    
    # Handle CLI arguments
    if args.test:
        success = test_existing_database()
    elif args.create:
        if not args.page_id and not args.auto:
            print("\n📋 To create a database, you need a Notion page where it will be created.")
            print("   1. Go to Notion and create or open a page")
            print("   2. Copy the page URL or ID")
            print("   3. Make sure your integration has access to that page\n")
        
        success = create_notion_database(
            page_id=args.page_id, 
            auto_confirm=args.force or args.auto
        )
    elif len(sys.argv) == 1:
        # Interactive mode (no CLI args)
        choice = input("Choose an option:\n1. Test existing database\n2. Create new database\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            success = test_existing_database()
        elif choice == "2":
            print("\n📋 To create a database, you need a Notion page where it will be created.")
            print("   1. Go to Notion and create or open a page")
            print("   2. Copy the page URL or ID")
            print("   3. Make sure your integration has access to that page\n")
            success = create_notion_database()
        else:
            print("❌ Invalid choice")
            return
    else:
        parser.print_help()
        return
    
    if success:
        print("\n🎉 Setup complete! You can now run the news analyzer.")
    else:
        print("\n⚠️  Setup failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
