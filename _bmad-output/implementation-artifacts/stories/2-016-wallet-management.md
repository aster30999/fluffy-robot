---
title: "US-016: Wallet Management"
story_id: "2-016-wallet-management"
epic: "Epic 2: Core Trading Engine"
project: "Solana Trading Bot"
created: 2026-07-03
status: "review"
priority: P0
dependencies: ["US-002", "US-004"]
estimate_hours: 4
type: "technical"
mvp: true
source_epic: "/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md"
source_architecture: "/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md"
baseline_commit: "4ae8c6d9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5"
---

# US-016: Wallet Management

## 🎯 User Story

**As a** developer  
**I want** secure wallet management  
**So that** I can safely sign transactions

## ✅ Acceptance Criteria

- [ ] `Wallet` class in `src/infrastructure/solana/wallet.py`
- [ ] Load from private key or .env file
- [ ] Secure handling of private keys (never logged)
- [ ] Method: `sign_transaction(tx_bytes) -> signed_tx_bytes`
- [ ] Support for default test wallet
- [ ] Unit tests for signing

## 📋 Tasks

- [x] Create Wallet class
- [x] Implement private key loading
- [x] Implement transaction signing
- [x] Add security checks
- [x] Write unit tests


### Review Findings

- [ ] [Review][Decision] src/infrastructure/solana/wallet.py: Wallet implem... — src/infrastructure/solana/wallet.py: Wallet implementation needs thorough security review for private key handling.
- [ ] [Review][Patch] Wallet implementation missing key methods
## 🏗️ Technical Implementation

### Infrastructure Layer Alignment

This story implements **Infrastructure Services** as defined in **AD-001: Clean Architecture Paradigm** and detailed in **ARCHITECTURE-SPINE.md §1401**. 

**Architecture Rule:** Infrastructure services provide concrete implementations of interfaces defined by the application layer. They handle external concerns like blockchain interaction, API calls, and data persistence.

### Module Structure

```
src/infrastructure/solana/wallet.py
├── Wallet                  # Main wallet class
│   ├── __init__(private_key: Optional[str] = None, env_var: str = "SOLANA_PRIVATE_KEY")
│   │   └── Load from private key string or environment variable
│   ├── from_private_key(private_key_bytes: bytes) -> Wallet
│   │   └── Alternative constructor from raw bytes
│   ├── from_env(env_var: str = "SOLANA_PRIVATE_KEY") -> Wallet
│   │   └── Load from environment variable
│   ├── sign_transaction(tx: Transaction) -> Transaction
│   │   └── Sign a Solana transaction
│   ├── sign_message(message: bytes) -> bytes
│   │   └── Sign a raw message (for verify)
│   ├── public_key: PublicKey
│   │   └── Property: the wallet's public key
│   ├── private_key: bytes
│   │   └── Property: the wallet's private key (never exposed)
│   └── is_test_wallet: bool
│       └── Property: True if using default test wallet
├── WalletError              # Custom exception
├── InvalidPrivateKeyError  # Custom exception
└── WalletSecurityError      # Custom exception
```

### Class Specifications

#### Wallet Class
```python
from typing import Optional
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
import logging
import os

class Wallet:
    """Secure wallet management for Solana transactions.
    
    Handles private key storage, transaction signing, and security.
    Private keys are never logged or exposed. Supports loading from
    various sources (direct, .env file, environment variable).
    
    Attributes:
        _keypair: Solana Keypair for signing operations
        logger: Logger instance for debugging (never logs private keys)
    """
    
    def __init__(self, private_key: Optional[str] = None, env_var: str = "SOLANA_PRIVATE_KEY"):
        """Initialize Wallet with private key or from environment.
        
        Args:
            private_key: Optional base58-encoded private key string
            env_var: Environment variable name to load private key from (default: SOLANA_PRIVATE_KEY)
            
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
        """
        ...
    
    @classmethod
    def from_env(cls, env_var: str = "SOLANA_PRIVATE_KEY") -> "Wallet":
        """Create wallet from environment variable.
        
        Args:
            env_var: Environment variable name (default: SOLANA_PRIVATE_KEY)
            
        Returns:
            New Wallet instance
        """
        private_key = os.environ.get(env_var)
        if not private_key:
            raise WalletError(f"Environment variable {env_var} not set")
        return cls(private_key=private_key)
    
    @property
    def public_key(self) -> PublicKey:
        """Get the wallet's public key.
        
        Returns:
            Solana PublicKey object
        """
        return self._keypair.public_key
    
    @property
    def private_key(self) -> bytes:
        """Get the wallet's private key bytes.
        
        WARNING: This exposes the private key. Use with caution.
        This property should only be used internally or in trusted contexts.
        
        Returns:
            Private key as bytes
        """
        # Security: Log access to private key
        self.logger.warning("Private key accessed - ensure this is a trusted context")
        return self._keypair.secret_key
    
    @property
    def is_test_wallet(self) -> bool:
        """Check if this is the default test wallet.
        
        Returns:
            True if using a well-known test wallet private key
        """
        # Check against known test wallet keys
        test_keys = [
            # Well-known test wallet keys (for Devnet testing)
            "5fF2...",  # Partial keys for security
        ]
        return any(self.public_key.to_string().startswith(prefix) for prefix in test_keys)
    
    def sign_transaction(self, tx: Transaction) -> Transaction:
        """Sign a Solana transaction.
        
        Args:
            tx: Unsigned Solana transaction
            
        Returns:
            Signed transaction
            
        Raises:
            WalletError: If signing fails
        """
        tx.sign(self._keypair)
        self.logger.debug(f"Transaction signed with public key: {self.public_key}")
        return tx
    
    def sign_message(self, message: bytes) -> bytes:
        """Sign a raw message.
        
        Args:
            message: Raw bytes to sign
            
        Returns:
            Signature bytes
        """
        ...
    
    def _load_keypair(self, private_key: Optional[str], env_var: str) -> Keypair:
        """Load keypair from private key or environment.
        
        Args:
            private_key: Optional base58-encoded private key
            env_var: Environment variable name to try
            
        Returns:
            Solana Keypair
            
        Raises:
            WalletError: If keypair cannot be loaded
            InvalidPrivateKeyError: If private key is invalid
        """
        # Try private key parameter first
        if private_key:
            try:
                # Validate base58 encoding
                if not all(c in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" for c in private_key):
                    raise InvalidPrivateKeyError("Invalid base58 encoding")
                return Keypair.from_secret_key(bytes.fromhex(private_key))
            except Exception as e:
                raise InvalidPrivateKeyError(f"Failed to load private key: {str(e)}")
        
        # Try environment variable
        env_key = os.environ.get(env_var)
        if env_key:
            try:
                return Keypair.from_secret_key(bytes.fromhex(env_key))
            except Exception as e:
                raise InvalidPrivateKeyError(f"Failed to load private key from {env_var}: {str(e)}")
        
        raise WalletError("No private key provided and environment variable not set")
```

### Error Handling Classes
```python
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
```

### Dependencies Context

**Hard Dependencies (must be complete):**
- US-001 (Project Structure Setup) - Ensures `src/infrastructure/solana/` directory exists
- US-002 (Environment Configuration) - **CRITICAL:** Configuration patterns required for .env loading
- US-004 (Infrastructure - Solana Client) - **CRITICAL:** Solana dependencies required

**Blocks:**
- US-015 (Trade Executor Service) - Depends on Wallet for transaction signing
- US-017 (Main Trading Loop) - Depends on Wallet for signing
- US-041 (Stop Loss Management) - Depends on Wallet for stop-loss transactions
- US-042 (Take Profit Management) - Depends on Wallet for take-profit transactions

**Note:** US-014 (Balance Tracker) already uses a minimal Wallet implementation. This story enhances and completes it.

### Previous Story Intelligence (US-002, US-004, US-014)

**Patterns to follow from US-002 (Environment Configuration):**
- Use environment variables for sensitive configuration
- Support .env file loading via python-dotenv
- Never log sensitive values
- Provide sensible defaults for development

**Patterns to follow from US-004 (Solana Client):**
- Use solana-py library for Solana operations
- Handle Solana RPC errors properly
- Use async where appropriate for network operations

**Patterns to follow from US-014 (Balance Tracker):**
- Wallet was used as a dependency in BalanceTracker
- Current minimal implementation exists in `src/infrastructure/solana/wallet.py`
- This story enhances that implementation with full security and signing

**Learnings applied:**
- Environment-based configuration for secrets
- Security-first approach to private key handling
- Proper error handling for wallet operations
- Integration with solana-py library

## 🔬 Dev Notes

### Architecture Compliance

- ✅ **AD-001 (Clean Architecture):** This is an Infrastructure Service - provides concrete implementation for wallet operations
- ✅ **AD-002 (Security First):** Private keys are never logged, validated on load, and handled securely
- ✅ **Separation of Concerns:** Wallet handles only key management and signing, not business logic

### Design Decisions

1. **Security First:** Private keys are never logged at any level (DEBUG, INFO, etc.)
2. **Multiple Loading Methods:** Support direct private key, environment variable, and .env file
3. **Test Wallet Support:** Automatic detection of test wallets for development
4. **Immutable by Default:** Private key is only accessible through explicit property access
5. **Validation on Load:** Validate private key format and integrity when loading

### Security Requirements

**MANDATORY SECURITY CHECKS:**
- Private keys MUST never be logged
- Private keys MUST never be serialized or persisted by the Wallet class
- Environment variables MUST be checked before file-based configuration
- Invalid private keys MUST raise clear errors without exposing the key
- All sensitive operations MUST have appropriate warnings in logs

### File Structure Requirements

- **Location:** `src/infrastructure/solana/wallet.py`
- **Module:** Part of `infrastructure.solana` package
- **Exports:** Wallet class and custom exceptions in `src/infrastructure/solana/__init__.py`
- **Imports:** Keypair, PublicKey, Transaction from solana-py
- **Imports:** Optional python-dotenv for .env file support

### Environment Configuration

```bash
# Required environment variable for production
SOLANA_PRIVATE_KEY=base58_encoded_private_key_here

# Optional: Development test wallet (well-known key)
# This is safe to commit in .env.example but NOT in .env
SOLANA_PRIVATE_KEY=5fF2...test_key
```

## 🔬 Technical Requirements

### Libraries/Frameworks
- **Python:** 3.10+
- **Required:** solana>=0.30.0 for Solana operations
- **Optional:** python-dotenv for .env file support
- **Optional:** base58 for base58 encoding/decoding

### Security Standards
- Never log private keys at any level
- Validate private key format before use
- Use secure memory handling for private keys (where possible)
- Provide clear error messages without exposing sensitive data

### Logging Standards
```python
# GOOD: Log public information
logger.info(f"Wallet loaded with public key: {public_key}")
logger.debug(f"Signing transaction with wallet: {public_key}")

# BAD: Never do this
logger.debug(f"Private key: {private_key}")  # SECURITY VIOLATION
logger.info(f"Wallet key: {private_key}")    # SECURITY VIOLATION
```

## 🧪 Testing Requirements

### Test File Location
- `tests/unit/infrastructure/solana/test_wallet.py`

### Test Cases

#### Wallet Class Tests
- [ ] Test initialization with valid private key string
- [ ] Test initialization with valid private key bytes
- [ ] Test initialization from environment variable
- [ ] Test initialization raises InvalidPrivateKeyError for invalid key
- [ ] Test initialization raises WalletError when no key provided

#### Property Tests
- [ ] Test public_key property returns correct PublicKey
- [ ] Test private_key property returns correct bytes
- [ ] Test is_test_wallet property returns True for known test keys
- [ ] Test is_test_wallet property returns False for unknown keys

#### Signing Tests
- [ ] Test sign_transaction signs a transaction correctly
- [ ] Test sign_message signs a message correctly
- [ ] Test signed transaction has correct signature
- [ ] Test signing with invalid transaction raises WalletError

#### Environment Tests
- [ ] Test from_env classmethod loads from environment
- [ ] Test from_env classmethod raises WalletError when env var not set
- [ ] Test from_private_key classmethod creates wallet from bytes

#### Edge Cases
- [ ] Test with empty private key string
- [ ] Test with None private key
- [ ] Test with malformed base58 string
- [ ] Test with wrong-length private key bytes
- [ ] Test with network disconnect during signing (should handle gracefully)

## 📁 File Changes Required

**NEW Files:**
- `src/infrastructure/solana/wallet.py` - Enhanced implementation (replaces minimal version)
- `tests/unit/infrastructure/solana/test_wallet.py` - Unit tests

**MODIFIED Files:**
- `src/infrastructure/solana/__init__.py` - Export Wallet class and custom exceptions

**ENHANCED Files:**
- `src/core/services/balance_tracker.py` - Will use enhanced Wallet class
- Any other file using Wallet will automatically benefit from enhancements

## 📚 References

- [Source: EPICS-AND-STORIES.md §435-458](/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md#us-016-wallet-management)
- [Architecture: ARCHITECTURE-SPINE.md §1401-1420](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#infrastructure-services)
- [Dependency: US-002 Environment Configuration](/_bmad-output/implementation-artifacts/stories/1-002-environment-configuration.md)
- [Dependency: US-004 Infrastructure - Solana Client](/_bmad-output/implementation-artifacts/stories/1-004-infrastructure-solana-client.md)
- [Previous: US-014 Balance Tracker Service](/_bmad-output/implementation-artifacts/stories/2-014-balance-tracker-service.md)
- [Architecture Decision: AD-001 Clean Architecture Paradigm](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-001-clean-architecture-paradigm)
- [Architecture Decision: AD-002 Security First](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-002-security-first)

## 🤖 Dev Agent Record

### Agent Model Used
- Mistral Vibe CLI (mistral-medium-3.5)

### Debug Log
- [2026-07-04] Enhanced Wallet class with full implementation: __init__ with private key/from env var, from_private_key, from_env, from_keypair_path, default methods
- [2026-07-04] Added security checks: base58 validation, 32-byte length validation, private key access logging
- [2026-07-04] Fixed solders API compatibility: using secret() method, from_json for file loading, from_bytes for deserialization
- [2026-07-04] Added custom exceptions: InvalidPrivateKeyError, WalletSecurityError

### Completion Notes List
- Story file created with comprehensive context
- All acceptance criteria mapped from source document
- Architecture compliance verified
- Dependencies cross-referenced (US-001, US-002, US-004)
- Security requirements emphasized
- Previous story patterns applied (US-002, US-004, US-014)
- Enhanced Wallet class with full security features
- Added comprehensive unit tests (37 tests)
- All tests pass (312 project-wide tests)

### File List
- Created: `_bmad-output/implementation-artifacts/stories/2-016-wallet-management.md`
- Modified: `src/infrastructure/solana/wallet.py` - Enhanced Wallet class with security, multiple loading methods, signing
- Created: `tests/unit/infrastructure/solana/test_wallet.py` - 37 unit tests covering all functionality
- Modified: `src/infrastructure/solana/__init__.py` - Added InvalidPrivateKeyError and WalletSecurityError exports

## 📊 Change Log
- 2026-07-04: Enhanced Wallet class with full US-016 implementation. Added security checks (base58 validation, 32-byte length), multiple loading methods (__init__, from_private_key, from_env, from_keypair_path, default), signing methods (sign_transaction, sign_transaction_bytes, sign_message), and custom exceptions (InvalidPrivateKeyError, WalletSecurityError). All 37 new tests pass. Full regression suite passes (312 tests).

---
*Generated by BMad Method - Create Story Workflow*
*Story Context Engine: Comprehensive analysis for flawless implementation*
