"""
Configuration loader utility for MarketMan.

This module provides a centralized way to load and manage all configuration
files including settings, strategies, and broker configurations.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Centralized configuration loader for MarketMan."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self._settings: Optional[Dict[str, Any]] = None
        self._strategies: Optional[Dict[str, Any]] = None
        self._brokers: Optional[Dict[str, Any]] = None
        
    def load_settings(self) -> Dict[str, Any]:
        """
        Load main settings configuration.
        
        Returns:
            Dictionary containing all settings
        """
        if self._settings is None:
            settings_path = self.config_dir / "settings.yaml"
            self._settings = self._load_yaml(settings_path)
        return self._settings
    
    def load_strategies(self) -> Dict[str, Any]:
        """
        Load strategy configuration.
        
        Returns:
            Dictionary containing all strategy configurations
        """
        if self._strategies is None:
            strategies_path = self.config_dir / "strategies.yaml"
            self._strategies = self._load_yaml(strategies_path)
        return self._strategies
    
    def load_brokers(self) -> Dict[str, Any]:
        """
        Load broker configuration.
        
        Returns:
            Dictionary containing all broker configurations
        """
        if self._brokers is None:
            brokers_path = self.config_dir / "brokers.yaml"
            self._brokers = self._load_yaml(brokers_path)
        return self._brokers
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Get a specific setting value using dot notation.
        
        Args:
            key_path: Dot-separated path to the setting (e.g., "app.debug")
            default: Default value if setting not found
            
        Returns:
            The setting value or default
        """
        settings = self.load_settings()
        keys = key_path.split('.')
        value = settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            logger.warning(f"Setting '{key_path}' not found, using default: {default}")
            return default
    
    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Strategy configuration dictionary
        """
        strategies = self.load_strategies()
        return strategies.get(strategy_name, {})
    
    def get_broker_config(self, broker_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific broker.
        
        Args:
            broker_name: Name of the broker
            
        Returns:
            Broker configuration dictionary
        """
        brokers = self.load_brokers()
        return brokers.get(broker_name, {})
    
    def is_feature_enabled(self, feature_path: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_path: Dot-separated path to the feature (e.g., "options.scalping_enabled")
            
        Returns:
            True if feature is enabled, False otherwise
        """
        return self.get_setting(feature_path, False)
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """
        Load a YAML configuration file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Dictionary containing the YAML data
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the YAML file is malformed
        """
        if not file_path.exists():
            logger.error(f"Configuration file not found: {file_path}")
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info(f"Loaded configuration from {file_path}")
                return config or {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration file {file_path}: {e}")
            raise
    
    def reload_configs(self) -> None:
        """Reload all configuration files from disk."""
        self._settings = None
        self._strategies = None
        self._brokers = None
        logger.info("Configuration files reloaded")


# Global configuration loader instance
config_loader = ConfigLoader()


def get_config() -> ConfigLoader:
    """
    Get the global configuration loader instance.
    
    Returns:
        Global ConfigLoader instance
    """
    return config_loader


def get_setting(key_path: str, default: Any = None) -> Any:
    """
    Convenience function to get a setting value.
    
    Args:
        key_path: Dot-separated path to the setting
        default: Default value if setting not found
        
    Returns:
        The setting value or default
    """
    return config_loader.get_setting(key_path, default)


def is_feature_enabled(feature_path: str) -> bool:
    """
    Convenience function to check if a feature is enabled.
    
    Args:
        feature_path: Dot-separated path to the feature
        
    Returns:
        True if feature is enabled, False otherwise
    """
    return config_loader.is_feature_enabled(feature_path) 