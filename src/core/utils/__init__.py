"""
Shared utilities module for MarketMan.

This module contains all shared helper functions and utilities including:
- Common data processing functions
- Formatting utilities
- Validation helpers
- Shared constants and configurations
"""

from .config_loader import ConfigLoader, get_config, get_setting, is_feature_enabled
from .formatting import (
    format_price_context,
    format_volume_with_liquidity,
    format_conviction_tier,
    format_signal_summary,
    format_percentage,
    format_currency,
    format_timestamp,
    truncate_text,
    clean_text,
    format_list,
    format_table,
)
from .validation import (
    validate_email,
    validate_symbol,
    validate_percentage,
    validate_confidence_score,
    validate_date_format,
    validate_required_fields,
    validate_numeric_range,
    validate_list_length,
    validate_url,
    validate_json_string,
    sanitize_filename,
    validate_config_section,
    validate_signal_data,
    validate_alert_data,
)

__all__ = [
    # Config utilities
    "ConfigLoader",
    "get_config",
    "get_setting",
    "is_feature_enabled",
    # Formatting utilities
    "format_price_context",
    "format_volume_with_liquidity",
    "format_conviction_tier",
    "format_signal_summary",
    "format_percentage",
    "format_currency",
    "format_timestamp",
    "truncate_text",
    "clean_text",
    "format_list",
    "format_table",
    # Validation utilities
    "validate_email",
    "validate_symbol",
    "validate_percentage",
    "validate_confidence_score",
    "validate_date_format",
    "validate_required_fields",
    "validate_numeric_range",
    "validate_list_length",
    "validate_url",
    "validate_json_string",
    "sanitize_filename",
    "validate_config_section",
    "validate_signal_data",
    "validate_alert_data",
]
