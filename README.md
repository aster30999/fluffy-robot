# Solana Trading Bot

A personal Python trading bot for automated Solana trading with technical indicators, risk management, and multi-pair support.

[![Python Test Suite](https://github.com/asteroid/solana-trading-bot/actions/workflows/test.yml/badge.svg)](https://github.com/asteroid/solana-trading-bot/actions/workflows/test.yml)
[![Code Coverage](https://codecov.io/gh/asteroid/solana-trading-bot/branch/main/graph/badge.svg)](https://codecov.io/gh/asteroid/solana-trading-bot)

**Note:** This project is currently in active development with a migration from a simple swap test script to a full-featured trading bot.

## Legacy: Solana Devnet Swap Test

This repository contains a legacy minimal Python script to test SOL to USDC swaps on Solana Devnet using **Jupiter API V2** (stable).

## Features

- ✅ Uses predefined test wallet from `~/wallet-1-keypair.json`
- ✅ Requests Devnet SOL via airdrop
- ✅ Performs SOL → USDT swap using **Jupiter API V2 Order & Execute** (direct HTTP calls)
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
USDT balance before swap: 0.000000 USDT

Swapping 0.1 SOL to USDT...
   Getting order from Jupiter API V2...
   Decoding and signing transaction...
   Executing transaction via Jupiter...
✅ Swap successful!
   Transaction: https://explorer.solana.com/tx/...?cluster=devnet

Checking balances after swap...
SOL balance after swap: 4.900000 SOL
USDT balance after swap: X.XXXXXX USDT

=== Summary ===
SOL spent: 0.100000 SOL
USDT received: X.XXXXXX USDT
Transaction: https://explorer.solana.com/tx/...?cluster=devnet

Test completed!
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SOLANA_RPC_URL` | Solana RPC endpoint | No | `https://api.devnet.solana.com` |
| `JUPITER_API_KEY` | Jupiter API key for higher rate limits | No | None (rate limited) |

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

This project uses **Jupiter API V2** directly via HTTP with the `/order` and `/execute` endpoints:

- 🔗 **Jupiter API V2**: [Documentation](https://dev.jup.ag/swap/order-and-execute)
- 📚 **Solana Python SDK**: [solana-py](https://github.com/michaelhly/solana-py)

### Why Jupiter API V2 Order & Execute?

| Solution | Type | Maintenance | Complexity | Stability |
| --- | --- | --- | --- | --- |
| Jupiter API V2 | API HTTP | ✅ DevRel | ⭐⭐ | ✅ High |
| jup-python-sdk | SDK | ✅ DevRel | ⭐ | ⚠️ Ultra API issues |
| jupiter-python-sdk | SDK | ⚠️ Community | ⭐⭐ | ❌ Deprecated |

**Jupiter API V2 with Order & Execute** provides the best pricing across all routers (Metis, JupiterZ, Dflow, OKX) with managed transaction landing.

## Troubleshooting

### Airdrop Fails

If the airdrop fails, try:
1. Wait a few minutes and retry
2. Use Solana CLI: `solana airdrop 1 6bXqg6oKUNtPbj84RkaCMvvfJFHiUiNVSwN9AYt65MaX --url https://api.devnet.solana.com`
3. Use Solana Explorer to manually request airdrop

### Swap Fails

1. **Check SOL balance**: Ensure you have at least 0.1 SOL for the swap
2. **Check USDT mint**: USDT Devnet mint is `Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB`
3. **Try smaller amount**: Use 0.01 SOL instead of 0.1 SOL
4. **Check Jupiter API status**: [Jupiter Status](https://status.jup.ag/)
5. **API Key**: For production use, get an API key from [Jupiter Portal](https://developers.jup.ag/portal)

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

## 🐳 Docker

Run the trading bot in a reproducible containerized environment.

### Prerequisites

- [Docker](https://www.docker.com/) installed
- [Docker Compose](https://docs.docker.com/compose/) (optional, for development)

### Quick Start

```bash
# Build the Docker image
docker build -t solana-trading-bot .

# Run the container
docker run -it --rm solana-trading-bot
```

### Development with Docker Compose

```bash
# Build and run with environment variables
docker-compose up --build

# Run tests in container
docker-compose run --rm trading-bot pytest tests/ -v

# Access shell
docker-compose exec trading-bot bash

# Stop
docker-compose down
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SOLANA_RPC_URL` | Solana RPC endpoint | `https://api.devnet.solana.com` |
| `NETWORK` | Network to use | `devnet` |
| `JUPITER_API_KEY` | Jupiter API key (optional) | - |
| `WALLET_PRIVATE_KEY` | Wallet private key | - |

### Mainnet Configuration

```bash
# Run on mainnet
docker run -it --rm \
  -e NETWORK=mainnet \
  -e SOLANA_RPC_URL=https://api.mainnet-beta.solana.com \
  solana-trading-bot
```

### Notes

- By default, containers run on **Devnet** for development
- Multi-stage build keeps final image small (~200MB)
- Non-root user for security
- Python 3.12.3 matches local development environment

## Dockerfile Structure

- **Stage 1**: Build stage installs all dependencies in a virtual environment
- **Stage 2**: Runtime stage copies only the virtual environment for a slim final image
- Uses `python:3.12.3-slim` as base image

## License

MIT License