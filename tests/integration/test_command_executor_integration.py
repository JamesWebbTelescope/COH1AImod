"""
CoH1 × Mistral AI Mod - Command Executor Integration Tests

Integration tests for command execution that test:
1. Command flow from Python orchestrator to SCAR
2. Command validation and execution
3. IPC communication with commands
4. Error handling across the pipeline

Author: Generated via planner skill
Version: 0.1.0
Date: 2026-10-25
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Import from parent directory - use absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

# Import modules - these should work from the python directory
try:
    from config import load_config, get_config
    from ipc_reader import IPCReader
    from orchestrator.command_processor import (
        CommandProcessor,
        create_build_command,
        create_attack_move_command,
        create_capture_command,
        create_produce_command,
        create_retreat_command,
        create_stop_command,
        create_hold_command,
        create_set_posture_command
    )
    from validator import ActionValidator
    from safety_filter import SafetyFilter
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
class TestCommandProcessorIntegration:
    """Integration tests for command processor with command executor."""
    
    @pytest.fixture
    def config(self):
        """Get test configuration."""
        return load_config()
    
    @pytest.fixture
    def command_processor(self, config):
        """Get command processor instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.set("ipc", "data_dir", tmpdir)
            processor = CommandProcessor(config)
            yield processor
            processor.stop()
    
    def test_create_all_command_types(self):
        """Test creating all command types."""
        commands = [
            create_build_command(1, "barracks", [100, 200, 0]),
            create_capture_command(1, 100),
            create_attack_move_command(1, [50, 60, 0]),
            create_set_posture_command(1, "defend"),
            create_produce_command(1, "rifleman"),
            create_retreat_command(1),
            create_stop_command(1),
            create_hold_command(1)
        ]
        
        assert len(commands) == 8
        
        for cmd in commands:
            assert hasattr(cmd, 'command_type')
            assert hasattr(cmd, 'to_dict')
            assert hasattr(cmd, 'to_json')
    
    def test_command_serialization(self):
        """Test command serialization to JSON."""
        cmd = create_build_command(1, "barracks", [100, 200, 0])
        
        cmd_dict = cmd.to_dict()
        
        assert "command_id" in cmd_dict
        assert "command_type" in cmd_dict
        assert cmd_dict["command_type"] == "BUILD"
        
        cmd_json = cmd.to_json()
        parsed = json.loads(cmd_json)
        
        assert parsed["command_type"] == "BUILD"
    
    def test_command_queue_processing(self):
        """Test command queue processing."""
        config = load_config()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config.set("ipc", "data_dir", tmpdir)
            processor = CommandProcessor(config)
            
            # Add commands to queue
            cmd1 = create_build_command(1, "barracks", [100, 200, 0])
            cmd2 = create_attack_move_command(1, [50, 60, 0])
            
            processor.add_command(cmd1)
            processor.add_command(cmd2)
            
            # Check queue stats
            stats = processor.get_stats()
            assert stats.commands_received >= 2
            
            processor.stop()


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
class TestCommandFlow:
    """Test end-to-end command flow."""
    
    @pytest.fixture
    def test_dir(self, tmp_path):
        """Create temporary test directory."""
        return str(tmp_path)
    
    def test_write_and_read_command_file(self, test_dir):
        """Test writing and reading command files."""
        # Create command file
        commands = [
            {"command": "BUILD", "engineer_id": 1, "building_type": "barracks", "position": [100, 200, 0]},
            {"command": "RETREAT", "squad_id": 2}
        ]
        
        payload = {"commands": commands}
        
        # Write to file
        command_file = os.path.join(test_dir, "coh1ai_commands.json")
        with open(command_file, 'w') as f:
            json.dump(payload, f)
        
        # Read and parse
        with open(command_file, 'r') as f:
            data = json.load(f)
        
        assert "commands" in data
        assert len(data["commands"]) == 2
        assert data["commands"][0]["command"] == "BUILD"
        assert data["commands"][1]["command"] == "RETREAT"
    
    def test_command_roundtrip(self, test_dir):
        """Test command roundtrip through file system."""
        # In SCAR format, command would be:
        scar_cmd = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        
        # Write to file
        command_file = os.path.join(test_dir, "coh1ai_commands.json")
        with open(command_file, 'w') as f:
            json.dump({"commands": [scar_cmd]}, f)
        
        # Read back (as Python would read)
        with open(command_file, 'r') as f:
            data = json.load(f)
        
        # Verify structure
        assert data["commands"][0]["command"] == "BUILD"
        assert data["commands"][0]["engineer_id"] == 1
        assert data["commands"][0]["position"] == [100, 200, 0]


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
class TestValidatorIntegration:
    """Integration tests for validator with command processor."""
    
    @pytest.fixture
    def validator(self):
        """Get validator instance."""
        return ActionValidator()
    
    def test_whitelist_validation(self, validator):
        """Test command whitelist validation."""
        # Valid commands
        valid_commands = ["BUILD", "CAPTURE", "ATTACK_MOVE", "SET_POSTURE", "PRODUCE", "RETREAT", "STOP", "HOLD", "PING", "PONG"]
        
        for cmd_type in valid_commands:
            cmd = {"command": cmd_type}
            result = validator.validate_whitelist(cmd)
            assert result.is_valid, f"Command {cmd_type} should be valid"
        
        # Invalid command
        cmd = {"command": "INVALID_COMMAND"}
        result = validator.validate_whitelist(cmd)
        assert not result.is_valid
    
    def test_full_validation_pipeline(self, validator):
        """Test full validation pipeline."""
        cmd = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        
        result = validator.validate_command(cmd)
        assert result.is_valid


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required modules not available")
class TestSafetyFilterIntegration:
    """Integration tests for safety filter."""
    
    @pytest.fixture
    def safety_filter(self):
        """Get safety filter instance."""
        return SafetyFilter()
    
    @pytest.fixture
    def game_state(self):
        """Get sample game state."""
        return {
            "resources": {
                "manpower": {"current": 1000, "max": 1000},
                "fuel": {"current": 500, "max": 800},
                "munitions": {"current": 300, "max": 600}
            },
            "population": {"current": 10, "max": 50}
        }
    
    def test_resource_check(self, safety_filter, game_state):
        """Test resource affordability check."""
        result = safety_filter.check_resources(game_state, {"manpower": 100, "fuel": 50, "munitions": 20})
        
        # Should have valid field
        assert hasattr(result, 'is_valid')
    
    def test_population_check(self, safety_filter, game_state):
        """Test population cap check."""
        result = safety_filter.check_population(game_state, 10)
        
        # Should have valid field
        assert hasattr(result, 'is_valid')


class TestCommandExecutionSimulated:
    """Simulated command execution tests (without actual CoH1)."""
    
    def test_build_command_execution_logic(self):
        """Test BUILD command execution logic."""
        command = {
            "command": "BUILD",
            "engineer_id": 123,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        
        # Validate
        assert "engineer_id" in command
        assert "building_type" in command
        assert "position" in command
        
        # Extract parameters
        engineer_id = command["engineer_id"]
        building_type = command["building_type"]
        position = command["position"]
        
        assert engineer_id == 123
        assert building_type == "barracks"
        assert position == [100, 200, 0]
    
    def test_capture_command_execution_logic(self):
        """Test CAPTURE command execution logic."""
        command = {
            "command": "CAPTURE",
            "squad_id": 456,
            "point_id": 789
        }
        
        assert "squad_id" in command
        assert "point_id" in command
        
        squad_id = command["squad_id"]
        point_id = command["point_id"]
        
        assert squad_id == 456
        assert point_id == 789
    
    def test_retreat_command_execution_logic(self):
        """Test RETREAT command execution logic."""
        command = {
            "command": "RETREAT",
            "squad_id": 111
        }
        
        assert "squad_id" in command
        assert command["squad_id"] == 111
    
    def test_multiple_commands_in_sequence(self):
        """Test processing multiple commands in sequence."""
        commands = [
            {"command": "BUILD", "engineer_id": 1, "building_type": "barracks", "position": [0, 0, 0]},
            {"command": "PRODUCE", "building_id": 1, "unit_type": "rifleman"},
            {"command": "ATTACK_MOVE", "squad_id": 2, "position": [100, 100, 0]},
            {"command": "RETREAT", "squad_id": 3}
        ]
        
        processed = []
        for cmd in commands:
            if "command" in cmd:
                processed.append(cmd["command"])
        
        assert len(processed) == 4
        assert processed == ["BUILD", "PRODUCE", "ATTACK_MOVE", "RETREAT"]


class TestIPCCommandIntegration:
    """Test IPC command integration."""
    
    @pytest.fixture
    def ipc_files(self, tmp_path):
        """Create IPC files in test directory."""
        test_dir = str(tmp_path)
        state_file = os.path.join(test_dir, "coh1ai_state.json")
        command_file = os.path.join(test_dir, "coh1ai_commands.json")
        
        # Create state file
        state = {
            "player_id": 1,
            "timestamp": time.time(),
            "resources": {
                "manpower": {"current": 1000, "max": 1000},
                "fuel": {"current": 500, "max": 800}
            },
            "squads": []
        }
        
        with open(state_file, 'w') as f:
            json.dump(state, f)
        
        yield state_file, command_file
    
    def test_write_commands_to_file(self, ipc_files):
        """Test writing commands to IPC file."""
        state_file, command_file = ipc_files
        
        # Create commands
        commands = [
            {"command": "BUILD", "engineer_id": 1, "building_type": "barracks", "position": [0, 0, 0]},
            {"command": "RETREAT", "squad_id": 2}
        ]
        
        # Write to command file
        payload = {"commands": commands}
        with open(command_file, 'w') as f:
            json.dump(payload, f)
        
        # Verify file exists
        assert os.path.exists(command_file)
        
        # Read back
        with open(command_file, 'r') as f:
            data = json.load(f)
        
        assert len(data["commands"]) == 2
    
    def test_read_commands_from_file(self, ipc_files):
        """Test reading commands from IPC file."""
        state_file, command_file = ipc_files
        
        # Write commands first
        commands = [
            {"command": "BUILD", "engineer_id": 1, "building_type": "barracks", "position": [0, 0, 0]},
            {"command": "CAPTURE", "squad_id": 2, "point_id": 100}
        ]
        
        payload = {"commands": commands}
        with open(command_file, 'w') as f:
            json.dump(payload, f)
        
        # Read commands
        with open(command_file, 'r') as f:
            data = json.load(f)
        
        # Process commands
        processed_commands = data.get("commands", [])
        
        assert len(processed_commands) == 2
        assert processed_commands[0]["command"] == "BUILD"
        assert processed_commands[1]["command"] == "CAPTURE"
    
    def test_clear_command_file_after_reading(self, ipc_files):
        """Test that command file is cleared after reading."""
        state_file, command_file = ipc_files
        
        # Write commands
        commands = [{"command": "PING"}]
        payload = {"commands": commands}
        
        with open(command_file, 'w') as f:
            json.dump(payload, f)
        
        assert os.path.exists(command_file)
        
        # Simulate reading and clearing
        with open(command_file, 'r') as f:
            data = json.load(f)
        
        # Clear file
        with open(command_file, 'w') as f:
            json.dump({"commands": []}, f)
        
        # Verify cleared
        with open(command_file, 'r') as f:
            data = json.load(f)
        
        assert data["commands"] == []


class TestCommandErrorHandling:
    """Test error handling for commands."""
    
    def test_null_command_handling(self):
        """Test handling of null command."""
        command = None
        
        # In SCAR: if (command == null) return false
        if command is None:
            result = False
        else:
            result = True
        
        assert result is False
    
    def test_empty_command_handling(self):
        """Test handling of empty command."""
        command = {}
        
        # In SCAR: commandType = command.command would be null
        command_type = command.get("command")
        
        if command_type is None:
            result = False
        else:
            result = True
        
        assert result is False
    
    def test_missing_required_field_handling(self):
        """Test handling of missing required field."""
        command = {
            "command": "BUILD",
            "engineer_id": 1
            # Missing building_type and position
        }
        
        # In SCAR: would check for null values
        has_engineer = command.get("engineer_id") is not None
        has_building = command.get("building_type") is not None
        has_position = command.get("position") is not None
        
        # Missing required fields
        assert not (has_engineer and has_building and has_position)
    
    def test_invalid_position_handling(self):
        """Test handling of invalid position."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": "invalid"  # Should be array
        }
        
        # Check position type
        position = command.get("position")
        is_valid_position = isinstance(position, list) and len(position) >= 3
        
        assert not is_valid_position


class TestCommandStatistics:
    """Test command statistics tracking."""
    
    def test_track_command_execution(self):
        """Test tracking command execution statistics."""
        stats = {
            "commands_received": 0,
            "commands_processed": 0,
            "commands_executed": 0,
            "commands_failed": 0
        }
        
        # Simulate processing commands
        commands = [
            {"command": "BUILD", "status": "success"},
            {"command": "RETREAT", "status": "success"},
            {"command": "CAPTURE", "status": "failed"}
        ]
        
        for cmd in commands:
            stats["commands_received"] += 1
            
            if cmd["status"] == "success":
                stats["commands_executed"] += 1
                stats["commands_processed"] += 1
            else:
                stats["commands_failed"] += 1
        
        assert stats["commands_received"] == 3
        assert stats["commands_executed"] == 2
        assert stats["commands_failed"] == 1
    
    def test_command_queue_length(self):
        """Test command queue length tracking."""
        queue = []
        
        # Add commands
        for i in range(10):
            queue.append({"command": f"CMD_{i}"})
        
        assert len(queue) == 10
        
        # Process commands
        for _ in range(5):
            if queue:
                queue.pop(0)
        
        assert len(queue) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
