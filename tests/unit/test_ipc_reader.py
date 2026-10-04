"""
Unit Tests for IPC Reader Module

Tests the file-based IPC communication system.
"""

import json
import tempfile
import os
import time
import threading
from pathlib import Path
import pytest

# Add parent directory to Python path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from ipc_reader import IPCReader, IPCMessage, IPCStats, IPCStatus, FileLock


class TestIPCReaderBasics:
    """Test basic IPC reader functionality."""
    
    def test_ipc_reader_creation(self):
        """Test that IPC reader can be created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a custom config with temp directory
            config_data = {
                "ipc": {
                    "state_file": "test_state.json",
                    "command_file": "test_commands.json",
                    "lock_file": "test_lock.tmp",
                    "data_dir": temp_dir,
                    "poll_interval": 0.01,
                    "max_retries": 2
                },
                "mod": {"version": "1.0.0"},
                "game": {"faction": "allies"},
                "mistral": {"api_url": "http://test.com"},
                "debug": {"enabled": False}
            }
            
            # Write config to file
            config_path = Path(temp_dir) / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
            
            # Import Configuration to read our test config
            from config import Configuration
            config = Configuration()
            config._config = config_data
            
            # Create IPC reader
            ipc = IPCReader(config)
            assert ipc is not None
            assert ipc.poll_interval == 0.01
            assert ipc.max_retries == 2
    
    def test_ipc_reader_default_paths(self):
        """Test IPC reader with default configuration."""
        # Create IPC reader with defaults
        from config import Configuration
        config = Configuration()
        ipc = IPCReader(config)
        
        # Should have default paths
        assert "state.json" in str(ipc.state_file).lower() or "state" in str(ipc.state_file).lower()
        assert "command" in str(ipc.command_file).lower()
        assert "lock" in str(ipc.lock_file).lower()


class TestFileLock:
    """Test file-based locking mechanism."""
    
    def test_file_lock_acquire_and_release(self):
        """Test acquiring and releasing file lock."""
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = Path(temp_dir) / "test.lock"
            
            # Should be able to acquire lock
            with FileLock(lock_file, timeout=0.1) as lock:
                assert lock.acquired
                assert lock_file.exists()
                
            # Lock should be released after context exit
            assert not lock.acquired
            assert not lock_file.exists()
    
    def test_file_lock_timeout(self):
        """Test file lock timeout."""
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = Path(temp_dir) / "test.lock"
            
            # Create the lock file manually
            lock_file.touch()
            
            # Should timeout when trying to acquire existing lock
            with pytest.raises(TimeoutError):
                with FileLock(lock_file, timeout=0.01):
                    pass  # Should not reach here


class TestIPCReaderFileOperations:
    """Test IPC reader file operations."""
    
    def test_read_state_file(self):
        """Test reading state from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"
            
            # Write test state
            test_state = {
                "player_id": 1,
                "timestamp": 123.456,
                "resources": {"manpower": 500, "fuel": 300},
                "squads": [{"id": 1, "type": "riflemen", "health": 0.8}]
            }
            
            with open(state_file, 'w') as f:
                json.dump(test_state, f)
            
            # Create IPC reader
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["state_file"] = str(state_file)
            config._config["ipc"]["data_dir"] = temp_dir
            
            ipc = IPCReader(config)
            
            # Read state
            state_data = ipc._read_state_file()
            assert state_data is not None
            assert state_data["player_id"] == 1
            assert state_data["resources"]["manpower"] == 500
            assert len(state_data["squads"]) == 1
    
    def test_read_empty_state_file(self):
        """Test reading empty state file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "empty.json"
            state_file.touch()  # Create empty file
            
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["state_file"] = str(state_file)
            config._config["ipc"]["data_dir"] = temp_dir
            
            ipc = IPCReader(config)
            state_data = ipc._read_state_file()
            assert state_data is None
    
    def test_read_invalid_json(self):
        """Test reading invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "invalid.json"
            
            with open(state_file, 'w') as f:
                f.write("{invalid json}")
            
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["state_file"] = str(state_file)
            config._config["ipc"]["data_dir"] = temp_dir
            
            ipc = IPCReader(config)
            state_data = ipc._read_state_file()
            assert state_data is None
    
    def test_send_command(self):
        """Test sending a command to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            command_file = Path(temp_dir) / "commands.json"
            
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["command_file"] = str(command_file)
            config._config["ipc"]["data_dir"] = temp_dir
            
            ipc = IPCReader(config)
            
            # Start the IPC reader
            assert ipc.start()
            
            # Send command
            test_command = {"command": "TEST", "squad_id": 1}
            assert ipc.send_command(test_command)
            
            # Verify file exists and contains command
            assert command_file.exists()
            
            with open(command_file, 'r') as f:
                content = f.read()
                data = json.loads(content)
                assert "commands" in data
                assert len(data["commands"]) == 1
                assert data["commands"][0]["command"] == "TEST"
    
    def test_send_multiple_commands(self):
        """Test sending multiple commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            command_file = Path(temp_dir) / "commands.json"
            
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["command_file"] = str(command_file)
            config._config["ipc"]["data_dir"] = temp_dir
            
            ipc = IPCReader(config)
            
            # Start the IPC reader
            assert ipc.start()
            
            # Send multiple commands
            commands = [
                {"command": "BUILD", "building": "barracks"},
                {"command": "PRODUCE", "unit": "riflemen"}
            ]
            assert ipc.send_commands(commands)
            
            # Verify commands
            with open(command_file, 'r') as f:
                content = f.read()
                data = json.loads(content)
                # The send_commands method wraps the commands in a command_data dict
                assert len(data["commands"]) == 2


class TestIPCStats:
    """Test IPC statistics tracking."""
    
    def test_ipc_stats_initialization(self):
        """Test IPC stats initialization."""
        stats = IPCStats()
        
        assert stats.messages_received == 0
        assert stats.messages_sent == 0
        assert stats.bytes_received == 0
        assert stats.bytes_sent == 0
        assert stats.read_errors == 0
        assert stats.write_errors == 0
    
    def test_ipc_stats_to_dict(self):
        """Test IPC stats to dictionary conversion."""
        stats = IPCStats()
        stats.messages_received = 10
        stats.messages_sent = 5
        
        stats_dict = stats.to_dict()
        
        assert stats_dict["messages_received"] == 10
        assert stats_dict["messages_sent"] == 5
    
    def test_ipc_reader_stats(self):
        """Test that IPC reader tracks stats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            
            ipc = IPCReader(config)
            
            # Stats should be initialized
            stats = ipc.get_stats()
            assert stats.messages_received == 0
            assert stats.messages_sent == 0


class TestIPCMessage:
    """Test IPC message class."""
    
    def test_ipc_message_creation(self):
        """Test creating IPC message."""
        data = {"player_id": 1, "timestamp": 123.456}
        message = IPCMessage(timestamp=123.456, data=data, message_type="state")
        
        assert message.timestamp == 123.456
        assert message.data == data
        assert message.message_type == "state"
    
    def test_ipc_message_default_type(self):
        """Test IPC message with default type."""
        message = IPCMessage(timestamp=123.456, data={})
        assert message.message_type == "state"


class TestIPCReaderLifecycle:
    """Test IPC reader lifecycle (start/stop)."""
    
    def test_start_stop_ipc_reader(self):
        """Test starting and stopping IPC reader."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            config._config["ipc"]["poll_interval"] = 0.01
            
            ipc = IPCReader(config)
            
            # Start
            assert ipc.start()
            assert ipc.running
            assert ipc.status == IPCStatus.DISCONNECTED  # Not connected until first message
            
            # Give it a moment to process
            time.sleep(0.1)
            
            # Stop
            assert ipc.stop()
            assert not ipc.running
    
    def test_double_start(self):
        """Test starting IPC reader twice."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            config._config["ipc"]["poll_interval"] = 0.01
            
            ipc = IPCReader(config)
            
            assert ipc.start()
            # Second start should fail
            assert not ipc.start()
            
            ipc.stop()
    
    def test_stop_without_start(self):
        """Test stopping IPC reader without starting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from config import Configuration
            config = Configuration()
            config._config["ipc"]["data_dir"] = temp_dir
            
            ipc = IPCReader(config)
            
            # Stop without start should succeed
            assert ipc.stop()


class TestIPCDataClasses:
    """Test IPC data classes."""
    
    def test_ipc_status_enum(self):
        """Test IPC status enum."""
        assert IPCStatus.DISCONNECTED.value != IPCStatus.CONNECTED.value
        assert IPCStatus.CONNECTED.value != IPCStatus.ERROR.value
        assert IPCStatus.DISCONNECTED.value != IPCStatus.ERROR.value
    
    def test_ipc_status_values(self):
        """Test IPC status values are unique."""
        values = [s.value for s in IPCStatus]
        assert len(values) == len(set(values))  # All unique


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
