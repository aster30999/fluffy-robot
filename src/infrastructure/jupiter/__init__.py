"""
Jupiter API Integration

HTTP client for Jupiter API V2.

Exports:
- JupiterClient: Main client class
- JupiterError: Base exception
- JupiterQuoteError: Quote-specific exception
- JupiterOrderError: Order-specific exception
- JupiterExecuteError: Execute-specific exception
- QuoteResponse: Data class for quote responses
- OrderResponse: Data class for order responses
- ExecuteResponse: Data class for execute responses
- get_jupiter_client: Get shared client instance
"""

from .client import (
    JupiterClient,
    JupiterError,
    JupiterRateLimitError,
    JupiterTimeoutError,
    JupiterInvalidResponseError,
    JupiterQuoteError,
    JupiterOrderError,
    JupiterExecuteError,
    QuoteResponse,
    OrderResponse,
    ExecuteResponse,
    Token,
    get_jupiter_client,
)

__version__ = "0.1.0"
