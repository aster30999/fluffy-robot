"""
Configuration

Project configuration and settings management.

Contains:
- settings: Main configuration settings
- config_loader: Load configuration from files/env
- validation: Configuration validation
- trading_config: Trading bot specific configuration (TradingConfig, TradingBotServices)
"""

__version__ = "0.1.0"

# Export trading configuration classes
from src.config.trading_config import (
    TradingConfig,
    TradingBotServices,
    TradingBotError,
    NetworkValidationError,
    ConfigurationError,
)

__all__ = [
    "TradingConfig",
    "TradingBotServices",
    "TradingBotError",
    "NetworkValidationError",
    "ConfigurationError",
]
