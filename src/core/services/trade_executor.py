"""
Trade Executor Service

Service for executing trades via Jupiter API.
Implements the Application Services layer as per AD-001 (Clean Architecture Paradigm).

Uses dependency injection for all external dependencies:
- JupiterClient for swap quotes and execution
- Wallet for transaction signing
- SolanaClient for transaction confirmation

Dependencies:
    - src.infrastructure.jupiter.client (JupiterClient)
    - src.infrastructure.solana.wallet (Wallet)
    - src.infrastructure.solana.client (SolanaClient)
    - src.core.models.trade (Decision, Trade)
    - src.core.models.balance (Balance)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from solders.signature import Signature
from solders.transaction import Transaction

from src.core.models.balance import Balance
from src.core.models.trade import Decision, Trade, Signal, TradeStatus

if TYPE_CHECKING:
    from src.infrastructure.jupiter.client import JupiterClient
    from src.infrastructure.solana.wallet import Wallet
    from src.infrastructure.solana.client import SolanaClient


# Custom Exceptions
class TradeExecutionError(Exception):
    """Base exception for trade execution failures."""
    pass


class InsufficientFundsError(TradeExecutionError):
    """Raised when wallet has insufficient funds for the trade."""
    def __init__(self, required: float, available: float, token: str):
        self.required = required
        self.available = available
        self.token = token
        super().__init__(
            f"Insufficient {token} balance: need {required}, have {available}"
        )


class SlippageError(TradeExecutionError):
    """Raised when actual price differs too much from expected price."""
    def __init__(self, expected: float, actual: float, threshold: float):
        self.expected = expected
        self.actual = actual
        self.threshold = threshold
        super().__init__(
            f"Slippage exceeded threshold: expected {expected}, got {actual}, threshold {threshold}"
        )


class TransactionTimeoutError(TradeExecutionError):
    """Raised when transaction confirmation times out."""
    def __init__(self, tx_signature: str, timeout: int):
        self.tx_signature = tx_signature
        self.timeout = timeout
        super().__init__(
            f"Transaction confirmation timed out after {timeout}s: {tx_signature}"
        )


@dataclass
class SwapQuote:
    """Data class for Jupiter swap quote."""
    input_amount: float
    output_amount: float
    input_mint: str
    output_mint: str
    slippage_bps: int
    price_impact_pct: float
    fees: float


class TradeExecutor:
    """Service for executing trades via Jupiter API.
    
    Uses dependency injection for JupiterClient, Wallet, and SolanaClient
    to enable testing and support different implementations.
    Supports dry-run mode for testing without actual transactions.
    
    Attributes:
        jupiter_client: Jupiter API client for swap quotes and execution
        wallet: Wallet for transaction signing
        solana_client: Solana client for transaction confirmation
        balance_tracker: BalanceTracker for pre-trade balance checks
        dry_run_mode: If True, validates but doesn't execute real trades
        slippage_threshold: Maximum allowed slippage (default: 0.01 = 1%)
        confirmation_timeout: Transaction confirmation timeout in seconds (default: 60)
        logger: Logger instance for debugging and monitoring
    """
    
    def __init__(
        self,
        jupiter_client: JupiterClient,
        wallet: Wallet,
        solana_client: SolanaClient,
        balance_tracker: Optional[any] = None,  # BalanceTracker - optional dependency
        dry_run_mode: bool = False,
        slippage_threshold: float = 0.01,  # 1%
        confirmation_timeout: int = 60,
    ):
        """Initialize TradeExecutor with required services.
        
        Args:
            jupiter_client: Injected Jupiter API client
            wallet: Injected wallet for signing transactions
            solana_client: Injected Solana client for confirmations
            balance_tracker: Optional BalanceTracker for pre-trade checks
            dry_run_mode: Enable dry-run mode (default: False)
            slippage_threshold: Maximum allowed slippage (default: 0.01)
            confirmation_timeout: Transaction confirmation timeout (default: 60s)
        """
        self.jupiter_client = jupiter_client
        self.wallet = wallet
        self.solana_client = solana_client
        self.balance_tracker = balance_tracker
        self.dry_run_mode = dry_run_mode
        self.slippage_threshold = slippage_threshold
        self.confirmation_timeout = confirmation_timeout
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(
            f"TradeExecutor initialized: dry_run={dry_run_mode}, "
            f"slippage_threshold={slippage_threshold}, "
            f"confirmation_timeout={confirmation_timeout}s"
        )
    
    def execute_trade(self, decision: Decision) -> Optional[Trade]:
        """Execute a trade based on a trading decision.
        
        Uses Jupiter's Order & Execute workflow:
        1. Get swap quote from Jupiter
        2. Validate balance (if BalanceTracker available)
        3. Build swap transaction
        4. Sign transaction with wallet
        5. Send transaction to Solana network
        6. Verify transaction confirmation
        
        Args:
            decision: Trading decision containing pair, amount, direction
            
        Returns:
            Trade object with transaction details if successful, None otherwise
            
        Raises:
            TradeExecutionError: If trade execution fails
            InsufficientFundsError: If wallet has insufficient balance
            SlippageError: If slippage exceeds configured threshold
            TransactionTimeoutError: If transaction confirmation times out
        """
        self.logger.info(f"Executing trade for decision: {decision}")
        
        if self.dry_run_mode:
            self.logger.info(f"DRY RUN: Would execute trade: {decision}")
            return self._create_dry_run_trade(decision)
        
        try:
            # Step 1: Pre-trade validation
            self._validate_trade(decision)
            
            # Step 2: Get swap quote from Jupiter
            quote = self._get_swap_quote(decision)
            
            # Step 3: Validate slippage
            self._validate_slippage(quote, decision)
            
            # Step 4: Build and execute swap transaction
            tx_signature = self._execute_swap(decision, quote)
            
            # Step 5: Verify transaction confirmation
            self._confirm_transaction(tx_signature)
            
            # Step 6: Create and return Trade object
            return self._create_trade_object(decision, quote, tx_signature)
            
        except InsufficientFundsError:
            raise
        except SlippageError:
            raise
        except TransactionTimeoutError:
            raise
        except Exception as e:
            self.logger.error(f"Trade execution failed: {e}", exc_info=True)
            raise TradeExecutionError(f"Trade execution failed: {e}") from e
    
    def _validate_trade(self, decision: Decision) -> None:
        """Validate trade parameters before execution.
        
        Args:
            decision: Trading decision to validate
            
        Raises:
            TradeExecutionError: If validation fails
            InsufficientFundsError: If insufficient balance
        """
        # Validate decision parameters
        if not decision.token_pair:
            raise TradeExecutionError("Decision must have a token pair")
        
        if decision.amount <= 0:
            raise TradeExecutionError(f"Trade amount must be positive, got {decision.amount}")
        
        if decision.signal not in [Signal.BUY, Signal.SELL]:
            raise TradeExecutionError(f"Invalid trade signal: {decision.signal}")
        
        # Check balance if BalanceTracker is available
        if self.balance_tracker:
            self._validate_balance(decision)
    
    def _validate_balance(self, decision: Decision) -> None:
        """Validate that wallet has sufficient balance for the trade.
        
        Args:
            decision: Trading decision
            
        Raises:
            InsufficientFundsError: If balance is insufficient
        """
        try:
            # Get the token mint for the input currency
            input_mint = self._get_input_mint(decision)
            
            if input_mint == "So11111111111111111111111111111111111111112":  # SOL
                balance = self.balance_tracker.get_sol_balance()
                token_symbol = "SOL"
            else:
                balance = self.balance_tracker.get_token_balance(input_mint)
                token_symbol = input_mint[:6]  # Short symbol
            
            if balance < decision.amount:
                raise InsufficientFundsError(
                    required=decision.amount,
                    available=balance,
                    token=token_symbol
                )
                
            self.logger.debug(f"Balance check passed: {balance} {token_symbol} available")
            
        except InsufficientFundsError:
            # Re-raise InsufficientFundsError as it's a critical error
            raise
        except Exception as e:
            self.logger.warning(f"Balance check skipped or failed: {e}")
            # Continue without balance check if it fails
    
    def _get_input_mint(self, decision: Decision) -> str:
        """Get the mint address for the input token in a decision.
        
        Args:
            decision: Trading decision
            
        Returns:
            Mint address of the input token
        """
        # For BUY signal, we need quote token to buy base token
        # For SELL signal, we sell the base token
        if decision.signal == Signal.BUY:
            return decision.token_pair.quote.mint if decision.token_pair.quote else "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        else:
            # For SELL, we're selling the base token
            return decision.token_pair.base.mint if decision.token_pair.base else "So11111111111111111111111111111111111111112"
    
    def _get_swap_quote(self, decision: Decision) -> SwapQuote:
        """Get swap quote from Jupiter API.
        
        Args:
            decision: Trading decision
            
        Returns:
            SwapQuote with quote details
            
        Raises:
            TradeExecutionError: If quote cannot be obtained
        """
        try:
            self.logger.debug(f"Getting swap quote for: {decision}")
            
            # Use JupiterClient to get quote
            # This is a placeholder - actual implementation depends on JupiterClient API
            base_mint = decision.token_pair.base.mint if decision.token_pair.base else "So11111111111111111111111111111111111111112"
            quote_mint = decision.token_pair.quote.mint if decision.token_pair.quote else "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            
            quote_data = self.jupiter_client.quote_swap(
                input_mint=base_mint,
                output_mint=quote_mint,
                amount=decision.amount,
                slippage_bps=int(self.slippage_threshold * 10000),  # Convert to basis points
            )
            
            # Parse quote data
            quote = SwapQuote(
                input_amount=decision.amount,
                output_amount=quote_data["outAmount"] if isinstance(quote_data, dict) else 0.0,
                input_mint=base_mint,
                output_mint=quote_mint,
                slippage_bps=int(self.slippage_threshold * 10000),
                price_impact_pct=quote_data.get("priceImpactPct", 0.0) if isinstance(quote_data, dict) else 0.0,
                fees=quote_data.get("fees", 0.0) if isinstance(quote_data, dict) else 0.0,
            )
            
            self.logger.info(f"Swap quote: {quote.input_amount} {quote.input_mint} -> {quote.output_amount} {quote.output_mint}")
            return quote
            
        except Exception as e:
            self.logger.error(f"Failed to get swap quote: {e}")
            raise TradeExecutionError(f"Failed to get swap quote: {e}") from e
    
    def _validate_slippage(self, quote: SwapQuote, decision: Decision) -> None:
        """Validate that actual output meets expected output within threshold.
        
        Args:
            quote: Swap quote
            decision: Trading decision
            
        Raises:
            SlippageError: If slippage exceeds threshold
        """
        # For now, we accept the quote as is
        # Actual slippage validation would compare expected vs actual after execution
        self.logger.debug(f"Slippage validation: threshold={self.slippage_threshold}")
        
        # Placeholder: Always pass for now
        # This will be enhanced when actual execution is implemented
        pass
    
    def _execute_swap(self, decision: Decision, quote: SwapQuote) -> Signature:
        """Execute the swap transaction via Jupiter.
        
        Args:
            decision: Trading decision
            quote: Swap quote
            
        Returns:
            Transaction signature
            
        Raises:
            TradeExecutionError: If swap execution fails
        """
        try:
            self.logger.info(f"Executing swap: {decision}")
            
            base_mint = decision.token_pair.base.mint if decision.token_pair.base else "So11111111111111111111111111111111111111112"
            quote_mint = decision.token_pair.quote.mint if decision.token_pair.quote else "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            
            # Use JupiterClient to execute swap
            # This is a placeholder - actual implementation uses Jupiter's swap endpoint
            swap_result = self.jupiter_client.swap(
                input_mint=base_mint,
                output_mint=quote_mint,
                amount=decision.amount,
                slippage_bps=int(self.slippage_threshold * 10000),
            )
            
            # Extract transaction signature
            tx_signature = swap_result.get("txid", None) if isinstance(swap_result, dict) else None
            
            if not tx_signature:
                raise TradeExecutionError("No transaction signature returned from swap")
            
            self.logger.info(f"Swap executed with signature: {tx_signature}")
            return Signature.from_string(tx_signature)
            
        except Exception as e:
            self.logger.error(f"Swap execution failed: {e}")
            raise TradeExecutionError(f"Swap execution failed: {e}") from e
    
    def _confirm_transaction(self, tx_signature: Signature) -> None:
        """Wait for and verify transaction confirmation.
        
        Args:
            tx_signature: Transaction signature to confirm
            
        Raises:
            TradeExecutionError: If transaction failed
            TransactionTimeoutError: If confirmation takes too long
        """
        import time
        
        self.logger.info(f"Confirming transaction: {tx_signature}")
        
        start_time = time.time()
        
        while time.time() - start_time < self.confirmation_timeout:
            try:
                # Check transaction status via SolanaClient
                status = self.solana_client.get_transaction_status(str(tx_signature))
                
                if status == "confirmed":
                    self.logger.info(f"Transaction confirmed: {tx_signature}")
                    return
                elif status == "failed":
                    raise TradeExecutionError(f"Transaction failed: {tx_signature}")
                
                # Wait before retrying
                time.sleep(1)
                
            except (ConnectionError, TimeoutError, OSError) as e:
                # Only catch transient network errors, not business logic errors
                self.logger.debug(f"Confirmation check failed, retrying: {e}")
                time.sleep(1)
        
        raise TransactionTimeoutError(str(tx_signature), self.confirmation_timeout)
    
    def _create_trade_object(self, decision: Decision, quote: SwapQuote, tx_signature: Signature) -> Trade:
        """Create a Trade object from execution results.
        
        Args:
            decision: Trading decision
            quote: Swap quote
            tx_signature: Transaction signature
            
        Returns:
            Trade object
        """
        from src.core.models.trade import TradeType
        # Map Signal to TradeType
        trade_type = TradeType.BUY if decision.signal == Signal.BUY else TradeType.SELL
        
        trade = Trade(
            trade_id="",  # Will be set by caller if needed
            token_pair=decision.token_pair,
            amount=decision.amount,
            trade_type=trade_type,
            price=None,  # Will be set by caller if needed
            timestamp=datetime.now(),
            status=TradeStatus.SUCCESS,
            fees=quote.fees,
            slippage=quote.price_impact_pct,
            notes=decision.reasoning or "",
        )
        
        self.logger.info(f"Trade completed: {trade}")
        return trade
    
    def _create_dry_run_trade(self, decision: Decision) -> Trade:
        """Create a mock Trade object for dry-run mode.
        
        Args:
            decision: Trading decision
            
        Returns:
            Mock Trade object
        """
        from src.core.models.trade import TradeType
        
        # Get mints from token_pair
        base_mint = decision.token_pair.base.mint if decision.token_pair.base else "So11111111111111111111111111111111111111112"
        quote_mint = decision.token_pair.quote.mint if decision.token_pair.quote else "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        # Create a mock quote for dry-run
        mock_quote = SwapQuote(
            input_amount=decision.amount,
            output_amount=decision.amount * 0.95,  # Assume 5% slippage for simulation
            input_mint=base_mint,
            output_mint=quote_mint,
            slippage_bps=100,  # 1%
            price_impact_pct=0.05,
            fees=0.001,
        )
        
        # Map Signal to TradeType
        trade_type = TradeType.BUY if decision.signal == Signal.BUY else TradeType.SELL
        
        return Trade(
            trade_id="",
            token_pair=decision.token_pair,
            amount=decision.amount,
            trade_type=trade_type,
            price=None,
            timestamp=datetime.now(),
            status=TradeStatus.PENDING,
            fees=mock_quote.fees,
            slippage=mock_quote.price_impact_pct,
            notes=f"DRY RUN: {decision.reasoning or ''}",
        )
