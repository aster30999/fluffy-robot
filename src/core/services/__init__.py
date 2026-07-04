"""
Core Application Services

Services layer implementing business logic and orchestration between
domain entities and external services, following Clean Architecture principles.

Architecture Decisions:
    AD-001: Clean Architecture Paradigm - Application services layer
    AD-004: Dependency Injection Pattern - All services accept dependencies via constructors

Services are stateless where possible and use dependency injection for all
external dependencies (infrastructure clients, repositories, etc.).
"""

__version__ = "0.1.0"

# Price Fetcher Service (US-013)
from .price_fetcher import PriceFetcher, PriceFetchError, RateLimitError

# Balance Tracker Service (US-014)
from .balance_tracker import BalanceTracker, BalanceTrackError, TokenNotFoundError

# Trade Executor Service (US-015)
from .trade_executor import (
    TradeExecutor,
    TradeExecutionError,
    InsufficientFundsError,
    SlippageError,
    TransactionTimeoutError,
    SwapQuote,
)

__all__ = [
    # US-013 Services
    "PriceFetcher",
    "PriceFetchError",
    "RateLimitError",
    # US-014 Services
    "BalanceTracker",
    "BalanceTrackError",
    "TokenNotFoundError",
    # US-015 Services
    "TradeExecutor",
    "TradeExecutionError",
    "InsufficientFundsError",
    "SlippageError",
    "TransactionTimeoutError",
    "SwapQuote",
]
