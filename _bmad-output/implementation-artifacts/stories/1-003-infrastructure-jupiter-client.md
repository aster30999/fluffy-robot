---
title: "US-003: Infrastructure Layer - Jupiter Client"
story_id: "1-003-infrastructure-jupiter-client"
epic: "Epic 1: Project Setup & Infrastructure"
project: "Solana Trading Bot"
created: 2026-07-02
status: "ready-for-dev"
priority: P0
dependencies: ["US-001", "US-002"]
estimate_hours: 6
type: "technical"
---

# US-003: Infrastructure Layer - Jupiter Client

## 🎯 User Story

**As a** developer  
**I want** a robust Jupiter API V2 HTTP client  
**So that** I can reliably fetch prices and execute trades

## ✅ Acceptance Criteria

- [x] `JupiterClient` class in `src/interfaces/jupiter/client.py`
- [x] Async HTTP client using `httpx`
- [x] Implemented endpoints: `/quote`, `/order`, `/execute`
- [x] Proper error handling (rate limiting, timeout, invalid response)
- [x] Retry with exponential backoff
- [x] API key support for higher rate limits
- [x] Unit tests with mock responses

## 📋 Tasks

- [x] Create JupiterClient class
- [x] Implement `/quote` endpoint
- [x] Implement `/order` endpoint
- [x] Implement `/execute` endpoint
- [x] Add error handling
- [x] Add retry logic
- [x] Add API key support
- [x] Write unit tests

## 🏗️ Technical Implementation

### JupiterClient Class

**Location**: `src/interfaces/jupiter/client.py`

**Features**:
- Async HTTP client using `httpx.AsyncClient`
- Context manager support (`async with client:`)
- Configurable base URL, timeout, retries
- Automatic API key injection from settings

### Endpoints Implemented

1. **`/v6/quote`** (GET)
   - Get price quote for token swap
   - Parameters: inputMint, outputMint, amount, slippageBps, swapMode
   - Returns: QuoteResponse (input_amount, output_amount, price_impact, fees, route)

2. **`/v6/order`** (POST)
   - Create swap order from quote
   - Parameters: quoteId, wrapUnwrapSol
   - Returns: OrderResponse (swap_transaction, setup_transaction, cleanup_transaction)

3. **`/v6/execute`** (POST)
   - Execute swap transaction
   - Parameters: swapTransaction, setupTransaction, cleanupTransaction
   - Returns: ExecuteResponse (transaction_signature)

### Convenience Methods

- `swap()`: Quote + Order + Execute in one call
- `get_price()`: Get current price for a pair
- `get_tokens()`: Get list of supported tokens

### Error Handling

**Exception Hierarchy**:
```
JupiterError (base)
├── JupiterRateLimitError (429)
├── JupiterTimeoutError (timeout)
├── JupiterInvalidResponseError (400, invalid JSON)
├── JupiterQuoteError (quote-specific)
├── JupiterOrderError (order-specific)
└── JupiterExecuteError (execute-specific)
```

**Retry Logic**:
- Exponential backoff: delay * (2 ^ attempt)
- Respects Retry-After header
- Configurable max retries (default: 3)
- Configurable initial delay (default: 1.0s)

### Data Classes

- `QuoteResponse`: Quote result with all details
- `OrderResponse`: Order with transaction data
- `ExecuteResponse`: Execution with signature
- `Token`: Token information

## 📁 File Changes Required

1. `src/interfaces/jupiter/client.py` - Main client implementation
2. `src/interfaces/jupiter/__init__.py` - Module exports
3. `tests/unit/test_jupiter_client.py` - Unit tests with mocks

## 🧪 Testing Strategy

### Mock Testing
```python
from unittest.mock import AsyncMock, patch
from httpx import Response
from src.interfaces.jupiter.client import JupiterClient

# Mock successful quote
with patch.object(client, '_request', new_callable=AsyncMock) as mock:
    mock.return_value = {"outAmount": "1000", "quoteId": "123"}
    quote = await client.get_quote("SOL", "USDC", "1")
    assert quote.output_amount == 1000.0

# Mock rate limiting
with patch.object(client, '_request', new_callable=AsyncMock) as mock:
    mock.side_effect = [
        Response(429, headers={"retry-after": "1"}),
        {"outAmount": "1000"}
    ]
    quote = await client.get_quote("SOL", "USDC", "1")
    assert quote.output_amount == 1000.0
```

### Error Testing
```python
# Test invalid response
with pytest.raises(JupiterQuoteError):
    await client.get_quote("SOL", "USDC", "1")  # with empty response

# Test rate limit exceeded
with pytest.raises(JupiterRateLimitError):
    await client.get_quote("SOL", "USDC", "1")  # with max retries exceeded
```

## 📊 Success Metrics

- All endpoints implemented and tested
- Error handling covers all edge cases
- Retry logic works correctly
- Unit tests pass with mock responses
- Client can be used as async context manager
- API key support works
- Integration with config/settings works

## ⚡ Dependencies

- US-001: Project Structure Setup (must have `src/interfaces/jupiter/`)
- US-002: Environment Configuration (must have settings for API URL/key)

## 📝 Notes

- Uses Jupiter API V6 (most stable)
- All I/O is async (httpx.AsyncClient)
- Follows AD-005: Jupiter API V2 HTTP for Swaps
- No SDK dependencies (pure HTTP)
- Configurable for different Jupiter API versions

---
*Generated for BMad workflow - Solana Trading Bot Project*