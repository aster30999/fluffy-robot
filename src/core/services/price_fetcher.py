"""
Price Fetcher Service

Application service for fetching current prices from Jupiter API.
Implements caching to avoid rate limiting and proper error handling.

Architecture Decisions:
    AD-001: Clean Architecture Paradigm - Application Service layer
    AD-004: Dependency Injection Pattern - JupiterClient injected via constructor

Dependencies:
    - JupiterClient from src.infrastructure.jupiter.client (US-003)
    - Price, TokenPair from src.core.models.price (US-010)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from src.core.models.price import Price, TokenPair
from src.infrastructure.jupiter.client import JupiterClient

if TYPE_CHECKING:
    pass


# Custom Exceptions
class PriceFetchError(Exception):
    """Raised when price fetching fails."""
    pass


class RateLimitError(PriceFetchError):
    """Raised when rate limited by Jupiter API."""
    pass


class PriceFetcher:
    """Service for fetching current prices from Jupiter API.
    
    Uses dependency injection for JupiterClient to enable testing
    and support different implementations. Implements caching to
    avoid rate limiting issues.
    
    This is an async service to work with the async JupiterClient.
    
    Attributes:
        jupiter_client: Jupiter API client for fetching prices
        cache_ttl: Time-to-live for cached prices in seconds
        cache: Dictionary storing cached prices with timestamps
    """
    
    DEFAULT_CACHE_TTL = 30  # seconds
    
    def __init__(self, jupiter_client: "JupiterClient", cache_ttl: int = DEFAULT_CACHE_TTL):
        """Initialize PriceFetcher with Jupiter client and cache settings.
        
        Args:
            jupiter_client: Injected Jupiter API client
            cache_ttl: Cache time-to-live in seconds (default: 30)
        """
        self.jupiter_client = jupiter_client
        self.cache_ttl = cache_ttl
        self.cache: dict[str, tuple["Price", datetime]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def fetch_price(self, pair: "TokenPair", amount: float = 1.0) -> Optional["Price"]:
        """Fetch current price for a token pair.
        
        First checks cache, then falls back to Jupiter API.
        Handles errors and rate limiting gracefully.
        
        Args:
            pair: TokenPair to fetch price for
            amount: Amount to calculate quote value (default: 1.0, not used for price)
            
        Returns:
            Price object if successful, None if failed
            
        Raises:
            PriceFetchError: If price fetching fails after retries
        """
        # Try to get from cache first
        cached_price = self._get_cached_price(pair)
        if cached_price is not None:
            self.logger.debug(f"Cache hit for pair: {pair}")
            return cached_price
        
        # Fetch from API
        self.logger.info(f"Fetching price from Jupiter API for pair: {pair}")
        try:
            price = await self._fetch_from_api(pair)
            if price is None:
                self.logger.warning(f"Failed to fetch price for pair: {pair}")
                return None
            
            # Cache the result
            self._cache_price(pair, price)
            return price
            
        except RateLimitError:
            # Re-raise RateLimitError without wrapping
            raise
        except Exception as e:
            self.logger.error(f"Error fetching price for {pair}: {e}", exc_info=True)
            raise PriceFetchError(f"Failed to fetch price for {pair}: {e}") from e
    
    def _get_cached_price(self, pair: "TokenPair") -> Optional["Price"]:
        """Get price from cache if still valid (synchronous, thread-safe for reads).
        
        Args:
            pair: TokenPair to look up in cache
            
        Returns:
            Cached Price if valid and not expired, None otherwise
        """
        cache_key = self._get_cache_key(pair)
        if cache_key not in self.cache:
            return None
        
        cached_price, cached_time = self.cache[cache_key]
        
        # Check if cache has expired
        if datetime.now() - cached_time > timedelta(seconds=self.cache_ttl):
            self.logger.debug(f"Cache expired for pair: {pair}")
            del self.cache[cache_key]
            return None
        
        self.logger.debug(f"Returning cached price for pair: {pair}")
        return cached_price
    
    def _cache_price(self, pair: "TokenPair", price: "Price") -> None:
        """Cache a price for a token pair (synchronous, thread-safe for writes).
        
        Args:
            pair: TokenPair to cache
            price: Price to cache
        """
        cache_key = self._get_cache_key(pair)
        self.cache[cache_key] = (price, datetime.now())
        self.logger.debug(f"Cached price for pair: {pair}")
    
    def _get_cache_key(self, pair: "TokenPair") -> str:
        """Generate cache key for a token pair.
        
        Args:
            pair: TokenPair to generate key for
            
        Returns:
            String key for caching
        """
        # Use the pair's token symbols for cache key
        return f"{pair.base.symbol}-{pair.quote.symbol}"
    
    async def _fetch_from_api(self, pair: "TokenPair") -> Optional["Price"]:
        """Fetch price directly from Jupiter API.
        
        Uses JupiterClient.get_price() which returns output_amount / input_amount.
        
        Args:
            pair: TokenPair to fetch price for
            
        Returns:
            Price object if successful, None otherwise
            
        Raises:
            RateLimitError: If rate limited by Jupiter API
        """
        try:
            # Use JupiterClient.get_quote directly to get raw amounts
            # Pass a reasonable amount in base units (e.g., 1 token worth)
            # For SOL (9 decimals): 1 SOL = 10^9 lamports
            # For USDC (6 decimals): 1 USDC = 10^6 units
            base_units = 10 ** pair.base.decimals
            
            quote = await self.jupiter_client.get_quote(
                input_token=pair.base.mint,
                output_token=pair.quote.mint,
                amount=base_units,  # 1 token worth in base units
                slippage=0.01
            )
            
            # Calculate price in decimal units
            # output_amount is in quote token base units, convert to decimal
            # input_amount is in base token base units, convert to decimal (which is 1 token)
            price_value = quote.output_amount / (10 ** pair.quote.decimals)
            
            # If price_value is invalid, return None
            if price_value is None or not isinstance(price_value, (int, float)) or price_value <= 0:
                self.logger.warning(f"Invalid price value received: {price_value}")
                return None
            
            return Price(
                value=price_value,
                timestamp=datetime.now(),
                currency=pair.quote.symbol
            )
            
        except Exception as e:
            # Check if it's a rate limit error
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Check for various rate limit error types
            if ("rate limit" in error_str or "429" in error_str or 
                "RateLimit" in error_type or "JupiterRateLimitError" in error_type):
                self.logger.warning(f"Rate limited by Jupiter API: {e}")
                raise RateLimitError(f"Rate limited: {e}") from e
            
            self.logger.error(f"API error fetching price: {e}")
            raise
    
    def clear_cache(self) -> None:
        """Clear all cached prices."""
        self.cache.clear()
        self.logger.debug("Price cache cleared")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self.cache),
            "ttl": self.cache_ttl,
            "entries": list(self.cache.keys())
        }
    
    # Synchronous wrapper methods for convenience
    def fetch_price_sync(self, pair: "TokenPair", amount: float = 1.0) -> Optional["Price"]:
        """Synchronous version of fetch_price using asyncio.run.
        
        WARNING: This should only be used in synchronous contexts.
        For async contexts, use fetch_price() directly.
        
        Args:
            pair: TokenPair to fetch price for
            amount: Amount to calculate quote value (default: 1.0)
            
        Returns:
            Price object if successful, None if failed
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in current thread, create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.fetch_price(pair, amount))
        finally:
            # Clean up if we created the loop
            if loop is not asyncio.get_event_loop():
                loop.close()
