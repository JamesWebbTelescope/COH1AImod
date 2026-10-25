"""
Unit Tests for Configuration Module

Tests the configuration management system for the CoH1 AI mod.
"""

import json
import tempfile
import os
from pathlib import Path
import pytest

# Add parent directory to Python path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from config import (
    COH1AI_DATA_DIR,
    Configuration,
    get_config,
    load_config,
    resolve_data_dir,
    save_config,
    reset_config,
)


class TestConfigurationBasics:
    """Test basic configuration functionality."""
    
    def test_default_configuration_exists(self):
        """Test that default configuration is not empty."""
        config = Configuration()
        assert config is not None
        assert config._config is not None
        assert len(config._config) > 0

    def test_configuration_instances_do_not_share_nested_defaults(self):
        first = Configuration()
        second = Configuration()

        first._config["ipc"]["data_dir"] = "custom_data"

        assert second._config["ipc"]["data_dir"] == "coh1ai_data"

    def test_default_data_paths_resolve_from_game_install(self):
        game_dir = Path(__file__).resolve().parents[4]
        data_dir = resolve_data_dir("coh1ai_data")

        assert data_dir == game_dir / "coh1ai_data"
        assert data_dir == COH1AI_DATA_DIR
        assert Configuration()._get_default_config_path() == data_dir / "config.json"

    def test_coh1ai_data_cannot_resolve_outside_game_install(self, tmp_path):
        with pytest.raises(ValueError, match="coh1ai_data must be located"):
            resolve_data_dir(tmp_path / "coh1ai_data")

        with pytest.raises(ValueError, match="Relative data directories"):
            resolve_data_dir(Path("..") / "Mods" / "COh1AIMod")
    
    def test_get_configuration_values(self):
        """Test getting configuration values."""
        config = Configuration()
        
        # Test various configuration paths
        assert config.get("mod", "version") is not None
        assert config.get("mod", "name") is not None
        assert config.get("mistral", "api_url") is not None
        assert config.get("game", "faction") is not None
        assert config.get("game", "difficulty") is not None
    
    def test_get_nonexistent_key(self):
        """Test getting non-existent configuration keys."""
        config = Configuration()
        
        # Non-existent keys should return None or default
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", default="default_value") == "default_value"
        assert config.get("level1", "level2", "level3") is None
        assert config.get("level1", "level2", "level3", default="default") == "default"
    
    def test_set_configuration_values(self):
        """Test setting configuration values."""
        config = Configuration()
        
        # Test setting simple value
        assert config.set("test", "simple", 42)
        assert config.get("test", "simple") == 42
        
        # Test setting nested value
        assert config.set("test", "nested", "value")
        assert config.get("test", "nested") == "value"
        
        # Test setting value in existing path
        assert config.set("mod", "test_key", "test_value")
        assert config.get("mod", "test_key") == "test_value"
    
    def test_set_invalid_path(self):
        """Test setting values with invalid paths."""
        config = Configuration()
        
        # Empty path should fail
        assert not config.set("test_value")


class TestConfigurationLoading:
    """Test configuration file loading and saving."""
    
    def test_save_and_load_configuration(self):
        """Test saving and loading configuration from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            
            # Create and configure
            config = Configuration()
            config.set("test", "custom_value", "saved_test")
            
            # Save
            assert config.save(str(config_path))
            assert config_path.exists()
            
            # Verify file content
            with open(config_path, 'r') as f:
                content = f.read()
                assert "saved_test" in content
                assert "custom_value" in content
            
            # Create new config and load
            new_config = Configuration()
            assert new_config.load(str(config_path))
            assert new_config.get("test", "custom_value") == "saved_test"
    
    def test_load_nonexistent_file(self):
        """Test loading from non-existent file."""
        config = Configuration()
        assert not config.load("/nonexistent/path/config.json")
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "invalid.json"
            
            # Write invalid JSON
            with open(config_path, 'w') as f:
                f.write("{invalid json}")
            
            config = Configuration()
            assert not config.load(str(config_path))
    
    def test_configuration_merge(self):
        """Test that loading partial config merges with defaults."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "partial.json"
            
            # Write partial config
            partial_config = {
                "mod": {"version": "9.9.9"},
                "mistral": {"model": "custom-model"}
            }
            
            with open(config_path, 'w') as f:
                json.dump(partial_config, f)
            
            config = Configuration()
            assert config.load(str(config_path))
            
            # Merged values should be from file
            assert config.get("mod", "version") == "9.9.9"
            assert config.get("mistral", "model") == "custom-model"
            
            # Default values should still exist
            assert config.get("mistral", "api_url") is not None
            assert config.get("game", "faction") is not None


class TestConfigurationValidation:
    """Test configuration validation."""
    
    def test_validate_default_configuration(self):
        """Test that default configuration is valid."""
        config = Configuration()
        assert config.validate()
    
    def test_validate_modified_configuration(self):
        """Test validation of modified configuration."""
        config = Configuration()
        
        # Set valid values
        config.set("game", "faction", "axis")
        config.set("game", "difficulty", "hard")
        
        assert config.validate()
    
    def test_validate_invalid_faction(self):
        """Test validation with invalid faction."""
        config = Configuration()
        config.set("game", "faction", "invalid_faction")
        
        assert not config.validate()
    
    def test_validate_invalid_difficulty(self):
        """Test validation with invalid difficulty."""
        config = Configuration()
        config.set("game", "difficulty", "invalid_difficulty")
        
        assert not config.validate()


class TestConfigurationToDict:
    """Test configuration to dictionary conversion."""
    
    def test_to_dict_returns_copy(self):
        """Test that to_dict returns a copy."""
        config = Configuration()
        config_dict = config.to_dict()
        
        # Modify the returned dict
        config_dict["test"] = "value"
        
        # Original should be unchanged
        assert config.get("test") is None
    
    def test_to_dict_contains_expected_keys(self):
        """Test that to_dict contains expected configuration keys."""
        config = Configuration()
        config_dict = config.to_dict()
        
        assert "mod" in config_dict
        assert "ipc" in config_dict
        assert "game" in config_dict
        assert "mistral" in config_dict
        assert "reflex" in config_dict
        assert "safety" in config_dict
        assert "debug" in config_dict


class TestGlobalConfiguration:
    """Test global configuration functions."""
    
    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        # Reset first
        reset_config()
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_reset_config(self):
        """Test resetting global configuration."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        # Should be different instances after reset
        assert config1 is not config2
    
    def test_load_config(self):
        """Test load_config convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.json"
            
            # Create a valid config file
            valid_config = {
                "mod": {"version": "1.0.0"},
                "game": {"faction": "axis"}
            }
            
            with open(config_path, 'w') as f:
                json.dump(valid_config, f)
            
            # Load config
            config = load_config(str(config_path))
            assert config.get("mod", "version") == "1.0.0"
            assert config.get("game", "faction") == "axis"
    
    def test_save_config(self):
        """Test save_config convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_save.json"
            
            # Get config and modify
            config = get_config()
            config.set("test", "save_test", "value")
            
            # Save
            assert save_config(str(config_path))
            assert config_path.exists()


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
