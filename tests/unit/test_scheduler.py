"""
Unit Tests for Scheduler Module

Tests the tick schedulers for strategic and fast decision-making.
"""

import time
import threading
import pytest
from pathlib import Path
import sys

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from scheduler import (
    SchedulerState, SchedulerStats, BaseTickScheduler,
    StrategicTickScheduler, FastTickScheduler, SchedulerManager,
    create_schedulers
)


class TestSchedulerStats:
    """Test scheduler statistics."""
    
    def test_scheduler_stats_defaults(self):
        """Test default scheduler statistics values."""
        stats = SchedulerStats()
        
        assert stats.ticks == 0
        assert stats.missed_ticks == 0
        assert stats.average_interval == 0.0
        assert stats.last_tick_time == 0.0
        assert stats.start_time == 0.0
        assert stats.state_changes == 0
    
    def test_scheduler_stats_to_dict(self):
        """Test scheduler stats to dictionary."""
        stats = SchedulerStats()
        stats.ticks = 10
        stats.missed_ticks = 1
        stats.average_interval = 1.0
        
        result = stats.to_dict()
        
        assert result["ticks"] == 10
        assert result["missed_ticks"] == 1
        assert result["average_interval"] == 1.0


class TestBaseTickScheduler:
    """Test base tick scheduler functionality."""
    
    def test_scheduler_creation(self):
        """Test creating a base scheduler."""
        scheduler = BaseTickScheduler(interval=1.0, name="TestScheduler")
        
        assert scheduler.interval == 1.0
        assert scheduler.name == "TestScheduler"
        assert scheduler.state == SchedulerState.STOPPED
        assert scheduler.callback is None
    
    def test_set_callback(self):
        """Test setting a callback."""
        scheduler = BaseTickScheduler(interval=1.0)
        
        called = [False]
        def test_callback():
            called[0] = True
        
        scheduler.set_callback(test_callback)
        assert scheduler.callback is test_callback
    
    def test_set_interval(self):
        """Test setting interval."""
        scheduler = BaseTickScheduler(interval=1.0)
        
        scheduler.set_interval(2.0)
        assert scheduler.interval == 2.0
    
    def test_start_stop(self):
        """Test starting and stopping scheduler."""
        scheduler = BaseTickScheduler(interval=0.5)
        
        # Start
        assert scheduler.start()
        assert scheduler.running
        assert scheduler.state == SchedulerState.RUNNING
        
        # Stop
        assert scheduler.stop()
        assert not scheduler.running
        assert scheduler.state == SchedulerState.STOPPED
    
    def test_double_start(self):
        """Test starting scheduler twice."""
        scheduler = BaseTickScheduler(interval=0.5)
        
        assert scheduler.start()
        assert not scheduler.start()  # Second start should fail
    
    def test_stop_without_start(self):
        """Test stopping scheduler without starting."""
        scheduler = BaseTickScheduler(interval=0.5)
        
        assert scheduler.stop()
    
    def test_callback_execution(self):
        """Test that callback is executed."""
        scheduler = BaseTickScheduler(interval=0.1)
        
        tick_count = [0]
        def test_callback():
            tick_count[0] += 1
        
        scheduler.set_callback(test_callback)
        scheduler.start()
        
        try:
            # Wait for at least one tick
            time.sleep(0.25)
            
            assert tick_count[0] >= 1
        finally:
            scheduler.stop()
    
    def test_get_stats(self):
        """Test getting scheduler statistics."""
        scheduler = BaseTickScheduler(interval=0.1)
        
        tick_count = [0]
        def test_callback():
            tick_count[0] += 1
        
        scheduler.set_callback(test_callback)
        scheduler.start()
        
        try:
            time.sleep(0.25)
            
            stats = scheduler.get_stats()
            assert stats.ticks >= 1
            assert stats.start_time > 0
        finally:
            scheduler.stop()
    
    def test_reset_stats(self):
        """Test resetting scheduler statistics."""
        scheduler = BaseTickScheduler(interval=0.1)
        
        scheduler.start()
        try:
            time.sleep(0.15)
            scheduler.reset_stats()
            
            stats = scheduler.get_stats()
            # After reset, ticks should be 0
            assert stats.ticks == 0
        finally:
            scheduler.stop()


class TestStrategicTickScheduler:
    """Test strategic tick scheduler."""
    
    def test_strategic_scheduler_creation(self):
        """Test creating strategic scheduler."""
        scheduler = StrategicTickScheduler(interval=10.0)
        
        assert scheduler.interval == 10.0
        assert scheduler.default_interval == 10.0
        assert scheduler.name == "StrategicScheduler"
    
    def test_strategic_scheduler_start(self):
        """Test starting strategic scheduler."""
        scheduler = StrategicTickScheduler(interval=0.5)
        
        assert scheduler.start()
        assert scheduler.running
        
        scheduler.stop()


class TestFastTickScheduler:
    """Test fast tick scheduler."""
    
    def test_fast_scheduler_creation(self):
        """Test creating fast scheduler."""
        scheduler = FastTickScheduler(interval=0.5)
        
        assert scheduler.interval == 0.5
        assert scheduler.default_interval == 0.5
        assert scheduler.name == "FastScheduler"
    
    def test_fast_scheduler_start(self):
        """Test starting fast scheduler."""
        scheduler = FastTickScheduler(interval=0.1)
        
        assert scheduler.start()
        assert scheduler.running
        
        scheduler.stop()


class TestSchedulerManager:
    """Test scheduler manager."""
    
    def test_manager_creation(self):
        """Test creating scheduler manager."""
        manager = SchedulerManager()
        
        assert manager is not None
        assert len(manager.schedulers) == 0
    
    def test_add_scheduler(self):
        """Test adding scheduler to manager."""
        manager = SchedulerManager()
        scheduler = StrategicTickScheduler(interval=1.0)
        
        assert manager.add_scheduler("strategic", scheduler)
        assert "strategic" in manager.schedulers
        assert manager.schedulers["strategic"] is scheduler
    
    def test_add_duplicate_scheduler(self):
        """Test adding duplicate scheduler."""
        manager = SchedulerManager()
        scheduler1 = StrategicTickScheduler(interval=1.0)
        scheduler2 = StrategicTickScheduler(interval=2.0)
        
        assert manager.add_scheduler("strategic", scheduler1)
        assert not manager.add_scheduler("strategic", scheduler2)  # Duplicate
    
    def test_remove_scheduler(self):
        """Test removing scheduler from manager."""
        manager = SchedulerManager()
        scheduler = StrategicTickScheduler(interval=1.0)
        
        manager.add_scheduler("strategic", scheduler)
        assert manager.remove_scheduler("strategic")
        assert "strategic" not in manager.schedulers
    
    def test_remove_nonexistent_scheduler(self):
        """Test removing nonexistent scheduler."""
        manager = SchedulerManager()
        
        assert not manager.remove_scheduler("nonexistent")
    
    def test_start_all_schedulers(self):
        """Test starting all schedulers."""
        manager = SchedulerManager()
        scheduler1 = StrategicTickScheduler(interval=0.5)
        scheduler2 = FastTickScheduler(interval=0.1)
        
        manager.add_scheduler("strategic", scheduler1)
        manager.add_scheduler("fast", scheduler2)
        
        assert manager.start_all()
        assert manager.running
        
        manager.stop_all()
    
    def test_stop_all_schedulers(self):
        """Test stopping all schedulers."""
        manager = SchedulerManager()
        scheduler1 = StrategicTickScheduler(interval=0.5)
        scheduler2 = FastTickScheduler(interval=0.1)
        
        manager.add_scheduler("strategic", scheduler1)
        manager.add_scheduler("fast", scheduler2)
        manager.start_all()
        
        assert manager.stop_all()
        assert not manager.running
    
    def test_get_scheduler(self):
        """Test getting scheduler by name."""
        manager = SchedulerManager()
        scheduler = StrategicTickScheduler(interval=1.0)
        
        manager.add_scheduler("strategic", scheduler)
        
        retrieved = manager.get_scheduler("strategic")
        assert retrieved is scheduler
        
        assert manager.get_scheduler("nonexistent") is None
    
    def test_get_stats(self):
        """Test getting all scheduler statistics."""
        manager = SchedulerManager()
        scheduler1 = StrategicTickScheduler(interval=0.1)
        scheduler2 = FastTickScheduler(interval=0.1)
        
        manager.add_scheduler("strategic", scheduler1)
        manager.add_scheduler("fast", scheduler2)
        manager.start_all()
        
        try:
            time.sleep(0.25)
            
            stats = manager.get_stats()
            assert "strategic" in stats
            assert "fast" in stats
            assert stats["strategic"].ticks >= 1
            assert stats["fast"].ticks >= 1
        finally:
            manager.stop_all()


class TestCreateSchedulers:
    """Test create_schedulers function."""
    
    def test_create_schedulers_default(self):
        """Test creating schedulers with default intervals."""
        schedulers = create_schedulers()
        
        assert "strategic" in schedulers
        assert "fast" in schedulers
        assert isinstance(schedulers["strategic"], StrategicTickScheduler)
        assert isinstance(schedulers["fast"], FastTickScheduler)
    
    def test_create_schedulers_custom_intervals(self):
        """Test creating schedulers with custom intervals."""
        schedulers = create_schedulers(strategic_interval=5.0, fast_interval=0.2)
        
        assert schedulers["strategic"].interval == 5.0
        assert schedulers["fast"].interval == 0.2


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
