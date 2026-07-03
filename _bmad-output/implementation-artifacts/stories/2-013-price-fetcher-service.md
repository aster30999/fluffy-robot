---
title: "US-013: Price Fetcher Service"
story_id: "2-013-price-fetcher-service"
epic: "Epic 2: Core Trading Engine"
project: "Solana Trading Bot"
created: 2026-07-02
status: "ready-for-dev"
priority: P0
dependencies: ["US-003", "US-010"]
estimate_hours: 4
type: "technical"
mvp: true
source_epic: "/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md"
source_architecture: "/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md"
baseline_commit: "d9f22e8a14e1b3c4d5f6e7a8b9c0d1e2f3a4b5c6"
---

# US-013: Price Fetcher Service

## 🎯 User Story

**As a** trading bot  
**I want** to fetch current prices from Jupiter API  
**So that** I can make informed trading decisions

## ✅ Acceptance Criteria

- [ ] `PriceFetcher` class in `src/core/services/price_fetcher.py`
- [ ] Method: `fetch_price(pair: TokenPair, amount: float) -> Optional[Price]`
- [ ] Dependency injection: accepts `JupiterClient`
- [ ] Proper error handling and logging
- [ ] Cache prices for X seconds to avoid rate limiting
- [ ] Unit tests with mock JupiterClient

## 📋 Tasks

- [ ] Create `PriceFetcher` class in `src/core/services/price_fetcher.py`
- [ ] Implement `fetch_price(pair: TokenPair, amount: float) -> Optional[Price]` method
- [ ] Add dependency injection pattern for `JupiterClient`
- [ ] Add proper error handling for API failures and rate limiting
- [ ] Implement price caching mechanism (TTL-based)
- [ ] Add comprehensive logging for debugging and monitoring
- [ ] Write unit tests with mocked `JupiterClient` in `tests/unit/core/services/test_price_fetcher.py`

## 🏗️ Technical Implementation

### Service Layer Alignment

This story implements **Application Services** as defined in **AD-001: Clean Architecture Paradigm** and detailed in **ARCHITECTURE-SPINE.md §1201**. 

**Architecture Rule:** Application services coordinate between domain entities and external services. They MUST use dependency injection for all external dependencies.

### Module Structure

```
src/core/services/price_fetcher.py
├── PriceFetcher              # Main service class
│   ├── __init__(jupiter_client: JupiterClient)  # Dependency injection
│   ├── fetch_price(pair, amount) -> Optional[Price]
│   ├── _get_cached_price(pair) -> Optional[Price]
│   ├── _fetch_from_api(pair) -> Optional[Price]
│   └── _calculate_slippage(amount, price) -> float
└── PriceFetchError           # Custom exception (optional)
```

### Class Specifications

#### PriceFetcher Class
```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
import logging

class PriceFetcher:
    """Service for fetching current prices from Jupiter API.
    
    Uses dependency injection for JupiterClient to enable testing
    and support different implementations. Implements caching to
    avoid rate limiting issues.
    
    Attributes:
        jupiter_client: Jupiter API client for fetching prices
        cache_ttl: Time-to-live for cached prices in seconds
        cache: Dictionary storing cached prices with timestamps
    """
    
    def __init__(self, jupiter_client: "JupiterClient", cache_ttl: int = 30):
        """Initialize PriceFetcher with Jupiter client and cache settings.
        
        Args:
            jupiter_client: Injected Jupiter API client
            cache_ttl: Cache time-to-live in seconds (default: 30)
        """
        self.jupiter_client = jupiter_client
        self.cache_ttl = cache_ttl
        self.cache: dict[str, tuple[Price, datetime]] = {}
        self.logger = logging.getLogger(__name__)
    
    def fetch_price(self, pair: "TokenPair", amount: float) -> Optional["Price"]:
        """Fetch current price for a token pair.
        
        First checks cache, then falls back to Jupiter API.
        Handles errors and rate limiting gracefully.
        
        Args:
            pair: TokenPair to fetch price for
            amount: Amount to calculate quote value (optional)
            
        Returns:
            Price object if successful, None if failed
            
        Raises:
            PriceFetchError: If price fetching fails after retries
        """
        ...
    
    def _get_cached_price(self, pair: "TokenPair") -> Optional["Price"]:
        """Get price from cache if still valid."""
        ...
    
    def _fetch_from_api(self, pair: "TokenPair") -> Optional["Price"]:
        """Fetch price directly from Jupiter API."""
        ...
```

### Dependencies Context

**Hard Dependencies (must be complete):**
- US-001 (Project Structure Setup) - Ensures `src/core/services/` directory exists
- US-002 (Environment Configuration) - Provides configuration patterns
- US-003 (Infrastructure - Jupiter Client) - **CRITICAL:** JupiterClient implementation required
- US-010 (Domain Models - Price & Market Data) - **CRITICAL:** Price, Token, TokenPair models required

**Blocks:**
- US-014 (Balance Tracker Service) - Depends on PriceFetcher for balance calculations
- US-015 (Trade Executor Service) - Depends on PriceFetcher for trade execution pricing
- US-017 (Main Trading Loop) - Depends on PriceFetcher for real-time price updates
- US-030 (Decision Engine) - Depends on PriceFetcher for decision-making data

### Previous Story Intelligence (US-003, US-010)

**Patterns to follow from US-003 (Jupiter Client):**
- Use async/await for API calls to Jupiter
- Implement proper rate limiting and retry logic
- Handle Jupiter API errors (JupiterError, JupiterAPIError)
- Use token mint addresses for price lookups
- Add timeout configurations for API calls

**Patterns to follow from US-010 (Domain Models):**
- Use TYPE_CHECKING for circular imports (Price, TokenPair)
- All domain models are frozen dataclasses
- Use Google-style docstrings
- Implement serialization (to_dict, from_dict)

**Learnings applied:**
- Dependency injection for external services (JupiterClient)
- Cache with TTL to prevent rate limiting
- Proper error handling with custom exceptions
- Comprehensive logging for debugging

## 🔬 Dev Notes

### Architecture Compliance

- ✅ **AD-001 (Clean Architecture):** This is an Application Service - orchestrates between Domain (Price, TokenPair) and Infrastructure (JupiterClient)
- ✅ **AD-004 (Dependency Injection):** JupiterClient is injected via constructor
- ✅ **Separation of Concerns:** PriceFetcher handles only price fetching, not trading logic

### Design Decisions

1. **Caching Strategy:** TTL-based cache (30 seconds default) to balance performance and freshness
2. **Error Handling:** Graceful degradation - returns None on failure, logs errors
3. **Async Support:** Optional async version can be added if needed for performance
4. **Cache Key:** Uses TokenPair string representation for cache keys
5. **Rate Limiting:** Respects Jupiter API rate limits through caching and retry logic

### File Structure Requirements

- **Location:** `src/core/services/price_fetcher.py`
- **Module:** Part of `core.services` package
- **Exports:** PriceFetcher class in `src/core/services/__init__.py`
- **Imports:** JupiterClient from `src.infrastructure.jupiter.client`
- **Imports:** Price, TokenPair from `src.core.models.price`

## 🔬 Technical Requirements

### Libraries/Frameworks
- **Python:** 3.10+
- **Dependencies:** JupiterClient (from US-003), Price/TokenPair models (from US-010)
- **Optional:** cachetools for advanced caching (if needed)

### Error Handling
```python
class PriceFetchError(Exception):
    """Raised when price fetching fails."""
    pass

class RateLimitError(PriceFetchError):
    """Raised when rate limited by Jupiter API."""
    pass
```

### Logging Requirements
- Log all API calls with pair and amount
- Log cache hits/misses for debugging
- Log errors with full context (pair, error message, timestamp)

## 🧪 Testing Requirements

### Test File Location
- `tests/unit/core/services/test_price_fetcher.py`

### Test Cases

#### PriceFetcher Class Tests
- [ ] Test initialization with JupiterClient
- [ ] Test fetch_price returns cached value on second call
- [ ] Test fetch_price calls Jupiter API when cache empty
- [ ] Test cache expiration after TTL
- [ ] Test fetch_price with invalid TokenPair
- [ ] Test fetch_price with API failure
- [ ] Test proper error logging

#### Mock JupiterClient Tests
- [ ] Test with mocked JupiterClient returning valid price
- [ ] Test with mocked JupiterClient raising JupiterError
- [ ] Test with mocked JupiterClient raising timeout
- [ ] Test with mocked JupiterClient returning None

#### Edge Cases
- [ ] Test with zero amount
- [ ] Test with negative amount
- [ ] Test with same pair requested concurrently
- [ ] Test cache cleanup or size limits

## 📁 File Changes Required

**NEW Files:**
- `src/core/services/price_fetcher.py` - Main implementation
- `tests/unit/core/services/test_price_fetcher.py` - Unit tests

**MODIFIED Files:**
- `src/core/services/__init__.py` - Export PriceFetcher class

## 📚 References

- [Source: EPICS-AND-STORIES.md §347-371](/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md#us-013-price-fetcher-service)
- [Architecture: ARCHITECTURE-SPINE.md §1201-1220](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#application-services-coreservices)
- [Dependency: US-003 Infrastructure - Jupiter Client](/_bmad-output/implementation-artifacts/stories/1-003-infrastructure-jupiter-client.md)
- [Dependency: US-010 Domain Models - Price & Market Data](/_bmad-output/implementation-artifacts/stories/2-010-domain-models-price-market-data.md)
- [Architecture Decision: AD-001 Clean Architecture Paradigm](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-001-clean-architecture-paradigm)
- [Architecture Decision: AD-004 Dependency Injection Pattern](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-004-dependency-injection-pattern)

## 🤖 Dev Agent Record

### Agent Model Used
- Mistral Vibe CLI (mistral-medium-3.5)

### Debug Log References
- [Inception] User request: "create the next story"
- [Analysis] Extracted US-013 from EPICS-AND-STORIES.md §347
- [Architecture] Validated against ARCHITECTURE-SPINE.md §1201
- [Dependency] Verified US-003 and US-010 are complete

### Completion Notes List
- Story file created with comprehensive context
- All acceptance criteria mapped from source document
- Architecture compliance verified
- Dependencies cross-referenced (US-001, US-002, US-003, US-010)
- Technical specifications aligned with clean architecture principles
- Previous story patterns applied (US-003, US-010)

### File List
- Created: `_bmad-output/implementation-artifacts/stories/2-013-price-fetcher-service.md`
- Next: `src/core/services/price_fetcher.py` (to be created by dev-story)
- Next: `tests/unit/core/services/test_price_fetcher.py` (to be created by dev-story)

---
*Generated by BMad Method - Create Story Workflow*
*Story Context Engine: Comprehensive analysis for flawless implementation*
