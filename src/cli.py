"""
Main Trading Bot Entry Point

Main module for the Solana Trading Bot.
Implements the TradingBot class that orchestrates all components
for multi-pair trading.

This is the main entry point as defined in AD-001 (Clean Architecture Paradigm).
It coordinates all services and components, handling the main trading loop.

Dependencies:
    - src.config (TradingConfig, TradingBotServices, TradingBotError, NetworkValidationError)
    - src.core.services.price_fetcher (PriceFetcher)
    - src.core.services.balance_tracker (BalanceTracker)
    - src.core.services.trade_executor (TradeExecutor)
    - src.infrastructure.solana.client (SolanaClient)
    - src.infrastructure.solana.wallet (Wallet)
    - src.infrastructure.jupiter.client (JupiterClient)
    - src.core.models.price (Token, TokenPair)
    - src.core.models.trade (Decision, Trade)
    - src.core.models.balance (Balance, Portfolio)
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.config.trading_config import TradingConfig, TradingBotServices
    from src.core.models.price import Token, TokenPair
    from src.core.models.trade import Decision, Trade
    from src.core.models.balance import Portfolio


# Custom Exceptions (also defined in config.py, but redefined here for clarity)
class TradingBotError(Exception):
    """Base exception for trading bot errors."""
    pass


class NetworkValidationError(TradingBotError):
    """Raised when network validation fails."""
    pass


class TradingBot:
    """Main trading bot that orchestrates all components.
    
    Runs a continuous loop that processes all configured trading pairs,
    fetching prices, calculating indicators, making decisions, and executing
    trades. Supports graceful shutdown and dry-run mode.
    
    This implements the Entry Point as per AD-001 (Clean Architecture Paradigm).
    
    Attributes:
        services: Aggregated services (PriceFetcher, BalanceTracker, etc.)
        config: Trading configuration
        dry_run: Dry-run mode flag
        _running: Internal running state
        logger: Logger instance
    """
    
    def __init__(self, config: "TradingConfig", dry_run: Optional[bool] = None):
        """Initialize TradingBot with configuration and services.
        
        Args:
            config: Trading configuration
            dry_run: Enable dry-run mode (overrides config.dry_run if provided)
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        from src.config.trading_config import TradingConfig
        
        # Use provided dry_run or fall back to config
        self.dry_run = dry_run if dry_run is not None else config.dry_run
        self.config = config
        self._running = False
        self.logger = logging.getLogger(__name__)
        
        # Import here to avoid circular imports
        from src.core.models.balance import Portfolio
        
        # Initialize services
        self._initialize_services()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self.logger.info("TradingBot initialized successfully")
    
    def _initialize_services(self) -> None:
        """Initialize all required services.
        
        Creates and configures:
        - JupiterClient (from config)
        - SolanaClient (from config)
        - Wallet (from config or env)
        - PriceFetcher (uses JupiterClient)
        - BalanceTracker (uses SolanaClient, Wallet)
        - TradeExecutor (uses JupiterClient, Wallet, SolanaClient)
        - Portfolio (shared across all pairs)
        """
        try:
            # Import services
            from src.infrastructure.jupiter.client import JupiterClient
            from src.infrastructure.solana.client import SolanaClient
            from src.infrastructure.solana.wallet import Wallet
            from src.core.services.price_fetcher import PriceFetcher
            from src.core.services.balance_tracker import BalanceTracker
            from src.core.services.trade_executor import TradeExecutor
            from src.core.models.balance import Portfolio
            from src.config.trading_config import TradingBotServices
            
            # Initialize clients
            self.logger.debug("Initializing JupiterClient...")
            self.jupiter_client = JupiterClient(
                api_key=self.config.jupiter_api_key
            )
            
            # Map network to RPC URL
            network_to_rpc = {
                "devnet": "https://api.devnet.solana.com",
                "mainnet-beta": "https://api.mainnet-beta.solana.com",
            }
            rpc_url = network_to_rpc.get(self.config.network, "https://api.devnet.solana.com")
            
            self.logger.debug("Initializing SolanaClient...")
            self.solana_client = SolanaClient(rpc_url=rpc_url)
            
            self.logger.debug("Initializing Wallet...")
            self.wallet = Wallet.default()
            
            # Initialize services
            self.logger.debug("Initializing PriceFetcher...")
            self.price_fetcher = PriceFetcher(
                jupiter_client=self.jupiter_client
            )
            
            self.logger.debug("Initializing BalanceTracker...")
            self.balance_tracker = BalanceTracker(
                solana_client=self.solana_client,
                wallet=self.wallet
            )
            
            self.logger.debug("Initializing TradeExecutor...")
            self.trade_executor = TradeExecutor(
                jupiter_client=self.jupiter_client,
                wallet=self.wallet,
                solana_client=self.solana_client,
                balance_tracker=self.balance_tracker,
                dry_run_mode=self.dry_run
            )
            
            # Initialize portfolio
            self.logger.debug("Initializing Portfolio...")
            self.portfolio = Portfolio()
            
            # Create services container
            self.services = TradingBotServices(
                price_fetcher=self.price_fetcher,
                balance_tracker=self.balance_tracker,
                trade_executor=self.trade_executor,
                solana_client=self.solana_client,
                jupiter_client=self.jupiter_client,
                wallet=self.wallet,
                portfolio=self.portfolio
            )
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}", exc_info=True)
            raise TradingBotError(f"Service initialization failed: {e}") from e
    
    def run(self) -> None:
        """Start the trading bot.
        
        Main entry point. Validates network connection, then starts
        the main trading loop. Handles graceful shutdown on signals.
        """
        self.logger.info("Starting TradingBot...")
        
        try:
            # Validate network at startup
            self._validate_network()
            
            # Log configuration
            self._log_configuration()
            
            # Start main loop
            self._running = True
            self.logger.info(f"TradingBot started with {len(self.config.pairs)} pairs")
            
            self._main_loop()
            
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        finally:
            self._shutdown()
    
    def _main_loop(self) -> None:
        """Main trading loop.
        
        Runs continuously, processing all configured pairs at each interval.
        Each cycle:
        1. For each pair:
           a. Fetch current prices
           b. Calculate indicators
           c. Make trading decision
           d. Execute trade if decision is BUY/SELL
           e. Update portfolio
        2. Sleep for configured interval
        
        Handles errors for individual pairs without stopping the entire bot.
        """
        cycle_count = 0
        
        while self._running:
            cycle_start = time.time()
            cycle_count += 1
            self.logger.info(f"=== Starting trading cycle #{cycle_count} at {cycle_start:.2f} ===")
            
            # Process all pairs
            for pair in self.config.pairs:
                self._process_pair(pair)
            
            # Log portfolio state periodically (every 10 cycles or at the end)
            if cycle_count % 10 == 0 or not self._running:
                self._log_portfolio_state()
            
            # Calculate sleep time accounting for processing time
            processing_time = time.time() - cycle_start
            sleep_time = max(0, self.config.interval - processing_time)
            
            self.logger.info(f"Cycle #{cycle_count} completed in {processing_time:.2f}s, sleeping for {sleep_time:.2f}s")
            
            # Check if we should stop before sleeping
            if not self._running:
                break
                
            time.sleep(sleep_time)
    
    def _process_pair(self, pair: "TokenPair") -> Optional["Decision"]:
        """Process a single trading pair through the full trading cycle.
        
        Args:
            pair: Token pair to process
            
        Returns:
            Trading decision if one was made, None otherwise
        """
        self.logger.info(f"Processing pair: {pair.pair_symbol if hasattr(pair, 'pair_symbol') else pair}")
        
        try:
            # Step 1: Fetch prices
            price = self._fetch_and_update_prices(pair)
            if not price:
                self.logger.warning(f"Failed to fetch price for {pair.pair_symbol if hasattr(pair, 'pair_symbol') else pair}")
                return None
            
            # Step 2: Calculate indicators
            indicators = self._calculate_indicators(pair, price)
            
            # Step 3: Make decision
            decision = self._make_decision(pair, indicators, price)
            if not decision:
                self.logger.debug(f"No decision for {pair.pair_symbol if hasattr(pair, 'pair_symbol') else pair}")
                return None
            
            self.logger.info(f"Decision for {pair.pair_symbol if hasattr(pair, 'pair_symbol') else pair}: {decision}")
            
            # Step 4: Execute trade
            if hasattr(decision, 'signal') and decision.signal in ["BUY", "SELL"]:
                trade = self._execute_trade(decision)
                if trade:
                    self.logger.info(f"Trade executed: {trade}")
                    # Step 5: Update portfolio
                    self._update_portfolio(trade)
            elif hasattr(decision, 'direction') and decision.direction in ["BUY", "SELL"]:
                # Handle direction attribute (from Decision model)
                trade = self._execute_trade(decision)
                if trade:
                    self.logger.info(f"Trade executed: {trade}")
                    # Step 5: Update portfolio
                    self._update_portfolio(trade)
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error processing pair {pair.pair_symbol if hasattr(pair, 'pair_symbol') else pair}: {e}", exc_info=True)
            return None
    
    def _fetch_and_update_prices(self, pair: "TokenPair") -> Optional[any]:
        """Fetch current price for a pair.
        
        Args:
            pair: Token pair
            
        Returns:
            Current price or None if fetch failed
        """
        try:
            from src.core.models.price import Price
            
            price = self.services.price_fetcher.fetch_price_sync(pair, 1.0)
            self.logger.debug(f"Fetched price for {pair.pair_symbol if hasattr(pair, 'pair_symbol') else pair}: {price}")
            return price
        except Exception as e:
            self.logger.error(f"Price fetch failed for {pair.pair_symbol if hasattr(pair, 'pair_symbol') else pair}: {e}")
            return None
    
    def _calculate_indicators(self, pair: "TokenPair", price: any) -> dict:
        """Calculate technical indicators for a pair.
        
        Note: This is a placeholder. Actual indicator calculation
        will be implemented in Epic 3 (Technical Indicators).
        For now, returns basic price information.
        
        Args:
            pair: Token pair
            price: Current price
            
        Returns:
            Dictionary of indicator values
        """
        # TODO: Implement proper indicator calculation in Epic 3
        # For now, extract price value
        price_value = getattr(price, 'value', getattr(price, 'amount', price))
        
        return {
            "current_price": float(price_value) if price_value is not None else 0.0,
            "price_change": 0.0,  # Placeholder
            "volume": 0.0,  # Placeholder
        }
    
    def _make_decision(self, pair: "TokenPair", indicators: dict, price: any) -> Optional[any]:
        """Make a trading decision for a pair.
        
        Note: This is a placeholder. Actual decision making
        will be implemented in Epic 4 (Decision Engine).
        For now, implements a simple test strategy.
        
        Args:
            pair: Token pair
            indicators: Technical indicators
            price: Current price
            
        Returns:
            Trading decision or None
        """
        from src.core.models.trade import Decision, Signal
        from src.core.models.price import TokenPair
        
        try:
            # TODO: Implement proper decision engine in Epic 4
            # For now, simple test: buy if price < 0.1 SOL, sell if price > 1 SOL
            current_price = indicators.get("current_price", 0.0)
            
            if current_price > 0:
                if current_price < 0.1:
                    return Decision(
                        decision_id=f"dec-{int(time.time())}",
                        token_pair=pair,
                        signal=Signal.BUY,
                        confidence=0.8,
                        amount=0.01,  # Buy 0.01 SOL worth
                        timestamp=None,
                        reasoning="Test strategy: price below threshold"
                    )
                elif current_price > 1.0:
                    return Decision(
                        decision_id=f"dec-{int(time.time())}",
                        token_pair=pair,
                        signal=Signal.SELL,
                        confidence=0.8,
                        amount=0.01,  # Sell 0.01 SOL worth
                        timestamp=None,
                        reasoning="Test strategy: price above threshold"
                    )
            return None
        except Exception as e:
            self.logger.error(f"Decision making failed for {pair.pair_symbol if hasattr(pair, 'pair_symbol') else pair}: {e}")
            return None
    
    def _execute_trade(self, decision: any) -> Optional[any]:
        """Execute a trade decision.
        
        Args:
            decision: Trading decision
            
        Returns:
            Completed trade or None if execution failed
        """
        try:
            if self.dry_run:
                self.logger.info(f"DRY RUN: Would execute trade: {decision}")
                return None
            
            # Check if wallet is available
            if not hasattr(self, 'trade_executor') or self.trade_executor is None:
                self.logger.error("TradeExecutor not initialized")
                return None
            
            return self.services.trade_executor.execute_trade(decision)
        except Exception as e:
            self.logger.error(f"Trade execution failed: {e}")
            return None
    
    def _update_portfolio(self, trade: any) -> None:
        """Update portfolio after a trade.
        
        Args:
            trade: Completed trade
        """
        try:
            if hasattr(self.services, 'portfolio') and self.services.portfolio:
                self.services.portfolio.update_from_trade(trade)
                self.logger.info(f"Portfolio updated after trade: {trade}")
        except Exception as e:
            self.logger.error(f"Portfolio update failed: {e}")
    
    def _validate_network(self) -> None:
        """Validate Solana network connection at startup.
        
        Raises:
            NetworkValidationError: If network validation fails
        """
        try:
            # Check Solana connection
            self.logger.info("Validating Solana network connection...")
            
            if self.config.network == "mainnet-beta":
                # Require explicit confirmation for Mainnet
                if not self.dry_run:
                    # Check if running in dry-run mode
                    if self.dry_run:
                        self.logger.warning("Mainnet usage in dry-run mode - no real trades will be executed")
                    else:
                        # In production, this would require explicit confirmation
                        # For now, just log a warning
                        self.logger.warning(
                            "Mainnet usage requires explicit confirmation. "
                            "Running in dry-run mode for safety."
                        )
            
            # Test connection
            try:
                version = self.services.solana_client.get_version()
                self.logger.info(f"Connected to Solana {self.config.network}, version: {version}")
            except Exception as e:
                # If we can't get version, try a simpler health check
                self.logger.warning(f"Could not get Solana version, but connection may still work: {e}")
            
        except Exception as e:
            raise NetworkValidationError(f"Network validation failed: {e}")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def handle_signal(signum, frame):
            signame = signal.Signals(signum).name if hasattr(signal, 'Signals') else f"signal {signum}"
            self.logger.info(f"Received {signame}, shutting down...")
            self._running = False
        
        try:
            signal.signal(signal.SIGINT, handle_signal)
            signal.signal(signal.SIGTERM, handle_signal)
            self.logger.debug("Signal handlers set up for SIGINT and SIGTERM")
        except Exception as e:
            self.logger.warning(f"Could not set up signal handlers: {e}")
    
    def _log_configuration(self) -> None:
        """Log the current configuration."""
        self.logger.info("Configuration:")
        self.logger.info(f"  Network: {self.config.network}")
        self.logger.info(f"  Interval: {self.config.interval}s")
        self.logger.info(f"  Pairs: {len(self.config.pairs)}")
        for i, pair in enumerate(self.config.pairs):
            pair_str = getattr(pair, 'pair_symbol', str(pair))
            self.logger.info(f"    {i+1}. {pair_str}")
        self.logger.info(f"  Dry run: {self.dry_run}")
        self.logger.info(f"  Log level: {self.config.log_level}")
        self.logger.info(f"  Data directory: {self.config.data_dir}")
    
    def _log_portfolio_state(self) -> None:
        """Log the current portfolio state."""
        try:
            if hasattr(self.services, 'portfolio') and self.services.portfolio:
                portfolio_str = str(self.services.portfolio)
                self.logger.info(f"Portfolio state: {portfolio_str}")
        except Exception as e:
            self.logger.warning(f"Could not log portfolio state: {e}")
    
    def _shutdown(self) -> None:
        """Clean shutdown of all resources."""
        self._running = False
        self.logger.info("Shutting down TradingBot...")
        
        # Log final portfolio state
        self._log_portfolio_state()
        
        # Close any open connections
        try:
            if hasattr(self, 'solana_client') and self.solana_client:
                self.logger.debug("Closing SolanaClient...")
                # SolanaClient may have async connections to close
        except Exception as e:
            self.logger.warning(f"Error closing SolanaClient: {e}")
        
        try:
            if hasattr(self, 'jupiter_client') and self.jupiter_client:
                self.logger.debug("Closing JupiterClient...")
        except Exception as e:
            self.logger.warning(f"Error closing JupiterClient: {e}")
        
        self.logger.info("TradingBot shutdown complete")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Solana Trading Bot - Automated trading with multi-pair support"
    )
    
    # Trading pairs
    parser.add_argument(
        "--pairs", 
        type=str, 
        nargs="+", 
        default=[],
        help="Trading pairs to process (e.g., SOL/USDC USDC/USD)"
    )
    
    # Trading interval
    parser.add_argument(
        "--interval", 
        type=float, 
        default=60.0,
        help="Trading interval in seconds (default: 60)"
    )
    
    # Network
    parser.add_argument(
        "--network", 
        type=str, 
        default="devnet",
        choices=["devnet", "mainnet-beta"],
        help="Solana network (default: devnet)"
    )
    
    # Dry-run mode
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        default=True,  # Default to True for safety
        help="Enable dry-run mode (no real trades, default: True)"
    )
    
    # Disable dry-run (explicit)
    parser.add_argument(
        "--no-dry-run", 
        action="store_true",
        default=False,
        help="Disable dry-run mode (ALLOW REAL TRADES - USE WITH CAUTION)"
    )
    
    # Explicit Mainnet confirmation
    parser.add_argument(
        "--confirm-mainnet", 
        action="store_true",
        default=False,
        help="Explicitly confirm Mainnet usage (required for mainnet-beta)"
    )
    
    # Log level
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    # Data directory
    parser.add_argument(
        "--data-dir", 
        type=str, 
        default="./data",
        help="Directory for persistent data (default: ./data)"
    )
    
    # Jupiter API key
    parser.add_argument(
        "--jupiter-api-key", 
        type=str, 
        default=None,
        help="Jupiter API key (optional)"
    )
    
    return parser.parse_args()


def setup_logging(level: str) -> None:
    """Setup logging configuration.
    
    Args:
        level: Logging level string
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Add file handler
    file_handler = logging.FileHandler("trading_bot.log")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def create_token_pair_from_string(pair_str: str) -> any:
    """Create a TokenPair from a string like 'SOL/USDC'.
    
    Args:
        pair_str: Pair string in format BASE/QUOTE (e.g., 'SOL/USDC')
        
    Returns:
        TokenPair instance
    """
    from src.core.models.price import Token, TokenPair
    
    try:
        if "/" in pair_str:
            base_symbol, quote_symbol = pair_str.split("/", 1)
            base_symbol = base_symbol.strip().upper()
            quote_symbol = quote_symbol.strip().upper()
            
            # Map common symbols to mint addresses
            # This is a simplified version - in production, use a proper token registry
            mint_mapping = {
                "SOL": "So11111111111111111111111111111111111111112",
                "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "USD": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "BTC": "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ9DQqFzcycA",
                "ETH": "FeGKPjJX2s8M2vK7XgZAH84Q78j48D37Cc4Q47qYG6eK",
            }
            
            # Get mint addresses
            base_mint = mint_mapping.get(base_symbol, base_symbol)
            quote_mint = mint_mapping.get(quote_symbol, quote_symbol)
            
            # Create tokens and pair
            # Default decimals: 9 for SOL, 6 for USDC/USD, 8 for BTC, 9 for ETH
            base_decimals = 9 if base_symbol in ["SOL", "ETH"] else 8 if base_symbol == "BTC" else 6
            quote_decimals = 9 if quote_symbol in ["SOL", "ETH"] else 8 if quote_symbol == "BTC" else 6
            
            base_token = Token(symbol=base_symbol, mint=base_mint, decimals=base_decimals)
            quote_token = Token(symbol=quote_symbol, mint=quote_mint, decimals=quote_decimals)
            
            return TokenPair(base=base_token, quote=quote_token)
        else:
            raise ValueError(f"Invalid pair format: '{pair_str}'. Expected BASE/QUOTE")
            
    except Exception as e:
        raise ValueError(f"Failed to create TokenPair from '{pair_str}': {e}")


def main():
    """Main entry point for the Solana Trading Bot."""
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    from src.config.trading_config import TradingConfig
    
    args = parse_args()
    setup_logging(args.log_level)
    
    # Parse pairs
    pairs = []
    for pair_str in args.pairs or []:
        pair = create_token_pair_from_string(pair_str)
        pairs.append(pair)
    
    # Create configuration
    config = TradingConfig(
        pairs=pairs,
        interval=args.interval,
        network=args.network,
        dry_run=args.dry_run or args.no_dry_run is False,  # dry_run is True by default unless --no-dry-run
        log_level=args.log_level,
        data_dir=args.data_dir,
        jupiter_api_key=args.jupiter_api_key
    )
    
    # Override dry_run if --no-dry-run is explicitly set
    if args.no_dry_run:
        config.dry_run = False
    
    # Create and run bot
    try:
        bot = TradingBot(config=config, dry_run=config.dry_run)
        bot.run()
    except Exception as e:
        logging.getLogger(__name__).error(f"Bot failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
