"""
Configuration Loader

Load configuration from YAML files and environment variables.
Supports multiple configuration profiles (dev, test, prod).
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache

from .settings import Settings, settings, validate_devnet_configuration


# Default configuration directory
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


class ConfigLoader:
    """Load and merge configuration from multiple sources."""
    
    def __init__(self, env: str = None):
        """
        Initialize config loader.
        
        Args:
            env: Environment name (dev, test, prod). Defaults to NETWORK from settings.
        """
        self.env = env or getattr(settings, 'network', 'dev')
        self._loaded_configs: Dict[str, Dict[str, Any]] = {}
    
    def load_yaml(self, config_name: str) -> Dict[str, Any]:
        """
        Load a YAML configuration file.
        
        Args:
            config_name: Name of the config file (without extension)
            
        Returns:
            Dictionary with configuration values
        """
        # Try different paths
        possible_paths = [
            CONFIG_DIR / f"{config_name}.yaml",
            CONFIG_DIR / f"{config_name}_{self.env}.yaml",
            CONFIG_DIR / self.env / f"{config_name}.yaml",
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        return yaml.safe_load(f) or {}
                except Exception as e:
                    logging.warning(f"Failed to load config {path}: {e}")
                    continue
        
        return {}
    
    def load_all(self) -> Dict[str, Any]:
        """
        Load all configuration files and merge with environment variables.
        
        Returns:
            Merged configuration dictionary
        """
        merged_config = {}
        
        # Load from YAML files
        config_files = [
            "main",           # Main configuration
            "trading",       # Trading-specific config
            "indicators",    # Indicator configurations
            "strategies",     # Strategy configurations
            "risk_management", # Risk management settings
        ]
        
        for config_name in config_files:
            config = self.load_yaml(config_name)
            if config:
                merged_config = self._deep_merge(merged_config, config)
                self._loaded_configs[config_name] = config
        
        return merged_config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Dot-separated key path (e.g., "trading.interval")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        full_config = self.load_all()
        
        keys = key.split('.')
        value = full_config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value


@lru_cache()
def get_config_loader(env: str = None) -> ConfigLoader:
    """
    Get a cached config loader instance.
    
    Args:
        env: Environment name
        
    Returns:
        ConfigLoader instance
    """
    return ConfigLoader(env)


def load_config(env: str = None) -> Dict[str, Any]:
    """
    Convenience function to load all configuration.
    
    Args:
        env: Environment name
        
    Returns:
        Merged configuration dictionary
    """
    loader = get_config_loader(env)
    return loader.load_all()


def get_setting(key: str, default: Any = None, env: str = None) -> Any:
    """
    Get a specific setting value.
    
    Args:
        key: Dot-separated key path
        default: Default value
        env: Environment name
        
    Returns:
        Setting value
    """
    loader = get_config_loader(env)
    return loader.get(key, default)


# Initialize configuration at import time
# This will load settings from environment variables
# Call validate_devnet_configuration() at application startup
