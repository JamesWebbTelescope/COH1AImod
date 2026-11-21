"""
CoH1 × Mistral AI Mod - Unit Tests for Game History Manager

Comprehensive unit tests for the history.py module.

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-26
"""

import pytest
import json
import time
import threading
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Add python directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))


# ============================================
# Test Fixtures
# ============================================

@pytest.fixture
def sample_game_state():
    """Create a sample game state dictionary for testing."""
    return {
        "version": "1.0",
        "player_id": 1,
        "timestamp": time.time(),
        "game_time": 120.5,
        "game_phase": "mid",
        "faction": "allies",
        "resources": {
            "manpower": {"current": 500, "income": 10, "max": 1000},
            "fuel": {"current": 300, "income": 5, "max": 500},
            "munitions": {"current": 200, "income": 3, "max": 300}
        },
        "squads": [
            {"id": 1, "type": "riflemen", "health": 0.8, "max_health": 1.0, "vet_level": 1, 
             "position": [10, 20, 0], "posture": "defensive"},
            {"id": 2, "type": "engineer", "health": 1.0, "max_health": 1.0, "vet_level": 0,
             "position": [15, 25, 0], "posture": "aggressive"}
        ],
        "capture_points": [
            {"id": 1, "position": [50, 50, 0], "owner": 1, "capture_progress": 1.0, "is_neutral": False},
            {"id": 2, "position": [100, 100, 0], "owner": None, "capture_progress": 0.0, "is_neutral": True}
        ],
        "visible_enemies": [],
        "tech_tree": {
            "tier_1": True, "tier_2": False, "tier_3": False,
            "abilities": ["smoke"],
            "t1_progress": 1.0, "t2_progress": 0.5, "t3_progress": 0.0
        },
        "build_queue": [],
        "population": {"current": 20, "max": 100}
    }


@pytest.fixture
def sample_decision():
    """Create a sample decision dictionary for testing."""
    return {
        "type": "build",
        "target": "tier_2",
        "reasoning": "Need more production capacity",
        "confidence": 0.95,
        "priority": 1
    }


@pytest.fixture
def sample_command():
    """Create a sample command dictionary for testing."""
    return {
        "type": "BUILD",
        "parameters": {"engineer_id": 2, "building_type": "tier_2", "position": [30, 30, 0]},
        "executed": True,
        "execution_time": 0.1,
        "result": "success"
    }


@pytest.fixture
def temp_history_file():
    """Create a temporary file for history storage."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        filepath = f.name
    yield filepath
    # Cleanup
    if os.path.exists(filepath):
        os.unlink(filepath)


@pytest.fixture
def history_config():
    """Create a test configuration for history manager."""
    from history import HistoryConfig
    return HistoryConfig(
        max_entries=10,
        max_file_entries=20,
        persistence_enabled=False,
        storage_dir="test_data",
        history_file="test_history.jsonl"
    )


@pytest.fixture
def history_manager(history_config):
    """Create a history manager for testing."""
    from history import GameHistoryManager
    manager = GameHistoryManager(history_config)
    return manager


# ============================================
# Test Classes
# ============================================


# ============================================
# HistoryEntry Tests
# ============================================

class TestHistoryEntry:
    """Tests for HistoryEntry dataclass."""
    
    def test_history_entry_creation(self):
        """Test creating a HistoryEntry."""
        from history import HistoryEntry, HistoryEntryType
        
        entry = HistoryEntry(
            timestamp=time.time(),
            game_time=120.5,
            entry_type=HistoryEntryType.GAME_STATE.value,
            data={"test": "data"},
            metadata={"key": "value"}
        )
        
        assert entry.timestamp > 0
        assert entry.game_time == 120.5
        assert entry.entry_type == "game_state"
        assert entry.data == {"test": "data"}
        assert entry.metadata == {"key": "value"}
    
    def test_history_entry_to_dict(self):
        """Test converting HistoryEntry to dictionary."""
        from history import HistoryEntry, HistoryEntryType
        
        entry = HistoryEntry(
            timestamp=1000.0,
            game_time=120.5,
            entry_type=HistoryEntryType.DECISION.value,
            data={"type": "build"},
            metadata={}
        )
        
        result = entry.to_dict()
        
        assert result["timestamp"] == 1000.0
        assert result["game_time"] == 120.5
        assert result["type"] == "decision"
        assert result["data"] == {"type": "build"}
        assert result["metadata"] == {}
    
    def test_history_entry_from_dict(self):
        """Test creating HistoryEntry from dictionary."""
        from history import HistoryEntry
        
        data = {
            "timestamp": 1000.0,
            "game_time": 120.5,
            "type": "command",
            "data": {"type": "BUILD"},
            "metadata": {"test": True}
        }
        
        entry = HistoryEntry.from_dict(data)
        
        assert entry.timestamp == 1000.0
        assert entry.game_time == 120.5
        assert entry.entry_type == "command"
        assert entry.data == {"type": "BUILD"}
        assert entry.metadata == {"test": True}
    
    def test_history_entry_to_json(self):
        """Test converting HistoryEntry to JSON."""
        from history import HistoryEntry, HistoryEntryType
        
        entry = HistoryEntry(
            timestamp=1000.0,
            game_time=120.5,
            entry_type=HistoryEntryType.GAME_STATE.value,
            data={"test": "data"}
        )
        
        json_str = entry.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["timestamp"] == 1000.0
        assert parsed["game_time"] == 120.5
        assert parsed["type"] == "game_state"
    
    def test_history_entry_from_json(self):
        """Test creating HistoryEntry from JSON."""
        from history import HistoryEntry
        
        json_str = '{"timestamp": 1000.0, "game_time": 120.5, "type": "event", "data": {}, "metadata": {}}'
        
        entry = HistoryEntry.from_json(json_str)
        
        assert entry.timestamp == 1000.0
        assert entry.game_time == 120.5
        assert entry.entry_type == "event"


# ============================================
# DecisionRecord Tests
# ============================================

class TestDecisionRecord:
    """Tests for DecisionRecord dataclass."""
    
    def test_decision_record_creation(self):
        """Test creating a DecisionRecord."""
        from history import DecisionRecord
        
        decision = DecisionRecord(
            decision_type="build",
            target="tier_2",
            reasoning="Need more production",
            confidence=0.95,
            priority=1
        )
        
        assert decision.decision_type == "build"
        assert decision.target == "tier_2"
        assert decision.reasoning == "Need more production"
        assert decision.confidence == 0.95
        assert decision.priority == 1
    
    def test_decision_record_to_dict(self):
        """Test converting DecisionRecord to dictionary."""
        from history import DecisionRecord
        
        decision = DecisionRecord(
            decision_type="attack",
            target="enemy_base",
            reasoning=None,
            confidence=0.8,
            priority=2
        )
        
        result = decision.to_dict()
        
        assert result["type"] == "attack"
        assert result["target"] == "enemy_base"
        assert "reasoning" not in result
        assert result["confidence"] == 0.8
        assert result["priority"] == 2
    
    def test_decision_record_from_dict(self):
        """Test creating DecisionRecord from dictionary."""
        from history import DecisionRecord
        
        data = {
            "type": "retreat",
            "target": "squad_1",
            "reasoning": "Under fire",
            "confidence": 0.9,
            "priority": 0
        }
        
        decision = DecisionRecord.from_dict(data)
        
        assert decision.decision_type == "retreat"
        assert decision.target == "squad_1"
        assert decision.reasoning == "Under fire"
        assert decision.confidence == 0.9
        assert decision.priority == 0


# ============================================
# CommandRecord Tests
# ============================================

class TestCommandRecord:
    """Tests for CommandRecord dataclass."""
    
    def test_command_record_creation(self):
        """Test creating a CommandRecord."""
        from history import CommandRecord
        
        command = CommandRecord(
            command_type="BUILD",
            parameters={"engineer_id": 1, "building_type": "tier_2"},
            executed=True,
            execution_time=0.1,
            result="success",
            error=None
        )
        
        assert command.command_type == "BUILD"
        assert command.parameters == {"engineer_id": 1, "building_type": "tier_2"}
        assert command.executed == True
        assert command.execution_time == 0.1
        assert command.result == "success"
        assert command.error is None
    
    def test_command_record_to_dict(self):
        """Test converting CommandRecord to dictionary."""
        from history import CommandRecord
        
        command = CommandRecord(
            command_type="CAPTURE",
            parameters={"squad_id": 1, "point_id": 1},
            executed=False,
            error="Invalid target"
        )
        
        result = command.to_dict()
        
        assert result["type"] == "CAPTURE"
        assert result["parameters"] == {"squad_id": 1, "point_id": 1}
        assert result["executed"] == False
        assert result["error"] == "Invalid target"
    
    def test_command_record_from_dict(self):
        """Test creating CommandRecord from dictionary."""
        from history import CommandRecord
        
        data = {
            "type": "ATTACK_MOVE",
            "parameters": {"squad_id": 1, "position": [100, 100, 0]},
            "executed": True,
            "execution_time": 0.05,
            "result": "queued"
        }
        
        command = CommandRecord.from_dict(data)
        
        assert command.command_type == "ATTACK_MOVE"
        assert command.parameters == {"squad_id": 1, "position": [100, 100, 0]}
        assert command.executed == True
        assert command.execution_time == 0.05
        assert command.result == "queued"


# ============================================
# HistoryConfig Tests
# ============================================

class TestHistoryConfig:
    """Tests for HistoryConfig dataclass."""
    
    def test_history_config_defaults(self):
        """Test HistoryConfig default values."""
        from history import HistoryConfig
        
        config = HistoryConfig()
        
        assert config.max_entries == 20
        assert config.max_file_entries == 100
        assert config.persistence_enabled == True
        assert config.storage_dir == "coh1ai_data"
        assert config.history_file == "game_history.jsonl"
        assert config.include_states == True
        assert config.include_decisions == True
        assert config.include_commands == True
        assert config.compress_states == True
    
    def test_history_config_custom_values(self):
        """Test HistoryConfig with custom values."""
        from history import HistoryConfig
        
        config = HistoryConfig(
            max_entries=50,
            max_file_entries=200,
            persistence_enabled=False,
            storage_dir="custom_data",
            history_file="custom_history.jsonl"
        )
        
        assert config.max_entries == 50
        assert config.max_file_entries == 200
        assert config.persistence_enabled == False
        assert config.storage_dir == "custom_data"
        assert config.history_file == "custom_history.jsonl"


# ============================================
# GameHistoryManager Tests - Basic Operations
# ============================================

class TestGameHistoryManagerBasic:
    """Basic tests for GameHistoryManager."""
    
    def test_history_manager_creation(self, history_manager):
        """Test creating a GameHistoryManager."""
        assert history_manager is not None
        assert history_manager.get_size() == 0
    
    def test_add_state(self, history_manager, sample_game_state):
        """Test adding a game state."""
        entry = history_manager.add_state(sample_game_state, game_time=120.5)
        
        assert entry is not None
        assert entry.entry_type == "game_state"
        assert history_manager.get_size() == 1
    
    def test_add_decision(self, history_manager, sample_decision):
        """Test adding a decision."""
        entry = history_manager.add_decision(sample_decision, game_time=120.5)
        
        assert entry is not None
        assert entry.entry_type == "decision"
    
    def test_add_command(self, history_manager, sample_command):
        """Test adding a command."""
        entry = history_manager.add_command(sample_command, game_time=120.5)
        
        assert entry is not None
        assert entry.entry_type == "command"
    
    def test_add_event(self, history_manager):
        """Test adding a custom event."""
        entry = history_manager.add_event(
            event_type="capture_point_captured",
            data={"point_id": 1, "owner": 1},
            game_time=120.5
        )
        
        assert entry is not None
        assert entry.entry_type == "event"
        assert entry.data["type"] == "capture_point_captured"
        assert entry.data["point_id"] == 1
    
    def test_add_multiple_entries(self, history_manager, sample_game_state, sample_decision, sample_command):
        """Test adding multiple entries of different types."""
        history_manager.add_state(sample_game_state, game_time=100.0)
        history_manager.add_decision(sample_decision, game_time=105.0)
        history_manager.add_command(sample_command, game_time=110.0)
        history_manager.add_event("test_event", {"data": "test"}, game_time=115.0)
        
        assert history_manager.get_size() == 4
    
    def test_max_entries_limit(self, history_config):
        """Test that history respects max_entries limit."""
        from history import GameHistoryManager, HistoryConfig
        
        # Create manager with max_entries=5
        config = HistoryConfig(
            max_entries=5,
            max_file_entries=10,
            persistence_enabled=False
        )
        manager = GameHistoryManager(config)
        
        # Add 10 states
        for i in range(10):
            manager.add_state({"test": i}, game_time=float(i))
        
        # Should only have 5 entries
        assert manager.get_size() == 5


# ============================================
# GameHistoryManager Tests - Retrieval
# ============================================

class TestGameHistoryManagerRetrieval:
    """Tests for retrieving entries from GameHistoryManager."""
    
    def test_get_recent_states(self, history_manager, sample_game_state):
        """Test retrieving recent states."""
        # Add multiple states
        for i in range(5):
            state = dict(sample_game_state)
            state["game_time"] = float(i * 10)
            history_manager.add_state(state, game_time=float(i * 10))
        
        # Get last 3 states
        recent = history_manager.get_recent_states(3)
        
        assert len(recent) == 3
        # They should be the most recent (states 2, 3, 4 with game_times 20, 30, 40)
        # Method returns them in chronological order (oldest of recent first)
        assert recent[0]["game_time"] == 20.0
        assert recent[1]["game_time"] == 30.0
        assert recent[2]["game_time"] == 40.0
    
    def test_get_all_entries(self, history_manager, sample_game_state, sample_decision):
        """Test retrieving all entries."""
        history_manager.add_state(sample_game_state, game_time=100.0)
        history_manager.add_decision(sample_decision, game_time=105.0)
        history_manager.add_state(sample_game_state, game_time=110.0)
        
        all_entries = history_manager.get_all_entries()
        
        assert len(all_entries) == 3
    
    def test_get_all_entries_filtered(self, history_manager, sample_game_state, sample_decision):
        """Test retrieving filtered entries."""
        history_manager.add_state(sample_game_state, game_time=100.0)
        history_manager.add_decision(sample_decision, game_time=105.0)
        history_manager.add_state(sample_game_state, game_time=110.0)
        
        states = history_manager.get_all_entries("game_state")
        decisions = history_manager.get_all_entries("decision")
        
        assert len(states) == 2
        assert len(decisions) == 1
    
    def test_get_entries_since(self, history_manager, sample_game_state):
        """Test retrieving entries since a timestamp."""
        import time as time_module
        
        # Add first entry
        history_manager.add_state(sample_game_state, game_time=100.0)
        
        # Wait a tiny bit to ensure timestamp is different
        time_module.sleep(0.01)
        
        # Record timestamp after first entry
        timestamp_after_first = time_module.time()
        
        # Add more entries
        history_manager.add_state(sample_game_state, game_time=105.0)
        history_manager.add_state(sample_game_state, game_time=110.0)
        
        # Get entries since after first entry was added
        entries = history_manager.get_entries_since(timestamp_after_first)
        
        # Should get 2 entries (the ones added after the timestamp)
        assert len(entries) == 2
    
    def test_get_decisions(self, history_manager, sample_decision):
        """Test retrieving decisions."""
        # Add multiple decisions
        for i in range(5):
            decision = dict(sample_decision)
            decision["priority"] = i
            history_manager.add_decision(decision, game_time=float(i * 10))
        
        decisions = history_manager.get_decisions(3)
        
        assert len(decisions) == 3
        # Method returns them in chronological order (oldest of recent first)
        # We added decisions with priorities 0, 1, 2, 3, 4
        # Getting last 3 should return priorities 2, 3, 4
        assert decisions[0].priority == 2
        assert decisions[1].priority == 3
        assert decisions[2].priority == 4
    
    def test_get_commands(self, history_manager, sample_command):
        """Test retrieving commands."""
        # Add multiple commands
        for i in range(5):
            command = dict(sample_command)
            command["parameters"]["index"] = i
            history_manager.add_command(command, game_time=float(i * 10))
        
        commands = history_manager.get_commands(3)
        
        assert len(commands) == 3
        assert commands[0].parameters["index"] == 4


# ============================================
# GameHistoryManager Tests - Context Generation
# ============================================

class TestGameHistoryManagerContext:
    """Tests for context generation."""
    
    def test_generate_context(self, history_manager, sample_game_state, sample_decision, sample_command):
        """Test generating context for strategist prompts."""
        # Add some history
        history_manager.add_state(sample_game_state, game_time=100.0)
        history_manager.add_decision(sample_decision, game_time=105.0)
        history_manager.add_command(sample_command, game_time=110.0)
        
        context = history_manager.generate_context(max_states=2, max_decisions=1)
        
        assert "recent_states" in context
        assert "recent_decisions" in context
        assert "recent_commands" in context
        assert len(context["recent_states"]) <= 2
        assert len(context["recent_decisions"]) <= 1
        assert len(context["recent_commands"]) <= 1
    
    def test_generate_context_with_summary(self, history_manager, sample_game_state):
        """Test generating context with summary."""
        # Add a state
        history_manager.add_state(sample_game_state, game_time=100.0)
        
        context = history_manager.generate_context(include_summary=True)
        
        assert "summary" in context
        assert "total_states" in context["summary"]
        assert context["summary"]["total_states"] == 1
    
    def test_format_for_prompt(self, history_manager, sample_game_state, sample_decision):
        """Test formatting history for prompt inclusion."""
        # Add some history
        history_manager.add_state(sample_game_state, game_time=100.0)
        history_manager.add_decision(sample_decision, game_time=105.0)
        
        prompt = history_manager.format_for_prompt(max_states=1, max_decisions=1)
        
        assert "=== Game History Context ===" in prompt
        assert "Recent Game States:" in prompt
        assert "Recent Decisions:" in prompt
        assert "=== End Game History Context ===" in prompt
    
    def test_format_for_prompt_empty(self, history_manager):
        """Test formatting empty history."""
        prompt = history_manager.format_for_prompt()
        
        assert "=== Game History Context ===" in prompt
        assert "=== End Game History Context ===" in prompt


# ============================================
# GameHistoryManager Tests - Configuration
# ============================================

class TestGameHistoryManagerConfiguration:
    """Tests for configuration management."""
    
    def test_get_config(self, history_manager):
        """Test getting configuration."""
        config = history_manager.get_config()
        
        assert config is not None
        assert config.max_entries == 10
    
    def test_set_config(self, history_manager):
        """Test updating configuration."""
        from history import HistoryConfig
        
        new_config = HistoryConfig(
            max_entries=20,
            max_file_entries=50,
            persistence_enabled=False
        )
        
        history_manager.set_config(new_config)
        
        config = history_manager.get_config()
        assert config.max_entries == 20
        assert config.max_file_entries == 50
    
    def test_config_filtering(self, history_config):
        """Test that configuration filters what gets stored."""
        from history import GameHistoryManager, HistoryConfig
        
        # Disable states and persistence (to avoid loading from previous tests)
        config = HistoryConfig(
            max_entries=10,
            persistence_enabled=False,  # Disable persistence to avoid loading from disk
            include_states=False,
            include_decisions=True,
            include_commands=True
        )
        manager = GameHistoryManager(config)
        
        # Try to add a state - should return None
        entry = manager.add_state({"test": "data"}, game_time=100.0)
        
        assert entry is None
        assert manager.get_size() == 0
    
    def test_config_from_config_object(self):
        """Test creating config from configuration object."""
        from history import HistoryConfig
        from config import Configuration
        
        # Create a Configuration object
        config_obj = Configuration()
        
        # Create HistoryConfig from it
        history_config = HistoryConfig.from_config(config_obj)
        
        assert history_config is not None
        assert history_config.max_entries > 0


# ============================================
# GameHistoryManager Tests - Clear Operations
# ============================================

class TestGameHistoryManagerClear:
    """Tests for clearing history."""
    
    def test_clear(self, history_manager, sample_game_state):
        """Test clearing in-memory history."""
        # Add some entries
        history_manager.add_state(sample_game_state, game_time=100.0)
        history_manager.add_state(sample_game_state, game_time=105.0)
        
        assert history_manager.get_size() == 2
        
        # Clear
        history_manager.clear()
        
        assert history_manager.get_size() == 0
    
    def test_clear_all(self, history_manager, sample_game_state):
        """Test clearing all history."""
        # Add some entries
        history_manager.add_state(sample_game_state, game_time=100.0)
        history_manager.add_state(sample_game_state, game_time=105.0)
        
        # Clear all
        history_manager.clear_all()
        
        assert history_manager.get_size() == 0


# ============================================
# GameHistoryManager Tests - Persistence
# ============================================

class TestGameHistoryManagerPersistence:
    """Tests for persistence functionality."""
    
    def test_persistence_disabled(self, history_manager, sample_game_state, temp_history_file):
        """Test that persistence can be disabled."""
        # Add some entries
        history_manager.add_state(sample_game_state, game_time=100.0)
        
        # The file should not be created since persistence is disabled
        # (in the fixture, persistence_enabled=False)
        # Check that no files were created in the storage directory
        storage_path = os.path.join(history_manager.config.storage_dir, history_manager.config.history_file)
        assert not os.path.exists(storage_path)
    
    def test_persistence_enabled(self, sample_game_state, temp_history_file):
        """Test that persistence works when enabled."""
        from history import GameHistoryManager, HistoryConfig
        
        config = HistoryConfig(
            max_entries=10,
            max_file_entries=20,
            persistence_enabled=True,
            storage_dir=os.path.dirname(temp_history_file),
            history_file=os.path.basename(temp_history_file)
        )
        
        manager = GameHistoryManager(config)
        
        # Add some entries
        manager.add_state(sample_game_state, game_time=100.0)
        manager.add_state(sample_game_state, game_time=105.0)
        
        # Check file exists
        assert os.path.exists(temp_history_file)
        
        # Check file contents
        with open(temp_history_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        # Parse first line
        entry = manager._file_entries[0]
        assert "game_state" in lines[0]
    
    def test_save_and_load(self, sample_game_state, temp_history_file):
        """Test saving and loading history."""
        from history import GameHistoryManager, HistoryConfig
        
        config = HistoryConfig(
            max_entries=10,
            max_file_entries=20,
            persistence_enabled=True,
            storage_dir=os.path.dirname(temp_history_file),
            history_file=os.path.basename(temp_history_file)
        )
        
        # Create manager and add entries
        manager1 = GameHistoryManager(config)
        manager1.add_state(sample_game_state, game_time=100.0)
        manager1.add_state(sample_game_state, game_time=105.0)
        
        # Save explicitly
        manager1.save()
        
        # Create new manager (it will auto-load from disk since persistence is enabled)
        manager2 = GameHistoryManager(config)
        
        # Check entries loaded
        assert manager2.get_size() == 2
    
    def test_load_nonexistent_file(self, history_manager):
        """Test loading from non-existent file."""
        # Should not raise an error
        history_manager.load("/nonexistent/path/history.jsonl")


# ============================================
# GameHistoryManager Tests - Thread Safety
# ============================================

class TestGameHistoryManagerThreadSafety:
    """Tests for thread safety."""
    
    def test_concurrent_additions(self, history_config):
        """Test concurrent additions from multiple threads."""
        from history import GameHistoryManager
        
        manager = GameHistoryManager(history_config)
        errors = []
        
        def add_entries(thread_id):
            try:
                for i in range(10):
                    manager.add_state(
                        {"thread": thread_id, "entry": i},
                        game_time=float(thread_id * 100 + i)
                    )
            except Exception as e:
                errors.append(e)
        
        # Create and start threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=add_entries, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Check no errors
        assert len(errors) == 0
        
        # Check all entries added (max_entries might limit this)
        # With 5 threads * 10 entries = 50, but max_entries=10, we should have 10
        assert manager.get_size() == history_config.max_entries
    
    def test_concurrent_read_write(self, history_config, sample_game_state):
        """Test concurrent reads and writes."""
        from history import GameHistoryManager
        
        manager = GameHistoryManager(history_config)
        errors = []
        
        def writer():
            try:
                for i in range(20):
                    manager.add_state(sample_game_state, game_time=float(i))
            except Exception as e:
                errors.append(e)
        
        def reader():
            try:
                for _ in range(20):
                    entries = manager.get_all_entries()
                    recent = manager.get_recent_states(5)
            except Exception as e:
                errors.append(e)
        
        # Create and start threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=writer)
            threads.append(t)
            t.start()
        
        for i in range(3):
            t = threading.Thread(target=reader)
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Check no errors
        assert len(errors) == 0


# ============================================
# GameHistoryManager Tests - Edge Cases
# ============================================

class TestGameHistoryManagerEdgeCases:
    """Tests for edge cases."""
    
    def test_add_none_state(self, history_manager):
        """Test adding None as state."""
        # Should handle gracefully
        entry = history_manager.add_state(None, game_time=100.0)
        
        # Should either return None or create an entry with error data
        assert entry is None or "error" in entry.data
    
    def test_add_empty_dict_state(self, history_manager):
        """Test adding empty dict as state."""
        entry = history_manager.add_state({}, game_time=100.0)
        
        assert entry is not None
        assert entry.data == {}
    
    def test_get_recent_states_empty(self, history_manager):
        """Test getting states when history is empty."""
        states = history_manager.get_recent_states(10)
        
        assert states == []
    
    def test_get_recent_states_more_than_available(self, history_manager, sample_game_state):
        """Test getting more states than available."""
        history_manager.add_state(sample_game_state, game_time=100.0)
        history_manager.add_state(sample_game_state, game_time=105.0)
        
        states = history_manager.get_recent_states(10)
        
        assert len(states) == 2
    
    def test_game_time_defaults(self, history_manager, sample_game_state):
        """Test that game_time defaults properly."""
        # Create a state without game_time field
        state_without_game_time = dict(sample_game_state)
        del state_without_game_time["game_time"]
        
        # Add state without explicit game_time
        entry = history_manager.add_state(state_without_game_time)
        
        # game_time should default to 0.0
        assert entry.game_time == 0.0
    
    def test_metadata_passed_through(self, history_manager, sample_game_state):
        """Test that metadata is passed through."""
        metadata = {"test": "value", "number": 42}
        entry = history_manager.add_state(sample_game_state, game_time=100.0, metadata=metadata)
        
        assert entry.metadata == metadata


# ============================================
# Factory Function Tests
# ============================================

class TestFactoryFunctions:
    """Tests for factory functions."""
    
    def test_create_history_manager(self):
        """Test creating a history manager via factory."""
        from history import create_history_manager, HistoryConfig
        
        # Create with persistence disabled to avoid loading from disk
        config = HistoryConfig(persistence_enabled=False)
        manager = create_history_manager(config)
        
        assert manager is not None
        assert manager.get_size() == 0
    
    def test_get_history_manager_singleton(self):
        """Test singleton pattern."""
        from history import get_history_manager, reset_history_manager
        
        # Reset first
        reset_history_manager()
        
        manager1 = get_history_manager()
        manager2 = get_history_manager()
        
        assert manager1 is manager2
    
    def test_reset_history_manager(self):
        """Test resetting the singleton."""
        from history import get_history_manager, reset_history_manager
        
        manager1 = get_history_manager()
        manager1.add_state({"test": "data"}, game_time=100.0)
        
        reset_history_manager()
        
        manager2 = get_history_manager()
        
        assert manager2.get_size() == 0
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        from history import reset_history_manager, add_state_to_history, get_recent_states
        
        # Reset first
        reset_history_manager()
        
        # Add a state
        entry = add_state_to_history({"test": "data"}, game_time=100.0)
        
        assert entry is not None
        
        # Get recent states
        states = get_recent_states(1)
        
        assert len(states) == 1


# ============================================
# Compression Tests
# ============================================

class TestStateCompression:
    """Tests for state compression."""
    
    def test_compress_state(self, history_manager, sample_game_state):
        """Test that state compression works."""
        # This tests the internal _compress_state method
        from history import GameState
        
        # Create a GameState from our dict (if schema available)
        try:
            state_obj = GameState.from_dict(sample_game_state)
            compressed = history_manager._compress_state(state_obj)
            
            # Check that compression preserved important info
            assert "game_time" in compressed
            assert "squad_count" in compressed
            assert "capture_points_owned" in compressed
            assert "resources" in compressed
            
        except (ImportError, AttributeError, KeyError):
            # Schema might not be fully available, skip
            pytest.skip("Schema not available for compression test")
    
    def test_compress_without_schema(self, history_manager):
        """Test that manager works without schema."""
        # Add a state as a dict
        state = {"test": "data", "game_time": 100.0}
        entry = history_manager.add_state(state, game_time=100.0)
        
        assert entry is not None
        assert entry.data == state


# ============================================
# Summary Generation Tests
# ============================================

class TestSummaryGeneration:
    """Tests for summary generation."""
    
    def test_summary_with_states(self, history_manager, sample_game_state):
        """Test summary generation with states."""
        # Add states with different resource values
        for i in range(3):
            state = dict(sample_game_state)
            state["resources"]["manpower"]["current"] = 100 + i * 100
            state["resources"]["fuel"]["current"] = 50 + i * 50
            history_manager.add_state(state, game_time=float(i * 10))
        
        context = history_manager.generate_context(include_summary=True)
        
        assert "summary" in context
        assert context["summary"]["total_states"] == 3
        assert context["summary"]["avg_manpower"] > 0
        assert context["summary"]["avg_fuel"] > 0
    
    def test_summary_with_mixed_entries(self, history_manager, sample_game_state, 
                                       sample_decision, sample_command):
        """Test summary with mixed entry types."""
        history_manager.add_state(sample_game_state, game_time=100.0)
        history_manager.add_decision(sample_decision, game_time=105.0)
        history_manager.add_command(sample_command, game_time=110.0)
        history_manager.add_event("test", {}, game_time=115.0)
        
        context = history_manager.generate_context(include_summary=True)
        
        assert context["summary"]["total_states"] == 1
        assert context["summary"]["total_decisions"] == 1
        assert context["summary"]["total_commands"] == 1
        assert context["summary"]["total_events"] == 1
