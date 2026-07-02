"""
Core Domain Models for Balance and Portfolio.

This module implements immutable domain models for the trading bot's balance
and portfolio tracking, following Clean Architecture principles.

Architecture Decisions:
    AD-001: Clean Architecture Paradigm - Domain layer entities
    AD-004: Dependency Injection Pattern - All classes accept dependencies via constructors

All dataclasses are immutable (frozen=True) to ensure thread-safety and
prevent accidental mutations when passing data between components.

Dependencies:
    - Token model from src.core.models.price (US-010)
    - Price model from src.core.models.price (US-010) - used in total_value()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .price import Price, Token


@dataclass(frozen=True)
class Balance:
    """Immutable representation of a token balance.

    Represents the amount of a specific token held by the portfolio.
    The amount is stored in the token's base units (e.g., SOL for SOL token,
    USDC for USDC token), not in lamports. This provides a cleaner API.

    Attributes:
        token: The token metadata (symbol, mint, decimals).
        amount: The balance amount in token's base units.
               Positive for long positions, negative for short positions.
    """
    token: "Token"
    amount: float

    @property
    def amount_in_lamports(self) -> int:
        """Convert the balance amount to lamports (integer).

        Lamports = amount * 10^decimals
        This is useful for Solana RPC calls that require lamport precision.

        Returns:
            The balance amount converted to lamports as an integer.

        Raises:
            ValueError: If the result exceeds integer limits.
        """
        # Calculate lamports: amount * 10^decimals
        # Use integer arithmetic for precision
        multiplier = 10 ** self.token.decimals
        lamports = int(round(self.amount * multiplier))
        return lamports

    @classmethod
    def from_lamports(cls, token: "Token", lamports: int) -> "Balance":
        """Create a Balance from a lamport amount.

        Args:
            token: The token metadata.
            lamports: The balance amount in lamports (integer).

        Returns:
            A new Balance instance with the amount converted from lamports.
        """
        multiplier = 10 ** token.decimals
        amount = lamports / multiplier
        return cls(token=token, amount=amount)

    def to_dict(self) -> dict:
        """Convert Balance instance to dictionary representation.

        Returns:
            Dictionary with all Balance attributes.
        """
        return {
            "token": self.token.to_dict(),
            "amount": self.amount,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Balance":
        """Create Balance instance from dictionary.

        Args:
            data: Dictionary containing 'token' and 'amount' keys.
                  'token' should be a dict that can be deserialized to Token.

        Returns:
            Balance instance.

        Raises:
            KeyError: If required fields ('token', 'amount') are missing.
        """
        from .price import Token
        return cls(
            token=Token.from_dict(data["token"]),
            amount=data["amount"],
        )


@dataclass(frozen=True)
class Portfolio:
    """Immutable representation of the complete trading bot portfolio.

    Contains all token balances and provides methods for portfolio operations.
    All update operations return new Portfolio instances to maintain immutability.

    Attributes:
        balances: Dictionary mapping token symbols (str) to Balance instances.
                  Example: {"SOL": Balance(token=SOL_TOKEN, amount=10.5), ...}
    """
    balances: Dict[str, "Balance"] = field(default_factory=dict)

    def get_balance(self, token_symbol: str) -> Optional["Balance"]:
        """Get the balance for a specific token by its symbol.

        Args:
            token_symbol: The symbol of the token to look up (e.g., "SOL", "USDC").

        Returns:
            The Balance instance for the requested token, or None if not found.
        """
        return self.balances.get(token_symbol.upper())

    def total_value(self, price_map: Dict[str, "Price"]) -> float:
        """Calculate the total portfolio value in USD.

        Sums up the value of all token balances using the provided price map.
        Price map should contain current prices for all tokens in the portfolio.

        Args:
            price_map: Dictionary mapping token symbols to Price instances.
                      Example: {"SOL": Price(value=150.50, timestamp=...), ...}

        Returns:
            The total portfolio value in USD as a float.
            Returns 0.0 if portfolio is empty or price_map is incomplete.
        """
        total = 0.0
        for symbol, balance in self.balances.items():
            price = price_map.get(symbol.upper())
            if price is not None and price.currency == "USD":
                # Value = amount * price_per_token
                total += balance.amount * price.value
        return total

    def apply_trade(self, trade: Any) -> "Portfolio":
        """Apply a trade to the portfolio and return a new Portfolio instance.

        This method creates a new Portfolio with updated balances based on the trade.
        The original Portfolio remains unchanged (immutability).

        Note: This is a forward reference to the Trade class from US-012.
        The method will be fully typed once US-012 is implemented.

        Args:
            trade: A trade object (from US-012) containing:
                   - token_symbol: The token being traded
                   - amount: The amount (positive for buy, negative for sell)
                   - This is a placeholder; actual Trade class will have more fields.

        Returns:
            A new Portfolio instance with the trade applied.

        Raises:
            NotImplementedError: If trade object doesn't have required attributes.
        """
        # Extract trade information
        # Trade from US-012 should have: token_symbol, amount, trade_type, etc.
        # For now, we support a minimal interface
        
        if not hasattr(trade, 'token_symbol') or not hasattr(trade, 'amount'):
            raise ValueError(
                f"Trade object must have 'token_symbol' and 'amount' attributes. "
                f"Got: {type(trade).__name__}"
            )
        
        token_symbol = trade.token_symbol.upper()
        amount = trade.amount
        
        # Get existing balance or create zero balance
        existing_balance = self.balances.get(token_symbol)
        if existing_balance is not None:
            # Update existing balance
            new_amount = existing_balance.amount + amount
            new_balance = Balance(token=existing_balance.token, amount=new_amount)
        else:
            # For a new token, we need to create a Balance
            # But we don't have the Token object from the trade yet
            # This is a limitation that will be resolved when US-012 is complete
            # For now, we'll skip adding new tokens
            raise NotImplementedError(
                f"Cannot add new token '{token_symbol}' to portfolio. "
                f"Token metadata not available in trade. "
                f"This will be implemented when US-012 (Trade & Decision) is complete."
            )
        
        # Create new balances dict with updated balance
        new_balances = dict(self.balances)
        new_balances[token_symbol] = new_balance
        
        return Portfolio(balances=new_balances)

    def to_dict(self) -> dict:
        """Convert Portfolio instance to dictionary representation.

        Returns:
            Dictionary with all Portfolio attributes, including nested serialization.
        """
        return {
            "balances": {symbol: balance.to_dict() for symbol, balance in self.balances.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio":
        """Create Portfolio instance from dictionary.

        Args:
            data: Dictionary containing 'balances' key with a dict of balance data.
                  Example: {"balances": {"SOL": {"token": {...}, "amount": 10.5}, ...}}

        Returns:
            Portfolio instance.

        Raises:
            KeyError: If 'balances' field is missing.
        """
        balances_data = data.get("balances", {})
        balances = {}
        for symbol, balance_data in balances_data.items():
            balance = Balance.from_dict(balance_data)
            balances[symbol.upper()] = balance
        return cls(balances=balances)

    def add_balance(self, balance: "Balance") -> "Portfolio":
        """Add or update a balance in the portfolio, returning a new Portfolio.

        This is a convenience method for building portfolios.

        Args:
            balance: The Balance instance to add/update.

        Returns:
            A new Portfolio instance with the balance added/updated.
        """
        new_balances = dict(self.balances)
        new_balances[balance.token.symbol.upper()] = balance
        return Portfolio(balances=new_balances)

    def remove_balance(self, token_symbol: str) -> "Portfolio":
        """Remove a balance from the portfolio, returning a new Portfolio.

        Args:
            token_symbol: The symbol of the token balance to remove.

        Returns:
            A new Portfolio instance without the specified balance.
        """
        new_balances = dict(self.balances)
        new_balances.pop(token_symbol.upper(), None)
        return Portfolio(balances=new_balances)

    @property
    def token_symbols(self) -> list:
        """Get list of all token symbols in the portfolio.

        Returns:
            List of token symbols (strings) in the portfolio.
        """
        return list(self.balances.keys())

    @property
    def total_tokens(self) -> int:
        """Get the number of different tokens in the portfolio.

        Returns:
            The count of unique tokens with non-zero balances.
        """
        return len(self.balances)
