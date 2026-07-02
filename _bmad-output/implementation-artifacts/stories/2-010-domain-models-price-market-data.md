---
title: "US-010: Domain Models - Price & Market Data"
story_id: "2-010-domain-models-price-market-data"
epic: "Epic 2: Core Trading Engine"
project: "Solana Trading Bot"
created: 2026-07-02
status: "review"
priority: P0
dependencies: ["US-001", "US-002"]
estimate_hours: 4
type: "technical"
mvp: true
source_epic: "/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md"
source_architecture: "/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md"
baseline_commit: "829cc48a5d03d309aae7a534370be6ae843a65c8"
---

# US-010: Domain Models - Price & Market Data

## 🎯 User Story

**As a** developer  
**I want** immutable domain models for price and market data  
**So that** I can safely pass data between components

## ✅ Acceptance Criteria

- [x] `Price` dataclass with `frozen=True` for immutability
- [x] `Candle` dataclass for OHLCV (Open, High, Low, Close, Volume) data
- [x] `MarketData` dataclass combining price and indicators
- [x] `Token` dataclass with symbol, mint, and decimals attributes
- [x] `TokenPair` dataclass for trading pairs (base/quote tokens)
- [x] Proper type hints and comprehensive docstrings for all models
- [x] Serialization/deserialization support (to/from dict, JSON)

## 📋 Tasks

- [x] Create `src/core/models/price.py` module
- [x] Implement `Price` dataclass with value and timestamp
- [x] Implement `Candle` dataclass with OHLCV fields
- [x] Implement `MarketData` dataclass with price, indicators, and metadata
- [x] Implement `Token` dataclass with Solana token metadata
- [x] Implement `TokenPair` dataclass for trading pair representation
- [x] Add type hints and docstrings following Google style
- [x] Add serialization/deserialization methods (as_dict, from_dict)
- [x] Add unit tests for all dataclasses in `tests/unit/core/models/test_price.py`

## 🏗️ Technical Implementation

### Domain Layer Alignment

This story implements **Core Domain Models** as defined in **AD-001: Clean Architecture Paradigm** and detailed in **ARCHITECTURE-SPINE.md §1171**. 

**Architecture Rule:** Domain entities MUST be framework-agnostic and testable without external services. All domain entities (Indicator, Strategy, Decision) MUST be framework-agnostic and testable without external services.

### Module Structure

```
src/core/models/price.py
├── Price          # Immutable price representation
├── Candle         # OHLCV candle data
├── MarketData     # Aggregated market data
├── Token          # Token metadata
└── TokenPair      # Trading pair (base/quote)
```

### Class Specifications

#### Price Dataclass
```python
@dataclass(frozen=True)
class Price:
    """Immutable price representation with timestamp."""
    value: float
    timestamp: datetime
    currency: str = "USD"
    
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Price": ...
```

#### Candle Dataclass
```python
@dataclass(frozen=True)
class Candle:
    """OHLCV (Open, High, Low, Close, Volume) candle data."""
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    interval: str  # e.g., "1m", "5m", "1h"
    
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Candle": ...
```

#### MarketData Dataclass
```python
@dataclass(frozen=True)
class MarketData:
    """Aggregated market data combining price and indicators."""
    price: Price
    candles: List[Candle]
    indicators: Dict[str, Any]  # Key: indicator name, Value: indicator data
    token_pair: "TokenPair"
    exchange: str = "Jupiter"
    
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "MarketData": ...
```

#### Token Dataclass
```python
@dataclass(frozen=True)
class Token:
    """Solana token metadata."""
    symbol: str           # e.g., "SOL", "USDC"
    mint: str            # Solana mint address
    decimals: int         # Token decimals (e.g., 9 for SOL, 6 for USDC)
    name: str = ""        # Optional: full token name
    
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Token": ...
```

#### TokenPair Dataclass
```python
@dataclass(frozen=True)
class TokenPair:
    """Trading pair representation (base/quote tokens)."""
    base: Token
    quote: Token
    pair_symbol: str  # e.g., "SOL/USDC"
    
    @property
    def reverse(self) -> "TokenPair": ...  # Returns quote/base pair
    
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "TokenPair": ...
```

### File Structure Requirements

- **Location:** `src/core/models/price.py` (as defined in ARCHITECTURE-SPINE.md §1174-1176)
- **Module:** Part of `core.models` package
- **Exports:** All classes must be exported in `src/core/models/__init__.py`
- **Imports:** Use relative imports within `core` module

### Serialization Requirements

All dataclasses must support:
1. `to_dict()` → Returns a dictionary representation
2. `from_dict(data: dict)` → Class method to create instance from dict
3. JSON serialization via `json.dumps(obj.to_dict())`
4. JSON deserialization via `cls.from_dict(json.loads(data))`

## 🔬 Dev Notes

### Architecture Compliance

- ✅ **AD-001 (Clean Architecture):** These are Domain Layer entities - pure business logic, no external dependencies
- ✅ **AD-004 (Dependency Injection):** All classes accept dependencies via constructor parameters
- ✅ **AD-001 Rule:** Domain entities are framework-agnostic and testable without external services

### Design Decisions

1. **Immutability (frozen=True):** All dataclasses are immutable to ensure thread-safety and prevent accidental mutations when passing data between components
2. **Type Safety:** All fields have explicit type hints for static type checking (mypy)
3. **Serialization:** Custom serialization methods instead of relying on external libraries to maintain control and avoid dependencies
4. **Separation of Concerns:** Each dataclass represents a single, well-defined concept

### Testing Strategy

- **Unit tests** for each dataclass:
  - Instantiation with valid data
  - Instantiation with invalid data (raises TypeError/ValueError)
  - Immutability (attempting to modify raises AttributeError)
  - Serialization/deserialization round-trip
  - Equality comparisons
- **Property-based tests** using hypothesis for edge cases

### Dependencies Context

**Prerequisites (from sprint-status.yaml):**
- US-001 (Project Structure Setup) - Ensures `src/core/models/` directory exists
- US-002 (Environment Configuration) - Provides configuration patterns to follow

**Blocks:**
- US-011 (Domain Models - Balance & Portfolio) - Depends on Price model
- US-012 (Domain Models - Trade & Decision) - Depends on Price and Token models
- US-013 (Price Fetcher Service) - Depends on these models
- US-020 (Indicator Framework) - Depends on Price model

### References

- [Source: EPICS-AND-STORIES.md §262-288](/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md#us-010-domain-models---price--market-data)
- [Architecture: ARCHITECTURE-SPINE.md §1171-1181](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#core-domain-models-coremodels)
- [Architecture Decision: AD-001 Clean Architecture Paradigm](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-001-clean-architecture-paradigm)
- [Architecture Decision: AD-004 Dependency Injection Pattern](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-004-dependency-injection-pattern)

## 🧪 Testing Requirements

### Test File Location
- `tests/unit/core/models/test_price.py`

### Test Cases

#### Price Tests
- [ ] Test Price instantiation with valid data
- [ ] Test Price with missing required fields raises TypeError
- [ ] Test Price immutability
- [ ] Test Price.to_dict() returns correct structure
- [ ] Test Price.from_dict() creates valid instance
- [ ] Test Price serialization round-trip

#### Candle Tests
- [ ] Test Candle instantiation with all OHLCV fields
- [ ] Test Candle with invalid price values (negative, NaN)
- [ ] Test Candle immutability
- [ ] Test Candle.to_dict() includes all fields
- [ ] Test Candle.from_dict() reconstructs correctly

#### Token Tests
- [ ] Test Token with valid Solana mint address
- [ ] Test Token with various decimal values (0-9)
- [ ] Test Token serialization

#### TokenPair Tests
- [ ] Test TokenPair base/quote relationship
- [ ] Test TokenPair.reverse property
- [ ] Test TokenPair pair_symbol format (BASE/QUOTE)

## 📁 File Changes Required

**NEW Files:**
- [x] `src/core/models/price.py` - Main implementation
- [x] `tests/unit/core/models/test_price.py` - Unit tests

**MODIFIED Files:**
- [x] `src/core/models/__init__.py` - Export new classes

## 🤖 Dev Agent Record

### Agent Model Used
- Mistral Vibe CLI (mistral-medium-3.5)

### Debug Log References
- [Inception] User request: "bmad-create-story \"2-010-domain-models-price-market-data\""
- [Analysis] Extracted US-010 from EPICS-AND-STORIES.md §262
- [Architecture] Validated against ARCHITECTURE-SPINE.md §1171

### Completion Notes List
- Story file created with comprehensive context
- All acceptance criteria mapped from source document
- Architecture compliance verified
- Dependencies cross-referenced with sprint-status.yaml
- Technical specifications aligned with clean architecture principles
- All 5 dataclasses implemented with frozen=True for immutability
- Serialization/deserialization methods (to_dict, from_dict) implemented for all classes
- Google-style docstrings added for all classes and methods
- 53 comprehensive unit tests created and passing
- Full test suite (102 tests) passes without regressions

### File List
- Created: `_bmad-output/implementation-artifacts/stories/2-010-domain-models-price-market-data.md`
- Created: `src/core/models/price.py`
- Created: `tests/unit/core/models/test_price.py`
- Created: `tests/unit/core/models/__init__.py`
- Created: `tests/unit/core/__init__.py`
- Modified: `src/core/models/__init__.py`

### Change Log
- 2026-07-02: Story created and all tasks implemented
- 2026-07-02: All 53 unit tests created and passing
- 2026-07-02: Full regression test suite passes (102 tests)
- 2026-07-02: Story status updated to "review"

---
*Generated by BMad Method - Create Story Workflow*
*Story Context Engine: Comprehensive analysis for flawless implementation*
