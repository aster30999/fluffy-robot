"""
Unit tests for Trade and Decision Domain Models (US-012).

Tests for:
- TradeStatus enum
- TradeType enum
- Signal enum
- Trade dataclass
- Decision dataclass

All tests follow the red-green-refactor cycle and verify:
1. Enum values and iteration
2. Instantiation with valid data
3. Instantiation with invalid/missing data raises appropriate errors
4. Immutability (frozen dataclasses)
5. Serialization/deserialization round-trip
6. Equality comparisons
7. Helper methods and properties
"""

from datetime import datetime
from uuid import uuid4

import pytest

from src.core.models.balance import Portfolio, Balance
from src.core.models.price import Price, Token, TokenPair
from src.core.models.trade import (
    Decision,
    Signal,
    Trade,
    TradeStatus,
    TradeType,
)


# =============================================================================
# Fixtures - Reusable test data
# =============================================================================

@pytest.fixture
def sol_token() -> Token:
    """SOL token with 9 decimals."""
    return Token(symbol="SOL", mint="So1111111111111111111111111111111111111111112", decimals=9, name="Solana")


@pytest.fixture
def usdc_token() -> Token:
    """USDC token with 6 decimals."""
    return Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6, name="USD Coin")


@pytest.fixture
def sol_usdc_pair(sol_token: Token, usdc_token: Token) -> TokenPair:
    """SOL/USDC token pair."""
    return TokenPair(base=sol_token, quote=usdc_token)


@pytest.fixture
def sol_price() -> Price:
    """Price for SOL in USD."""
    return Price(value=150.50, timestamp=datetime(2026, 7, 2, 12, 0, 0), currency="USD")


@pytest.fixture
def usdc_price() -> Price:
    """Price for USDC in USD."""
    return Price(value=1.00, timestamp=datetime(2026, 7, 2, 12, 0, 0), currency="USD")


@pytest.fixture
def sol_balance(sol_token: Token) -> Balance:
    """Balance of 10 SOL."""
    return Balance(token=sol_token, amount=10.0)


@pytest.fixture
def usdc_balance(usdc_token: Token) -> Balance:
    """Balance of 1000 USDC."""
    return Balance(token=usdc_token, amount=1000.0)


@pytest.fixture
def portfolio(sol_balance: Balance, usdc_balance: Balance) -> Portfolio:
    """Portfolio with SOL and USDC balances."""
    return Portfolio(balances={"SOL": sol_balance, "USDC": usdc_balance})


# =============================================================================
# TradeStatus Enum Tests
# =============================================================================


class TestTradeStatus:
    """Tests for TradeStatus enum."""

    def test_all_values_accessible(self) -> None:
        """Test all TradeStatus enum values are accessible."""
        assert TradeStatus.PENDING is not None
        assert TradeStatus.SUCCESS is not None
        assert TradeStatus.FAILED is not None

    def test_enum_comparison(self) -> None:
        """Test TradeStatus enum comparison."""
        assert TradeStatus.PENDING == TradeStatus.PENDING
        assert TradeStatus.PENDING != TradeStatus.SUCCESS
        assert TradeStatus.SUCCESS != TradeStatus.FAILED

    def test_enum_iteration(self) -> None:
        """Test TradeStatus enum iteration."""
        values = list(TradeStatus)
        assert len(values) == 3
        assert TradeStatus.PENDING in values
        assert TradeStatus.SUCCESS in values
        assert TradeStatus.FAILED in values

    def test_enum_name(self) -> None:
        """Test TradeStatus enum names."""
        assert TradeStatus.PENDING.name == "PENDING"
        assert TradeStatus.SUCCESS.name == "SUCCESS"
        assert TradeStatus.FAILED.name == "FAILED"


# =============================================================================
# TradeType Enum Tests
# =============================================================================


class TestTradeType:
    """Tests for TradeType enum."""

    def test_all_values_accessible(self) -> None:
        """Test all TradeType enum values are accessible."""
        assert TradeType.BUY is not None
        assert TradeType.SELL is not None
        assert TradeType.SWAP is not None

    def test_enum_comparison(self) -> None:
        """Test TradeType enum comparison."""
        assert TradeType.BUY == TradeType.BUY
        assert TradeType.BUY != TradeType.SELL
        assert TradeType.SELL != TradeType.SWAP

    def test_enum_iteration(self) -> None:
        """Test TradeType enum iteration."""
        values = list(TradeType)
        assert len(values) == 3
        assert TradeType.BUY in values
        assert TradeType.SELL in values
        assert TradeType.SWAP in values

    def test_enum_name(self) -> None:
        """Test TradeType enum names."""
        assert TradeType.BUY.name == "BUY"
        assert TradeType.SELL.name == "SELL"
        assert TradeType.SWAP.name == "SWAP"


# =============================================================================
# Signal Enum Tests
# =============================================================================


class TestSignal:
    """Tests for Signal enum."""

    def test_all_values_accessible(self) -> None:
        """Test all Signal enum values are accessible."""
        assert Signal.BUY is not None
        assert Signal.SELL is not None
        assert Signal.NEUTRAL is not None

    def test_enum_comparison(self) -> None:
        """Test Signal enum comparison."""
        assert Signal.BUY == Signal.BUY
        assert Signal.BUY != Signal.SELL
        assert Signal.SELL != Signal.NEUTRAL

    def test_enum_iteration(self) -> None:
        """Test Signal enum iteration."""
        values = list(Signal)
        assert len(values) == 3
        assert Signal.BUY in values
        assert Signal.SELL in values
        assert Signal.NEUTRAL in values

    def test_enum_name(self) -> None:
        """Test Signal enum names."""
        assert Signal.BUY.name == "BUY"
        assert Signal.SELL.name == "SELL"
        assert Signal.NEUTRAL.name == "NEUTRAL"


# =============================================================================
# Trade Dataclass Tests
# =============================================================================


class TestTradeInstantiation:
    """Tests for Trade dataclass instantiation."""

    def test_trade_with_all_required_fields(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade creation with all required fields."""
        trade = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=datetime(2026, 7, 2, 12, 0, 0),
        )

        assert trade.trade_id == "trade-001"
        assert trade.token_pair == sol_usdc_pair
        assert trade.amount == 5.0
        assert trade.trade_type == TradeType.BUY
        assert trade.price == sol_price
        assert trade.timestamp == datetime(2026, 7, 2, 12, 0, 0)
        assert trade.status == TradeStatus.PENDING
        assert trade.fees == 0.0
        assert trade.slippage == 0.0
        assert trade.notes == ""

    def test_trade_with_all_fields(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade creation with all fields including optional ones."""
        trade = Trade(
            trade_id="trade-002",
            token_pair=sol_usdc_pair,
            amount=10.0,
            trade_type=TradeType.SELL,
            price=sol_price,
            timestamp=datetime(2026, 7, 2, 12, 0, 0),
            status=TradeStatus.SUCCESS,
            fees=0.005,
            slippage=0.1,
            notes="Test trade",
        )

        assert trade.status == TradeStatus.SUCCESS
        assert trade.fees == 0.005
        assert trade.slippage == 0.1
        assert trade.notes == "Test trade"

    def test_trade_with_sell_type(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade with SELL type."""
        trade = Trade(
            trade_id="trade-003",
            token_pair=sol_usdc_pair,
            amount=2.5,
            trade_type=TradeType.SELL,
            price=sol_price,
            timestamp=datetime.now(),
        )
        assert trade.trade_type == TradeType.SELL

    def test_trade_with_swap_type(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade with SWAP type."""
        trade = Trade(
            trade_id="trade-004",
            token_pair=sol_usdc_pair,
            amount=100.0,
            trade_type=TradeType.SWAP,
            price=sol_price,
            timestamp=datetime.now(),
        )
        assert trade.trade_type == TradeType.SWAP


class TestTradeProperties:
    """Tests for Trade properties."""

    def test_base_amount(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade.base_amount property."""
        trade = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=datetime.now(),
        )
        assert trade.base_amount == 5.0

    def test_quote_amount(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade.quote_amount property."""
        # SOL price is 150.50 USD
        # Trading 5 SOL should give 5 * 150.50 = 752.50 USD (quote amount)
        trade = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=datetime.now(),
        )
        expected = 5.0 * 150.50
        assert trade.quote_amount == pytest.approx(expected)

    def test_total_cost_buy(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade.total_cost for BUY trade."""
        # BUY: quote_amount + fees
        trade = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=datetime.now(),
            fees=0.01,  # 0.01 USDC in fees
        )
        expected = (5.0 * 150.50) + 0.01
        assert trade.total_cost == pytest.approx(expected)

    def test_total_cost_sell(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade.total_cost for SELL trade."""
        # SELL: quote_amount - fees (fees deducted from proceeds)
        trade = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.SELL,
            price=sol_price,
            timestamp=datetime.now(),
            fees=0.01,  # 0.01 USDC in fees
        )
        expected = (5.0 * 150.50) - 0.01
        assert trade.total_cost == pytest.approx(expected)

    def test_total_cost_swap(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade.total_cost for SWAP trade."""
        # SWAP: quote_amount + fees
        trade = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.SWAP,
            price=sol_price,
            timestamp=datetime.now(),
            fees=0.01,
        )
        expected = (5.0 * 150.50) + 0.01
        assert trade.total_cost == pytest.approx(expected)


class TestTradeSerialization:
    """Tests for Trade serialization and deserialization."""

    def test_trade_to_dict(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade.to_dict() returns correct structure."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        trade = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=timestamp,
            status=TradeStatus.PENDING,
            fees=0.0,
            slippage=0.0,
            notes="",
        )
        result = trade.to_dict()

        assert result["trade_id"] == "trade-001"
        assert result["amount"] == 5.0
        assert result["trade_type"] == "BUY"
        assert result["status"] == "PENDING"
        assert result["fees"] == 0.0
        assert "token_pair" in result
        assert "price" in result
        assert "timestamp" in result

    def test_trade_from_dict(
        self, sol_token: Token, usdc_token: Token
    ) -> None:
        """Test Trade.from_dict() creates valid instance."""
        data = {
            "trade_id": "trade-001",
            "token_pair": {
                "base": {"symbol": "SOL", "mint": "So1...", "decimals": 9},
                "quote": {"symbol": "USDC", "mint": "EPj...", "decimals": 6},
                "pair_symbol": "SOL/USDC",
            },
            "amount": 5.0,
            "trade_type": "BUY",
            "price": {"value": 150.50, "timestamp": "2026-07-02T12:00:00", "currency": "USD"},
            "timestamp": "2026-07-02T12:00:00",
            "status": "PENDING",
            "fees": 0.0,
            "slippage": 0.0,
            "notes": "",
        }
        trade = Trade.from_dict(data)

        assert trade.trade_id == "trade-001"
        assert trade.amount == 5.0
        assert trade.trade_type == TradeType.BUY
        assert trade.status == TradeStatus.PENDING

    def test_trade_from_dict_with_optional_fields(
        self, sol_token: Token, usdc_token: Token
    ) -> None:
        """Test Trade.from_dict() with all optional fields."""
        data = {
            "trade_id": "trade-002",
            "token_pair": {
                "base": {"symbol": "SOL", "mint": "So1...", "decimals": 9},
                "quote": {"symbol": "USDC", "mint": "EPj...", "decimals": 6},
                "pair_symbol": "SOL/USDC",
            },
            "amount": 10.0,
            "trade_type": "SELL",
            "price": {"value": 150.50, "timestamp": "2026-07-02T12:00:00", "currency": "USD"},
            "timestamp": "2026-07-02T12:00:00",
            "status": "SUCCESS",
            "fees": 0.005,
            "slippage": 0.1,
            "notes": "Test trade",
        }
        trade = Trade.from_dict(data)

        assert trade.status == TradeStatus.SUCCESS
        assert trade.fees == 0.005
        assert trade.slippage == 0.1
        assert trade.notes == "Test trade"

    def test_trade_roundtrip_serialization(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade serialization and deserialization round-trip."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        original = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=timestamp,
            status=TradeStatus.SUCCESS,
            fees=0.005,
            slippage=0.1,
            notes="Test",
        )

        data = original.to_dict()
        restored = Trade.from_dict(data)

        assert restored == original


class TestTradeImmutability:
    """Tests for Trade immutability."""

    def test_trade_is_frozen(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test Trade dataclass is frozen (immutable)."""
        trade = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=datetime.now(),
        )

        with pytest.raises(AttributeError):
            trade.amount = 10.0  # type: ignore


class TestTradeEquality:
    """Tests for Trade equality comparisons."""

    def test_trade_equality_same_values(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test two Trade instances with same values are equal."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        trade1 = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=timestamp,
        )
        trade2 = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=timestamp,
        )
        assert trade1 == trade2

    def test_trade_equality_different_trade_id(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test two Trade instances with different trade_id are not equal."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        trade1 = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=timestamp,
        )
        trade2 = Trade(
            trade_id="trade-002",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=timestamp,
        )
        assert trade1 != trade2


# =============================================================================
# Decision Dataclass Tests
# =============================================================================


class TestDecisionInstantiation:
    """Tests for Decision dataclass instantiation."""

    def test_decision_with_all_required_fields(
        self, sol_usdc_pair: TokenPair
    ) -> None:
        """Test Decision creation with all required fields."""
        decision = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.85,
            timestamp=datetime(2026, 7, 2, 12, 0, 0),
        )

        assert decision.decision_id == "decision-001"
        assert decision.token_pair == sol_usdc_pair
        assert decision.signal == Signal.BUY
        assert decision.confidence == 0.85
        assert decision.timestamp == datetime(2026, 7, 2, 12, 0, 0)
        assert decision.reasoning == ""
        assert decision.indicators == {}
        assert decision.portfolio_snapshot is None

    def test_decision_with_all_fields(
        self, sol_usdc_pair: TokenPair, portfolio: Portfolio
    ) -> None:
        """Test Decision creation with all fields including optional ones."""
        decision = Decision(
            decision_id="decision-002",
            token_pair=sol_usdc_pair,
            signal=Signal.SELL,
            confidence=0.95,
            timestamp=datetime(2026, 7, 2, 12, 0, 0),
            reasoning="RSI above 70",
            indicators={"RSI": 75.0, "MACD": 1.2},
            portfolio_snapshot=portfolio,
        )

        assert decision.reasoning == "RSI above 70"
        assert decision.indicators["RSI"] == 75.0
        assert decision.portfolio_snapshot == portfolio

    def test_decision_with_neutral_signal(
        self, sol_usdc_pair: TokenPair
    ) -> None:
        """Test Decision with NEUTRAL signal."""
        decision = Decision(
            decision_id="decision-003",
            token_pair=sol_usdc_pair,
            signal=Signal.NEUTRAL,
            confidence=0.5,
            timestamp=datetime.now(),
        )
        assert decision.signal == Signal.NEUTRAL

    def test_decision_confidence_validation_too_low(self, sol_usdc_pair: TokenPair) -> None:
        """Test Decision raises ValueError for confidence < 0."""
        with pytest.raises(ValueError, match="confidence must be between"):
            Decision(
                decision_id="decision-001",
                token_pair=sol_usdc_pair,
                signal=Signal.BUY,
                confidence=-0.1,
                timestamp=datetime.now(),
            )

    def test_decision_confidence_validation_too_high(self, sol_usdc_pair: TokenPair) -> None:
        """Test Decision raises ValueError for confidence > 1."""
        with pytest.raises(ValueError, match="confidence must be between"):
            Decision(
                decision_id="decision-001",
                token_pair=sol_usdc_pair,
                signal=Signal.BUY,
                confidence=1.5,
                timestamp=datetime.now(),
            )

    def test_decision_confidence_boundary_values(self, sol_usdc_pair: TokenPair) -> None:
        """Test Decision with boundary confidence values."""
        # 0.0 is valid
        decision1 = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.0,
            timestamp=datetime.now(),
        )
        assert decision1.confidence == 0.0

        # 1.0 is valid
        decision2 = Decision(
            decision_id="decision-002",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=1.0,
            timestamp=datetime.now(),
        )
        assert decision2.confidence == 1.0


class TestDecisionProperties:
    """Tests for Decision properties."""

    def test_is_actionable_buy(self, sol_usdc_pair: TokenPair) -> None:
        """Test Decision.is_actionable returns True for BUY signal."""
        decision = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.8,
            timestamp=datetime.now(),
        )
        assert decision.is_actionable is True

    def test_is_actionable_sell(self, sol_usdc_pair: TokenPair) -> None:
        """Test Decision.is_actionable returns True for SELL signal."""
        decision = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.SELL,
            confidence=0.8,
            timestamp=datetime.now(),
        )
        assert decision.is_actionable is True

    def test_is_actionable_neutral(self, sol_usdc_pair: TokenPair) -> None:
        """Test Decision.is_actionable returns False for NEUTRAL signal."""
        decision = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.NEUTRAL,
            confidence=0.8,
            timestamp=datetime.now(),
        )
        assert decision.is_actionable is False

    def test_is_strong_high_confidence(self, sol_usdc_pair: TokenPair) -> None:
        """Test Decision.is_strong returns True for high confidence."""
        decision = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.8,
            timestamp=datetime.now(),
        )
        assert decision.is_strong is True

    def test_is_strong_low_confidence(self, sol_usdc_pair: TokenPair) -> None:
        """Test Decision.is_strong returns False for low confidence."""
        decision = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.6,
            timestamp=datetime.now(),
        )
        assert decision.is_strong is False

    def test_is_strong_boundary(self, sol_usdc_pair: TokenPair) -> None:
        """Test Decision.is_strong boundary at 0.7."""
        # Exactly 0.7 should be strong
        decision1 = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.7,
            timestamp=datetime.now(),
        )
        assert decision1.is_strong is True

        # Just below 0.7 should not be strong
        decision2 = Decision(
            decision_id="decision-002",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.699,
            timestamp=datetime.now(),
        )
        assert decision2.is_strong is False


class TestDecisionSerialization:
    """Tests for Decision serialization and deserialization."""

    def test_decision_to_dict(
        self, sol_usdc_pair: TokenPair
    ) -> None:
        """Test Decision.to_dict() returns correct structure."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        decision = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.85,
            timestamp=timestamp,
            reasoning="RSI above 70",
            indicators={"RSI": 75.0},
            portfolio_snapshot=None,
        )
        result = decision.to_dict()

        assert result["decision_id"] == "decision-001"
        assert result["signal"] == "BUY"
        assert result["confidence"] == 0.85
        assert result["reasoning"] == "RSI above 70"
        assert result["indicators"]["RSI"] == 75.0
        assert result["portfolio_snapshot"] is None

    def test_decision_from_dict(
        self, sol_token: Token, usdc_token: Token
    ) -> None:
        """Test Decision.from_dict() creates valid instance."""
        data = {
            "decision_id": "decision-001",
            "token_pair": {
                "base": {"symbol": "SOL", "mint": "So1...", "decimals": 9},
                "quote": {"symbol": "USDC", "mint": "EPj...", "decimals": 6},
                "pair_symbol": "SOL/USDC",
            },
            "signal": "BUY",
            "confidence": 0.85,
            "timestamp": "2026-07-02T12:00:00",
            "reasoning": "RSI above 70",
            "indicators": {"RSI": 75.0},
            "portfolio_snapshot": None,
        }
        decision = Decision.from_dict(data)

        assert decision.decision_id == "decision-001"
        assert decision.signal == Signal.BUY
        assert decision.confidence == 0.85
        assert decision.reasoning == "RSI above 70"
        assert decision.indicators["RSI"] == 75.0

    def test_decision_from_dict_with_portfolio(
        self, sol_token: Token, usdc_token: Token
    ) -> None:
        """Test Decision.from_dict() with portfolio_snapshot."""
        data = {
            "decision_id": "decision-001",
            "token_pair": {
                "base": {"symbol": "SOL", "mint": "So1...", "decimals": 9},
                "quote": {"symbol": "USDC", "mint": "EPj...", "decimals": 6},
                "pair_symbol": "SOL/USDC",
            },
            "signal": "BUY",
            "confidence": 0.85,
            "timestamp": "2026-07-02T12:00:00",
            "reasoning": "",
            "indicators": {},
            "portfolio_snapshot": {
                "balances": {
                    "SOL": {
                        "token": {"symbol": "SOL", "mint": "So1...", "decimals": 9},
                        "amount": 10.0,
                    },
                    "USDC": {
                        "token": {"symbol": "USDC", "mint": "EPj...", "decimals": 6},
                        "amount": 1000.0,
                    },
                }
            },
        }
        decision = Decision.from_dict(data)

        assert decision.portfolio_snapshot is not None
        assert decision.portfolio_snapshot.get_balance("SOL") is not None
        assert decision.portfolio_snapshot.get_balance("SOL").amount == 10.0

    def test_decision_roundtrip_serialization(
        self, sol_usdc_pair: TokenPair
    ) -> None:
        """Test Decision serialization and deserialization round-trip."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        original = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.85,
            timestamp=timestamp,
            reasoning="RSI above 70",
            indicators={"RSI": 75.0, "MACD": 1.2},
            portfolio_snapshot=None,
        )

        data = original.to_dict()
        restored = Decision.from_dict(data)

        assert restored == original


class TestDecisionImmutability:
    """Tests for Decision immutability."""

    def test_decision_is_frozen(
        self, sol_usdc_pair: TokenPair
    ) -> None:
        """Test Decision dataclass is frozen (immutable)."""
        decision = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.85,
            timestamp=datetime.now(),
        )

        with pytest.raises(AttributeError):
            decision.confidence = 0.9  # type: ignore


class TestDecisionEquality:
    """Tests for Decision equality comparisons."""

    def test_decision_equality_same_values(
        self, sol_usdc_pair: TokenPair
    ) -> None:
        """Test two Decision instances with same values are equal."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        decision1 = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.85,
            timestamp=timestamp,
        )
        decision2 = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.85,
            timestamp=timestamp,
        )
        assert decision1 == decision2

    def test_decision_equality_different_decision_id(
        self, sol_usdc_pair: TokenPair
    ) -> None:
        """Test two Decision instances with different decision_id are not equal."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        decision1 = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.85,
            timestamp=timestamp,
        )
        decision2 = Decision(
            decision_id="decision-002",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.85,
            timestamp=timestamp,
        )
        assert decision1 != decision2


# =============================================================================
# Integration Tests
# =============================================================================


class TestTradeDecisionIntegration:
    """Integration tests for Trade and Decision models."""

    def test_trade_to_decision_link(
        self, sol_usdc_pair: TokenPair, sol_price: Price
    ) -> None:
        """Test that Trade and Decision can be created with same token_pair."""
        timestamp = datetime(2026, 7, 2, 12, 0, 0)
        
        decision = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.85,
            timestamp=timestamp,
        )
        
        trade = Trade(
            trade_id="trade-001",
            token_pair=sol_usdc_pair,
            amount=5.0,
            trade_type=TradeType.BUY,
            price=sol_price,
            timestamp=timestamp,
        )
        
        assert decision.token_pair == trade.token_pair

    def test_decision_with_portfolio_snapshot(
        self, sol_usdc_pair: TokenPair, portfolio: Portfolio
    ) -> None:
        """Test Decision with portfolio snapshot can be serialized and deserialized."""
        decision = Decision(
            decision_id="decision-001",
            token_pair=sol_usdc_pair,
            signal=Signal.BUY,
            confidence=0.85,
            timestamp=datetime.now(),
            portfolio_snapshot=portfolio,
        )
        
        data = decision.to_dict()
        restored = Decision.from_dict(data)
        
        assert restored.portfolio_snapshot is not None
        assert restored.portfolio_snapshot.total_tokens == portfolio.total_tokens

    def test_trade_quote_amount_calculation(
        self, sol_usdc_pair: TokenPair
    ) -> None:
        """Test Trade.quote_amount calculation with different prices."""
        # Test with different price values
        for price_value in [100.0, 150.50, 200.0, 0.5]:
            price = Price(
                value=price_value,
                timestamp=datetime.now(),
                currency="USD"
            )
            trade = Trade(
                trade_id=f"trade-{price_value}",
                token_pair=sol_usdc_pair,
                amount=10.0,
                trade_type=TradeType.BUY,
                price=price,
                timestamp=datetime.now(),
            )
            expected = 10.0 * price_value
            assert trade.quote_amount == pytest.approx(expected)
