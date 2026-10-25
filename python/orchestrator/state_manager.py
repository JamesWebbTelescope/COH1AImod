"""
CoH1 × Mistral AI Mod - State Manager

Manages game state collection, processing, and storage for the orchestrator.
This version is specifically for the orchestrator package.

Responsibilities:
- Receive and process game state from IPC
- Maintain current and historical game states
- Provide state access to other components
- Handle state validation and filtering

Author: Generated via planner skill
Version: 0.1.0
Date: 2026-10-11
"""

import json
import time
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from collections import deque

try:
    from .config import Configuration
except ImportError:
    # For direct execution or testing
    from config import Configuration


@dataclass
class StateManagerStats:
    """Statistics for the state manager."""
    states_received: int = 0
    states_processed: int = 0
    validation_errors: int = 0
    last_state_time: float = 0.0
    last_error_time: float = 0.0
    average_processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "states_received": self.states_received,
            "states_processed": self.states_processed,
            "validation_errors": self.validation_errors,
            "last_state_time": self.last_state_time,
            "last_error_time": self.last_error_time,
            "average_processing_time": self.average_processing_time
        }


class StateManager:
    """
    Manages game state collection and processing.
    
    Receives game state from IPC reader, validates it, and makes it
    available to other components of the orchestrator.
    """
    
    def __init__(self, config: Configuration = None, ipc_reader=None):
        """
        Initialize state manager.
        
        Args:
            config: Configuration instance
            ipc_reader: IPC reader instance for receiving states
        """
        self.config = config or Configuration()
        self.ipc_reader = ipc_reader
        self.logger = logging.getLogger(__name__)
        
        # State storage
        self.current_state = None
        self.previous_states = deque(maxlen=100)  # Keep last 100 states for history
        self._lock = threading.Lock()
        
        # Statistics
        self.stats = StateManagerStats()
        
        # Configuration
        self.history_depth = self.config.get("state", "history_depth", default=100)
        self.validation_enabled = self.config.get("state", "validation_enabled", default=True)
        
        # State flags
        self.running = False
        self.thread = None
        
        self.logger.info("State manager initialized")
        
    def start(self) -> bool:
        """Start the state manager."""
        if self.running:
            self.logger.warning("State manager is already running")
            return False
        
        self.running = True
        self.logger.info("State manager started")
        return True
    
    def stop(self) -> bool:
        """Stop the state manager."""
        if not self.running:
            return True
        
        self.running = False
        
        # Wait for thread to finish if it exists
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        
        self.logger.info("State manager stopped")
        return True
    
    def update_state(self, state: Dict[str, Any]) -> bool:
        """
        Update the current game state.
        
        Args:
            state: New game state to process
            
        Returns:
            True if state was processed successfully, False otherwise
        """
        if not self.running:
            self.logger.warning("State manager is not running, cannot update state")
            return False
        
        start_time = time.time()
        
        try:
            with self._lock:
                # Validate state
                if self.validation_enabled:
                    if not self._validate_state(state):
                        self.stats.validation_errors += 1
                        self.stats.last_error_time = start_time
                        self.logger.warning(f"State validation failed")
                        return False
                
                # Process and store state
                processed_state = self._process_state(state)
                
                # Update current state
                self.current_state = processed_state
                
                # Add to history
                self.previous_states.append(processed_state)
                
                # Ensure history doesn't exceed max length
                while len(self.previous_states) > self.history_depth:
                    self.previous_states.popleft()
                
                # Update statistics
                self.stats.states_received += 1
                self.stats.states_processed += 1
                self.stats.last_state_time = start_time
                
                # Update average processing time
                processing_time = time.time() - start_time
                if self.stats.states_processed > 0:
                    self.stats.average_processing_time = (
                        (self.stats.average_processing_time * (self.stats.states_processed - 1)) + processing_time
                    ) / self.stats.states_processed
                else:
                    self.stats.average_processing_time = processing_time
                
                self.logger.debug(f"State updated at game time: {processed_state.get('game_time', 0):.1f}s")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating state: {e}")
            return False
    
    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get the current game state."""
        with self._lock:
            return self.current_state.copy() if self.current_state else None
    
    def get_previous_state(self, n: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get a previous game state.
        
        Args:
            n: How many states back to go (1 = most recent previous)
            
        Returns:
            Previous state or None if not available
        """
        with self._lock:
            if n <= 0 or n > len(self.previous_states):
                return None
            return self.previous_states[-n].copy()
    
    def get_state_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent state history.
        
        Args:
            count: Number of historical states to return
            
        Returns:
            List of recent states
        """
        with self._lock:
            start = max(0, len(self.previous_states) - count)
            return [state.copy() for state in list(self.previous_states)[start:]]
    
    def get_state_at_time(self, game_time: float) -> Optional[Dict[str, Any]]:
        """
        Get the state closest to a specific game time.
        
        Args:
            game_time: Target game time to find state for
            
        Returns:
            State closest to the target time or None
        """
        with self._lock:
            best_state = None
            best_diff = float('inf')
            
            # Check current state
            if self.current_state:
                diff = abs(self.current_state.get('game_time', 0) - game_time)
                if diff < best_diff:
                    best_diff = diff
                    best_state = self.current_state
            
            # Check historical states
            for state in self.previous_states:
                diff = abs(state.get('game_time', 0) - game_time)
                if diff < best_diff:
                    best_diff = diff
                    best_state = state
            
            return best_state.copy() if best_state else None
    
    def _validate_state(self, state: Dict[str, Any]) -> bool:
        """
        Validate a game state.
        
        Args:
            state: State to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(state, dict):
            self.logger.error("State is not a dictionary")
            return False
        
        # Check required fields
        required_fields = ['version', 'player_id', 'timestamp']
        for field in required_fields:
            if field not in state:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate version
        version = state.get('version')
        if version not in ['1.0']:
            self.logger.warning(f"Unexpected state version: {version}")
            # Still accept but log warning
        
        # Validate player_id
        player_id = state.get('player_id')
        if not isinstance(player_id, int) or player_id <= 0:
            self.logger.error(f"Invalid player_id: {player_id}")
            return False
        
        # Validate resources
        if 'resources' in state:
            resources = state['resources']
            for resource_type in ['manpower', 'fuel', 'munitions']:
                if resource_type in resources:
                    resource = resources[resource_type]
                    if not isinstance(resource, dict):
                        self.logger.error(f"Invalid resource data for {resource_type}")
                        return False
                    for field in ['current', 'income', 'max']:
                        if field not in resource:
                            self.logger.error(f"Missing {field} in {resource_type}")
                            return False
        
        return True
    
    def _process_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and normalize a game state.
        
        Args:
            state: Raw state to process
            
        Returns:
            Processed state
        """
        processed = state.copy()
        
        # Ensure all expected fields exist
        processed.setdefault('version', '1.0')
        processed.setdefault('player_id', 1)
        processed.setdefault('timestamp', time.time())
        processed.setdefault('game_time', 0.0)
        processed.setdefault('phase', 'early')
        processed.setdefault('faction', 'allies')
        
        # Ensure nested structures exist
        processed.setdefault('resources', {})
        for resource_type in ['manpower', 'fuel', 'munitions']:
            if resource_type not in processed['resources']:
                processed['resources'][resource_type] = {'current': 0, 'income': 0, 'max': 0}
            else:
                # Ensure resource fields exist
                for field in ['current', 'income', 'max']:
                    processed['resources'][resource_type].setdefault(field, 0)
        
        processed.setdefault('squads', [])
        processed.setdefault('cps', [])
        processed.setdefault('enemies', [])
        processed.setdefault('tech', {})
        processed.setdefault('queue', [])
        processed.setdefault('pop', [0, 100])
        
        return processed
    
    def get_stats(self) -> StateManagerStats:
        """Get current statistics."""
        return self.stats
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = StateManagerStats()
    
    def clear_history(self):
        """Clear state history."""
        with self._lock:
            self.previous_states.clear()


if __name__ == "__main__":
    # Test state manager
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing State Manager...")
    
    # Create state manager
    state_manager = StateManager()
    
    if state_manager.start():
        print("State manager started successfully")
    
    # Test with mock state
    test_state = {
        "version": "1.0",
        "player_id": 1,
        "timestamp": time.time(),
        "game_time": 45.0,
        "phase": "mid",
        "faction": "allies",
        "resources": {
            "manpower": {"current": 1500, "income": 50, "max": 3000},
            "fuel": {"current": 800, "income": 30, "max": 1500},
            "munitions": {"current": 1000, "income": 20, "max": 2000}
        },
        "squads": [
            {"id": 1, "type": "riflemen", "health": 0.8, "position": [10, 20, 30]},
            {"id": 2, "type": "engineer", "health": 1.0, "position": [15, 25, 35]}
        ],
        "cps": [
            {"id": 1, "position": [100, 200], "owner": 1},
            {"id": 2, "position": [300, 400], "owner": 2}
        ]
    }
    
    # Update state
    if state_manager.update_state(test_state):
        print("State updated successfully")
        
        # Get current state
        current = state_manager.get_current_state()
        if current:
            print(f"Current state has {len(current.get('squads', []))} squads")
        
        # Get stats
        stats = state_manager.get_stats()
        print(f"States processed: {stats.states_processed}")
    
    # Test state at time
    state_at_time = state_manager.get_state_at_time(45.0)
    if state_at_time:
        print(f"Found state at game_time=45.0")
    
    # Stop state manager
    if state_manager.stop():
        print("State manager stopped")
    
    print("\nState manager tests completed successfully")
