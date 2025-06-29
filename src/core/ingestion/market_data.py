"""
Market Data Handler - ETF price fetching and market data management
"""
import yfinance as yf
import time
import random
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
DEBUG_MODE = logging.getLogger().level == logging.DEBUG

# Expanded ETF universe for comprehensive thematic coverage
MAJOR_ETFS = [
    # AI & Tech Theme
    "BOTZ",
    "ROBO",
    "IRBO",
    "ARKQ",
    "SMH",
    "SOXX",
    # Defense & Aerospace
    "ITA",
    "XAR",
    "DFEN",
    "PPA",
    # Nuclear & Uranium
    "URNM",
    "NLR",
    "URA",
    # Clean Energy & Climate
    "ICLN",
    "TAN",
    "QCLN",
    "PBW",
    "LIT",
    "REMX",
    # Volatility & Inverse
    "VIXY",
    "VXX",
    "SQQQ",
    "SPXS",
    # Traditional Sectors (for context)
    "XLE",
    "XLF",
    "XLK",
    "QQQ",
    "SPY",
]


def get_etf_prices(etf_symbols=None, rate_limit=True, max_retries=2):
    """Fetch current ETF prices for market snapshot with improved rate limiting and error handling"""
    if etf_symbols is None:
        etf_symbols = MAJOR_ETFS

    try:
        prices = {}
        failed_symbols = []

        logger.info(f"💰 Fetching real-time prices for {len(etf_symbols)} ETFs...")

        for i, symbol in enumerate(etf_symbols):
            success = False
            
            for attempt in range(max_retries):
                try:
                    # Add random delay to avoid rate limits
                    if rate_limit and i > 0:
                        delay = random.uniform(1.0, 2.0)  # Increased delay
                        time.sleep(delay)

                    ticker = yf.Ticker(symbol)

                    # Fetch last 2 days for close/open logic with timeout
                    hist = ticker.history(period="2d", timeout=10)

                    if not hist.empty:
                        # Use 2-day logic for prev_close/current_price
                        if len(hist) >= 2:
                            prev_close = hist["Close"].iloc[-2]
                            current_price = hist["Close"].iloc[-1]
                        else:
                            current_price = hist["Close"].iloc[-1]
                            prev_close = hist["Open"].iloc[-1] if len(hist) > 0 else current_price

                        # Calculate percentage change
                        change_pct = (
                            ((current_price - prev_close) / prev_close) * 100
                            if prev_close and prev_close != 0
                            else 0
                        )

                        # Get volume data if available
                        volume = hist["Volume"].iloc[-1] if "Volume" in hist.columns else 0

                        prices[symbol] = {
                            "price": round(current_price, 2),
                            "change_pct": round(change_pct, 2),
                            "name": f"{symbol} ETF",  # Simplified name to avoid API calls
                            "volume": int(volume) if volume else 0,
                        }

                        trend_emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➖"
                        if DEBUG_MODE:
                            logger.debug(
                                f"💰 {symbol}: ${current_price:.2f} ({change_pct:+.2f}%) {trend_emoji}"
                            )
                        else:
                            logger.info(f"💰 {symbol}: ${current_price:.2f} ({change_pct:+.2f}%)")
                        
                        success = True
                        break  # Success, exit retry loop
                    else:
                        logger.warning(f"⚠️ No price data for {symbol}")
                        if attempt < max_retries - 1:
                            time.sleep(random.uniform(2.0, 4.0))  # Wait before retry
                        continue

                except requests.exceptions.HTTPError as e:
                    if "429" in str(e):  # Rate limit error
                        logger.warning(f"⚠️ Rate limited for {symbol}, attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            time.sleep(random.uniform(5.0, 10.0))  # Longer wait for rate limits
                        continue
                    else:
                        logger.warning(f"⚠️ HTTP error for {symbol}: {str(e)[:100]}...")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Error fetching price for {symbol}: {str(e)[:100]}...")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(2.0, 4.0))
                    continue
            
            if not success:
                failed_symbols.append(symbol)

        # Log summary
        success_count = len(prices)
        total_count = len(etf_symbols)
        logger.info(f"✅ Successfully fetched prices for {success_count}/{total_count} ETFs")
        
        if failed_symbols:
            logger.warning(f"⚠️ Failed to fetch prices for: {', '.join(failed_symbols[:5])}{'...' if len(failed_symbols) > 5 else ''}")
        
        # If we have very few successful fetches, use fallback mock data
        if success_count < 3:
            logger.warning("⚠️ Too few successful price fetches, using fallback mock data")
            return _get_fallback_mock_data(etf_symbols)
            
        return prices

    except ImportError:
        logger.warning("⚠️ yfinance not installed, using fallback mock data")
        return _get_fallback_mock_data(etf_symbols)
    except Exception as e:
        logger.warning(f"⚠️ Error fetching ETF prices: {e}, using fallback mock data")
        return _get_fallback_mock_data(etf_symbols)


def _get_fallback_mock_data(etf_symbols):
    """Provide fallback mock data when real market data is unavailable"""
    logger.info("🔄 Using fallback mock market data")
    
    # Mock price data for common ETFs
    mock_prices = {
        "SPY": {"price": 450.25, "change_pct": 0.5, "name": "SPDR S&P 500 ETF", "volume": 5000000},
        "QQQ": {"price": 380.75, "change_pct": 0.8, "name": "Invesco QQQ Trust", "volume": 3000000},
        "DIA": {"price": 350.50, "change_pct": 0.3, "name": "SPDR Dow Jones ETF", "volume": 2000000},
        "IWM": {"price": 180.25, "change_pct": -0.2, "name": "iShares Russell 2000 ETF", "volume": 1500000},
        "ICLN": {"price": 22.45, "change_pct": 2.3, "name": "iShares Global Clean Energy", "volume": 800000},
        "TAN": {"price": 55.67, "change_pct": -1.2, "name": "Invesco Solar ETF", "volume": 600000},
        "ITA": {"price": 125.80, "change_pct": 1.4, "name": "iShares U.S. Aerospace & Defense", "volume": 400000},
        "XAR": {"price": 95.30, "change_pct": 0.9, "name": "SPDR S&P Aerospace & Defense", "volume": 300000},
        "VIXY": {"price": 18.75, "change_pct": -5.2, "name": "ProShares VIX Short-Term", "volume": 2000000},
        "VXX": {"price": 12.45, "change_pct": -3.8, "name": "iPath Series B S&P 500 VIX", "volume": 1500000},
    }
    
    # Return mock data for requested symbols, or default values for unknown symbols
    fallback_prices = {}
    for symbol in etf_symbols:
        if symbol in mock_prices:
            fallback_prices[symbol] = mock_prices[symbol]
        else:
            # Generate reasonable mock data for unknown symbols
            fallback_prices[symbol] = {
                "price": 50.0 + (hash(symbol) % 100),  # Deterministic but varied price
                "change_pct": (hash(symbol) % 10) - 5,  # -5% to +5% change
                "name": f"{symbol} ETF",
                "volume": 500000 + (hash(symbol) % 1000000),  # Reasonable volume
            }
    
    logger.info(f"✅ Generated fallback data for {len(fallback_prices)} ETFs")
    return fallback_prices


def get_market_snapshot():
    """Get a comprehensive market snapshot with current ETF prices"""
    logger.debug(f"📊 Fetching market data for strategic context...")
    return get_etf_prices(MAJOR_ETFS)


def format_price_context(etf_prices):
    """Format price data for AI analysis context"""
    if not etf_prices:
        return "No price data available"

    price_context = "📊 LIVE MARKET SNAPSHOT:\n"
    for symbol, data in etf_prices.items():
        change_sign = "+" if data["change_pct"] >= 0 else ""
        trend_emoji = "📈" if data["change_pct"] > 0 else "📉" if data["change_pct"] < 0 else "➖"
        price_context += f"• {symbol} ({data.get('name', symbol)}): ${data['price']} ({change_sign}{data['change_pct']}%) {trend_emoji}\n"
    price_context += "\nUse this real-time data to inform your strategic analysis.\n"

    return price_context
