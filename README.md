# Solana Devnet Swap Test

A minimal Python script to test SOL to USDC swaps on Solana Devnet using **Jupiter API V6** (stable).

## Features

- ✅ Uses predefined test wallet from `~/wallet-1-keypair.json`
- ✅ Requests Devnet SOL via airdrop
- ✅ Performs SOL → USDC swap using **Jupiter API V6** (direct HTTP calls)
- ✅ Displays balances before/after swap
- ✅ Shows transaction details

## Requirements

- Python 3.8+
- Solana Devnet RPC access
- Internet connection

## Installation

```bash
# Clone or download this repository
cd solana-swap-test

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Quick Start

```bash
# Run the test with predefined wallet
python swap_test.py
```

### With Custom Wallet

If you want to use a different wallet, modify the `TEST_WALLET_SECRET_KEY` variable in `swap_test.py`.

## Expected Output

```
=== Solana Devnet Swap Test ===

Using test wallet: 6bXqg6oKUNtPbj84RkaCMvvfJFHiUiNVSwN9AYt65MaX
Wallet address: 6bXqg6oKUNtPbj84RkaCMvvfJFHiUiNVSwN9AYt65MaX

Checking initial balances...
SOL balance before swap: 5.000000 SOL
USDC balance before swap: 0.000000 USDC

Swapping 0.1 SOL to USDC...
   Getting quote from Jupiter API...
   Getting swap transaction...
   Signing and sending transaction...
✅ Swap successful!
   Transaction: https://explorer.solana.com/tx/...?cluster=devnet

Checking balances after swap...
SOL balance after swap: 4.900000 SOL
USDC balance after swap: X.XXXXXX USDC

=== Summary ===
SOL spent: 0.100000 SOL
USDC received: X.XXXXXX USDC
Transaction: https://explorer.solana.com/tx/...?cluster=devnet

Test completed!
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SOLANA_RPC_URL` | Solana RPC endpoint | No | Devnet |

### Test Wallet

The script uses a predefined test wallet with the following secret key:
```python
TEST_WALLET_SECRET_KEY = [
    21,173,82,149,254,53,244,45,76,83,122,87,69,48,52,14,
    171,255,204,65,114,110,37,38,147,24,98,206,124,142,250,251,
    83,35,13,89,102,161,10,217,163,39,32,27,102,48,255,182,
    210,50,248,207,42,238,97,67,121,234,181,132,191,7,209,120
]
```

Wallet address: `6bXqg6oKUNtPbj84RkaCMvvfJFHiUiNVSwN9AYt65MaX`

## Technology Stack

This project uses **Jupiter API V6** directly via HTTP:

- 🔗 **Jupiter API V6**: [Documentation](https://dev.jup.ag/api-reference/swap/quote)
- 📚 **Solana Python SDK**: [solana-py](https://github.com/michaelhly/solana-py)

### Why Jupiter API V6?

| Solution | Type | Maintenance | Complexity | Stability |
| --- | --- | --- | --- | --- |
| Jupiter API V6 | API HTTP | ✅ DevRel | ⭐⭐ | ✅ High |
| jup-python-sdk | SDK | ✅ DevRel | ⭐ | ⚠️ Ultra API issues |
| jupiter-python-sdk | SDK | ⚠️ Community | ⭐⭐ | ❌ Deprecated |

**Jupiter API V6** is the most stable and reliable solution for production use.

## Troubleshooting

### Airdrop Fails

If the airdrop fails, try:
1. Wait a few minutes and retry
2. Use Solana CLI: `solana airdrop 1 6bXqg6oKUNtPbj84RkaCMvvfJFHiUiNVSwN9AYt65MaX --url https://api.devnet.solana.com`
3. Use Solana Explorer to manually request airdrop

### Swap Fails

1. **Check SOL balance**: Ensure you have at least 0.1 SOL for the swap
2. **Check USDC mint**: USDC Devnet mint is `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU`
3. **Try smaller amount**: Use 0.01 SOL instead of 0.1 SOL
4. **Check Jupiter API status**: [Jupiter Status](https://status.jup.ag/)

### Common Errors

- **500 Internal Server Error**: Jupiter API temporary issue, retry later
- **Insufficient SOL**: Request airdrop first
- **Transaction timeout**: Increase timeout or retry

## Dependencies

- `solana>=0.36.6` - Solana Python SDK
- `solders>=0.27.0` - Solana data structures
- `httpx>=0.28.1` - Async HTTP client
- `base58>=2.1.0` - Base58 encoding
- `python-dotenv>=1.0.0` - Environment variables

## License

MIT License