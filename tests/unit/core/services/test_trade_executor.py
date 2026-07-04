"""
Unit tests for TradeExecutor Service (US-015)

Tests cover:
- TradeExecutor class initialization
- execute_trade method
- Error handling (TradeExecutionError, InsufficientFundsError, SlippageError, TransactionTimeoutError)
- Dry-run mode
- Mock dependencies (JupiterClient, Wallet, SolanaClient)
"""

from __future__ import annotations

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.core.models.price import Token, TokenPair
from src.core.models.trade import Decision, Signal, TradeType, TradeStatus


# Helper to create test objects
def create_sol_token():
    """Create SOL token."""
    return Token(symbol="SOL", mint="So11111111111111111111111111111111111111112", decimals=9)


def create_usdc_token():
    """Create USDC token."""
    return Token(symbol="USDC", mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals=6)


def create_token_pair():
    """Create SOL/USDC token pair."""
    return TokenPair(base=create_sol_token(), quote=create_usdc_token())


def create_decision(token_pair=None, signal=Signal.BUY, amount=0.1, confidence=0.8):
    """Create a Decision for testing."""
    if token_pair is None:
        token_pair = create_token_pair()
    
    return Decision(
        decision_id="test-1",
        token_pair=token_pair,
        signal=signal,
        confidence=confidence,
        amount=amount,
        timestamp=datetime.now(),
        reasoning="Test trade",
    )


class TestTradeExecutorInitialization:
    """Tests for TradeExecutor initialization."""

    def test_init_with_required_dependencies(self, mock_jupiter_client, mock_wallet, mock_solana_client):
        """Test TradeExecutor initialization with all required dependencies."""
        from src.core.services.trade_executor import TradeExecutor
        
        executor = TradeExecutor(
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            solana_client=mock_solana_client,
        )
        
        assert executor.jupiter_client == mock_jupiter_client
        assert executor.wallet == mock_wallet
        assert executor.solana_client == mock_solana_client
        assert executor.dry_run_mode is False
        assert executor.slippage_threshold == 0.01
        assert executor.confirmation_timeout == 60
    
    def test_init_with_optional_parameters(self, mock_jupiter_client, mock_wallet, mock_solana_client):
        """Test TradeExecutor initialization with optional parameters."""
        from src.core.services.trade_executor import TradeExecutor
        
        executor = TradeExecutor(
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            solana_client=mock_solana_client,
            dry_run_mode=True,
            slippage_threshold=0.05,
            confirmation_timeout=120,
        )
        
        assert executor.dry_run_mode is True
        assert executor.slippage_threshold == 0.05
        assert executor.confirmation_timeout == 120
    
    def test_init_with_balance_tracker(self, mock_jupiter_client, mock_wallet, mock_solana_client, mock_balance_tracker):
        """Test TradeExecutor initialization with BalanceTracker."""
        from src.core.services.trade_executor import TradeExecutor
        
        executor = TradeExecutor(
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            solana_client=mock_solana_client,
            balance_tracker=mock_balance_tracker,
        )
        
        assert executor.balance_tracker == mock_balance_tracker


class TestTradeExecutorExecuteTrade:
    """Tests for execute_trade method."""

    @pytest.fixture
    def trade_executor(self, mock_jupiter_client, mock_wallet, mock_solana_client):
        """Create a TradeExecutor instance for testing."""
        from src.core.services.trade_executor import TradeExecutor
        return TradeExecutor(
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            solana_client=mock_solana_client,
        )

    def test_execute_trade_dry_run_mode(self, trade_executor):
        """Test execute_trade in dry-run mode returns mock Trade."""
        trade_executor.dry_run_mode = True
        
        decision = create_decision(amount=0.1)
        
        result = trade_executor.execute_trade(decision)
        
        assert result is not None
        assert result.status.name == "PENDING"
        assert "DRY RUN" in result.notes
    
    def test_execute_trade_invalid_decision_no_pair(self, trade_executor):
        """Test execute_trade raises error when decision has no token_pair."""
        from src.core.services.trade_executor import TradeExecutionError
        
        decision = Decision(
            decision_id="test-1",
            token_pair=None,
            signal=Signal.BUY,
            confidence=0.8,
            amount=0.1,
            timestamp=datetime.now(),
        )
        
        with pytest.raises(TradeExecutionError, match="Decision must have a token pair"):
            trade_executor.execute_trade(decision)
    
    def test_execute_trade_invalid_amount_zero(self, trade_executor):
        """Test execute_trade raises error when amount is zero."""
        from src.core.services.trade_executor import TradeExecutionError
        
        decision = create_decision(amount=0)
        
        with pytest.raises(TradeExecutionError, match="Trade amount must be positive"):
            trade_executor.execute_trade(decision)
    
    def test_execute_trade_invalid_amount_negative(self, trade_executor):
        """Test execute_trade raises error when amount is negative."""
        from src.core.services.trade_executor import TradeExecutionError
        
        decision = create_decision(amount=-0.1)
        
        with pytest.raises(TradeExecutionError, match="Trade amount must be positive"):
            trade_executor.execute_trade(decision)
    
    def test_execute_trade_invalid_signal(self, trade_executor):
        """Test execute_trade raises error when signal is invalid (None)."""
        from src.core.services.trade_executor import TradeExecutionError
        
        decision = create_decision(signal=None, amount=0.1)
        
        with pytest.raises(TradeExecutionError, match="Invalid trade signal"):
            trade_executor.execute_trade(decision)


class TestTradeExecutorValidation:
    """Tests for validation methods."""

    @pytest.fixture
    def trade_executor_with_balance(self, mock_jupiter_client, mock_wallet, mock_solana_client, mock_balance_tracker):
        """Create TradeExecutor with BalanceTracker."""
        from src.core.services.trade_executor import TradeExecutor
        return TradeExecutor(
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            solana_client=mock_solana_client,
            balance_tracker=mock_balance_tracker,
        )

    def test_validate_balance_sufficient_sol(self, trade_executor_with_balance):
        """Test balance validation passes with sufficient SOL."""
        decision = create_decision(amount=0.1)
        
        trade_executor_with_balance.balance_tracker.get_sol_balance.return_value = 10.0
        
        with patch.object(trade_executor_with_balance, '_get_input_mint', return_value="So11111111111111111111111111111111111111112"):
            # No exception should be raised
            trade_executor_with_balance._validate_balance(decision)
            
            trade_executor_with_balance.balance_tracker.get_sol_balance.assert_called_once()
    
    def test_validate_balance_insufficient_sol(self, trade_executor_with_balance):
        """Test balance validation raises InsufficientFundsError for insufficient SOL."""
        from src.core.services.trade_executor import InsufficientFundsError
        
        decision = create_decision(amount=10.0)
        
        trade_executor_with_balance.balance_tracker.get_sol_balance.return_value = 5.0
        
        with patch.object(trade_executor_with_balance, '_get_input_mint', return_value="So11111111111111111111111111111111111111112"):
            with pytest.raises(InsufficientFundsError) as exc_info:
                trade_executor_with_balance._validate_balance(decision)
            
            assert exc_info.value.required == 10.0
            assert exc_info.value.available == 5.0
            assert exc_info.value.token == "SOL"
    
    def test_validate_balance_skipped_on_error(self, trade_executor_with_balance):
        """Test balance validation continues if BalanceTracker raises error."""
        decision = create_decision(amount=0.1)
        
        trade_executor_with_balance.balance_tracker.get_sol_balance.side_effect = Exception("Connection error")
        
        # Mock _get_input_mint to return SOL mint so it tries get_sol_balance
        with patch.object(trade_executor_with_balance, '_get_input_mint', return_value="So11111111111111111111111111111111111111112"):
            # Should not raise, just log warning
            trade_executor_with_balance._validate_balance(decision)
            
            # Verify that get_sol_balance was called
            trade_executor_with_balance.balance_tracker.get_sol_balance.assert_called_once()


class TestTradeExecutorSwapQuote:
    """Tests for swap quote functionality."""

    @pytest.fixture
    def trade_executor(self, mock_jupiter_client, mock_wallet, mock_solana_client):
        from src.core.services.trade_executor import TradeExecutor
        return TradeExecutor(
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            solana_client=mock_solana_client,
        )

    def test_get_swap_quote_success(self, trade_executor, mock_jupiter_client):
        """Test getting swap quote from Jupiter API."""
        decision = create_decision(amount=0.1)
        
        mock_jupiter_client.quote_swap.return_value = {
            "outAmount": 0.5,
            "priceImpactPct": 0.02,
            "fees": 0.001,
        }
        
        quote = trade_executor._get_swap_quote(decision)
        
        assert quote.input_amount == 0.1
        assert quote.output_amount == 0.5
        assert quote.fees == 0.001
        
        mock_jupiter_client.quote_swap.assert_called_once()
    
    def test_get_swap_quote_failure(self, trade_executor, mock_jupiter_client):
        """Test swap quote failure raises TradeExecutionError."""
        from src.core.services.trade_executor import TradeExecutionError
        
        decision = create_decision(amount=0.1)
        
        mock_jupiter_client.quote_swap.side_effect = Exception("API error")
        
        with pytest.raises(TradeExecutionError, match="Failed to get swap quote"):
            trade_executor._get_swap_quote(decision)


class TestTradeExecutorSwapExecution:
    """Tests for swap execution functionality."""

    @pytest.fixture
    def trade_executor(self, mock_jupiter_client, mock_wallet, mock_solana_client):
        from src.core.services.trade_executor import TradeExecutor
        return TradeExecutor(
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            solana_client=mock_solana_client,
        )

    def test_execute_swap_success(self, trade_executor, mock_jupiter_client):
        """Test successful swap execution."""
        from solders.signature import Signature
        
        decision = create_decision(amount=0.1)
        
        # Mock the swap to return a valid signature string
        mock_jupiter_client.swap.return_value = {"txid": "5VERv8NMvnb294x5XSS4jD2XX853QX8pR8Dr6L7KmmCkD5qe3DnSx9YLi3si9rbfGd7StXhRnSW6KeQnDLN4J7Jd"}
        
        from src.core.services.trade_executor import SwapQuote
        quote = SwapQuote(
            input_amount=0.1,
            output_amount=0.5,
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            slippage_bps=100,
            price_impact_pct=0.05,
            fees=0.001,
        )
        
        result = trade_executor._execute_swap(decision, quote)
        
        assert isinstance(result, Signature)
        # The signature string is a real base58 encoded signature
        assert len(str(result)) > 0
    
    def test_execute_swap_no_signature(self, trade_executor, mock_jupiter_client):
        """Test swap execution fails when no signature returned."""
        from src.core.services.trade_executor import TradeExecutionError
        
        decision = create_decision(amount=0.1)
        
        mock_jupiter_client.swap.return_value = {}
        
        from src.core.services.trade_executor import SwapQuote
        quote = SwapQuote(
            input_amount=0.1,
            output_amount=0.5,
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            slippage_bps=100,
            price_impact_pct=0.05,
            fees=0.001,
        )
        
        with pytest.raises(TradeExecutionError, match="No transaction signature returned"):
            trade_executor._execute_swap(decision, quote)


class TestTradeExecutorConfirmation:
    """Tests for transaction confirmation functionality."""

    @pytest.fixture
    def trade_executor(self, mock_jupiter_client, mock_wallet, mock_solana_client):
        from src.core.services.trade_executor import TradeExecutor
        return TradeExecutor(
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            solana_client=mock_solana_client,
            confirmation_timeout=5,
        )

    @patch('time.time')
    @patch('time.sleep')
    def test_confirm_transaction_success(self, mock_sleep, mock_time, trade_executor, mock_solana_client):
        """Test successful transaction confirmation."""
        from solders.signature import Signature
        
        mock_time.side_effect = [0, 1, 2]
        mock_solana_client.get_transaction_status.return_value = "confirmed"
        
        # Create a mock signature
        tx_sig = MagicMock(spec=Signature)
        tx_sig.__str__ = MagicMock(return_value="mock_signature")
        
        trade_executor._confirm_transaction(tx_sig)
        
        mock_solana_client.get_transaction_status.assert_called_once_with("mock_signature")
    
    @patch('time.time')
    @patch('time.sleep')
    def test_confirm_transaction_failed(self, mock_sleep, mock_time, mock_jupiter_client, mock_wallet, mock_solana_client):
        """Test transaction confirmation fails."""
        from src.core.services.trade_executor import TradeExecutor, TradeExecutionError
        from solders.signature import Signature
        
        mock_solana_client.get_transaction_status.return_value = "failed"
        
        # Create executor
        executor = TradeExecutor(
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            solana_client=mock_solana_client,
            confirmation_timeout=5,
        )
        
        # Create a mock signature
        tx_sig = MagicMock(spec=Signature)
        tx_sig.__str__ = MagicMock(return_value="mock_signature")
        
        # start_time = time.time() -> 0, while condition: time.time() -> 0.1 (< 5, enters loop)
        # Then get_transaction_status returns "failed", raises error
        mock_time.side_effect = [0, 0.1, 10]
        
        with pytest.raises(TradeExecutionError, match="Transaction failed"):
            executor._confirm_transaction(tx_sig)
    
    @patch('time.time')
    @patch('time.sleep')
    def test_confirm_transaction_timeout(self, mock_sleep, mock_time, trade_executor, mock_solana_client):
        """Test transaction confirmation times out."""
        from src.core.services.trade_executor import TransactionTimeoutError
        from solders.signature import Signature
        
        mock_time.side_effect = [0, 6, 12]
        mock_solana_client.get_transaction_status.return_value = "pending"
        
        # Create a mock signature
        tx_sig = MagicMock(spec=Signature)
        tx_sig.__str__ = MagicMock(return_value="mock_signature")
        
        with pytest.raises(TransactionTimeoutError) as exc_info:
            trade_executor._confirm_transaction(tx_sig)
        
        assert exc_info.value.tx_signature == "mock_signature"
        assert exc_info.value.timeout == 5


class TestTradeExecutorDryRun:
    """Tests for dry-run mode functionality."""

    @pytest.fixture
    def trade_executor(self, mock_jupiter_client, mock_wallet, mock_solana_client):
        from src.core.services.trade_executor import TradeExecutor
        return TradeExecutor(
            jupiter_client=mock_jupiter_client,
            wallet=mock_wallet,
            solana_client=mock_solana_client,
            dry_run_mode=True,
        )

    def test_dry_run_does_not_execute(self, trade_executor, mock_jupiter_client, mock_solana_client):
        """Test that dry-run mode does not execute real trades."""
        decision = create_decision(amount=0.1)
        
        result = trade_executor.execute_trade(decision)
        
        mock_jupiter_client.swap.assert_not_called()
        mock_solana_client.get_transaction_status.assert_not_called()
        
        assert result is not None
        assert result.status.name == "PENDING"
    
    def test_dry_run_returns_mock_trade(self, trade_executor):
        """Test that dry-run mode returns a mock Trade object."""
        decision = create_decision(amount=0.1)
        
        result = trade_executor.execute_trade(decision)
        
        assert result is not None
        assert result.status.name == "PENDING"
        assert result.amount == 0.1
        assert "DRY RUN" in result.notes


# Fixtures for test dependencies

@pytest.fixture
def mock_jupiter_client():
    """Create a mock JupiterClient."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_wallet():
    """Create a mock Wallet."""
    mock = MagicMock()
    mock.public_key = "mock_public_key"
    return mock


@pytest.fixture
def mock_solana_client():
    """Create a mock SolanaClient."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_balance_tracker():
    """Create a mock BalanceTracker."""
    mock = MagicMock()
    mock.get_sol_balance.return_value = 10.0
    mock.get_token_balance.return_value = 100.0
    return mock
