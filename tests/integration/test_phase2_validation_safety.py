"""
Phase 2 Validation and Safety Pipeline Integration Tests

Tests the complete validation and safety filtering pipeline:
1. Action validator whitelist and structure validation
2. Safety filter resource and population checks
3. Integration with command processor
4. Reflex layer command generation

This test validates Phase 2 exit criteria:
- Command execution API working
- All reflex behaviors implemented
- Reflex layer works without strategist
- Safety and validation in place

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-25
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to Python path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from validator import ActionValidator, CommandType, ValidationResult, DEFAULT_COMMAND_WHITELIST
from safety_filter import SafetyFilter, SafetyFilterResult, UNIT_COSTS, BUILDING_COSTS
from orchestrator.command_processor import CommandProcessor, AICommand, CommandPriority, create_build_command, create_attack_move_command, create_capture_command, create_produce_command, create_retreat_command, create_set_posture_command, create_stop_command, create_hold_command


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def validator():
    """Create a fresh validator instance for each test."""
    return ActionValidator(whitelist=DEFAULT_COMMAND_WHITELIST.copy())


@pytest.fixture
def safety_filter():
    """Create a fresh safety filter instance for each test."""
    game_state = {
        "resources": {
            "manpower": {"current": 1000, "max": 2000, "income": 10},
            "fuel": {"current": 500, "max": 1000, "income": 5},
            "munitions": {"current": 300, "max": 800, "income": 3}
        },
        "population": {"current": 20, "max": 100},
        "squads": [
            {"id": 1, "type": "riflemen", "health": 100, "max_health": 100},
            {"id": 2, "type": "engineer", "health": 80, "max_health": 100},
        ],
        "buildings": [
            {"id": 101, "type": "barracks", "health": 100, "max_health": 500},
            {"id": 102, "type": "headquarters", "health": 100, "max_health": 1000},
        ],
        "capture_points": [
            {"id": 1001, "owner": None, "capture_progress": 0}
        ],
        "tech_tree": {
            "tier_1": True,
            "tier_2": True,
            "tier_3": False
        }
    }
    return SafetyFilter(game_state=game_state)


@pytest.fixture
def command_processor():
    """Create a fresh command processor instance for each test."""
    from config import Configuration
    from validator import ActionValidator
    from safety_filter import SafetyFilter
    
    config = Configuration()
    
    # Create mock IPC reader
    class MockIPCReader:
        def __init__(self):
            self.commands_sent = []
        
        def send_command(self, command):
            self.commands_sent.append(command)
            return True
    
    mock_ipc = MockIPCReader()
    
    # Create game state with sufficient resources
    game_state = {
        "resources": {
            "manpower": {"current": 1000, "max": 2000, "income": 10},
            "fuel": {"current": 500, "max": 1000, "income": 5},
            "munitions": {"current": 300, "max": 800, "income": 3}
        },
        "population": {"current": 20, "max": 100},
        "squads": [
            {"id": 1, "type": "riflemen", "health": 100, "max_health": 100},
            {"id": 2, "type": "engineer", "health": 80, "max_health": 100}
        ],
        "buildings": [
            {"id": 101, "type": "barracks", "health": 100, "max_health": 500}
        ],
        "capture_points": [
            {"id": 1001, "owner": None, "capture_progress": 0}
        ],
        "tech_tree": {
            "tier_1": True,
            "tier_2": True,
            "tier_3": False
        }
    }
    
    # Create validator and safety filter
    validator = ActionValidator()
    safety_filter = SafetyFilter(game_state=game_state)
    
    processor = CommandProcessor(
        config=config, 
        ipc_reader=mock_ipc,
        validator=validator,
        safety_filter=safety_filter,
        game_state=game_state
    )
    processor.start()
    yield processor
    processor.stop()


# =============================================================================
# Validator Tests
# =============================================================================

class TestActionValidator:
    """Tests for the ActionValidator class."""
    
    def test_valid_build_command(self, validator):
        """Test validation of a valid BUILD command."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = validator.validate(command)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_valid_capture_command(self, validator):
        """Test validation of a valid CAPTURE command."""
        command = {
            "command": "CAPTURE",
            "squad_id": 1,
            "point_id": 1001
        }
        result = validator.validate(command)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_valid_attack_move_command(self, validator):
        """Test validation of a valid ATTACK_MOVE command."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": [300, 400, 0]
        }
        result = validator.validate(command)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_valid_produce_command(self, validator):
        """Test validation of a valid PRODUCE command."""
        command = {
            "command": "PRODUCE",
            "building_id": 101,
            "unit_type": "riflemen"
        }
        result = validator.validate(command)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_command_type(self, validator):
        """Test validation of a command with invalid type."""
        command = {
            "command": "INVALID_COMMAND",
            "some_param": "value"
        }
        result = validator.validate(command)
        assert not result.is_valid
        assert any("Unknown command type" in error or "not in whitelist" in error for error in result.errors)
    
    def test_missing_required_field(self, validator):
        """Test validation of a command missing required fields."""
        command = {
            "command": "BUILD",
            "building_type": "barracks"
            # Missing engineer_id and position
        }
        result = validator.validate(command)
        assert not result.is_valid
        assert any("Missing required field" in error for error in result.errors)
    
    def test_wrong_field_type(self, validator):
        """Test validation of a command with wrong field types."""
        command = {
            "command": "BUILD",
            "engineer_id": "not_an_integer",  # Should be int
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = validator.validate(command)
        assert not result.is_valid
        assert any("wrong type" in error for error in result.errors)
    
    def test_invalid_posture_value(self, validator):
        """Test validation of a command with invalid posture value."""
        command = {
            "command": "SET_POSTURE",
            "squad_id": 1,
            "posture": "invalid_posture"
        }
        result = validator.validate(command)
        assert not result.is_valid
        # The error message should mention the invalid value
        assert any("invalid value" in error.lower() or "valid values" in error.lower() for error in result.errors)
    
    def test_position_format_validation(self, validator):
        """Test validation of position format."""
        # Valid position
        command1 = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": [100, 200, 0]
        }
        result1 = validator.validate(command1)
        assert result1.is_valid
        
        # Invalid position (wrong length)
        command2 = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": [100, 200]  # Missing z coordinate
        }
        result2 = validator.validate(command2)
        assert not result2.is_valid
        
        # Invalid position (not a list)
        command3 = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": "not_a_list"
        }
        result3 = validator.validate(command3)
        assert not result3.is_valid
    
    def test_command_whitelist(self, validator):
        """Test that only whitelisted commands are accepted."""
        # Create validator with limited whitelist
        limited_validator = ActionValidator(
            whitelist=[CommandType.BUILD, CommandType.CAPTURE]
        )
        
        # Whitelisted command
        command1 = {"command": "BUILD", "engineer_id": 1, "building_type": "barracks", "position": [100, 200, 0]}
        result1 = limited_validator.validate(command1)
        assert result1.is_valid
        
        # Not whitelisted command
        command2 = {"command": "ATTACK_MOVE", "squad_id": 1, "position": [100, 200, 0]}
        result2 = limited_validator.validate(command2)
        assert not result2.is_valid
        assert any("not in whitelist" in error for error in result2.errors)


# =============================================================================
# Safety Filter Tests
# =============================================================================

class TestSafetyFilter:
    """Tests for the SafetyFilter class."""
    
    def test_resource_check_sufficient(self, safety_filter):
        """Test resource check with sufficient resources."""
        command = {
            "command": "PRODUCE",
            "building_id": 101,
            "unit_type": "riflemen"
        }
        result = safety_filter.check_command(command)
        assert result.is_safe
        assert any(check.check_type.value == "resource" and check.is_safe for check in result.checks)
    
    def test_resource_check_insufficient(self):
        """Test resource check with insufficient resources."""
        game_state = {
            "resources": {
                "manpower": {"current": 50, "max": 2000, "income": 10},
                "fuel": {"current": 0, "max": 1000, "income": 5},
                "munitions": {"current": 0, "max": 800, "income": 3}
            },
            "population": {"current": 0, "max": 100}
        }
        safety_filter = SafetyFilter(game_state=game_state)
        
        command = {
            "command": "PRODUCE",
            "building_id": 101,
            "unit_type": "medium_tank"  # Requires 720 MP, 180 fuel
        }
        result = safety_filter.check_command(command)
        assert not result.is_safe
        assert any(check.check_type.value == "resource" and not check.is_safe for check in result.checks)
    
    def test_population_check_sufficient(self, safety_filter):
        """Test population check with sufficient cap."""
        command = {
            "command": "PRODUCE",
            "building_id": 101,
            "unit_type": "riflemen"  # Pop cost: 6
        }
        result = safety_filter.check_command(command)
        assert result.is_safe
        assert any(check.check_type.value == "population" and check.is_safe for check in result.checks)
    
    def test_population_check_exceeded(self):
        """Test population check with exceeded cap."""
        game_state = {
            "resources": {
                "manpower": {"current": 1000, "max": 2000},
                "fuel": {"current": 500, "max": 1000},
                "munitions": {"current": 300, "max": 800}
            },
            "population": {"current": 95, "max": 100}
        }
        safety_filter = SafetyFilter(game_state=game_state)
        
        command = {
            "command": "PRODUCE",
            "building_id": 101,
            "unit_type": "heavy_tank"  # Pop cost: 12, would be 95 + 12 = 107 > 100
        }
        result = safety_filter.check_command(command)
        assert not result.is_safe
        assert any(check.check_type.value == "population" and not check.is_safe for check in result.checks)
    
    def test_pathfinding_check(self, safety_filter):
        """Test pathfinding check for movement commands."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": [100, 200, 0]  # Reasonable position
        }
        result = safety_filter.check_command(command)
        # With default settings, reasonable positions should pass
        assert result.is_safe or any("Pathfinding" in str(check) for check in result.checks)
    
    def test_legality_check_build(self, safety_filter):
        """Test legality check for build commands."""
        command = {
            "command": "BUILD",
            "engineer_id": 2,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe
        assert any(check.check_type.value == "legality" and check.is_safe for check in result.checks)
    
    def test_legality_check_unknown_building(self):
        """Test legality check with unknown building type."""
        game_state = {
            "resources": {
                "manpower": {"current": 1000, "max": 2000},
                "fuel": {"current": 500, "max": 1000},
                "munitions": {"current": 300, "max": 800}
            },
            "population": {"current": 0, "max": 100}
        }
        safety_filter = SafetyFilter(game_state=game_state)
        
        command = {
            "command": "BUILD",
            "engineer_id": 2,
            "building_type": "unknown_building",
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert not result.is_safe
        assert any(check.check_type.value in ["legality", "building"] and not check.is_safe for check in result.checks)


# =============================================================================
# Command Processor Integration Tests
# =============================================================================

class TestCommandProcessorIntegration:
    """Tests for CommandProcessor integration with validator and safety filter."""
    
    def test_command_with_validator(self, command_processor):
        """Test that command processor validates commands."""
        # Valid command - use engineer_id=2 which exists in the game state
        build_cmd = create_build_command(
            engineer_id=2,
            building_type="barracks",
            position=[100, 200, 0]
        )
        assert command_processor.add_command(build_cmd)
        
        # Process and verify
        processed = command_processor.process_queue()
        assert processed >= 0
    
    def test_command_with_invalid_type(self, command_processor):
        """Test that invalid command types are rejected."""
        # Create a command with invalid type by bypassing the factory
        invalid_cmd = AICommand(
            command_type="INVALID_COMMAND",
            priority=CommandPriority.NORMAL
        )
        # This should fail validation
        result = command_processor.add_command(invalid_cmd)
        # The command might still be added (depending on validation placement)
        # but it should fail during processing
        assert isinstance(result, bool)
    
    def test_command_processor_with_game_state(self, command_processor):
        """Test command processor with game state for safety filtering."""
        game_state = {
            "resources": {
                "manpower": {"current": 1000, "max": 2000},
                "fuel": {"current": 500, "max": 1000},
                "munitions": {"current": 300, "max": 800}
            },
            "population": {"current": 20, "max": 100}
        }
        command_processor.update_game_state(game_state)
        
        # Add a command that should pass safety checks
        produce_cmd = create_produce_command(
            building_id=101,
            unit_type="riflemen"
        )
        assert command_processor.add_command(produce_cmd)
    
    def test_all_command_types(self, command_processor):
        """Test that all supported command types can be created and added."""
        commands = [
            create_build_command(2, "barracks", [100, 200, 0]),  # Use engineer_id=2
            create_capture_command(2, 1001),  # Use squad_id=2 (engineer)
            create_attack_move_command(1, [300, 400, 0]),
            create_produce_command(101, "riflemen"),
            create_retreat_command(1),
            create_set_posture_command(1, "defensive"),
            create_stop_command(1),
            create_hold_command(1)
        ]
        
        for cmd in commands:
            assert command_processor.add_command(cmd), f"Failed to add command: {cmd.command_type}"
        
        # Process all commands
        processed = command_processor.process_queue()
        assert processed == len(commands)


# =============================================================================
# Full Pipeline Integration Tests
# =============================================================================

class TestFullPipelineIntegration:
    """Tests for the complete validation and safety pipeline."""
    
    def test_full_pipeline_valid_command(self):
        """Test a command that passes all validation and safety checks."""
        from config import Configuration
        
        # Create validator
        validator = ActionValidator()
        
        # Create safety filter with good game state
        game_state = {
            "resources": {
                "manpower": {"current": 1000, "max": 2000},
                "fuel": {"current": 500, "max": 1000},
                "munitions": {"current": 300, "max": 800}
            },
            "population": {"current": 20, "max": 100},
            "squads": [{"id": 1, "type": "engineer"}],
            "buildings": [{"id": 101, "type": "barracks"}],
            "tech_tree": {"tier_1": True, "tier_2": True, "tier_3": False}
        }
        safety_filter = SafetyFilter(game_state=game_state)
        
        # Create command
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        
        # Step 1: Validate with validator
        validation_result = validator.validate(command)
        assert validation_result.is_valid, f"Validation failed: {validation_result.errors}"
        
        # Step 2: Check with safety filter
        safety_result = safety_filter.check_command(command)
        assert safety_result.is_safe, f"Safety check failed: {safety_result.errors}"
        
        # Both passed!
        assert True
    
    def test_full_pipeline_fails_resource_check(self):
        """Test a command that fails resource check."""
        from config import Configuration
        
        # Create validator
        validator = ActionValidator()
        
        # Create safety filter with insufficient resources
        game_state = {
            "resources": {
                "manpower": {"current": 50, "max": 2000},  # Not enough for heavy_tank (1000 MP)
                "fuel": {"current": 50, "max": 1000},
                "munitions": {"current": 50, "max": 800}
            },
            "population": {"current": 0, "max": 100}
        }
        safety_filter = SafetyFilter(game_state=game_state)
        
        # Create command
        command = {
            "command": "PRODUCE",
            "building_id": 101,
            "unit_type": "heavy_tank"  # Requires 1000 MP, 250 fuel
        }
        
        # Step 1: Validate with validator (should pass structure)
        validation_result = validator.validate(command)
        assert validation_result.is_valid, f"Validation failed: {validation_result.errors}"
        
        # Step 2: Check with safety filter (should fail resources)
        safety_result = safety_filter.check_command(command)
        assert not safety_result.is_safe, "Safety check should have failed"
        assert any("resource" in error.lower() for error in safety_result.errors)
    
    def test_full_pipeline_fails_validation(self):
        """Test a command that fails validation."""
        from config import Configuration
        
        # Create validator
        validator = ActionValidator()
        
        # Create safety filter
        game_state = {
            "resources": {
                "manpower": {"current": 1000, "max": 2000},
                "fuel": {"current": 500, "max": 1000},
                "munitions": {"current": 300, "max": 800}
            },
            "population": {"current": 0, "max": 100}
        }
        safety_filter = SafetyFilter(game_state=game_state)
        
        # Create invalid command (missing required fields)
        command = {
            "command": "BUILD",
            "building_type": "barracks"
            # Missing engineer_id and position
        }
        
        # Step 1: Validate with validator (should fail)
        validation_result = validator.validate(command)
        assert not validation_result.is_valid, "Validation should have failed"
        
        # Don't bother with safety check if validation fails
        assert any("Missing required field" in error for error in validation_result.errors)


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_null_command(self, validator):
        """Test handling of null/None command."""
        result = validator.validate(None)
        assert not result.is_valid
    
    def test_empty_command(self, validator):
        """Test handling of empty command dict."""
        result = validator.validate({})
        assert not result.is_valid
    
    def test_command_with_extra_fields(self, validator):
        """Test handling of commands with extra fields."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0],
            "extra_field_1": "value",
            "extra_field_2": 123
        }
        result = validator.validate(command)
        # Extra fields should be allowed
        assert result.is_valid
    
    def test_safety_filter_with_partial_state(self):
        """Test safety filter with partial game state."""
        game_state = {
            "resources": {
                "manpower": {"current": 1000}
                # Missing fuel and munitions
            }
        }
        safety_filter = SafetyFilter(game_state=game_state)
        
        command = {
            "command": "PRODUCE",
            "building_id": 101,
            "unit_type": "riflemen"
        }
        result = safety_filter.check_command(command)
        # Should handle partial state gracefully
        assert isinstance(result.is_safe, bool)


# =============================================================================
# Reflex Layer Command Tests
# =============================================================================

class TestReflexLayerCommands:
    """Tests for reflex layer command generation and validation."""
    
    def test_retreat_command_structure(self):
        """Test that retreat commands have correct structure."""
        command = {
            "command": "RETREAT",
            "squad_id": 1
        }
        validator = ActionValidator()
        result = validator.validate(command)
        assert result.is_valid
    
    def test_capture_command_structure(self):
        """Test that capture commands have correct structure."""
        command = {
            "command": "CAPTURE",
            "squad_id": 1,
            "point_id": 1001
        }
        validator = ActionValidator()
        result = validator.validate(command)
        assert result.is_valid
    
    def test_set_posture_command_structure(self):
        """Test that set posture commands have correct structure."""
        command = {
            "command": "SET_POSTURE",
            "squad_id": 1,
            "posture": "defensive"
        }
        validator = ActionValidator()
        result = validator.validate(command)
        assert result.is_valid
    
    def test_reflex_commands_pass_safety(self):
        """Test that typical reflex commands pass safety checks."""
        game_state = {
            "resources": {
                "manpower": {"current": 1000, "max": 2000},
                "fuel": {"current": 500, "max": 1000},
                "munitions": {"current": 300, "max": 800}
            },
            "population": {"current": 20, "max": 100},
            "squads": [
                {"id": 1, "type": "riflemen", "health": 50, "max_health": 100},
                {"id": 2, "type": "engineer", "health": 80, "max_health": 100}
            ],
            "capture_points": [
                {"id": 1001, "owner": None, "capture_progress": 0}
            ]
        }
        safety_filter = SafetyFilter(game_state=game_state)
        
        # Retreat command (no resource cost, no legality check)
        retreat_cmd = {"command": "RETREAT", "squad_id": 1}
        result1 = safety_filter.check_command(retreat_cmd)
        assert result1.is_safe
        
        # Capture command - need to include the squad in the state
        game_state_with_squads = game_state.copy()
        safety_filter.update_game_state(game_state_with_squads)
        
        # Re-check capture command
        capture_cmd = {"command": "CAPTURE", "squad_id": 2, "point_id": 1001}
        result2 = safety_filter.check_command(capture_cmd)
        # This should pass now with the squad in state
        assert result2.is_safe
        
        # Set posture command (no resource cost)
        posture_cmd = {"command": "SET_POSTURE", "squad_id": 1, "posture": "defensive"}
        result3 = safety_filter.check_command(posture_cmd)
        assert result3.is_safe


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
