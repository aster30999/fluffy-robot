"""
Core Domain Models for Price and Market Data.

This module implements immutable domain models for the trading bot's core
price and market data representation, following Clean Architecture principles.

Architecture Decisions:
    AD-001: Clean Architecture Paradigm - Domain layer entities
    AD-004: Dependency Injection Pattern - All classes accept dependencies via constructors

All dataclasses are immutable (frozen=True) to ensure thread-safety and
prevent accidental mutations when passing data between components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Price:
    """Immutable price representation with timestamp.

    Represents a single price point with its value, timestamp, and optional currency.
    Used throughout the system to pass price information between components.

    Attributes:
        value: The numerical price value (e.g., 150.50 for 150.50 USD).
        timestamp: The datetime when this price was observed/recorded.
        currency: The currency of the price value (default: "USD").
    """
    value: float
    timestamp: datetime
    currency: str = "USD"

    def to_dict(self) -> dict:
        """Convert Price instance to dictionary representation.

        Returns:
            Dictionary with all Price attributes, including ISO format timestamp.
        """
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "currency": self.currency,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Price":
        """Create Price instance from dictionary.

        Args:
            data: Dictionary containing 'value', 'timestamp', and optionally 'currency'.
                  Timestamp can be ISO format string or datetime object.

        Returns:
            Price instance.

        Raises:
            KeyError: If required fields ('value', 'timestamp') are missing.
            TypeError: If timestamp cannot be converted to datetime.
        """
        timestamp = data["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            value=data["value"],
            timestamp=timestamp,
            currency=data.get("currency", "USD"),
        )


@dataclass(frozen=True)
class Candle:
    """OHLCV (Open, High, Low, Close, Volume) candle data.

    Represents candlestick data for a specific time interval.
    Used for technical analysis and price history tracking.

    Attributes:
        open: The opening price for the interval.
        high: The highest price during the interval.
        low: The lowest price during the interval.
        close: The closing price for the interval.
        volume: The trading volume during the interval.
        timestamp: The start datetime of this candle's interval.
        interval: The time interval string (e.g., "1m", "5m", "1h", "1d").
    """
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    interval: str = "1m"

    def to_dict(self) -> dict:
        """Convert Candle instance to dictionary representation.

        Returns:
            Dictionary with all Candle attributes.
        """
        return {
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timestamp": self.timestamp.isoformat(),
            "interval": self.interval,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Candle":
        """Create Candle instance from dictionary.

        Args:
            data: Dictionary containing all Candle attributes.
                  Timestamp can be ISO format string or datetime object.

        Returns:
            Candle instance.

        Raises:
            KeyError: If required fields are missing.
        """
        timestamp = data["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
            timestamp=timestamp,
            interval=data.get("interval", "1m"),
        )


@dataclass(frozen=True)
class Token:
    """Solana token metadata.

    Represents a token on the Solana blockchain with its metadata.
    Used for identifying and working with different tokens in the system.

    Attributes:
        symbol: The token symbol (e.g., "SOL", "USDC", "BONK").
        mint: The Solana mint address (base58 encoded string).
        decimals: The number of decimals for this token.
                   SOL has 9 decimals, USDC has 6, etc.
        name: Optional full token name (e.g., "Solana", "USD Coin").
    """
    symbol: str
    mint: str
    decimals: int
    name: str = ""

    def to_dict(self) -> dict:
        """Convert Token instance to dictionary representation.

        Returns:
            Dictionary with all Token attributes.
        """
        return {
            "symbol": self.symbol,
            "mint": self.mint,
            "decimals": self.decimals,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Token":
        """Create Token instance from dictionary.

        Args:
            data: Dictionary containing Token attributes.

        Returns:
            Token instance.

        Raises:
            KeyError: If required fields ('symbol', 'mint', 'decimals') are missing.
        """
        return cls(
            symbol=data["symbol"],
            mint=data["mint"],
            decimals=data["decimals"],
            name=data.get("name", ""),
        )

    @property
    def mint_address(self) -> str:
        """Alias for mint attribute for clarity."""
        return self.mint


@dataclass(frozen=True)
class TokenPair:
    """Trading pair representation (base/quote tokens).

    Represents a trading pair consisting of a base token and a quote token.
    Used for identifying which tokens are being traded against each other.

    Attributes:
        base: The base token of the pair (what you're buying/selling).
        quote: The quote token of the pair (what you're using to buy/sell).
        pair_symbol: The string representation of the pair (e.g., "SOL/USDC").
    """
    base: Token
    quote: Token
    pair_symbol: str = ""

    def __post_init__(self):
        """Validate pair_symbol format if provided, or generate it."""
        if not self.pair_symbol:
            object.__setattr__(self, "pair_symbol", f"{self.base.symbol}/{self.quote.symbol}")

    def to_dict(self) -> dict:
        """Convert TokenPair instance to dictionary representation.

        Returns:
            Dictionary with base, quote (as dicts), and pair_symbol.
        """
        return {
            "base": self.base.to_dict(),
            "quote": self.quote.to_dict(),
            "pair_symbol": self.pair_symbol,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenPair":
        """Create TokenPair instance from dictionary.

        Args:
            data: Dictionary containing 'base', 'quote' (as dicts), and optionally 'pair_symbol'.

        Returns:
            TokenPair instance.

        Raises:
            KeyError: If required fields ('base', 'quote') are missing.
        """
        return cls(
            base=Token.from_dict(data["base"]),
            quote=Token.from_dict(data["quote"]),
            pair_symbol=data.get("pair_symbol", ""),
        )

    @property
    def reverse(self) -> "TokenPair":
        """Return the reverse trading pair (quote becomes base, base becomes quote).

        Returns:
            A new TokenPair instance with tokens swapped.
        """
        return TokenPair(
            base=self.quote,
            quote=self.base,
            pair_symbol=f"{self.quote.symbol}/{self.base.symbol}",
        )


@dataclass(frozen=True)
class MarketData:
    """Aggregated market data combining price and indicators.

    Represents comprehensive market data for a specific token pair at a point in time.
    Combines price data with technical indicators for decision making.

    Attributes:
        price: The current price for this market.
        token_pair: The trading pair this market data pertains to.
        candles: List of recent candlestick data for technical analysis.
        indicators: Dictionary of technical indicator values.
                    Keys are indicator names (e.g., "RSI", "MACD"), values are indicator data.
        exchange: The exchange/source of this data (default: "Jupiter").
    """
    price: Price
    token_pair: TokenPair
    candles: List[Candle] = field(default_factory=list)
    indicators: Dict[str, Any] = field(default_factory=dict)
    exchange: str = "Jupiter"

    def to_dict(self) -> dict:
        """Convert MarketData instance to dictionary representation.

        Returns:
            Dictionary with all MarketData attributes, including nested serialization.
        """
        return {
            "price": self.price.to_dict(),
            "candles": [candle.to_dict() for candle in self.candles],
            "indicators": self.indicators,
            "token_pair": self.token_pair.to_dict(),
            "exchange": self.exchange,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MarketData":
        """Create MarketData instance from dictionary.

        Args:
            data: Dictionary containing MarketData attributes.
                  'price' and 'token_pair' should be dicts that can be deserialized.
                  'candles' should be a list of dicts.

        Returns:
            MarketData instance.

        Raises:
            KeyError: If required fields ('price', 'token_pair') are missing.
        """
        return cls(
            price=Price.from_dict(data["price"]),
            candles=[Candle.from_dict(candle) for candle in data.get("candles", [])],
            indicators=data.get("indicators", {}),
            token_pair=TokenPair.from_dict(data["token_pair"]),
            exchange=data.get("exchange", "Jupiter"),
        )

    def get_indicator(self, name: str) -> Optional[Any]:
        """Get a specific indicator value by name.

        Args:
            name: The name of the indicator to retrieve.

        Returns:
            The indicator value if found, None otherwise.
        """
        return self.indicators.get(name)

    def has_indicator(self, name: str) -> bool:
        """Check if a specific indicator is present in this market data.

        Args:
            name: The name of the indicator to check for.

        Returns:
            True if the indicator exists, False otherwise.
        """
        return name in self.indicators
