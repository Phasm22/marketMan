"""
Technicals Module - Fetches or mocks technical indicators for ETFs/tickers
"""
import random

def get_mock_technicals(ticker):
    """Return mock technical indicators for a given ticker"""
    # In production, fetch from Finnhub, Yahoo, etc.
    return {
        "rsi": round(random.uniform(30, 70), 2),
        "macd": round(random.uniform(-2, 2), 2),
        "bollinger": random.choice(["tight", "wide"]),
        "sma_50": round(random.uniform(80, 120), 2),
        "sma_200": round(random.uniform(80, 120), 2),
    }

def get_batch_technicals(tickers):
    """Return a dict of technicals for a list of tickers"""
    return {ticker: get_mock_technicals(ticker) for ticker in tickers} 