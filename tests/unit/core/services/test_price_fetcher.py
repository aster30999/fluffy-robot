"""
Unit tests for PriceFetcher service (US-013).

Tests cover:
- PriceFetcher class initialization
- fetch_price method with caching
- Error handling and rate limiting
- Cache TTL expiration
- Mock JupiterClient integration
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import the classes under test
from src.core.services.price_fetcher import (
    PriceFetcher,
    PriceFetchError,
    RateLimitError,
)

# Import domain models (from US-010)
from src.core.models.price import Price, Token, TokenPair


# Test fixtures
@pytest.fixture
def mock_jupiter_client():
    """Create a mock JupiterClient for testing."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_token():
    """Create a mock Token for testing."""
    return Token(
        symbol="SOL",
        mint="So11111111111111111111111111111111111111112",
        decimals=9,
        name="Solana",
    )


@pytest.fixture
def mock_token_pair(mock_token):
    """Create a mock TokenPair for testing."""
    usdc = Token(
        symbol="USDC",
        mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        decimals=6,
        name="USD Coin",
    )
    return TokenPair(base=mock_token, quote=usdc)


@pytest.fixture
def price_fetcher(mock_jupiter_client):
    """Create a PriceFetcher instance with mock client."""
    return PriceFetcher(jupiter_client=mock_jupiter_client, cache_ttl=10)


# ============================================================================
# PriceFetcher Class Tests
# ============================================================================

class TestPriceFetcherInitialization:
    """Tests for PriceFetcher initialization."""

    def test_init_with_jupiter_client(self, mock_jupiter_client):
        """Test initialization with JupiterClient."""
        fetcher = PriceFetcher(jupiter_client=mock_jupiter_client)
        assert fetcher.jupiter_client == mock_jupiter_client
        assert fetcher.cache_ttl == 30  # Default TTL
        assert fetcher.cache == {}

    def test_init_with_custom_cache_ttl(self, mock_jupiter_client):
        """Test initialization with custom cache TTL."""
        fetcher = PriceFetcher(jupiter_client=mock_jupiter_client, cache_ttl=60)
        assert fetcher.cache_ttl == 60

    def test_init_with_zero_cache_ttl(self, mock_jupiter_client):
        """Test initialization with zero cache TTL (effectively no caching)."""
        fetcher = PriceFetcher(jupiter_client=mock_jupiter_client, cache_ttl=0)
        assert fetcher.cache_ttl == 0


class TestPriceFetcherFetchPrice:
    """Tests for fetch_price method."""

    @pytest.mark.asyncio
    async def test_fetch_price_returns_cached_value(self, price_fetcher, mock_token_pair):
        """Test fetch_price returns cached value on second call."""
        # Setup: put a price in cache
        cached_price = Price(value=150.50, timestamp=datetime.now(), currency="USDC")
        price_fetcher._cache_price(mock_token_pair, cached_price)
        
        # First call should return cached value
        result = await price_fetcher.fetch_price(mock_token_pair)
        assert result == cached_price
        
        # Verify Jupiter API was NOT called
        price_fetcher.jupiter_client.get_price.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_price_calls_api_when_cache_empty(self, price_fetcher, mock_jupiter_client, mock_token_pair):
        """Test fetch_price calls Jupiter API when cache is empty."""
        # Setup: mock get_price to return a value
        mock_jupiter_client.get_price.return_value = 150.50
        
        # Call fetch_price
        result = await price_fetcher.fetch_price(mock_token_pair)
        
        # Verify API was called
        mock_jupiter_client.get_price.assert_called_once()
        
        # Verify result is a Price object
        assert isinstance(result, Price)
        assert result.value == 150.50
        assert result.currency == "USDC"
        
        # Verify price was cached
        cached = price_fetcher._get_cached_price(mock_token_pair)
        assert cached is not None
        assert cached.value == 150.50

    @pytest.mark.asyncio
    async def test_fetch_price_with_api_failure(self, price_fetcher, mock_jupiter_client, mock_token_pair):
        """Test fetch_price with API failure returns None."""
        # Setup: mock get_price to return None
        mock_jupiter_client.get_price.return_value = None
        
        # Call fetch_price
        result = await price_fetcher.fetch_price(mock_token_pair)
        
        # Verify result is None
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_price_with_exception(self, price_fetcher, mock_jupiter_client, mock_token_pair):
        """Test fetch_price with exception raises PriceFetchError."""
        # Setup: mock get_price to raise exception
        mock_jupiter_client.get_price.side_effect = Exception("API Error")
        
        # Call fetch_price and expect exception
        with pytest.raises(PriceFetchError) as exc_info:
            await price_fetcher.fetch_price(mock_token_pair)
        
        assert "Failed to fetch price" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_price_with_rate_limit(self, price_fetcher, mock_jupiter_client, mock_token_pair):
        """Test fetch_price with rate limit raises RateLimitError."""
        # Setup: mock get_price to raise rate limit error
        from src.infrastructure.jupiter.client import JupiterRateLimitError
        mock_jupiter_client.get_price.side_effect = JupiterRateLimitError("Rate limited")
        
        # Call fetch_price and expect RateLimitError
        with pytest.raises(RateLimitError) as exc_info:
            await price_fetcher.fetch_price(mock_token_pair)
        
        assert "Rate limited" in str(exc_info.value)


# ============================================================================
# Cache Tests
# ============================================================================

class TestPriceFetcherCache:
    """Tests for caching mechanism."""

    def test_cache_price_and_retrieve(self, price_fetcher, mock_token_pair):
        """Test caching a price and retrieving it."""
        price = Price(value=100.0, timestamp=datetime.now(), currency="USDC")
        
        # Cache the price
        price_fetcher._cache_price(mock_token_pair, price)
        
        # Retrieve from cache
        cached = price_fetcher._get_cached_price(mock_token_pair)
        assert cached == price

    def test_cache_miss(self, price_fetcher, mock_token_pair):
        """Test cache miss returns None."""
        result = price_fetcher._get_cached_price(mock_token_pair)
        assert result is None

    def test_cache_expiration(self, price_fetcher, mock_token_pair):
        """Test cache expiration after TTL."""
        # Set very short TTL
        price_fetcher.cache_ttl = 1
        
        price = Price(value=100.0, timestamp=datetime.now(), currency="USDC")
        price_fetcher._cache_price(mock_token_pair, price)
        
        # Should be in cache
        cached = price_fetcher._get_cached_price(mock_token_pair)
        assert cached is not None
        
        # Wait for expiration
        import time
        time.sleep(1.1)
        
        # Should be expired
        cached = price_fetcher._get_cached_price(mock_token_pair)
        assert cached is None

    def test_clear_cache(self, price_fetcher, mock_token_pair):
        """Test clear_cache method."""
        price = Price(value=100.0, timestamp=datetime.now(), currency="USDC")
        price_fetcher._cache_price(mock_token_pair, price)
        
        # Verify cache has entry
        assert len(price_fetcher.cache) == 1
        
        # Clear cache
        price_fetcher.clear_cache()
        
        # Verify cache is empty
        assert len(price_fetcher.cache) == 0

    def test_get_cache_stats(self, price_fetcher, mock_token_pair):
        """Test get_cache_stats method."""
        price = Price(value=100.0, timestamp=datetime.now(), currency="USDC")
        price_fetcher._cache_price(mock_token_pair, price)
        
        stats = price_fetcher.get_cache_stats()
        assert stats["size"] == 1
        assert stats["ttl"] == 10
        assert len(stats["entries"]) == 1


# ============================================================================
# Cache Key Generation Tests
# ============================================================================

class TestPriceFetcherCacheKey:
    """Tests for cache key generation."""

    def test_get_cache_key(self, price_fetcher, mock_token_pair):
        """Test cache key generation."""
        key = price_fetcher._get_cache_key(mock_token_pair)
        assert key == "SOL-USDC"

    def test_get_cache_key_different_pairs(self, price_fetcher, mock_token):
        """Test cache keys are different for different pairs."""
        usdc = Token(symbol="USDC", mint="USDC_ADDR", name="USD Coin", decimals=6)
        sol = Token(symbol="SOL", mint="SOL_ADDR", name="Solana", decimals=9)
        
        pair1 = TokenPair(base=sol, quote=usdc)
        pair2 = TokenPair(base=usdc, quote=sol)
        
        key1 = price_fetcher._get_cache_key(pair1)
        key2 = price_fetcher._get_cache_key(pair2)
        
        assert key1 == "SOL-USDC"
        assert key2 == "USDC-SOL"
        assert key1 != key2


# ============================================================================
# Mock JupiterClient Tests
# ============================================================================

class TestPriceFetcherWithMockClient:
    """Tests using mocked JupiterClient with different scenarios."""

    @pytest.mark.asyncio
    async def test_with_valid_price_response(self, mock_jupiter_client, mock_token_pair):
        """Test with mocked JupiterClient returning valid price."""
        mock_jupiter_client.get_price.return_value = 200.75
        
        fetcher = PriceFetcher(jupiter_client=mock_jupiter_client)
        result = await fetcher.fetch_price(mock_token_pair)
        
        assert result is not None
        assert result.value == 200.75
        assert result.currency == "USDC"
        assert isinstance(result.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_with_none_response(self, mock_jupiter_client, mock_token_pair):
        """Test with mocked JupiterClient returning None."""
        mock_jupiter_client.get_price.return_value = None
        
        fetcher = PriceFetcher(jupiter_client=mock_jupiter_client)
        result = await fetcher.fetch_price(mock_token_pair)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_with_exception_response(self, mock_jupiter_client, mock_token_pair):
        """Test with mocked JupiterClient raising exception."""
        mock_jupiter_client.get_price.side_effect = Exception("Network error")
        
        fetcher = PriceFetcher(jupiter_client=mock_jupiter_client)
        
        with pytest.raises(PriceFetchError):
            await fetcher.fetch_price(mock_token_pair)

    @pytest.mark.asyncio
    async def test_with_rate_limit_exception(self, mock_jupiter_client, mock_token_pair):
        """Test with mocked JupiterClient raising rate limit exception."""
        from src.infrastructure.jupiter.client import JupiterRateLimitError
        mock_jupiter_client.get_price.side_effect = JupiterRateLimitError("Rate limited")
        
        fetcher = PriceFetcher(jupiter_client=mock_jupiter_client)
        
        with pytest.raises(RateLimitError):
            await fetcher.fetch_price(mock_token_pair)


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestPriceFetcherEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_with_zero_amount(self, price_fetcher, mock_jupiter_client, mock_token_pair):
        """Test fetch_price with zero amount (should still work)."""
        mock_jupiter_client.get_price.return_value = 100.0
        
        result = await price_fetcher.fetch_price(mock_token_pair, amount=0)
        assert result is not None
        assert result.value == 100.0

    @pytest.mark.asyncio
    async def test_with_negative_amount(self, price_fetcher, mock_jupiter_client, mock_token_pair):
        """Test fetch_price with negative amount."""
        mock_jupiter_client.get_price.return_value = 100.0
        
        result = await price_fetcher.fetch_price(mock_token_pair, amount=-1.0)
        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_pairs_caching(self, price_fetcher, mock_jupiter_client, mock_token):
        """Test caching works correctly with multiple pairs."""
        usdc = Token(symbol="USDC", mint="USDC_ADDR", name="USD Coin", decimals=6)
        sol = Token(symbol="SOL", mint="SOL_ADDR", name="Solana", decimals=9)
        
        pair1 = TokenPair(base=sol, quote=usdc)
        pair2 = TokenPair(base=usdc, quote=sol)
        
        # Mock different prices for each pair
        mock_jupiter_client.get_price.side_effect = [150.0, 0.0067]
        
        # Fetch both prices
        result1 = await price_fetcher.fetch_price(pair1)
        result2 = await price_fetcher.fetch_price(pair2)
        
        # Verify both are cached
        cached1 = price_fetcher._get_cached_price(pair1)
        cached2 = price_fetcher._get_cached_price(pair2)
        
        assert cached1.value == 150.0
        assert cached2.value == 0.0067
        assert len(price_fetcher.cache) == 2


# ============================================================================
# Logging Tests
# ============================================================================

class TestPriceFetcherLogging:
    """Tests for logging behavior."""

    @pytest.mark.asyncio
    async def test_cache_hit_logging(self, price_fetcher, mock_token_pair, caplog):
        """Test logging on cache hit."""
        price = Price(value=100.0, timestamp=datetime.now(), currency="USDC")
        price_fetcher._cache_price(mock_token_pair, price)
        
        with caplog.at_level("DEBUG"):
            await price_fetcher.fetch_price(mock_token_pair)
        
        assert "Cache hit" in caplog.text

    @pytest.mark.asyncio
    async def test_api_fetch_logging(self, price_fetcher, mock_jupiter_client, mock_token_pair, caplog):
        """Test logging on API fetch."""
        mock_jupiter_client.get_price.return_value = 100.0
        
        with caplog.at_level("INFO"):
            await price_fetcher.fetch_price(mock_token_pair)
        
        assert "Fetching price from Jupiter API" in caplog.text

    @pytest.mark.asyncio
    async def test_error_logging(self, price_fetcher, mock_jupiter_client, mock_token_pair, caplog):
        """Test logging on error."""
        mock_jupiter_client.get_price.side_effect = Exception("API Error")
        
        with caplog.at_level("ERROR"):
            with pytest.raises(PriceFetchError):
                await price_fetcher.fetch_price(mock_token_pair)
        
        assert "Error fetching price" in caplog.text
