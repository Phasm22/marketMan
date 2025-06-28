"""
Validation utilities for MarketMan.

This module contains common validation functions used across the codebase
to ensure data integrity and proper input validation.
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_symbol(symbol: str) -> bool:
    """
    Validate stock/ETF symbol format.

    Args:
        symbol: Symbol to validate

    Returns:
        True if valid, False otherwise
    """
    if not symbol:
        return False

    # Basic symbol validation: 1-5 uppercase letters
    pattern = r"^[A-Z]{1,5}$"
    return bool(re.match(pattern, symbol))


def validate_percentage(value: Union[int, float]) -> bool:
    """
    Validate percentage value.

    Args:
        value: Percentage value to validate

    Returns:
        True if valid (0-100), False otherwise
    """
    try:
        float_value = float(value)
        return 0 <= float_value <= 100
    except (ValueError, TypeError):
        return False


def validate_confidence_score(score: Union[int, float]) -> bool:
    """
    Validate confidence score.

    Args:
        score: Confidence score to validate

    Returns:
        True if valid (0-10), False otherwise
    """
    try:
        float_score = float(score)
        return 0 <= float_score <= 10
    except (ValueError, TypeError):
        return False


def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """
    Validate date string format.

    Args:
        date_str: Date string to validate
        format_str: Expected date format

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that required fields are present in data.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        List of missing field names (empty if all present)
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    return missing_fields


def validate_numeric_range(value: Union[int, float], min_val: float, max_val: float) -> bool:
    """
    Validate that a numeric value is within a range.

    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        True if valid, False otherwise
    """
    try:
        float_value = float(value)
        return min_val <= float_value <= max_val
    except (ValueError, TypeError):
        return False


def validate_list_length(
    items: List[Any], min_length: int = 0, max_length: Optional[int] = None
) -> bool:
    """
    Validate list length.

    Args:
        items: List to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length (None for no limit)

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(items, list):
        return False

    if len(items) < min_length:
        return False

    if max_length is not None and len(items) > max_length:
        return False

    return True


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False

    # Basic URL validation
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def validate_json_string(json_str: str) -> bool:
    """
    Validate JSON string format.

    Args:
        json_str: JSON string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        import json

        json.loads(json_str)
        return True
    except (ValueError, TypeError):
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip(". ")

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def validate_config_section(
    config: Dict[str, Any], section: str, required_keys: List[str]
) -> List[str]:
    """
    Validate a configuration section.

    Args:
        config: Configuration dictionary
        section: Section name to validate
        required_keys: List of required keys in the section

    Returns:
        List of missing keys (empty if all present)
    """
    if section not in config:
        return required_keys

    section_data = config[section]
    if not isinstance(section_data, dict):
        return required_keys

    return validate_required_fields(section_data, required_keys)


def validate_signal_data(signal_data: Dict[str, Any]) -> List[str]:
    """
    Validate signal data structure.

    Args:
        signal_data: Signal data to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Required fields
    required_fields = ["signal", "confidence", "etfs", "reasoning"]
    missing_fields = validate_required_fields(signal_data, required_fields)
    errors.extend([f"Missing required field: {field}" for field in missing_fields])

    # Validate signal type
    if "signal" in signal_data:
        valid_signals = ["Bullish", "Bearish", "Neutral"]
        if signal_data["signal"] not in valid_signals:
            errors.append(f"Invalid signal type: {signal_data['signal']}")

    # Validate confidence score
    if "confidence" in signal_data:
        if not validate_confidence_score(signal_data["confidence"]):
            errors.append(f"Invalid confidence score: {signal_data['confidence']}")

    # Validate ETFs list
    if "etfs" in signal_data:
        if not isinstance(signal_data["etfs"], list):
            errors.append("ETFs must be a list")
        elif not validate_list_length(signal_data["etfs"], min_length=1):
            errors.append("ETFs list cannot be empty")
        else:
            for etf in signal_data["etfs"]:
                if not validate_symbol(etf):
                    errors.append(f"Invalid ETF symbol: {etf}")

    return errors


def validate_alert_data(alert_data: Dict[str, Any]) -> List[str]:
    """
    Validate alert data structure.

    Args:
        alert_data: Alert data to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Required fields
    required_fields = ["signal", "confidence", "title", "reasoning", "etfs"]
    missing_fields = validate_required_fields(alert_data, required_fields)
    errors.extend([f"Missing required field: {field}" for field in missing_fields])

    # Validate confidence score
    if "confidence" in alert_data:
        if not validate_confidence_score(alert_data["confidence"]):
            errors.append(f"Invalid confidence score: {alert_data['confidence']}")

    # Validate title length
    if "title" in alert_data:
        if len(alert_data["title"]) > 500:
            errors.append("Title too long (max 500 characters)")

    # Validate reasoning length
    if "reasoning" in alert_data:
        if len(alert_data["reasoning"]) > 2000:
            errors.append("Reasoning too long (max 2000 characters)")

    return errors
