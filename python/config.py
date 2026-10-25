"""
CoH1 × Mistral AI Mod - Configuration Management

Handles all configuration for the mod, including:
- API settings
- Game settings
- IPC settings
- Debug settings
- Fallback settings

Author: Generated via planner skill
Version: 0.1.0
Date: 2026-10-04
"""

import json
import os
import logging
import copy
from typing import Optional, Dict, Any
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "mod": {
        "version": "0.1.0",
        "name": "CoH1 Mistral AI Mod"
    },
    "ipc": {
        "state_file": "coh1ai_state.json",
        "command_file": "coh1ai_commands.json",
        "lock_file": "coh1ai_lock.tmp",
        "poll_interval": 0.05,
        "max_retries": 3,
        "data_dir": "coh1ai_data"
    },
    "game": {
        "faction": "allies",
        "difficulty": "normal",
        "player_id": 1
    },
    "mistral": {
        "api_url": "https://api.mistral.ai/v1/chat/completions",
        "model": "mistral-small-latest",
        "max_calls_per_match": 200,
        "api_key": "",
        "temperature": 0.7,
        "max_tokens": 2048,
        "json_mode": True
    },
    "reflex": {
        "enabled": True,
        "retreat_health_threshold": 0.3,
        "critical_health_threshold": 0.15,
        "under_fire_duration": 2.0,
        "suppression_duration": 1.5,
        "build_queue_min": 1,
        "build_queue_max": 5,
        "update_interval": 0.2
    },
    "safety": {
        "check_resources": True,
        "check_population": True,
        "check_pathfinding": True,
        "check_legality": True,
        "min_resource_margin": 50,
        "min_population_margin": 5
    },
    "fallback": {
        "enabled": True,
        "to_stock_ai": True,
        "to_reflex_only": True,
        "to_heuristics": True,
        "api_timeout": 5.0,
        "api_error_limit": 3
    },
    "debug": {
        "enabled": True,
        "level": "INFO",
        "file_logging": True,
        "console_logging": True,
        "log_file": "coh1ai.log",
        "state_log_file": "states.jsonl",
        "command_log_file": "commands.jsonl",
        "error_log_file": "errors.log"
    },
    "testing": {
        "test_mode": False,
        "fake_game_data": False,
        "test_tick_interval": 0.1,
        "max_run_time": 300
    }
}


COH1_INSTALL_DIR = Path(__file__).resolve().parents[3]
COH1AI_DATA_DIR = COH1_INSTALL_DIR / "coh1ai_data"


def resolve_data_dir(config_data_dir: Path | str = "coh1ai_data") -> Path:
    """Resolve the shared SCAR/Python data directory under the CoH1 install."""
    data_dir = Path(config_data_dir)
    if data_dir.is_absolute():
        resolved_dir = data_dir.resolve()
        if data_dir.name.casefold() == "coh1ai_data" and resolved_dir != COH1AI_DATA_DIR:
            raise ValueError(f"coh1ai_data must be located at {COH1AI_DATA_DIR}")
        return resolved_dir

    resolved_dir = (COH1_INSTALL_DIR / data_dir).resolve()
    if data_dir.name.casefold() == "coh1ai_data" and resolved_dir != COH1AI_DATA_DIR:
        raise ValueError(f"coh1ai_data must be located at {COH1AI_DATA_DIR}")
    try:
        resolved_dir.relative_to(COH1_INSTALL_DIR)
    except ValueError as error:
        raise ValueError(
            f"Relative data directories must remain under {COH1_INSTALL_DIR}"
        ) from error
    return resolved_dir


class Configuration:
    """Main configuration class for the CoH1 AI mod."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Optional path to config file. If None, uses default path.
        """
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._config_path = config_path or self._get_default_config_path()
        self._logger = None
        
    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        return resolve_data_dir(self._config["ipc"]["data_dir"]) / "config.json"
    
    def load(self, path: Optional[str] = None) -> bool:
        """
        Load configuration from file.
        
        Args:
            path: Optional path to config file. Uses default if None.
            
        Returns:
            True if loaded successfully, False otherwise.
        """
        load_path = Path(path) if path else self._config_path
        
        try:
            if load_path.exists():
                with open(load_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
                self._logger_debug(f"Configuration loaded from {load_path}")
                return True
        except (json.JSONDecodeError, IOError) as e:
            self._logger_error(f"Failed to load configuration: {e}")
            return False
        
        return False
    
    def save(self, path: Optional[str] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            path: Optional path to save config file. Uses default if None.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        save_path = Path(path) if path else self._config_path
        
        try:
            # Ensure directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            self._logger_debug(f"Configuration saved to {save_path}")
            return True
        except (IOError, TypeError) as e:
            self._logger_error(f"Failed to save configuration: {e}")
            return False
    
    def _merge_config(self, file_config: Dict[str, Any]) -> None:
        """Merge file configuration with defaults."""
        def merge_recursive(default: Dict, file: Dict) -> Dict:
            result = default.copy()
            for key, value in file.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_recursive(result[key], value)
                else:
                    result[key] = value
            return result
        
        self._config = merge_recursive(self._config, file_config)
    
    def _resolve_data_dir(self, config_data_dir: Path) -> Path:
        """
        Resolve the data directory by checking multiple possible locations.
        
        SCAR writes to coh1ai_data/ relative to CoH1's base directory,
        while Python might run from the mod directory.
        
        Args:
            config_data_dir: The configured data directory path
            
        Returns:
            Path to the resolved data directory
        """
        return resolve_data_dir(config_data_dir)
    
    def get(self, *keys, default=None) -> Any:
        """
        Get a configuration value by key path.
        
        Args:
            *keys: Sequence of keys to traverse the config.
            default: Default value if key not found.
            
        Returns:
            The configuration value or default.
            
        Examples:
            config.get("mod", "version")  # Get nested value
            config.get("nonexistent", "default_value")  # Get with default
        """
        if not keys:
            return default
            
        value = self._config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, *keys_and_value) -> bool:
        """
        Set a configuration value by key path.
        
        Args:
            *keys_and_value: Sequence of keys to traverse the config,
                           followed by the value to set. The last argument is the value,
                           all previous arguments are keys.
            
        Returns:
            True if set successfully, False otherwise.
            
        Examples:
            config.set("mod", "version", "1.0.0")  # Sets _config["mod"]["version"] = "1.0.0"
            config.set("test", 42)  # Sets _config["test"] = 42
        """
        if len(keys_and_value) < 1:
            return False
        
        # The last argument is the value, everything before is the key path
        *keys, value = keys_and_value
        
        if not keys:
            return False
        
        current = self._config
        
        # Navigate to the parent of the final key
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        # Set the value at the final key
        current[keys[-1]] = value
        return True
    
    def _logger_debug(self, message: str) -> None:
        """Log debug message if debugging is enabled."""
        if self._logger:
            self._logger.debug(message)
    
    def _logger_error(self, message: str) -> None:
        """Log error message."""
        if self._logger:
            self._logger.error(message)
    
    def setup_logging(self) -> logging.Logger:
        """
        Set up logging based on configuration.
        
        Returns:
            Configured logger instance.
        """
        # Get debug config
        debug_config = self._config.get("debug", {})
        enabled = debug_config.get("enabled", True)
        level_str = debug_config.get("level", "INFO").upper()
        file_logging = debug_config.get("file_logging", True)
        console_logging = debug_config.get("console_logging", True)
        
        # Determine log level
        level = getattr(logging, level_str, logging.INFO)
        
        # Create logger
        logger = logging.getLogger("coh1ai")
        logger.setLevel(level if enabled else logging.CRITICAL)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add console handler if enabled
        if console_logging and enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # Add file handler if enabled
        if file_logging and enabled:
            data_dir = self._config["ipc"]["data_dir"]
            # Resolve the data directory to handle SCAR writing to CoH1 base vs Python in mod dir
            resolved_data_dir = self._resolve_data_dir(Path(data_dir))
            log_file = resolved_data_dir / debug_config.get("log_file", "coh1ai.log")
            
            try:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(level)
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except (IOError, OSError) as e:
                print(f"Warning: Could not set up file logging: {e}")
        
        self._logger = logger
        return logger
    
    def validate(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        errors = []
        
        # Check critical settings
        if not self.get("mistral", "api_url"):
            errors.append("Mistral API URL is not set")
        
        if not self.get("mistral", "model"):
            errors.append("Mistral model is not set")
        
        # Validate faction
        faction = self.get("game", "faction") or ""
        if faction.lower() not in ["allies", "axis"]:
            errors.append(f"Invalid faction: {faction}")
        
        # Validate difficulty
        difficulty = self.get("game", "difficulty") or ""
        valid_difficulties = ["easy", "normal", "hard", "expert"]
        if difficulty.lower() not in valid_difficulties:
            errors.append(f"Invalid difficulty: {difficulty}")
        
        # Log errors
        for error in errors:
            self._logger_error(error)
        
        return len(errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the configuration as a dictionary."""
        return self._config.copy()


# Global configuration instance
_config = None


def get_config() -> Configuration:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Configuration()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config
    _config = None


# Convenience functions
def load_config(path: Optional[str] = None) -> Configuration:
    """Load configuration from file."""
    config = get_config()
    if not config.load(path):
        # If loading fails, save default config
        config.save(path)
    config.setup_logging()
    return config


def save_config(path: Optional[str] = None) -> bool:
    """Save current configuration to file."""
    return get_config().save(path)


if __name__ == "__main__":
    # Test configuration
    config = load_config()
    print("Configuration loaded successfully!")
    print(f"API URL: {config.get('mistral', 'api_url')}")
    print(f"Model: {config.get('mistral', 'model')}")
    print(f"Faction: {config.get('game', 'faction')}")
    print(f"Difficulty: {config.get('game', 'difficulty')}")
