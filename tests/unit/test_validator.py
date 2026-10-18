"""
Unit tests for the Action Validator module.

Tests cover:
- Command whitelist validation
- Required field validation
- Type validation
- Position validation
- Custom validators
- Statistics tracking
- Error handling

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-18
"""

import pytest
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Add parent directory to Python path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from validator import (
    ActionValidator,
    CommandType,
    ValidationError,
    ValidationResult,
    ValidatorStats,
    DEFAULT_COMMAND_WHITELIST,
    create_validator,
    get_validator,
    reset_validator,
    validate_command,
    is_whitelisted,
    get_supported_commands,
    get_whitelisted_commands,
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def validator():
    """Create a fresh validator for each test."""
    return ActionValidator(strict_mode=False, log_errors=False)


@pytest.fixture
def strict_validator():
    """Create a strict validator for testing error raising."""
    return ActionValidator(strict_mode=True, log_errors=False)


@pytest.fixture
def custom_whitelist_validator():
    """Create a validator with custom whitelist."""
    return ActionValidator(
        whitelist=[CommandType.BUILD, CommandType.CAPTURE],
        log_errors=False
    )


# ============================================
# Test CommandType Enum
# ============================================

class TestCommandType:
    """Tests for CommandType enum."""
    
    def test_command_type_values(self):
        """Test that all expected command types exist."""
        expected_types = [
            "BUILD", "CAPTURE", "ATTACK_MOVE", "SET_POSTURE",
            "PRODUCE", "RETREAT", "STOP", "HOLD", "PING", "PONG"
        ]
        for cmd_type in expected_types:
            assert hasattr(CommandType, cmd_type)
            assert CommandType[cmd_type].value == cmd_type
    
    def test_command_type_unique(self):
        """Test that all command type values are unique."""
        values = [ct.value for ct in CommandType]
        assert len(values) == len(set(values))


# ============================================
# Test ValidationResult
# ============================================

class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test creating a validation result."""
        result = ValidationResult(
            is_valid=True,
            command={"command": "BUILD"},
            errors=[],
            warnings=[]
        )
        assert result.is_valid is True
        assert result.command == {"command": "BUILD"}
        assert result.errors == []
        assert result.warnings == []
    
    def test_validation_result_to_dict(self):
        """Test converting validation result to dict."""
        result = ValidationResult(
            is_valid=False,
            command={"command": "INVALID"},
            errors=["Unknown command"],
            warnings=["Deprecated syntax"]
        )
        result_dict = result.to_dict()
        assert result_dict["is_valid"] is False
        assert result_dict["command"] == {"command": "INVALID"}
        assert result_dict["errors"] == ["Unknown command"]
        assert result_dict["warnings"] == ["Deprecated syntax"]


# ============================================
# Test ValidatorStats
# ============================================

class TestValidatorStats:
    """Tests for ValidatorStats dataclass."""
    
    def test_stats_initialization(self):
        """Test stats initialization."""
        stats = ValidatorStats()
        assert stats.total_validations == 0
        assert stats.passed == 0
        assert stats.failed == 0
        assert stats.errors_by_type == {}
        assert stats.warnings_by_type == {}
    
    def test_stats_record_validation_passed(self):
        """Test recording a passed validation."""
        stats = ValidatorStats()
        result = ValidationResult(
            is_valid=True,
            command={"command": "BUILD"},
            errors=[]
        )
        stats.record_validation(result)
        assert stats.total_validations == 1
        assert stats.passed == 1
        assert stats.failed == 0
    
    def test_stats_record_validation_failed(self):
        """Test recording a failed validation."""
        stats = ValidatorStats()
        result = ValidationResult(
            is_valid=False,
            command={"command": "INVALID"},
            errors=["TypeError: Invalid command type"]
        )
        stats.record_validation(result)
        assert stats.total_validations == 1
        assert stats.passed == 0
        assert stats.failed == 1
        assert stats.errors_by_type.get("TypeError", 0) == 1
    
    def test_stats_to_dict(self):
        """Test converting stats to dict."""
        stats = ValidatorStats(
            total_validations=10,
            passed=8,
            failed=2,
            errors_by_type={"TypeError": 1, "ValueError": 1},
            warnings_by_type={"Deprecation": 1}
        )
        stats_dict = stats.to_dict()
        assert stats_dict["total_validations"] == 10
        assert stats_dict["passed"] == 8
        assert stats_dict["failed"] == 2
        assert stats_dict["pass_rate"] == 0.8


# ============================================
# Test ValidationError
# ============================================

class TestValidationError:
    """Tests for ValidationError exception."""
    
    def test_validation_error_creation(self):
        """Test creating a validation error."""
        error = ValidationError(
            message="Test error",
            command={"command": "BAD"},
            field="command",
            expected="BUILD",
            actual="BAD"
        )
        assert "Test error" in str(error)
        assert "BUILD" in str(error)
        assert "BAD" in str(error)
    
    def test_validation_error_minimal(self):
        """Test creating a validation error with minimal info."""
        error = ValidationError(message="Simple error")
        assert str(error) == "ValidationError: Simple error"


# ============================================
# Test ActionValidator - Basic Validation
# ============================================

class TestActionValidatorBasic:
    """Tests for basic validator functionality."""
    
    def test_validate_valid_build_command(self, validator):
        """Test validating a valid BUILD command."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = validator.validate(command)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_valid_capture_command(self, validator):
        """Test validating a valid CAPTURE command."""
        command = {
            "command": "CAPTURE",
            "squad_id": 1,
            "point_id": 5
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_valid_attack_move_command(self, validator):
        """Test validating a valid ATTACK_MOVE command."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": [300, 400, 0]
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_valid_set_posture_command(self, validator):
        """Test validating a valid SET_POSTURE command."""
        command = {
            "command": "SET_POSTURE",
            "squad_id": 1,
            "posture": "defensive"
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_valid_produce_command(self, validator):
        """Test validating a valid PRODUCE command."""
        command = {
            "command": "PRODUCE",
            "building_id": 1,
            "unit_type": "riflemen"
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_valid_retreat_command(self, validator):
        """Test validating a valid RETREAT command."""
        command = {
            "command": "RETREAT",
            "squad_id": 1
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_valid_stop_command(self, validator):
        """Test validating a valid STOP command."""
        command = {
            "command": "STOP",
            "squad_id": 1
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_valid_hold_command(self, validator):
        """Test validating a valid HOLD command."""
        command = {
            "command": "HOLD",
            "squad_id": 1
        }
        result = validator.validate(command)
        assert result.is_valid is True


# ============================================
# Test ActionValidator - Whitelist Validation
# ============================================

class TestActionValidatorWhitelist:
    """Tests for whitelist validation."""
    
    def test_validate_unknown_command_type(self, validator):
        """Test validating a command with unknown type."""
        command = {"command": "UNKNOWN_COMMAND"}
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Unknown command type" in error for error in result.errors)
    
    def test_validate_command_not_in_whitelist(self, custom_whitelist_validator):
        """Test validating a command not in custom whitelist."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": [100, 200, 0]
        }
        result = custom_whitelist_validator.validate(command)
        assert result.is_valid is False
        assert any("not in whitelist" in error for error in result.errors)
    
    def test_validate_command_in_custom_whitelist(self, custom_whitelist_validator):
        """Test validating a command in custom whitelist."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = custom_whitelist_validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_empty_command_field(self, validator):
        """Test validating a command with missing command field."""
        command = {"squad_id": 1}
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("missing 'command' field" in error for error in result.errors)
    
    def test_validate_command_none(self, validator):
        """Test validating None."""
        result = validator.validate(None)
        assert result.is_valid is False
    
    def test_validate_command_not_dict(self, validator):
        """Test validating a non-dict value."""
        result = validator.validate("not a dict")
        assert result.is_valid is False


# ============================================
# Test ActionValidator - Required Fields
# ============================================

class TestActionValidatorRequiredFields:
    """Tests for required field validation."""
    
    def test_validate_build_missing_engineer_id(self, validator):
        """Test BUILD command missing engineer_id."""
        command = {
            "command": "BUILD",
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Missing required field 'engineer_id'" in error for error in result.errors)
    
    def test_validate_build_missing_building_type(self, validator):
        """Test BUILD command missing building_type."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "position": [100, 200, 0]
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Missing required field 'building_type'" in error for error in result.errors)
    
    def test_validate_build_missing_position(self, validator):
        """Test BUILD command missing position."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks"
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Missing required field 'position'" in error for error in result.errors)
    
    def test_validate_capture_missing_squad_id(self, validator):
        """Test CAPTURE command missing squad_id."""
        command = {
            "command": "CAPTURE",
            "point_id": 5
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Missing required field 'squad_id'" in error for error in result.errors)
    
    def test_validate_capture_missing_point_id(self, validator):
        """Test CAPTURE command missing point_id."""
        command = {
            "command": "CAPTURE",
            "squad_id": 1
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Missing required field 'point_id'" in error for error in result.errors)
    
    def test_validate_attack_move_missing_position(self, validator):
        """Test ATTACK_MOVE command missing position."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 1
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Missing required field 'position'" in error for error in result.errors)
    
    def test_validate_set_posture_missing_posture(self, validator):
        """Test SET_POSTURE command missing posture."""
        command = {
            "command": "SET_POSTURE",
            "squad_id": 1
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Missing required field 'posture'" in error for error in result.errors)


# ============================================
# Test ActionValidator - Type Validation
# ============================================

class TestActionValidatorTypeValidation:
    """Tests for field type validation."""
    
    def test_validate_build_wrong_engineer_id_type(self, validator):
        """Test BUILD command with wrong engineer_id type."""
        command = {
            "command": "BUILD",
            "engineer_id": "not_an_int",
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("engineer_id" in error and "type" in error.lower() for error in result.errors)
    
    def test_validate_build_wrong_position_type(self, validator):
        """Test BUILD command with wrong position type."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": "not_a_list"
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("position" in error and "list" in error.lower() for error in result.errors)
    
    def test_validate_build_wrong_building_type_type(self, validator):
        """Test BUILD command with wrong building_type type."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": 123,
            "position": [100, 200, 0]
        }
        result = validator.validate(command)
        assert result.is_valid is False


# ============================================
# Test ActionValidator - Position Validation
# ============================================

class TestActionValidatorPositionValidation:
    """Tests for position format validation."""
    
    def test_validate_position_not_list(self, validator):
        """Test command with position not a list."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": "not_a_list"
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Position must be a list" in error for error in result.errors)
    
    def test_validate_position_wrong_length(self, validator):
        """Test command with position of wrong length."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200]  # Only 2 elements
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Position must have 3 elements" in error for error in result.errors)
    
    def test_validate_position_non_numeric(self, validator):
        """Test command with non-numeric position elements."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, "not_a_number", 0]
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Position" in error and "number" in error.lower() for error in result.errors)
    
    def test_validate_position_float_coordinates(self, validator):
        """Test command with float position coordinates (should be valid)."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100.5, 200.7, 0.0]
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_position_tuple(self, validator):
        """Test command with tuple position (should be valid)."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": (100, 200, 0)
        }
        result = validator.validate(command)
        assert result.is_valid is True


# ============================================
# Test ActionValidator - Valid Values
# ============================================

class TestActionValidatorValidValues:
    """Tests for valid value validation."""
    
    def test_validate_set_posture_valid_values(self, validator):
        """Test SET_POSTURE with valid posture values."""
        valid_postures = ["aggressive", "defensive", "retreat", "hold"]
        for posture in valid_postures:
            command = {
                "command": "SET_POSTURE",
                "squad_id": 1,
                "posture": posture
            }
            result = validator.validate(command)
            assert result.is_valid is True, f"Posture '{posture}' should be valid"
    
    def test_validate_set_posture_invalid_value(self, validator):
        """Test SET_POSTURE with invalid posture value."""
        command = {
            "command": "SET_POSTURE",
            "squad_id": 1,
            "posture": "invalid_posture"
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("posture" in error and "invalid" in error.lower() for error in result.errors)


# ============================================
# Test ActionValidator - Custom Validators
# ============================================

class TestActionValidatorCustomValidators:
    """Tests for custom validator functionality."""
    
    def test_add_custom_validator(self, validator):
        """Test adding a custom validator."""
        def check_positive_engineer_id(command):
            if command.get("command") == "BUILD":
                engineer_id = command.get("engineer_id")
                if engineer_id is not None and engineer_id <= 0:
                    return "engineer_id must be positive"
            return None
        
        validator.add_validator("positive_engineer", check_positive_engineer_id)
        assert "positive_engineer" in validator.list_validators()
    
    def test_custom_validator_called(self, validator):
        """Test that custom validator is called during validation."""
        def check_max_engineer_id(command):
            if command.get("command") == "BUILD":
                engineer_id = command.get("engineer_id")
                if engineer_id is not None and engineer_id > 1000:
                    return "engineer_id too large"
            return None
        
        validator.add_validator("max_engineer", check_max_engineer_id)
        
        # Valid command
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = validator.validate(command)
        assert result.is_valid is True
        
        # Invalid command
        command = {
            "command": "BUILD",
            "engineer_id": 2000,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = validator.validate(command)
        assert result.is_valid is False
        assert any("Custom validator" in error and "engineer_id too large" in error for error in result.errors)
    
    def test_remove_custom_validator(self, validator):
        """Test removing a custom validator."""
        def dummy_validator(command):
            return None
        
        validator.add_validator("dummy", dummy_validator)
        assert "dummy" in validator.list_validators()
        
        removed = validator.remove_validator("dummy")
        assert removed is True
        assert "dummy" not in validator.list_validators()
        
        # Try removing non-existent validator
        removed = validator.remove_validator("nonexistent")
        assert removed is False


# ============================================
# Test ActionValidator - Whitelist Management
# ============================================

class TestActionValidatorWhitelistManagement:
    """Tests for whitelist management."""
    
    def test_get_whitelist(self, validator):
        """Test getting the whitelist."""
        whitelist = validator.get_whitelist()
        assert len(whitelist) > 0
        assert CommandType.BUILD in whitelist
    
    def test_set_whitelist(self, validator):
        """Test setting a custom whitelist."""
        new_whitelist = [CommandType.BUILD, CommandType.CAPTURE]
        validator.set_whitelist(new_whitelist)
        assert validator.get_whitelist() == new_whitelist
    
    def test_add_to_whitelist(self, validator):
        """Test adding to whitelist."""
        original_count = len(validator.get_whitelist())
        validator.add_to_whitelist(CommandType.PING)
        new_count = len(validator.get_whitelist())
        # PING might already be in whitelist
        assert new_count >= original_count
        assert CommandType.PING in validator.get_whitelist()
    
    def test_remove_from_whitelist(self, validator):
        """Test removing from whitelist."""
        validator.add_to_whitelist(CommandType.BUILD)
        removed = validator.remove_from_whitelist(CommandType.BUILD)
        assert removed is True
        assert CommandType.BUILD not in validator.get_whitelist()


# ============================================
# Test ActionValidator - Statistics
# ============================================

class TestActionValidatorStatistics:
    """Tests for statistics tracking."""
    
    def test_stats_tracking(self, validator):
        """Test that validation statistics are tracked."""
        # Valid command
        validator.validate({"command": "BUILD", "engineer_id": 1, "building_type": "barracks", "position": [100, 200, 0]})
        
        # Invalid command
        validator.validate({"command": "INVALID"})
        
        stats = validator.get_stats()
        assert stats.total_validations == 2
        assert stats.passed == 1
        assert stats.failed == 1
    
    def test_reset_stats(self, validator):
        """Test resetting statistics."""
        validator.validate({"command": "BUILD", "engineer_id": 1, "building_type": "barracks", "position": [100, 200, 0]})
        validator.reset_stats()
        
        stats = validator.get_stats()
        assert stats.total_validations == 0
        assert stats.passed == 0
        assert stats.failed == 0


# ============================================
# Test Strict Mode
# ============================================

class TestActionValidatorStrictMode:
    """Tests for strict mode validation."""
    
    def test_strict_mode_raises_error(self, strict_validator):
        """Test that strict mode raises ValidationError."""
        command = {"command": "INVALID"}
        
        with pytest.raises(ValidationError):
            strict_validator.validate(command)
    
    def test_strict_mode_valid_command(self, strict_validator):
        """Test that strict mode doesn't raise for valid commands."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        # Should not raise
        result = strict_validator.validate(command)
        assert result.is_valid is True


# ============================================
# Test is_valid Method
# ============================================

class TestActionValidatorIsValid:
    """Tests for the is_valid convenience method."""
    
    def test_is_valid_true(self, validator):
        """Test is_valid returns True for valid command."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        assert validator.is_valid(command) is True
    
    def test_is_valid_false(self, validator):
        """Test is_valid returns False for invalid command."""
        command = {"command": "INVALID"}
        assert validator.is_valid(command) is False


# ============================================
# Test Factory Functions
# ============================================

class TestFactoryFunctions:
    """Tests for factory functions."""
    
    def test_create_validator(self):
        """Test creating a validator with factory."""
        validator = create_validator(strict_mode=True)
        assert isinstance(validator, ActionValidator)
        assert validator.strict_mode is True
    
    def test_get_validator_singleton(self):
        """Test getting singleton validator."""
        validator1 = get_validator()
        validator2 = get_validator()
        assert validator1 is validator2
    
    def test_reset_validator(self):
        """Test resetting singleton validator."""
        validator1 = get_validator()
        reset_validator()
        validator2 = get_validator()
        assert validator1 is not validator2
    
    def test_validate_command_function(self):
        """Test validate_command convenience function."""
        reset_validator()  # Reset to ensure fresh instance
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        assert validate_command(command) is True
        
        invalid_command = {"command": "INVALID"}
        assert validate_command(invalid_command) is False


# ============================================
# Test Convenience Functions
# ============================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_is_whitelisted(self):
        """Test checking if command is whitelisted."""
        assert is_whitelisted("BUILD") is True
        assert is_whitelisted("CAPTURE") is True
        assert is_whitelisted("INVALID") is False
    
    def test_get_supported_commands(self):
        """Test getting list of supported commands."""
        commands = get_supported_commands()
        assert "BUILD" in commands
        assert "CAPTURE" in commands
        assert "INVALID" not in commands
    
    def test_get_whitelisted_commands(self):
        """Test getting list of whitelisted commands."""
        commands = get_whitelisted_commands()
        assert "BUILD" in commands
        assert "CAPTURE" in commands
        # All supported commands should be whitelisted by default
        assert set(commands) == set(get_supported_commands())


# ============================================
# Test Default Whitelist
# ============================================

class TestDefaultWhitelist:
    """Tests for default whitelist."""
    
    def test_default_whitelist_not_empty(self):
        """Test that default whitelist is not empty."""
        assert len(DEFAULT_COMMAND_WHITELIST) > 0
    
    def test_default_whitelist_contains_all_standard_commands(self):
        """Test that default whitelist contains all standard commands."""
        standard_commands = [
            CommandType.BUILD,
            CommandType.CAPTURE,
            CommandType.ATTACK_MOVE,
            CommandType.SET_POSTURE,
            CommandType.PRODUCE,
            CommandType.RETREAT,
            CommandType.STOP,
            CommandType.HOLD,
        ]
        for cmd in standard_commands:
            assert cmd in DEFAULT_COMMAND_WHITELIST


# ============================================
# Test Edge Cases
# ============================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_validate_empty_dict(self, validator):
        """Test validating empty dict."""
        result = validator.validate({})
        assert result.is_valid is False
    
    def test_validate_command_with_extra_fields(self, validator):
        """Test validating command with extra fields (should still be valid)."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0],
            "extra_field": "should be ignored"
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_position_with_negative_coordinates(self, validator):
        """Test position with negative coordinates (should be valid)."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [-100, -200, 0]
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_position_with_zero_coordinates(self, validator):
        """Test position with zero coordinates (should be valid)."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [0, 0, 0]
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_validate_command_case_sensitivity(self, validator):
        """Test that command type is case-sensitive."""
        command = {"command": "build"}  # lowercase
        result = validator.validate(command)
        assert result.is_valid is False


# ============================================
# Test Performance
# ============================================

class TestPerformance:
    """Tests for validator performance."""
    
    def test_validation_performance(self, validator):
        """Test that validation is fast."""
        import time
        
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        
        start = time.time()
        for _ in range(1000):
            validator.validate(command)
        elapsed = time.time() - start
        
        # Should be able to validate 1000 commands in under 1 second
        assert elapsed < 1.0, f"Validation too slow: {elapsed:.3f}s for 1000 commands"
