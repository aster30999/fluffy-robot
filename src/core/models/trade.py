"""
Core Domain Models for Trade and Decision.

This module implements immutable domain models for the trading bot's trade
execution and decision making, following Clean Architecture principles.

Architecture Decisions:
    AD-001: Clean Architecture Paradigm - Domain layer entities
    AD-004: Dependency Injection Pattern - All classes accept dependencies via constructors

All dataclasses are immutable (frozen=True) to ensure thread-safety and
prevent accidental mutations when passing data between components.

Dependencies:
    - Token, TokenPair, Price models from src.core.models.price (US-010)
    - Portfolio model from src.core.models.balance (US-011) - forward reference
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .balance import Portfolio
    from .price import Price, TokenPair


class TradeStatus(Enum):
    """Status of a trade execution.

    Represents the current state of a trade in its lifecycle.

    Attributes:
        PENDING: Trade has been submitted but not yet executed.
        SUCCESS: Trade executed successfully.
        FAILED: Trade execution failed.
    """
    PENDING = auto()
    SUCCESS = auto()
    FAILED = auto()


class TradeType(Enum):
    """Type of trade action.

    Represents the kind of trading operation to be performed.

    Attributes:
        BUY: Buy operation - adds to portfolio (amount is positive).
        SELL: Sell operation - removes from portfolio (amount is positive, direction indicated separately).
        SWAP: Swap between two tokens.
    """
    BUY = auto()
    SELL = auto()
    SWAP = auto()


class Signal(Enum):
    """Trading signal for decisions.

    Represents the recommendation from a trading strategy.

    Attributes:
        BUY: Strong buy signal - recommendation to purchase.
        SELL: Strong sell signal - recommendation to sell.
        NEUTRAL: No strong signal - recommendation to hold current position.
    """
    BUY = auto()
    SELL = auto()
    NEUTRAL = auto()


@dataclass(frozen=True)
class Trade:
    """Immutable representation of a trade execution.

    Contains all details needed to execute and track a trade.
    This is a core domain model used throughout the trading system.

    Attributes:
        trade_id: Unique identifier for the trade (UUID or similar).
        token_pair: The trading pair (from US-010).
        amount: The amount to trade, in base token units.
                For BUY: positive amount to add to portfolio.
                For SELL: positive amount to remove from portfolio.
                For SWAP: positive amount of base token to swap.
        trade_type: The type of trade operation (BUY, SELL, SWAP).
        price: The execution price per unit of base token (from US-010).
        timestamp: When the trade was created/initiated.
        status: Current status of the trade. Defaults to PENDING.
        fees: Transaction fees paid, in quote token units. Defaults to 0.0.
        slippage: Price slippage percentage from expected price. Defaults to 0.0.
        notes: Additional notes or metadata. Defaults to empty string.
    """
    trade_id: str
    token_pair: "TokenPair"
    amount: float
    trade_type: TradeType
    price: "Price"
    timestamp: datetime
    status: TradeStatus = TradeStatus.PENDING
    fees: float = 0.0
    slippage: float = 0.0
    notes: str = ""

    @property
    def base_amount(self) -> float:
        """Get the amount in base token units.

        Returns:
            The amount value as-is (in base token units).
        """
        return self.amount

    @property
    def quote_amount(self) -> float:
        """Calculate the equivalent amount in quote token units.

        For a trade of `amount` base tokens at `price` per base token,
        the quote amount is amount * price.

        Returns:
            The equivalent value in quote token units.
        """
        return self.amount * self.price.value

    @property
    def total_cost(self) -> float:
        """Calculate the total cost including fees.

        For BUY trades: quote_amount + fees
        For SELL trades: quote_amount - fees (assuming fees deducted from proceeds)
        For SWAP trades: quote_amount + fees

        Returns:
            The total cost including fees in quote token units.
        """
        if self.trade_type == TradeType.SELL:
            return self.quote_amount - self.fees
        return self.quote_amount + self.fees

    def to_dict(self) -> dict:
        """Convert Trade instance to dictionary representation.

        Returns:
            Dictionary with all Trade attributes, including nested serialization.
        """
        return {
            "trade_id": self.trade_id,
            "token_pair": self.token_pair.to_dict(),
            "amount": self.amount,
            "trade_type": self.trade_type.name,
            "price": self.price.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.name,
            "fees": self.fees,
            "slippage": self.slippage,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trade":
        """Create Trade instance from dictionary.

        Args:
            data: Dictionary containing Trade attributes.
                  'token_pair' and 'price' should be dicts that can be deserialized.
                  'trade_type' and 'status' should be strings matching enum names.

        Returns:
            Trade instance.

        Raises:
            KeyError: If required fields are missing.
            ValueError: If enum values are invalid.
        """
        from .price import Price, TokenPair

        # Convert string to enum
        trade_type = TradeType[data["trade_type"]]
        status = TradeStatus[data["status"]]

        timestamp = data["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            trade_id=data["trade_id"],
            token_pair=TokenPair.from_dict(data["token_pair"]),
            amount=data["amount"],
            trade_type=trade_type,
            price=Price.from_dict(data["price"]),
            timestamp=timestamp,
            status=status,
            fees=data.get("fees", 0.0),
            slippage=data.get("slippage", 0.0),
            notes=data.get("notes", ""),
        )


@dataclass(frozen=True)
class Decision:
    """Immutable representation of a trading decision.

    Represents the result of a trading strategy's analysis.
    Contains the signal, confidence level, and related market data.
    This is a core domain model used by the decision engine.

    Attributes:
        decision_id: Unique identifier for the decision (UUID or similar).
        token_pair: The trading pair this decision pertains to (from US-010).
        signal: The trading signal recommendation (BUY, SELL, NEUTRAL).
        confidence: Confidence level in the decision (0.0 to 1.0).
                    0.0 = no confidence, 1.0 = certain.
        timestamp: When the decision was generated.
        reasoning: Human-readable explanation of the decision. Defaults to empty string.
        indicators: Dictionary of indicator values that led to this decision.
                    Keys are indicator names (e.g., "RSI", "MACD"), values are indicator data.
                    Defaults to empty dict.
        portfolio_snapshot: Optional snapshot of portfolio state at decision time.
                          This allows replaying decisions with historical context.
                          Defaults to None.
    """
    decision_id: str
    token_pair: "TokenPair"
    signal: Signal
    confidence: float
    timestamp: datetime
    reasoning: str = ""
    indicators: Dict[str, Any] = field(default_factory=dict)
    portfolio_snapshot: Optional["Portfolio"] = None

    def __post_init__(self):
        """Validate confidence is between 0.0 and 1.0."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

    @property
    def is_actionable(self) -> bool:
        """Check if this decision recommends taking action.

        A decision is actionable if the signal is BUY or SELL.
        NEUTRAL signals are not actionable (hold position).

        Returns:
            True if signal is BUY or SELL, False if NEUTRAL.
        """
        return self.signal in (Signal.BUY, Signal.SELL)

    @property
    def is_strong(self) -> bool:
        """Check if this decision has high confidence.

        A decision is considered strong if confidence >= 0.7.

        Returns:
            True if confidence >= 0.7, False otherwise.
        """
        return self.confidence >= 0.7

    def to_dict(self) -> dict:
        """Convert Decision instance to dictionary representation.

        Returns:
            Dictionary with all Decision attributes, including nested serialization.
        """
        result = {
            "decision_id": self.decision_id,
            "token_pair": self.token_pair.to_dict(),
            "signal": self.signal.name,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "reasoning": self.reasoning,
            "indicators": self.indicators,
            "portfolio_snapshot": None if self.portfolio_snapshot is None else self.portfolio_snapshot.to_dict(),
        }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Decision":
        """Create Decision instance from dictionary.

        Args:
            data: Dictionary containing Decision attributes.
                  'token_pair' should be a dict that can be deserialized.
                  'signal' should be a string matching Signal enum names.
                  'portfolio_snapshot' is optional and may be None or a dict.

        Returns:
            Decision instance.

        Raises:
            KeyError: If required fields are missing.
            ValueError: If confidence is out of range or enum values are invalid.
        """
        from .price import TokenPair

        # Convert string to enum
        signal = Signal[data["signal"]]

        timestamp = data["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        portfolio_snapshot = data.get("portfolio_snapshot")
        if portfolio_snapshot is not None:
            from .balance import Portfolio
            portfolio_snapshot = Portfolio.from_dict(portfolio_snapshot)

        return cls(
            decision_id=data["decision_id"],
            token_pair=TokenPair.from_dict(data["token_pair"]),
            signal=signal,
            confidence=data["confidence"],
            timestamp=timestamp,
            reasoning=data.get("reasoning", ""),
            indicators=data.get("indicators", {}),
            portfolio_snapshot=portfolio_snapshot,
        )
