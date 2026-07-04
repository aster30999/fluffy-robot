# Solana Trading Bot
# Core package initialization
"""
Solana Trading Bot - Main package

This package contains the core trading engine, technical indicators,
decision engine, and risk management components for automated
Solana-based cryptocurrency trading.
"""

# Load environment variables from .env file
from src.utils.load_env import *

__version__ = "0.1.0"
__author__ = "asteroid"
__description__ = "Personal Solana Trading Bot"

# Export main classes for easy access
from src.cli import TradingBot, TradingBotError, NetworkValidationError
from src.config.trading_config import TradingConfig, TradingBotServices, ConfigurationError

__all__ = [
    "TradingBot",
    "TradingConfig",
    "TradingBotServices",
    "TradingBotError",
    "NetworkValidationError",
    "ConfigurationError",
]