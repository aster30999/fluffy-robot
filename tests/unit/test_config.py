"""
Unit tests for Trading Bot Configuration

Tests the TradingConfig and TradingBotServices dataclasses.
"""

import pytest
from dataclasses import dataclass
from src.config.trading_config import TradingConfig, TradingBotServices, ConfigurationError
from src.core.models.price import Token, TokenPair


class TestTradingConfig:
    """Tests for TradingConfig dataclass."""

    def test_default_values(self):
        """Test TradingConfig with default values."""
        config = TradingConfig()
        
        assert config.pairs == []
        assert config.interval == 60.0
        assert config.network == "devnet"
        assert config.dry_run is True
        assert config.log_level == "INFO"
        assert config.data_dir == "./data"
        assert config.jupiter_api_key is None
        assert config.max_concurrent_trades == 1

    def test_custom_values(self):
        """Test TradingConfig with custom values."""
        pairs = [
            TokenPair(
                base=Token(symbol="SOL", mint="So11111111111111111111111111111111111111112", decimals=9),
                quote=Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)
            )
        ]
        
        config = TradingConfig(
            pairs=pairs,
            interval=30.0,
            network="mainnet-beta",
            dry_run=False,
            log_level="DEBUG",
            data_dir="/tmp/data",
            jupiter_api_key="test_key",
            max_concurrent_trades=5
        )
        
        assert config.pairs == pairs
        assert config.interval == 30.0
        assert config.network == "mainnet-beta"
        assert config.dry_run is False
        assert config.log_level == "DEBUG"
        assert config.data_dir == "/tmp/data"
        assert config.jupiter_api_key == "test_key"
        assert config.max_concurrent_trades == 5

    def test_invalid_network_raises_error(self):
        """Test that invalid network raises ConfigurationError."""
        with pytest.raises(ValueError) as exc_info:
            TradingConfig(network="invalid_network")
        
        assert "Invalid network" in str(exc_info.value)
        assert "devnet, mainnet-beta" in str(exc_info.value)

    def test_invalid_interval_raises_error(self):
        """Test that non-positive interval raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TradingConfig(interval=-1.0)
        
        assert "Interval must be positive" in str(exc_info.value)

    def test_invalid_log_level_raises_error(self):
        """Test that invalid log level raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TradingConfig(log_level="INVALID")
        
        assert "Invalid log_level" in str(exc_info.value)

    def test_invalid_max_concurrent_trades_raises_error(self):
        """Test that max_concurrent_trades < 1 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TradingConfig(max_concurrent_trades=0)
        
        assert "max_concurrent_trades must be at least 1" in str(exc_info.value)

    def test_zero_interval_raises_error(self):
        """Test that zero interval raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TradingConfig(interval=0)
        
        assert "Interval must be positive" in str(exc_info.value)

    def test_valid_mainnet_network(self):
        """Test that mainnet-beta is a valid network."""
        config = TradingConfig(network="mainnet-beta")
        assert config.network == "mainnet-beta"

    def test_valid_log_levels(self):
        """Test all valid log levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            config = TradingConfig(log_level=level)
            assert config.log_level == level


class TestTradingBotServices:
    """Tests for TradingBotServices dataclass."""

    def test_default_values_are_none(self):
        """Test TradingBotServices with default values."""
        services = TradingBotServices()
        
        assert services.price_fetcher is None
        assert services.balance_tracker is None
        assert services.trade_executor is None
        assert services.solana_client is None
        assert services.jupiter_client is None
        assert services.wallet is None
        assert services.portfolio is None

    def test_custom_values(self):
        """Test TradingBotServices with custom service instances."""
        class MockService:
            pass
        
        mock_price_fetcher = MockService()
        mock_balance_tracker = MockService()
        mock_trade_executor = MockService()
        mock_solana_client = MockService()
        mock_jupiter_client = MockService()
        mock_wallet = MockService()
        mock_portfolio = MockService()
        
        services = TradingBotServices(
            price_fetcher=mock_price_fetcher,
            balance_tracker=mock_balance_tracker,
            trade_executor=mock_trade_executor,
            solana_client=mock_solana_client,
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            portfolio=mock_portfolio
        )
        
        assert services.price_fetcher is mock_price_fetcher
        assert services.balance_tracker is mock_balance_tracker
        assert services.trade_executor is mock_trade_executor
        assert services.solana_client is mock_solana_client
        assert services.jupiter_client is mock_jupiter_client
        assert services.wallet is mock_wallet
        assert services.portfolio is mock_portfolio


class TestExceptionClasses:
    """Tests for custom exception classes."""

    def test_trading_bot_error_hierarchy(self):
        """Test exception class hierarchy."""
        from src.config.trading_config import TradingBotError, NetworkValidationError, ConfigurationError
        
        # All should be subclasses of Exception
        assert issubclass(TradingBotError, Exception)
        assert issubclass(NetworkValidationError, TradingBotError)
        assert issubclass(ConfigurationError, TradingBotError)

    def test_exception_instantiation(self):
        """Test that exceptions can be instantiated."""
        from src.config.trading_config import TradingBotError, NetworkValidationError, ConfigurationError
        
        error1 = TradingBotError("test error")
        assert str(error1) == "test error"
        
        error2 = NetworkValidationError("network error")
        assert str(error2) == "network error"
        assert isinstance(error2, TradingBotError)
        
        error3 = ConfigurationError("config error")
        assert str(error3) == "config error"
        assert isinstance(error3, TradingBotError)
