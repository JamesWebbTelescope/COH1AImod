"""
Phase 3: Game History Manager Unit Tests

Tests for the history module (already exists from Phase 2, but adding Phase 3 tests).

Author: Generated for Phase 3 pytest integration
Version: 1.0.0
Date: 2026-11-21
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root and python directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python"))


@pytest.fixture
def history_manager():
    """Create a history manager for testing."""
    from history import GameHistoryManager
    
    manager = GameHistoryManager(max_entries=10)
    yield manager


@pytest.fixture
def temp_history_file():
    """Create a temporary history file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("[]")
        yield f.name
    os.unlink(f.name)


class TestHistoryManagerInitialization:
    """Tests for history manager initialization."""
    
    def test_default_initialization(self, history_manager):
        """Test default history manager initialization."""
        assert history_manager.max_entries == 10
        assert len(history_manager.get_all_entries()) == 0
    
    def test_custom_max_entries(self):
        """Test custom max entries."""
        from history import GameHistoryManager
        
        manager = GameHistoryManager(max_entries=5)
        assert manager.max_entries == 5
    
    def test_initial_state_empty(self, history_manager):
        """Test that initial state is empty."""
        entries = history_manager.get_all_entries()
        assert len(entries) == 0


class TestHistoryManagerAddEntries:
    """Tests for adding entries to history."""
    
    def test_add_single_entry(self, history_manager):
        """Test adding a single entry."""
        entry = {
            "game_time": 120.5,
            "timestamp": datetime.now().timestamp(),
            "resources": {"manpower": {"current": 500}},
            "squads": [],
            "cps": []
        }
        
        history_manager.add_entry(entry)
        
        entries = history_manager.get_all_entries()
        assert len(entries) == 1
        assert entries[0] == entry
    
    def test_add_multiple_entries(self, history_manager):
        """Test adding multiple entries."""
        for i in range(5):
            entry = {
                "game_time": float(i * 30),
                "timestamp": datetime.now().timestamp(),
                "resources": {"manpower": {"current": 100 + i * 100}},
                "squads": [],
                "cps": []
            }
            history_manager.add_entry(entry)
        
        entries = history_manager.get_all_entries()
        assert len(entries) == 5
    
    def test_add_entry_exceeds_max(self, history_manager):
        """Test that adding entries beyond max removes oldest."""
        # Add 15 entries to a manager with max 10
        for i in range(15):
            entry = {
                "game_time": float(i * 30),
                "timestamp": datetime.now().timestamp(),
                "resources": {"manpower": {"current": 100}},
                "squads": [],
                "cps": []
            }
            history_manager.add_entry(entry)
        
        entries = history_manager.get_all_entries()
        assert len(entries) == 10  # Should only keep last 10
        
        # First entry should be game_time = 5*30 = 150 (entries 5-14)
        assert entries[0]["game_time"] == 150.0


class TestHistoryManagerRetrieval:
    """Tests for retrieving entries from history."""
    
    def test_get_all_entries(self, history_manager):
        """Test getting all entries."""
        for i in range(3):
            entry = {"game_time": float(i * 30), "data": f"entry_{i}"}
            history_manager.add_entry(entry)
        
        entries = history_manager.get_all_entries()
        assert len(entries) == 3
    
    def test_get_recent_entries(self, history_manager):
        """Test getting recent entries."""
        for i in range(10):
            entry = {"game_time": float(i * 30), "data": f"entry_{i}"}
            history_manager.add_entry(entry)
        
        recent = history_manager.get_recent_entries(3)
        assert len(recent) == 3
        assert recent[0]["data"] == "entry_7"
        assert recent[1]["data"] == "entry_8"
        assert recent[2]["data"] == "entry_9"
    
    def test_get_recent_entries_more_than_available(self, history_manager):
        """Test getting more entries than available."""
        for i in range(3):
            entry = {"game_time": float(i * 30), "data": f"entry_{i}"}
            history_manager.add_entry(entry)
        
        recent = history_manager.get_recent_entries(10)
        assert len(recent) == 3  # Should return all available
    
    def test_get_last_n_entries(self, history_manager):
        """Test getting last N entries."""
        for i in range(10):
            entry = {"game_time": float(i * 30), "data": f"entry_{i}"}
            history_manager.add_entry(entry)
        
        last_3 = history_manager.get_last_n_entries(3)
        assert len(last_3) == 3


class TestHistoryManagerClear:
    """Tests for clearing history."""
    
    def test_clear_all_entries(self, history_manager):
        """Test clearing all entries."""
        for i in range(5):
            entry = {"game_time": float(i * 30), "data": f"entry_{i}"}
            history_manager.add_entry(entry)
        
        history_manager.clear()
        
        entries = history_manager.get_all_entries()
        assert len(entries) == 0
    
    def test_clear_preserves_max_entries(self, history_manager):
        """Test that clear preserves max entries setting."""
        history_manager.clear()
        
        assert history_manager.max_entries == 10


class TestHistoryManagerStatistics:
    """Tests for history statistics."""
    
    def test_get_entry_count(self, history_manager):
        """Test getting entry count."""
        for i in range(5):
            entry = {"game_time": float(i * 30)}
            history_manager.add_entry(entry)
        
        count = history_manager.get_entry_count()
        assert count == 5
    
    def test_get_entry_count_empty(self, history_manager):
        """Test entry count when empty."""
        count = history_manager.get_entry_count()
        assert count == 0


class TestHistoryEntryStructure:
    """Tests for history entry structure."""
    
    def test_entry_with_all_fields(self, history_manager):
        """Test entry with all expected fields."""
        entry = {
            "version": "1.0",
            "player_id": 1,
            "timestamp": datetime.now().timestamp(),
            "game_time": 120.5,
            "phase": "early",
            "faction": "allies",
            "resources": {
                "manpower": {"current": 500, "income": 10, "max": 1000},
                "fuel": {"current": 300, "income": 5, "max": 800},
                "munitions": {"current": 200, "income": 3, "max": 600}
            },
            "squads": [
                {"id": 1, "type": "riflemen", "health": 0.8, "max_health": 1.0, "pos": [100, 200, 0]}
            ],
            "cps": [
                {"id": 1, "pos": [500, 500, 0], "owner": 1, "capture_progress": 1.0}
            ],
            "tech": {
                "tier_1": True,
                "tier_2": False,
                "tier_3": False
            },
            "queue": [],
            "pop": [11, 100]
        }
        
        history_manager.add_entry(entry)
        
        entries = history_manager.get_all_entries()
        assert len(entries) == 1
        assert entries[0]["game_time"] == 120.5
        assert entries[0]["faction"] == "allies"
    
    def test_entry_with_minimal_fields(self, history_manager):
        """Test entry with minimal fields."""
        entry = {
            "game_time": 120.5,
            "timestamp": datetime.now().timestamp()
        }
        
        history_manager.add_entry(entry)
        
        entries = history_manager.get_all_entries()
        assert len(entries) == 1
        assert entries[0]["game_time"] == 120.5


class TestHistoryManagerWithGameState:
    """Tests for history manager with game state objects."""
    
    def test_add_game_state_dict(self, history_manager):
        """Test adding game state as dictionary."""
        game_state = {
            "game_time": 120.5,
            "phase": "early",
            "faction": "allies",
            "player_id": 1,
            "resources": {"manpower": {"current": 500}},
            "squads": [],
            "cps": [],
            "tech": {},
            "queue": [],
            "pop": [11, 100]
        }
        
        history_manager.add_entry(game_state)
        
        entries = history_manager.get_all_entries()
        assert len(entries) == 1
        assert entries[0]["game_time"] == 120.5
    
    def test_add_multiple_game_states(self, history_manager):
        """Test adding multiple game states."""
        for i in range(5):
            game_state = {
                "game_time": float(i * 30),
                "phase": "early",
                "faction": "allies",
                "player_id": 1,
                "resources": {"manpower": {"current": 100 + i * 100}},
                "squads": [],
                "cps": [],
                "tech": {},
                "queue": [],
                "pop": [11, 100]
            }
            history_manager.add_entry(game_state)
        
        entries = history_manager.get_all_entries()
        assert len(entries) == 5


class TestHistoryManagerThreadSafety:
    """Tests for thread safety (basic)."""
    
    def test_concurrent_access(self, history_manager):
        """Test basic concurrent access (not comprehensive)."""
        import threading
        
        def add_entries(start, count):
            for i in range(start, start + count):
                entry = {"game_time": float(i * 30), "data": f"entry_{i}"}
                history_manager.add_entry(entry)
        
        # Create threads
        threads = []
        for i in range(0, 10, 2):
            t = threading.Thread(target=add_entries, args=(i, 2))
            threads.append(t)
            t.start()
        
        # Wait for threads
        for t in threads:
            t.join()
        
        # Should have 10 entries total
        entries = history_manager.get_all_entries()
        assert len(entries) == 10


class TestHistoryPersistence:
    """Tests for history persistence."""
    
    def test_save_and_load_history(self, temp_history_file):
        """Test saving and loading history."""
        from history import GameHistoryManager
        
        manager = GameHistoryManager(max_entries=10)
        
        # Add entries
        for i in range(5):
            entry = {"game_time": float(i * 30), "data": f"entry_{i}"}
            manager.add_entry(entry)
        
        # Save to file
        manager.save_to_file(temp_history_file)
        
        # Create new manager and load
        new_manager = GameHistoryManager(max_entries=10)
        new_manager.load_from_file(temp_history_file)
        
        entries = new_manager.get_all_entries()
        assert len(entries) == 5


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
