---
title: "US-002: Environment Configuration"
story_id: "1-002-environment-configuration"
epic: "Epic 1: Project Setup & Infrastructure"
project: "Solana Trading Bot"
created: 2026-07-02
status: "ready-for-dev"
priority: P0
dependencies: ["US-001"]
estimate_hours: 2
type: "technical"
---

# US-002: Environment Configuration

## 🎯 User Story

**As a** developer  
**I want** to configure the bot via environment variables and YAML files  
**So that** I can easily switch between different configurations

## ✅ Acceptance Criteria

- [x] `.env.example` with all required variables
- [x] `.env` (gitignored) for local development
- [x] Configuration loading from environment variables
- [x] YAML configuration files for strategies and indicators
- [x] Configuration validation using Pydantic
- [x] Devnet-only validation at startup

## 📋 Tasks

- [x] Create `.env.example` with comprehensive documentation
- [x] Create configuration dataclasses with Pydantic
- [x] Implement YAML loading from config/ directory
- [x] Implement Pydantic validation for all settings
- [x] Add Devnet validation to prevent accidental mainnet usage
- [x] Create `config/` directory with default configs
- [x] Create environment-specific configs (dev, test, prod)

## 🏗️ Technical Implementation

### Configuration Structure

```
config/
├── main.yaml           # Default configuration
├── trading.yaml       # Trading-specific settings
├── indicators.yaml    # Technical indicator configs
├── strategies.yaml    # Trading strategy configs
├── risk_management.yaml # Risk management settings
├── dev/
│   └── main.yaml      # Dev environment overrides
├── test/
│   └── main.yaml      # Test environment overrides
└── prod/
    └── main.yaml      # Production environment overrides
```

### Settings Classes

- `SolanaSettings`: RPC URL, network, wallet configuration
- `JupiterSettings`: API key, API URL
- `TradingSettings`: Interval, swap amount, risk settings
- `RiskManagementSettings`: Stop loss, take profit, position sizing
- `LoggingSettings`: Log level, format
- `DatabaseSettings`: DB type, path
- `MonitoringSettings`: Metrics enabled, port
- `Settings`: Main class combining all settings

### Pydantic Features Used

- `BaseSettings`: Automatic environment variable loading
- `Field`: Type hints, validation, defaults
- `validator`: Custom validation logic
- `SecretStr`: Secure handling of sensitive values
- Type validation: int, float, str, List, Optional

### Devnet Validation

- At startup, `validate_devnet_configuration()` checks:
  - If NETWORK=devnet, RPC URL must contain "devnet" or "localhost"
  - Prevents accidental mainnet usage during development

## 📁 File Changes Required

1. `.env.example` - Updated with all required variables
2. `src/config/__init__.py` - Config package
3. `src/config/settings.py` - Pydantic settings classes
4. `src/config/config_loader.py` - YAML configuration loader
5. `config/main.yaml` - Default configuration
6. `config/trading.yaml` - Trading configuration
7. `config/indicators.yaml` - Indicator configurations
8. `config/strategies.yaml` - Strategy configurations
9. `config/risk_management.yaml` - Risk management settings
10. `config/dev/main.yaml` - Dev environment overrides
11. `config/test/main.yaml` - Test environment overrides
12. `config/prod/main.yaml` - Production environment overrides

## 🧪 Testing Strategy

### Validation Test
```python
from src.config.settings import settings, validate_devnet_configuration

# Should load from .env or defaults
assert settings.solana_rpc_url == "https://api.devnet.solana.com"
assert settings.network == "devnet"

# Should validate Devnet configuration
validate_devnet_configuration()  # Should not raise
```

### YAML Loading Test
```python
from src.config.config_loader import load_config, get_setting

config = load_config()
assert config["trading"]["interval"] == 60

# Get specific setting
assert get_setting("trading.interval") == 60
```

### Pydantic Validation Test
```python
from src.config.settings import Settings
from pydantic import ValidationError

# Invalid network should raise
try:
    Settings(network="invalid")
    assert False, "Should have raised ValidationError"
except ValidationError:
    pass  # Expected
```

## 📊 Success Metrics

- All environment variables have sensible defaults
- YAML configuration files are valid and loadable
- Pydantic validation catches invalid values
- Devnet validation prevents accidental mainnet usage
- Configuration can be loaded from multiple sources
- Environment-specific overrides work correctly

## ⚡ Dependencies

- US-001: Project Structure Setup (must have `src/config/` directory)

## 📝 Notes

- Configuration follows 12-factor app principles
- Sensitive values use `SecretStr` for security
- YAML files allow for complex nested configurations
- Environment variables can override YAML settings
- Devnet validation is critical for preventing costly mistakes

---
*Generated for BMad workflow - Solana Trading Bot Project*