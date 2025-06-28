#!/usr/bin/env python3
"""
Notion Imports Watcher for MarketMan
Watches a Notion 'Imports' database/page for new broker statement uploads, processes them, and auto-populates the TRADES and PERFORMANCE databases.
"""
import os
import time
import requests
import csv
import argparse
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIG ---
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
IMPORTS_DATABASE_ID = os.getenv("IMPORTS_DATABASE_ID")  # Notion DB/page for uploads
TRADES_DATABASE_ID = os.getenv("TRADES_DATABASE_ID")
PERFORMANCE_DATABASE_ID = os.getenv("PERFORMANCE_DATABASE_ID")
NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


# --- UTILS ---
def get_new_imports():
    """Query the Imports database for new (unprocessed) uploads"""
    url = f"https://api.notion.com/v1/databases/{IMPORTS_DATABASE_ID}/query"
    payload = {"filter": {"property": "Status", "select": {"equals": "New"}}, "page_size": 10}
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json().get("results", [])


def download_file_from_notion(file_prop):
    """Download the file from Notion file property (assumes external file)"""
    files = file_prop.get("files", [])
    if not files:
        return None
    file_url = files[0].get("external", {}).get("url") or files[0].get("file", {}).get("url")
    if not file_url:
        return None
    local_path = f"/tmp/{files[0]['name']}"
    r = requests.get(file_url)
    with open(local_path, "wb") as f:
        f.write(r.content)
    return local_path


def mark_import_processed(page_id, filename=None, error_message=None, debug=False):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    properties = {"Status": {"select": {"name": "Processed"}}}
    if filename:
        properties["File Name"] = {"title": [{"text": {"content": filename}}]}
    if error_message:
        properties["Notes/Error Message"] = {"rich_text": [{"text": {"content": error_message}}]}
    properties["Processed Date"] = {"date": {"start": datetime.now().isoformat()}}
    payload = {"properties": properties}
    resp = requests.patch(url, headers=HEADERS, json=payload)
    if debug:
        print(f"[DEBUG] mark_import_processed response: {resp.status_code} {resp.text}")
    return resp.status_code == 200


def trade_exists_in_notion(trade, debug=False):
    """Check if a trade with the same Symbol, Action, Quantity, Price, and Trade Date exists in Notion TRADES DB."""
    url = f"https://api.notion.com/v1/databases/{TRADES_DATABASE_ID}/query"
    filter_obj = {
        "and": [
            {"property": "Ticker", "title": {"equals": trade["Symbol"]}},
            {"property": "Action", "select": {"equals": trade["Action"]}},
            {"property": "Quantity", "number": {"equals": float(trade["Quantity"])}},
            {"property": "Price", "number": {"equals": float(trade["Price"])}},
            {"property": "Trade Date", "date": {"equals": trade["Run Date"]}},
        ]
    }
    payload = {"filter": filter_obj, "page_size": 1}
    resp = requests.post(url, headers=HEADERS, json=payload)
    if debug:
        print(f"[DEBUG] trade_exists_in_notion response: {resp.status_code} {resp.text}")
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        return len(results) > 0
    return False


def add_trade_to_notion(trade, debug=False):
    """Add a single trade to the Notion TRADES database, skipping if duplicate."""
    if trade_exists_in_notion(trade, debug=debug):
        if debug:
            print(
                f"[SKIP] Duplicate trade found, skipping: {trade['Symbol']} {trade['Action']} {trade['Quantity']} @ {trade['Price']} {trade['Run Date']}"
            )
        return False
    if debug:
        print(f"[DEBUG] Trade fields: {trade}")
    payload = {
        "parent": {"database_id": TRADES_DATABASE_ID},
        "properties": {
            "Ticker": {"title": [{"text": {"content": trade["Symbol"]}}]},
            "Action": {"select": {"name": trade["Action"]}},
            "Quantity": {"number": float(trade["Quantity"])},
            "Price": {"number": float(trade["Price"])},
            "Trade Date": {"date": {"start": trade["Run Date"]}},
        },
    }
    try:
        trade_value = float(trade["Quantity"]) * float(trade["Price"])
        payload["properties"]["Trade Value"] = {"number": trade_value}
    except Exception:
        pass
    if "Signal Confidence" in trade and trade["Signal Confidence"]:
        payload["properties"]["Signal Confidence"] = {"number": float(trade["Signal Confidence"])}
    if "Signal Reference" in trade and trade["Signal Reference"]:
        payload["properties"]["Signal Reference"] = {
            "rich_text": [{"text": {"content": str(trade["Signal Reference"])}}]
        }
    if debug:
        print(f"[DEBUG] Trade payload: {payload}")
    resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
    if debug:
        print(f"[DEBUG] add_trade_to_notion response: {resp.status_code} {resp.text}")
    if resp.status_code == 200:
        if debug:
            print(
                f"[NOTION] Added trade: {trade['Symbol']} {trade['Action']} {trade['Quantity']} @ {trade['Price']}"
            )
        return True
    else:
        print(f"[NOTION] Failed to add trade: {resp.text}")
        return False


# --- MAIN WORKFLOW ---
def process_import(file_path, debug=False):
    """Parse the broker file and add trades to Notion (essentials only)"""
    print(f"[IMPORT] Processing {file_path} ... (CSV parse and import)")
    with open(file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        if debug:
            print(f"[DEBUG] CSV Header: {reader.fieldnames}")
        row_count = 0
        imported_count = 0
        for row in reader:
            row_count += 1
            row = {
                k.lstrip("\ufeff").strip(): (v.strip() if isinstance(v, str) else v)
                for k, v in row.items()
            }
            if debug:
                print(f"[DEBUG] Raw CSV row {row_count}: {row}")
            essentials = ["Run Date", "Action", "Symbol", "Quantity", "Price"]
            missing = [f for f in essentials if not row.get(f)]
            if missing:
                if debug:
                    print(f"[WARN] Skipping row {row_count} due to missing fields: {missing}")
                continue
            action = (
                "Buy"
                if "BOUGHT" in row["Action"].upper()
                else "Sell"
                if "SOLD" in row["Action"].upper()
                else row["Action"]
            )
            trade = {
                "Run Date": datetime.strptime(row["Run Date"], "%m/%d/%y").date().isoformat(),
                "Action": action,
                "Symbol": row["Symbol"],
                "Quantity": row["Quantity"],
                "Price": row["Price"],
                "Signal Confidence": row.get("Signal Confidence", ""),
                "Signal Reference": row.get("Signal Reference", ""),
            }
            if debug:
                print(f"[DEBUG] Parsed trade row: {trade}")
            add_trade_to_notion(trade, debug=debug)
            imported_count += 1
        if debug:
            print(f"[DEBUG] Total rows: {row_count}, Imported: {imported_count}")
    return True


def main():
    parser = argparse.ArgumentParser(description="MarketMan Notion Imports Watcher")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    debug = args.debug
    print("🚀 MarketMan Notion Imports Watcher started.")
    while True:
        try:
            imports = get_new_imports()
            if not imports:
                print(f"[{datetime.now()}] No new imports. Sleeping...")
                time.sleep(60)
                continue
            for entry in imports:
                page_id = entry["id"]
                props = entry["properties"]
                file_prop = props.get("File")
                filename = (
                    file_prop["files"][0]["name"] if file_prop and file_prop.get("files") else None
                )
                if not file_prop:
                    print(f"[WARN] No file found in import entry {page_id}")
                    mark_import_processed(
                        page_id, filename, error_message="No file found", debug=debug
                    )
                    continue
                file_path = download_file_from_notion(file_prop)
                if not file_path:
                    print(f"[WARN] Could not download file for entry {page_id}")
                    mark_import_processed(
                        page_id, filename, error_message="Could not download file", debug=debug
                    )
                    continue
                try:
                    if process_import(file_path, debug=debug):
                        print(f"[SUCCESS] Processed {file_path}")
                        mark_import_processed(page_id, filename, debug=debug)
                    else:
                        print(f"[FAIL] Failed to process {file_path}")
                        mark_import_processed(
                            page_id, filename, error_message="Failed to process file", debug=debug
                        )
                except Exception as e:
                    print(f"[ERROR] {e}")
                    mark_import_processed(page_id, filename, error_message=str(e), debug=debug)
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(60)


if __name__ == "__main__":
    main()
