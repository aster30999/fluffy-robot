"""
Jupiter API V2 HTTP Client

Async client for Jupiter API V2 using httpx.
Implements quote, order, and execute endpoints.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from functools import wraps
from enum import Enum

import httpx
from httpx import AsyncClient, Response, RequestError, HTTPStatusError

from src.config import settings


# Configure logger
logger = logging.getLogger(__name__)


class JupiterError(Exception):
    """Base exception for Jupiter API errors."""
    pass


class JupiterRateLimitError(JupiterError):
    """Rate limit exceeded."""
    pass


class JupiterTimeoutError(JupiterError):
    """Request timeout."""
    pass


class JupiterInvalidResponseError(JupiterError):
    """Invalid response from API."""
    pass


class JupiterQuoteError(JupiterError):
    """Error getting quote."""
    pass


class JupiterOrderError(JupiterError):
    """Error creating order."""
    pass


class JupiterExecuteError(JupiterError):
    """Error executing transaction."""
    pass


@dataclass
class QuoteResponse:
    """Response from /quote endpoint."""
    input_amount: float
    output_amount: float
    price_impact: float
    fees: Dict[str, float]
    route: List[Dict[str, Any]]
    raw: Dict[str, Any] = field(default_factory=dict)  # Full response


@dataclass
class OrderResponse:
    """Response from /order endpoint."""
    swap_transaction: str  # Base64 encoded transaction
    setup_transaction: Optional[str] = None
    cleanup_transaction: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)  # Full response


@dataclass
class ExecuteResponse:
    """Response from /execute endpoint."""
    transaction_signature: str
    raw: Dict[str, Any] = field(default_factory=dict)  # Full response


@dataclass
class Token:
    """Token information."""
    address: str
    symbol: str
    name: str
    decimals: int
    logo_uri: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class JupiterClient:
    """
    Async HTTP client for Jupiter API V2.
    
    Uses httpx.AsyncClient for all requests.
    Implements quote, order, and execute endpoints.
    Includes retry logic with exponential backoff.
    """
    
    # Jupiter API V2 endpoints
    QUOTE_ENDPOINT = "/v6/quote"
    ORDER_ENDPOINT = "/v6/order"
    EXECUTE_ENDPOINT = "/v6/execute"
    
    # Default headers
    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Jupiter client.
        
        Args:
            base_url: Base API URL (default from settings)
            api_key: Jupiter API key (optional, from settings if not provided)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Initial delay between retries in seconds
        """
        self.base_url = base_url or getattr(settings, 'jupiter_api_url', 'https://quote-api.jup.ag')
        self.api_key = api_key or (getattr(settings, 'jupiter_api_key', None))
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._client: Optional[AsyncClient] = None
        logger.info(f"JupiterClient initialized with base_url={self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_client(self) -> AsyncClient:
        """Ensure client is initialized."""
        if self._client is None or self._client.is_closed:
            headers = self.DEFAULT_HEADERS.copy()
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
            logger.debug("Jupiter AsyncClient initialized")
        return self._client
    
    async def close(self):
        """Close the client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("Jupiter AsyncClient closed")
            self._client = None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx
            
        Returns:
            JSON response as dictionary
            
        Raises:
            JupiterRateLimitError: If rate limited (429)
            JupiterTimeoutError: If request times out
            JupiterInvalidResponseError: If response is invalid
            JupiterError: For other errors
        """
        client = await self._ensure_client()
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await client.request(method, endpoint, **kwargs)
                
                # Check for errors
                if response.status_code == 429:
                    # Rate limited
                    retry_after = float(response.headers.get('retry-after', self.retry_delay))
                    if attempt < self.max_retries:
                        logger.warning(f"Rate limited. Retrying after {retry_after}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        await asyncio.sleep(retry_after)
                        continue
                    raise JupiterRateLimitError(f"Rate limit exceeded after {self.max_retries} retries")
                elif response.status_code == 400:
                    # Bad request - invalid response
                    raise JupiterInvalidResponseError(f"Bad request {response.status_code}: {response.text}")
                elif 400 < response.status_code < 600:
                    # Other HTTP errors
                    raise JupiterError(f"HTTP error {response.status_code}: {response.text}")
                
                # Parse JSON
                try:
                    return response.json()
                except ValueError as e:
                    raise JupiterInvalidResponseError(f"Invalid JSON response: {e}")
                    
            except (RequestError, HTTPStatusError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Request failed: {e}. Retrying in {delay}s (attempt {attempt + 1}/{self.max_retries + 1})")
                    await asyncio.sleep(delay)
                    continue
                
                # Map to specific exceptions
                if isinstance(e, HTTPStatusError):
                    if e.response.status_code == 400:
                        raise JupiterInvalidResponseError(f"Bad request: {e}")
                    elif e.response.status_code == 401:
                        raise JupiterError(f"Unauthorized: {e}")
                    elif e.response.status_code == 404:
                        raise JupiterError(f"Endpoint not found: {e}")
                    elif e.response.status_code == 500:
                        raise JupiterError(f"Server error: {e}")
                
                raise JupiterError(f"Request failed after {self.max_retries} retries: {e}")
        
        raise JupiterError(f"Request failed: {last_exception}")
    
    async def get_quote(
        self,
        input_token: str,
        output_token: str,
        amount: Union[int, float, str],
        slippage: float = 0.01,
        swap_mode: str = "ExactIn",
        **kwargs
    ) -> QuoteResponse:
        """
        Get a price quote from Jupiter.
        
        Args:
            input_token: Input token mint address or symbol
            output_token: Output token mint address or symbol
            amount: Amount to swap (in input token units)
            slippage: Maximum allowed slippage (0-1)
            swap_mode: "ExactIn" or "ExactOut"
            **kwargs: Additional query parameters
            
        Returns:
            QuoteResponse with price information
            
        Raises:
            JupiterQuoteError: If quote cannot be obtained
        """
        logger.debug(f"Getting quote: {input_token} -> {output_token}, amount={amount}")
        
        params = {
            "inputMint": input_token,
            "outputMint": output_token,
            "amount": str(amount),
            "slippageBps": int(slippage * 10000),  # Convert to basis points
            "swapMode": swap_mode,
            **kwargs
        }
        
        try:
            data = await self._request("GET", self.QUOTE_ENDPOINT, params=params)
        except JupiterError as e:
            raise JupiterQuoteError(f"Failed to get quote: {e}")
        
        # Validate required fields
        if "outAmount" not in data:
            raise JupiterQuoteError("Invalid quote response: missing outAmount field")
        if "quoteId" not in data:
            raise JupiterQuoteError("Invalid quote response: missing quoteId field")
        
        # Parse response
        try:
            return QuoteResponse(
                input_amount=float(amount),
                output_amount=float(data.get("outAmount", 0)),
                price_impact=float(data.get("priceImpactPct", 0)),
                fees={str(k): float(v) for k, v in data.get("fees", {}).items()},
                route=data.get("route", []),
                raw=data
            )
        except (KeyError, ValueError, TypeError) as e:
            raise JupiterQuoteError(f"Invalid quote response format: {e}")
    
    async def create_order(
        self,
        quote_response: Union[QuoteResponse, Dict[str, Any]],
        **kwargs
    ) -> OrderResponse:
        """
        Create a swap order from a quote.
        
        Args:
            quote_response: QuoteResponse or raw quote data
            **kwargs: Additional request parameters
            
        Returns:
            OrderResponse with transaction data
            
        Raises:
            JupiterOrderError: If order cannot be created
        """
        logger.debug("Creating order from quote")
        
        # Extract quote response ID
        if isinstance(quote_response, QuoteResponse):
            quote_data = quote_response.raw
        else:
            quote_data = quote_response
        
        quote_id = quote_data.get("quoteId")
        if not quote_id:
            raise JupiterOrderError("No quoteId in quote response")
        
        payload = {
            "quoteId": quote_id,
            "wrapUnwrapSol": True,
            **kwargs
        }
        
        try:
            data = await self._request("POST", self.ORDER_ENDPOINT, json=payload)
        except JupiterError as e:
            raise JupiterOrderError(f"Failed to create order: {e}")
        
        # Parse response
        try:
            return OrderResponse(
                swap_transaction=data.get("swapTransaction"),
                setup_transaction=data.get("setupTransaction"),
                cleanup_transaction=data.get("cleanupTransaction"),
                raw=data
            )
        except (KeyError, TypeError) as e:
            raise JupiterOrderError(f"Invalid order response format: {e}")
    
    async def execute_order(
        self,
        order_response: Union[OrderResponse, Dict[str, Any]],
        **kwargs
    ) -> ExecuteResponse:
        """
        Execute a swap order.
        
        Args:
            order_response: OrderResponse or raw order data
            **kwargs: Additional request parameters
            
        Returns:
            ExecuteResponse with transaction signature
            
        Raises:
            JupiterExecuteError: If execution fails
        """
        logger.debug("Executing order")
        
        # Extract transactions
        if isinstance(order_response, OrderResponse):
            swap_tx = order_response.swap_transaction
            setup_tx = order_response.setup_transaction
            cleanup_tx = order_response.cleanup_transaction
        else:
            swap_tx = order_response.get("swapTransaction")
            setup_tx = order_response.get("setupTransaction")
            cleanup_tx = order_response.get("cleanupTransaction")
        
        if not swap_tx:
            raise JupiterExecuteError("No swap transaction in order response")
        
        payload = {
            "swapTransaction": swap_tx,
        }
        if setup_tx:
            payload["setupTransaction"] = setup_tx
        if cleanup_tx:
            payload["cleanupTransaction"] = cleanup_tx
        
        try:
            data = await self._request("POST", self.EXECUTE_ENDPOINT, json=payload)
        except JupiterError as e:
            raise JupiterExecuteError(f"Failed to execute order: {e}")
        
        # Parse response
        try:
            return ExecuteResponse(
                transaction_signature=data.get("transactionSignature", ""),
                raw=data
            )
        except (KeyError, TypeError) as e:
            raise JupiterExecuteError(f"Invalid execute response format: {e}")
    
    async def swap(
        self,
        input_token: str,
        output_token: str,
        amount: Union[int, float, str],
        slippage: float = 0.01,
        **kwargs
    ) -> ExecuteResponse:
        """
        Convenience method: quote + order + execute in one call.
        
        Args:
            input_token: Input token mint address or symbol
            output_token: Output token mint address or symbol
            amount: Amount to swap
            slippage: Maximum allowed slippage
            **kwargs: Additional parameters for quote/order/execute
            
        Returns:
            ExecuteResponse with transaction signature
            
        Raises:
            JupiterError: If any step fails
        """
        logger.info(f"Swapping {amount} {input_token} -> {output_token}")
        
        # Get quote
        quote = await self.get_quote(input_token, output_token, amount, slippage, **kwargs)
        
        # Create order
        order = await self.create_order(quote, **kwargs)
        
        # Execute order
        return await self.execute_order(order, **kwargs)
    
    async def get_tokens(self) -> List[Token]:
        """
        Get list of supported tokens.
        
        Returns:
            List of Token objects
        """
        logger.debug("Getting token list")
        
        # Note: Jupiter doesn't have a public token list endpoint in V2
        # This would need to be fetched from a different source or cached
        # For now, return empty list
        # In production, this would fetch from Jupiter's token list API
        return []
    
    async def get_price(
        self,
        input_token: str,
        output_token: str,
        amount: Union[int, float, str] = 1,
    ) -> float:
        """
        Get current price for a token pair.
        
        Args:
            input_token: Input token mint address or symbol
            output_token: Output token mint address or symbol
            amount: Amount to quote (default: 1)
            
        Returns:
            Output amount for 1 unit of input token
        """
        quote = await self.get_quote(input_token, output_token, amount)
        return quote.output_amount / float(amount)


# Singleton instance (optional)
_jupiter_client: Optional[JupiterClient] = None


async def get_jupiter_client() -> JupiterClient:
    """Get a shared JupiterClient instance."""
    global _jupiter_client
    if _jupiter_client is None:
        _jupiter_client = JupiterClient()
    return _jupiter_client
