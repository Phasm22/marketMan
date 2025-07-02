"""
Market Data Handler - ETF price fetching and market data management
"""
import yfinance as yf
import time
import random
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from src.core.utils.config_loader import get_config

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
    """Fetch current ETF prices for market snapshot with improved rate limiting and error handling.
    Returns: (prices: dict, used_fallback: bool, fallback_reason: str or None)
    """
    if etf_symbols is None:
        etf_symbols = MAJOR_ETFS

    # Load config for random delays
    config = get_config().config if callable(get_config) else {}
    random_delay_cfg = config.get('random_delay', {})
    price_fetch_min, price_fetch_max = random_delay_cfg.get('price_fetch', [1.0, 2.0])
    retry_min, retry_max = random_delay_cfg.get('retry', [2.0, 4.0])
    rate_limit_min, rate_limit_max = random_delay_cfg.get('rate_limit', [5.0, 10.0])

    try:
        prices = {}
        failed_symbols = []
        split_adjustments = {}  # Track split adjustments for price anchors

        logger.info(f"💰 Fetching real-time prices for {len(etf_symbols)} ETFs...")

        for i, symbol in enumerate(etf_symbols):
            success = False
            
            for attempt in range(max_retries):
                try:
                    # Add random delay to avoid rate limits
                    if rate_limit and i > 0:
                        delay = random.uniform(price_fetch_min, price_fetch_max)
                        time.sleep(delay)

                    ticker = yf.Ticker(symbol)

                    # Check for corporate actions (splits) first
                    split_factor = check_corporate_actions(ticker, symbol)
                    if split_factor != 1.0:
                        split_adjustments[symbol] = split_factor
                        logger.info(f"🔄 Detected split for {symbol}: {split_factor}x adjustment factor")

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

                        # Apply split adjustment if needed
                        if split_factor != 1.0:
                            prev_close *= split_factor
                            current_price *= split_factor
                            logger.info(f"🔄 Applied {split_factor}x split adjustment to {symbol} prices")

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
                            "split_factor": split_factor,  # Include split factor in price data
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
                            time.sleep(random.uniform(retry_min, retry_max))  # Wait before retry
                        continue

                except requests.exceptions.HTTPError as e:
                    if "429" in str(e):  # Rate limit error
                        logger.warning(f"⚠️ Rate limited for {symbol}, attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            time.sleep(random.uniform(rate_limit_min, rate_limit_max))  # Longer wait for rate limits
                        continue
                    else:
                        logger.warning(f"⚠️ HTTP error for {symbol}: {str(e)[:100]}...")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Error fetching price for {symbol}: {str(e)[:100]}...")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(retry_min, retry_max))
                    continue
            
            if not success:
                failed_symbols.append(symbol)

        # Log summary
        success_count = len(prices)
        total_count = len(etf_symbols)
        logger.info(f"✅ Successfully fetched prices for {success_count}/{total_count} ETFs")
        
        if failed_symbols:
            logger.warning(f"⚠️ Failed to fetch prices for: {', '.join(failed_symbols[:5])}{'...' if len(failed_symbols) > 5 else ''}")
        
        # Log split adjustments summary
        if split_adjustments:
            logger.info(f"🔄 Split adjustments applied: {split_adjustments}")
        
        # If we have very few successful fetches, use fallback mock data
        if success_count < 3:
            reason = "Too few successful price fetches, using fallback mock data"
            logger.warning(f"⚠️ {reason}")
            return _get_fallback_mock_data(etf_symbols, config), True, reason
            
        return prices, False, None

    except ImportError:
        reason = "yfinance not installed, using fallback mock data"
        logger.warning(f"⚠️ {reason}")
        return _get_fallback_mock_data(etf_symbols, config), True, reason
    except Exception as e:
        reason = f"Error fetching ETF prices: {e}, using fallback mock data"
        logger.warning(f"⚠️ {reason}")
        return _get_fallback_mock_data(etf_symbols, config), True, reason


def check_corporate_actions(ticker, symbol):
    """
    Check for corporate actions (splits) and return adjustment factor.
    Returns 1.0 if no split, or the split factor (e.g., 2.0 for 2:1 split).
    Uses ticker.splits (preferred) or ticker.actions (fallback).
    """
    try:
        today = datetime.now()
        split_factor = 1.0
        found_split = False

        # --- Preferred: Use ticker.splits (pandas Series) ---
        splits = getattr(ticker, 'splits', None)
        if splits is not None and not splits.empty:
            # Check for splits in the last 5 days
            for split_date, ratio in splits.items():
                if ratio != 1.0:
                    if isinstance(split_date, str):
                        split_date_dt = datetime.strptime(split_date, '%Y-%m-%d')
                    else:
                        split_date_dt = split_date.to_pydatetime() if hasattr(split_date, 'to_pydatetime') else split_date
                    if (today - split_date_dt).days <= 5:
                        split_factor = ratio
                        found_split = True
                        logger.info(f"🔄 Found recent split for {symbol} on {split_date_dt.date()}: {ratio}x")
                        # Log event
                        log_corporate_action_event(symbol, {'date': str(split_date_dt.date()), 'ratio': ratio}, split_factor)
                        break

        # --- Fallback: Use ticker.actions (DataFrame) ---
        if not found_split:
            actions = getattr(ticker, 'actions', None)
            if actions is not None and not actions.empty and 'splitRatio' in actions.columns:
                for action_date, row in actions.iterrows():
                    split_ratio = row.get('splitRatio', 1.0)
                    if split_ratio != 1.0:
                        if isinstance(action_date, str):
                            action_date_dt = datetime.strptime(action_date, '%Y-%m-%d')
                        else:
                            action_date_dt = action_date.to_pydatetime() if hasattr(action_date, 'to_pydatetime') else action_date
                        if (today - action_date_dt).days <= 5:
                            split_factor = split_ratio
                            found_split = True
                            logger.info(f"🔄 Found recent split for {symbol} in actions on {action_date_dt.date()}: {split_ratio}x")
                            log_corporate_action_event(symbol, {'date': str(action_date_dt.date()), 'ratio': split_ratio}, split_factor)
                            break

        return split_factor
    except Exception as e:
        logger.warning(f"⚠️ Error checking corporate actions for {symbol}: {e}")
        return 1.0


def log_corporate_action_event(symbol, event_data, split_factor):
    """
    Log raw yfinance corporate action events for verification and debugging.
    Logs events for 5 days around the split to verify consistency.
    """
    try:
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Create corporate actions log file
        log_file = logs_dir / "corporate_actions.log"
        
        # Prepare log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "split_factor": split_factor,
            "event_data": event_data.to_dict() if hasattr(event_data, 'to_dict') else str(event_data),
            "event_type": "stock_split",
            "verification_period": "5_days_around_split"
        }
        
        # Append to log file
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        logger.info(f"📝 Logged corporate action event for {symbol} to {log_file}")
        
    except Exception as e:
        logger.error(f"❌ Error logging corporate action event for {symbol}: {e}")


def adjust_price_anchors_for_splits(price_anchors, split_adjustments):
    """
    Automatically adjust price anchor fields with split factors.
    This function should be called when processing price anchors for signals.
    """
    if not split_adjustments:
        return price_anchors
    
    adjusted_anchors = price_anchors.copy()
    
    for symbol, split_factor in split_adjustments.items():
        if symbol in adjusted_anchors:
            # Adjust all price-related fields
            for field in ['prev_close', 'pre_market', 'current_price']:
                if field in adjusted_anchors[symbol]:
                    original_value = adjusted_anchors[symbol][field]
                    adjusted_value = original_value * split_factor
                    adjusted_anchors[symbol][field] = round(adjusted_value, 2)
                    logger.info(f"🔄 Adjusted {symbol} {field}: {original_value} -> {adjusted_value} (split factor: {split_factor})")
            
            # Add split factor to the anchor data for reference
            adjusted_anchors[symbol]['split_factor'] = split_factor
    
    return adjusted_anchors


def _get_fallback_mock_data(etf_symbols, config=None):
    """Provide fallback mock data when real market data is unavailable"""
    logger.info("🔄 Using fallback mock market data")
    if config is None:
        config = get_config().config if callable(get_config) else {}
    fallback_cfg = config.get('fallback_data', {})
    price_min, price_max = fallback_cfg.get('price_range', [50, 150])
    change_min, change_max = fallback_cfg.get('change_pct_range', [-5, 5])
    volume_min, volume_max = fallback_cfg.get('volume_range', [500000, 1500000])

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
            # Generate reasonable mock data for unknown symbols using config-driven ranges
            fallback_prices[symbol] = {
                "price": round(random.uniform(price_min, price_max), 2),
                "change_pct": round(random.uniform(change_min, change_max), 2),
                "name": f"{symbol} ETF",
                "volume": int(random.uniform(volume_min, volume_max)),
            }
    
    logger.info(f"✅ Generated fallback data for {len(fallback_prices)} ETFs")
    return fallback_prices


def get_market_snapshot():
    """Get a comprehensive market snapshot with current ETF prices, returns (prices, used_fallback, fallback_reason)"""
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
