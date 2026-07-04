"""
Unit tests for BalanceTracker service (US-014).

Tests cover:
- BalanceTracker class initialization
- get_sol_balance, get_token_balance, get_all_balances methods
- Error handling and edge cases
- Mock SolanaClient integration
"""

import asyncio
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import the classes under test
from src.core.services.balance_tracker import (
    BalanceTracker,
    BalanceTrackError,
    TokenNotFoundError,
)

# Import domain models (from US-010, US-011)
from src.core.models.price import Token
from src.core.models.balance import Balance


# Test fixtures
@pytest.fixture
def mock_solana_client():
    """Create a mock SolanaClient for testing."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_wallet():
    """Create a mock Wallet for testing."""
    wallet = Mock()
    wallet.public_key_str = "TestPubKey1111111111111111111111111111"
    wallet.pubkey = Mock(return_value="TestPubKey1111111111111111111111111111")
    return wallet


@pytest.fixture
def balance_tracker(mock_solana_client, mock_wallet):
    """Create a BalanceTracker instance with mock dependencies."""
    return BalanceTracker(solana_client=mock_solana_client, wallet=mock_wallet)


# ============================================================================
# BalanceTracker Class Tests
# ============================================================================

class TestBalanceTrackerInitialization:
    """Tests for BalanceTracker initialization."""

    def test_init_with_solana_client_and_wallet(self, mock_solana_client, mock_wallet):
        """Test initialization with SolanaClient and Wallet."""
        tracker = BalanceTracker(solana_client=mock_solana_client, wallet=mock_wallet)
        assert tracker.solana_client == mock_solana_client
        assert tracker.wallet == mock_wallet
        assert tracker.SOL_MINT == "So11111111111111111111111111111111111111112"


class TestBalanceTrackerGetSolBalance:
    """Tests for get_sol_balance method."""

    @pytest.mark.asyncio
    async def test_get_sol_balance_returns_float(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_sol_balance returns float value."""
        # Setup: mock get_balance to return a Balance object
        from src.infrastructure.solana.client import Balance as SolanaBalance
        mock_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=1000000000,  # 1 SOL in lamports
            decimals=9,
            ui_amount=1.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_balance
        
        # Call get_sol_balance
        result = await balance_tracker.get_sol_balance()
        
        # Verify result
        assert isinstance(result, float)
        assert result == 1.0

    @pytest.mark.asyncio
    async def test_get_sol_balance_with_zero(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_sol_balance with zero balance."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        mock_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=0,
            decimals=9,
            ui_amount=0.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_balance
        
        result = await balance_tracker.get_sol_balance()
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_get_sol_balance_with_exception(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_sol_balance with exception raises BalanceTrackError."""
        mock_solana_client.get_balance.side_effect = Exception("RPC Error")
        
        with pytest.raises(BalanceTrackError) as exc_info:
            await balance_tracker.get_sol_balance()
        
        assert "Failed to fetch SOL balance" in str(exc_info.value)


# ============================================================================
# get_token_balance Tests
# ============================================================================

class TestBalanceTrackerGetTokenBalance:
    """Tests for get_token_balance method."""

    @pytest.mark.asyncio
    async def test_get_token_balance_for_sol_mint(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_token_balance with SOL mint uses get_sol_balance."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        mock_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=2000000000,
            decimals=9,
            ui_amount=2.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_balance
        
        # Call with SOL mint
        result = await balance_tracker.get_token_balance("So11111111111111111111111111111111111111112")
        assert result == 2.0
        mock_solana_client.get_balance.assert_called_once()
        mock_solana_client.get_token_balance.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_token_balance_for_token_mint(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_token_balance for a token mint."""
        from src.infrastructure.solana.client import TokenBalance
        mock_token_balance = TokenBalance(
            address="TokenAccountAddress",
            amount=1000000,  # 1.0 token (6 decimals)
            decimals=6,
            ui_amount=1.0,
            mint_address="TestMint1111111111111111111111111111",
            owner_address=mock_wallet.public_key_str
        )
        mock_solana_client.get_token_balance.return_value = mock_token_balance
        
        result = await balance_tracker.get_token_balance("TestMint1111111111111111111111111111")
        assert result == 1.0

    @pytest.mark.asyncio
    async def test_get_token_balance_with_sol_lowercase(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_token_balance with 'sol' lowercase."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        mock_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=1500000000,
            decimals=9,
            ui_amount=1.5,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_balance
        
        result = await balance_tracker.get_token_balance("sol")
        assert result == 1.5

    @pytest.mark.asyncio
    async def test_get_token_balance_not_found(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_token_balance when token not found."""
        mock_solana_client.get_token_balance.return_value = None
        
        result = await balance_tracker.get_token_balance("UnknownMint11111111111111111111")
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_get_token_balance_with_exception(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_token_balance with exception raises BalanceTrackError."""
        mock_solana_client.get_token_balance.side_effect = Exception("RPC Error")
        
        with pytest.raises(BalanceTrackError) as exc_info:
            await balance_tracker.get_token_balance("TestMint1111111111111111111111111111")
        
        assert "Failed to fetch token balance" in str(exc_info.value)


# ============================================================================
# get_all_balances Tests
# ============================================================================

class TestBalanceTrackerGetAllBalances:
    """Tests for get_all_balances method."""

    @pytest.mark.asyncio
    async def test_get_all_balances_returns_dict(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_all_balances returns dictionary."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        
        # Mock SOL balance
        mock_sol_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=1000000000,
            decimals=9,
            ui_amount=1.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_sol_balance
        
        # Mock token accounts response
        mock_rpc_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "value": []
            }
        }
        mock_solana_client._http_request.return_value = mock_rpc_response
        
        result = await balance_tracker.get_all_balances()
        
        assert isinstance(result, dict)
        assert balance_tracker.SOL_MINT in result
        assert result[balance_tracker.SOL_MINT] == 1.0

    @pytest.mark.asyncio
    async def test_get_all_balances_with_token_accounts(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_all_balances with token accounts."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        
        # Mock SOL balance
        mock_sol_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=2000000000,
            decimals=9,
            ui_amount=2.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_sol_balance
        
        # Mock token accounts response with a USDC account
        mock_rpc_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "value": [
                    {
                        "pubkey": "TokenAccount1",
                        "account": {
                            "data": {
                                "parsed": {
                                    "info": {
                                        "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                                        "tokenAmount": {
                                            "amount": "1000000",
                                            "decimals": 6
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        mock_solana_client._http_request.return_value = mock_rpc_response
        
        result = await balance_tracker.get_all_balances()
        
        assert result[balance_tracker.SOL_MINT] == 2.0
        assert "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" in result
        # 1000000 with 6 decimals = 1.0
        assert result["EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"] == 1.0

    @pytest.mark.asyncio
    async def test_get_all_balances_rpc_failure_fallback(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_all_balances with RPC failure falls back gracefully."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        
        # Mock SOL balance
        mock_sol_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=1000000000,
            decimals=9,
            ui_amount=1.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_sol_balance
        
        # Mock RPC failure
        mock_solana_client._http_request.side_effect = Exception("RPC failure")
        
        result = await balance_tracker.get_all_balances()
        
        # Should still return SOL balance
        assert result[balance_tracker.SOL_MINT] == 1.0


# ============================================================================
# get_balance_for_token Tests
# ============================================================================

class TestBalanceTrackerGetBalanceForToken:
    """Tests for get_balance_for_token method."""

    @pytest.mark.asyncio
    async def test_get_balance_for_token_returns_balance_domain_model(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_balance_for_token returns Balance domain model."""
        from src.infrastructure.solana.client import TokenBalance
        
        # Create a token
        sol_token = Token(
            symbol="SOL",
            mint="So11111111111111111111111111111111111111112",
            decimals=9,
            name="Solana"
        )
        
        # Mock SOL balance
        from src.infrastructure.solana.client import Balance as SolanaBalance
        mock_sol_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=2000000000,
            decimals=9,
            ui_amount=2.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_sol_balance
        
        result = await balance_tracker.get_balance_for_token(sol_token)
        
        assert isinstance(result, Balance)
        assert result.amount == 2.0
        assert result.token == sol_token


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestBalanceTrackerEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_get_token_balance_with_empty_mint(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_token_balance with empty mint."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        mock_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=1000000000,
            decimals=9,
            ui_amount=1.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_balance
        
        result = await balance_tracker.get_token_balance("")
        assert result == 1.0  # Empty string treated as SOL

    @pytest.mark.asyncio
    async def test_get_all_balances_with_multiple_tokens(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test get_all_balances with multiple token accounts."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        
        # Mock SOL balance
        mock_sol_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=1000000000,
            decimals=9,
            ui_amount=1.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_sol_balance
        
        # Mock multiple token accounts
        mock_rpc_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "value": [
                    {
                        "pubkey": "TokenAccount1",
                        "account": {
                            "data": {
                                "parsed": {
                                    "info": {
                                        "mint": "TokenMint1",
                                        "tokenAmount": {"amount": "1000000000", "decimals": 9}
                                    }
                                }
                            }
                        }
                    },
                    {
                        "pubkey": "TokenAccount2",
                        "account": {
                            "data": {
                                "parsed": {
                                    "info": {
                                        "mint": "TokenMint2",
                                        "tokenAmount": {"amount": "5000000", "decimals": 6}
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        mock_solana_client._http_request.return_value = mock_rpc_response
        
        result = await balance_tracker.get_all_balances()
        
        assert result[balance_tracker.SOL_MINT] == 1.0
        assert result["TokenMint1"] == 1.0
        assert result["TokenMint2"] == 5.0


# ============================================================================
# Synchronous Wrapper Tests
# ============================================================================

class TestBalanceTrackerSyncWrappers:
    """Tests for synchronous wrapper methods."""

    def test_get_sol_balance_sync(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test synchronous get_sol_balance_sync."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        mock_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=1500000000,
            decimals=9,
            ui_amount=1.5,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_balance
        
        result = balance_tracker.get_sol_balance_sync()
        assert result == 1.5

    def test_get_token_balance_sync(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test synchronous get_token_balance_sync."""
        from src.infrastructure.solana.client import TokenBalance
        mock_token_balance = TokenBalance(
            address="TokenAccountAddress",
            amount=5000000,
            decimals=6,
            ui_amount=5.0,
            mint_address="TestMint",
            owner_address=mock_wallet.public_key_str
        )
        mock_solana_client.get_token_balance.return_value = mock_token_balance
        
        result = balance_tracker.get_token_balance_sync("TestMint")
        assert result == 5.0

    def test_get_all_balances_sync(self, balance_tracker, mock_solana_client, mock_wallet):
        """Test synchronous get_all_balances_sync."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        
        mock_sol_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=2000000000,
            decimals=9,
            ui_amount=2.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_sol_balance
        mock_solana_client._http_request.return_value = {
            "result": {"value": []}
        }
        
        result = balance_tracker.get_all_balances_sync()
        assert result[balance_tracker.SOL_MINT] == 2.0


# ============================================================================
# Logging Tests
# ============================================================================

class TestBalanceTrackerLogging:
    """Tests for logging behavior."""

    @pytest.mark.asyncio
    async def test_get_sol_balance_logging(self, balance_tracker, mock_solana_client, mock_wallet, caplog):
        """Test logging on SOL balance fetch."""
        from src.infrastructure.solana.client import Balance as SolanaBalance
        mock_balance = SolanaBalance(
            address=mock_wallet.public_key_str,
            amount=1000000000,
            decimals=9,
            ui_amount=1.0,
            symbol="SOL"
        )
        mock_solana_client.get_balance.return_value = mock_balance
        
        with caplog.at_level("DEBUG"):
            await balance_tracker.get_sol_balance()
        
        assert "SOL balance" in caplog.text

    @pytest.mark.asyncio
    async def test_error_logging(self, balance_tracker, mock_solana_client, mock_wallet, caplog):
        """Test logging on error."""
        mock_solana_client.get_balance.side_effect = Exception("RPC Error")
        
        with caplog.at_level("ERROR"):
            with pytest.raises(BalanceTrackError):
                await balance_tracker.get_sol_balance()
        
        assert "Error fetching SOL balance" in caplog.text
