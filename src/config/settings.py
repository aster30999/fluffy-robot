"""
Application Settings

Pydantic models for configuration management.
Uses environment variables with sensible defaults.
"""

from typing import List, Optional, Dict, Any
try:
    # Pydantic v2
    from pydantic_settings import BaseSettings
    from pydantic import validator, Field, SecretStr
    import logging
    PYDANTIC_V2 = True
except ImportError:
    try:
        # Pydantic v1
        from pydantic import BaseSettings, validator, Field, SecretStr
        import logging
        PYDANTIC_V2 = False
    except ImportError:
        raise ImportError("Neither pydantic v1 nor v2 with pydantic-settings is installed")


class SolanaSettings(BaseSettings):
    """Solana blockchain configuration."""
    
    # RPC Configuration
    solana_rpc_url: str = Field(
        default="https://api.devnet.solana.com",
        env="SOLANA_RPC_URL"
    )
    
    # Network configuration
    network: str = Field(
        default="devnet",
        env="NETWORK"
    )
    
    # Wallet configuration
    wallet_private_key: Optional[SecretStr] = Field(
        default=None,
        env="WALLET_PRIVATE_KEY"
    )
    
    wallet_keypair_path: Optional[str] = Field(
        default=None,
        env="WALLET_KEYPAIR_PATH"
    )
    
    @validator('network')
    def validate_network(cls, v):
        """Validate network is one of the allowed values."""
        allowed_networks = ['devnet', 'testnet', 'mainnet-beta', 'mainnet', 'localnet']
        if v not in allowed_networks:
            raise ValueError(f'Network must be one of {allowed_networks}')
        return v
    
    @validator('solana_rpc_url')
    def validate_devnet_only(cls, v, values):
        """Ensure Devnet RPC URL is used when in devnet mode."""
        if values.get('network') == 'devnet':
            if 'devnet' not in v.lower() and 'localhost' not in v.lower():
                logging.warning(
                    f"Devnet mode selected but RPC URL '{v}' does not appear to be Devnet. "
                    f"Consider using 'https://api.devnet.solana.com'"
                )
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class JupiterSettings(BaseSettings):
    """Jupiter API configuration."""
    
    jupiter_api_key: Optional[SecretStr] = Field(
        default=None,
        env="JUPITER_API_KEY"
    )
    
    jupiter_api_url: str = Field(
        default="https://quote-api.jup.ag",
        env="JUPITER_API_URL"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class TradingSettings(BaseSettings):
    """Trading configuration."""
    
    trading_interval: int = Field(
        default=60,
        env="TRADING_INTERVAL",
        ge=1,
        le=86400
    )
    
    default_swap_amount: float = Field(
        default=0.01,
        env="DEFAULT_SWAP_AMOUNT",
        gt=0
    )
    
    max_portfolio_risk: float = Field(
        default=0.01,
        env="MAX_PORTFOLIO_RISK",
        ge=0,
        le=1
    )
    
    slippage_tolerance: float = Field(
        default=0.01,
        env="SLIPPAGE_TOLERANCE",
        ge=0,
        le=1
    )
    
    trading_pairs: List[str] = Field(
        default_factory=lambda: ["SOL-USDC"],
        env="TRADING_PAIRS"
    )
    
    @validator('trading_pairs', pre=True)
    def parse_trading_pairs(cls, v):
        """Parse comma-separated trading pairs."""
        if isinstance(v, str):
            return [pair.strip() for pair in v.split(',') if pair.strip()]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class RiskManagementSettings(BaseSettings):
    """Risk management configuration."""
    
    stop_loss_percentage: float = Field(
        default=0.05,
        env="STOP_LOSS_PERCENTAGE",
        ge=0,
        le=1
    )
    
    take_profit_percentage: float = Field(
        default=0.10,
        env="TAKE_PROFIT_PERCENTAGE",
        ge=0,
        le=1
    )
    
    max_open_trades: int = Field(
        default=5,
        env="MAX_OPEN_TRADES",
        ge=1,
        le=100
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL"
    )
    
    log_format: str = Field(
        default="text",
        env="LOG_FORMAT"
    )
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    @validator('log_format')
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = ['text', 'json']
        if v.lower() not in valid_formats:
            raise ValueError(f'Log format must be one of {valid_formats}')
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    db_type: str = Field(
        default="sqlite",
        env="DB_TYPE"
    )
    
    db_path: str = Field(
        default="./data/trading_bot.db",
        env="DB_PATH"
    )
    
    @validator('db_type')
    def validate_db_type(cls, v):
        """Validate database type."""
        valid_types = ['sqlite', 'postgres']
        if v.lower() not in valid_types:
            raise ValueError(f'DB type must be one of {valid_types}')
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class MonitoringSettings(BaseSettings):
    """Monitoring configuration."""
    
    metrics_enabled: bool = Field(
        default=False,
        env="METRICS_ENABLED"
    )
    
    metrics_port: int = Field(
        default=9090,
        env="METRICS_PORT",
        ge=1024,
        le=65535
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(
    SolanaSettings,
    JupiterSettings,
    TradingSettings,
    RiskManagementSettings,
    LoggingSettings,
    DatabaseSettings,
    MonitoringSettings
):
    """
    Main application settings.
    Combines all configuration sections.
    """
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()


def validate_devnet_configuration():
    """
    Validate that Devnet-only configuration is being used when in devnet mode.
    This is called at startup to prevent accidental mainnet usage during development.
    """
    if settings.network == "devnet":
        if "devnet" not in settings.solana_rpc_url.lower() and "localhost" not in settings.solana_rpc_url.lower():
            raise ValueError(
                f"Devnet mode selected but RPC URL '{settings.solana_rpc_url}' "
                f"does not appear to be Devnet. For development, use 'https://api.devnet.solana.com' "
                f"or set NETWORK=mainnet for production."
            )
    
    # Additional Devnet validation can be added here
    return True
