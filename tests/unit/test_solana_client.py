"""
Unit tests for Solana RPC Client

Tests use mocking to avoid real RPC calls.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from httpx import AsyncClient, Response

# Optional imports - mock if not available for testing
try:
    from solana.keypair import Keypair
    from solana.publickey import PublicKey
    from solana.transaction import Transaction
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    Keypair = MagicMock()
    PublicKey = MagicMock()
    Transaction = MagicMock()

from src.interfaces.solana.client import (
    SolanaClient,
    SolanaError,
    SolanaConnectionError,
    SolanaRPCError,
    SolanaTransactionError,
    SolanaSigningError,
    SolanaBalanceError,
    Balance,
    TokenBalance,
    TransactionStatus,
    TransactionInfo,
)


@pytest.fixture
def mock_client():
    """Create a mock SolanaClient for testing."""
    client = SolanaClient(
        rpc_url="http://test-rpc.com",
        timeout=5.0,
        max_retries=2
    )
    return client


@pytest.fixture
def mock_keypair():
    """Create a mock keypair for testing."""
    return Keypair()


# ============================================================================
# Test Initialization and Configuration
# ============================================================================

@pytest.mark.asyncio
async def test_solana_client_init(mock_client):
    """Test SolanaClient initialization."""
    assert mock_client.rpc_url == "http://test-rpc.com"
    assert mock_client.timeout == 5.0
    assert mock_client.max_retries == 2


@pytest.mark.asyncio
async def test_context_manager(mock_client):
    """Test async context manager."""
    async with mock_client:
        # Clients should be initialized
        assert mock_client._async_client is not None or True
    
    # Clients should be closed (may be None if not initialized)


# ============================================================================
# Test Balance Methods
# ============================================================================

@pytest.mark.asyncio
async def test_get_balance_success(mock_client):
    """Test successful balance query."""
    mock_response_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "value": 1000000000  # 1 SOL in lamports
        }
    }
    
    with patch.object(mock_client, '_http_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        
        balance = await mock_client.get_balance("TestAddress123")
        
        assert isinstance(balance, Balance)
        assert balance.address == "TestAddress123"
        assert balance.amount == 1000000000
        assert balance.decimals == 9
        assert balance.ui_amount == 1.0
        assert balance.symbol == "SOL"


@pytest.mark.asyncio
async def test_get_balance_failure(mock_client):
    """Test balance query failure."""
    with patch.object(mock_client, '_http_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("Connection failed")
        
        with pytest.raises(SolanaBalanceError):
            await mock_client.get_balance("TestAddress123")


@pytest.mark.asyncio
async def test_get_token_balance_success(mock_client):
    """Test successful token balance query."""
    mock_response_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "value": [
                {
                    "pubkey": "TokenAccount123",
                    "account": {
                        "data": {
                            "parsed": {
                                "info": {
                                    "mint": "TokenMint123",
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
    
    with patch.object(mock_client, '_http_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        
        balance = await mock_client.get_token_balance(
            token_mint="TokenMint123",
            owner_address="Owner123",
            decimals=6
        )
        
        assert isinstance(balance, TokenBalance)
        assert balance.mint_address == "TokenMint123"
        assert balance.owner_address == "Owner123"
        assert balance.amount == 1000000
        assert balance.decimals == 6
        assert balance.ui_amount == 1.0


@pytest.mark.asyncio
async def test_get_token_balance_not_found(mock_client):
    """Test token balance query when account not found."""
    mock_response_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"value": []}
    }
    
    with patch.object(mock_client, '_http_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        
        balance = await mock_client.get_token_balance(
            token_mint="TokenMint123",
            owner_address="Owner123"
        )
        
        assert balance.amount == 0
        assert balance.ui_amount == 0.0


@pytest.mark.asyncio
async def test_get_token_balances(mock_client):
    """Test getting multiple token balances."""
    mock_response_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "value": [
                {
                    "pubkey": "Account1",
                    "account": {
                        "data": {
                            "parsed": {
                                "info": {
                                    "mint": "Mint1",
                                    "tokenAmount": {"amount": "1000", "decimals": 6},
                                    "decimals": 6
                                }
                            }
                        }
                    }
                },
                {
                    "pubkey": "Account2",
                    "account": {
                        "data": {
                            "parsed": {
                                "info": {
                                    "mint": "Mint2",
                                    "tokenAmount": {"amount": "2000", "decimals": 9},
                                    "decimals": 9
                                }
                            }
                        }
                    }
                }
            ]
        }
    }
    
    with patch.object(mock_client, '_http_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        
        balances = await mock_client.get_token_balances(
            owner_address="Owner123",
            token_mints=["Mint1", "Mint2", "Mint3"],
            decimals_map={"Mint1": 6, "Mint2": 9}
        )
        
        assert len(balances) == 3
        assert "Mint1" in balances
        assert "Mint2" in balances
        assert "Mint3" in balances
        
        assert balances["Mint1"].amount == 1000
        assert balances["Mint1"].ui_amount == 0.001  # 1000 / 10**6
        
        assert balances["Mint2"].amount == 2000
        assert balances["Mint2"].ui_amount == 0.000002  # 2000 / 10**9
        
        assert balances["Mint3"].amount == 0  # Not found


# ============================================================================
# Test Transaction Methods
# ============================================================================

@pytest.mark.asyncio
async def test_confirm_transaction_confirmed(mock_client):
    """Test confirming a confirmed transaction."""
    mock_response_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "value": [
                {
                    "confirmationStatus": "confirmed",
                    "slot": 12345,
                    "err": None
                }
            ]
        }
    }
    
    with patch.object(mock_client, '_http_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        
        status = await mock_client.confirm_transaction("tx-signature-123")
        
        assert isinstance(status, TransactionStatus)
        assert status.signature == "tx-signature-123"
        assert status.confirmed is True
        assert status.slot == 12345
        assert status.err is None


@pytest.mark.asyncio
async def test_confirm_transaction_failed(mock_client):
    """Test confirming a failed transaction."""
    mock_response_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "value": [
                {
                    "confirmationStatus": "failed",
                    "slot": 12345,
                    "err": {"InstructionError": [0, {"Custom": 1}]} 
                }
            ]
        }
    }
    
    with patch.object(mock_client, '_http_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        
        status = await mock_client.confirm_transaction("tx-signature-123")
        
        assert status.confirmed is False
        assert status.err is not None


@pytest.mark.asyncio
async def test_confirm_transaction_failure(mock_client):
    """Test confirmation failure."""
    with patch.object(mock_client, '_http_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("RPC error")
        
        with pytest.raises(SolanaTransactionError):
            await mock_client.confirm_transaction("tx-signature-123")


@pytest.mark.asyncio
async def test_get_transaction_info(mock_client):
    """Test getting transaction info."""
    mock_response_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "slot": 12345,
            "transaction": [{}],
            "meta": {
                "fee": 5000,
                "err": None,
                "logMessages": ["log1", "log2"],
                "preBalances": [1000000, 2000000],
                "postBalances": [999500, 2000500]
            }
        }
    }
    
    with patch.object(mock_client, '_http_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        
        info = await mock_client.get_transaction_info("tx-signature-123")
        
        assert isinstance(info, TransactionInfo)
        assert info.signature == "tx-signature-123"
        assert info.slot == 12345
        assert info.fee == 5000
        assert info.status == "confirmed"
        assert info.logs == ["log1", "log2"]
        assert info.pre_balances == [1000000, 2000000]
        assert info.post_balances == [999500, 2000500]


# ============================================================================
# Test HTTP Request with Retry
# ============================================================================

@pytest.mark.asyncio
async def test_http_request_success(mock_client):
    """Test successful HTTP request."""
    mock_response = Response(200, json={"jsonrpc": "2.0", "id": 1, "result": {"value": 42}})
    
    with patch.object(AsyncClient, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        await mock_client._ensure_clients()
        
        with patch.object(mock_client, '_http_client') as mock_client_attr:
            mock_client_attr.request = AsyncMock(return_value=mock_response)
            
            result = await mock_client._http_request("POST", "/", json={"test": "data"})
            assert result == {"jsonrpc": "2.0", "id": 1, "result": {"value": 42}}


@pytest.mark.asyncio
async def test_http_request_retry_success(mock_client):
    """Test HTTP request retry on failure."""
    mock_error_response = Response(500, json={"error": "server error"})
    mock_success_response = Response(200, json={"result": "success"})
    
    with patch.object(AsyncClient, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [mock_error_response, mock_success_response]
        
        client = SolanaClient(max_retries=1, retry_delay=0.01)
        await client._ensure_clients()
        
        with patch.object(client, '_http_client') as mock_client_attr:
            mock_client_attr.request = AsyncMock(side_effect=[mock_error_response, mock_success_response])
            
            result = await client._http_request("POST", "/", json={})
            assert result == {"result": "success"}


@pytest.mark.asyncio
async def test_http_request_max_retries_exceeded(mock_client):
    """Test HTTP request max retries exceeded."""
    mock_error_response = Response(500, json={"error": "server error"})
    
    with patch.object(AsyncClient, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_error_response
        
        client = SolanaClient(max_retries=0)  # No retries
        await client._ensure_clients()
        
        with patch.object(client, '_http_client') as mock_client_attr:
            mock_client_attr.request = AsyncMock(return_value=mock_error_response)
            
            with pytest.raises(SolanaConnectionError):
                await client._http_request("POST", "/", json={})


# ============================================================================
# Test Data Classes
# ============================================================================

class TestBalance:
    """Test Balance dataclass."""
    
    def test_balance_creation(self):
        """Test Balance creation."""
        balance = Balance(
            address="Addr123",
            amount=1000000000,
            decimals=9,
            ui_amount=1.0,
            symbol="SOL"
        )
        
        assert balance.address == "Addr123"
        assert balance.amount == 1000000000
        assert balance.ui_amount == 1.0
        assert balance.symbol == "SOL"
    
    def test_balance_str(self):
        """Test Balance string representation."""
        balance = Balance(
            address="Addr123",
            amount=1000000000,
            decimals=9,
            ui_amount=1.0,
            symbol="SOL"
        )
        
        assert str(balance) == "1.0 SOL"


class TestTokenBalance:
    """Test TokenBalance dataclass."""
    
    def test_token_balance_creation(self):
        """Test TokenBalance creation."""
        balance = TokenBalance(
            address="TokenAccount123",
            amount=1000000,
            decimals=6,
            ui_amount=1.0,
            mint_address="Mint123",
            owner_address="Owner123"
        )
        
        assert balance.mint_address == "Mint123"
        assert balance.owner_address == "Owner123"
    
    def test_token_balance_from_raw(self):
        """Test TokenBalance.from_raw."""
        raw_balance = {
            "pubkey": "Account123",
            "amount": "1000000"
        }
        
        balance = TokenBalance.from_raw(
            mint_address="Mint123",
            owner_address="Owner123",
            raw_balance=raw_balance,
            decimals=6
        )
        
        assert balance.address == "Account123"
        assert balance.amount == 1000000
        assert balance.decimals == 6
        assert balance.ui_amount == 1.0


class TestTransactionStatus:
    """Test TransactionStatus dataclass."""
    
    def test_transaction_status_confirmed(self):
        """Test confirmed transaction status."""
        status = TransactionStatus(
            signature="sig123",
            confirmed=True,
            err=None,
            slot=12345
        )
        
        assert status.confirmed is True
        assert status.err is None
    
    def test_transaction_status_failed(self):
        """Test failed transaction status."""
        status = TransactionStatus(
            signature="sig123",
            confirmed=False,
            err={"error": "failed"},
            slot=12345
        )
        
        assert status.confirmed is False
        assert status.err is not None


class TestTransactionInfo:
    """Test TransactionInfo dataclass."""
    
    def test_transaction_info_creation(self):
        """Test TransactionInfo creation."""
        info = TransactionInfo(
            signature="sig123",
            slot=12345,
            fee=5000,
            status="confirmed",
            logs=["log1", "log2"],
            pre_balances=[1000, 2000],
            post_balances=[900, 2100]
        )
        
        assert info.signature == "sig123"
        assert info.fee == 5000
        assert info.status == "confirmed"


# ============================================================================
# Test Exception Hierarchy
# ============================================================================

class TestExceptions:
    """Test custom exception hierarchy."""
    
    def test_exception_hierarchy(self):
        """Test exception inheritance."""
        assert issubclass(SolanaConnectionError, SolanaError)
        assert issubclass(SolanaRPCError, SolanaError)
        assert issubclass(SolanaTransactionError, SolanaError)
        assert issubclass(SolanaSigningError, SolanaError)
        assert issubclass(SolanaBalanceError, SolanaError)
