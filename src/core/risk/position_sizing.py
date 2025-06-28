"""
Position sizing module for MarketMan.

This module implements various position sizing strategies including:
- Kelly Criterion
- Fixed percentage
- Risk-based sizing
- Volatility-adjusted sizing
"""

import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from src.core.utils import get_config


logger = logging.getLogger(__name__)


@dataclass
class PositionSizeResult:
    """Result of position sizing calculation."""

    quantity: int
    dollar_amount: float
    risk_amount: float
    method: str
    confidence: float


class PositionSizer:
    """
    Position sizing calculator for risk management.

    Implements various position sizing strategies to manage risk
    and optimize position sizes based on account size and risk tolerance.
    """

    def __init__(self):
        """Initialize the position sizer."""
        self.config = get_config()
        self.risk_config = self.config.get_strategy_config("risk_management")
        self.position_config = self.risk_config.get("position_sizing", {})

        # Default values
        self.account_size = 100000  # TODO: Get from broker
        self.max_position_size = self.position_config.get("max_position_size", 10000)
        self.min_position_size = self.position_config.get("min_position_size", 100)
        self.max_kelly_fraction = self.position_config.get("max_kelly_fraction", 0.25)

        logger.info("Initialized position sizer")

    def calculate_kelly_size(
        self, win_rate: float, avg_win: float, avg_loss: float, confidence: float = 1.0
    ) -> PositionSizeResult:
        """
        Calculate position size using Kelly Criterion.

        Args:
            win_rate: Historical win rate (0.0 to 1.0)
            avg_win: Average winning trade amount
            avg_loss: Average losing trade amount
            confidence: Confidence factor (0.0 to 1.0)

        Returns:
            PositionSizeResult with calculated size
        """
        if win_rate <= 0 or win_rate >= 1:
            logger.warning(f"Invalid win rate: {win_rate}")
            return self._create_minimal_result("kelly")

        if avg_win <= 0 or avg_loss <= 0:
            logger.warning("Invalid average win/loss amounts")
            return self._create_minimal_result("kelly")

        # Kelly formula: f = (bp - q) / b
        # where b = odds received, p = probability of win, q = probability of loss
        b = avg_win / avg_loss  # odds received
        p = win_rate
        q = 1 - win_rate

        kelly_fraction = (b * p - q) / b

        # Apply confidence factor and maximum limit
        kelly_fraction *= confidence
        kelly_fraction = min(kelly_fraction, self.max_kelly_fraction)
        kelly_fraction = max(kelly_fraction, 0)

        dollar_amount = self.account_size * kelly_fraction
        quantity = int(dollar_amount / avg_win) if avg_win > 0 else 0

        # Apply limits
        quantity = max(quantity, 1)
        quantity = min(quantity, int(self.max_position_size / avg_win))

        return PositionSizeResult(
            quantity=quantity,
            dollar_amount=quantity * avg_win,
            risk_amount=dollar_amount,
            method="kelly",
            confidence=confidence,
        )

    def calculate_fixed_percentage(
        self, percentage: float, price: float, confidence: float = 1.0
    ) -> PositionSizeResult:
        """
        Calculate position size using fixed percentage of account.

        Args:
            percentage: Percentage of account to risk (0.0 to 1.0)
            price: Price per unit
            confidence: Confidence factor (0.0 to 1.0)

        Returns:
            PositionSizeResult with calculated size
        """
        if percentage <= 0 or percentage > 1:
            logger.warning(f"Invalid percentage: {percentage}")
            return self._create_minimal_result("fixed_percentage")

        if price <= 0:
            logger.warning(f"Invalid price: {price}")
            return self._create_minimal_result("fixed_percentage")

        # Apply confidence factor
        adjusted_percentage = percentage * confidence

        dollar_amount = self.account_size * adjusted_percentage
        quantity = int(dollar_amount / price)

        # Apply limits
        quantity = max(quantity, 1)
        quantity = min(quantity, int(self.max_position_size / price))

        return PositionSizeResult(
            quantity=quantity,
            dollar_amount=quantity * price,
            risk_amount=dollar_amount,
            method="fixed_percentage",
            confidence=confidence,
        )

    def calculate_risk_based_size(
        self, stop_loss_pct: float, max_risk_amount: float, price: float, confidence: float = 1.0
    ) -> PositionSizeResult:
        """
        Calculate position size based on risk amount and stop loss.

        Args:
            stop_loss_pct: Stop loss percentage (0.0 to 1.0)
            max_risk_amount: Maximum dollar amount to risk
            price: Current price per unit
            confidence: Confidence factor (0.0 to 1.0)

        Returns:
            PositionSizeResult with calculated size
        """
        if stop_loss_pct <= 0 or stop_loss_pct >= 1:
            logger.warning(f"Invalid stop loss percentage: {stop_loss_pct}")
            return self._create_minimal_result("risk_based")

        if max_risk_amount <= 0:
            logger.warning(f"Invalid max risk amount: {max_risk_amount}")
            return self._create_minimal_result("risk_based")

        if price <= 0:
            logger.warning(f"Invalid price: {price}")
            return self._create_minimal_result("risk_based")

        # Apply confidence factor
        adjusted_risk = max_risk_amount * confidence

        # Calculate quantity based on risk per unit
        risk_per_unit = price * stop_loss_pct
        quantity = int(adjusted_risk / risk_per_unit)

        # Apply limits
        quantity = max(quantity, 1)
        quantity = min(quantity, int(self.max_position_size / price))

        return PositionSizeResult(
            quantity=quantity,
            dollar_amount=quantity * price,
            risk_amount=adjusted_risk,
            method="risk_based",
            confidence=confidence,
        )

    def calculate_volatility_adjusted_size(
        self, price: float, volatility: float, base_size: float, confidence: float = 1.0
    ) -> PositionSizeResult:
        """
        Calculate position size adjusted for volatility.

        Args:
            price: Current price per unit
            volatility: Volatility measure (0.0 to 1.0)
            base_size: Base position size in dollars
            confidence: Confidence factor (0.0 to 1.0)

        Returns:
            PositionSizeResult with calculated size
        """
        if volatility <= 0:
            logger.warning(f"Invalid volatility: {volatility}")
            return self._create_minimal_result("volatility_adjusted")

        if price <= 0:
            logger.warning(f"Invalid price: {price}")
            return self._create_minimal_result("volatility_adjusted")

        # Adjust size inversely to volatility
        # Higher volatility = smaller position
        volatility_factor = 1.0 / (1.0 + volatility)
        adjusted_size = base_size * volatility_factor * confidence

        quantity = int(adjusted_size / price)

        # Apply limits
        quantity = max(quantity, 1)
        quantity = min(quantity, int(self.max_position_size / price))

        return PositionSizeResult(
            quantity=quantity,
            dollar_amount=quantity * price,
            risk_amount=adjusted_size,
            method="volatility_adjusted",
            confidence=confidence,
        )

    def _create_minimal_result(self, method: str) -> PositionSizeResult:
        """
        Create a minimal position size result.

        Args:
            method: Method used for calculation

        Returns:
            Minimal PositionSizeResult
        """
        return PositionSizeResult(
            quantity=1,
            dollar_amount=self.min_position_size,
            risk_amount=self.min_position_size,
            method=method,
            confidence=0.0,
        )

    def set_account_size(self, account_size: float) -> None:
        """
        Update the account size for calculations.

        Args:
            account_size: New account size
        """
        if account_size > 0:
            self.account_size = account_size
            logger.info(f"Updated account size to: ${account_size:,.2f}")
        else:
            logger.warning(f"Invalid account size: {account_size}")

    def get_position_limits(self) -> Dict[str, float]:
        """
        Get current position sizing limits.

        Returns:
            Dictionary with current limits
        """
        return {
            "account_size": self.account_size,
            "max_position_size": self.max_position_size,
            "min_position_size": self.min_position_size,
            "max_kelly_fraction": self.max_kelly_fraction,
        }
