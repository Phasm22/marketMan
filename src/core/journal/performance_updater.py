#!/usr/bin/env python3
"""
Performance Updater for MarketMan
Reads the TRADES database schema and data from Notion, validates, aggregates, and updates the PERFORMANCE database.
"""
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
TRADES_DATABASE_ID = os.getenv("TRADES_DATABASE_ID")
PERFORMANCE_DATABASE_ID = os.getenv("PERFORMANCE_DATABASE_ID")

NOTION_VERSION = "2022-06-28"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


def get_database_schema(database_id):
    resp = requests.get(f"https://api.notion.com/v1/databases/{database_id}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("properties", {})


def get_all_trades():
    trades = []
    next_cursor = None
    while True:
        url = f"https://api.notion.com/v1/databases/{TRADES_DATABASE_ID}/query"
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor
        resp = requests.post(url, headers=HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()
        for row in data["results"]:
            trades.append(row)
        if not data.get("has_more"):
            break
        next_cursor = data["next_cursor"]
    return trades


def parse_trade_row(row, schema):
    # Map Notion property types to expected fields
    props = row["properties"]
    try:
        ticker = props["Ticker"]["title"][0]["plain_text"].strip()
        action = props["Action"]["select"]["name"].strip().upper()
        quantity = float(props["Quantity"]["number"])
        price = float(props["Price"]["number"])
        trade_value = float(props["Trade Value"]["number"])
        trade_date = props["Trade Date"]["date"]["start"]
        signal_conf = float(props["Signal Confidence"]["number"])
        signal_ref = (
            props["Signal Reference"]["url"] if "url" in props["Signal Reference"] else None
        )
        return {
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "price": price,
            "trade_value": trade_value,
            "trade_date": trade_date,
            "signal_confidence": signal_conf,
            "signal_reference": signal_ref,
        }
    except Exception as e:
        print(f"❌ Invalid trade row: {e}")
        return None


def aggregate_performance(trades):
    # Example: aggregate by month
    from collections import defaultdict

    perf = defaultdict(
        lambda: {"Total Trades": 0, "Total P&L": 0.0, "Win Rate": 0, "Total P&L %": 0.0}
    )
    for trade in trades:
        if not trade:
            continue
        # Parse period (e.g., '2025-06')
        period = trade["trade_date"][:7]
        perf[period]["Total Trades"] += 1
        # For now, P&L is not tracked (need exit price for closed trades)
        # You can extend this logic as needed
    return perf


def update_performance_db(perf):
    for period, stats in perf.items():
        # Build Notion page payload
        payload = {
            "parent": {"database_id": PERFORMANCE_DATABASE_ID},
            "properties": {
                "Period": {"title": [{"text": {"content": period}}]},
                "Total Trades": {"number": stats["Total Trades"]},
                "Total P&L": {"number": stats["Total P&L"]},
                "Win Rate": {"number": stats["Win Rate"]},
                "Total P&L %": {"number": stats["Total P&L %"]},
            },
        }
        resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
        if resp.status_code == 200:
            print(f"✅ Updated performance for {period}")
        else:
            print(f"❌ Failed to update performance for {period}: {resp.text}")


def main():
    print("🚀 Reading TRADES database schema...")
    schema = get_database_schema(TRADES_DATABASE_ID)
    print(f"Schema columns: {list(schema.keys())}")
    print("📥 Fetching all trades...")
    trades_raw = get_all_trades()
    trades = [parse_trade_row(row, schema) for row in trades_raw]
    trades = [t for t in trades if t]
    print(f"Found {len(trades)} valid trades.")
    print("📊 Aggregating performance...")
    perf = aggregate_performance(trades)
    print("📝 Updating PERFORMANCE database...")
    update_performance_db(perf)
    print("✅ Done.")


if __name__ == "__main__":
    main()
