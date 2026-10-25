"""
CoH1 × Mistral AI Mod - Command Executor Tests

Tests for command execution logic and validation.
This tests the command structure and validation that the SCAR command_executor.scar handles.

Author: Generated via planner skill
Version: 1.0.0
Date: 2026-10-25
"""

import json
import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum, auto


# ============================================
# Test Setup
# ============================================

class CommandType(Enum):
    """Command types supported by the executor."""
    BUILD = "BUILD"
    CAPTURE = "CAPTURE"
    ATTACK_MOVE = "ATTACK_MOVE"
    SET_POSTURE = "SET_POSTURE"
    PRODUCE = "PRODUCE"
    RETREAT = "RETREAT"
    STOP = "STOP"
    HOLD = "HOLD"
    PING = "PING"
    PONG = "PONG"


class Posture(Enum):
    """Unit postures."""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    RETREAT = "retreat"
    HOLD = "hold"


@dataclass
class CommandValidationResult:
    """Result of command validation."""
    is_valid: bool
    command_type: Optional[str] = None
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


# ============================================
# Command Validation (Python-side mirror of SCAR logic)
# ============================================

class CommandValidator:
    """
    Python mirror of the SCAR command_executor.scar validation logic.
    Used for testing command structures before sending to SCAR.
    """
    
    VALID_COMMAND_TYPES = {
        CommandType.BUILD.value,
        CommandType.CAPTURE.value,
        CommandType.ATTACK_MOVE.value,
        CommandType.SET_POSTURE.value,
        CommandType.PRODUCE.value,
        CommandType.RETREAT.value,
        CommandType.STOP.value,
        CommandType.HOLD.value,
        CommandType.PING.value,
        CommandType.PONG.value,
    }
    
    VALID_POSTURES = {
        Posture.AGGRESSIVE.value,
        Posture.DEFENSIVE.value,
        Posture.RETREAT.value,
        Posture.HOLD.value,
    }
    
    REQUIRED_FIELDS = {
        CommandType.BUILD.value: ["engineer_id", "building_type", "position"],
        CommandType.CAPTURE.value: ["squad_id", "point_id"],
        CommandType.ATTACK_MOVE.value: ["squad_id", "position"],
        CommandType.SET_POSTURE.value: ["squad_id", "posture"],
        CommandType.PRODUCE.value: ["building_id", "unit_type"],
        CommandType.RETREAT.value: ["squad_id"],
        CommandType.STOP.value: ["squad_id"],
        CommandType.HOLD.value: ["squad_id"],
        CommandType.PING.value: [],
        CommandType.PONG.value: [],
    }
    
    @classmethod
    def validate(cls, command: Dict[str, Any]) -> CommandValidationResult:
        """Validate a command dictionary."""
        result = CommandValidationResult(is_valid=True)
        
        if not isinstance(command, dict):
            return CommandValidationResult(
                is_valid=False,
                errors=["Command must be a dictionary"]
            )
        
        # Check command type
        command_type = command.get("command")
        if command_type is None:
            return CommandValidationResult(
                is_valid=False,
                errors=["Missing 'command' field"]
            )
        
        result.command_type = command_type
        
        # Check if command type is valid
        if command_type not in cls.VALID_COMMAND_TYPES:
            return CommandValidationResult(
                is_valid=False,
                command_type=command_type,
                errors=[f"Invalid command type: {command_type}"]
            )
        
        # Check required fields
        required_fields = cls.REQUIRED_FIELDS.get(command_type, [])
        for field_name in required_fields:
            if field_name not in command:
                result.errors.append(f"Missing required field: {field_name}")
                result.is_valid = False
        
        # Validate posture for SET_POSTURE
        if command_type == CommandType.SET_POSTURE.value:
            posture = command.get("posture")
            if posture and posture not in cls.VALID_POSTURES:
                result.errors.append(f"Invalid posture: {posture}")
                result.is_valid = False
        
        # Validate position format
        if "position" in command:
            position = command["position"]
            if not isinstance(position, (list, tuple)) or len(position) < 3:
                result.errors.append("Position must be a list/tuple of at least 3 coordinates")
                result.is_valid = False
            else:
                # Check if position has valid numeric values
                try:
                    for i, coord in enumerate(position[:3]):
                        float(coord)
                except (ValueError, TypeError):
                    result.errors.append("Position coordinates must be numeric")
                    result.is_valid = False
        
        return result
    
    @classmethod
    def validate_command_list(cls, commands: list) -> list:
        """Validate a list of commands."""
        results = []
        for i, command in enumerate(commands):
            result = cls.validate(command)
            result.errors = [f"Command {i}: {err}" for err in result.errors]
            result.warnings = [f"Command {i}: {warn}" for warn in result.warnings]
            results.append(result)
        return results


# ============================================
# Test Data
# ============================================

# Valid command examples
VALID_BUILD_COMMAND = {
    "command": "BUILD",
    "engineer_id": 1,
    "building_type": "tactical_support",
    "position": [100.0, 50.0, 0.0]
}

VALID_CAPTURE_COMMAND = {
    "command": "CAPTURE",
    "squad_id": 5,
    "point_id": 2
}

VALID_ATTACK_MOVE_COMMAND = {
    "command": "ATTACK_MOVE",
    "squad_id": 3,
    "position": [200.0, 150.0, 0.0]
}

VALID_SET_POSTURE_COMMAND = {
    "command": "SET_POSTURE",
    "squad_id": 4,
    "posture": "aggressive"
}

VALID_PRODUCE_COMMAND = {
    "command": "PRODUCE",
    "building_id": 10,
    "unit_type": "riflemen"
}

VALID_RETREAT_COMMAND = {
    "command": "RETREAT",
    "squad_id": 7
}

VALID_STOP_COMMAND = {
    "command": "STOP",
    "squad_id": 8
}

VALID_HOLD_COMMAND = {
    "command": "HOLD",
    "squad_id": 9
}

VALID_PING_COMMAND = {
    "command": "PING",
    "timestamp": 123.456
}

# Invalid command examples
INVALID_NO_COMMAND_FIELD = {
    "squad_id": 1,
    "position": [100, 100, 0]
}

INVALID_COMMAND_TYPE = {
    "command": "INVALID_COMMAND",
    "squad_id": 1
}

INVALID_BUILD_MISSING_FIELDS = {
    "command": "BUILD",
    "engineer_id": 1
    # Missing building_type and position
}

INVALID_POSTURE = {
    "command": "SET_POSTURE",
    "squad_id": 1,
    "posture": "invalid_posture"
}

INVALID_POSITION = {
    "command": "ATTACK_MOVE",
    "squad_id": 1,
    "position": [100, 100]  # Only 2 coordinates
}

INVALID_POSITION_VALUES = {
    "command": "ATTACK_MOVE",
    "squad_id": 1,
    "position": ["not_a_number", 100, 0]
}


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def validator():
    """Create a CommandValidator instance."""
    return CommandValidator


# ============================================
# Test Classes
# ============================================

class TestCommandValidation:
    """Test command validation logic."""
    
    def test_validate_valid_build_command(self, validator):
        """Test validation of valid BUILD command."""
        result = validator.validate(VALID_BUILD_COMMAND)
        assert result.is_valid is True
        assert result.command_type == "BUILD"
        assert len(result.errors) == 0
    
    def test_validate_valid_capture_command(self, validator):
        """Test validation of valid CAPTURE command."""
        result = validator.validate(VALID_CAPTURE_COMMAND)
        assert result.is_valid is True
        assert result.command_type == "CAPTURE"
        assert len(result.errors) == 0
    
    def test_validate_valid_attack_move_command(self, validator):
        """Test validation of valid ATTACK_MOVE command."""
        result = validator.validate(VALID_ATTACK_MOVE_COMMAND)
        assert result.is_valid is True
        assert result.command_type == "ATTACK_MOVE"
        assert len(result.errors) == 0
    
    def test_validate_valid_set_posture_command(self, validator):
        """Test validation of valid SET_POSTURE command."""
        result = validator.validate(VALID_SET_POSTURE_COMMAND)
        assert result.is_valid is True
        assert result.command_type == "SET_POSTURE"
        assert len(result.errors) == 0
    
    def test_validate_valid_produce_command(self, validator):
        """Test validation of valid PRODUCE command."""
        result = validator.validate(VALID_PRODUCE_COMMAND)
        assert result.is_valid is True
        assert result.command_type == "PRODUCE"
        assert len(result.errors) == 0
    
    def test_validate_valid_retreat_command(self, validator):
        """Test validation of valid RETREAT command."""
        result = validator.validate(VALID_RETREAT_COMMAND)
        assert result.is_valid is True
        assert result.command_type == "RETREAT"
        assert len(result.errors) == 0
    
    def test_validate_valid_stop_command(self, validator):
        """Test validation of valid STOP command."""
        result = validator.validate(VALID_STOP_COMMAND)
        assert result.is_valid is True
        assert result.command_type == "STOP"
        assert len(result.errors) == 0
    
    def test_validate_valid_hold_command(self, validator):
        """Test validation of valid HOLD command."""
        result = validator.validate(VALID_HOLD_COMMAND)
        assert result.is_valid is True
        assert result.command_type == "HOLD"
        assert len(result.errors) == 0
    
    def test_validate_valid_ping_command(self, validator):
        """Test validation of valid PING command."""
        result = validator.validate(VALID_PING_COMMAND)
        assert result.is_valid is True
        assert result.command_type == "PING"
        assert len(result.errors) == 0


class TestCommandValidationErrors:
    """Test command validation error cases."""
    
    def test_validate_null_command(self, validator):
        """Test validation of null command."""
        result = validator.validate(None)
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validate_missing_command_field(self, validator):
        """Test validation when command field is missing."""
        result = validator.validate(INVALID_NO_COMMAND_FIELD)
        assert result.is_valid is False
        assert "Missing 'command' field" in result.errors[0]
    
    def test_validate_invalid_command_type(self, validator):
        """Test validation of invalid command type."""
        result = validator.validate(INVALID_COMMAND_TYPE)
        assert result.is_valid is False
        assert "Invalid command type" in result.errors[0]
    
    def test_validate_build_missing_fields(self, validator):
        """Test validation of BUILD command with missing fields."""
        result = validator.validate(INVALID_BUILD_MISSING_FIELDS)
        assert result.is_valid is False
        assert any("building_type" in err for err in result.errors)
        assert any("position" in err for err in result.errors)
    
    def test_validate_invalid_posture(self, validator):
        """Test validation of SET_POSTURE with invalid posture."""
        result = validator.validate(INVALID_POSTURE)
        assert result.is_valid is False
        assert any("Invalid posture" in err for err in result.errors)
    
    def test_validate_invalid_position_length(self, validator):
        """Test validation of ATTACK_MOVE with invalid position."""
        result = validator.validate(INVALID_POSITION)
        assert result.is_valid is False
        assert any("Position must be a list/tuple of at least 3" in err for err in result.errors)
    
    def test_validate_invalid_position_values(self, validator):
        """Test validation of ATTACK_MOVE with non-numeric position."""
        result = validator.validate(INVALID_POSITION_VALUES)
        assert result.is_valid is False
        assert any("Position coordinates must be numeric" in err for err in result.errors)


class TestAllCommandTypes:
    """Test all supported command types."""
    
    ALL_COMMAND_TYPES = [
        CommandType.BUILD.value,
        CommandType.CAPTURE.value,
        CommandType.ATTACK_MOVE.value,
        CommandType.SET_POSTURE.value,
        CommandType.PRODUCE.value,
        CommandType.RETREAT.value,
        CommandType.STOP.value,
        CommandType.HOLD.value,
        CommandType.PING.value,
        CommandType.PONG.value,
    ]
    
    def test_all_command_types_are_valid(self, validator):
        """Test that all command types in the enum are recognized."""
        for cmd_type in self.ALL_COMMAND_TYPES:
            result = validator.validate({"command": cmd_type})
            # Some commands require additional fields, but the type itself should be valid
            assert result.command_type == cmd_type


class TestCommandListValidation:
    """Test validation of command lists."""
    
    def test_validate_command_list_all_valid(self, validator):
        """Test validation of list with all valid commands."""
        commands = [
            VALID_BUILD_COMMAND,
            VALID_CAPTURE_COMMAND,
            VALID_ATTACK_MOVE_COMMAND,
        ]
        results = validator.validate_command_list(commands)
        assert all(r.is_valid for r in results)
    
    def test_validate_command_list_with_invalid(self, validator):
        """Test validation of list with some invalid commands."""
        commands = [
            VALID_BUILD_COMMAND,
            INVALID_NO_COMMAND_FIELD,
            VALID_ATTACK_MOVE_COMMAND,
        ]
        results = validator.validate_command_list(commands)
        assert results[0].is_valid is True
        assert results[1].is_valid is False
        assert results[2].is_valid is True


class TestCommandSerialization:
    """Test command serialization and deserialization."""
    
    def test_serialize_valid_command(self):
        """Test serialization of valid command to JSON."""
        json_str = json.dumps(VALID_BUILD_COMMAND)
        assert isinstance(json_str, str)
        
        # Deserialize and verify
        deserialized = json.loads(json_str)
        assert deserialized == VALID_BUILD_COMMAND
    
    def test_serialize_command_list(self):
        """Test serialization of command list."""
        commands = {
            "commands": [
                VALID_BUILD_COMMAND,
                VALID_ATTACK_MOVE_COMMAND,
            ]
        }
        json_str = json.dumps(commands)
        
        deserialized = json.loads(json_str)
        assert deserialized["commands"][0]["command"] == "BUILD"
        assert deserialized["commands"][1]["command"] == "ATTACK_MOVE"
    
    def test_deserialize_command_file(self):
        """Test reading commands from a file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            commands = {
                "commands": [
                    VALID_BUILD_COMMAND,
                    VALID_CAPTURE_COMMAND
                ]
            }
            json.dump(commands, f)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                loaded_commands = json.load(f)
            
            assert len(loaded_commands["commands"]) == 2
            assert loaded_commands["commands"][0]["command"] == "BUILD"
        finally:
            os.unlink(temp_path)


class TestCommandEdgeCases:
    """Test edge cases for command validation."""
    
    def test_command_with_extra_fields(self, validator):
        """Test command with extra fields not in spec."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 100, 0],
            "extra_field": "should be ignored"
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_command_with_zero_position(self, validator):
        """Test command with zero position coordinates."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": [0.0, 0.0, 0.0]
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_command_with_negative_position(self, validator):
        """Test command with negative position coordinates."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": [-100.0, -50.0, 0.0]
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_command_with_float_position(self, validator):
        """Test command with float position values."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": [100.5, 50.7, 0.3]
        }
        result = validator.validate(command)
        assert result.is_valid is True
    
    def test_all_postures_valid(self, validator):
        """Test all valid posture values."""
        for posture in [
            Posture.AGGRESSIVE.value,
            Posture.DEFENSIVE.value,
            Posture.RETREAT.value,
            Posture.HOLD.value
        ]:
            command = {
                "command": "SET_POSTURE",
                "squad_id": 1,
                "posture": posture
            }
            result = validator.validate(command)
            assert result.is_valid is True


class TestCommandBuildingTypes:
    """Test command building type validation."""
    
    VALID_BUILDING_TYPES = [
        "tactical_support",
        "supply_plant",
        "munitions_depot",
        "fuel_depot",
        "vehicle_depot",
        "infantry_depot",
        "barracks",
        "command_post",
        "supply_yard",
    ]
    
    def test_build_command_with_various_building_types(self, validator):
        """Test BUILD command with various building types."""
        for building_type in self.VALID_BUILDING_TYPES:
            command = {
                "command": "BUILD",
                "engineer_id": 1,
                "building_type": building_type,
                "position": [100, 100, 0]
            }
            result = validator.validate(command)
            assert result.is_valid is True


class TestCommandUnitTypes:
    """Test command unit type validation."""
    
    VALID_UNIT_TYPES = [
        "riflemen",
        "engineer",
        "sniper",
        "machine_gun",
        "mortar",
        "bazooka",
        "scout_car",
        "halftrack",
        "light_tank",
        "medium_tank",
        "heavy_tank",
    ]
    
    def test_produce_command_with_various_unit_types(self, validator):
        """Test PRODUCE command with various unit types."""
        for unit_type in self.VALID_UNIT_TYPES:
            command = {
                "command": "PRODUCE",
                "building_id": 1,
                "unit_type": unit_type
            }
            result = validator.validate(command)
            assert result.is_valid is True


class TestCommandStatistics:
    """Test command statistics tracking."""
    
    def test_command_statistics_initialization(self):
        """Test command statistics initialization."""
        stats = {
            "executed": 0,
            "succeeded": 0,
            "failed": 0,
            "last_command": "",
            "last_error": ""
        }
        assert stats["executed"] == 0
        assert stats["succeeded"] == 0
        assert stats["failed"] == 0
    
    def test_command_success_rate_calculation(self):
        """Test success rate calculation."""
        stats = {
            "executed": 10,
            "succeeded": 8,
            "failed": 2
        }
        success_rate = stats["executed"] > 0 and (stats["succeeded"] / stats["executed"]) or 0
        assert success_rate == 0.8


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
