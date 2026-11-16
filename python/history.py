"""
CoH1 × Mistral AI Mod - Game History Manager

Maintains a rolling log of game state snapshots and AI decisions for strategist continuity.
This module provides context-aware history management for the Mistral strategist,
allowing it to make decisions based on past game states and previous decisions.

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-26
"""

import json
import time
import threading
import copy
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


# ============================================
# Type Definitions
# ============================================

try:
    from schema import (
        GameState, Position, SquadData, CapturePointData, EnemyData,
        TechTreeData, BuildQueueItem, PopulationData, ResourceData
    )
    SCHEMA_AVAILABLE = True
except ImportError:
    # Fallback for testing or standalone execution
    GameState = Any
    Position = Any
    SquadData = Any
    CapturePointData = Any
    EnemyData = Any
    TechTreeData = Any
    BuildQueueItem = Any
    PopulationData = Any
    ResourceData = Any
    SCHEMA_AVAILABLE = False


# ============================================
# History Entry Types
# ============================================

class HistoryEntryType(Enum):
    """Types of history entries."""
    GAME_STATE = "game_state"      # Full game state snapshot
    DECISION = "decision"          # AI decision made
    COMMAND = "command"            # Command executed
    EVENT = "event"                # Game event (capture, loss, etc.)


@dataclass
class HistoryEntry:
    """
    A single entry in the game history.
    
    Represents either a game state snapshot or an AI decision/command.
    """
    timestamp: float  # Unix timestamp when entry was created
    game_time: float  # In-game time in seconds
    entry_type: str  # HistoryEntryType value
    data: Dict[str, Any]  # The actual data (state, decision, command, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "game_time": self.game_time,
            "type": self.entry_type,
            "data": self.data,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """Create history entry from dictionary."""
        return cls(
            timestamp=data.get("timestamp", time.time()),
            game_time=data.get("game_time", 0.0),
            entry_type=data.get("type", "game_state"),
            data=data.get("data", {}),
            metadata=data.get("metadata", {})
        )
    
    def to_json(self) -> str:
        """Convert entry to JSON string."""
        return json.dumps(self.to_dict(), separators=(',', ':'))
    
    @classmethod
    def from_json(cls, json_str: str) -> "HistoryEntry":
        """Create history entry from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class DecisionRecord:
    """
    Record of an AI decision made by the strategist.
    
    This is stored in history to provide context for future decisions.
    """
    decision_type: str  # e.g., "build", "attack", "retreat", "defend"
    target: Optional[str] = None  # What the decision affects
    reasoning: Optional[str] = None  # Why this decision was made
    confidence: float = 1.0  # Confidence score (0.0 - 1.0)
    priority: int = 0  # Priority level
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert decision record to dictionary."""
        result = {
            "type": self.decision_type,
            "confidence": self.confidence,
            "priority": self.priority
        }
        if self.target:
            result["target"] = self.target
        if self.reasoning:
            result["reasoning"] = self.reasoning
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionRecord":
        """Create decision record from dictionary."""
        return cls(
            decision_type=data.get("type", "unknown"),
            target=data.get("target"),
            reasoning=data.get("reasoning"),
            confidence=data.get("confidence", 1.0),
            priority=data.get("priority", 0)
        )


@dataclass
class CommandRecord:
    """
    Record of a command executed by the AI.
    
    This is stored in history to track what actions have been taken.
    """
    command_type: str  # e.g., "BUILD", "CAPTURE", "ATTACK_MOVE"
    parameters: Dict[str, Any] = field(default_factory=dict)
    executed: bool = False
    execution_time: float = 0.0
    result: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command record to dictionary."""
        result = {
            "type": self.command_type,
            "parameters": self.parameters,
            "executed": self.executed,
            "execution_time": self.execution_time
        }
        if self.result:
            result["result"] = self.result
        if self.error:
            result["error"] = self.error
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandRecord":
        """Create command record from dictionary."""
        return cls(
            command_type=data.get("type", "unknown"),
            parameters=data.get("parameters", {}),
            executed=data.get("executed", False),
            execution_time=data.get("execution_time", 0.0),
            result=data.get("result"),
            error=data.get("error")
        )


# ============================================
# History Manager Configuration
# ============================================

@dataclass
class HistoryConfig:
    """
    Configuration for the game history manager.
    
    Allows customization of history depth, storage, and persistence.
    """
    max_entries: int = 20  # Maximum number of history entries to keep in memory
    max_file_entries: int = 100  # Maximum entries to keep in persistent storage
    persistence_enabled: bool = True  # Whether to persist history to disk
    storage_dir: str = "coh1ai_data"  # Directory for persistent storage
    history_file: str = "game_history.jsonl"  # File for persistent history
    include_states: bool = True  # Include game state snapshots in history
    include_decisions: bool = True  # Include AI decisions in history
    include_commands: bool = True  # Include executed commands in history
    compress_states: bool = True  # Use compact representation for states
    
    @classmethod
    def from_config(cls, config: Any) -> "HistoryConfig":
        """
        Create history config from main configuration.
        
        Args:
            config: Main configuration object or dict
            
        Returns:
            HistoryConfig instance
        """
        # Handle Configuration objects
        if hasattr(config, "get") and hasattr(config, "_config"):
            orchestrator_config = config.get("orchestrator") or {}
            ipc_config = config.get("ipc") or {}
            debug_config = config.get("debug") or {}
        else:
            orchestrator_config = config.get("orchestrator", {}) if isinstance(config, dict) else {}
            ipc_config = config.get("ipc", {}) if isinstance(config, dict) else {}
            debug_config = config.get("debug", {}) if isinstance(config, dict) else {}
        
        return cls(
            max_entries=orchestrator_config.get("history_max_entries", 20),
            max_file_entries=orchestrator_config.get("history_max_file_entries", 100),
            persistence_enabled=debug_config.get("persist_history", True),
            storage_dir=ipc_config.get("data_dir", "coh1ai_data"),
            history_file=debug_config.get("history_file", "game_history.jsonl"),
            include_states=orchestrator_config.get("history_include_states", True),
            include_decisions=orchestrator_config.get("history_include_decisions", True),
            include_commands=orchestrator_config.get("history_include_commands", True),
            compress_states=orchestrator_config.get("history_compress_states", True)
        )


# ============================================
# Game History Manager
# ============================================

class GameHistoryManager:
    """
    Manages rolling log of game state snapshots and AI decisions.
    
    This class provides:
    - In-memory history with configurable depth
    - Persistent storage with log rotation
    - Efficient retrieval of recent states
    - Context generation for strategist prompts
    - Thread-safe operations
    
    Features:
    - Configurable history depth (N snapshots)
    - Efficient storage (memory + optional disk persistence)
    - History included in strategist prompts
    - History can be persisted and loaded
    
    Example:
        >>> manager = GameHistoryManager()
        >>> manager.add_state(state)  # Add a game state
        >>> manager.add_decision(decision)  # Add a decision
        >>> recent = manager.get_recent_states(5)  # Get last 5 states
        >>> context = manager.generate_context()  # For strategist prompt
    """
    
    def __init__(self, config: Optional[HistoryConfig] = None):
        """
        Initialize the game history manager.
        
        Args:
            config: Optional configuration. Uses defaults if None.
        """
        self.config = config or HistoryConfig()
        self._entries: deque = deque(maxlen=self.config.max_entries)
        self._file_entries: deque = deque(maxlen=self.config.max_file_entries)
        self._lock = threading.Lock()
        self._storage_path = None
        self._initialized = False
        
        self._init_storage()
    
    def _init_storage(self):
        """Initialize storage directory and paths."""
        if not self._initialized:
            # Resolve storage directory
            try:
                from config import resolve_data_dir
                storage_dir = resolve_data_dir(self.config.storage_dir)
            except ImportError:
                storage_dir = Path(self.config.storage_dir)
            
            self._storage_path = storage_dir / self.config.history_file
            
            # Create directory if it doesn't exist
            try:
                storage_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                # If we can't create the directory, disable persistence
                import warnings
                warnings.warn(f"Failed to create history storage directory: {e}. Persistence disabled.")
                self.config = HistoryConfig(
                    max_entries=self.config.max_entries,
                    max_file_entries=self.config.max_file_entries,
                    persistence_enabled=False,
                    storage_dir=self.config.storage_dir,
                    history_file=self.config.history_file
                )
            
            # Load existing history from disk if persistence is enabled
            if self.config.persistence_enabled:
                self._load_from_disk()
            
            self._initialized = True
    
    def add_state(self, state: Union[GameState, Dict[str, Any]], game_time: Optional[float] = None, 
                  metadata: Optional[Dict[str, Any]] = None) -> HistoryEntry:
        """
        Add a game state snapshot to the history.
        
        Args:
            state: Game state object or dictionary
            game_time: In-game time in seconds. Uses state.game_time if available.
            metadata: Optional additional metadata
            
        Returns:
            The created HistoryEntry
        """
        if self.config.include_states == False:
            return None
        # Extract game time from state if not provided
        if game_time is None:
            if hasattr(state, 'game_time'):
                game_time = state.game_time
            elif isinstance(state, dict):
                game_time = state.get('game_time', state.get('time', 0.0))
            else:
                game_time = 0.0
        
        # Convert state to dict if it's a GameState object
        if SCHEMA_AVAILABLE and isinstance(state, GameState):
            if self.config.compress_states:
                state_dict = self._compress_state(state)
            else:
                state_dict = state.to_dict()
        elif isinstance(state, dict):
            state_dict = state
        else:
            # Try to convert unknown types
            try:
                state_dict = state.to_dict() if hasattr(state, 'to_dict') else dict(state)
            except:
                state_dict = {"error": "Failed to serialize state"}
        
        # Override game_time in the state dict if provided
        if SCHEMA_AVAILABLE and isinstance(state_dict, dict):
            if "game_time" in state_dict:
                state_dict["game_time"] = game_time
            elif "time" in state_dict:
                state_dict["time"] = game_time
        
        entry = HistoryEntry(
            timestamp=time.time(),
            game_time=game_time,
            entry_type=HistoryEntryType.GAME_STATE.value,
            data=state_dict,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._entries.append(entry)
            if self.config.persistence_enabled:
                self._file_entries.append(entry)
                self._persist_to_disk(entry)
        
        return entry
    
    def add_decision(self, decision: Union[DecisionRecord, Dict[str, Any]], game_time: Optional[float] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> HistoryEntry:
        """
        Add an AI decision to the history.
        
        Args:
            decision: DecisionRecord object or dictionary
            game_time: In-game time in seconds
            metadata: Optional additional metadata
            
        Returns:
            The created HistoryEntry
        """
        if not self.config.include_decisions:
            return None
        
        if game_time is None:
            game_time = 0.0
        
        # Convert decision to dict
        if isinstance(decision, DecisionRecord):
            decision_dict = decision.to_dict()
        elif isinstance(decision, dict):
            decision_dict = decision
        else:
            try:
                decision_dict = decision.to_dict() if hasattr(decision, 'to_dict') else dict(decision)
            except:
                decision_dict = {"error": "Failed to serialize decision"}
        
        entry = HistoryEntry(
            timestamp=time.time(),
            game_time=game_time,
            entry_type=HistoryEntryType.DECISION.value,
            data=decision_dict,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._entries.append(entry)
            if self.config.persistence_enabled:
                self._file_entries.append(entry)
                self._persist_to_disk(entry)
        
        return entry
    
    def add_command(self, command: Union[CommandRecord, Dict[str, Any]], game_time: Optional[float] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> HistoryEntry:
        """
        Add an executed command to the history.
        
        Args:
            command: CommandRecord object or dictionary
            game_time: In-game time in seconds
            metadata: Optional additional metadata
            
        Returns:
            The created HistoryEntry
        """
        if not self.config.include_commands:
            return None
        
        if game_time is None:
            game_time = 0.0
        
        # Convert command to dict
        if isinstance(command, CommandRecord):
            command_dict = command.to_dict()
        elif isinstance(command, dict):
            command_dict = command
        else:
            try:
                command_dict = command.to_dict() if hasattr(command, 'to_dict') else dict(command)
            except:
                command_dict = {"error": "Failed to serialize command"}
        
        entry = HistoryEntry(
            timestamp=time.time(),
            game_time=game_time,
            entry_type=HistoryEntryType.COMMAND.value,
            data=command_dict,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._entries.append(entry)
            if self.config.persistence_enabled:
                self._file_entries.append(entry)
                self._persist_to_disk(entry)
        
        return entry
    
    def add_event(self, event_type: str, data: Dict[str, Any], game_time: Optional[float] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> HistoryEntry:
        """
        Add a custom event to the history.
        
        Args:
            event_type: Type of event (e.g., "capture_point_captured", "squad_lost")
            data: Event data
            game_time: In-game time in seconds
            metadata: Optional additional metadata
            
        Returns:
            The created HistoryEntry
        """
        if game_time is None:
            game_time = 0.0
        
        event_data = {"type": event_type, **data}
        
        entry = HistoryEntry(
            timestamp=time.time(),
            game_time=game_time,
            entry_type=HistoryEntryType.EVENT.value,
            data=event_data,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._entries.append(entry)
            if self.config.persistence_enabled:
                self._file_entries.append(entry)
                self._persist_to_disk(entry)
        
        return entry
    
    def get_recent_states(self, count: int = 10) -> List[GameState]:
        """
        Get the most recent game states from history.
        
        Args:
            count: Number of states to retrieve (max: history depth)
            
        Returns:
            List of GameState objects (or dicts if schema not available)
        """
        with self._lock:
            entries = list(self._entries)
        
        # Filter for game state entries only
        state_entries = [
            entry for entry in entries 
            if entry.entry_type == HistoryEntryType.GAME_STATE.value
        ]
        
        # Get most recent
        recent = state_entries[-count:] if count > 0 else state_entries
        
        # Convert back to GameState objects if possible
        result = []
        for entry in recent:
            if SCHEMA_AVAILABLE:
                try:
                    result.append(GameState.from_dict(entry.data))
                except:
                    result.append(entry.data)
            else:
                result.append(entry.data)
        
        return result
    
    def get_all_entries(self, entry_type: Optional[str] = None) -> List[HistoryEntry]:
        """
        Get all history entries, optionally filtered by type.
        
        Args:
            entry_type: Optional filter by entry type (GAME_STATE, DECISION, COMMAND, EVENT)
            
        Returns:
            List of HistoryEntry objects
        """
        with self._lock:
            entries = list(self._entries)
        
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        
        return entries
    
    def get_entries_since(self, timestamp: float, entry_type: Optional[str] = None) -> List[HistoryEntry]:
        """
        Get history entries since a specific timestamp.
        
        Args:
            timestamp: Unix timestamp to filter from
            entry_type: Optional filter by entry type
            
        Returns:
            List of HistoryEntry objects
        """
        with self._lock:
            entries = list(self._entries)
        
        entries = [e for e in entries if e.timestamp >= timestamp]
        
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        
        return entries
    
    def get_decisions(self, count: Optional[int] = None) -> List[DecisionRecord]:
        """
        Get recent AI decisions from history.
        
        Args:
            count: Number of decisions to retrieve (None = all)
            
        Returns:
            List of DecisionRecord objects
        """
        with self._lock:
            entries = list(self._entries)
        
        decision_entries = [
            entry for entry in entries 
            if entry.entry_type == HistoryEntryType.DECISION.value
        ]
        
        if count:
            decision_entries = decision_entries[-count:]
        
        return [DecisionRecord.from_dict(e.data) for e in decision_entries]
    
    def get_commands(self, count: Optional[int] = None) -> List[CommandRecord]:
        """
        Get recent commands from history.
        
        Args:
            count: Number of commands to retrieve (None = all)
            
        Returns:
            List of CommandRecord objects
        """
        with self._lock:
            entries = list(self._entries)
        
        command_entries = [
            entry for entry in entries 
            if entry.entry_type == HistoryEntryType.COMMAND.value
        ]
        
        if count:
            command_entries = command_entries[-count:]
        
        return [CommandRecord.from_dict(e.data) for e in command_entries]
    
    def clear(self):
        """Clear all history entries from memory."""
        with self._lock:
            self._entries.clear()
    
    def clear_all(self):
        """Clear all history entries from memory and disk."""
        with self._lock:
            self._entries.clear()
            self._file_entries.clear()
            
            # Clear disk storage
            if self._storage_path and self._storage_path.exists():
                try:
                    self._storage_path.unlink()
                except OSError:
                    pass
    
    def generate_context(self, max_states: int = 5, max_decisions: int = 3, 
                         include_summary: bool = True) -> Dict[str, Any]:
        """
        Generate context string for strategist prompts.
        
        This creates a formatted summary of recent game history that can be
        included in prompts to the Mistral strategist for context-aware decisions.
        
        Args:
            max_states: Maximum number of recent states to include
            max_decisions: Maximum number of recent decisions to include
            include_summary: Whether to include a summary section
            
        Returns:
            Dictionary with formatted context strings
        """
        with self._lock:
            entries = list(self._entries)
        
        context = {
            "recent_states": [],
            "recent_decisions": [],
            "recent_commands": [],
            "summary": {
                "total_states": 0,
                "total_decisions": 0,
                "total_commands": 0,
                "total_events": 0
            }
        }
        
        # Extract recent states
        state_entries = [
            entry for entry in entries 
            if entry.entry_type == HistoryEntryType.GAME_STATE.value
        ]
        recent_states = state_entries[-max_states:]
        
        for i, entry in enumerate(recent_states):
            state_summary = self._summarize_state(entry.data, entry.game_time)
            context["recent_states"].append(state_summary)
        
        # Extract recent decisions
        decision_entries = [
            entry for entry in entries 
            if entry.entry_type == HistoryEntryType.DECISION.value
        ]
        recent_decisions = decision_entries[-max_decisions:]
        
        for entry in recent_decisions:
            decision = DecisionRecord.from_dict(entry.data)
            context["recent_decisions"].append({
                "type": decision.decision_type,
                "target": decision.target,
                "confidence": decision.confidence,
                "priority": decision.priority,
                "game_time": entry.game_time
            })
        
        # Extract recent commands
        command_entries = [
            entry for entry in entries 
            if entry.entry_type == HistoryEntryType.COMMAND.value
        ]
        recent_commands = command_entries[-max_decisions:]
        
        for entry in recent_commands:
            command = CommandRecord.from_dict(entry.data)
            context["recent_commands"].append({
                "type": command.command_type,
                "parameters": command.parameters,
                "executed": command.executed,
                "game_time": entry.game_time
            })
        
        # Generate summary
        if include_summary:
            context["summary"].update(self._generate_summary(entries))
        
        return context
    
    def format_for_prompt(self, max_states: int = 5, max_decisions: int = 3) -> str:
        """
        Format history as a string for inclusion in strategist prompts.
        
        Args:
            max_states: Maximum number of recent states to include
            max_decisions: Maximum number of recent decisions to include
            
        Returns:
            Formatted string suitable for prompt inclusion
        """
        context = self.generate_context(max_states, max_decisions)
        
        lines = [
            "=== Game History Context ===",
            ""
        ]
        
        # Recent states
        if context["recent_states"]:
            lines.append("Recent Game States:")
            for i, state in enumerate(context["recent_states"]):
                lines.append(f"  State {len(context['recent_states']) - i} (t={state.get('game_time', 0):.1f}s):")
                lines.append(f"    Resources: MP={state.get('resources', {}).get('manpower', {}).get('current', 0)}, "
                           f"Fuel={state.get('resources', {}).get('fuel', {}).get('current', 0)}, "
                           f"Munitions={state.get('resources', {}).get('munitions', {}).get('current', 0)}")
                lines.append(f"    Squads: {state.get('squad_count', len(state.get('squads', [])))} units")
                lines.append(f"    Capture Points: {state.get('capture_points_owned', 0)}/{state.get('total_capture_points', 0)}")
                lines.append(f"    Tech: T1={state.get('tier_1', False)}, T2={state.get('tier_2', False)}, T3={state.get('tier_3', False)}")
        
        # Recent decisions
        if context["recent_decisions"]:
            lines.append("")
            lines.append("Recent Decisions:")
            for decision in context["recent_decisions"]:
                lines.append(f"  - {decision['type']} ({decision.get('game_time', 0):.1f}s): "
                           f"target={decision.get('target', 'N/A')}, "
                           f"confidence={decision.get('confidence', 1.0):.2f}")
        
        # Recent commands
        if context["recent_commands"]:
            lines.append("")
            lines.append("Recent Commands:")
            for command in context["recent_commands"]:
                lines.append(f"  - {command['type']} ({command.get('game_time', 0):.1f}s): "
                           f"executed={command.get('executed', False)}")
        
        # Summary
        if context.get("summary"):
            lines.append("")
            lines.append("Summary:")
            summary = context["summary"]
            lines.append(f"  Average resources: MP={summary.get('avg_manpower', 0):.0f}, "
                       f"Fuel={summary.get('avg_fuel', 0):.0f}, Munitions={summary.get('avg_munitions', 0):.0f}")
            lines.append(f"  Squads lost: {summary.get('squads_lost', 0)}, Built: {summary.get('buildings_built', 0)}")
            lines.append(f"  Game phase: {summary.get('game_phase', 'unknown')}")
        
        lines.append("")
        lines.append("=== End Game History Context ===")
        
        return "\n".join(lines)
    
    def get_size(self) -> int:
        """Get the number of entries in history."""
        with self._lock:
            return len(self._entries)
    
    def get_config(self) -> HistoryConfig:
        """Get the current configuration."""
        return self.config
    
    def set_config(self, config: HistoryConfig):
        """Update the configuration."""
        with self._lock:
            self.config = config
            # Recreate deque with new maxlen
            old_entries = list(self._entries)
            self._entries = deque(old_entries[-config.max_entries:], maxlen=config.max_entries)
    
    def save(self, path: Optional[str] = None):
        """
        Save history to a specific file.
        
        Args:
            path: Optional path to save to. Uses configured path if None.
        """
        save_path = Path(path) if path else self._storage_path
        if not save_path:
            return
        
        with self._lock:
            entries = list(self._file_entries)
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                for entry in entries:
                    f.write(entry.to_json() + '\n')
        except OSError as e:
            import warnings
            warnings.warn(f"Failed to save history to {save_path}: {e}")
    
    def load(self, path: Optional[str] = None):
        """
        Load history from a file.
        
        Args:
            path: Optional path to load from. Uses configured path if None.
        """
        load_path = Path(path) if path else self._storage_path
        if not load_path or not load_path.exists():
            return
        
        with self._lock:
            self._file_entries.clear()
        
        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = HistoryEntry.from_json(line)
                            with self._lock:
                                self._file_entries.append(entry)
                                # Also add to in-memory if there's space
                                if len(self._entries) < self.config.max_entries:
                                    self._entries.append(entry)
                        except (json.JSONDecodeError, KeyError):
                            # Skip invalid entries
                            continue
        except OSError as e:
            import warnings
            warnings.warn(f"Failed to load history from {load_path}: {e}")
    
    def _compress_state(self, state: GameState) -> Dict[str, Any]:
        """
        Create a compressed representation of a game state.
        
        This reduces storage requirements while preserving important information.
        
        Args:
            state: GameState object to compress
            
        Returns:
            Compressed dictionary representation
        """
        compressed = {
            "version": state.version,
            "player_id": state.player_id,
            "game_time": state.game_time,
            "game_phase": state.game_phase,
            "faction": state.faction,
            "timestamp": state.timestamp,
            "resources": {},
            "squad_count": len(state.squads),
            "squad_summary": self._compress_squads(state.squads),
            "capture_points": self._compress_capture_points(state.capture_points),
            "capture_points_owned": sum(1 for cp in state.capture_points if cp.owner == state.player_id),
            "total_capture_points": len(state.capture_points),
            "visible_enemies_count": len(state.visible_enemies),
            "tech_tree": state.tech_tree.to_dict(),
            "build_queue_count": len(state.build_queue),
            "population": state.population.to_dict(),
            "avg_resource_income": self._calculate_avg_income(state.resources),
            "avg_resource_stock": self._calculate_avg_stock(state.resources)
        }
        
        # Compress resources
        for resource_name, resource_data in state.resources.items():
            compressed["resources"][resource_name] = {
                "current": resource_data.current,
                "income": resource_data.income
            }
        
        return compressed
    
    def _compress_squads(self, squads: List[SquadData]) -> Dict[str, int]:
        """Compress squad data to type counts."""
        counts = {}
        for squad in squads:
            squad_type = squad.type
            counts[squad_type] = counts.get(squad_type, 0) + 1
        return counts
    
    def _compress_capture_points(self, cps: List[CapturePointData]) -> List[Dict[str, Any]]:
        """Compress capture point data."""
        return [
            {
                "id": cp.id,
                "owner": cp.owner,
                "is_neutral": cp.is_neutral,
                "progress": cp.capture_progress
            }
            for cp in cps
        ]
    
    def _calculate_avg_income(self, resources: Dict[str, ResourceData]) -> float:
        """Calculate average resource income."""
        if not resources:
            return 0.0
        total = sum(r.income for r in resources.values())
        return total / len(resources)
    
    def _calculate_avg_stock(self, resources: Dict[str, ResourceData]) -> float:
        """Calculate average resource stock."""
        if not resources:
            return 0.0
        total = sum(r.current for r in resources.values())
        return total / len(resources)
    
    def _summarize_state(self, state_data: Dict[str, Any], game_time: float) -> Dict[str, Any]:
        """Create a summary of a game state for context."""
        summary = {
            "game_time": game_time,
            "resources": state_data.get("resources", {}),
            "squad_count": state_data.get("squad_count", 0),
            "capture_points_owned": state_data.get("capture_points_owned", 0),
            "total_capture_points": state_data.get("total_capture_points", 0),
            "visible_enemies": state_data.get("visible_enemies_count", 0),
            "tier_1": state_data.get("tech_tree", {}).get("tier_1", False),
            "tier_2": state_data.get("tech_tree", {}).get("tier_2", False),
            "tier_3": state_data.get("tech_tree", {}).get("tier_3", False),
            "population": state_data.get("population", {}),
            "avg_income": state_data.get("avg_resource_income", 0),
            "avg_stock": state_data.get("avg_resource_stock", 0)
        }
        
        # Add squad type breakdown if available
        if "squad_summary" in state_data:
            summary["squad_types"] = state_data["squad_summary"]
        
        return summary
    
    def _generate_summary(self, entries: List[HistoryEntry]) -> Dict[str, Any]:
        """Generate a summary of all history entries."""
        summary = {
            "total_states": 0,
            "total_decisions": 0,
            "total_commands": 0,
            "total_events": 0,
            "avg_manpower": 0,
            "avg_fuel": 0,
            "avg_munitions": 0,
            "squads_lost": 0,
            "buildings_built": 0,
            "game_phase": "early"
        }
        
        resources_sum = {"manpower": 0, "fuel": 0, "munitions": 0}
        resource_counts = {"manpower": 0, "fuel": 0, "munitions": 0}
        
        for entry in entries:
            if entry.entry_type == HistoryEntryType.GAME_STATE.value:
                summary["total_states"] += 1
                state = entry.data
                
                # Extract resources
                resources = state.get("resources", {})
                for res_name in ["manpower", "fuel", "munitions"]:
                    if res_name in resources:
                        resources_sum[res_name] += resources[res_name].get("current", 0)
                        resource_counts[res_name] += 1
                
                # Get game phase
                summary["game_phase"] = state.get("game_phase", summary["game_phase"])
                
                # Track squad changes (would need comparison with previous state)
                
            elif entry.entry_type == HistoryEntryType.DECISION.value:
                summary["total_decisions"] += 1
                
            elif entry.entry_type == HistoryEntryType.COMMAND.value:
                summary["total_commands"] += 1
                
            elif entry.entry_type == HistoryEntryType.EVENT.value:
                summary["total_events"] += 1
        
        # Calculate averages
        for res_name in ["manpower", "fuel", "munitions"]:
            if resource_counts[res_name] > 0:
                summary[f"avg_{res_name}"] = resources_sum[res_name] / resource_counts[res_name]
        
        return summary
    
    def _persist_to_disk(self, entry: HistoryEntry):
        """Persist a single entry to disk."""
        if not self._storage_path or not self.config.persistence_enabled:
            return
        
        try:
            with open(self._storage_path, 'a', encoding='utf-8') as f:
                f.write(entry.to_json() + '\n')
        except OSError as e:
            import warnings
            warnings.warn(f"Failed to persist history entry: {e}")
    
    def _load_from_disk(self):
        """Load existing history from disk."""
        if not self._storage_path or not self._storage_path.exists():
            return
        
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = HistoryEntry.from_json(line)
                            with self._lock:
                                self._file_entries.append(entry)
                                # Add to in-memory if there's space
                                if len(self._entries) < self.config.max_entries:
                                    self._entries.append(entry)
                        except (json.JSONDecodeError, KeyError):
                            continue
        except OSError:
            pass


# ============================================
# Factory Functions
# ============================================

_default_history_manager: Optional[GameHistoryManager] = None


def create_history_manager(config: Optional[HistoryConfig] = None) -> GameHistoryManager:
    """
    Create a new GameHistoryManager instance.
    
    Args:
        config: Optional configuration
        
    Returns:
        New GameHistoryManager instance
    """
    return GameHistoryManager(config)


def get_history_manager(config: Optional[HistoryConfig] = None) -> GameHistoryManager:
    """
    Get or create the default GameHistoryManager singleton.
    
    Args:
        config: Optional configuration for new instance
        
    Returns:
        Default GameHistoryManager instance
    """
    global _default_history_manager
    if _default_history_manager is None:
        _default_history_manager = create_history_manager(config)
    return _default_history_manager


def reset_history_manager() -> None:
    """Reset the default GameHistoryManager singleton."""
    global _default_history_manager
    if _default_history_manager is not None:
        _default_history_manager.clear_all()
    _default_history_manager = None


# ============================================
# Convenience Functions
# ============================================


def add_state_to_history(state: Union[GameState, Dict[str, Any]], game_time: Optional[float] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> HistoryEntry:
    """Add a game state to the default history manager."""
    return get_history_manager().add_state(state, game_time, metadata)


def add_decision_to_history(decision: Union[DecisionRecord, Dict[str, Any]], game_time: Optional[float] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> HistoryEntry:
    """Add a decision to the default history manager."""
    return get_history_manager().add_decision(decision, game_time, metadata)


def add_command_to_history(command: Union[CommandRecord, Dict[str, Any]], game_time: Optional[float] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> HistoryEntry:
    """Add a command to the default history manager."""
    return get_history_manager().add_command(command, game_time, metadata)


def get_recent_states(count: int = 10) -> List[GameState]:
    """Get recent states from the default history manager."""
    return get_history_manager().get_recent_states(count)


def generate_history_context(max_states: int = 5, max_decisions: int = 3) -> Dict[str, Any]:
    """Generate context from the default history manager."""
    return get_history_manager().generate_context(max_states, max_decisions)


def format_history_for_prompt(max_states: int = 5, max_decisions: int = 3) -> str:
    """Format history for prompt from the default history manager."""
    return get_history_manager().format_for_prompt(max_states, max_decisions)
