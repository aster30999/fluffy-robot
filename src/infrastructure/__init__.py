"""
Infrastructure Layer

External integrations and framework-specific implementations.
Contains:
- Jupiter API client (HTTP)
- Solana RPC client (mixed solana-py + solders)
- Other external service integrations
"""

# Re-export for convenience
from .jupiter import *
from .solana import *
