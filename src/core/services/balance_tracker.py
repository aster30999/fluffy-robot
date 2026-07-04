"""
Balance Tracker Service

Application service for tracking SOL and token balances from Solana blockchain.
Uses SolanaClient for RPC calls and Wallet for public key management.

Architecture Decisions:
    AD-001: Clean Architecture Paradigm - Application Service layer
    AD-004: Dependency Injection Pattern - SolanaClient and Wallet injected via constructor

Dependencies:
    - SolanaClient from src.infrastructure.solana.client (US-004)
    - Wallet from src.infrastructure.solana.wallet
    - Balance from src.core.models.balance (US-011)
    - Token from src.core.models.price (US-010)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.models.balance import Balance
    from src.core.models.price import Token
    from src.infrastructure.solana.client import SolanaClient
    from src.infrastructure.solana.wallet import Wallet


# Custom Exceptions
class BalanceTrackError(Exception):
    """Raised when balance tracking fails."""
    pass


class TokenNotFoundError(BalanceTrackError):
    """Raised when a token is not found in wallet."""
    pass


class BalanceTracker:
    """Service for tracking SOL and token balances from Solana blockchain.
    
    Uses dependency injection for SolanaClient and Wallet to enable testing
    and support different implementations.
    
    Attributes:
        solana_client: Solana API client for fetching balances
        wallet: Wallet containing the public key for balance lookups
    """
    
    # SOL mint address (native SOL)
    SOL_MINT = "So11111111111111111111111111111111111111112"
    
    def __init__(self, solana_client: "SolanaClient", wallet: "Wallet"):
        """Initialize BalanceTracker with Solana client and wallet.
        
        Args:
            solana_client: Injected Solana API client
            wallet: Injected wallet containing the public key
        """
        self.solana_client = solana_client
        self.wallet = wallet
        self.logger = logging.getLogger(__name__)
    
    async def get_sol_balance(self) -> float:
        """Get the SOL balance for the wallet.
        
        Returns:
            SOL balance in SOL units (float)
            
        Raises:
            BalanceTrackError: If balance fetching fails
        """
        try:
            # Get balance from Solana RPC
            balance = await self.solana_client.get_balance(
                self.wallet.public_key_str
            )
            
            # Use ui_amount which is already in SOL units
            sol_balance = balance.ui_amount if hasattr(balance, 'ui_amount') else balance.amount / 1_000_000_000
            
            self.logger.debug(f"SOL balance: {sol_balance} SOL")
            return float(sol_balance)
            
        except Exception as e:
            self.logger.error(f"Error fetching SOL balance: {e}", exc_info=True)
            raise BalanceTrackError(f"Failed to fetch SOL balance: {e}") from e
    
    async def get_token_balance(self, mint: str) -> float:
        """Get the token balance for a specific mint address.
        
        Args:
            mint: Token mint address to check balance for
            
        Returns:
            Token balance in base units (float)
            Returns 0.0 if token not found or error occurs
            
        Raises:
            BalanceTrackError: If balance fetching fails
        """
        try:
            # For SOL, use get_sol_balance
            if mint == self.SOL_MINT or mint.lower() == "sol":
                return await self.get_sol_balance()
            
            # Get token balance from Solana RPC
            balance = await self.solana_client.get_token_balance(
                self.wallet.public_key_str,
                mint
            )
            
            if balance is None:
                self.logger.warning(f"Token {mint} not found in wallet")
                return 0.0
            
            # balance is a TokenBalance object, use ui_amount
            balance_value = balance.ui_amount if hasattr(balance, 'ui_amount') else balance.amount / (10 ** balance.decimals)
            self.logger.debug(f"Token {mint} balance: {balance_value} units")
            return float(balance_value)
            
        except Exception as e:
            self.logger.error(f"Error fetching token balance for {mint}: {e}", exc_info=True)
            raise BalanceTrackError(f"Failed to fetch token balance for {mint}: {e}") from e
    
    async def get_all_balances(self) -> dict[str, float]:
        """Get all token balances for the wallet.
        
        Returns:
            Dictionary mapping mint addresses to balances (float)
            Includes SOL balance with key SOL_MINT
            
        Raises:
            BalanceTrackError: If balance fetching fails
        """
        try:
            balances: dict[str, float] = {}
            
            # Get SOL balance
            sol_balance = await self.get_sol_balance()
            balances[self.SOL_MINT] = sol_balance
            
            # Get all token account balances using RPC directly
            # We use getTokenAccountsByOwner to get all token accounts
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenAccountsByOwner",
                    "params": [
                        self.wallet.public_key_str,
                        {"encoding": "jsonParsed"}
                    ]
                }
                data = await self.solana_client._http_request("POST", "/", json=payload)
                result = data.get("result", {})
                token_accounts = result.get("value", [])
                
                for account in token_accounts:
                    account_data = account.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                    mint = account_data.get("mint", "")
                    if mint and mint != self.SOL_MINT:
                        # Extract amount from token account
                        amount_str = account_data.get("tokenAmount", {}).get("amount", "0")
                        amount = int(amount_str)
                        decimals = account_data.get("tokenAmount", {}).get("decimals", 9)
                        balance = amount / (10 ** decimals)
                        balances[mint] = balance
                        self.logger.debug(f"Token account: {mint} = {balance}")
                        
            except Exception as e:
                self.logger.warning(f"Could not fetch all token accounts: {e}")
                # Fallback: try to get balances for known tokens if any
                pass
            
            self.logger.debug(f"All balances: {balances}")
            return balances
            
        except Exception as e:
            self.logger.error(f"Error fetching all balances: {e}", exc_info=True)
            raise BalanceTrackError(f"Failed to fetch all balances: {e}") from e
    
    async def get_balance_for_token(self, token: "Token") -> "Balance":
        """Get balance for a specific Token as a Balance domain model.
        
        Args:
            token: Token to get balance for
            
        Returns:
            Balance domain model instance
            
        Raises:
            BalanceTrackError: If balance fetching fails
        """
        from src.core.models.balance import Balance
        
        balance_amount = await self.get_token_balance(token.mint)
        return Balance(token=token, amount=balance_amount)
    
    # Synchronous wrappers for convenience
    def get_sol_balance_sync(self) -> float:
        """Synchronous version of get_sol_balance.
        
        WARNING: This should only be used in synchronous contexts.
        For async contexts, use get_sol_balance() directly.
        
        Returns:
            SOL balance in SOL units (float)
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.get_sol_balance())
        finally:
            if loop is not asyncio.get_event_loop():
                loop.close()
    
    def get_token_balance_sync(self, mint: str) -> float:
        """Synchronous version of get_token_balance.
        
        WARNING: This should only be used in synchronous contexts.
        For async contexts, use get_token_balance() directly.
        
        Args:
            mint: Token mint address
            
        Returns:
            Token balance in base units (float)
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.get_token_balance(mint))
        finally:
            if loop is not asyncio.get_event_loop():
                loop.close()
    
    def get_all_balances_sync(self) -> dict[str, float]:
        """Synchronous version of get_all_balances.
        
        WARNING: This should only be used in synchronous contexts.
        For async contexts, use get_all_balances() directly.
        
        Returns:
            Dictionary mapping mint addresses to balances (float)
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.get_all_balances())
        finally:
            if loop is not asyncio.get_event_loop():
                loop.close()
