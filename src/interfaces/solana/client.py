"""
Solana RPC Client

Mixed approach: use solana-py + solders for transaction signing,
and direct HTTP for balance/token account queries.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union, Tuple
from functools import lru_cache

import httpx
import base58
from solana.rpc.async_api import AsyncClient as SolanaAsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer
from solders.signature import Signature
from solders.hash import Hash

from src.config import settings


# Configure logger
logger = logging.getLogger(__name__)


class SolanaError(Exception):
    """Base exception for Solana errors."""
    pass


class SolanaConnectionError(SolanaError):
    """Connection to Solana RPC failed."""
    pass


class SolanaRPCError(SolanaError):
    """RPC call failed."""
    pass


class SolanaTransactionError(SolanaError):
    """Transaction failed."""
    pass


class SolanaSigningError(SolanaError):
    """Transaction signing failed."""
    pass


class SolanaBalanceError(SolanaError):
    """Balance query failed."""
    pass


@dataclass
class Balance:
    """Token balance information."""
    address: str
    amount: int  # Raw amount (in lamports or token base units)
    decimals: int
    ui_amount: float  # Human-readable amount
    symbol: Optional[str] = None
    
    def __str__(self):
        return f"{self.ui_amount} {self.symbol or 'token'}"


@dataclass
class TokenBalance(Balance):
    """Token balance with additional token info."""
    mint_address: str = ""
    owner_address: str = ""
    
    @classmethod
    def from_raw(cls, mint_address: str, owner_address: str, raw_balance: Dict[str, Any], decimals: int = 9) -> "TokenBalance":
        """Create TokenBalance from raw RPC response."""
        amount = int(raw_balance.get("amount", 0))
        return cls(
            address=raw_balance.get("pubkey", ""),
            amount=amount,
            decimals=decimals,
            ui_amount=amount / (10 ** decimals),
            mint_address=mint_address,
            owner_address=owner_address,
            symbol=None
        )


@dataclass
class TransactionStatus:
    """Transaction confirmation status."""
    signature: str
    confirmed: bool
    err: Optional[Any] = None
    slot: Optional[int] = None
    logs: Optional[List[str]] = None


@dataclass
class TransactionInfo:
    """Detailed transaction information."""
    signature: str
    slot: int
    fee: int
    status: str
    logs: List[str] = field(default_factory=list)
    pre_balances: List[int] = field(default_factory=list)
    post_balances: List[int] = field(default_factory=list)


class SolanaClient:
    """
    Solana RPC client with mixed approach.
    
    Uses:
    - solana-py for transaction building and signing
    - solders for data structures
    - httpx for simple HTTP RPC calls (balances, token accounts)
    
    Implements:
    - get_balance: Get SOL balance (direct HTTP)
    - get_token_balance: Get token balance (direct HTTP)
    - confirm_transaction: Confirm transaction (direct HTTP)
    - sign_transaction: Sign transaction (solana-py)
    - send_transaction: Send signed transaction (solana-py)
    """
    
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize Solana client.
        
        Args:
            rpc_url: Solana RPC URL (default from settings)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.rpc_url = rpc_url or getattr(settings, 'solana_rpc_url', 'https://api.devnet.solana.com')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Lazy initialization
        self._async_client: Optional[SolanaAsyncClient] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"SolanaClient initialized with rpc_url={self.rpc_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_clients()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_clients(self):
        """Ensure both clients are initialized."""
        if self._async_client is None or self._async_client._closed:
            self._async_client = SolanaAsyncClient(self.rpc_url)
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.rpc_url,
                timeout=self.timeout
            )
    
    async def close(self):
        """Close all clients."""
        if self._async_client and not self._async_client._closed:
            await self._async_client.close()
            self._async_client = None
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
    
    async def _http_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to Solana RPC with retry logic.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: RPC endpoint
            **kwargs: Additional arguments for httpx
            
        Returns:
            JSON response as dictionary
            
        Raises:
            SolanaConnectionError: If connection fails
            SolanaRPCError: If RPC call fails
        """
        await self._ensure_clients()
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._http_client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = 1.0 * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                raise SolanaConnectionError(f"HTTP request failed after {self.max_retries} retries: {e}")
        
        raise SolanaConnectionError(f"HTTP request failed: {last_exception}")
    
    async def get_balance(self, address: str) -> Balance:
        """
        Get SOL balance for an address (using direct HTTP for efficiency).
        
        Args:
            address: Public key address (base58 string)
            
        Returns:
            Balance object with SOL balance
            
        Raises:
            SolanaBalanceError: If balance cannot be retrieved
        """
        logger.debug(f"Getting SOL balance for {address}")
        
        try:
            # Use direct HTTP for simple balance query
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [address]
            }
            
            data = await self._http_request("POST", "/", json=payload)
            
            result = data.get("result", {})
            value = int(result.get("value", 0))
            
            return Balance(
                address=address,
                amount=value,
                decimals=9,  # SOL has 9 decimals
                ui_amount=value / 10**9,
                symbol="SOL"
            )
        except Exception as e:
            raise SolanaBalanceError(f"Failed to get balance for {address}: {e}")
    
    async def get_token_balance(
        self,
        token_mint: str,
        owner_address: str,
        decimals: int = 9
    ) -> TokenBalance:
        """
        Get token balance for an owner (using direct HTTP).
        
        Args:
            token_mint: Token mint address
            owner_address: Owner wallet address
            decimals: Token decimals (default: 9)
            
        Returns:
            TokenBalance object
            
        Raises:
            SolanaBalanceError: If balance cannot be retrieved
        """
        logger.debug(f"Getting token balance for {token_mint} owner={owner_address}")
        
        try:
            # Use getTokenAccountsByOwner with mint filter
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [
                    owner_address,
                    {"mint": token_mint},
                    {"encoding": "jsonParsed"}
                ]
            }
            
            data = await self._http_request("POST", "/", json=payload)
            
            result = data.get("result", {})
            value = result.get("value", [])
            
            if not value:
                # No token account found
                return TokenBalance(
                    address="",
                    amount=0,
                    decimals=decimals,
                    ui_amount=0.0,
                    mint_address=token_mint,
                    owner_address=owner_address
                )
            
            # Get first token account
            account = value[0]
            pubkey = account.get("pubkey", "")
            parsed = account.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
            amount = int(parsed.get("tokenAmount", {}).get("amount", 0))
            
            return TokenBalance(
                address=pubkey,
                amount=amount,
                decimals=decimals,
                ui_amount=amount / (10 ** decimals),
                mint_address=token_mint,
                owner_address=owner_address
            )
        except Exception as e:
            raise SolanaBalanceError(f"Failed to get token balance for {token_mint} owner={owner_address}: {e}")
    
    async def get_token_balances(
        self,
        owner_address: str,
        token_mints: List[str],
        decimals_map: Optional[Dict[str, int]] = None
    ) -> Dict[str, TokenBalance]:
        """
        Get multiple token balances for an owner.
        
        Args:
            owner_address: Owner wallet address
            token_mints: List of token mint addresses
            decimals_map: Optional dict mapping mint to decimals
            
        Returns:
            Dict mapping mint address to TokenBalance
        """
        decimals_map = decimals_map or {}
        results = {}
        
        # Get all token accounts for owner
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                owner_address,
                {"encoding": "jsonParsed"}
            ]
        }
        
        data = await self._http_request("POST", "/", json=payload)
        result = data.get("result", {})
        value = result.get("value", [])
        
        # Build mint -> account map
        mint_to_account: Dict[str, Dict[str, Any]] = {}
        for account_data in value:
            pubkey = account_data.get("pubkey", "")
            parsed = account_data.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
            mint = parsed.get("mint", "")
            mint_to_account[mint] = {
                "pubkey": pubkey,
                "amount": int(parsed.get("tokenAmount", {}).get("amount", 0)),
                "decimals": parsed.get("decimals", 9)
            }
        
        # Get balances for requested mints
        for mint in token_mints:
            if mint in mint_to_account:
                account = mint_to_account[mint]
                decimals = account.get("decimals", decimals_map.get(mint, 9))
                results[mint] = TokenBalance(
                    address=account["pubkey"],
                    amount=account["amount"],
                    decimals=decimals,
                    ui_amount=account["amount"] / (10 ** decimals),
                    mint_address=mint,
                    owner_address=owner_address
                )
            else:
                # Token account not found
                decimals = decimals_map.get(mint, 9)
                results[mint] = TokenBalance(
                    address="",
                    amount=0,
                    decimals=decimals,
                    ui_amount=0.0,
                    mint_address=mint,
                    owner_address=owner_address
                )
        
        return results
    
    async def confirm_transaction(self, signature: str, timeout: int = 60) -> TransactionStatus:
        """
        Confirm a transaction (using direct HTTP).
        
        Args:
            signature: Transaction signature
            timeout: Timeout in seconds
            
        Returns:
            TransactionStatus with confirmation info
            
        Raises:
            SolanaTransactionError: If confirmation fails
        """
        logger.debug(f"Confirming transaction {signature}")
        
        try:
            # Check transaction status
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignatureStatuses",
                "params": [[signature]]
            }
            
            data = await self._http_request("POST", "/", json=payload, timeout=timeout)
            
            result = data.get("result", {})
            value = result.get("value", [{}])[0]
            
            confirmed = value.get("confirmationStatus", "") == "confirmed"
            err = value.get("err")
            slot = value.get("slot")
            
            return TransactionStatus(
                signature=signature,
                confirmed=confirmed,
                err=err,
                slot=slot
            )
        except Exception as e:
            raise SolanaTransactionError(f"Failed to confirm transaction {signature}: {e}")
    
    async def get_transaction_info(self, signature: str) -> TransactionInfo:
        """
        Get detailed transaction information.
        
        Args:
            signature: Transaction signature
            
        Returns:
            TransactionInfo with all details
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [signature, {"encoding": "json", "maxSupportedTransactionVersion": 0}]
        }
        
        data = await self._http_request("POST", "/", json=payload)
        result = data.get("result", {})
        
        transaction = result.get("transaction", [{}])[0]
        meta = result.get("meta", {})
        
        return TransactionInfo(
            signature=signature,
            slot=result.get("slot", 0),
            fee=meta.get("fee", 0),
            status=meta.get("err") is None and "confirmed" or "failed",
            logs=meta.get("logMessages", []),
            pre_balances=meta.get("preBalances", []),
            post_balances=meta.get("postBalances", [])
        )
    
    # ========================================================================
    # Transaction Building and Signing (using solana-py)
    # ========================================================================
    
    async def get_keypair(self) -> Keypair:
        """
        Get keypair from configuration.
        
        Returns:
            Keypair object
            
        Raises:
            SolanaSigningError: If keypair cannot be loaded
        """
        await self._ensure_clients()
        
        # Try to get from private key
        private_key = getattr(settings, 'wallet_private_key', None)
        if private_key:
            try:
                # private_key is SecretStr, need to get the actual value
                if hasattr(private_key, 'get_secret_value'):
                    pk_str = private_key.get_secret_value()
                else:
                    pk_str = str(private_key)
                
                if pk_str:
                    # Decode base58
                    secret_key_bytes = base58.b58decode(pk_str)
                    return Keypair.from_secret_key(secret_key_bytes)
            except Exception as e:
                logger.warning(f"Failed to load private key from env: {e}")
        
        # Try to get from keypair file
        keypair_path = getattr(settings, 'wallet_keypair_path', None)
        if keypair_path:
            try:
                with open(keypair_path, 'r') as f:
                    secret_key_bytes = json.load(f)
                return Keypair.from_secret_key(bytes(secret_key_bytes))
            except Exception as e:
                logger.warning(f"Failed to load keypair from {keypair_path}: {e}")
        
        raise SolanaSigningError("No wallet private key or keypair file configured")
    
    async def get_public_key(self) -> PublicKey:
        """
        Get public key from configuration.
        
        Returns:
            PublicKey object
        """
        keypair = await self.get_keypair()
        return keypair.public_key
    
    async def sign_transaction(self, transaction: Transaction) -> Transaction:
        """
        Sign a transaction (using solana-py).
        
        Args:
            transaction: Transaction to sign
            
        Returns:
            Signed transaction
            
        Raises:
            SolanaSigningError: If signing fails
        """
        try:
            keypair = await self.get_keypair()
            transaction.sign(keypair)
            return transaction
        except Exception as e:
            raise SolanaSigningError(f"Failed to sign transaction: {e}")
    
    async def send_transaction(self, transaction: Transaction) -> str:
        """
        Send a signed transaction (using solana-py).
        
        Args:
            transaction: Signed transaction
            
        Returns:
            Transaction signature
            
        Raises:
            SolanaTransactionError: If send fails
        """
        await self._ensure_clients()
        
        try:
            signature = await self._async_client.send_transaction(transaction)
            return str(signature.value)
        except Exception as e:
            raise SolanaTransactionError(f"Failed to send transaction: {e}")
    
    async def send_and_confirm(
        self,
        transaction: Transaction,
        confirm_timeout: int = 60
    ) -> Tuple[str, TransactionStatus]:
        """
        Send a transaction and wait for confirmation.
        
        Args:
            transaction: Transaction to send
            confirm_timeout: Timeout for confirmation
            
        Returns:
            Tuple of (signature, status)
        """
        # Sign if not already signed
        if not transaction.signatures:
            transaction = await self.sign_transaction(transaction)
        
        # Send
        signature = await self.send_transaction(transaction)
        
        # Confirm
        status = await self.confirm_transaction(signature, timeout=confirm_timeout)
        
        return signature, status
    
    # ========================================================================
    # Convenience Methods
    # ========================================================================
    
    async def transfer_sol(
        self,
        recipient: str,
        amount: float,
        confirm: bool = True,
        confirm_timeout: int = 60
    ) -> Tuple[str, Optional[TransactionStatus]]:
        """
        Transfer SOL to another address.
        
        Args:
            recipient: Recipient public key (base58 string)
            amount: Amount in SOL
            confirm: Whether to wait for confirmation
            confirm_timeout: Timeout for confirmation
            
        Returns:
            Tuple of (signature, status) if confirm=True, else (signature, None)
        """
        keypair = await self.get_keypair()
        recipient_pubkey = PublicKey(recipient)
        
        # Convert SOL to lamports
        lamports = int(amount * 10**9)
        
        # Build transaction
        transaction = Transaction()
        transaction.add(
            transfer(
                TransferParams(
                    program_id=PublicKey("11111111111111111111111111111111"),
                    source=keypair.public_key,
                    dest=recipient_pubkey,
                    lamports=lamports
                )
            )
        )
        
        # Sign and send
        transaction = await self.sign_transaction(transaction)
        signature = await self.send_transaction(transaction)
        
        if confirm:
            status = await self.confirm_transaction(signature, timeout=confirm_timeout)
            return signature, status
        else:
            return signature, None
    
    async def get_recent_blockhash(self) -> Hash:
        """
        Get recent blockhash (needed for transactions).
        
        Returns:
            Recent blockhash
        """
        await self._ensure_clients()
        blockhash = await self._async_client.get_recent_blockhash()
        return blockhash.value


# Singleton instance
_solana_client: Optional[SolanaClient] = None


async def get_solana_client() -> SolanaClient:
    """Get a shared SolanaClient instance."""
    global _solana_client
    if _solana_client is None:
        _solana_client = SolanaClient()
    return _solana_client
