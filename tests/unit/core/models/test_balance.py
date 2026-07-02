"""
Unit tests for Balance and Portfolio Domain Models (US-011).

Tests for immutable dataclasses:
- Balance
- Portfolio

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

from src.core.models.balance import Balance, Portfolio
from src.core.models.price import Price, Token


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
def bonk_token() -> Token:
    """BONK token with 5 decimals."""
    return Token(symbol="BONK", mint="DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", decimals=5, name="Bonk")


@pytest.fixture
def price_map() -> Dict[str, Price]:
    """Price map for portfolio valuation tests."""
    now = datetime(2026, 7, 2, 12, 0, 0)
    return {
        "SOL": Price(value=150.50, timestamp=now, currency="USD"),
        "USDC": Price(value=1.00, timestamp=now, currency="USD"),
        "BONK": Price(value=0.000025, timestamp=now, currency="USD"),
    }


# =============================================================================
# Balance Tests
# =============================================================================


class TestBalanceInstantiation:
    """Tests for Balance dataclass instantiation."""

    def test_balance_with_valid_token_and_amount(self, sol_token: Token) -> None:
        """Test Balance creation with valid token and positive amount."""
        balance = Balance(token=sol_token, amount=10.5)

        assert balance.token == sol_token
        assert balance.amount == 10.5

    def test_balance_with_zero_amount(self, sol_token: Token) -> None:
        """Test Balance with zero amount."""
        balance = Balance(token=sol_token, amount=0.0)
        assert balance.amount == 0.0

    def test_balance_with_negative_amount(self, sol_token: Token) -> None:
        """Test Balance with negative amount (short position)."""
        balance = Balance(token=sol_token, amount=-5.0)
        assert balance.amount == -5.0

    def test_balance_with_large_amount(self, sol_token: Token) -> None:
        """Test Balance with large amount."""
        balance = Balance(token=sol_token, amount=1_000_000.0)
        assert balance.amount == 1_000_000.0

    def test_balance_with_small_fractional_amount(self, sol_token: Token) -> None:
        """Test Balance with small fractional amount."""
        balance = Balance(token=sol_token, amount=0.000000001)
        assert balance.amount == 0.000000001


class TestBalanceLamportsConversion:
    """Tests for Balance lamports conversion."""

    def test_amount_in_lamports_sol(self, sol_token: Token) -> None:
        """Test SOL balance conversion to lamports (9 decimals)."""
        balance = Balance(token=sol_token, amount=10.5)
        # 10.5 SOL * 10^9 = 10,500,000,000 lamports
        assert balance.amount_in_lamports == 10_500_000_000

    def test_amount_in_lamports_usdc(self, usdc_token: Token) -> None:
        """Test USDC balance conversion to lamports (6 decimals)."""
        balance = Balance(token=usdc_token, amount=100.5)
        # 100.5 USDC * 10^6 = 100,500,000 lamports
        assert balance.amount_in_lamports == 100_500_000

    def test_amount_in_lamports_bonk(self, bonk_token: Token) -> None:
        """Test BONK balance conversion to lamports (5 decimals)."""
        balance = Balance(token=bonk_token, amount=1000.0)
        # 1000 BONK * 10^5 = 100,000,000 lamports
        assert balance.amount_in_lamports == 100_000_000

    def test_amount_in_lamports_zero(self, sol_token: Token) -> None:
        """Test zero amount conversion to lamports."""
        balance = Balance(token=sol_token, amount=0.0)
        assert balance.amount_in_lamports == 0

    def test_amount_in_lamports_negative(self, sol_token: Token) -> None:
        """Test negative amount conversion to lamports."""
        balance = Balance(token=sol_token, amount=-5.0)
        # -5 SOL * 10^9 = -5,000,000,000 lamports
        assert balance.amount_in_lamports == -5_000_000_000

    def test_from_lamports_sol(self, sol_token: Token) -> None:
        """Test creating Balance from lamports for SOL."""
        balance = Balance.from_lamports(token=sol_token, lamports=10_500_000_000)
        assert balance.amount == 10.5

    def test_from_lamports_usdc(self, usdc_token: Token) -> None:
        """Test creating Balance from lamports for USDC."""
        balance = Balance.from_lamports(token=usdc_token, lamports=100_500_000)
        assert balance.amount == 100.5

    def test_lamports_roundtrip_sol(self, sol_token: Token) -> None:
        """Test lamports conversion round-trip for SOL."""
        original = Balance(token=sol_token, amount=10.5)
        lamports = original.amount_in_lamports
        restored = Balance.from_lamports(token=sol_token, lamports=lamports)
        assert restored.amount == original.amount

    def test_lamports_roundtrip_usdc(self, usdc_token: Token) -> None:
        """Test lamports conversion round-trip for USDC."""
        original = Balance(token=usdc_token, amount=100.5)
        lamports = original.amount_in_lamports
        restored = Balance.from_lamports(token=usdc_token, lamports=lamports)
        assert restored.amount == original.amount


class TestBalanceSerialization:
    """Tests for Balance serialization and deserialization."""

    def test_balance_to_dict(self, sol_token: Token) -> None:
        """Test Balance.to_dict() returns correct structure."""
        balance = Balance(token=sol_token, amount=10.5)
        result = balance.to_dict()

        assert "token" in result
        assert "amount" in result
        assert result["amount"] == 10.5
        assert result["token"]["symbol"] == "SOL"

    def test_balance_from_dict(self, sol_token: Token) -> None:
        """Test Balance.from_dict() creates valid instance."""
        data = {
            "token": {"symbol": "SOL", "mint": "So1...", "decimals": 9, "name": "Solana"},
            "amount": 10.5,
        }
        balance = Balance.from_dict(data)

        assert balance.amount == 10.5
        assert balance.token.symbol == "SOL"
        assert balance.token.decimals == 9

    def test_balance_from_dict_missing_token_raises(self) -> None:
        """Test Balance.from_dict() raises KeyError when token is missing."""
        data = {"amount": 10.5}
        with pytest.raises(KeyError, match="token"):
            Balance.from_dict(data)

    def test_balance_from_dict_missing_amount_raises(self, sol_token: Token) -> None:
        """Test Balance.from_dict() raises KeyError when amount is missing."""
        data = {"token": sol_token.to_dict()}
        with pytest.raises(KeyError, match="amount"):
            Balance.from_dict(data)

    def test_balance_roundtrip_serialization(self, sol_token: Token) -> None:
        """Test Balance serialization and deserialization round-trip."""
        original = Balance(token=sol_token, amount=10.5)
        data = original.to_dict()
        restored = Balance.from_dict(data)

        assert restored == original
        assert restored.amount == original.amount
        assert restored.token == original.token


class TestBalanceImmutability:
    """Tests for Balance immutability."""

    def test_balance_is_frozen(self, sol_token: Token) -> None:
        """Test Balance dataclass is frozen (immutable)."""
        balance = Balance(token=sol_token, amount=10.5)

        with pytest.raises(AttributeError):
            balance.amount = 20.0  # type: ignore

    def test_balance_frozen_prevents_token_change(self, sol_token: Token) -> None:
        """Test Balance frozen prevents token modification."""
        balance = Balance(token=sol_token, amount=10.5)

        with pytest.raises(AttributeError):
            balance.token = Token(symbol="USDC", mint="EPj...", decimals=6)  # type: ignore


class TestBalanceEquality:
    """Tests for Balance equality comparisons."""

    def test_balance_equality_same_values(self, sol_token: Token) -> None:
        """Test two Balance instances with same values are equal."""
        balance1 = Balance(token=sol_token, amount=10.5)
        balance2 = Balance(token=sol_token, amount=10.5)
        assert balance1 == balance2

    def test_balance_equality_different_amounts(self, sol_token: Token) -> None:
        """Test two Balance instances with different amounts are not equal."""
        balance1 = Balance(token=sol_token, amount=10.5)
        balance2 = Balance(token=sol_token, amount=20.0)
        assert balance1 != balance2

    def test_balance_equality_different_tokens(self, sol_token: Token, usdc_token: Token) -> None:
        """Test two Balance instances with different tokens are not equal."""
        balance1 = Balance(token=sol_token, amount=10.5)
        balance2 = Balance(token=usdc_token, amount=10.5)
        assert balance1 != balance2


# =============================================================================
# Portfolio Tests
# =============================================================================


class TestPortfolioInstantiation:
    """Tests for Portfolio dataclass instantiation."""

    def test_portfolio_empty(self) -> None:
        """Test Portfolio creation with empty balances."""
        portfolio = Portfolio()
        assert portfolio.balances == {}
        assert portfolio.token_symbols == []
        assert portfolio.total_tokens == 0

    def test_portfolio_with_single_balance(self, sol_token: Token) -> None:
        """Test Portfolio creation with a single balance."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio = Portfolio(balances={"SOL": balance})

        assert portfolio.get_balance("SOL") == balance
        assert portfolio.get_balance("sol") == balance  # Case insensitive
        assert portfolio.get_balance("USDC") is None

    def test_portfolio_with_multiple_balances(self, sol_token: Token, usdc_token: Token) -> None:
        """Test Portfolio creation with multiple balances."""
        sol_balance = Balance(token=sol_token, amount=10.5)
        usdc_balance = Balance(token=usdc_token, amount=1000.0)
        portfolio = Portfolio(balances={"SOL": sol_balance, "USDC": usdc_balance})

        assert portfolio.get_balance("SOL") == sol_balance
        assert portfolio.get_balance("USDC") == usdc_balance
        assert portfolio.total_tokens == 2


class TestPortfolioMethods:
    """Tests for Portfolio methods."""

    def test_get_balance_missing_token(self, sol_token: Token) -> None:
        """Test Portfolio.get_balance() returns None for missing token."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio = Portfolio(balances={"SOL": balance})

        assert portfolio.get_balance("BTC") is None
        assert portfolio.get_balance("") is None

    def test_get_balance_case_insensitive(self, sol_token: Token) -> None:
        """Test Portfolio.get_balance() is case insensitive."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio = Portfolio(balances={"SOL": balance})

        assert portfolio.get_balance("sol") == balance
        assert portfolio.get_balance("Sol") == balance
        assert portfolio.get_balance("SOL") == balance

    def test_total_value_empty_portfolio(self) -> None:
        """Test Portfolio.total_value() with empty portfolio."""
        portfolio = Portfolio()
        price_map = {"SOL": Price(value=150.50, timestamp=datetime.now(), currency="USD")}
        assert portfolio.total_value(price_map) == 0.0

    def test_total_value_single_token(self, sol_token: Token) -> None:
        """Test Portfolio.total_value() with single token."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio = Portfolio(balances={"SOL": balance})
        price_map = {"SOL": Price(value=150.50, timestamp=datetime.now(), currency="USD")}

        # 10.5 SOL * 150.50 USD/SOL = 1580.25 USD
        assert portfolio.total_value(price_map) == pytest.approx(10.5 * 150.50)

    def test_total_value_multiple_tokens(self, sol_token: Token, usdc_token: Token) -> None:
        """Test Portfolio.total_value() with multiple tokens."""
        sol_balance = Balance(token=sol_token, amount=10.0)
        usdc_balance = Balance(token=usdc_token, amount=1000.0)
        portfolio = Portfolio(balances={"SOL": sol_balance, "USDC": usdc_balance})
        
        price_map = {
            "SOL": Price(value=150.50, timestamp=datetime.now(), currency="USD"),
            "USDC": Price(value=1.00, timestamp=datetime.now(), currency="USD"),
        }

        # 10 SOL * 150.50 + 1000 USDC * 1.00 = 1505 + 1000 = 2505 USD
        expected = 10.0 * 150.50 + 1000.0 * 1.00
        assert portfolio.total_value(price_map) == pytest.approx(expected)

    def test_total_value_missing_price(self, sol_token: Token) -> None:
        """Test Portfolio.total_value() with missing price in price_map."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio = Portfolio(balances={"SOL": balance})
        price_map = {}  # No SOL price
        
        assert portfolio.total_value(price_map) == 0.0

    def test_total_value_partial_price_map(self, sol_token: Token, usdc_token: Token) -> None:
        """Test Portfolio.total_value() with partial price_map."""
        sol_balance = Balance(token=sol_token, amount=10.0)
        usdc_balance = Balance(token=usdc_token, amount=1000.0)
        portfolio = Portfolio(balances={"SOL": sol_balance, "USDC": usdc_balance})
        
        price_map = {
            "SOL": Price(value=150.50, timestamp=datetime.now(), currency="USD"),
            # USDC price missing
        }

        # Only SOL value counted
        assert portfolio.total_value(price_map) == pytest.approx(10.0 * 150.50)

    def test_add_balance_new_token(self, sol_token: Token) -> None:
        """Test Portfolio.add_balance() adds a new token."""
        portfolio = Portfolio()
        balance = Balance(token=sol_token, amount=10.5)
        
        new_portfolio = portfolio.add_balance(balance)
        
        assert new_portfolio.get_balance("SOL") == balance
        assert portfolio.get_balance("SOL") is None  # Original unchanged

    def test_add_balance_update_existing(self, sol_token: Token) -> None:
        """Test Portfolio.add_balance() updates existing token."""
        balance1 = Balance(token=sol_token, amount=10.0)
        portfolio = Portfolio(balances={"SOL": balance1})
        
        balance2 = Balance(token=sol_token, amount=20.0)
        new_portfolio = portfolio.add_balance(balance2)
        
        assert new_portfolio.get_balance("SOL") == balance2
        assert portfolio.get_balance("SOL") == balance1  # Original unchanged

    def test_remove_balance_existing(self, sol_token: Token) -> None:
        """Test Portfolio.remove_balance() removes existing token."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio = Portfolio(balances={"SOL": balance})
        
        new_portfolio = portfolio.remove_balance("SOL")
        
        assert new_portfolio.get_balance("SOL") is None
        assert portfolio.get_balance("SOL") == balance  # Original unchanged

    def test_remove_balance_missing(self, sol_token: Token) -> None:
        """Test Portfolio.remove_balance() handles missing token gracefully."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio = Portfolio(balances={"SOL": balance})
        
        new_portfolio = portfolio.remove_balance("BTC")
        
        # No error, portfolio unchanged
        assert new_portfolio.get_balance("SOL") == balance


class TestPortfolioProperties:
    """Tests for Portfolio properties."""

    def test_token_symbols_empty(self) -> None:
        """Test Portfolio.token_symbols with empty portfolio."""
        portfolio = Portfolio()
        assert portfolio.token_symbols == []

    def test_token_symbols_with_balances(self, sol_token: Token, usdc_token: Token) -> None:
        """Test Portfolio.token_symbols returns all symbols."""
        portfolio = Portfolio(balances={
            "SOL": Balance(token=sol_token, amount=10.0),
            "USDC": Balance(token=usdc_token, amount=1000.0),
        })
        symbols = portfolio.token_symbols
        assert "SOL" in symbols
        assert "USDC" in symbols

    def test_total_tokens_empty(self) -> None:
        """Test Portfolio.total_tokens with empty portfolio."""
        portfolio = Portfolio()
        assert portfolio.total_tokens == 0

    def test_total_tokens_with_balances(self, sol_token: Token, usdc_token: Token) -> None:
        """Test Portfolio.total_tokens counts unique tokens."""
        portfolio = Portfolio(balances={
            "SOL": Balance(token=sol_token, amount=10.0),
            "USDC": Balance(token=usdc_token, amount=1000.0),
        })
        assert portfolio.total_tokens == 2


class TestPortfolioSerialization:
    """Tests for Portfolio serialization and deserialization."""

    def test_portfolio_to_dict_empty(self) -> None:
        """Test empty Portfolio.to_dict()."""
        portfolio = Portfolio()
        result = portfolio.to_dict()

        assert "balances" in result
        assert result["balances"] == {}

    def test_portfolio_to_dict_with_balances(self, sol_token: Token) -> None:
        """Test Portfolio.to_dict() with balances."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio = Portfolio(balances={"SOL": balance})
        result = portfolio.to_dict()

        assert "balances" in result
        assert "SOL" in result["balances"]
        assert result["balances"]["SOL"]["amount"] == 10.5

    def test_portfolio_from_dict_empty(self) -> None:
        """Test Portfolio.from_dict() with empty balances."""
        data = {"balances": {}}
        portfolio = Portfolio.from_dict(data)

        assert portfolio.balances == {}

    def test_portfolio_from_dict_with_balances(self, sol_token: Token) -> None:
        """Test Portfolio.from_dict() with balances."""
        data = {
            "balances": {
                "SOL": {
                    "token": {"symbol": "SOL", "mint": "So1...", "decimals": 9},
                    "amount": 10.5,
                }
            }
        }
        portfolio = Portfolio.from_dict(data)

        assert portfolio.get_balance("SOL") is not None
        assert portfolio.get_balance("SOL").amount == 10.5

    def test_portfolio_from_dict_multiple_balances(self, sol_token: Token, usdc_token: Token) -> None:
        """Test Portfolio.from_dict() with multiple balances."""
        data = {
            "balances": {
                "SOL": {
                    "token": {"symbol": "SOL", "mint": "So1...", "decimals": 9},
                    "amount": 10.5,
                },
                "USDC": {
                    "token": {"symbol": "USDC", "mint": "EPj...", "decimals": 6},
                    "amount": 1000.0,
                }
            }
        }
        portfolio = Portfolio.from_dict(data)

        assert portfolio.get_balance("SOL") is not None
        assert portfolio.get_balance("SOL").amount == 10.5
        assert portfolio.get_balance("USDC") is not None
        assert portfolio.get_balance("USDC").amount == 1000.0

    def test_portfolio_roundtrip_serialization(self, sol_token: Token, usdc_token: Token) -> None:
        """Test Portfolio serialization and deserialization round-trip."""
        original = Portfolio(balances={
            "SOL": Balance(token=sol_token, amount=10.5),
            "USDC": Balance(token=usdc_token, amount=1000.0),
        })

        data = original.to_dict()
        restored = Portfolio.from_dict(data)

        assert restored == original


class TestPortfolioImmutability:
    """Tests for Portfolio immutability."""

    def test_portfolio_is_frozen(self, sol_token: Token) -> None:
        """Test Portfolio dataclass is frozen (immutable)."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio = Portfolio(balances={"SOL": balance})

        with pytest.raises(AttributeError):
            portfolio.balances = {}  # type: ignore

    def test_add_balance_returns_new_instance(self, sol_token: Token) -> None:
        """Test Portfolio.add_balance() returns new instance."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio1 = Portfolio()
        portfolio2 = portfolio1.add_balance(balance)

        assert portfolio1 is not portfolio2
        assert portfolio1 != portfolio2

    def test_remove_balance_returns_new_instance(self, sol_token: Token) -> None:
        """Test Portfolio.remove_balance() returns new instance."""
        balance = Balance(token=sol_token, amount=10.5)
        portfolio1 = Portfolio(balances={"SOL": balance})
        portfolio2 = portfolio1.remove_balance("SOL")

        assert portfolio1 is not portfolio2
        assert portfolio1 != portfolio2


class TestApplyTrade:
    """Tests for Portfolio.apply_trade() method."""

    def test_apply_trade_simple_object(self, sol_token: Token) -> None:
        """Test apply_trade with a simple object having required attributes."""
        balance = Balance(token=sol_token, amount=10.0)
        portfolio = Portfolio(balances={"SOL": balance})
        
        # Simple trade object
        class SimpleTrade:
            token_symbol = "SOL"
            amount = 5.0
        
        trade = SimpleTrade()
        new_portfolio = portfolio.apply_trade(trade)
        
        # SOL balance should be updated: 10.0 + 5.0 = 15.0
        assert new_portfolio.get_balance("SOL") is not None
        assert new_portfolio.get_balance("SOL").amount == pytest.approx(15.0)
        # Original portfolio unchanged
        assert portfolio.get_balance("SOL").amount == 10.0

    def test_apply_trade_sell(self, sol_token: Token) -> None:
        """Test apply_trade with sell (negative amount)."""
        balance = Balance(token=sol_token, amount=10.0)
        portfolio = Portfolio(balances={"SOL": balance})
        
        class SimpleTrade:
            token_symbol = "SOL"
            amount = -2.5  # Sell 2.5 SOL
        
        trade = SimpleTrade()
        new_portfolio = portfolio.apply_trade(trade)
        
        # SOL balance should be: 10.0 - 2.5 = 7.5
        assert new_portfolio.get_balance("SOL").amount == pytest.approx(7.5)

    def test_apply_trade_missing_token_symbol_raises(self, sol_token: Token) -> None:
        """Test apply_trade raises ValueError when trade missing token_symbol."""
        balance = Balance(token=sol_token, amount=10.0)
        portfolio = Portfolio(balances={"SOL": balance})
        
        class InvalidTrade:
            amount = 5.0
            # Missing token_symbol
        
        trade = InvalidTrade()
        with pytest.raises(ValueError, match="token_symbol"):
            portfolio.apply_trade(trade)

    def test_apply_trade_missing_amount_raises(self, sol_token: Token) -> None:
        """Test apply_trade raises ValueError when trade missing amount."""
        balance = Balance(token=sol_token, amount=10.0)
        portfolio = Portfolio(balances={"SOL": balance})
        
        class InvalidTrade:
            token_symbol = "SOL"
            # Missing amount
        
        trade = InvalidTrade()
        with pytest.raises(ValueError, match="amount"):
            portfolio.apply_trade(trade)

    def test_apply_trade_new_token_raises(self, sol_token: Token) -> None:
        """Test apply_trade raises NotImplementedError for new tokens."""
        portfolio = Portfolio(balances={"SOL": Balance(token=sol_token, amount=10.0)})
        
        class Trade:
            token_symbol = "BTC"  # Not in portfolio
            amount = 5.0
        
        trade = Trade()
        with pytest.raises(NotImplementedError, match="Cannot add new token"):
            portfolio.apply_trade(trade)


class TestBalancePortfolioIntegration:
    """Integration tests for Balance and Portfolio."""

    def test_portfolio_from_balances_list(self, sol_token: Token, usdc_token: Token) -> None:
        """Test building Portfolio from a list of Balance objects."""
        balances = [
            Balance(token=sol_token, amount=10.0),
            Balance(token=usdc_token, amount=1000.0),
        ]
        
        portfolio = Portfolio()
        for balance in balances:
            portfolio = portfolio.add_balance(balance)
        
        assert portfolio.total_tokens == 2
        assert portfolio.get_balance("SOL").amount == 10.0
        assert portfolio.get_balance("USDC").amount == 1000.0

    def test_portfolio_value_with_price_map_fixture(self, sol_token: Token, usdc_token: Token, price_map: Dict[str, Price]) -> None:
        """Test portfolio valuation using fixture price_map."""
        portfolio = Portfolio(balances={
            "SOL": Balance(token=sol_token, amount=10.0),
            "USDC": Balance(token=usdc_token, amount=1000.0),
        })
        
        total = portfolio.total_value(price_map)
        expected = 10.0 * 150.50 + 1000.0 * 1.00
        assert total == pytest.approx(expected)
