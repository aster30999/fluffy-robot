"""
Solana Integration

Solana RPC and wallet management using solana-py and solders.

Exports:
- SolanaClient: Main Solana RPC client
- SolanaError: Base exception
- SolanaConnectionError: Connection error
- SolanaRPCError: RPC error
- SolanaTransactionError: Transaction error
- SolanaSigningError: Signing error
- SolanaBalanceError: Balance query error
- Balance: SOL balance data class
- TokenBalance: Token balance data class
- TransactionStatus: Transaction confirmation status
- TransactionInfo: Detailed transaction info
- get_solana_client: Get shared client instance
"""

from .client import (
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
    get_solana_client,
)

__version__ = "0.1.0"
