---
title: "US-011: Domain Models - Balance & Portfolio"
story_id: "2-011-domain-models-balance-portfolio"
epic: "Epic 2: Core Trading Engine"
project: "Solana Trading Bot"
created: 2026-07-02
status: "ready-for-dev"
priority: P0
dependencies: ["US-001", "US-002", "US-010"]
estimate_hours: 4
type: "technical"
mvp: true
source_epic: "/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md"
source_architecture: "/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md"
---

# US-011: Domain Models - Balance & Portfolio

## 🎯 User Story

**As a** developer  
**I want** immutable models for balances and portfolio  
**So that** I can track the bot's financial state accurately

## ✅ Acceptance Criteria

- [ ] `Balance` dataclass for token balances
- [ ] `Portfolio` dataclass with SOL and token balances
- [ ] Methods: `total_value()`, `get_balance(token)`, `apply_trade(trade)`
- [ ] Immutable updates (return new instance)
- [ ] Proper type hints and comprehensive docstrings

## 📋 Tasks

- [ ] Create `src/core/models/balance.py` module
- [ ] Implement `Balance` dataclass for individual token balance
- [ ] Implement `Portfolio` dataclass for complete portfolio state
- [ ] Implement `total_value()` method for portfolio valuation
- [ ] Implement `get_balance(token)` method for specific token lookup
- [ ] Implement `apply_trade(trade)` method for portfolio updates (immutable)
- [ ] Add type hints and docstrings following Google style
- [ ] Add unit tests for all dataclasses in `tests/unit/core/models/test_balance.py`

## 🏗️ Technical Implementation

### Domain Layer Alignment

This story implements **Core Domain Models** as defined in **AD-001: Clean Architecture Paradigm** and detailed in **ARCHITECTURE-SPINE.md §1171**. 

**Architecture Rule:** Domain entities MUST be framework-agnostic and testable without external services.

**Dependency on US-010:** This story depends on the Price and Token models from US-010, which must be imported and used for type consistency.

### Module Structure

```
src/core/models/balance.py
├── Balance         # Individual token balance with amount and token info
└── Portfolio       # Complete portfolio with multiple balances
```

### Class Specifications

#### Balance Dataclass
```python
@dataclass(frozen=True)
class Balance:
    """Immutable representation of a token balance.
    
    Represents the amount of a specific token held by the portfolio.
    """
    token: Token      # Token metadata (from US-010)
    amount: float     # Balance amount in token's base units (not lamports)
    
    @property
    def amount_in_lamports(self) -> int: ...  # Amount converted to lamports
    
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Balance": ...
```

**Note:** The amount is stored in the token's base units (e.g., SOL for SOL, USDC for USDC), not in lamports. This provides a cleaner API. The `amount_in_lamports` property can be used when lamport-level precision is needed.

#### Portfolio Dataclass
```python
@dataclass(frozen=True)
class Portfolio:
    """Immutable representation of the complete trading bot portfolio.
    
    Contains all token balances and provides methods for portfolio operations.
    All update operations return new Portfolio instances (immutability).
    """
    balances: Dict[str, Balance]  # Key: token symbol (e.g., "SOL", "USDC")
    
    def total_value(self, price_map: Dict[str, Price]) -> float: ...
    # Calculate total portfolio value in USD using provided price map
    
    def get_balance(self, token_symbol: str) -> Optional[Balance]: ...
    # Get balance for specific token, returns None if not found
    
    def apply_trade(self, trade: "Trade") -> "Portfolio": ...
    # Apply trade to portfolio, return new Portfolio instance
    # Note: Trade type from US-012 (forward reference acceptable)
    
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio": ...
```

**Immutability Note:** The `apply_trade` method returns a **new** Portfolio instance rather than modifying the existing one. This ensures thread-safety and prevents accidental state mutations.

### File Structure Requirements

- **Location:** `src/core/models/balance.py` (as referenced in architecture)
- **Module:** Part of `core.models` package
- **Exports:** All classes must be exported in `src/core/models/__init__.py`
- **Imports:** Use Token from `src.core.models.price` (US-010 dependency)

## 🔬 Dev Notes

### Architecture Compliance

- ✅ **AD-001 (Clean Architecture):** These are Domain Layer entities - pure business logic, no external dependencies
- ✅ **AD-004 (Dependency Injection):** All classes accept dependencies via constructor parameters
- ✅ **AD-001 Rule:** Domain entities are framework-agnostic and testable without external services

### Design Decisions

1. **Immutability (frozen=True):** All dataclasses are immutable to ensure thread-safety and prevent accidental mutations
2. **Symbol-based lookup:** Portfolio uses token symbols (strings) as dictionary keys for easy lookup
3. **Base units storage:** Balances are stored in token base units (not lamports) for cleaner API
4. **Functional updates:** All modification methods return new instances (functional programming pattern)
5. **Price dependency:** total_value() requires a price_map parameter rather than having internal price fetching (keeps domain layer pure)

### Dependencies Context

**Hard Dependencies (must be complete):**
- US-001 (Project Structure Setup) - Ensures `src/core/models/` directory exists
- US-002 (Environment Configuration) - Provides configuration patterns
- US-010 (Domain Models - Price & Market Data) - **CRITICAL:** Token, Price models required for type hints

**Blocks:**
- US-012 (Domain Models - Trade & Decision) - Depends on Portfolio for trade application
- US-013 (Price Fetcher Service) - Indirect dependency through portfolio valuation
- US-014 (Balance Tracker Service) - Depends on Portfolio and Balance models

### Previous Story Intelligence (US-010)

**Learnings from US-010 that apply to this story:**
- Use `frozen=True` for all domain dataclasses
- Implement `to_dict()` and `from_dict()` for serialization
- Use Google-style docstrings for all classes and methods
- Place classes in `src/core/models/` directory
- Export classes in `__init__.py`
- Create comprehensive unit tests (10+ per class)
- Test immutability, serialization, equality

**Patterns to follow:**
- Module structure: One class per logical section with clear separation
- Type hints: Use forward references for circular dependencies (e.g., `"Trade"`)
- Testing: Test edge cases (zero balances, negative values, missing tokens)

### References

- [Source: EPICS-AND-STORIES.md §292-314](/_bmad-output/planning-artifacts/epics-and-stories-2026-06-30/EPICS-AND-STORIES.md#us-011-domain-models---balance--portfolio)
- [Architecture: ARCHITECTURE-SPINE.md §1171-1181](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#core-domain-models-coremodels)
- [Dependency: US-010 Domain Models - Price & Market Data](/_bmad-output/implementation-artifacts/stories/2-010-domain-models-price-market-data.md)
- [Architecture Decision: AD-001 Clean Architecture Paradigm](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-001-clean-architecture-paradigm)
- [Architecture Decision: AD-004 Dependency Injection Pattern](/_bmad-output/planning-artifacts/architecture-trading-bot-2026-06-30/ARCHITECTURE-SPINE.md#ad-004-dependency-injection-pattern)

## 🧪 Testing Requirements

### Test File Location
- `tests/unit/core/models/test_balance.py`

### Test Cases

#### Balance Tests
- [ ] Test Balance instantiation with valid Token and amount
- [ ] Test Balance with zero amount
- [ ] Test Balance with negative amount (short positions)
- [ ] Test Balance.amount_in_lamports property for SOL (9 decimals)
- [ ] Test Balance.amount_in_lamports property for USDC (6 decimals)
- [ ] Test Balance immutability
- [ ] Test Balance.to_dict() returns correct structure
- [ ] Test Balance.from_dict() creates valid instance
- [ ] Test Balance serialization round-trip
- [ ] Test Balance equality

#### Portfolio Tests
- [ ] Test Portfolio instantiation with empty balances
- [ ] Test Portfolio instantiation with multiple balances
- [ ] Test Portfolio.get_balance() returns correct Balance
- [ ] Test Portfolio.get_balance() returns None for missing token
- [ ] Test Portfolio.total_value() with empty portfolio
- [ ] Test Portfolio.total_value() with single token (using price_map)
- [ ] Test Portfolio.total_value() with multiple tokens (using price_map)
- [ ] Test Portfolio.apply_trade() creates new Portfolio instance
- [ ] Test Portfolio.apply_trade() updates correct token balance
- [ ] Test Portfolio immutability
- [ ] Test Portfolio.to_dict() includes all balances
- [ ] Test Portfolio.from_dict() creates valid instance
- [ ] Test Portfolio serialization round-trip

## 📁 File Changes Required

**NEW Files:**
- `src/core/models/balance.py` - Main implementation
- `tests/unit/core/models/test_balance.py` - Unit tests

**MODIFIED Files:**
- `src/core/models/__init__.py` - Export new classes (Balance, Portfolio)

## 🤖 Dev Agent Record

### Agent Model Used
- Mistral Vibe CLI (mistral-medium-3.5)

### Debug Log References
- [Inception] User request: "bmad-create-story 2-011"
- [Analysis] Extracted US-011 from EPICS-AND-STORIES.md §292
- [Architecture] Validated against ARCHITECTURE-SPINE.md §1171
- [Dependency] Verified US-010 (Price & Market Data) is complete

### Completion Notes List
- Story file created with comprehensive context
- All acceptance criteria mapped from source document
- Architecture compliance verified
- Dependencies cross-referenced (US-001, US-002, US-010)
- Technical specifications aligned with clean architecture principles
- Previous story patterns applied (US-010)

### File List
- Created: `_bmad-output/implementation-artifacts/stories/2-011-domain-models-balance-portfolio.md`
- Next: `src/core/models/balance.py` (to be created by dev-story)
- Next: `tests/unit/core/models/test_balance.py` (to be created by dev-story)

---
*Generated by BMad Method - Create Story Workflow*
*Story Context Engine: Comprehensive analysis for flawless implementation*
