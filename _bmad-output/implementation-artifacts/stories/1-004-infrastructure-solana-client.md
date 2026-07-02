---
title: "US-004: Infrastructure Layer - Solana Client"
story_id: "1-004-infrastructure-solana-client"
epic: "Epic 1: Project Setup & Infrastructure"
project: "Solana Trading Bot"
created: 2026-07-02
status: "ready-for-dev"
priority: P0
dependencies: ["US-001", "US-002", "US-003"]
estimate_hours: 6
type: "technical"
---

# US-004: Infrastructure Layer - Solana Client

## 🎯 User Story

**As a** developer  
**I want** a Solana RPC client with mixed approach  
**So that** I can query balances and manage transactions efficiently

## ✅ Acceptance Criteria

- [x] `SolanaClient` class in `src/interfaces/solana/client.py`
- [x] Use `solana-py` + `solders` for transaction signing
- [x] Use direct HTTP for balance and token account queries
- [x] Implemented methods: `get_balance`, `get_token_balance`, `confirm_transaction`
- [x] Proper error handling
- [x] Unit tests with mock RPC responses

## 📋 Tasks

- [x] Create SolanaClient class
- [x] Implement `get_balance` (using lib for SOL balance)
- [x] Implement `get_token_balance` (using HTTP for token accounts)
- [x] Implement `confirm_transaction` (using HTTP)
- [x] Add transaction signing with solana-py
- [x] Add transaction sending
- [x] Add error handling
- [x] Write unit tests

## 🏗️ Technical Implementation

### Mixed Approach (AD-006)

**Use `solana-py` + `solders` for:**
- Keypair management (`Keypair`)
- Transaction signing (`transaction.sign()`)
- Transaction sending (`send_transaction()`)
- Complex transaction building

**Use direct HTTP for:**
- Simple balance queries (`getBalance`)
- Token account queries (`getTokenAccountsByOwner`)
- Transaction confirmation (`getSignatureStatuses`)
- Transaction info (`getTransaction`)

### SolanaClient Class

**Location**: `src/interfaces/solana/client.py`

**Features**:
- Async HTTP client using both `httpx` and `solana-py`
- Context manager support (`async with client:`)
- Configurable RPC URL from settings
- Automatic retry with exponential backoff
- Devnet validation support

### Implemented Methods

#### Balance Methods
1. **`get_balance(address: str) -> Balance`**
   - Uses direct HTTP POST to RPC
   - Returns SOL balance in lamports and UI amount
   - Handles connection errors

2. **`get_token_balance(mint: str, owner: str, decimals: int) -> TokenBalance`**
   - Uses `getTokenAccountsByOwner` with mint filter
   - Returns token balance with mint and owner info
   - Handles missing accounts (returns 0 balance)

3. **`get_token_balances(owner: str, mints: List[str]) -> Dict[str, TokenBalance]`**
   - Gets all token accounts for owner in one call
   - Maps to requested mint addresses
   - Returns dict of mint -> TokenBalance

#### Transaction Methods
1. **`confirm_transaction(signature: str) -> TransactionStatus`**
   - Uses `getSignatureStatuses` RPC method
   - Returns confirmed status and error info
   - Supports timeout

2. **`get_transaction_info(signature: str) -> TransactionInfo`**
   - Uses `getTransaction` RPC method
   - Returns full transaction details including:
     - Slot
     - Fee
     - Status
     - Logs
     - Pre/post balances

3. **`sign_transaction(transaction: Transaction) -> Transaction`**
   - Uses solana-py Keypair
   - Loads keypair from environment or file
   - Signs transaction in place

4. **`send_transaction(transaction: Transaction) -> str`**
   - Uses solana-py AsyncClient
   - Returns transaction signature

5. **`send_and_confirm(transaction: Transaction) -> Tuple[str, TransactionStatus]`**
   - Signs, sends, and confirms transaction
   - Returns signature and status

#### Convenience Methods
1. **`transfer_sol(recipient: str, amount: float) -> Tuple[str, TransactionStatus]`**
   - Builds transfer transaction
   - Signs, sends, and confirms
   - Returns signature and status

2. **`get_recent_blockhash() -> Hash`**
   - Gets recent blockhash for transactions
   - Required for transaction building

3. **`get_keypair() -> Keypair`**
   - Loads keypair from configuration
   - Supports both private key string and keypair file

4. **`get_public_key() -> PublicKey`**
   - Gets public key from keypair

### Error Handling

**Exception Hierarchy**:
```
SolanaError (base)
├── SolanaConnectionError (HTTP/connection failures)
├── SolanaRPCError (RPC call failures)
├── SolanaTransactionError (transaction failures)
├── SolanaSigningError (signing failures)
└── SolanaBalanceError (balance query failures)
```

**Retry Logic**:
- Exponential backoff: delay * (2 ^ attempt)
- Configurable max retries (default: 3)
- Handles RPC errors gracefully

### Data Classes

- `Balance`: SOL balance with raw and UI amounts
- `TokenBalance`: Token balance with mint and owner info
- `TransactionStatus`: Confirmation status and error info
- `TransactionInfo`: Full transaction details

## 📁 File Changes Required

1. `src/interfaces/solana/client.py` - Main client implementation
2. `src/interfaces/solana/__init__.py` - Module exports
3. `tests/unit/test_solana_client.py` - Unit tests with mocks

## 🧪 Testing Strategy

### Mock Testing
```python
from unittest.mock import AsyncMock, patch
from httpx import Response
from src.interfaces.solana.client import SolanaClient

# Mock successful balance query
with patch.object(client, '_http_request', new_callable=AsyncMock) as mock:
    mock.return_value = {
        "jsonrpc": "2.0",
        "result": {"value": 1000000000}
    }
    balance = await client.get_balance("Addr123")
    assert balance.ui_amount == 1.0

# Mock confirmed transaction
with patch.object(client, '_http_request', new_callable=AsyncMock) as mock:
    mock.return_value = {
        "result": {"value": [{"confirmationStatus": "confirmed"}]}
    }
    status = await client.confirm_transaction("sig123")
    assert status.confirmed is True
```

### Error Testing
```python
# Test connection failure
with patch.object(client, '_http_request', new_callable=AsyncMock) as mock:
    mock.side_effect = Exception("Connection failed")
    with pytest.raises(SolanaBalanceError):
        await client.get_balance("Addr123")
```

## 📊 Success Metrics

- All methods implemented and tested
- Mixed approach (lib + HTTP) works correctly
- Error handling covers all edge cases
- Unit tests pass with mock responses
- Client can be used as async context manager
- Integration with config/settings works
- Devnet validation is supported

## ⚡ Dependencies

- US-001: Project Structure Setup (must have `src/interfaces/solana/`)
- US-002: Environment Configuration (must have settings for RPC URL)
- US-003: Infrastructure - Jupiter Client (parallel development)

## 📝 Notes

- Follows AD-006: Mixed Approach for Solana Interaction
- Uses solana-py only when it provides significant value
- Direct HTTP for simple queries improves performance
- Transaction signing requires private key in environment
- All I/O is async for consistency

---
*Generated for BMad workflow - Solana Trading Bot Project*