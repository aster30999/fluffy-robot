"""
Trading Bot Configuration

Configuration classes for the trading bot.
Uses dataclasses for simple, type-safe configuration management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.models.price import TokenPair


@dataclass
class TradingConfig:
    """Configuration for the trading bot.
    
    Main configuration class that holds all trading parameters.
    Can be created from code or loaded from environment/config files.
    
    Attributes:
        pairs: List of token pairs to trade
        interval: Seconds between trading cycles (default: 60 = 1 minute)
        network: Solana network ("devnet" or "mainnet-beta") (default: "devnet")
        dry_run: Enable dry-run mode (no real trades) (default: True for safety)
        log_level: Logging level (default: "INFO")
        data_dir: Directory for persistent data (default: "./data")
        jupiter_api_key: Optional Jupiter API key
        max_concurrent_trades: Maximum concurrent trades (default: 1 for safety)
    """
    pairs: list["TokenPair"] = field(default_factory=list)
    interval: float = 60.0  # Default: 1 minute
    network: str = "devnet"
    dry_run: bool = True  # Default to dry-run for safety
    log_level: str = "INFO"
    data_dir: str = "./data"
    jupiter_api_key: Optional[str] = None
    max_concurrent_trades: int = 1
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate network
        if self.network not in ["devnet", "mainnet-beta"]:
            raise ValueError(
                f"Invalid network: {self.network}. "
                f"Must be one of: devnet, mainnet-beta"
            )
        
        # Validate interval
        if self.interval <= 0:
            raise ValueError(f"Interval must be positive, got: {self.interval}")
        
        # Validate log_level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(
                f"Invalid log_level: {self.log_level}. "
                f"Must be one of: {valid_log_levels}"
            )
        
        # Validate max_concurrent_trades
        if self.max_concurrent_trades < 1:
            raise ValueError(
                f"max_concurrent_trades must be at least 1, got: {self.max_concurrent_trades}"
            )


@dataclass
class TradingBotServices:
    """Aggregated services for the TradingBot.
    
    Holds all the service instances that the TradingBot needs.
    Uses lazy initialization to avoid circular imports.
    
    Attributes:
        price_fetcher: PriceFetcher service for fetching prices
        balance_tracker: BalanceTracker service for tracking portfolio
        trade_executor: TradeExecutor service for executing trades
        solana_client: SolanaClient for Solana RPC operations
        jupiter_client: JupiterClient for Jupiter API operations
        wallet: Wallet for transaction signing
    """
    price_fetcher: Optional[any] = None  # PriceFetcher
    balance_tracker: Optional[any] = None  # BalanceTracker
    trade_executor: Optional[any] = None  # TradeExecutor
    solana_client: Optional[any] = None  # SolanaClient
    jupiter_client: Optional[any] = None  # JupiterClient
    wallet: Optional[any] = None  # Wallet
    portfolio: Optional[any] = None  # Portfolio


class TradingBotError(Exception):
    """Base exception for trading bot errors."""
    pass


class NetworkValidationError(TradingBotError):
    """Raised when network validation fails."""
    pass


class ConfigurationError(TradingBotError):
    """Raised when configuration is invalid."""
    pass
