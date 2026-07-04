"""
Wallet Management

Secure wallet class for managing Solana keypairs and signing transactions.
Implements Infrastructure Services layer as per AD-001 (Clean Architecture Paradigm).
Full enhanced implementation for US-016 replacing minimal US-014 version.

Security Notes:
- Private keys are NEVER logged at any level
- Private keys are validated on load
- Environment variables are checked before file-based configuration
- All sensitive operations have appropriate warnings in logs

Dependencies:
    - solders.keypair for Keypair handling
    - solders.pubkey for PublicKey
    - solders.transaction for Transaction signing
    - src.config for environment configuration
"""

from __future__ import annotations

import base58
import logging
import os
from dataclasses import dataclass
from typing import Optional

from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey
from solders.signature import Signature
from solders.transaction import Transaction

from src.config import settings


# Custom Exceptions
class WalletError(Exception):
    """Base exception for wallet-related errors."""
    pass


class InvalidPrivateKeyError(WalletError):
    """Raised when a private key is invalid or malformed."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Invalid private key: {message}")


class WalletSecurityError(WalletError):
    """Raised when a security check fails."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Wallet security error: {message}")


class WalletLoadError(WalletError):
    """Raised when wallet cannot be loaded."""
    pass


class WalletSigningError(WalletError):
    """Raised when transaction signing fails."""
    pass


@dataclass
class Wallet:
    """Secure Solana wallet for managing keypairs and signing transactions.
    
    Handles private key storage, transaction signing, and security.
    Private keys are never logged or exposed. Supports loading from
    various sources (direct, .env file, environment variable).
    
    This is an enhanced implementation for US-016, replacing the minimal
    version from US-014. Maintains backward compatibility.
    
    Attributes:
        _keypair: Solders Keypair for signing operations (private attribute)
        logger: Logger instance for debugging (never logs private keys)
    """
    _keypair: Keypair
    logger: logging.Logger
    
    def __init__(self, private_key: Optional[str] = None, env_var: str = "WALLET_PRIVATE_KEY"):
        """Initialize Wallet with private key or from environment.
        
        Args:
            private_key: Optional base58-encoded private key string
            env_var: Environment variable name to load private key from (default: WALLET_PRIVATE_KEY)
            
        Raises:
            WalletError: If private key cannot be loaded
            InvalidPrivateKeyError: If private key is invalid
            WalletSecurityError: If security check fails
        """
        self.logger = logging.getLogger(__name__)
        self._keypair = self._load_keypair(private_key, env_var)
        self.logger.info("Wallet loaded successfully")
    
    @classmethod
    def from_private_key(cls, private_key_bytes: bytes) -> "Wallet":
        """Create wallet from raw private key bytes.
        
        Args:
            private_key_bytes: Raw private key bytes (32 bytes)
            
        Returns:
            New Wallet instance
            
        Raises:
            InvalidPrivateKeyError: If private key is invalid
        """
        try:
            # Validate that we have 32 bytes
            if len(private_key_bytes) != 32:
                raise InvalidPrivateKeyError(
                    f"Private key must be 32 bytes, got {len(private_key_bytes)}"
                )
            keypair = Keypair.from_seed(private_key_bytes)
            instance = cls.__new__(cls)
            instance.logger = logging.getLogger(__name__)
            instance._keypair = keypair
            instance.logger.info("Wallet created from private key bytes")
            return instance
        except Exception as e:
            raise InvalidPrivateKeyError(f"Failed to load private key: {str(e)}") from e
    
    @classmethod
    def from_env(cls, env_var: str = "WALLET_PRIVATE_KEY") -> "Wallet":
        """Create wallet from environment variable.
        
        Args:
            env_var: Environment variable name (default: WALLET_PRIVATE_KEY)
            
        Returns:
            New Wallet instance
            
        Raises:
            WalletError: If environment variable not set
            InvalidPrivateKeyError: If private key in environment is invalid
        """
        private_key = os.environ.get(env_var)
        if not private_key:
            raise WalletError(f"Environment variable {env_var} not set")
        return cls(private_key=private_key, env_var=env_var)
    
    @classmethod
    def from_keypair_path(cls, path: str) -> "Wallet":
        """Create wallet from keypair file path.
        
        Args:
            path: Path to keypair file (JSON format)
            
        Returns:
            Wallet instance
            
        Raises:
            WalletLoadError: If keypair file cannot be loaded
        """
        try:
            # Load JSON from file and create keypair
            import json
            with open(path, 'r') as f:
                keypair_data = json.load(f)
            keypair = Keypair.from_json(keypair_data)
            instance = cls.__new__(cls)
            instance.logger = logging.getLogger(__name__)
            instance._keypair = keypair
            instance.logger.info(f"Wallet loaded from keypair file: {path}")
            return instance
        except Exception as e:
            raise WalletLoadError(f"Failed to load wallet from {path}: {e}") from e
    
    @classmethod
    def default(cls) -> "Wallet":
        """Create a default wallet from environment configuration.
        
        Tries to load from:
        1. WALLET_PRIVATE_KEY environment variable (base58 encoded)
        2. wallet_private_key from settings
        3. wallet_keypair_path from settings
        
        Returns:
            Wallet instance
            
        Raises:
            WalletLoadError: If no valid wallet configuration found
        """
        # Try environment variable first
        private_key = os.environ.get("WALLET_PRIVATE_KEY")
        if private_key:
            try:
                return cls(private_key=private_key)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load wallet from WALLET_PRIVATE_KEY: {e}")
        
        # Try private key from settings
        settings_private_key = getattr(settings, 'wallet_private_key', None)
        if settings_private_key:
            try:
                # If it's a string, assume it's base58 encoded
                if isinstance(settings_private_key, str):
                    return cls(private_key=settings_private_key)
                # If it's bytes, use from_private_key
                elif isinstance(settings_private_key, bytes):
                    return cls.from_private_key(settings_private_key)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load wallet from settings.wallet_private_key: {e}")
        
        # Try keypair path from settings
        keypair_path = getattr(settings, 'wallet_keypair_path', None)
        if keypair_path:
            try:
                return cls.from_keypair_path(keypair_path)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load wallet from {keypair_path}: {e}")
        
        raise WalletLoadError(
            "No valid wallet configuration found. "
            "Set WALLET_PRIVATE_KEY environment variable or configure wallet_private_key/wallet_keypair_path in settings."
        )
    
    @property
    def public_key(self) -> PublicKey:
        """Get the wallet's public key.
        
        Returns:
            Solders PublicKey object
        """
        return self._keypair.pubkey()
    
    @property
    def public_key_str(self) -> str:
        """Get the wallet's public key as a string.
        
        Returns:
            Base58-encoded public key string
        """
        return str(self.public_key)
    
    @property
    def private_key(self) -> bytes:
        """Get the wallet's private key bytes.
        
        WARNING: This exposes the private key. Use with caution.
        This property should only be used internally or in trusted contexts.
        Access is logged as a security warning.
        
        Returns:
            Private key as bytes (32 bytes)
            
        Raises:
            WalletSecurityError: If accessed inappropriately (logged but not blocked)
        """
        # Security: Log access to private key
        self.logger.warning(
            "Private key accessed - ensure this is a trusted context. "
            "Public key: %s", self.public_key_str
        )
        return self._keypair.secret()
    
    @property
    def is_test_wallet(self) -> bool:
        """Check if this is a well-known test wallet.
        
        Returns:
            True if using a well-known test wallet private key
        """
        # Check against known test wallet public keys
        # These are partial prefixes for security - full keys should not be hardcoded
        test_key_prefixes = [
            "5fF2",  # Well-known test wallet prefix
            "31LK",  # Another test wallet prefix
            "9BvP",  # Test wallet prefix
        ]
        return any(
            self.public_key_str.startswith(prefix) 
            for prefix in test_key_prefixes
        )
    
    def sign_transaction(self, tx: Transaction) -> Transaction:
        """Sign a Solana transaction.
        
        Args:
            tx: Unsigned Solana transaction
            
        Returns:
            Signed transaction
            
        Raises:
            WalletSigningError: If signing fails
        """
        try:
            from solders.hash import Hash
            # Get recent blockhash from the transaction or use default
            recent_blockhash = getattr(tx, 'recent_blockhash', None)
            if recent_blockhash is None:
                recent_blockhash = Hash.default()
            tx.sign([self._keypair], recent_blockhash)
            self.logger.debug(
                f"Transaction signed with public key: {self.public_key_str}"
            )
            return tx
        except Exception as e:
            raise WalletSigningError(f"Failed to sign transaction: {e}") from e
    
    def sign_transaction_bytes(self, transaction_bytes: bytes) -> bytes:
        """Sign a serialized transaction.
        
        Args:
            transaction_bytes: Serialized transaction bytes
            
        Returns:
            Signed transaction bytes
            
        Raises:
            WalletSigningError: If signing fails
        """
        try:
            from solders.hash import Hash
            tx = Transaction.from_bytes(transaction_bytes)
            # Need to pass recent_blockhash to sign
            # For now, use a default blockhash
            recent_blockhash = Hash.default()
            tx.sign([self._keypair], recent_blockhash)
            return bytes(tx)
        except Exception as e:
            raise WalletSigningError(f"Failed to sign transaction: {e}") from e
    
    def sign_message(self, message: bytes) -> Signature:
        """Sign a raw message.
        
        Args:
            message: Raw bytes to sign
            
        Returns:
            Signature object
        """
        try:
            signature = self._keypair.sign_message(message)
            self.logger.debug(
                f"Message signed with public key: {self.public_key_str}"
            )
            return signature
        except Exception as e:
            raise WalletSigningError(f"Failed to sign message: {e}") from e
    
    def _load_keypair(self, private_key: Optional[str], env_var: str) -> Keypair:
        """Load keypair from private key or environment.
        
        Args:
            private_key: Optional base58-encoded private key string
            env_var: Environment variable name to try
            
        Returns:
            Solders Keypair
            
        Raises:
            WalletError: If keypair cannot be loaded
            InvalidPrivateKeyError: If private key is invalid
        """
        # Try private key parameter first
        if private_key:
            try:
                # Validate base58 encoding
                if not all(
                    c in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" 
                    for c in private_key
                ):
                    raise InvalidPrivateKeyError("Invalid base58 encoding")
                
                # Decode from base58
                private_key_bytes = base58.b58decode(private_key)
                
                # Validate length (should be 32 bytes for Solana private key)
                if len(private_key_bytes) != 32:
                    raise InvalidPrivateKeyError(
                        f"Private key must be 32 bytes, got {len(private_key_bytes)}"
                    )
                
                return Keypair.from_seed(private_key_bytes)
                
            except InvalidPrivateKeyError:
                raise
            except Exception as e:
                raise InvalidPrivateKeyError(
                    f"Failed to load private key: {str(e)}"
                ) from e
        
        # Try environment variable
        env_key = os.environ.get(env_var)
        if env_key:
            try:
                # Validate base58 encoding
                if not all(
                    c in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" 
                    for c in env_key
                ):
                    raise InvalidPrivateKeyError(
                        f"Invalid base58 encoding in {env_var}"
                    )
                
                private_key_bytes = base58.b58decode(env_key)
                
                if len(private_key_bytes) != 32:
                    raise InvalidPrivateKeyError(
                        f"Private key in {env_var} must be 32 bytes, "
                        f"got {len(private_key_bytes)}"
                    )
                
                return Keypair.from_seed(private_key_bytes)
                
            except InvalidPrivateKeyError:
                raise
            except Exception as e:
                raise InvalidPrivateKeyError(
                    f"Failed to load private key from {env_var}: {str(e)}"
                ) from e
        
        raise WalletError(
            f"No private key provided and environment variable {env_var} not set"
        )


# Legacy alias for backward compatibility
WalletLoadError_ = WalletLoadError
WalletSigningError_ = WalletSigningError
