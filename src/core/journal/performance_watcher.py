#!/usr/bin/env python3
"""
MarketMan Performance Watcher
Aggregates trades from the TRADES table, matches buys and sells (FIFO), computes realized P&L, holding period, and updates the PERFORMANCE table in Notion.
"""
import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIG ---
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


def fetch_all_trades():
    """Fetch all trades from the Notion TRADES database."""
    url = f"https://api.notion.com/v1/databases/{TRADES_DATABASE_ID}/query"
    all_trades = []
    next_cursor = None
    while True:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor
        resp = requests.post(url, headers=HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()
        all_trades.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        next_cursor = data.get("next_cursor")
    return all_trades


def parse_trade(page):
    props = page["properties"]
    return {
        "id": page["id"],
        "Symbol": props["Ticker"]["title"][0]["plain_text"] if props["Ticker"]["title"] else None,
        "Action": props["Action"]["select"]["name"] if props["Action"]["select"] else None,
        "Quantity": float(props["Quantity"]["number"]),
        "Price": float(props["Price"]["number"]),
        "Trade Date": props["Trade Date"]["date"]["start"] if props["Trade Date"]["date"] else None,
    }


def aggregate_trades(trades):
    """Group trades by symbol and sort by date."""
    from collections import defaultdict

    grouped = defaultdict(list)
    for t in trades:
        if t["Symbol"]:
            grouped[t["Symbol"]].append(t)
    for symbol in grouped:
        grouped[symbol].sort(key=lambda x: x["Trade Date"])
    return grouped


def compute_performance_for_symbol(trades):
    """Simple FIFO matching for buys and sells, returns realized P&L and holding period for each sell."""
    lots = []  # open buy lots: [{qty, price, date}]
    results = []
    for t in trades:
        if t["Action"] == "Buy":
            lots.append({"qty": t["Quantity"], "price": t["Price"], "date": t["Trade Date"]})
        elif t["Action"] == "Sell":
            qty_to_match = t["Quantity"]
            sell_price = t["Price"]
            sell_date = t["Trade Date"]
            while qty_to_match > 0 and lots:
                lot = lots[0]
                matched_qty = min(qty_to_match, lot["qty"])
                pnl = (sell_price - lot["price"]) * matched_qty
                holding_days = (
                    datetime.fromisoformat(sell_date) - datetime.fromisoformat(lot["date"])
                ).days
                results.append(
                    {
                        "Symbol": t["Symbol"],
                        "Buy Date": lot["date"],
                        "Sell Date": sell_date,
                        "Buy Price": lot["price"],
                        "Sell Price": sell_price,
                        "Quantity": matched_qty,
                        "PnL": pnl,
                        "Holding Days": holding_days,
                    }
                )
                lot["qty"] -= matched_qty
                qty_to_match -= matched_qty
                if lot["qty"] == 0:
                    lots.pop(0)
    return results


def performance_row_exists(perf, debug=False):
    """Check if a performance row with the same Symbol, Buy Date, Sell Date, Quantity exists."""
    url = f"https://api.notion.com/v1/databases/{PERFORMANCE_DATABASE_ID}/query"
    filter_obj = {
        "and": [
            {"property": "Symbol", "title": {"equals": perf["Symbol"]}},
            {"property": "Buy Date", "date": {"equals": perf["Buy Date"]}},
            {"property": "Sell Date", "date": {"equals": perf["Sell Date"]}},
            {"property": "Quantity", "number": {"equals": perf["Quantity"]}},
        ]
    }
    payload = {"filter": filter_obj, "page_size": 1}
    resp = requests.post(url, headers=HEADERS, json=payload)
    if debug:
        print(f"[DEBUG] performance_row_exists response: {resp.status_code} {resp.text}")
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        return len(results) > 0
    return False


def upsert_performance_row(perf, debug=False):
    """Add or update a row in the PERFORMANCE table for a realized trade, skipping if duplicate."""
    if performance_row_exists(perf, debug=debug):
        if debug:
            print(f"[SKIP] Duplicate performance row found, skipping: {perf}")
        return False
    url = "https://api.notion.com/v1/pages"
    properties = {
        "Symbol": {"title": [{"text": {"content": perf["Symbol"]}}]},
        "Buy Date": {"date": {"start": perf["Buy Date"]}},
        "Sell Date": {"date": {"start": perf["Sell Date"]}},
        "Buy Price": {"number": perf["Buy Price"]},
        "Sell Price": {"number": perf["Sell Price"]},
        "Quantity": {"number": perf["Quantity"]},
        "PnL": {"number": perf["PnL"]},
        "Holding Days": {"number": perf["Holding Days"]},
    }
    payload = {"parent": {"database_id": PERFORMANCE_DATABASE_ID}, "properties": properties}
    resp = requests.post(url, headers=HEADERS, json=payload)
    print(f"[DEBUG] upsert_performance_row: {resp.status_code} {resp.text}")
    return resp.status_code == 200


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    debug = args.debug
    print("🚀 MarketMan Performance Watcher started.")
    trades = fetch_all_trades()
    print(f"[DEBUG] Fetched {len(trades)} trades from Notion.")
    parsed = [parse_trade(t) for t in trades]
    print(f"[DEBUG] Parsed {len(parsed)} trades.")
    grouped = aggregate_trades(parsed)
    print(f"[DEBUG] Found {len(grouped)} symbols: {list(grouped.keys())}")
    for symbol, trades in grouped.items():
        print(f"[DEBUG] Processing symbol: {symbol} with {len(trades)} trades.")
        perf_rows = compute_performance_for_symbol(trades)
        print(f"[DEBUG] Generated {len(perf_rows)} performance rows for {symbol}.")
        for perf in perf_rows:
            print(f"[DEBUG] Performance row: {perf}")
            upsert_performance_row(perf, debug=debug)
    print("[SUCCESS] Performance table updated.")


if __name__ == "__main__":
    main()
