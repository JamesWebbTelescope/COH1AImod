"""
CoH1 × Mistral AI Mod - Integration Tests for Game History Manager

Integration tests for history.py module with other system components.

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-26
"""

import pytest
import json
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys

# Add python directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))


# ============================================
# Test Fixtures
# ============================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    # Cleanup
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def history_config_with_persistence(temp_dir):
    """Create a history config with persistence enabled."""
    from history import HistoryConfig
    return HistoryConfig(
        max_entries=10,
        max_file_entries=20,
        persistence_enabled=True,
        storage_dir=temp_dir,
        history_file="test_history.jsonl",
        compress_states=False  # Disable compression for tests
    )


@pytest.fixture
def history_config_with_compression(temp_dir):
    """Create a history config with compression enabled."""
    from history import HistoryConfig
    return HistoryConfig(
        max_entries=10,
        max_file_entries=20,
        persistence_enabled=True,
        storage_dir=temp_dir,
        history_file="test_history_compressed.jsonl",
        compress_states=True  # Enable compression for tests
    )


@pytest.fixture
def history_manager_with_persistence(history_config_with_persistence):
    """Create a history manager with persistence."""
    from history import GameHistoryManager
    return GameHistoryManager(history_config_with_persistence)


@pytest.fixture
def history_manager_with_compression(history_config_with_compression):
    """Create a history manager with compression enabled."""
    from history import GameHistoryManager
    return GameHistoryManager(history_config_with_compression)


@pytest.fixture
def mock_game_state():
    """Create a mock game state."""
    from schema import (
        GameState, ResourceData, Position, SquadData,
        CapturePointData, EnemyData, TechTreeData, BuildQueueItem, PopulationData
    )
    
    return GameState(
        version="1.0",
        player_id=1,
        timestamp=time.time(),
        game_time=120.5,
        game_phase="mid",
        faction="allies",
        resources={
            "manpower": ResourceData(current=500, income=10, max=1000),
            "fuel": ResourceData(current=300, income=5, max=500),
            "munitions": ResourceData(current=200, income=3, max=300)
        },
        squads=[
            SquadData(id=1, type="riflemen", health=0.8, max_health=1.0, vet_level=1,
                     position=Position(x=10, y=20, z=0), posture="defensive"),
            SquadData(id=2, type="engineer", health=1.0, max_health=1.0, vet_level=0,
                     position=Position(x=15, y=25, z=0), posture="aggressive")
        ],
        capture_points=[
            CapturePointData(id=1, position=Position(x=50, y=50, z=0), owner=1,
                           capture_progress=1.0, is_neutral=False),
            CapturePointData(id=2, position=Position(x=100, y=100, z=0), owner=None,
                           capture_progress=0.0, is_neutral=True)
        ],
        visible_enemies=[],
        tech_tree=TechTreeData(
            tier_1=True, tier_2=False, tier_3=False,
            abilities=["smoke"],
            tier_1_progress=1.0, tier_2_progress=0.5, tier_3_progress=0.0
        ),
        build_queue=[],
        population=PopulationData(current=20, max=100)
    )


@pytest.fixture
def mock_orchestrator_config():
    """Create a mock orchestrator configuration."""
    from config import Configuration
    
    config = Configuration()
    config._config["orchestrator"] = {
        "history_max_entries": 15,
        "history_max_file_entries": 30,
        "history_include_states": True,
        "history_include_decisions": True,
        "history_include_commands": True,
        "history_compress_states": True
    }
    config._config["ipc"] = {
        "data_dir": "test_data"
    }
    config._config["debug"] = {
        "persist_history": True,
        "history_file": "test_history.jsonl"
    }
    return config


# ============================================
# Integration Test Classes
# ============================================


class TestHistoryWithSchemaIntegration:
    """Test history manager integration with schema module."""
    
    def test_add_game_state_object(self, history_manager_with_persistence, mock_game_state):
        """Test adding a GameState object directly."""
        entry = history_manager_with_persistence.add_state(
            mock_game_state,
            game_time=120.5
        )
        
        assert entry is not None
        assert entry.entry_type == "game_state"
        
        # Verify data was stored
        states = history_manager_with_persistence.get_recent_states(1)
        assert len(states) == 1
        
        # The state should be converted back to GameState
        assert isinstance(states[0], type(mock_game_state))
        assert states[0].game_time == 120.5
    
    def test_compressed_state_storage(self, history_manager_with_compression, mock_game_state):
        """Test that compressed states are stored correctly."""
        # Add a state
        entry = history_manager_with_compression.add_state(mock_game_state, game_time=120.5)
        
        # Get the stored entry from file
        file_entries = list(history_manager_with_compression._file_entries)
        assert len(file_entries) == 1
        
        # The compressed data should have summary fields
        data = file_entries[0].data
        assert "squad_count" in data
        assert "capture_points_owned" in data
        assert "squad_summary" in data
    
    def test_state_serialization_roundtrip(self, history_manager_with_persistence, mock_game_state):
        """Test that states can be serialized and deserialized."""
        # Add a state
        history_manager_with_persistence.add_state(mock_game_state, game_time=100.0)
        
        # Save to disk
        history_manager_with_persistence.save()
        
        # Create new manager and load
        history_manager_with_persistence.load()
        
        # Get states
        states = history_manager_with_persistence.get_recent_states(1)
        
        assert len(states) == 1
        assert states[0].game_time == 100.0


class TestHistoryWithConfigIntegration:
    """Test history manager integration with config module."""
    
    def test_config_from_config_object(self, mock_orchestrator_config):
        """Test creating HistoryConfig from Configuration object."""
        from history import HistoryConfig
        
        history_config = HistoryConfig.from_config(mock_orchestrator_config)
        
        assert history_config.max_entries == 15
        assert history_config.max_file_entries == 30
        assert history_config.include_states == True
        assert history_config.compress_states == True
    
    def test_history_manager_with_orchestrator_config(self, mock_orchestrator_config, temp_dir):
        """Test creating history manager with orchestrator config."""
        from history import GameHistoryManager, HistoryConfig
        
        # Create config from orchestrator config
        history_config = HistoryConfig.from_config(mock_orchestrator_config)
        history_config.storage_dir = temp_dir
        
        manager = GameHistoryManager(history_config)
        
        assert manager.config.max_entries == 15
        assert manager.config.max_file_entries == 30


class TestHistoryWithDecisionIntegration:
    """Test history manager integration with decision records."""
    
    def test_add_decision_record(self, history_manager_with_persistence):
        """Test adding a DecisionRecord object."""
        from history import DecisionRecord
        
        decision = DecisionRecord(
            decision_type="build",
            target="tier_2",
            reasoning="Need more production",
            confidence=0.95,
            priority=1
        )
        
        entry = history_manager_with_persistence.add_decision(decision, game_time=120.5)
        
        assert entry is not None
        assert entry.entry_type == "decision"
        
        # Get decisions
        decisions = history_manager_with_persistence.get_decisions(1)
        assert len(decisions) == 1
        assert decisions[0].decision_type == "build"
        assert decisions[0].target == "tier_2"
    
    def test_add_command_record(self, history_manager_with_persistence):
        """Test adding a CommandRecord object."""
        from history import CommandRecord
        
        command = CommandRecord(
            command_type="BUILD",
            parameters={"engineer_id": 1, "building_type": "tier_2"},
            executed=True,
            execution_time=0.1,
            result="success"
        )
        
        entry = history_manager_with_persistence.add_command(command, game_time=120.5)
        
        assert entry is not None
        assert entry.entry_type == "command"
        
        # Get commands
        commands = history_manager_with_persistence.get_commands(1)
        assert len(commands) == 1
        assert commands[0].command_type == "BUILD"


class TestHistoryPersistenceIntegration:
    """Test history manager persistence with file system."""
    
    def test_persistence_across_instances(self, temp_dir):
        """Test that history persists across manager instances."""
        from history import GameHistoryManager, HistoryConfig
        
        config = HistoryConfig(
            max_entries=10,
            max_file_entries=20,
            persistence_enabled=True,
            storage_dir=temp_dir,
            history_file="shared_history.jsonl"
        )
        
        # Create first manager and add entries
        manager1 = GameHistoryManager(config)
        manager1.add_state({"test": 1}, game_time=100.0)
        manager1.add_state({"test": 2}, game_time=105.0)
        
        # Create second manager (should load from same file)
        manager2 = GameHistoryManager(config)
        
        # Should have loaded entries
        assert manager2.get_size() == 2
        
        # Add more entries to second manager
        manager2.add_state({"test": 3}, game_time=110.0)
        
        # First manager should still have its entries
        assert manager1.get_size() == 2
    
    def test_persistence_file_format(self, history_manager_with_persistence, mock_game_state):
        """Test that persistence file uses correct format."""
        # Add some entries
        history_manager_with_persistence.add_state(mock_game_state, game_time=100.0)
        history_manager_with_persistence.add_state(mock_game_state, game_time=105.0)
        
        # Save explicitly
        history_manager_with_persistence.save()
        
        # Check file contents
        storage_path = history_manager_with_persistence._storage_path
        assert storage_path.exists()
        
        with open(storage_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line.strip())
            assert "timestamp" in data
            assert "game_time" in data
            assert "type" in data
            assert "data" in data


class TestHistoryContextIntegration:
    """Test history context generation for strategist prompts."""
    
    def test_context_for_strategist_prompt(self, history_manager_with_persistence, mock_game_state):
        """Test generating context for strategist prompt."""
        # Add some history
        for i in range(3):
            state = mock_game_state
            state.game_time = 100.0 + i * 10
            history_manager_with_persistence.add_state(state, game_time=state.game_time)
        
        # Add some decisions
        from history import DecisionRecord
        history_manager_with_persistence.add_decision(
            DecisionRecord("build", "tier_2", "Need production", 0.9, 1),
            game_time=105.0
        )
        
        # Generate context
        context = history_manager_with_persistence.generate_context(
            max_states=3,
            max_decisions=1,
            include_summary=True
        )
        
        # Verify structure
        assert "recent_states" in context
        assert len(context["recent_states"]) == 3
        assert "recent_decisions" in context
        assert len(context["recent_decisions"]) == 1
        assert "summary" in context
        assert context["summary"]["total_states"] == 3
    
    def test_format_for_prompt_integration(self, history_manager_with_persistence, mock_game_state):
        """Test formatting history for prompt with realistic data."""
        # Add some states with varying data
        for i in range(3):
            state = mock_game_state
            state.game_time = 100.0 + i * 10
            state.resources["manpower"].current = 500 + i * 100
            history_manager_with_persistence.add_state(state, game_time=state.game_time)
        
        # Format for prompt
        prompt = history_manager_with_persistence.format_for_prompt(
            max_states=3,
            max_decisions=0
        )
        
        # Verify it's a valid string
        assert isinstance(prompt, str)
        assert "=== Game History Context ===" in prompt
        assert "Recent Game States:" in prompt
        
        # Check for resource info
        assert "MP=" in prompt
        assert "Fuel=" in prompt


class TestHistoryWithOrchestratorIntegration:
    """Test history manager integration with orchestrator components."""
    
    def test_history_manager_creation_with_orchestrator(self, mock_orchestrator_config, temp_dir):
        """Test that history manager can be created with orchestrator config."""
        from history import GameHistoryManager, HistoryConfig
        
        # Simulate orchestrator creating a history manager
        history_config = HistoryConfig.from_config(mock_orchestrator_config)
        history_config.storage_dir = temp_dir
        
        manager = GameHistoryManager(history_config)
        
        # Verify it's properly configured
        assert manager.config.max_entries == 15
        assert manager.config.include_states == True
    
    def test_history_context_for_strategist(self, history_manager_with_persistence, mock_game_state):
        """Test that context can be generated for strategist."""
        # Simulate orchestrator adding states and getting context
        
        # Add states at different times
        for i in range(5):
            state = mock_game_state
            state.game_time = 100.0 + i * 20
            state.resources["manpower"].current = 500 + i * 50
            state.resources["fuel"].current = 300 + i * 30
            history_manager_with_persistence.add_state(state, game_time=state.game_time)
        
        # Get context for strategist
        context = history_manager_with_persistence.generate_context(
            max_states=5,
            max_decisions=3,
            include_summary=True
        )
        
        # Verify context has all needed information
        assert len(context["recent_states"]) == 5
        assert "game_time" in context["recent_states"][0]
        assert "resources" in context["recent_states"][0]
        assert "summary" in context
        
        # Verify summary has useful data
        summary = context["summary"]
        assert summary["total_states"] == 5
        assert "avg_manpower" in summary
        assert "avg_fuel" in summary


class TestHistoryEdgeCaseIntegration:
    """Test edge cases in integration scenarios."""
    
    def test_empty_history_context(self, history_manager_with_persistence):
        """Test context generation with empty history."""
        context = history_manager_with_persistence.generate_context()
        
        assert context["recent_states"] == []
        assert context["recent_decisions"] == []
        assert context["recent_commands"] == []
        assert context["summary"]["total_states"] == 0
    
    def test_partial_history_types(self, history_manager_with_persistence, mock_game_state):
        """Test context with only some history types."""
        # Only add states, no decisions or commands
        history_manager_with_persistence.add_state(mock_game_state, game_time=100.0)
        history_manager_with_persistence.add_state(mock_game_state, game_time=105.0)
        
        context = history_manager_with_persistence.generate_context()
        
        assert len(context["recent_states"]) == 2
        assert len(context["recent_decisions"]) == 0
        assert len(context["recent_commands"]) == 0
    
    def test_history_with_missing_data(self, history_manager_with_persistence):
        """Test history with incomplete state data."""
        # Add state with minimal data
        minimal_state = {
            "version": "1.0",
            "player_id": 1
        }
        
        entry = history_manager_with_persistence.add_state(minimal_state, game_time=100.0)
        
        assert entry is not None
        
        # Should still be retrievable
        states = history_manager_with_persistence.get_recent_states(1)
        assert len(states) == 1


class TestHistoryPerformanceIntegration:
    """Test performance characteristics of history manager."""
    
    def test_memory_usage_with_large_history(self, history_manager_with_persistence):
        """Test that history manager handles large histories efficiently."""
        import gc
        
        # Add many entries
        for i in range(100):
            history_manager_with_persistence.add_state(
                {"test": i, "data": [j for j in range(100)]},
                game_time=float(i)
            )
        
        # Should only keep max_entries in memory
        assert history_manager_with_persistence.get_size() <= \
               history_manager_with_persistence.config.max_entries
        
        # Force garbage collection
        gc.collect()
    
    def test_file_persistence_with_many_entries(self, temp_dir):
        """Test persistence with many entries."""
        from history import GameHistoryManager, HistoryConfig
        
        config = HistoryConfig(
            max_entries=10,
            max_file_entries=100,
            persistence_enabled=True,
            storage_dir=temp_dir,
            history_file="large_history.jsonl"
        )
        
        manager = GameHistoryManager(config)
        
        # Add many entries
        for i in range(200):
            manager.add_state({"test": i}, game_time=float(i))
        
        # Check file size
        storage_path = manager._storage_path
        assert storage_path.exists()
        
        # File should have max_file_entries
        file_size = len(manager._file_entries)
        assert file_size == config.max_file_entries


class TestHistoryConcurrencyIntegration:
    """Test concurrency scenarios in integration."""
    
    def test_concurrent_state_addition(self, history_config_with_persistence, mock_game_state):
        """Test concurrent addition of states from multiple sources."""
        from history import GameHistoryManager
        import threading
        
        manager = GameHistoryManager(history_config_with_persistence)
        errors = []
        
        def add_states(thread_id):
            try:
                for i in range(10):
                    state = mock_game_state
                    state.game_time = thread_id * 100 + i
                    manager.add_state(state, game_time=state.game_time)
            except Exception as e:
                errors.append(e)
        
        # Create and start threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=add_states, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Check no errors
        assert len(errors) == 0
        
        # Check entries were added (up to max_entries)
        assert manager.get_size() > 0
        assert manager.get_size() <= history_config_with_persistence.max_entries
