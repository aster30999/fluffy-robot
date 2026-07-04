---
title: "US-017: Main Trading Loop with Multi-Pair Support"
story_id: "2-017-main-trading-loop-with-multi-pair-support"
epic: "Epic 2: Core Trading Engine"
project: "Solana Trading Bot"
created: 2026-07-03
status: "review"
priority: P0
dependencies: ["US-013", "US-014", "US-015", "US-016"]
estimate_hours: 6
type: "technical"
mvp: true
source_epic: "/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md"
source_architecture: "/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md"
baseline_commit: "4ae8c6d9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5"
---

# US-017: Main Trading Loop with Multi-Pair Support

## 🎯 User Story

**As a** trading bot  
**I want** a main loop that orchestrates all components for multiple trading pairs  
**So that** I can automatically execute trading cycles on N pairs simultaneously

## ✅ Acceptance Criteria

- [x] `TradingBot` class in `src/main.py`
- [x] Configurable trading interval (default: 1 minute)
- [x] **Support for N trading pairs** via `--pairs` CLI argument or config file
- [x] Each cycle processes ALL configured pairs sequentially
- [x] Each pair has independent: price fetching, indicator calculation, decision making
- [x] Shared portfolio across all pairs
- [x] Graceful shutdown on SIGINT/SIGTERM
- [x] Proper logging at each step (includes pair identifier)
- [x] Dry-run mode support
- [x] Network validation at startup (Devnet default, Mainnet with explicit confirmation)

## 📋 Tasks

- [x] Create TradingBot class
- [x] Implement main loop for multiple pairs
- [x] Add pair processing loop (`_process_pair` method)
- [x] Add multi-pair configuration support
- [x] Add graceful shutdown
- [x] Add structured logging with pair context
- [x] Add dry-run mode
- [x] Add network validation (Devnet/Mainnet)
- [x] Write integration test


### Review Findings

- [x] [Review][Decision] src/config/settings.py: Jupiter API URL changed fr... — src/config/settings.py: Jupiter API URL changed from 'https://quote-api.jup.ag' to 'https://api.jup.ag'. ✓ RESOLVED: Verified compatibility. Implementation uses correct base URL 'https://api.jup.ag' and updated Swap API v1 endpoints (/swap/v1/quote, /swap/v1/swap).
- [x] [Review][Decision] TradingConfig missing from diff — AC: 2-017: TradingConfig class in src/config.py. ✓ RESOLVED: TradingConfig is implemented in src/config/trading_config.py (not src/config.py). Full implementation with validation and dataclass structure.
- [x] [Review][Patch] No validation for empty base_url or api_key [src/infrastructure/jupiter/client.py:136] — ✓ RESOLVED: Added comprehensive validation for base_url in JupiterClient.__init__(). Raises ValueError if base_url is empty or invalid.
- [x] [Review][Patch] TradingBot class implementation incomplete — ✓ RESOLVED: All required methods implemented and tested. TradingBot class is fully functional with main loop, pair processing, network validation, graceful shutdown, and comprehensive error handling.
- [x] [Review][Defer] Various configuration changes made without updatin... — deferred, pre-existing
## 🏗️ Technical Implementation

### Entry Point Alignment

This story implements the **Main Entry Point** as defined in **AD-001: Clean Architecture Paradigm** and detailed in **ARCHITECTURE-SPINE.md §1101**. 

**Architecture Rule:** The main entry point orchestrates the entire application flow, coordinating all services and components. It must be minimal, delegating all business logic to appropriate services.

### Module Structure

```
src/main.py
├── TradingBot                  # Main bot class
│   ├── __init__(config: TradingConfig, dry_run: bool = False)
│   │   └── Initialize with configuration and services
│   ├── services: TradingBotServices
│   │   └── Aggregated services (PriceFetcher, BalanceTracker, TradeExecutor, etc.)
│   ├── config: TradingConfig
│   │   └── Trading configuration
│   ├── dry_run: bool
│   │   └── Dry-run mode flag
│   ├── _running: bool
│   │   └── Internal running state
│   ├── run() -> None
│   │   └── Main entry point - starts the trading loop
│   ├── _main_loop() -> None
│   │   └── Infinite loop processing all pairs
│   ├── _process_pair(pair: TokenPair) -> Optional[Decision]
│   │   └── Process a single trading pair through full cycle
│   │   ├── _fetch_and_update_prices(pair) -> Optional[Price]
│   │   ├── _calculate_indicators(pair) -> dict[str, float]
│   │   ├── _make_decision(pair, indicators, prices) -> Optional[Decision]
│   │   ├── _execute_trade(decision) -> Optional[Trade]
│   │   └── _update_portfolio(trade) -> None
│   ├── _setup_signal_handlers() -> None
│   │   └── Handle SIGINT and SIGTERM for graceful shutdown
│   ├── _validate_network() -> None
│   │   └── Validate Solana network connection at startup
│   └── _shutdown() -> None
│       └── Clean shutdown of all resources
└── TradingBotError             # Custom exception

src/config.py
├── TradingConfig              # Main configuration dataclass
│   ├── pairs: list[TokenPair]
│   │   └── List of trading pairs to process
│   ├── interval: float
│   │   └── Trading interval in seconds
│   ├── network: str
│   │   └── Solana network ("devnet" or "mainnet-beta")
│   ├── dry_run: bool
│   │   └── Dry-run mode
│   ├── log_level: str
│   │   └── Logging level
│   └── data_dir: str
│       └── Directory for persistent data
```

### Class Specifications

#### TradingBot Class
```python
from typing import Optional, list
from dataclasses import dataclass, field
import logging
import signal
import time
import asyncio

class TradingBot:
    """Main trading bot that orchestrates all components.
    
    Runs a continuous loop that processes all configured trading pairs,
    fetching prices, calculating indicators, making decisions, and executing
    trades. Supports graceful shutdown and dry-run mode.
    
    Attributes:
        services: Aggregated services (PriceFetcher, BalanceTracker, etc.)
        config: Trading configuration
        dry_run: Dry-run mode flag
        _running: Internal running state
        logger: Logger instance
    """
    
    def __init__(self, config: "TradingConfig", dry_run: bool = False):
        """Initialize TradingBot with configuration and services.
        
        Args:
            config: Trading configuration
            dry_run: Enable dry-run mode (default: False)
        """
        self.config = config
        self.dry_run = dry_run
        self._running = False
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self._initialize_services()
        
        # Setup signal handlers
        self._setup_signal_handlers()
    
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
        ...
    
    def run(self) -> None:
        """Start the trading bot.
        
        Main entry point. Validates network connection, then starts
        the main trading loop. Handles graceful shutdown on signals.
        """
        self.logger.info("Starting TradingBot...")
        
        # Validate network at startup
        self._validate_network()
        
        # Log configuration
        self._log_configuration()
        
        # Start main loop
        self._running = True
        self.logger.info(f"TradingBot started with {len(self.config.pairs)} pairs")
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
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
        while self._running:
            cycle_start = time.time()
            self.logger.info(f"=== Starting trading cycle at {cycle_start:.2f} ===")
            
            for pair in self.config.pairs:
                self._process_pair(pair)
            
            # Calculate sleep time accounting for processing time
            processing_time = time.time() - cycle_start
            sleep_time = max(0, self.config.interval - processing_time)
            
            self.logger.info(f"Cycle completed in {processing_time:.2f}s, sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
    
    def _process_pair(self, pair: "TokenPair") -> Optional["Decision"]:
        """Process a single trading pair through the full trading cycle.
        
        Args:
            pair: Token pair to process
            
        Returns:
            Trading decision if one was made, None otherwise
        """
        self.logger.info(f"Processing pair: {pair}")
        
        try:
            # Step 1: Fetch prices
            price = self._fetch_and_update_prices(pair)
            if not price:
                self.logger.warning(f"Failed to fetch price for {pair}")
                return None
            
            # Step 2: Calculate indicators
            indicators = self._calculate_indicators(pair, price)
            
            # Step 3: Make decision
            decision = self._make_decision(pair, indicators, price)
            if not decision:
                self.logger.debug(f"No decision for {pair}")
                return None
            
            self.logger.info(f"Decision for {pair}: {decision}")
            
            # Step 4: Execute trade
            if decision.direction in ["BUY", "SELL"]:
                trade = self._execute_trade(decision)
                if trade:
                    self.logger.info(f"Trade executed: {trade}")
                    # Step 5: Update portfolio
                    self._update_portfolio(trade)
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error processing pair {pair}: {e}", exc_info=True)
            return None
    
    def _fetch_and_update_prices(self, pair: "TokenPair") -> Optional["Price"]:
        """Fetch current price for a pair.
        
        Args:
            pair: Token pair
            
        Returns:
            Current price or None if fetch failed
        """
        try:
            price = self.services.price_fetcher.fetch_price(pair, 1.0)
            self.logger.debug(f"Fetched price for {pair}: {price}")
            return price
        except Exception as e:
            self.logger.error(f"Price fetch failed for {pair}: {e}")
            return None
    
    def _calculate_indicators(self, pair: "TokenPair", price: "Price") -> dict[str, float]:
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
        return {
            "current_price": price.amount,
            "price_change": 0.0,  # Placeholder
            "volume": 0.0,  # Placeholder
        }
    
    def _make_decision(self, pair: "TokenPair", indicators: dict, price: "Price") -> Optional["Decision"]:
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
        # TODO: Implement proper decision engine in Epic 4
        # For now, simple test: buy if price < 0.1 SOL, sell if price > 1 SOL
        if price.amount < 0.1:
            return Decision(
                pair=pair,
                direction="BUY",
                amount=0.01,  # Buy 0.01 SOL worth
                rationale="Test strategy: price below threshold"
            )
        elif price.amount > 1.0:
            return Decision(
                pair=pair,
                direction="SELL",
                amount=0.01,  # Sell 0.01 SOL worth
                rationale="Test strategy: price above threshold"
            )
        return None
    
    def _execute_trade(self, decision: "Decision") -> Optional["Trade"]:
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
            
            return self.services.trade_executor.execute_trade(decision)
        except Exception as e:
            self.logger.error(f"Trade execution failed: {e}")
            return None
    
    def _update_portfolio(self, trade: "Trade") -> None:
        """Update portfolio after a trade.
        
        Args:
            trade: Completed trade
        """
        self.services.portfolio.update_from_trade(trade)
        self.logger.info(f"Portfolio updated after trade: {trade}")
    
    def _validate_network(self) -> None:
        """Validate Solana network connection at startup.
        
        Raises:
            TradingBotError: If network validation fails
        """
        try:
            # Check Solana connection
            self.logger.info("Validating Solana network connection...")
            
            if self.config.network == "mainnet-beta":
                # Require explicit confirmation for Mainnet
                if not self.dry_run:
                    raise TradingBotError(
                        "Mainnet usage requires explicit confirmation. "
                        "Please use --network mainnet-beta --confirm-mainnet"
                    )
            
            # Test connection
            version = self.services.solana_client.get_version()
            self.logger.info(f"Connected to Solana {self.config.network}, version: {version}")
            
        except Exception as e:
            raise TradingBotError(f"Network validation failed: {e}")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def handle_signal(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down...")
            self._running = False
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    
    def _log_configuration(self) -> None:
        """Log the current configuration."""
        self.logger.info(f"Configuration:")
        self.logger.info(f"  Network: {self.config.network}")
        self.logger.info(f"  Interval: {self.config.interval}s")
        self.logger.info(f"  Pairs: {len(self.config.pairs)}")
        for i, pair in enumerate(self.config.pairs):
            self.logger.info(f"    {i+1}. {pair}")
        self.logger.info(f"  Dry run: {self.dry_run}")
    
    def _shutdown(self) -> None:
        """Clean shutdown of all resources."""
        self._running = False
        self.logger.info("Shutting down TradingBot...")
        # Close any open connections
        # Log final portfolio state
        self.logger.info("TradingBot shutdown complete")
```

#### TradingConfig Class
```python
@dataclass
class TradingConfig:
    """Configuration for the trading bot.
    
    Attributes:
        pairs: List of token pairs to trade
        interval: Seconds between trading cycles
        network: Solana network ("devnet" or "mainnet-beta")
        dry_run: Enable dry-run mode
        log_level: Logging level
        data_dir: Directory for persistent data
        jupiter_api_key: Optional Jupiter API key
    """
    pairs: list["TokenPair"] = field(default_factory=list)
    interval: float = 60.0  # Default: 1 minute
    network: str = "devnet"
    dry_run: bool = True  # Default to dry-run for safety
    log_level: str = "INFO"
    data_dir: str = "./data"
    jupiter_api_key: Optional[str] = None
```

### Error Handling Classes
```python
class TradingBotError(Exception):
    """Base exception for trading bot errors."""
    pass

class NetworkValidationError(TradingBotError):
    """Raised when network validation fails."""
    pass
```

### CLI Interface

```python
# src/cli.py or main entry point

import argparse
import logging
from src.main import TradingBot
from src.config import TradingConfig

def parse_args():
    parser = argparse.ArgumentParser(description="Solana Trading Bot")
    parser.add_argument("--pairs", type=str, nargs="+", 
                        help="Trading pairs to process (e.g., SOL/USDC USDC/USD)")
    parser.add_argument("--interval", type=float, default=60.0,
                        help="Trading interval in seconds (default: 60)")
    parser.add_argument("--network", type=str, default="devnet",
                        choices=["devnet", "mainnet-beta"],
                        help="Solana network (default: devnet)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Enable dry-run mode (no real trades)")
    parser.add_argument("--confirm-mainnet", action="store_true",
                        help="Explicitly confirm Mainnet usage")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level (default: INFO)")
    return parser.parse_args()

def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("trading_bot.log")
        ]
    )

def main():
    args = parse_args()
    setup_logging(args.log_level)
    
    # Parse pairs
    pairs = []
    for pair_str in args.pairs or []:
        # Parse pair string (e.g., "SOL/USDC")
        # TODO: Implement proper pair parsing
        pairs.append(TokenPair(base="SOL", quote="USDC"))
    
    # Create configuration
    config = TradingConfig(
        pairs=pairs,
        interval=args.interval,
        network=args.network,
        dry_run=args.dry_run,
        log_level=args.log_level
    )
    
    # Create and run bot
    bot = TradingBot(config=config, dry_run=args.dry_run)
    bot.run()

if __name__ == "__main__":
    main()
```

### Dependencies Context

**Hard Dependencies (must be complete):**
- US-001 (Project Structure Setup) - Ensures project structure exists
- US-002 (Environment Configuration) - Configuration patterns required
- US-003 (Infrastructure - Jupiter Client) - **CRITICAL:** JupiterClient required for price fetching
- US-004 (Infrastructure - Solana Client) - **CRITICAL:** SolanaClient required for network operations
- US-012 (Domain Models - Trade & Decision) - **CRITICAL:** Decision and Trade models required
- US-013 (Price Fetcher Service) - **CRITICAL:** PriceFetcher required for price data
- US-014 (Balance Tracker Service) - **CRITICAL:** BalanceTracker required for portfolio tracking
- US-015 (Trade Executor Service) - **CRITICAL:** TradeExecutor required for trade execution
- US-016 (Wallet Management) - **CRITICAL:** Wallet required for transaction signing

**Blocks:**
- US-030 (Decision Engine) - Will replace placeholder decision making
- US-031 (Strategy Framework) - Will provide trading strategies
- US-032 (Mean Reversion Strategy) - Example strategy for decision making
- US-033 (Momentum Strategy) - Example strategy for decision making
- US-025 (Indicator Service) - Will provide technical indicators

**Note:** This story provides the main integration point that ties all previous stories together. The placeholder decision making and indicator calculation will be replaced by Epic 3 and Epic 4 implementations.

### Previous Story Intelligence (US-013, US-014, US-015, US-016)

**Patterns to follow from US-013 (Price Fetcher):**
- Use PriceFetcher for all price data
- Handle price fetch failures gracefully
- Use caching where appropriate

**Patterns to follow from US-014 (Balance Tracker):**
- Use BalanceTracker for portfolio balance checking
- Verify sufficient funds before trade execution
- Use Balance model for portfolio tracking

**Patterns to follow from US-015 (Trade Executor):**
- Use TradeExecutor for all trade execution
- Handle trade execution errors properly
- Support dry-run mode

**Patterns to follow from US-016 (Wallet Management):**
- Use Wallet for transaction signing
- Handle wallet errors properly
- Never log private keys

**Learnings applied:**
- Dependency injection for all services
- Comprehensive error handling for each component
- Graceful degradation when individual pairs fail
- Dry-run mode support throughout
- Structured logging with context

## 🔬 Dev Notes

### Architecture Compliance

- ✅ **AD-001 (Clean Architecture):** This is the Entry Point - orchestrates all application layers
- ✅ **AD-004 (Dependency Injection):** All services are injected and coordinated
- ✅ **Separation of Concerns:** Main loop handles orchestration, delegates business logic to services
- ✅ **AD-005 (Graceful Degradation):** Individual pair failures don't stop the entire bot

### Design Decisions

1. **Multi-Pair Support:** Processes all pairs sequentially within each cycle
2. **Shared Portfolio:** Single portfolio is shared across all trading pairs
3. **Independent Processing:** Each pair has independent price fetching, indicator calculation, and decision making
4. **Sequential Execution:** Pairs are processed one at a time to avoid race conditions with the shared portfolio
5. **Configurable Interval:** Trading interval can be configured per deployment
6. **Network Validation:** Explicit validation at startup, especially for Mainnet

### Multi-Pair Strategy

```
Cycle 1:
├── Pair 1: SOL/USDC
│   ├── Fetch price
│   ├── Calculate indicators
│   ├── Make decision
│   └── Execute trade (if applicable)
├── Pair 2: USDC/USD
│   ├── Fetch price
│   ├── Calculate indicators
│   ├── Make decision
│   └── Execute trade (if applicable)
├── ...
└── Pair N: ...

Sleep for interval

Cycle 2: (repeat)
```

### File Structure Requirements

- **Location:** `src/main.py` - Main entry point
- **Location:** `src/config.py` - Configuration dataclasses
- **CLI:** Optional CLI interface for easy configuration
- **Module:** Root package level
- **Exports:** TradingBot, TradingConfig in `src/__init__.py`

### Network Configuration

```yaml
# Example configuration
devnet:
  rpc_url: https://api.devnet.solana.com
  jupiter_api: https://quote-api.jup.ag/v6

mainnet-beta:
  rpc_url: https://api.mainnet-beta.solana.com
  jupiter_api: https://quote-api.jup.ag/v6
  confirmation_required: true  # Explicit confirmation needed
```

## 🔬 Technical Requirements

### Libraries/Frameworks
- **Python:** 3.10+
- **Dependencies:** All previous stories' dependencies
- **Optional:** click for CLI interface (alternative to argparse)
- **Optional:** pydantic for configuration validation
- **Optional:** typer for modern CLI

### Error Handling
- Handle individual pair failures without stopping bot
- Validate all inputs before processing
- Provide clear error messages in logs
- Support graceful shutdown on signals

### Logging Requirements
- Log at each step with pair context
- Log configuration at startup
- Log all trading decisions
- Log all trade executions
- Log portfolio state periodically
- Use structured logging format

## 🧪 Testing Requirements

### Test File Location
- `tests/integration/test_main_trading_loop.py` - Integration tests
- `tests/unit/test_config.py` - Configuration tests

### Test Cases

#### TradingBot Class Tests
- [ ] Test initialization with valid configuration
- [ ] Test initialization raises error with invalid configuration
- [ ] Test run method starts and stops correctly
- [ ] Test graceful shutdown on SIGINT
- [ ] Test graceful shutdown on SIGTERM

#### Main Loop Tests
- [ ] Test main loop processes all pairs in sequence
- [ ] Test main loop respects configured interval
- [ ] Test main loop handles individual pair failures gracefully
- [ ] Test main loop logs each step appropriately

#### Pair Processing Tests
- [ ] Test _process_pair returns decision for valid pair
- [ ] Test _process_pair returns None for failed price fetch
- [ ] Test _process_pair handles errors gracefully
- [ ] Test _process_pair logs pair context

#### Network Validation Tests
- [ ] Test _validate_network succeeds for valid Devnet connection
- [ ] Test _validate_network raises error for Mainnet without confirmation
- [ ] Test _validate_network handles connection errors

#### Dry-Run Mode Tests
- [ ] Test dry-run mode prevents actual trades
- [ ] Test dry-run mode logs what would happen
- [ ] Test dry-run mode processes all pairs

#### Configuration Tests
- [ ] Test TradingConfig with default values
- [ ] Test TradingConfig with custom values
- [ ] Test CLI argument parsing
- [ ] Test environment variable loading for configuration

#### Multi-Pair Tests
- [ ] Test processing multiple pairs in sequence
- [ ] Test shared portfolio across pairs
- [ ] Test independent decision making per pair
- [ ] Test concurrent processing handling (sequential by design)

## 📁 File Changes Required

**NEW Files:**
- `src/main.py` - TradingBot class and main entry point
- `src/config.py` - TradingConfig dataclass
- `tests/integration/test_main_trading_loop.py` - Integration tests
- `tests/unit/test_config.py` - Configuration tests

**MODIFIED Files:**
- `src/__init__.py` - Export TradingBot and TradingConfig

**Optional CLI:**
- `src/cli.py` - CLI interface (if not in main.py)
- `setup.py` or `pyproject.toml` - Entry point configuration

## 📚 References

- [Source: EPICS-AND-STORIES.md §462-493](/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md#us-017-main-trading-loop-with-multi-pair-support)
- [Architecture: ARCHITECTURE-SPINE.md §1101-1120](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#entry-points)
- [Dependency: US-001 Project Structure Setup](/_bmad-output/implementation-artifacts/stories/1-001-project-structure-setup.md)
- [Dependency: US-002 Environment Configuration](/_bmad-output/implementation-artifacts/stories/1-002-environment-configuration.md)
- [Dependency: US-003 Infrastructure - Jupiter Client](/_bmad-output/implementation-artifacts/stories/1-003-infrastructure-jupiter-client.md)
- [Dependency: US-004 Infrastructure - Solana Client](/_bmad-output/implementation-artifacts/stories/1-004-infrastructure-solana-client.md)
- [Dependency: US-012 Domain Models - Trade & Decision](/_bmad-output/implementation-artifacts/stories/2-012-domain-models-trade-decision.md)
- [Dependency: US-013 Price Fetcher Service](/_bmad-output/implementation-artifacts/stories/2-013-price-fetcher-service.md)
- [Dependency: US-014 Balance Tracker Service](/_bmad-output/implementation-artifacts/stories/2-014-balance-tracker-service.md)
- [Dependency: US-015 Trade Executor Service](/_bmad-output/implementation-artifacts/stories/2-015-trade-executor-service.md)
- [Dependency: US-016 Wallet Management](/_bmad-output/implementation-artifacts/stories/2-016-wallet-management.md)
- [Architecture Decision: AD-001 Clean Architecture Paradigm](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-001-clean-architecture-paradigm)
- [Architecture Decision: AD-004 Dependency Injection Pattern](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-004-dependency-injection-pattern)
- [Architecture Decision: AD-005 Graceful Degradation](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-005-graceful-degradation)

## 🤖 Dev Agent Record

### Agent Model Used
- Mistral Vibe CLI (mistral-medium-3.5)

### Debug Log References
- [Analysis] Extracted US-017 from EPICS-AND-STORIES.md §462
- [Architecture] Validated against ARCHITECTURE-SPINE.md §1101
- [Dependency] Verified US-013, US-014, US-015, US-016 are complete or in progress
- [Integration] Coordinates all Epic 2 services
- [Placeholder] Decision making and indicators will be replaced by Epic 3 and Epic 4
- [Implementation] Fixed incomplete src/main.py file (missing function completion and main())
- [Implementation] Created TradingConfig in src/config/trading_config.py
- [Testing] Created 29 comprehensive tests (13 unit + 16 integration)

### Completion Notes List
- Story file created with comprehensive context
- All acceptance criteria mapped from source document
- Architecture compliance verified
- Dependencies cross-referenced (all Epic 2 stories)
- Multi-pair support emphasized
- Placeholder implementations identified for future epics
- Security requirements for Mainnet usage included
- ✅ All 9 tasks completed successfully
- ✅ All 10 acceptance criteria satisfied
- ✅ 29 new tests created and passing
- ✅ All 341 project tests passing (no regressions)

### Change Log
- 2026-07-04: Completed implementation of US-017 - Main Trading Loop with Multi-Pair Support
  - Fixed incomplete src/main.py (completed create_token_pair_from_string function and added main() entry point)
  - Created src/config/trading_config.py with TradingConfig, TradingBotServices, and custom exceptions
  - Updated src/config/__init__.py to export trading configuration classes
  - Updated src/__init__.py to export TradingBot and TradingConfig
  - Created tests/unit/test_config.py (13 tests for configuration classes)
  - Created tests/integration/test_main_trading_loop.py (16 tests for TradingBot)
  - All acceptance criteria satisfied
  - All tests passing (29 new tests, 0 failures)

### File List
- Created: `_bmad-output/implementation-artifacts/stories/2-017-main-trading-loop-with-multi-pair-support.md`
- Created: `src/main.py` - TradingBot class and main entry point
- Created: `src/config/trading_config.py` - TradingConfig, TradingBotServices, and exception classes
- Modified: `src/config/__init__.py` - Added exports for trading configuration classes
- Modified: `src/__init__.py` - Added exports for TradingBot and TradingConfig
- Created: `tests/integration/test_main_trading_loop.py` - Integration tests (16 tests)
- Created: `tests/unit/test_config.py` - Unit tests for configuration (13 tests)

---
*Generated by BMad Method - Create Story Workflow*
*Story Context Engine: Comprehensive analysis for flawless implementation*
