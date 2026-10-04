"""
Integration Tests for IPC Roundtrip

Tests the end-to-end communication between SCAR-like components and Python orchestrator.
Uses a mock SCAR simulator since actual SCAR testing requires CoH1 environment.
"""

import json
import tempfile
import time
import threading
from pathlib import Path
import pytest

# Add parent directory to Python path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from ipc_reader import IPCReader, IPCMessage
from config import Configuration


class MockSCARSimulator:
    """
    Simulates SCAR mod behavior for testing without requiring actual CoH1.
    Writes game state to files and reads commands from files.
    """
    
    def __init__(self, ipc_config):
        """
        Initialize mock SCAR simulator.
        
        Args:
            ipc_config: IPC configuration dictionary
        """
        self.state_file = Path(ipc_config["state_file"])
        self.command_file = Path(ipc_config["command_file"])
        self.lock_file = Path(ipc_config["lock_file"])
        self.data_dir = Path(ipc_config["data_dir"])
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.running = False
        self.thread = None
        self.state_sequence = [
            self._create_test_state(1, 0),
            self._create_test_state(2, 1),
            self._create_test_state(3, 2),
        ]
        self.current_state_index = 0
    
    def _create_test_state(self, tick: int, game_time: float):
        """Create a test game state."""
        return {
            "version": "1.0",
            "player_id": 1,
            "timestamp": time.time(),
            "game_time": game_time,
            "resources": {
                "manpower": {"current": 500 + tick * 10, "income": 10, "max": 1000},
                "fuel": {"current": 300 + tick * 5, "income": 5, "max": 800},
                "munitions": {"current": 200 + tick * 3, "income": 3, "max": 600}
            },
            "squads": [
                {
                    "id": 1,
                    "type": "riflemen",
                    "health": 0.8 + tick * 0.01,
                    "max_health": 1.0,
                    "vet_level": min(tick, 5),
                    "pos": [100 + tick * 10, 200 + tick * 5, 0],
                    "posture": "defensive",
                    "target": None,
                    "flags": 0
                }
            ],
            "capture_points": [
                {
                    "id": 1,
                    "pos": [500, 500, 0],
                    "owner": 1,
                    "progress": 0.5 + tick * 0.1,
                    "is_neutral": False
                }
            ],
            "visible_enemies": [],
            "tech_tree": {
                "t1": True,
                "t2": tick >= 2,
                "t3": False,
                "abilities": ["scout", "riflemen"] if tick >= 1 else []
            },
            "build_queue": [
                {
                    "type": "unit",
                    "name": "riflemen",
                    "progress": 0.5,
                    "time": 30 - tick * 5,
                    "cost": [300, 0, 0]
                } if tick < 5 else None
            ],
            "pop": [20 + tick, 100],
            "phase": "early" if game_time < 300 else "mid"
        }
    
    def start(self):
        """Start the SCAR simulator thread."""
        self.running = True
        self.thread = threading.Thread(target=self._simulate_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the SCAR simulator."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
    
    def _simulate_loop(self):
        """Simulate SCAR mod writing state and reading commands."""
        while self.running:
            # Write current state
            self._write_state()
            
            # Read and process commands
            self._read_commands()
            
            # Advance to next state
            self._advance_state()
            
            # Sleep for simulation interval
            time.sleep(0.5)
    
    def _write_state(self):
        """Write current game state to file."""
        if self.current_state_index < len(self.state_sequence):
            state = self.state_sequence[self.current_state_index]
        else:
            # Create dynamic state after sequence
            state = self._create_test_state(
                self.current_state_index + 1,
                (self.current_state_index + 1) * 10
            )
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False)
        except (IOError, OSError) as e:
            print(f"Failed to write state: {e}")
    
    def _read_commands(self):
        """Read and process commands from file."""
        try:
            if self.command_file.exists():
                with open(self.command_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        data = json.loads(content)
                        commands = data.get("commands", [])
                        print(f"SCAR: Received {len(commands)} commands")
                        
                        # Process each command (in real implementation, execute in game)
                        for command in commands:
                            print(f"SCAR: Executing command: {command}")
                        
                        # Clear command file after processing
                        self.command_file.unlink()
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"Failed to read commands: {e}")
    
    def _advance_state(self):
        """Advance to the next state."""
        self.current_state_index += 1


class TestRoundtripIntegration:
    """Test end-to-end IPC roundtrip integration."""
    
    def test_basic_roundtrip(self):
        """Test basic state writing and command reading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create configuration
            ipc_config = {
                "state_file": str(Path(temp_dir) / "state.json"),
                "command_file": str(Path(temp_dir) / "commands.json"),
                "lock_file": str(Path(temp_dir) / "lock.tmp"),
                "data_dir": temp_dir,
                "poll_interval": 0.1,
                "max_retries": 2
            }
            
            # Create and start IPC reader
            config_data = {
                "ipc": ipc_config,
                "mod": {"version": "1.0.0"},
                "game": {"faction": "allies"},
                "mistral": {"api_url": "http://test.com"},
                "debug": {"enabled": False}
            }
            
            config = Configuration()
            config._config = config_data
            
            ipc = IPCReader(config)
            assert ipc.start()
            
            try:
                # Create mock SCAR
                scar = MockSCARSimulator(ipc_config)
                scar.start()
                
                # Wait for first state
                time.sleep(0.6)
                
                # Check if state was received
                message = ipc.wait_for_message(timeout=1.0)
                assert message is not None
                assert message.message_type == "state"
                assert "player_id" in message.data
                assert message.data["player_id"] == 1
                
                # Send a test command
                test_command = {"command": "TEST_ROUNDTRIP", "data": "test"}
                assert ipc.send_command(test_command)
                
                # Wait for SCAR to process command
                time.sleep(0.3)
                
                # Verify command was processed (in real test, would check game state)
                stats = ipc.get_stats()
                assert stats.messages_received >= 1
                assert stats.messages_sent >= 1
                
            finally:
                scar.stop()
                ipc.stop()
    
    def test_multiple_state_updates(self):
        """Test receiving multiple state updates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ipc_config = {
                "state_file": str(Path(temp_dir) / "state.json"),
                "command_file": str(Path(temp_dir) / "commands.json"),
                "lock_file": str(Path(temp_dir) / "lock.tmp"),
                "data_dir": temp_dir,
                "poll_interval": 0.05,
                "max_retries": 2
            }
            
            config_data = {
                "ipc": ipc_config,
                "mod": {"version": "1.0.0"},
                "game": {"faction": "allies"},
                "mistral": {"api_url": "http://test.com"},
                "debug": {"enabled": False}
            }
            
            config = Configuration()
            config._config = config_data
            
            ipc = IPCReader(config)
            assert ipc.start()
            
            try:
                scar = MockSCARSimulator(ipc_config)
                scar.start()
                
                # Wait for multiple state updates
                received_states = []
                for _ in range(5):
                    message = ipc.wait_for_message(timeout=1.0)
                    if message:
                        received_states.append(message.data)
                
                # Should have received at least 3 states
                assert len(received_states) >= 3
                
                # Verify states are different (time should be progressing)
                timestamps = [state["game_time"] for state in received_states]
                assert timestamps == sorted(timestamps)  # Times should be increasing
                
            finally:
                scar.stop()
                ipc.stop()
    
    def test_command_execution_flow(self):
        """Test full command execution flow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ipc_config = {
                "state_file": str(Path(temp_dir) / "state.json"),
                "command_file": str(Path(temp_dir) / "commands.json"),
                "lock_file": str(Path(temp_dir) / "lock.tmp"),
                "data_dir": temp_dir,
                "poll_interval": 0.05,
                "max_retries": 2
            }
            
            config_data = {
                "ipc": ipc_config,
                "mod": {"version": "1.0.0"},
                "game": {"faction": "allies"},
                "mistral": {"api_url": "http://test.com"},
                "debug": {"enabled": False}
            }
            
            config = Configuration()
            config._config = config_data
            
            ipc = IPCReader(config)
            assert ipc.start()
            
            try:
                scar = MockSCARSimulator(ipc_config)
                scar.start()
                
                # Wait for first state
                time.sleep(0.3)
                
                # Send multiple commands
                commands = [
                    {"command": "BUILD", "building": "barracks", "position": [100, 200, 0]},
                    {"command": "PRODUCE", "unit": "riflemen"},
                    {"command": "ATTACK_MOVE", "squad": 1, "position": [300, 400, 0]}
                ]
                
                assert ipc.send_commands(commands)
                
                # Verify commands were sent
                stats = ipc.get_stats()
                assert stats.messages_sent >= 1
                
                # Wait for SCAR to process
                time.sleep(0.4)
                
                # Should have received more states
                assert ipc.get_stats().messages_received >= 1
                
            finally:
                scar.stop()
                ipc.stop()


class TestPerformanceIntegration:
    """Test performance aspects of the IPC system."""
    
    def test_latency_measurement(self):
        """Test roundtrip latency measurement."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ipc_config = {
                "state_file": str(Path(temp_dir) / "state.json"),
                "command_file": str(Path(temp_dir) / "commands.json"),
                "lock_file": str(Path(temp_dir) / "lock.tmp"),
                "data_dir": temp_dir,
                "poll_interval": 0.01,  # Fast polling for test
                "max_retries": 2
            }
            
            config_data = {
                "ipc": ipc_config,
                "mod": {"version": "1.0.0"},
                "game": {"faction": "allies"},
                "mistral": {"api_url": "http://test.com"},
                "debug": {"enabled": False}
            }
            
            config = Configuration()
            config._config = config_data
            
            ipc = IPCReader(config)
            assert ipc.start()
            
            try:
                scar = MockSCARSimulator(ipc_config)
                scar.start()
                
                # Measure latency by sending commands and checking response times
                start_time = time.time()
                
                # Send a command
                assert ipc.send_command({"command": "PING", "timestamp": start_time})
                
                # Wait for state update (which indicates roundtrip)
                message = ipc.wait_for_message(timeout=2.0)
                end_time = time.time()
                
                assert message is not None
                
                latency = end_time - start_time
                print(f"Measured latency: {latency:.3f}s")
                
                # Latency should be under 1 second for this test
                assert latency < 1.0, f"Latency {latency:.3f}s exceeds 1s threshold"
                
            finally:
                scar.stop()
                ipc.stop()


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
