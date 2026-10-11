"""
Unit Tests for Logger Module

Tests the state logging and log parsing functionality.
"""

import json
import tempfile
import os
import time
from pathlib import Path
import pytest

# Add parent directory to Python path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from logger import StateLogger, LogParser, LogRotator, LogConfig


class TestLogConfig:
    """Test log configuration."""
    
    def test_log_config_defaults(self):
        """Test default log configuration values."""
        config = LogConfig()
        
        assert config.log_dir == "coh1ai_data"
        assert config.state_log_file == "states.jsonl"
        assert config.command_log_file == "commands.jsonl"
        assert config.error_log_file == "errors.log"
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.max_backups == 5
    
    def test_log_config_from_config(self):
        """Test creating log config from main configuration."""
        from config import Configuration
        config = Configuration()
        log_config = LogConfig.from_config(config)
        
        assert log_config is not None
        assert log_config.log_dir is not None


class TestLogRotator:
    """Test log file rotator."""
    
    def test_rotator_creation(self):
        """Test creating log rotator."""
        with tempfile.TemporaryDirectory() as temp_dir:
            rotator = LogRotator(temp_dir, max_size=100, max_backups=3)
            assert rotator is not None
            assert rotator.max_size == 100
            assert rotator.max_backups == 3
    
    def test_rotator_ensure_dir(self):
        """Test that rotator creates directory if needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            subdir = Path(temp_dir) / "logs"
            rotator = LogRotator(subdir, max_size=100, max_backups=3)
            
            # Directory should be created
            assert subdir.exists()
    
    def test_should_rotate_false(self):
        """Test should_rotate returns False for small file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            rotator = LogRotator(temp_dir, max_size=100, max_backups=3)
            
            # File doesn't exist
            assert rotator.should_rotate(log_file) == False
            
            # Create small file
            log_file.write_text("small")
            assert rotator.should_rotate(log_file) == False
    
    def test_should_rotate_true(self):
        """Test should_rotate returns True for large file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            rotator = LogRotator(temp_dir, max_size=100, max_backups=3)
            
            # Create large file
            log_file.write_text("x" * 200)  # 200 bytes > 100 max
            assert rotator.should_rotate(log_file) == True
    
    def test_rotate_file(self):
        """Test rotating a log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            rotator = LogRotator(temp_dir, max_size=100, max_backups=3)
            
            # Create a file that needs rotation
            log_file.write_text("x" * 200)
            
            # Rotate it
            assert rotator.rotate(log_file)
            
            # Original file should not exist
            assert not log_file.exists()
            
            # Backup file should exist
            backup_file = Path(temp_dir) / "test.1.log"
            assert backup_file.exists()
            assert backup_file.read_text() == "x" * 200
    
    def test_rotate_multiple_times(self):
        """Test rotating multiple times creates numbered backups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            rotator = LogRotator(temp_dir, max_size=100, max_backups=3)
            
            # Write initial content
            log_file.write_text("content1")
            
            # First rotation
            assert rotator.rotate(log_file)
            
            # Write new content
            log_file.write_text("content2")
            
            # Second rotation
            assert rotator.rotate(log_file)
            
            # Check backups exist
            assert (Path(temp_dir) / "test.1.log").exists()
            assert (Path(temp_dir) / "test.2.log").exists()
    
    def test_rotate_max_backups(self):
        """Test that oldest backups are removed when max is reached."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            rotator = LogRotator(temp_dir, max_size=100, max_backups=2)
            
            # Create and rotate multiple times
            for i in range(5):
                log_file.write_text(f"content{i}")
                rotator.rotate(log_file)
            
            # Only the 2 most recent backups should exist
            assert (Path(temp_dir) / "test.1.log").exists()
            assert (Path(temp_dir) / "test.2.log").exists()
            assert not (Path(temp_dir) / "test.3.log").exists()


class TestStateLogger:
    """Test state logger."""
    
    def test_state_logger_creation(self):
        """Test creating state logger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            config._config["debug"]["state_log_file"] = "test_states.jsonl"
            
            logger = StateLogger(config)
            assert logger is not None
            assert logger.log_dir.exists()
    
    def test_log_state_dict(self):
        """Test logging a state as dictionary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            
            logger = StateLogger(config)
            
            # Log a state
            state = {"player_id": 1, "timestamp": 123.456}
            assert logger.log_state(state)
            
            # Check file exists and contains data
            state_file = logger.log_dir / logger.state_log_file
            assert state_file.exists()
            
            content = state_file.read_text()
            assert "player_id" in content
            assert "123.456" in content
    
    def test_log_state_object(self):
        """Test logging a GameState object."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            from schema import GameState, PopulationData
            
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            
            logger = StateLogger(config)
            
            # Create a GameState
            state = GameState(
                version="1.0",
                player_id=1,
                timestamp=123.456,
                population=PopulationData(current=20, max=100)
            )
            
            # Log it
            assert logger.log_state(state)
            
            # Check it was serialized
            state_file = logger.log_dir / logger.state_log_file
            content = state_file.read_text()
            assert "player_id" in content or "player" in content
    
    def test_log_command(self):
        """Test logging a command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            
            logger = StateLogger(config)
            
            # Log a command
            command = {"command": "BUILD", "building": "barracks"}
            assert logger.log_command(command)
            
            # Check file exists
            command_file = logger.log_dir / logger.command_log_file
            assert command_file.exists()
            
            content = command_file.read_text()
            assert "BUILD" in content
    
    def test_log_batch(self):
        """Test logging multiple states at once."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            
            logger = StateLogger(config)
            
            # Log multiple states
            states = [
                {"player_id": 1, "time": 100},
                {"player_id": 1, "time": 200},
                {"player_id": 1, "time": 300}
            ]
            
            count = logger.log_batch(states)
            assert count == 3
    
    def test_get_stats(self):
        """Test getting logger statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            
            logger = StateLogger(config)
            
            # Log some data
            logger.log_state({"player_id": 1})
            logger.log_state({"player_id": 1})
            logger.log_command({"command": "TEST"})
            
            stats = logger.get_stats()
            assert stats["states_logged"] == 2
            assert stats["commands_logged"] == 1
    
    def test_reset_stats(self):
        """Test resetting logger statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            
            logger = StateLogger(config)
            
            # Log some data
            logger.log_state({"player_id": 1})
            logger.reset_stats()
            
            stats = logger.get_stats()
            assert stats["states_logged"] == 0


class TestLogParser:
    """Test log parser."""
    
    def test_parser_creation(self):
        """Test creating log parser."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = LogParser(temp_dir)
            assert parser is not None
    
    def test_parse_state_log(self):
        """Test parsing state log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "states.jsonl"
            
            # Write some states
            with open(state_file, 'w') as f:
                f.write(json.dumps({"player_id": 1, "time": 100}) + "\n")
                f.write(json.dumps({"player_id": 1, "time": 200}) + "\n")
            
            parser = LogParser(temp_dir)
            states = parser.parse_state_log(state_file)
            
            assert len(states) == 2
            assert states[0]["player_id"] == 1
            assert states[0]["time"] == 100
    
    def test_parse_empty_state_log(self):
        """Test parsing empty state log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = LogParser(temp_dir)
            states = parser.parse_state_log()
            
            assert states == []
    
    def test_parse_command_log(self):
        """Test parsing command log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            command_file = Path(temp_dir) / "commands.jsonl"
            
            # Write some commands
            with open(command_file, 'w') as f:
                f.write(json.dumps({"command": "BUILD"}) + "\n")
                f.write(json.dumps({"command": "ATTACK"}) + "\n")
            
            parser = LogParser(temp_dir)
            commands = parser.parse_command_log(command_file)
            
            assert len(commands) == 2
            assert commands[0]["command"] == "BUILD"
    
    def test_parse_error_log(self):
        """Test parsing error log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            error_file = Path(temp_dir) / "errors.log"
            
            # Write some errors
            with open(error_file, 'w') as f:
                f.write("[2026-01-01] Error 1\n")
                f.write("[2026-01-02] Error 2\n")
            
            parser = LogParser(temp_dir)
            errors = parser.parse_error_log(error_file)
            
            assert len(errors) == 2
            assert "Error 1" in errors[0]
    
    def test_get_all_logs(self):
        """Test getting all logs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create state log
            state_file = Path(temp_dir) / "states.jsonl"
            with open(state_file, 'w') as f:
                f.write(json.dumps({"player_id": 1}) + "\n")
            
            # Create command log
            command_file = Path(temp_dir) / "commands.jsonl"
            with open(command_file, 'w') as f:
                f.write(json.dumps({"command": "BUILD"}) + "\n")
            
            # Create error log
            error_file = Path(temp_dir) / "errors.log"
            with open(error_file, 'w') as f:
                f.write("Error 1\n")
            
            parser = LogParser(temp_dir)
            logs = parser.get_all_logs()
            
            assert len(logs["states"]) == 1
            assert len(logs["commands"]) == 1
            assert len(logs["errors"]) == 1
    
    def test_get_match_summary(self):
        """Test getting match summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "states.jsonl"
            
            # Write states at different times
            with open(state_file, 'w') as f:
                f.write(json.dumps({"player_id": 1, "_log_timestamp": 100.0, "resources": {"manpower": {"current": 500}}, "squads": [{"id": 1}], "cps": [{"id": 1}], "pop": [20, 100]}) + "\n")
                f.write(json.dumps({"player_id": 1, "_log_timestamp": 200.0, "resources": {"manpower": {"current": 800}}, "squads": [{"id": 1}, {"id": 2}], "cps": [{"id": 1}], "pop": [40, 100]}) + "\n")
            
            parser = LogParser(temp_dir)
            summary = parser.get_match_summary()
            
            assert summary["states_count"] == 2
            assert summary["duration"] > 0
            assert summary["max_squads"] == 2
            assert summary["final_squads"] == 2
    
    def test_filter_by_time(self):
        """Test filtering logs by time range."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "states.jsonl"
            
            # Write states at different times
            with open(state_file, 'w') as f:
                f.write(json.dumps({"player_id": 1, "_log_timestamp": 100.0}) + "\n")
                f.write(json.dumps({"player_id": 1, "_log_timestamp": 200.0}) + "\n")
                f.write(json.dumps({"player_id": 1, "_log_timestamp": 300.0}) + "\n")
            
            parser = LogParser(temp_dir)
            filtered = parser.filter_by_time(150.0, 250.0)
            
            # Should only get the state at 200.0
            assert len(filtered["states"]) == 1


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
