"""
Unit tests for Price and Market Data Domain Models (US-010).

Tests for immutable dataclasses:
- Price
- Candle
- Token
- TokenPair
- MarketData

All tests follow the red-green-refactor cycle and verify:
1. Instantiation with valid data
2. Instantiation with invalid/missing data raises appropriate errors
3. Immutability (frozen dataclasses)
4. Serialization/deserialization round-trip
5. Equality comparisons
6. Helper methods and properties
"""

from datetime import datetime
from typing import Any, Dict

import pytest

from src.core.models.price import (
    Candle,
    MarketData,
    Price,
    Token,
    TokenPair,
)


# =============================================================================
# Price Tests
# =============================================================================


class TestPriceInstantiation:
    """Tests for Price dataclass instantiation."""

    def test_price_with_required_fields(self) -> None:
        """Test Price creation with required fields only."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        price = Price(value=150.50, timestamp=timestamp)

        assert price.value == 150.50
        assert price.timestamp == timestamp
        assert price.currency == "USD"  # default

    def test_price_with_all_fields(self) -> None:
        """Test Price creation with all fields including currency."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        price = Price(value=150.50, timestamp=timestamp, currency="EUR")

        assert price.value == 150.50
        assert price.timestamp == timestamp
        assert price.currency == "EUR"

    def test_price_with_negative_value(self) -> None:
        """Test Price allows negative values (for price changes, etc.)."""
        timestamp = datetime.now()
        price = Price(value=-5.0, timestamp=timestamp)
        assert price.value == -5.0

    def test_price_with_zero_value(self) -> None:
        """Test Price allows zero value."""
        timestamp = datetime.now()
        price = Price(value=0.0, timestamp=timestamp)
        assert price.value == 0.0


class TestPriceSerialization:
    """Tests for Price serialization and deserialization."""

    def test_price_to_dict(self) -> None:
        """Test Price.to_dict() returns correct structure."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        price = Price(value=150.50, timestamp=timestamp, currency="USD")
        result = price.to_dict()

        assert isinstance(result, dict)
        assert result["value"] == 150.50
        assert result["timestamp"] == "2026-07-02T12:00:00"
        assert result["currency"] == "USD"

    def test_price_from_dict_with_datetime(self) -> None:
        """Test Price.from_dict() with datetime object."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        data = {"value": 150.50, "timestamp": timestamp}
        price = Price.from_dict(data)

        assert price.value == 150.50
        assert price.timestamp == timestamp
        assert price.currency == "USD"

    def test_price_from_dict_with_iso_string(self) -> None:
        """Test Price.from_dict() with ISO format timestamp string."""
        data = {"value": 150.50, "timestamp": "2026-07-02T12:00:00"}
        price = Price.from_dict(data)

        assert price.value == 150.50
        assert price.timestamp == datetime(2026, 7, 2, 12, 0, 0)
        assert price.currency == "USD"

    def test_price_from_dict_with_custom_currency(self) -> None:
        """Test Price.from_dict() with custom currency."""
        data = {"value": 150.50, "timestamp": "2026-07-02T12:00:00", "currency": "EUR"}
        price = Price.from_dict(data)
        assert price.currency == "EUR"

    def test_price_from_dict_missing_value_raises(self) -> None:
        """Test Price.from_dict() raises KeyError when value is missing."""
        data = {"timestamp": datetime.now()}
        with pytest.raises(KeyError, match="value"):
            Price.from_dict(data)

    def test_price_from_dict_missing_timestamp_raises(self) -> None:
        """Test Price.from_dict() raises KeyError when timestamp is missing."""
        data = {"value": 150.50}
        with pytest.raises(KeyError, match="timestamp"):
            Price.from_dict(data)

    def test_price_roundtrip_serialization(self) -> None:
        """Test Price serialization and deserialization round-trip."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        original = Price(value=150.50, timestamp=timestamp, currency="EUR")
        data = original.to_dict()
        restored = Price.from_dict(data)

        assert restored == original
        assert restored.value == original.value
        assert restored.timestamp == original.timestamp
        assert restored.currency == original.currency


class TestPriceImmutability:
    """Tests for Price immutability."""

    def test_price_is_frozen(self) -> None:
        """Test Price dataclass is frozen (immutable)."""
        timestamp = datetime.now()
        price = Price(value=150.50, timestamp=timestamp)

        with pytest.raises(AttributeError):
            price.value = 200.0  # type: ignore

    def test_price_frozen_prevents_timestamp_change(self) -> None:
        """Test Price frozen prevents timestamp modification."""
        timestamp = datetime.now()
        price = Price(value=150.50, timestamp=timestamp)

        with pytest.raises(AttributeError):
            price.timestamp = datetime.now()  # type: ignore


class TestPriceEquality:
    """Tests for Price equality comparisons."""

    def test_price_equality_same_values(self) -> None:
        """Test two Price instances with same values are equal."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        price1 = Price(value=150.50, timestamp=timestamp)
        price2 = Price(value=150.50, timestamp=timestamp)
        assert price1 == price2

    def test_price_equality_different_values(self) -> None:
        """Test two Price instances with different values are not equal."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        price1 = Price(value=150.50, timestamp=timestamp)
        price2 = Price(value=200.0, timestamp=timestamp)
        assert price1 != price2

    def test_price_equality_different_timestamps(self) -> None:
        """Test two Price instances with different timestamps are not equal."""
        price1 = Price(value=150.50, timestamp=datetime(2026, 7, 2, 12, 0, 0))
        price2 = Price(value=150.50, timestamp=datetime(2026, 7, 2, 13, 0, 0))
        assert price1 != price2


# =============================================================================
# Candle Tests
# =============================================================================


class TestCandleInstantiation:
    """Tests for Candle dataclass instantiation."""

    def test_candle_with_all_fields(self) -> None:
        """Test Candle creation with all OHLCV fields."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        candle = Candle(
            open=150.0,
            high=155.0,
            low=148.0,
            close=152.50,
            volume=1000.0,
            timestamp=timestamp,
            interval="1h",
        )

        assert candle.open == 150.0
        assert candle.high == 155.0
        assert candle.low == 148.0
        assert candle.close == 152.50
        assert candle.volume == 1000.0
        assert candle.timestamp == timestamp
        assert candle.interval == "1h"

    def test_candle_with_default_interval(self) -> None:
        """Test Candle creation with default interval (1m)."""
        timestamp = datetime.now()
        candle = Candle(
            open=150.0,
            high=155.0,
            low=148.0,
            close=152.50,
            volume=1000.0,
            timestamp=timestamp,
        )
        assert candle.interval == "1m"

    def test_candle_with_various_intervals(self) -> None:
        """Test Candle with different time intervals."""
        timestamp = datetime.now()
        for interval in ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]:
            candle = Candle(
                open=150.0, high=155.0, low=148.0, close=152.50,
                volume=1000.0, timestamp=timestamp, interval=interval
            )
            assert candle.interval == interval


class TestCandleSerialization:
    """Tests for Candle serialization and deserialization."""

    def test_candle_to_dict(self) -> None:
        """Test Candle.to_dict() returns correct structure."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        candle = Candle(
            open=150.0, high=155.0, low=148.0, close=152.50,
            volume=1000.0, timestamp=timestamp, interval="1h"
        )
        result = candle.to_dict()

        assert result["open"] == 150.0
        assert result["high"] == 155.0
        assert result["low"] == 148.0
        assert result["close"] == 152.50
        assert result["volume"] == 1000.0
        assert result["timestamp"] == "2026-07-02T12:00:00"
        assert result["interval"] == "1h"

    def test_candle_from_dict(self) -> None:
        """Test Candle.from_dict() creates valid instance."""
        data = {
            "open": 150.0,
            "high": 155.0,
            "low": 148.0,
            "close": 152.50,
            "volume": 1000.0,
            "timestamp": "2026-07-02T12:00:00",
            "interval": "1h",
        }
        candle = Candle.from_dict(data)

        assert candle.open == 150.0
        assert candle.high == 155.0
        assert candle.low == 148.0
        assert candle.close == 152.50
        assert candle.volume == 1000.0
        assert candle.timestamp == datetime(2026, 7, 2, 12, 0, 0)
        assert candle.interval == "1h"

    def test_candle_from_dict_missing_required_field_raises(self) -> None:
        """Test Candle.from_dict() raises KeyError when required field is missing."""
        data = {"high": 155.0, "low": 148.0, "close": 152.50, "volume": 1000.0, "timestamp": datetime.now()}
        with pytest.raises(KeyError, match="open"):
            Candle.from_dict(data)

    def test_candle_roundtrip_serialization(self) -> None:
        """Test Candle serialization and deserialization round-trip."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        original = Candle(
            open=150.0, high=155.0, low=148.0, close=152.50,
            volume=1000.0, timestamp=timestamp, interval="5m"
        )
        data = original.to_dict()
        restored = Candle.from_dict(data)

        assert restored == original


class TestCandleImmutability:
    """Tests for Candle immutability."""

    def test_candle_is_frozen(self) -> None:
        """Test Candle dataclass is frozen (immutable)."""
        timestamp = datetime.now()
        candle = Candle(
            open=150.0, high=155.0, low=148.0, close=152.50,
            volume=1000.0, timestamp=timestamp
        )

        with pytest.raises(AttributeError):
            candle.open = 200.0  # type: ignore


# =============================================================================
# Token Tests
# =============================================================================


class TestTokenInstantiation:
    """Tests for Token dataclass instantiation."""

    def test_token_with_required_fields(self) -> None:
        """Test Token creation with required fields."""
        token = Token(symbol="SOL", mint="So1111111111111111111111111111111111111111112", decimals=9)

        assert token.symbol == "SOL"
        assert token.mint == "So1111111111111111111111111111111111111111112"
        assert token.decimals == 9
        assert token.name == ""

    def test_token_with_full_name(self) -> None:
        """Test Token creation with full name."""
        token = Token(
            symbol="SOL",
            mint="So1111111111111111111111111111111111111111112",
            decimals=9,
            name="Solana",
        )
        assert token.name == "Solana"

    def test_token_usdc_example(self) -> None:
        """Test Token with USDC (6 decimals)."""
        token = Token(
            symbol="USDC",
            mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            decimals=6,
            name="USD Coin",
        )
        assert token.symbol == "USDC"
        assert token.decimals == 6

    def test_token_various_decimals(self) -> None:
        """Test Token with various decimal values."""
        for decimals in range(0, 10):
            token = Token(symbol="TEST", mint="T" * 44, decimals=decimals)
            assert token.decimals == decimals


class TestTokenSerialization:
    """Tests for Token serialization and deserialization."""

    def test_token_to_dict(self) -> None:
        """Test Token.to_dict() returns correct structure."""
        token = Token(
            symbol="SOL",
            mint="So1111111111111111111111111111111111111111112",
            decimals=9,
            name="Solana",
        )
        result = token.to_dict()

        assert result["symbol"] == "SOL"
        assert result["mint"] == "So1111111111111111111111111111111111111111112"
        assert result["decimals"] == 9
        assert result["name"] == "Solana"

    def test_token_from_dict(self) -> None:
        """Test Token.from_dict() creates valid instance."""
        data = {
            "symbol": "SOL",
            "mint": "So1111111111111111111111111111111111111111112",
            "decimals": 9,
        }
        token = Token.from_dict(data)

        assert token.symbol == "SOL"
        assert token.mint == "So1111111111111111111111111111111111111111112"
        assert token.decimals == 9
        assert token.name == ""

    def test_token_from_dict_missing_required_field_raises(self) -> None:
        """Test Token.from_dict() raises KeyError when required field is missing."""
        data = {"symbol": "SOL", "mint": "So1..."}
        with pytest.raises(KeyError, match="decimals"):
            Token.from_dict(data)

    def test_token_roundtrip_serialization(self) -> None:
        """Test Token serialization and deserialization round-trip."""
        original = Token(
            symbol="SOL",
            mint="So1111111111111111111111111111111111111111112",
            decimals=9,
            name="Solana",
        )
        data = original.to_dict()
        restored = Token.from_dict(data)

        assert restored == original


class TestTokenProperties:
    """Tests for Token properties."""

    def test_mint_address_property(self) -> None:
        """Test Token.mint_address property returns mint value."""
        token = Token(
            symbol="SOL",
            mint="So1111111111111111111111111111111111111111112",
            decimals=9,
        )
        assert token.mint_address == "So1111111111111111111111111111111111111111112"


class TestTokenImmutability:
    """Tests for Token immutability."""

    def test_token_is_frozen(self) -> None:
        """Test Token dataclass is frozen (immutable)."""
        token = Token(symbol="SOL", mint="So1...", decimals=9)

        with pytest.raises(AttributeError):
            token.symbol = "BTC"  # type: ignore


# =============================================================================
# TokenPair Tests
# =============================================================================


class TestTokenPairInstantiation:
    """Tests for TokenPair dataclass instantiation."""

    def test_token_pair_with_tokens(self) -> None:
        """Test TokenPair creation with base and quote tokens."""
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)

        assert pair.base == sol
        assert pair.quote == usdc
        assert pair.pair_symbol == "SOL/USDC"

    def test_token_pair_with_explicit_pair_symbol(self) -> None:
        """Test TokenPair with explicitly provided pair_symbol."""
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc, pair_symbol="SOL-USDC")

        assert pair.pair_symbol == "SOL-USDC"

    def test_token_pair_auto_generates_pair_symbol(self) -> None:
        """Test TokenPair auto-generates pair_symbol when not provided."""
        base = Token(symbol="BTC", mint="B...", decimals=8)
        quote = Token(symbol="ETH", mint="E...", decimals=18)
        pair = TokenPair(base=base, quote=quote)

        assert pair.pair_symbol == "BTC/ETH"


class TestTokenPairSerialization:
    """Tests for TokenPair serialization and deserialization."""

    def test_token_pair_to_dict(self) -> None:
        """Test TokenPair.to_dict() returns correct structure."""
        sol = Token(symbol="SOL", mint="So1...", decimals=9, name="Solana")
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6, name="USD Coin")
        pair = TokenPair(base=sol, quote=usdc, pair_symbol="SOL/USDC")
        result = pair.to_dict()

        assert result["pair_symbol"] == "SOL/USDC"
        assert result["base"]["symbol"] == "SOL"
        assert result["quote"]["symbol"] == "USDC"

    def test_token_pair_from_dict(self) -> None:
        """Test TokenPair.from_dict() creates valid instance."""
        data = {
            "base": {"symbol": "SOL", "mint": "So1...", "decimals": 9},
            "quote": {"symbol": "USDC", "mint": "EPj...", "decimals": 6},
            "pair_symbol": "SOL/USDC",
        }
        pair = TokenPair.from_dict(data)

        assert pair.base.symbol == "SOL"
        assert pair.quote.symbol == "USDC"
        assert pair.pair_symbol == "SOL/USDC"

    def test_token_pair_roundtrip_serialization(self) -> None:
        """Test TokenPair serialization and deserialization round-trip."""
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        original = TokenPair(base=sol, quote=usdc, pair_symbol="SOL/USDC")

        data = original.to_dict()
        restored = TokenPair.from_dict(data)

        assert restored == original


class TestTokenPairProperties:
    """Tests for TokenPair properties."""

    def test_reverse_property(self) -> None:
        """Test TokenPair.reverse returns swapped tokens."""
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc, pair_symbol="SOL/USDC")

        reversed_pair = pair.reverse

        assert reversed_pair.base == usdc
        assert reversed_pair.quote == sol
        assert reversed_pair.pair_symbol == "USDC/SOL"

    def test_reverse_returns_new_instance(self) -> None:
        """Test TokenPair.reverse returns a new instance, not modifying original."""
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)

        reversed_pair = pair.reverse

        # Original should be unchanged
        assert pair.base == sol
        assert pair.quote == usdc
        assert pair.pair_symbol == "SOL/USDC"

        # Reversed should be different
        assert reversed_pair != pair


class TestTokenPairImmutability:
    """Tests for TokenPair immutability."""

    def test_token_pair_is_frozen(self) -> None:
        """Test TokenPair dataclass is frozen (immutable)."""
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)

        new_sol = Token(symbol="BTC", mint="B...", decimals=8)
        with pytest.raises(AttributeError):
            pair.base = new_sol  # type: ignore


# =============================================================================
# MarketData Tests
# =============================================================================


class TestMarketDataInstantiation:
    """Tests for MarketData dataclass instantiation."""

    def test_market_data_with_required_fields(self) -> None:
        """Test MarketData creation with required fields."""
        price = Price(value=150.50, timestamp=datetime(2026, 7, 2, 12, 0, 0))
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)

        market_data = MarketData(price=price, token_pair=pair)

        assert market_data.price == price
        assert market_data.token_pair == pair
        assert market_data.candles == []
        assert market_data.indicators == {}
        assert market_data.exchange == "Jupiter"

    def test_market_data_with_all_fields(self) -> None:
        """Test MarketData creation with all optional fields."""
        price = Price(value=150.50, timestamp=datetime(2026, 7, 2, 12, 0, 0))
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)
        candle = Candle(
            open=150.0, high=155.0, low=148.0, close=152.50,
            volume=1000.0, timestamp=datetime(2026, 7, 2, 11, 55, 0)
        )

        market_data = MarketData(
            price=price,
            candles=[candle],
            indicators={"RSI": 70.5},
            token_pair=pair,
            exchange="Jupiter",
        )

        assert len(market_data.candles) == 1
        assert market_data.indicators["RSI"] == 70.5
        assert market_data.candles[0] == candle

    def test_market_data_empty_candles_and_indicators(self) -> None:
        """Test MarketData with empty candles and indicators."""
        price = Price(value=150.50, timestamp=datetime.now())
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)

        market_data = MarketData(price=price, token_pair=pair)

        assert market_data.candles == []
        assert market_data.indicators == {}


class TestMarketDataMethods:
    """Tests for MarketData methods."""

    def test_get_indicator(self) -> None:
        """Test MarketData.get_indicator() returns correct value."""
        price = Price(value=150.50, timestamp=datetime.now())
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)

        market_data = MarketData(
            price=price,
            token_pair=pair,
            indicators={"RSI": 70.5, "MACD": 1.2},
        )

        assert market_data.get_indicator("RSI") == 70.5
        assert market_data.get_indicator("MACD") == 1.2
        assert market_data.get_indicator("NonExistent") is None

    def test_has_indicator(self) -> None:
        """Test MarketData.has_indicator() returns correct boolean."""
        price = Price(value=150.50, timestamp=datetime.now())
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)

        market_data = MarketData(
            price=price,
            token_pair=pair,
            indicators={"RSI": 70.5},
        )

        assert market_data.has_indicator("RSI") is True
        assert market_data.has_indicator("MACD") is False


class TestMarketDataSerialization:
    """Tests for MarketData serialization and deserialization."""

    def test_market_data_to_dict(self) -> None:
        """Test MarketData.to_dict() returns correct structure."""
        price = Price(value=150.50, timestamp=datetime(2026, 7, 2, 12, 0, 0))
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)
        candle = Candle(
            open=150.0, high=155.0, low=148.0, close=152.50,
            volume=1000.0, timestamp=datetime(2026, 7, 2, 11, 55, 0)
        )

        market_data = MarketData(
            price=price,
            candles=[candle],
            indicators={"RSI": 70.5},
            token_pair=pair,
        )
        result = market_data.to_dict()

        assert "price" in result
        assert "candles" in result
        assert "indicators" in result
        assert "token_pair" in result
        assert "exchange" in result
        assert len(result["candles"]) == 1
        assert result["indicators"]["RSI"] == 70.5

    def test_market_data_from_dict(self) -> None:
        """Test MarketData.from_dict() creates valid instance."""
        data = {
            "price": {"value": 150.50, "timestamp": "2026-07-02T12:00:00"},
            "candles": [
                {
                    "open": 150.0,
                    "high": 155.0,
                    "low": 148.0,
                    "close": 152.50,
                    "volume": 1000.0,
                    "timestamp": "2026-07-02T11:55:00",
                    "interval": "5m",
                }
            ],
            "indicators": {"RSI": 70.5},
            "token_pair": {
                "base": {"symbol": "SOL", "mint": "So1...", "decimals": 9},
                "quote": {"symbol": "USDC", "mint": "EPj...", "decimals": 6},
                "pair_symbol": "SOL/USDC",
            },
        }
        market_data = MarketData.from_dict(data)

        assert market_data.price.value == 150.50
        assert len(market_data.candles) == 1
        assert market_data.indicators["RSI"] == 70.5
        assert market_data.token_pair.pair_symbol == "SOL/USDC"

    def test_market_data_from_dict_missing_required_field_raises(self) -> None:
        """Test MarketData.from_dict() raises KeyError when required field is missing."""
        data = {
            "candles": [],
            "indicators": {},
            "token_pair": {
                "base": {"symbol": "SOL", "mint": "So1...", "decimals": 9},
                "quote": {"symbol": "USDC", "mint": "EPj...", "decimals": 6},
            },
        }
        with pytest.raises(KeyError, match="price"):
            MarketData.from_dict(data)

    def test_market_data_roundtrip_serialization(self) -> None:
        """Test MarketData serialization and deserialization round-trip."""
        price = Price(value=150.50, timestamp=datetime(2026, 7, 2, 12, 0, 0))
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)
        candle = Candle(
            open=150.0, high=155.0, low=148.0, close=152.50,
            volume=1000.0, timestamp=datetime(2026, 7, 2, 11, 55, 0), interval="5m"
        )

        original = MarketData(
            price=price,
            candles=[candle],
            indicators={"RSI": 70.5, "MACD": 1.2},
            token_pair=pair,
            exchange="Jupiter",
        )

        data = original.to_dict()
        restored = MarketData.from_dict(data)

        assert restored == original


class TestMarketDataImmutability:
    """Tests for MarketData immutability."""

    def test_market_data_is_frozen(self) -> None:
        """Test MarketData dataclass is frozen (immutable)."""
        price = Price(value=150.50, timestamp=datetime.now())
        sol = Token(symbol="SOL", mint="So1...", decimals=9)
        usdc = Token(symbol="USDC", mint="EPj...", decimals=6)
        pair = TokenPair(base=sol, quote=usdc)

        market_data = MarketData(price=price, token_pair=pair)

        new_price = Price(value=200.0, timestamp=datetime.now())
        with pytest.raises(AttributeError):
            market_data.price = new_price  # type: ignore
