---
title: "US-012: Domain Models - Trade & Decision"
story_id: "2-012-domain-models-trade-decision"
epic: "Epic 2: Core Trading Engine"
project: "Solana Trading Bot"
created: 2026-07-02
status: "ready-for-dev"
priority: P0
dependencies: ["US-001", "US-002", "US-010", "US-011"]
estimate_hours: 3
type: "technical"
mvp: true
source_epic: "/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md"
source_architecture: "/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md"
---

# US-012: Domain Models - Trade & Decision

## 🎯 User Story

**As a** developer  
**I want** models for trades and trading decisions  
**So that** I can track and execute trading actions

## ✅ Acceptance Criteria

- [ ] `Trade` dataclass with all trade details
- [ ] `TradeStatus` enum (PENDING, SUCCESS, FAILED)
- [ ] `TradeType` enum (BUY, SELL, SWAP)
- [ ] `Decision` dataclass for trading decisions
- [ ] `Signal` enum (BUY, SELL, NEUTRAL)
- [ ] Proper type hints and docstrings

## 📋 Tasks

- [ ] Create `src/core/models/trade.py` module
- [ ] Implement `Trade` dataclass with trade details
- [ ] Implement `TradeStatus` enum (PENDING, SUCCESS, FAILED)
- [ ] Implement `TradeType` enum (BUY, SELL, SWAP)
- [ ] Implement `Decision` dataclass for trading decisions
- [ ] Implement `Signal` enum (BUY, SELL, NEUTRAL)
- [ ] Add type hints and docstrings following Google style
- [ ] Add unit tests for all models in `tests/unit/core/models/test_trade.py`

## 🏗️ Technical Implementation

### Domain Layer Alignment

This story implements **Core Domain Models** as defined in **AD-001: Clean Architecture Paradigm** and detailed in **ARCHITECTURE-SPINE.md §1171**. 

**Architecture Rule:** Domain entities MUST be framework-agnostic and testable without external services.

**Dependencies on Previous Stories:**
- US-010 (Price & Market Data) - Uses Price, Token, TokenPair models
- US-011 (Balance & Portfolio) - Decision.model will reference Portfolio for state

### Module Structure

```
src/core/models/trade.py
├── Enums
│   ├── TradeStatus      # PENDING, SUCCESS, FAILED
│   ├── TradeType        # BUY, SELL, SWAP
│   └── Signal           # BUY, SELL, NEUTRAL
└── Dataclasses
    ├── Trade             # Trade execution details
    └── Decision          # Trading decision with signal and confidence
```

### Class Specifications

#### TradeStatus Enum
```python
from enum import Enum, auto

class TradeStatus(Enum):
    """Status of a trade execution."""
    PENDING = auto()   # Trade has been submitted but not yet executed
    SUCCESS = auto()   # Trade executed successfully
    FAILED = auto()    # Trade execution failed
```

#### TradeType Enum
```python
class TradeType(Enum):
    """Type of trade action."""
    BUY = auto()      # Buy operation (add to portfolio)
    SELL = auto()     # Sell operation (remove from portfolio)
    SWAP = auto()     # Swap between two tokens
```

#### Signal Enum
```python
class Signal(Enum):
    """Trading signal for decisions."""
    BUY = auto()      # Strong buy signal
    SELL = auto()     # Strong sell signal
    NEUTRAL = auto()  # No strong signal, hold position
```

#### Trade Dataclass
```python
@dataclass(frozen=True)
class Trade:
    """Immutable representation of a trade execution.
    
    Contains all details needed to execute and track a trade.
    """
    trade_id: str                      # Unique identifier for the trade
    token_pair: TokenPair              # Trading pair (from US-010)
    amount: float                      # Amount to trade (in base token units)
    trade_type: TradeType              # BUY, SELL, or SWAP
    price: Price                       # Execution price (from US-010)
    timestamp: datetime                # When the trade was created
    status: TradeStatus = TradeStatus.PENDING
    fees: float = 0.0                  # Transaction fees paid
    slippage: float = 0.0              # Price slippage percentage
    notes: str = ""                    # Additional notes/metadata
    
    @property
    def base_amount(self) -> float: ...      # Amount in base token
    
    @property
    def quote_amount(self) -> float: ...     # Amount in quote token (amount * price)
    
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Trade": ...
```

**Trade Fields Explanation:**
- `trade_id`: UUID or unique string identifier for tracking
- `token_pair`: The trading pair (e.g., SOL/USDC)
- `amount`: Quantity to trade (positive for BUY, negative for SELL)
- `trade_type`: Enum indicating operation type
- `price`: The price at which the trade was/will be executed
- `timestamp`: When the trade was initiated
- `status`: Current status of the trade
- `fees`: Transaction fees (in quote token)
- `slippage`: Percentage of price slippage from expected

**Note on amount sign:**
- For BUY trades: amount is positive (adding to portfolio)
- For SELL trades: amount is negative (removing from portfolio)
- For SWAP trades: amount is positive (swapping base for quote)

#### Decision Dataclass
```python
@dataclass(frozen=True)
class Decision:
    """Immutable representation of a trading decision.
    
    Represents the result of a trading strategy's analysis.
    Contains the signal, confidence level, and related market data.
    """
    decision_id: str                   # Unique identifier
    token_pair: TokenPair              # Trading pair (from US-010)
    signal: Signal                     # Trading signal (BUY, SELL, NEUTRAL)
    confidence: float                  # Confidence level (0.0 to 1.0)
    timestamp: datetime                # When decision was made
    reasoning: str = ""                # Human-readable reasoning
    indicators: Dict[str, Any] = field(default_factory=dict)  # Indicator values
    portfolio_snapshot: Optional["Portfolio"] = None  # Portfolio state at decision time
    
    @property
    def is_actionable(self) -> bool: ...     # True if signal is BUY or SELL
    
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Decision": ...
```

**Decision Fields Explanation:**
- `decision_id`: UUID or unique string identifier
- `token_pair`: The trading pair this decision pertains to
- `signal`: The trading signal (BUY, SELL, NEUTRAL)
- `confidence`: How confident the strategy is (0.0 = no confidence, 1.0 = certain)
- `timestamp`: When the decision was generated
- `reasoning`: Human-readable explanation of the decision
- `indicators`: Dictionary of indicator values that led to this decision
- `portfolio_snapshot`: Optional snapshot of portfolio state at decision time

### File Structure Requirements

- **Location:** `src/core/models/trade.py`
- **Module:** Part of `core.models` package
- **Exports:** All classes/enums must be exported in `src/core/models/__init__.py`
- **Imports:** Use Token, TokenPair, Price from `src.core.models.price` (US-010)
- **Forward references:** Use TYPE_CHECKING for Portfolio (US-011) to avoid circular imports

## 🔬 Dev Notes

### Architecture Compliance

- ✅ **AD-001 (Clean Architecture):** These are Domain Layer entities - pure business logic, no external dependencies
- ✅ **AD-004 (Dependency Injection):** All classes accept dependencies via constructor parameters
- ✅ **AD-001 Rule:** Domain entities are framework-agnostic and testable without external services

### Design Decisions

1. **Immutability (frozen=True):** All dataclasses are immutable to ensure thread-safety
2. **Enums for discrete values:** TradeStatus, TradeType, Signal use enums for type safety
3. **Forward references:** Decision references Portfolio from US-011 using Optional type hint
4. **Comprehensive trade details:** Trade captures all execution-related information
5. **Confidence level:** Decision includes confidence (0.0-1.0) for risk management

### Dependencies Context

**Hard Dependencies (must be complete):**
- US-001 (Project Structure Setup) - Ensures `src/core/models/` directory exists
- US-002 (Environment Configuration) - Provides configuration patterns
- US-010 (Domain Models - Price & Market Data) - **CRITICAL:** Price, Token, TokenPair models required
- US-011 (Domain Models - Balance & Portfolio) - **CRITICAL:** Portfolio model for Decision

**Blocks:**
- US-013 (Price Fetcher Service) - Depends on Trade and Decision models
- US-014 (Balance Tracker Service) - Depends on Trade model
- US-015 (Trade Executor Service) - Depends on Trade model
- US-017 (Main Trading Loop) - Depends on all trade/decision models
- US-030 (Decision Engine) - Depends on Decision model
- US-031 (Strategy Framework) - Depends on Decision model

### Previous Story Intelligence (US-010, US-011)

**Patterns to follow from US-010:**
- Use `frozen=True` for all domain dataclasses
- Implement `to_dict()` and `from_dict()` for serialization
- Use Google-style docstrings for all classes and methods
- Place classes in `src/core/models/` directory
- Export classes in `__init__.py`

**Patterns to follow from US-011:**
- Use forward references with TYPE_CHECKING for circular dependencies
- Add convenience methods (properties, class methods)
- Test edge cases (enum values, optional fields)

**Learnings applied:**
- Enum usage for discrete value sets
- Optional fields with defaults for flexibility
- Comprehensive serialization support
- Immutability throughout

### References

- [Source: EPICS-AND-STORIES.md §318-343](/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md#us-012-domain-models---trade--decision)
- [Architecture: ARCHITECTURE-SPINE.md §1171-1181](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#core-domain-models-coremodels)
- [Dependency: US-010 Domain Models - Price & Market Data](/_bmad-output/implementation-artifacts/stories/2-010-domain-models-price-market-data.md)
- [Dependency: US-011 Domain Models - Balance & Portfolio](/_bmad-output/implementation-artifacts/stories/2-011-domain-models-balance-portfolio.md)
- [Architecture Decision: AD-001 Clean Architecture Paradigm](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-001-clean-architecture-paradigm)
- [Architecture Decision: AD-004 Dependency Injection Pattern](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-004-dependency-injection-pattern)

## 🧪 Testing Requirements

### Test File Location
- `tests/unit/core/models/test_trade.py`

### Test Cases

#### TradeStatus Enum Tests
- [ ] Test all enum values are accessible
- [ ] Test enum comparison
- [ ] Test enum iteration

#### TradeType Enum Tests
- [ ] Test all enum values are accessible
- [ ] Test enum comparison
- [ ] Test enum iteration

#### Signal Enum Tests
- [ ] Test all enum values are accessible
- [ ] Test enum comparison
- [ ] Test enum iteration

#### Trade Dataclass Tests
- [ ] Test Trade instantiation with all fields
- [ ] Test Trade with default values (PENDING status, 0 fees, 0 slippage)
- [ ] Test Trade with all optional fields
- [ ] Test Trade.base_amount property
- [ ] Test Trade.quote_amount property
- [ ] Test Trade immutability
- [ ] Test Trade.to_dict() returns correct structure
- [ ] Test Trade.from_dict() creates valid instance
- [ ] Test Trade serialization round-trip
- [ ] Test Trade equality

#### Decision Dataclass Tests
- [ ] Test Decision instantiation with all fields
- [ ] Test Decision with default values (empty reasoning, indicators, portfolio_snapshot)
- [ ] Test Decision.is_actionable property (True for BUY/SELL, False for NEUTRAL)
- [ ] Test Decision immutability
- [ ] Test Decision.to_dict() returns correct structure
- [ ] Test Decision.from_dict() creates valid instance
- [ ] Test Decision serialization round-trip
- [ ] Test Decision equality

## 📁 File Changes Required

**NEW Files:**
- `src/core/models/trade.py` - Main implementation
- `tests/unit/core/models/test_trade.py` - Unit tests

**MODIFIED Files:**
- `src/core/models/__init__.py` - Export new classes/enums (Trade, Decision, TradeStatus, TradeType, Signal)

## 🤖 Dev Agent Record

### Agent Model Used
- Mistral Vibe CLI (mistral-medium-3.5)

### Debug Log References
- [Inception] User request: "create the next story"
- [Analysis] Extracted US-012 from EPICS-AND-STORIES.md §318
- [Architecture] Validated against ARCHITECTURE-SPINE.md §1171
- [Dependency] Verified US-010 and US-011 are complete

### Completion Notes List
- Story file created with comprehensive context
- All acceptance criteria mapped from source document
- Architecture compliance verified
- Dependencies cross-referenced (US-001, US-002, US-010, US-011)
- Technical specifications aligned with clean architecture principles
- Previous story patterns applied (US-010, US-011)

### File List
- Created: `_bmad-output/implementation-artifacts/stories/2-012-domain-models-trade-decision.md`
- Next: `src/core/models/trade.py` (to be created by dev-story)
- Next: `tests/unit/core/models/test_trade.py` (to be created by dev-story)

---
*Generated by BMad Method - Create Story Workflow*
*Story Context Engine: Comprehensive analysis for flawless implementation*
