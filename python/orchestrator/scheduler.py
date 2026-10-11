"""
CoH1 × Mistral AI Mod - Scheduler Module

Provides tick schedulers for strategic and fast decision-making cycles.
This version is specifically for the orchestrator package.

Author: Generated via planner skill
Version: 0.1.0
Date: 2026-10-11
"""

import threading
import time
import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto


class SchedulerState(Enum):
    """States for schedulers."""
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR = auto()


@dataclass
class SchedulerStats:
    """Statistics for a scheduler."""
    ticks: int = 0
    missed_ticks: int = 0
    average_interval: float = 0.0
    last_tick_time: float = 0.0
    start_time: float = 0.0
    state_changes: int = 0
    
    def to_dict(self) -> dict:
        """Convert stats to dictionary."""
        return {
            "ticks": self.ticks,
            "missed_ticks": self.missed_ticks,
            "average_interval": self.average_interval,
            "last_tick_time": self.last_tick_time,
            "start_time": self.start_time,
            "state_changes": self.state_changes
        }


class BaseTickScheduler:
    """
    Base class for tick schedulers.
    
    Provides common functionality for scheduling periodic callbacks.
    Subclass this to create specific schedulers.
    """
    
    def __init__(self, interval: float, callback: Optional[Callable] = None, name: str = "BaseScheduler"):
        """
        Initialize the scheduler.
        
        Args:
            interval: Time between ticks in seconds
            callback: Function to call on each tick
            name: Name of the scheduler for logging
        """
        self.interval = interval
        self.callback = callback
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # State
        self.state = SchedulerState.STOPPED
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # Threading
        self.thread = None
        self.running = False
        self.paused = False
        
        # Timing
        self.next_tick_time = 0.0
        self.last_tick_time = 0.0
        self.start_time = 0.0
        
        # Statistics
        self.stats = SchedulerStats()
        
        # Configuration
        self.catch_up = True  # Try to catch up if ticks are missed
        self.max_drift = 0.5   # Maximum allowed drift from schedule in seconds
    
    def start(self) -> bool:
        """
        Start the scheduler.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning(f"{self.name}: Already running")
            return False
        
        self.logger.info(f"{self.name}: Starting with interval {self.interval}s")
        
        try:
            self._stop_event.clear()
            self._pause_event.clear()
            self.state = SchedulerState.RUNNING
            self.running = True
            self.paused = False
            self.start_time = time.time()
            self.stats.start_time = self.start_time
            
            self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.thread.start()
            
            self.logger.info(f"{self.name}: Started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"{self.name}: Failed to start: {e}")
            self.state = SchedulerState.ERROR
            return False
    
    def stop(self) -> bool:
        """
        Stop the scheduler.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.running:
            self.logger.info(f"{self.name}: Already stopped")
            return True
        
        self.logger.info(f"{self.name}: Stopping...")
        
        try:
            self.running = False
            self._stop_event.set()
            
            # Wait for thread to finish
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1.0)
                if self.thread.is_alive():
                    self.logger.warning(f"{self.name}: Thread did not stop gracefully")
            
            self.state = SchedulerState.STOPPED
            self.logger.info(f"{self.name}: Stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"{self.name}: Failed to stop: {e}")
            return False
    
    def pause(self):
        """Pause the scheduler."""
        if self.state == SchedulerState.PAUSED:
            return
        
        self.logger.info(f"{self.name}: Pausing")
        self._pause_event.set()
        self.paused = True
        self.state = SchedulerState.PAUSED
    
    def resume(self):
        """Resume the scheduler."""
        if self.state != SchedulerState.PAUSED:
            return
        
        self.logger.info(f"{self.name}: Resuming")
        self._pause_event.clear()
        self.paused = False
        self.state = SchedulerState.RUNNING
    
    def _scheduler_loop(self):
        """Main scheduler loop that runs in a separate thread."""
        self.logger.debug(f"{self.name}: Scheduler loop started")
        
        # Initialize next tick time
        self.next_tick_time = time.time() + self.interval
        
        while self.running:
            try:
                # Check for stop or pause
                if self._stop_event.is_set():
                    break
                
                if self._pause_event.is_set():
                    # Paused, sleep a bit and continue
                    time.sleep(0.05)
                    continue
                
                # Check if it's time for next tick
                current_time = time.time()
                
                if current_time >= self.next_tick_time:
                    self._execute_tick(current_time)
                    
                    # Schedule next tick
                    if self.catch_up:
                        # Try to catch up by scheduling next tick at interval from last
                        self.next_tick_time = self.last_tick_time + self.interval
                    else:
                        # Simple scheduling from current time
                        self.next_tick_time = current_time + self.interval
                else:
                    # Sleep until next tick or check more frequently
                    sleep_time = min(self.next_tick_time - current_time, 0.05)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"{self.name}: Error in scheduler loop: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
        
        self.logger.debug(f"{self.name}: Scheduler loop stopped")
    
    def _execute_tick(self, current_time: float):
        """
        Execute a single tick.
        
        Args:
            current_time: Current timestamp
        """
        try:
            # Check drift
            drift = current_time - self.next_tick_time
            if abs(drift) > self.max_drift and not self.catch_up:
                self.logger.warning(f"{self.name}: Scheduler drift detected: {drift:.3f}s")
                self.stats.missed_ticks += 1
                
                # Adjust next tick time to prevent drift accumulation
                self.next_tick_time = current_time + self.interval
            
            # Execute callback
            if self.callback:
                try:
                    self.callback()
                except Exception as e:
                    self.logger.error(f"{self.name}: Callback error: {e}")
                    import traceback
                    self.logger.error(traceback.format_exc())
            
            # Update statistics
            self.stats.ticks += 1
            self.last_tick_time = current_time
            self.stats.last_tick_time = current_time
            
            # Update average interval
            if self.stats.ticks > 1:
                elapsed = current_time - self.start_time
                self.stats.average_interval = elapsed / self.stats.ticks
            else:
                self.stats.average_interval = self.interval
                
        except Exception as e:
            self.logger.error(f"{self.name}: Error executing tick: {e}")
    
    def set_interval(self, interval: float):
        """
        Set the scheduler interval.
        
        Args:
            interval: New interval in seconds
        """
        self.interval = interval
        self.logger.info(f"{self.name}: Interval changed to {interval}s")
    
    def set_callback(self, callback: Callable):
        """
        Set the callback function.
        
        Args:
            callback: Function to call on each tick
        """
        self.callback = callback
        self.logger.info(f"{self.name}: Callback updated")
    
    def get_stats(self) -> SchedulerStats:
        """Get scheduler statistics."""
        return self.stats
    
    def reset_stats(self):
        """Reset scheduler statistics."""
        self.stats = SchedulerStats()
        self.stats.start_time = time.time()


class StrategicTickScheduler(BaseTickScheduler):
    """
    Scheduler for strategic decision-making ticks.
    
    Triggers the strategist (Mistral AI) at configurable intervals
    to make macro-level decisions (build orders, tech tree, posture).
    """
    
    def __init__(self, interval: float = 10.0, callback: Optional[Callable] = None):
        """
        Initialize strategic tick scheduler.
        
        Args:
            interval: Time between strategic ticks in seconds (10-15s recommended)
            callback: Function to call on each strategic tick
        """
        super().__init__(interval, callback, "StrategicScheduler")
        self.default_interval = 10.0
    
    def start(self) -> bool:
        """Start the strategic scheduler."""
        if not super().start():
            return False
        
        self.logger.info(f"Strategic scheduler: Ready for macro-level decisions every {self.interval}s")
        return True


class FastTickScheduler(BaseTickScheduler):
    """
    Scheduler for fast decision-making ticks.
    
    Handles reflex layer needs and urgent events at sub-second intervals.
    Used for local heuristics that don't require Mistral AI.
    """
    
    def __init__(self, interval: float = 0.5, callback: Optional[Callable] = None):
        """
        Initialize fast tick scheduler.
        
        Args:
            interval: Time between fast ticks in seconds (<=1s recommended)
            callback: Function to call on each fast tick
        """
        super().__init__(interval, callback, "FastScheduler")
        self.default_interval = 0.5
    
    def start(self) -> bool:
        """Start the fast scheduler."""
        if not super().start():
            return False
        
        self.logger.info(f"Fast scheduler: Ready for urgent events every {self.interval}s")
        return True


class SchedulerManager:
    """
    Manages multiple schedulers and their coordination.
    
    Ensures no conflicts between strategic and fast schedulers.
    """
    
    def __init__(self):
        """Initialize scheduler manager."""
        self.logger = logging.getLogger(__name__)
        self.schedulers = {}
        self.running = False
    
    def add_scheduler(self, name: str, scheduler: BaseTickScheduler) -> bool:
        """
        Add a scheduler to the manager.
        
        Args:
            name: Name to identify the scheduler
            scheduler: Scheduler instance to add
            
        Returns:
            True if added successfully, False otherwise
        """
        if name in self.schedulers:
            self.logger.warning(f"Scheduler '{name}' already exists")
            return False
        
        self.schedulers[name] = scheduler
        self.logger.info(f"Added scheduler: {name}")
        return True
    
    def remove_scheduler(self, name: str) -> bool:
        """
        Remove a scheduler from the manager.
        
        Args:
            name: Name of the scheduler to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        if name not in self.schedulers:
            self.logger.warning(f"Scheduler '{name}' does not exist")
            return False
        
        scheduler = self.schedulers[name]
        if scheduler.running:
            scheduler.stop()
        
        del self.schedulers[name]
        self.logger.info(f"Removed scheduler: {name}")
        return True
    
    def start_all(self) -> bool:
        """
        Start all managed schedulers.
        
        Returns:
            True if all schedulers started successfully, False otherwise
        """
        success = True
        for name, scheduler in self.schedulers.items():
            if not scheduler.start():
                self.logger.error(f"Failed to start scheduler: {name}")
                success = False
        
        if success:
            self.running = True
            self.logger.info("All schedulers started")
        
        return success
    
    def stop_all(self) -> bool:
        """
        Stop all managed schedulers.
        
        Returns:
            True if all schedulers stopped successfully, False otherwise
        """
        success = True
        for name, scheduler in self.schedulers.items():
            if not scheduler.stop():
                self.logger.error(f"Failed to stop scheduler: {name}")
                success = False
        
        if success:
            self.running = False
            self.logger.info("All schedulers stopped")
        
        return success
    
    def pause_all(self):
        """Pause all managed schedulers."""
        for name, scheduler in self.schedulers.items():
            scheduler.pause()
        self.logger.info("All schedulers paused")
    
    def resume_all(self):
        """Resume all managed schedulers."""
        for name, scheduler in self.schedulers.items():
            scheduler.resume()
        self.logger.info("All schedulers resumed")
    
    def get_scheduler(self, name: str) -> Optional[BaseTickScheduler]:
        """
        Get a scheduler by name.
        
        Args:
            name: Name of the scheduler
            
        Returns:
            Scheduler instance or None if not found
        """
        return self.schedulers.get(name)
    
    def get_stats(self) -> dict:
        """
        Get statistics for all schedulers.
        
        Returns:
            Dictionary with scheduler names as keys and their stats as values
        """
        return {name: scheduler.get_stats() for name, scheduler in self.schedulers.items()}


def create_schedulers(strategic_interval: float = 10.0, fast_interval: float = 0.5) -> dict:
    """
    Create standard schedulers with specified intervals.
    
    Args:
        strategic_interval: Interval for strategic scheduler in seconds
        fast_interval: Interval for fast scheduler in seconds
        
    Returns:
        Dictionary with scheduler instances
    """
    schedulers = {}
    
    # Create strategic scheduler
    schedulers["strategic"] = StrategicTickScheduler(interval=strategic_interval)
    
    # Create fast scheduler
    schedulers["fast"] = FastTickScheduler(interval=fast_interval)
    
    return schedulers


# Test the schedulers if executed directly
if __name__ == "__main__":
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing Scheduler Module...")
    
    # Test strategic scheduler
    print("\n--- Testing Strategic Tick Scheduler ---")
    strategic = StrategicTickScheduler(interval=1.0)
    
    # Track ticks
    tick_count = [0]
    def strategic_callback():
        tick_count[0] += 1
        print(f"Strategic tick #{tick_count[0]}")
    
    strategic.set_callback(strategy_callback)
    
    if strategic.start():
        time.sleep(2.5)
        stats = strategic.get_stats()
        print(f"Strategic ticks: {stats.ticks}")
        print(f"Missed ticks: {stats.missed_ticks}")
        print(f"Average interval: {stats.average_interval:.3f}s")
        
        if strategic.stop():
            print("Strategic scheduler stopped")
    
    # Test fast scheduler
    print("\n--- Testing Fast Tick Scheduler ---")
    fast = FastTickScheduler(interval=0.2)
    
    fast_tick_count = [0]
    def fast_callback():
        fast_tick_count[0] += 1
        print(f"Fast tick #{fast_tick_count[0]}")
    
    fast.set_callback(fast_callback)
    
    if fast.start():
        time.sleep(1.0)
        stats = fast.get_stats()
        print(f"Fast ticks: {stats.ticks}")
        print(f"Average interval: {stats.average_interval:.3f}s")
        
        if fast.stop():
            print("Fast scheduler stopped")
    
    # Test scheduler manager
    print("\n--- Testing Scheduler Manager ---")
    manager = SchedulerManager()
    
    # Add schedulers
    manager.add_scheduler("strategic", StrategicTickScheduler(interval=2.0))
    manager.add_scheduler("fast", FastTickScheduler(interval=0.3))
    
    # Start all
    if manager.start_all():
        time.sleep(1.5)
        
        # Get stats
        all_stats = manager.get_stats()
        for name, stats in all_stats.items():
            print(f"{name}: {stats.ticks} ticks")
        
        # Stop all
        if manager.stop_all():
            print("All schedulers stopped")
    
    print("\nScheduler tests completed successfully")
