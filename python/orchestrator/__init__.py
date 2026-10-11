"""
CoH1 × Mistral AI Mod - Orchestrator Package

This package contains the main orchestrator components for the mod.

Components:
- scheduler: Tick schedulers for strategic and fast decision-making cycles
- state_manager: Manages game state collection and processing
- command_processor: Processes and executes AI commands
- main: Main orchestrator service entry point

Author: Generated via planner skill
Version: 0.1.0
Date: 2026-10-11
"""

# Import key modules for easy access
from .scheduler import (
    BaseTickScheduler,
    StrategicTickScheduler,
    FastTickScheduler,
    SchedulerManager,
    SchedulerState,
    SchedulerStats,
    create_schedulers,
)

from .state_manager import StateManager, StateManagerStats
from .command_processor import CommandProcessor, CommandProcessorStats

# Version info
__version__ = "0.1.0"
__all__ = [
    "BaseTickScheduler",
    "StrategicTickScheduler", 
    "FastTickScheduler",
    "SchedulerManager",
    "SchedulerState",
    "SchedulerStats",
    "StateManager",
    "StateManagerStats",
    "CommandProcessor",
    "CommandProcessorStats",
    "create_schedulers",
]
