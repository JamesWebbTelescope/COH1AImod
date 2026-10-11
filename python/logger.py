"""
CoH1 × Mistral AI Mod - State Logging Module

Handles logging of game states for post-match analysis and debugging.
Implements log rotation to manage file sizes.

Author: Generated via planner skill
Version: 0.1.0
Date: 2026-10-10
"""

import json
import os
import time
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field

try:
    from .config import get_config
    from .schema import GameState
except ImportError:
    # For direct execution or testing
    pass


@dataclass
class LogConfig:
    """Configuration for logging."""
    log_dir: str = "coh1ai_data"
    state_log_file: str = "states.jsonl"
    command_log_file: str = "commands.jsonl"
    error_log_file: str = "errors.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_backups: int = 5
    
    @classmethod
    def from_config(cls, config: Any) -> "LogConfig":
        """Create log config from main configuration."""
        # Handle Configuration objects which have get(*keys) method
        if hasattr(config, "get") and hasattr(config, "_config"):
            debug_config = config.get("debug") or {}
            ipc_config = config.get("ipc") or {}
        else:
            # Handle regular dict objects
            debug_config = config.get("debug", {}) if isinstance(config, dict) else {}
            ipc_config = config.get("ipc", {}) if isinstance(config, dict) else {}
        
        return cls(
            log_dir=ipc_config.get("data_dir", "coh1ai_data"),
            state_log_file=debug_config.get("state_log_file", "states.jsonl"),
            command_log_file=debug_config.get("command_log_file", "commands.jsonl"),
            error_log_file=debug_config.get("error_log_file", "errors.log"),
            max_file_size=debug_config.get("max_file_size", 10 * 1024 * 1024),
            max_backups=debug_config.get("max_backups", 5)
        )


class LogRotator:
    """
    Handles log file rotation to prevent files from growing too large.
    """
    
    def __init__(self, log_dir: str, max_size: int, max_backups: int):
        """
        Initialize log rotator.
        
        Args:
            log_dir: Directory for log files
            max_size: Maximum file size in bytes before rotation
            max_backups: Maximum number of backup files to keep
        """
        self.log_dir = Path(log_dir)
        self.max_size = max_size
        self.max_backups = max_backups
        self._lock = threading.Lock()
        
        # Ensure log directory exists
        self._ensure_dir()
    
    def _ensure_dir(self):
        """Ensure log directory exists."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create log directory {self.log_dir}: {e}")
    
    def should_rotate(self, filepath: Path) -> bool:
        """
        Check if a log file should be rotated.
        
        Args:
            filepath: Path to the log file
            
        Returns:
            True if file should be rotated, False otherwise
        """
        if not filepath.exists():
            return False
        
        try:
            size = filepath.stat().st_size
            return size >= self.max_size
        except OSError:
            return False
    
    def rotate(self, filepath: Path) -> bool:
        """
        Rotate a log file.
        
        Args:
            filepath: Path to the log file to rotate
            
        Returns:
            True if rotation successful, False otherwise
        """
        with self._lock:
            try:
                # Generate backup filename
                stem = filepath.stem
                suffix = filepath.suffix
                
                # Remove the oldest backup if we have too many
                self._remove_oldest_backup(filepath)
                
                # Rotate existing backups
                for i in range(self.max_backups - 1, 0, -1):
                    old_backup = filepath.with_name(f"{stem}.{i}{suffix}")
                    new_backup = filepath.with_name(f"{stem}.{i + 1}{suffix}")
                    
                    if old_backup.exists():
                        if new_backup.exists():
                            new_backup.unlink()
                        old_backup.rename(new_backup)
                
                # Rotate current file to .1
                backup_1 = filepath.with_name(f"{stem}.1{suffix}")
                if backup_1.exists():
                    backup_1.unlink()
                filepath.rename(backup_1)
                
                return True
                
            except (IOError, OSError) as e:
                logging.getLogger(__name__).error(f"Failed to rotate {filepath}: {e}")
                return False
    
    def _remove_oldest_backup(self, filepath: Path):
        """Remove the oldest backup file if we have too many."""
        stem = filepath.stem
        suffix = filepath.suffix
        oldest_backup = filepath.with_name(f"{stem}.{self.max_backups}{suffix}")
        
        if oldest_backup.exists():
            try:
                oldest_backup.unlink()
            except (IOError, OSError):
                pass


class StateLogger:
    """
    Logs game state snapshots for post-match analysis.
    """
    
    def __init__(self, config: Any = None):
        """
        Initialize state logger.
        
        Args:
            config: Configuration object or LogConfig
        """
        self.logger = logging.getLogger(__name__)
        
        # Get configuration
        if config is None:
            from .config import get_config
            config = get_config()
        
        if isinstance(config, LogConfig):
            self.log_config = config
        else:
            self.log_config = LogConfig.from_config(config)
        
        # Resolve log directory - check multiple possible locations
        # SCAR writes to coh1ai_data/ relative to CoH1's base directory
        self.log_dir = self._resolve_log_dir(Path(self.log_config.log_dir))
        self.state_log_file = self.log_dir / self.log_config.state_log_file
        self.command_log_file = self.log_dir / self.log_config.command_log_file
        self.error_log_file = self.log_dir / self.log_config.error_log_file
        
        # Log rotator
        self.rotator = LogRotator(
            self.log_dir,
            self.log_config.max_file_size,
            self.log_config.max_backups
        )
        
        # Ensure directory exists
        self._ensure_dir()
        
        self.logger.info(f"State logger using directory: {self.log_dir}")
        
        # Statistics
        self.stats = {
            "states_logged": 0,
            "commands_logged": 0,
            "errors_logged": 0,
            "rotations": 0,
            "last_state_time": 0.0,
            "last_command_time": 0.0
        }
        
        # Lock for thread safety
        self._lock = threading.Lock()
    
    def _ensure_dir(self):
        """Ensure log directory exists."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.logger.error(f"Failed to create log directory: {e}")
            raise
    
    def _resolve_log_dir(self, config_data_dir: Path) -> Path:
        """
        Resolve the log directory by checking multiple possible locations.
        
        SCAR writes to coh1ai_data/ relative to CoH1's base directory,
        while Python might run from the mod directory.
        
        Args:
            config_data_dir: The configured data directory path
            
        Returns:
            Path to the resolved log directory
        """
        # Try multiple data directories - CHECK COH1 BASE FIRST since that's where SCAR writes
        data_dirs = []
        
        # FIRST: Check in CoH1's base directory (where SCAR writes files)
        coh1_base = Path(__file__).parent.parent.parent.parent  # Go up to CoH1 base
        data_dirs.append(coh1_base / config_data_dir)
        
        # SECOND: Check absolute Steam path
        steam_path = Path("D:/SteamLibrary/steamapps/common/Company of Heroes Relaunch")
        if steam_path.exists():
            data_dirs.append(steam_path / config_data_dir)
        
        # THIRD: Check in the mod directory
        mod_dir = Path(__file__).parent
        data_dirs.append(mod_dir / config_data_dir)
        
        # FOURTH: Check in mod directory under Steam
        if steam_path.exists():
            data_dirs.append(steam_path / "Mods" / "COh1AIMod" / config_data_dir)
        
        # FIFTH: Add the configured data directory relative to current working dir
        data_dirs.append(Path(config_data_dir))
        
        # Remove duplicates while preserving order
        seen = set()
        data_dirs = [p for p in data_dirs if not (p in seen or seen.add(p))]
        
        # Always prefer CoH1 base directory since that's where SCAR writes
        # If it doesn't exist, it will be created when SCAR writes files
        coh1_base_dir = data_dirs[0]  # First one is CoH1 base
        self.logger.info(f"Using data directory: {coh1_base_dir}")
        return coh1_base_dir
    
    def log_state(self, state: Union[Dict[str, Any], GameState], timestamp: Optional[float] = None) -> bool:
        """
        Log a game state.
        
        Args:
            state: Game state to log (dict or GameState object)
            timestamp: Optional timestamp (uses current time if None)
            
        Returns:
            True if state was logged successfully, False otherwise
        """
        try:
            # Convert to dict if GameState
            if hasattr(state, "to_dict"):
                state_dict = state.to_dict()
            elif isinstance(state, dict):
                state_dict = state
            else:
                self.logger.warning(f"Cannot log state of type {type(state)}")
                return False
            
            # Add timestamp if not provided
            if timestamp is None:
                timestamp = time.time()
            
            state_dict["_log_timestamp"] = timestamp
            
            # Check if we need to rotate
            with self._lock:
                if self.rotator.should_rotate(self.state_log_file):
                    if self.rotator.rotate(self.state_log_file):
                        self.stats["rotations"] += 1
                
                # Write state as JSON line
                with open(self.state_log_file, 'a', encoding='utf-8') as f:
                    json.dump(state_dict, f, ensure_ascii=False)
                    f.write('\n')
                
                self.stats["states_logged"] += 1
                self.stats["last_state_time"] = timestamp
                
                return True
                
        except (IOError, OSError, TypeError, ValueError) as e:
            self.logger.error(f"Failed to log state: {e}")
            self._log_error(f"State logging error: {e}")
            return False
    
    def log_command(self, command: Dict[str, Any], timestamp: Optional[float] = None) -> bool:
        """
        Log a command.
        
        Args:
            command: Command to log
            timestamp: Optional timestamp (uses current time if None)
            
        Returns:
            True if command was logged successfully, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = time.time()
            
            # Add timestamp
            command_with_ts = command.copy()
            command_with_ts["_log_timestamp"] = timestamp
            
            # Check if we need to rotate
            with self._lock:
                if self.rotator.should_rotate(self.command_log_file):
                    if self.rotator.rotate(self.command_log_file):
                        self.stats["rotations"] += 1
                
                # Write command as JSON line
                with open(self.command_log_file, 'a', encoding='utf-8') as f:
                    json.dump(command_with_ts, f, ensure_ascii=False)
                    f.write('\n')
                
                self.stats["commands_logged"] += 1
                self.stats["last_command_time"] = timestamp
                
                return True
                
        except (IOError, OSError, TypeError) as e:
            self.logger.error(f"Failed to log command: {e}")
            self._log_error(f"Command logging error: {e}")
            return False
    
    def log_error(self, error: str, timestamp: Optional[float] = None) -> bool:
        """
        Log an error.
        
        Args:
            error: Error message to log
            timestamp: Optional timestamp (uses current time if None)
            
        Returns:
            True if error was logged successfully, False otherwise
        """
        return self._log_error(error, timestamp)
    
    def _log_error(self, error: str, timestamp: Optional[float] = None):
        """Internal method to log an error."""
        try:
            if timestamp is None:
                timestamp = time.time()
            
            # Format error with timestamp
            error_line = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}] {error}\n"
            
            # Check if we need to rotate
            with self._lock:
                if self.rotator.should_rotate(self.error_log_file):
                    if self.rotator.rotate(self.error_log_file):
                        self.stats["rotations"] += 1
                
                # Write error
                with open(self.error_log_file, 'a', encoding='utf-8') as f:
                    f.write(error_line)
                
                self.stats["errors_logged"] += 1
                
        except (IOError, OSError) as e:
            # Can't log the logging error, just print
            print(f"CRITICAL: Failed to log error: {e}")
    
    def log_batch(self, states: List[Union[Dict[str, Any], GameState]]) -> int:
        """
        Log a batch of states.
        
        Args:
            states: List of states to log
            
        Returns:
            Number of states successfully logged
        """
        count = 0
        for state in states:
            if self.log_state(state):
                count += 1
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logger statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset logger statistics."""
        for key in self.stats:
            if isinstance(self.stats[key], int):
                self.stats[key] = 0
            else:
                self.stats[key] = 0.0


class LogParser:
    """
    Parses log files for post-match analysis.
    """
    
    def __init__(self, log_dir: str = "coh1ai_data"):
        """
        Initialize log parser.
        
        Args:
            log_dir: Directory containing log files
        """
        self.logger = logging.getLogger(__name__)
        # Resolve log directory using same logic as StateLogger
        self.log_dir = self._resolve_log_dir(Path(log_dir))
    
    def _resolve_log_dir(self, config_data_dir: Path) -> Path:
        """
        Resolve the log directory by checking multiple possible locations.
        
        SCAR writes to coh1ai_data/ relative to CoH1's base directory,
        while Python might run from the mod directory.
        
        Args:
            config_data_dir: The configured data directory path
            
        Returns:
            Path to the resolved log directory
        """
        # Try multiple data directories - CHECK COH1 BASE FIRST since that's where SCAR writes
        data_dirs = []
        
        # FIRST: Check in CoH1's base directory (where SCAR writes files)
        coh1_base = Path(__file__).parent.parent.parent.parent  # Go up to CoH1 base
        data_dirs.append(coh1_base / config_data_dir)
        
        # SECOND: Check absolute Steam path
        steam_path = Path("D:/SteamLibrary/steamapps/common/Company of Heroes Relaunch")
        if steam_path.exists():
            data_dirs.append(steam_path / config_data_dir)
        
        # THIRD: Check in the mod directory
        mod_dir = Path(__file__).parent
        data_dirs.append(mod_dir / config_data_dir)
        
        # FOURTH: Check in mod directory under Steam
        if steam_path.exists():
            data_dirs.append(steam_path / "Mods" / "COh1AIMod" / config_data_dir)
        
        # FIFTH: Add the configured data directory relative to current working dir
        data_dirs.append(Path(config_data_dir))
        
        # Remove duplicates while preserving order
        seen = set()
        data_dirs = [p for p in data_dirs if not (p in seen or seen.add(p))]
        
        # Always prefer CoH1 base directory since that's where SCAR writes
        # If it doesn't exist, it will be created when SCAR writes files
        coh1_base_dir = data_dirs[0]  # First one is CoH1 base
        self.logger.info(f"Using data directory: {coh1_base_dir}")
        return coh1_base_dir
    
    def parse_state_log(self, filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Parse the state log file.
        
        Args:
            filepath: Optional path to state log file. Uses default if None.
            
        Returns:
            List of state dictionaries
        """
        if filepath is None:
            filepath = self.log_dir / "states.jsonl"
        
        states = []
        
        try:
            if not filepath.exists():
                self.logger.warning(f"State log file not found: {filepath}")
                return states
            
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            state = json.loads(line)
                            states.append(state)
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Failed to parse state line: {e}")
            
            self.logger.info(f"Parsed {len(states)} states from {filepath}")
            return states
            
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to read state log: {e}")
            return states
    
    def parse_command_log(self, filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Parse the command log file.
        
        Args:
            filepath: Optional path to command log file. Uses default if None.
            
        Returns:
            List of command dictionaries
        """
        if filepath is None:
            filepath = self.log_dir / "commands.jsonl"
        
        commands = []
        
        try:
            if not filepath.exists():
                self.logger.warning(f"Command log file not found: {filepath}")
                return commands
            
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            command = json.loads(line)
                            commands.append(command)
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Failed to parse command line: {e}")
            
            self.logger.info(f"Parsed {len(commands)} commands from {filepath}")
            return commands
            
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to read command log: {e}")
            return commands
    
    def parse_error_log(self, filepath: Optional[Path] = None) -> List[str]:
        """
        Parse the error log file.
        
        Args:
            filepath: Optional path to error log file. Uses default if None.
            
        Returns:
            List of error strings
        """
        if filepath is None:
            filepath = self.log_dir / "errors.log"
        
        errors = []
        
        try:
            if not filepath.exists():
                self.logger.warning(f"Error log file not found: {filepath}")
                return errors
            
            with open(filepath, 'r', encoding='utf-8') as f:
                errors = f.readlines()
            
            self.logger.info(f"Parsed {len(errors)} errors from {filepath}")
            return errors
            
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to read error log: {e}")
            return errors
    
    def get_all_logs(self) -> Dict[str, Any]:
        """
        Get all parsed logs.
        
        Returns:
            Dictionary with 'states', 'commands', and 'errors' keys
        """
        return {
            "states": self.parse_state_log(),
            "commands": self.parse_command_log(),
            "errors": self.parse_error_log()
        }
    
    def get_match_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the match from logs.
        
        Returns:
            Dictionary with match summary statistics
        """
        states = self.parse_state_log()
        commands = self.parse_command_log()
        errors = self.parse_error_log()
        
        if not states:
            return {"error": "No state data found"}
        
        # Get first and last state
        first_state = states[0]
        last_state = states[-1]
        
        # Calculate duration
        start_time = first_state.get("_log_timestamp", first_state.get("timestamp", 0))
        end_time = last_state.get("_log_timestamp", last_state.get("timestamp", 0))
        duration = end_time - start_time if end_time > start_time else 0
        
        # Count resources
        resource_types = ["manpower", "fuel", "munitions"]
        max_resources = {}
        final_resources = {}
        
        for resource_type in resource_types:
            max_val = 0
            final_val = 0
            
            for state in states:
                resources = state.get("resources", {})
                if resource_type in resources:
                    current = resources[resource_type].get("current", 0)
                    max_val = max(max_val, current)
            
            if states:
                final_resources[resource_type] = last_state.get("resources", {}).get(resource_type, {}).get("current", 0)
            
            max_resources[resource_type] = max_val
        
        # Count squads
        max_squads = max(len(state.get("squads", [])) for state in states) if states else 0
        final_squads = len(last_state.get("squads", [])) if states else 0
        
        # Count capture points
        max_cps = max(len(state.get("cps", state.get("capture_points", []))) for state in states) if states else 0
        final_cps = len(last_state.get("cps", last_state.get("capture_points", []))) if states else 0
        
        return {
            "duration": duration,
            "start_time": start_time,
            "end_time": end_time,
            "states_count": len(states),
            "commands_count": len(commands),
            "errors_count": len(errors),
            "max_resources": max_resources,
            "final_resources": final_resources,
            "max_squads": max_squads,
            "final_squads": final_squads,
            "max_capture_points": max_cps,
            "final_capture_points": final_cps,
            "faction": last_state.get("faction", "unknown") if states else "unknown"
        }
    
    def filter_by_time(self, start_time: float, end_time: float) -> Dict[str, Any]:
        """
        Filter logs by time range.
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            Dictionary with filtered states, commands, and errors
        """
        all_logs = self.get_all_logs()
        
        filtered_states = [
            s for s in all_logs["states"] 
            if start_time <= s.get("_log_timestamp", s.get("timestamp", 0)) <= end_time
        ]
        
        filtered_commands = [
            c for c in all_logs["commands"] 
            if start_time <= c.get("_log_timestamp", 0) <= end_time
        ]
        
        return {
            "states": filtered_states,
            "commands": filtered_commands,
            "errors": all_logs["errors"]  # Errors don't have timestamps in current format
        }


# Global logger instances
_state_logger = None
_command_logger = None
_log_parser = None


def get_state_logger() -> StateLogger:
    """Get the global state logger instance."""
    global _state_logger
    if _state_logger is None:
        from .config import get_config
        config = get_config()
        _state_logger = StateLogger(config)
    return _state_logger


def get_log_parser() -> LogParser:
    """Get the global log parser instance."""
    global _log_parser
    if _log_parser is None:
        from .config import get_config
        config = get_config()
        _log_parser = LogParser(config.get("ipc", {}).get("data_dir", "coh1ai_data"))
    return _log_parser


def log_state(state: Union[Dict[str, Any], GameState]) -> bool:
    """Log a game state using the global logger."""
    return get_state_logger().log_state(state)


def log_command(command: Dict[str, Any]) -> bool:
    """Log a command using the global logger."""
    return get_state_logger().log_command(command)


if __name__ == "__main__":
    # Test the logger
    print("Testing State Logger...")
    
    try:
        from .config import Configuration
        config = Configuration()
        
        # Test state logging
        logger = StateLogger(config)
        
        test_state = {
            "version": "1.0",
            "player_id": 1,
            "timestamp": time.time(),
            "game_time": 120.5,
            "resources": {
                "manpower": {"current": 500, "income": 10, "max": 1000},
                "fuel": {"current": 300, "income": 5, "max": 800}
            },
            "squads": [{"id": 1, "type": "riflemen", "health": 0.8}]
        }
        
        # Log a state
        assert logger.log_state(test_state)
        print("State logged successfully")
        
        # Log a command
        test_command = {"command": "BUILD", "building": "barracks"}
        assert logger.log_command(test_command)
        print("Command logged successfully")
        
        # Parse logs
        parser = LogParser()
        states = parser.parse_state_log()
        print(f"Parsed {len(states)} states")
        
        # Get summary
        summary = parser.get_match_summary()
        print(f"Match duration: {summary.get('duration', 0):.1f}s")
        print(f"Final resources: {summary.get('final_resources', {})}")
        
        print("Logger tests completed successfully")
        
    except Exception as e:
        print(f"Logger test failed: {e}")
        import traceback
        traceback.print_exc()
