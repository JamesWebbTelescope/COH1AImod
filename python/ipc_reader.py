"""
CoH1 × Mistral AI Mod - IPC File Reader

Handles reading of state files from SCAR mod and sending commands back.
This is the Python side of the IPC channel.

Author: Generated via planner skill
Version: 0.1.0
Date: 2026-10-04
"""

import json
import os
import time
import threading
import queue
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum, auto
import logging

try:
    from .config import get_config, resolve_data_dir
except ImportError:
    # For direct execution or testing
    from config import get_config, resolve_data_dir


class IPCStatus(Enum):
    """Status of the IPC channel."""
    DISCONNECTED = auto()
    CONNECTED = auto()
    ERROR = auto()


@dataclass
class IPCMessage:
    """Represents an IPC message."""
    timestamp: float
    data: Dict[str, Any]
    message_type: str = "state"


@dataclass
class IPCStats:
    """Statistics for IPC performance monitoring."""
    messages_received: int = 0
    messages_sent: int = 0
    bytes_received: int = 0
    bytes_sent: int = 0
    read_errors: int = 0
    write_errors: int = 0
    last_message_time: float = 0.0
    last_error_time: float = 0.0
    average_latency: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "messages_received": self.messages_received,
            "messages_sent": self.messages_sent,
            "bytes_received": self.bytes_received,
            "bytes_sent": self.bytes_sent,
            "read_errors": self.read_errors,
            "write_errors": self.write_errors,
            "last_message_time": self.last_message_time,
            "last_error_time": self.last_error_time,
            "average_latency": self.average_latency
        }


class IPCReader:
    """
    File-based IPC reader for communication with SCAR mod.
    
    Implements polling mechanism to read state files and send commands.
    """
    
    def __init__(self, config=None):
        """
        Initialize IPC reader.
        
        Args:
            config: Configuration instance. Uses global config if None.
        """
        self.config = config or get_config()
        self.logger = logging.getLogger(__name__)
        
        # Get paths from config
        ipc_config = self.config.get("ipc") or {}
        self.state_file_name = ipc_config.get("state_file") or "coh1ai_state.json"
        self.command_file_name = ipc_config.get("command_file") or "coh1ai_commands.json"
        self.lock_file_name = ipc_config.get("lock_file") or "coh1ai_lock.tmp"
        
        self.poll_interval = ipc_config.get("poll_interval") or 0.05
        self.max_retries = ipc_config.get("max_retries") or 3
        
        config_data_dir = ipc_config.get("data_dir") or "coh1ai_data"
        self.data_dir = resolve_data_dir(config_data_dir)
        self.data_dirs = [self.data_dir]
        
        self.logger.info(f"Checking data directories: {[str(d) for d in self.data_dirs]}")
        self.logger.info(f"Using data directory: {self.data_dir}")
        
        # Ensure data directory exists
        self._ensure_data_dir()
        
        # Update file paths to use the resolved data_dir
        self.state_file = self.data_dir / self.state_file_name
        self.command_file = self.data_dir / self.command_file_name
        self.lock_file = self.data_dir / self.lock_file_name
        
        self.logger.info(f"State file: {self.state_file}")
        self.logger.info(f"Command file: {self.command_file}")
        self.logger.info(f"Lock file: {self.lock_file}")
        
        # Status and state
        self.status = IPCStatus.DISCONNECTED
        self.running = False
        self.thread = None
        self.message_queue = queue.Queue()
        self.stats = IPCStats()
        self._lock = threading.Lock()
        
        # Event for signaling new messages
        self.new_message_event = threading.Event()
        
    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.logger.error(f"Failed to create data directory {self.data_dir}: {e}")
            raise
    
    def start(self) -> bool:
        """Start the IPC reader thread."""
        if self.running:
            self.logger.warning("IPC reader is already running")
            return False
        
        try:
            # Start the polling thread
            self.running = True
            self.status = IPCStatus.DISCONNECTED
            self.thread = threading.Thread(target=self._poll_loop, daemon=True)
            self.thread.start()
            
            self.logger.info(f"IPC reader started, polling interval: {self.poll_interval}s")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start IPC reader: {e}")
            self.running = False
            return False
    
    def stop(self) -> bool:
        """Stop the IPC reader thread."""
        if not self.running:
            return True
        
        self.running = False
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            if self.thread.is_alive():
                self.logger.warning("IPC reader thread did not stop gracefully")
                return False
        
        self.status = IPCStatus.DISCONNECTED
        self.logger.info("IPC reader stopped")
        return True
    
    def _poll_loop(self):
        """Main polling loop that runs in a separate thread."""
        self.logger.debug("IPC polling loop started")
        
        while self.running:
            try:
                self._poll_once()
            except Exception as e:
                self.logger.error(f"Error in IPC poll loop: {e}")
                self.stats.read_errors += 1
                self.stats.last_error_time = time.time()
                self.status = IPCStatus.ERROR
            
            # Sleep for the poll interval
            time.sleep(self.poll_interval)
        
        self.logger.debug("IPC polling loop stopped")
    
    def _poll_once(self):
        """Perform one polling cycle."""
        # Try to read state file
        state_data = self._read_state_file()
        
        if state_data:
            self.status = IPCStatus.CONNECTED
            self.stats.messages_received += 1
            self.stats.bytes_received += len(json.dumps(state_data))
            self.stats.last_message_time = time.time()
            
            # Put message in queue
            message = IPCMessage(
                timestamp=time.time(),
                data=state_data,
                message_type="state"
            )
            self.message_queue.put(message)
            self.new_message_event.set()
            
            # Clean up the file after reading
            self._cleanup_state_file()
    
    def _read_state_file(self) -> Optional[Dict[str, Any]]:
        """Read the state file if it exists."""
        # Try primary state file first
        if self.state_file.exists():
            return self._read_state_file_at(self.state_file)
        
        return None
    
    def _read_state_file_at(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Read state file at a specific path."""
        try:
            with self._acquire_lock():
                if not filepath.exists():
                    return None
                    
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.strip():
                        return None
                    
                    try:
                        data = json.loads(content)
                        return data
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse JSON from state file {filepath}: {e}")
                        return None
        except (IOError, OSError) as e:
            self.logger.warning(f"Failed to read state file {filepath}: {e}")
            return None
    
    def _cleanup_state_file(self):
        """Clean up the state file after reading."""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
        except (IOError, OSError) as e:
            self.logger.warning(f"Failed to cleanup state file: {e}")
    
    def send_command(self, command: Dict[str, Any]) -> bool:
        """
        Send a command to the SCAR mod.
        
        Args:
            command: Command dictionary to send.
            
        Returns:
            True if command was sent successfully, False otherwise.
        """
        if not self.running:
            self.logger.warning("IPC reader is not running, cannot send command")
            return False
        
        try:
            command_data = {
                "timestamp": time.time(),
                "commands": [command] if isinstance(command, dict) else command
            }
            
            json_data = json.dumps(command_data, ensure_ascii=False)
            
            with self._acquire_lock():
                with open(self.command_file, 'w', encoding='utf-8') as f:
                    f.write(json_data)
            
            self.stats.messages_sent += 1
            self.stats.bytes_sent += len(json_data)
            self.logger.debug(f"Sent command: {command}")
            return True
            
        except (IOError, OSError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to send command: {e}")
            self.stats.write_errors += 1
            return False
    
    def send_commands(self, commands: List[Dict[str, Any]]) -> bool:
        """
        Send multiple commands to the SCAR mod.
        
        Args:
            commands: List of command dictionaries to send.
            
        Returns:
            True if commands were sent successfully, False otherwise.
        """
        if not commands:
            return False
            
        command_data = {
            "timestamp": time.time(),
            "commands": commands
        }
        
        # For send_commands, we bypass the single command wrapping in send_command
        # and write directly to the file
        try:
            json_data = json.dumps(command_data, ensure_ascii=False)
            
            with self._acquire_lock():
                with open(self.command_file, 'w', encoding='utf-8') as f:
                    f.write(json_data)
            
            self.stats.messages_sent += 1
            self.stats.bytes_sent += len(json_data)
            self.logger.debug(f"Sent {len(commands)} commands")
            return True
            
        except (IOError, OSError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to send commands: {e}")
            self.stats.write_errors += 1
            return False
    
    def get_message(self, timeout: Optional[float] = None) -> Optional[IPCMessage]:
        """
        Get a message from the queue.
        
        Args:
            timeout: Optional timeout in seconds.
            
        Returns:
            IPCMessage if available, None otherwise.
        """
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def wait_for_message(self, timeout: Optional[float] = None) -> Optional[IPCMessage]:
        """
        Wait for a new message with timeout.
        
        Args:
            timeout: Optional timeout in seconds.
            
        Returns:
            IPCMessage if received within timeout, None otherwise.
        """
        if self.new_message_event.wait(timeout=timeout):
            self.new_message_event.clear()
            return self.get_message(timeout=0.1)
        return None
    
    def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest state from the queue without removing it.
        
        Returns:
            Latest state dictionary or None.
        """
        try:
            # Try to peek at the latest message
            if not self.message_queue.empty():
                # Get and re-queue the latest message
                message = self.message_queue.get(timeout=0.1)
                if message:
                    self.message_queue.put(message)
                    return message.data
        except queue.Empty:
            pass
        return None
    
    def get_stats(self) -> IPCStats:
        """Get current IPC statistics."""
        return self.stats
    
    def reset_stats(self):
        """Reset IPC statistics."""
        self.stats = IPCStats()
    
    def _acquire_lock(self):
        """Acquire the IPC lock file."""
        return FileLock(self.lock_file, timeout=1.0)


class FileLock:
    """Context manager for file-based locking."""
    
    def __init__(self, lock_file: Path, timeout: float = 1.0):
        """
        Initialize file lock.
        
        Args:
            lock_file: Path to the lock file.
            timeout: Maximum time to wait for lock in seconds.
        """
        self.lock_file = lock_file
        self.timeout = timeout
        self.acquired = False
        
    def __enter__(self):
        """Acquire the lock."""
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                # Try to create the lock file exclusively
                self.lock_file.touch(exist_ok=False)
                self.acquired = True
                return self
            except OSError:
                # File exists, wait and retry
                time.sleep(0.01)
        
        raise TimeoutError(f"Could not acquire lock on {self.lock_file} within {self.timeout}s")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the lock."""
        if self.acquired:
            try:
                self.lock_file.unlink()
            except (IOError, OSError):
                pass
            self.acquired = False


class LatencyTester:
    """Helper class for testing IPC latency."""
    
    def __init__(self, ipc_reader: IPCReader, num_tests: int = 100):
        """
        Initialize latency tester.
        
        Args:
            ipc_reader: IPCReader instance to test.
            num_tests: Number of tests to run.
        """
        self.ipc_reader = ipc_reader
        self.num_tests = num_tests
        self.latencies = []
        
    def run_test(self) -> Dict[str, Any]:
        """
        Run latency test.
        
        Returns:
            Dictionary with test results.
        """
        self.latencies = []
        start_time = time.time()
        
        for i in range(self.num_tests):
            test_latency = self._measure_single_latency()
            if test_latency >= 0:
                self.latencies.append(test_latency)
            
            # Small delay between tests
            time.sleep(0.01)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        return self._calculate_stats(total_time)
    
    def _measure_single_latency(self) -> float:
        """Measure a single round-trip latency."""
        # Create a test message with timestamp
        test_command = {
            "command": "PING",
            "timestamp": time.time(),
            "test_id": len(self.latencies) + 1
        }
        
        start_time = time.time()
        
        # Send ping
        if not self.ipc_reader.send_command(test_command):
            return -1
        
        # Wait for pong (in real implementation, SCAR would send pong)
        # For testing, we'll simulate the round-trip
        pong_message = self.ipc_reader.wait_for_message(timeout=1.0)
        
        if pong_message and pong_message.data.get("command") == "PONG":
            end_time = time.time()
            return end_time - start_time
        
        return -1
    
    def _calculate_stats(self, total_time: float) -> Dict[str, Any]:
        """Calculate statistics from latency measurements."""
        if not self.latencies:
            return {
                "num_tests": 0,
                "total_time": total_time,
                "average_latency": 0,
                "min_latency": 0,
                "max_latency": 0,
                "std_dev": 0,
                "success_rate": 0
            }
        
        avg = sum(self.latencies) / len(self.latencies)
        min_lat = min(self.latencies)
        max_lat = max(self.latencies)
        
        # Calculate standard deviation
        variance = sum((x - avg) ** 2 for x in self.latencies) / len(self.latencies)
        std_dev = variance ** 0.5
        
        success_rate = len(self.latencies) / self.num_tests * 100
        
        return {
            "num_tests": len(self.latencies),
            "total_time": total_time,
            "average_latency": avg,
            "min_latency": min_lat,
            "max_latency": max_lat,
            "std_dev": std_dev,
            "success_rate": success_rate
        }


# Convenience functions
_def_ipc_reader = None


def get_ipc_reader() -> IPCReader:
    """Get the global IPC reader instance."""
    global _def_ipc_reader
    if _def_ipc_reader is None:
        _def_ipc_reader = IPCReader()
    return _def_ipc_reader


def start_ipc() -> bool:
    """Start the global IPC reader."""
    return get_ipc_reader().start()


def stop_ipc() -> bool:
    """Stop the global IPC reader."""
    return get_ipc_reader().stop()


def send_command(command: Dict[str, Any]) -> bool:
    """Send a command via the global IPC reader."""
    return get_ipc_reader().send_command(command)


if __name__ == "__main__":
    # Test IPC reader
    print("Testing IPC Reader...")
    
    # Create a test config
    from .config import Configuration
    config = Configuration()
    
    # Create and start IPC reader
    ipc = IPCReader(config)
    if not ipc.start():
        print("Failed to start IPC reader")
        exit(1)
    
    print(f"IPC reader started with status: {ipc.status}")
    
    # Test sending a command
    test_command = {
        "command": "TEST",
        "data": "test_data",
        "timestamp": time.time()
    }
    
    if ipc.send_command(test_command):
        print("Test command sent successfully")
    else:
        print("Failed to send test command")
    
    # Run for a few seconds
    time.sleep(2)
    
    # Stop IPC reader
    ipc.stop()
    print(f"IPC stats: {ipc.get_stats()}")
    print("IPC test completed")
