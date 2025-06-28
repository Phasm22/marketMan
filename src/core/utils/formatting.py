"""
Formatting utilities for MarketMan.

This module contains common formatting functions used across the codebase
to ensure consistent formatting of data, prices, volumes, and other values.
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime


def format_price_context(etf_prices: Dict[str, Any]) -> str:
    """
    Format ETF price context for display.

    Args:
        etf_prices: Dictionary of ETF price data

    Returns:
        Formatted price context string
    """
    if not etf_prices:
        return "No price data available"

    context_lines = []
    for symbol, data in etf_prices.items():
        change_sign = "+" if data.get("change_pct", 0) >= 0 else ""
        trend_emoji = (
            "📈" if data.get("change_pct", 0) > 0 else "📉" if data.get("change_pct", 0) < 0 else "➖"
        )

        price = data.get("price", 0)
        change_pct = data.get("change_pct", 0)
        name = data.get("name", symbol)

        context_lines.append(
            f"• {symbol} ({name}): ${price:.2f} ({change_sign}{change_pct:.2f}%) {trend_emoji}"
        )

    return "\n".join(context_lines)


def format_volume_with_liquidity(volume: float) -> str:
    """
    Format volume with liquidity indicators.

    Args:
        volume: Volume value

    Returns:
        Formatted volume string with liquidity indicator
    """
    if volume >= 1_000_000_000:  # 1B+
        return f"${volume/1_000_000_000:.1f}B (High)"
    elif volume >= 100_000_000:  # 100M+
        return f"${volume/1_000_000:.0f}M (High)"
    elif volume >= 10_000_000:  # 10M+
        return f"${volume/1_000_000:.1f}M (Medium)"
    elif volume >= 1_000_000:  # 1M+
        return f"${volume/1_000_000:.2f}M (Medium)"
    else:
        return f"${volume:,.0f} (Low)"


def format_conviction_tier(confidence: float) -> str:
    """
    Format confidence level into a conviction tier.

    Args:
        confidence: Confidence score (0-10)

    Returns:
        Formatted conviction tier string
    """
    if confidence >= 9:
        return "🔥 HIGH CONVICTION"
    elif confidence >= 7:
        return "⚡ STRONG SIGNAL"
    elif confidence >= 5:
        return "📊 MODERATE SIGNAL"
    else:
        return "⚠️ WEAK SIGNAL"


def format_signal_summary(signal: str, confidence: float, etfs: List[str], reasoning: str) -> str:
    """
    Format a signal summary for display.

    Args:
        signal: Signal type (Bullish/Bearish/Neutral)
        confidence: Confidence score
        etfs: List of affected ETFs
        reasoning: Signal reasoning

    Returns:
        Formatted signal summary
    """
    signal_emoji = {"Bullish": "↗️", "Bearish": "↘️", "Neutral": "➡️"}.get(signal, "❓")

    conviction = format_conviction_tier(confidence)
    etf_list = ", ".join(etfs[:5]) + ("..." if len(etfs) > 5 else "")

    summary = f"{signal_emoji} {signal.upper()} Signal ({confidence}/10)\n"
    summary += f"{conviction}\n\n"
    summary += f"ETFs: {etf_list}\n\n"
    summary += f"Reasoning: {reasoning[:200]}{'...' if len(reasoning) > 200 else ''}"

    return summary


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Format a value as a percentage.

    Args:
        value: Value to format (0.0 to 1.0)
        decimal_places: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimal_places}f}%"


def format_currency(value: float, currency: str = "$") -> str:
    """
    Format a value as currency.

    Args:
        value: Value to format
        currency: Currency symbol

    Returns:
        Formatted currency string
    """
    if abs(value) >= 1_000_000:
        return f"{currency}{value/1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"{currency}{value/1_000:.1f}K"
    else:
        return f"{currency}{value:.2f}"


def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a timestamp for display.

    Args:
        timestamp: Datetime object
        format_str: Format string

    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime(format_str)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text.strip())

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    return text


def format_list(items: List[str], max_items: int = 5, separator: str = ", ") -> str:
    """
    Format a list of items with truncation.

    Args:
        items: List of items
        max_items: Maximum number of items to show
        separator: Separator between items

    Returns:
        Formatted list string
    """
    if not items:
        return ""

    if len(items) <= max_items:
        return separator.join(items)

    return separator.join(items[:max_items]) + "..."


def format_table(data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
    """
    Format data as a table.

    Args:
        data: List of dictionaries representing rows
        headers: Optional list of header names

    Returns:
        Formatted table string
    """
    if not data:
        return "No data available"

    if not headers:
        headers = list(data[0].keys())

    # Calculate column widths
    col_widths = {}
    for header in headers:
        col_widths[header] = len(header)

    for row in data:
        for header in headers:
            value = str(row.get(header, ""))
            col_widths[header] = max(col_widths[header], len(value))

    # Build table
    lines = []

    # Header
    header_line = "| " + " | ".join(header.ljust(col_widths[header]) for header in headers) + " |"
    lines.append(header_line)

    # Separator
    separator_line = "|" + "|".join("-" * (width + 2) for width in col_widths.values()) + "|"
    lines.append(separator_line)

    # Data rows
    for row in data:
        row_line = (
            "| "
            + " | ".join(str(row.get(header, "")).ljust(col_widths[header]) for header in headers)
            + " |"
        )
        lines.append(row_line)

    return "\n".join(lines)
