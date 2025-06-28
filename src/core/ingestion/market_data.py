"""
Market Data Handler - ETF price fetching and market data management
"""
import yfinance as yf
import time
import random
import logging

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


def get_etf_prices(etf_symbols=None, rate_limit=True):
    """Fetch current ETF prices for market snapshot with rate limiting"""
    if etf_symbols is None:
        etf_symbols = MAJOR_ETFS

    try:
        prices = {}

        logger.info(f"💰 Fetching real-time prices for {len(etf_symbols)} ETFs...")

        for i, symbol in enumerate(etf_symbols):
            try:
                # Add random delay to avoid rate limits
                if rate_limit and i > 0:
                    delay = random.uniform(0.5, 1.5)
                    time.sleep(delay)

                ticker = yf.Ticker(symbol)

                # Fetch last 2 days for close/open logic
                hist = ticker.history(period="2d")

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
                else:
                    logger.warning(f"⚠️ No price data for {symbol}")

            except Exception as e:
                if DEBUG_MODE:
                    logger.warning(f"⚠️ Error fetching price for {symbol}: {str(e)[:100]}...")
                continue  # Continue with next symbol

        logger.info(f"✅ Successfully fetched prices for {len(prices)}/{len(etf_symbols)} ETFs")
        return prices

    except ImportError:
        logger.warning("⚠️ yfinance not installed, skipping price data")
        return {}
    except Exception as e:
        logger.warning(f"⚠️ Error fetching ETF prices: {e}")
        return {}


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
