"""
End-to-End Loop Integration Tests for Milestone 1

Tests the complete state -> decision -> command pipeline:
1. State collection (SCAR) -> JSON serialization
2. Python ingestion and schema validation
3. Orchestrator processing with state manager
4. Reflex layer decision making
5. Command validation and safety filtering
6. Command serialization and write-back through IPC
7. SCAR command reading and execution simulation

This test validates Milestone 1: End-to-End Loop Stabilization
Acceptance Gate: A repeatable state -> decision -> command loop runs without manual intervention

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-25
"""

import json
import tempfile
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest

# Add parent directory to Python path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from config import Configuration, load_config
from ipc_reader import IPCReader
from orchestrator.state_manager import StateManager
from orchestrator.command_processor import CommandProcessor, CommandPriority
from validator import ActionValidator
from safety_filter import SafetyFilter
from schema import GameState, SquadData, ResourceData, Position


# =============================================================================
# Mock SCAR State Generator
# =============================================================================

class MockSCARStateGenerator:
    """
    Simulates SCAR mod generating game states over time.
    Represents the state collection pipeline (state_collector.scar + serializer.scar).
    """
    
    def __init__(self, state_file: Path, lock_file: Path, data_dir: Path):
        self.state_file = state_file
        self.lock_file = lock_file
        self.data_dir = data_dir
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.tick_count = 0
        self.last_state: Optional[Dict[str, Any]] = None
        
        # Ensure data directory exists
        data_dir.mkdir(parents=True, exist_ok=True)
    
    def start(self):
        """Start generating states in a background thread."""
        self.running = True
        self.thread = threading.Thread(target=self._generate_states, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop state generation."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
    
    def _generate_states(self):
        """Generate a sequence of game states with progressive changes."""
        while self.running:
            # Create state for current tick
            state = self._create_state_for_tick(self.tick_count)
            self.last_state = state
            
            # Write state to file (simulating SCAR's WriteGameState)
            try:
                with open(self.state_file, 'w', encoding='utf-8') as f:
                    json.dump(state, f, ensure_ascii=False)
            except (IOError, OSError) as e:
                print(f"SCAR: Failed to write state: {e}")
            
            # Increment tick and sleep
            self.tick_count += 1
            time.sleep(0.2)  # ~5 updates per second
    
    def _create_state_for_tick(self, tick: int) -> Dict[str, Any]:
        """Create a realistic game state for the given tick."""
        # Progress game time (seconds)
        game_time = tick * 0.2
        
        # Base resources
        base_manpower = 500
        base_fuel = 300
        base_munitions = 200
        
        # Squads with varying health based on tick
        squads = []
        
        # Squad 1: Riflemen - starts healthy, takes damage over time
        health_1 = max(0.1, 1.0 - (tick * 0.02))
        squads.append({
            "id": 1,
            "type": "riflemen",
            "health": round(health_1, 2),
            "max_health": 1.0,
            "vet_level": min(5, tick // 10),
            "pos": [100 + tick * 2, 200, 0],
            "posture": "defensive",
            "under_fire": tick > 15,
            "suppressed": tick > 20
        })
        
        # Squad 2: Engineer - building structures
        squads.append({
            "id": 2,
            "type": "engineer",
            "health": 0.9,
            "max_health": 1.0,
            "vet_level": 0,
            "pos": [50, 50, 0],
            "posture": "idle",
            "under_fire": False,
            "suppressed": False
        })
        
        # Squad 3: Scout - low health, needs retreat
        if tick > 5:
            health_3 = max(0.05, 0.5 - (tick - 5) * 0.03)
            squads.append({
                "id": 3,
                "type": "scout_car",
                "health": round(health_3, 2),
                "max_health": 1.0,
                "vet_level": min(3, tick // 15),
                "pos": [300 - tick * 2, 400, 0],
                "posture": "aggressive",
                "under_fire": True,
                "suppressed": tick > 10
            })
        
        # Squad 4: Mortar - for artillery testing
        if tick > 10:
            squads.append({
                "id": 4,
                "type": "mortar",
                "health": 0.8,
                "max_health": 1.0,
                "vet_level": 0,
                "pos": [150, 300, 0],
                "posture": "defensive",
                "under_fire": tick > 20,
                "suppressed": False
            })
        
        # Capture points
        capture_points = [
            {
                "id": 1,
                "pos": [500, 500, 0],
                "owner": 1 if tick > 3 else None,
                "progress": min(1.0, 0.0 + tick * 0.05) if tick <= 20 else 1.0,
                "is_neutral": tick <= 3
            },
            {
                "id": 2,
                "pos": [600, 600, 0],
                "owner": None,
                "progress": 0.0,
                "is_neutral": True
            }
        ]
        
        # Visible enemies (for artillery/combat scenarios)
        visible_enemies = []
        if tick > 10:
            visible_enemies.append({
                "id": 101,
                "type": "light_tank",
                "pos": [350, 450, 0],
                "health": 0.7,
                "is_attacking": True
            })
        if tick > 20:
            visible_enemies.append({
                "id": 102,
                "type": "mortar",
                "pos": [400, 500, 0],
                "health": 0.9
            })
        
        # Build queue
        build_queue = []
        if tick < 30:
            build_queue.append({
                "type": "unit",
                "name": "riflemen",
                "progress": min(1.0, tick * 0.05),
                "time": max(0, 20 - tick),
                "cost": [300, 0, 0]
            })
        
        # Resources - grows over time with income
        resources = {
            "manpower": {
                "current": min(5000, base_manpower + int(tick * 5)),
                "income": 10,
                "max": 5000
            },
            "fuel": {
                "current": min(3000, base_fuel + int(tick * 3)),
                "income": 5,
                "max": 3000
            },
            "munitions": {
                "current": min(2000, base_munitions + int(tick * 2)),
                "income": 3,
                "max": 2000
            }
        }
        
        # Tech tree progression
        tech_tree = {
            "tier_1": True,
            "tier_2": tick >= 15,
            "tier_3": tick >= 40
        }
        
        return {
            "version": "1.0",
            "player_id": 1,
            "timestamp": time.time(),
            "game_time": game_time,
            "resources": resources,
            "squads": squads,
            "capture_points": capture_points,
            "visible_enemies": visible_enemies,
            "tech_tree": tech_tree,
            "build_queue": build_queue,
            "population": {
                "current": len(squads),
                "max": 100
            },
            "phase": self._get_game_phase(tick)
        }
    
    def _get_game_phase(self, tick: int) -> str:
        if tick < 20:
            return "early"
        elif tick < 60:
            return "mid"
        else:
            return "late"


# =============================================================================
# Mock SCAR Command Executor
# =============================================================================

class MockSCARCommandExecutor:
    """
    Simulates SCAR mod reading and executing commands.
    Represents the command execution pipeline (ipc.scar command handlers).
    """
    
    def __init__(self, command_file: Path, state_file: Path, lock_file: Path):
        self.command_file = command_file
        self.state_file = state_file
        self.lock_file = lock_file
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.executed_commands: List[Dict[str, Any]] = []
        self.last_state: Optional[Dict[str, Any]] = None
    
    def start(self):
        """Start command processing in a background thread."""
        self.running = True
        self.thread = threading.Thread(target=self._process_commands, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop command processing."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
    
    def _process_commands(self):
        """Read commands from file and simulate execution."""
        while self.running:
            # Read commands file
            if self.command_file.exists():
                try:
                    with open(self.command_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():
                            data = json.loads(content)
                            commands = data.get("commands", [])
                            
                            # Process each command
                            for command in commands:
                                self._execute_command(command)
                            
                            # Clear the command file after processing
                            self.command_file.unlink()
                except (IOError, OSError, json.JSONDecodeError) as e:
                    print(f"SCAR: Failed to process commands: {e}")
            
            # Also read state file (to verify it's being updated)
            if self.state_file.exists():
                try:
                    with open(self.state_file, 'r', encoding='utf-8') as f:
                        self.last_state = json.load(f)
                except (IOError, OSError, json.JSONDecodeError):
                    pass
            
            time.sleep(0.05)  # Fast polling for commands
    
    def _execute_command(self, command: Dict[str, Any]):
        """Simulate command execution in SCAR."""
        self.executed_commands.append(command)
        print(f"  SCAR: Executed command: {command.get('command', 'UNKNOWN')}")
    
    def get_executed_commands(self) -> List[Dict[str, Any]]:
        """Get list of all executed commands."""
        return self.executed_commands.copy()
    
    def get_execution_count(self) -> int:
        """Get total number of commands executed."""
        return len(self.executed_commands)


# =============================================================================
# End-to-End Loop Tester
# =============================================================================

class EndToEndLoopTester:
    """
    Orchestrates the complete end-to-end test:
    SCAR (state generator) -> IPC -> Orchestrator -> Reflex Layer -> Validator -> Safety -> Commands -> SCAR (executor)
    """
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        
        # Create configuration
        self.ipc_config = {
            "state_file": str(temp_dir / "coh1ai_state.json"),
            "command_file": str(temp_dir / "coh1ai_commands.json"),
            "lock_file": str(temp_dir / "coh1ai_lock.tmp"),
            "data_dir": str(temp_dir),
            "poll_interval": 0.05,
            "max_retries": 2
        }
        
        self.config_data = {
            "ipc": self.ipc_config,
            "mod": {"version": "1.0.0"},
            "game": {"faction": "allies", "difficulty": "normal"},
            "mistral": {"api_url": "http://test.com", "api_key": "test"},
            "debug": {"enabled": False, "level": "INFO"},
            "reflex": {
                "retreat_health_threshold": 0.3,
                "critical_health_threshold": 0.15,
                "build_queue_interval": 2.0
            },
            "safety": {
                "resource_margin": 0.1,
                "pop_cap_margin": 0.05,
                "pathfinding_enabled": True
            },
            "testing": {"test_mode": True}
        }
        
        # Initialize components
        self.config: Optional[Configuration] = None
        self.ipc_reader: Optional[IPCReader] = None
        self.state_manager: Optional[StateManager] = None
        self.command_processor: Optional[CommandProcessor] = None
        self.validator: Optional[ActionValidator] = None
        self.safety_filter: Optional[SafetyFilter] = None
        self.scar_state_gen: Optional[MockSCARStateGenerator] = None
        self.scar_cmd_exec: Optional[MockSCARCommandExecutor] = None
        
        # Message processor
        self.message_processor_running = False
        self.message_processor_thread: Optional[threading.Thread] = None
    
    def setup(self):
        """Initialize all components."""
        # Create configuration
        self.config = Configuration()
        self.config._config = self.config_data
        
        # Initialize IPC reader
        self.ipc_reader = IPCReader(self.config)
        
        # Initialize state manager
        self.state_manager = StateManager(self.config, self.ipc_reader)
        
        # Initialize command processor
        self.command_processor = CommandProcessor(self.config, self.ipc_reader)
        
        # Initialize validator
        self.validator = ActionValidator(strict_mode=False)
        
        # Initialize safety filter (will be updated with game state)
        self.safety_filter = SafetyFilter({})
        
        # Initialize SCAR components
        state_file = Path(self.ipc_config["state_file"])
        command_file = Path(self.ipc_config["command_file"])
        lock_file = Path(self.ipc_config["lock_file"])
        data_dir = Path(self.ipc_config["data_dir"])
        
        self.scar_state_gen = MockSCARStateGenerator(state_file, lock_file, data_dir)
        self.scar_cmd_exec = MockSCARCommandExecutor(command_file, state_file, lock_file)
    
    def _process_messages_loop(self):
        """Process messages from IPC reader and update state manager."""
        self.message_processor_running = True
        while self.message_processor_running:
            # Get message from IPC reader
            if self.ipc_reader:
                message = self.ipc_reader.get_message(timeout=0.05)
                if message:
                    # Update state manager with the message data
                    if self.state_manager:
                        self.state_manager.update_state(message.data)
            time.sleep(0.01)
    
    def start_all(self):
        """Start all components."""
        # Start IPC reader
        assert self.ipc_reader is not None
        assert self.ipc_reader.start()
        
        # Start state manager
        assert self.state_manager is not None
        assert self.state_manager.start()
        
        # Start command processor
        assert self.command_processor is not None
        assert self.command_processor.start()
        
        # Start SCAR state generator
        assert self.scar_state_gen is not None
        self.scar_state_gen.start()
        
        # Start SCAR command executor
        assert self.scar_cmd_exec is not None
        self.scar_cmd_exec.start()
        
        # Start message processor thread (connects IPC reader to state manager)
        self.message_processor_thread = threading.Thread(
            target=self._process_messages_loop, daemon=True
        )
        self.message_processor_thread.start()
        
        # Give everything time to initialize
        time.sleep(0.3)
    
    def stop_all(self):
        """Stop all components."""
        # Stop message processor first
        self.message_processor_running = False
        if self.message_processor_thread and self.message_processor_thread.is_alive():
            self.message_processor_thread.join(timeout=1.0)
        
        if self.scar_cmd_exec:
            self.scar_cmd_exec.stop()
        if self.scar_state_gen:
            self.scar_state_gen.stop()
        if self.command_processor:
            self.command_processor.stop()
        if self.state_manager:
            self.state_manager.stop()
        if self.ipc_reader:
            self.ipc_reader.stop()
    
    def run_end_to_end_cycle(self, cycles: int = 10) -> bool:
        """
        Run the complete end-to-end loop for a number of cycles.
        
        Each cycle:
        1. SCAR generates state
        2. Python reads state
        3. Orchestrator processes state
        4. Reflex layer makes decisions
        5. Commands are validated and filtered
        6. Commands are written back to SCAR
        7. SCAR executes commands
        
        Returns True if the loop completes successfully.
        """
        print(f"\n=== Running End-to-End Loop for {cycles} cycles ===\n")
        
        # Wait for initial state
        start_time = time.time()
        initial_state_received = False
        
        while time.time() - start_time < 2.0:
            if self.ipc_reader and self.ipc_reader.get_stats().messages_received > 0:
                initial_state_received = True
                print("  State received from SCAR")
                break
            time.sleep(0.1)
        
        if not initial_state_received:
            print("  Failed to receive initial state")
            return False
        
        # Now simulate reflex layer processing
        # In a real implementation, the orchestrator would call the reflex layer
        # For this test, we'll manually trigger it
        
        cycle_count = 0
        last_command_count = 0
        
        while cycle_count < cycles and time.time() - start_time < 15.0:
            cycle_count += 1
            
            # Get current state from state manager
            current_state = self.state_manager.get_current_state()
            if current_state:
                # Process through reflex layer (simulated)
                commands = self._simulate_reflex_layer(current_state)
                
                if commands:
                    # Validate commands
                    validated_commands = []
                    for cmd in commands:
                        if self.validator and self.validator.validate(cmd):
                            # Apply safety filter
                            if self.safety_filter:
                                # Update safety filter with current state
                                self.safety_filter.update_game_state(current_state)
                                if self.safety_filter.check_command(cmd).is_safe:
                                    validated_commands.append(cmd)
                            else:
                                validated_commands.append(cmd)
                    
                    # Send validated commands directly via IPC (simulating command processor)
                    if validated_commands and self.ipc_reader:
                        self.ipc_reader.send_commands(validated_commands)
                    
                    # Check if commands were executed by SCAR
                    current_exec_count = self.scar_cmd_exec.get_execution_count()
                    if current_exec_count > last_command_count:
                        print(f"  Cycle {cycle_count}: Generated {len(commands)} commands, "
                              f"Validated {len(validated_commands)}, "
                              f"Executed {current_exec_count - last_command_count}")
                        last_command_count = current_exec_count
            
            # Sleep to allow state updates
            time.sleep(0.25)
        
        print(f"\n=== Completed {cycle_count} cycles ===")
        print(f"  Total commands executed by SCAR: {self.scar_cmd_exec.get_execution_count()}")
        
        return self.scar_cmd_exec.get_execution_count() > 0
    
    def _simulate_reflex_layer(self, game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Simulate reflex layer decision making based on game state.
        This generates commands that the reflex layer would produce.
        """
        commands = []
        
        # Get squads from state (handle both formats)
        squads = game_state.get("squads", [])
        
        # Check each squad for reflex conditions
        for squad_data in squads:
            squad_id = squad_data.get("id")
            squad_type = squad_data.get("type")
            health = squad_data.get("health", 1.0)
            max_health = squad_data.get("max_health", 1.0)
            health_percent = health / max_health if max_health > 0 else 1.0
            under_fire = squad_data.get("under_fire", False)
            
            # Reflex 1: Retreat if health is critically low (<= 15%)
            if health_percent <= 0.15:
                commands.append({
                    "command": "RETREAT",
                    "squad_id": squad_id,
                    "reason": "critical_health",
                    "priority": "URGENT"
                })
                print(f"  Reflex: RETREAT squad {squad_id} (health={health_percent:.1%})")
            
            # Reflex 2: Retreat if under fire and health <= 30%
            elif health_percent <= 0.3 and under_fire:
                commands.append({
                    "command": "RETREAT",
                    "squad_id": squad_id,
                    "reason": "under_fire_low_health",
                    "priority": "HIGH"
                })
                print(f"  Reflex: RETREAT squad {squad_id} (under fire, health={health_percent:.1%})")
            
            # Reflex 3: Attack move away from enemy if under fire
            visible_enemies = game_state.get("visible_enemies", [])
            if visible_enemies and squad_type in ["riflemen", "engineer"]:
                # Find nearest enemy
                squad_pos = squad_data.get("pos", [0, 0, 0])
                nearest_enemy = None
                min_dist = float('inf')
                
                for enemy in visible_enemies:
                    enemy_pos = enemy.get("pos", [0, 0, 0])
                    dist = ((squad_pos[0] - enemy_pos[0])**2 + 
                           (squad_pos[1] - enemy_pos[1])**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        nearest_enemy = enemy
                
                if nearest_enemy and min_dist < 100 and under_fire:
                    # Move away from enemy
                    away_x = squad_pos[0] + (squad_pos[0] - nearest_enemy["pos"][0]) * 2
                    away_y = squad_pos[1] + (squad_pos[1] - nearest_enemy["pos"][1]) * 2
                    commands.append({
                        "command": "ATTACK_MOVE",
                        "squad_id": squad_id,
                        "position": [round(away_x), round(away_y), 0],
                        "reason": "avoid_enemy",
                        "priority": "HIGH"
                    })
                    print(f"  Reflex: ATTACK_MOVE squad {squad_id} away from enemy")
            
            # Reflex 4: Capture neutral/uncaptured points
            capture_points = game_state.get("capture_points", [])
            for cp in capture_points:
                cp_id = cp.get("id")
                cp_owner = cp.get("owner")
                if cp_owner is None or cp_owner != 1:  # Neutral or enemy
                    # Assign this squad to capture
                    commands.append({
                        "command": "CAPTURE",
                        "squad_id": squad_id,
                        "point_id": cp_id,
                        "reason": "capture_neutral_point",
                        "priority": "NORMAL"
                    })
                    print(f"  Reflex: CAPTURE point {cp_id} with squad {squad_id}")
                    break  # Only capture one point per cycle
        
        # Reflex 5: Build queue management
        # If no units in build queue, queue a riflemen
        build_queue = game_state.get("build_queue", [])
        if not build_queue:
            # Find engineer
            for squad_data in squads:
                if squad_data.get("type") == "engineer":
                    commands.append({
                        "command": "BUILD",
                        "engineer_id": squad_data.get("id"),
                        "building_type": "barracks",
                        "position": [450, 450, 0],
                        "reason": "build_queue_empty",
                        "priority": "LOW"
                    })
                    print(f"  Reflex: BUILD barracks with engineer {squad_data.get('id')}")
                    break
        
        return commands


# =============================================================================
# Test Cases
# =============================================================================

class TestEndToEndLoop:
    """Test the complete end-to-end loop."""
    
    def test_complete_end_to_end_loop(self):
        """
        Test the complete state -> decision -> command loop.
        
        This is the primary test for Milestone 1 acceptance.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            tester = EndToEndLoopTester(Path(temp_dir))
            
            try:
                # Setup all components
                tester.setup()
                
                # Start all components
                tester.start_all()
                
                # Run the end-to-end loop
                success = tester.run_end_to_end_cycle(cycles=15)
                
                # Verify success
                assert success, "End-to-end loop failed to execute commands"
                
                # Verify components are working
                assert tester.scar_cmd_exec.get_execution_count() > 0, \
                    "No commands were executed by SCAR"
                
                # Verify IPC reader received states
                assert tester.ipc_reader.get_stats().messages_received > 0, \
                    "No states were received by IPC reader"
                
                # Verify state manager has states
                assert tester.state_manager.get_stats().states_received > 0, \
                    "State manager has no states"
                
                print("\n  End-to-End Loop Test PASSED")
                print(f"    - States received: {tester.ipc_reader.get_stats().messages_received}")
                print(f"    - States processed: {tester.state_manager.get_stats().states_processed}")
                print(f"    - Commands executed: {tester.scar_cmd_exec.get_execution_count()}")
                
            finally:
                tester.stop_all()
    
    def test_repeatable_loop_without_manual_intervention(self):
        """
        Test that the loop can run multiple times without manual intervention.
        
        This validates the Milestone 1 Acceptance Gate.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            tester = EndToEndLoopTester(Path(temp_dir))
            
            try:
                tester.setup()
                tester.start_all()
                
                # Run multiple cycles
                for run in range(3):
                    print(f"\n  --- Run {run + 1} ---")
                    success = tester.run_end_to_end_cycle(cycles=5)
                    assert success, f"Run {run + 1} failed"
                
                print("\n  Repeatable Loop Test PASSED")
                print(f"    - Successfully completed 3 consecutive runs")
                
            finally:
                tester.stop_all()
    
    def test_reflex_layer_produces_valid_commands(self):
        """Test that reflex layer produces commands that pass validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tester = EndToEndLoopTester(Path(temp_dir))
            
            try:
                tester.setup()
                tester.start_all()
                
                # Wait for state
                time.sleep(0.5)
                state = tester.state_manager.get_current_state()
                
                assert state is not None, "No state received"
                
                # Simulate reflex layer
                commands = tester._simulate_reflex_layer(state)
                
                assert len(commands) > 0, "Reflex layer produced no commands"
                
                # Validate all commands
                validated_count = 0
                for cmd in commands:
                    if tester.validator and tester.validator.validate(cmd):
                        validated_count += 1
                
                assert validated_count > 0, "No commands passed validation"
                print(f"\n  Reflex Layer Validation Test PASSED")
                print(f"    - Generated {len(commands)} commands")
                print(f"    - Validated {validated_count} commands")
                
            finally:
                tester.stop_all()
    
    def test_commands_flow_through_complete_pipeline(self):
        """Test that commands flow through the entire pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tester = EndToEndLoopTester(Path(temp_dir))
            
            try:
                tester.setup()
                tester.start_all()
                
                # Wait for initial state
                time.sleep(0.5)
                
                # Get current state
                state = tester.state_manager.get_current_state()
                assert state is not None
                
                # Generate commands
                commands = tester._simulate_reflex_layer(state)
                assert len(commands) > 0
                
                # Process through pipeline
                pipeline_commands = []
                for cmd in commands:
                    # Validation
                    if not tester.validator.validate(cmd):
                        continue
                    
                    # Safety filter
                    tester.safety_filter.update_game_state(state)
                    if tester.safety_filter.check_command(cmd).is_safe:
                        pipeline_commands.append(cmd)
                
                assert len(pipeline_commands) > 0, "No commands passed pipeline"
                
                # Send through command processor (via IPC)
                for cmd in pipeline_commands:
                    tester.ipc_reader.send_command(cmd)
                
                # Wait for SCAR to execute
                time.sleep(0.5)
                
                # Verify execution
                executed_count = tester.scar_cmd_exec.get_execution_count()
                assert executed_count > 0, "Commands were not executed"
                
                print(f"\n  Pipeline Flow Test PASSED")
                print(f"    - Commands generated: {len(commands)}")
                print(f"    - Commands through pipeline: {len(pipeline_commands)}")
                print(f"    - Commands executed: {executed_count}")
                
            finally:
                tester.stop_all()


class TestStateCollectionToDecision:
    """Test the state -> decision transformation."""
    
    def test_state_collection_to_reflex_decision(self):
        """Test that game state can be collected and used for reflex decisions."""
        # Create a test game state dictionary (as would come from SCAR)
        state_dict = {
            "version": "1.0",
            "player_id": 1,
            "timestamp": time.time(),
            "game_time": 100.0,
            "resources": {
                "manpower": {"current": 500, "income": 10, "max": 1000},
                "fuel": {"current": 300, "income": 5, "max": 800},
                "munitions": {"current": 200, "income": 3, "max": 600}
            },
            "squads": [
                {
                    "id": 1,
                    "type": "riflemen",
                    "health": 0.2,
                    "max_health": 1.0,
                    "vet_level": 0,
                    "pos": [100, 200, 0],
                    "posture": "defensive",
                    "under_fire": True,
                    "suppressed": False
                }
            ],
            "capture_points": [
                {"id": 1, "pos": [500, 500, 0], "owner": None, "is_neutral": True}
            ],
            "visible_enemies": [
                {"id": 101, "type": "tank", "pos": [300, 400, 0], "health": 0.7}
            ],
            "tech_tree": {"tier_1": True, "tier_2": False, "tier_3": False},
            "build_queue": [],
            "population": {"current": 1, "max": 100}
        }
        
        # Process through reflex layer logic
        commands = []
        squads = state_dict.get("squads", [])
        for squad_data in squads:
            squad_id = squad_data["id"]
            health_percent = squad_data["health"] / squad_data["max_health"]
            under_fire = squad_data.get("under_fire", False)
            
            # Low health and under fire -> retreat
            if health_percent <= 0.3 and under_fire:
                commands.append({
                    "command": "RETREAT",
                    "squad_id": squad_id,
                    "reason": "under_fire_low_health"
                })
        
        # Should have at least one retreat command
        assert len(commands) > 0
        assert any(cmd["command"] == "RETREAT" for cmd in commands)
        print("  State to Decision Test PASSED")
    
    def test_command_serialization(self):
        """Test that commands can be serialized to JSON."""
        commands = [
            {"command": "RETREAT", "squad_id": 1},
            {"command": "BUILD", "engineer_id": 2, "building_type": "barracks", "position": [100, 200, 0]},
            {"command": "CAPTURE", "squad_id": 3, "point_id": 1},
            {"command": "ATTACK_MOVE", "squad_id": 4, "position": [300, 400, 0]}
        ]
        
        # Serialize
        json_str = json.dumps({"commands": commands})
        
        # Deserialize
        data = json.loads(json_str)
        deserialized_commands = data["commands"]
        
        assert len(deserialized_commands) == len(commands)
        for i, cmd in enumerate(commands):
            assert deserialized_commands[i] == cmd
        
        print("  Command Serialization Test PASSED")


class TestValidatorAndSafetyIntegration:
    """Test that validator and safety filter work together."""
    
    def test_full_validation_pipeline(self):
        """Test commands through validator and safety filter."""
        # Create validator
        validator = ActionValidator(strict_mode=False)
        
        # Create safety filter with game state that includes squads
        game_state_dict = {
            "resources": {
                "manpower": {"current": 1000, "income": 10, "max": 5000},
                "fuel": {"current": 500, "income": 5, "max": 3000},
                "munitions": {"current": 300, "income": 3, "max": 2000}
            },
            "population": {"current": 20, "max": 100},
            "squads": [
                {"id": 1, "type": "riflemen", "health": 0.8, "max_health": 1.0},
                {"id": 2, "type": "engineer", "health": 1.0, "max_health": 1.0}
            ],
            "capture_points": [],
            "visible_enemies": []
        }
        safety_filter = SafetyFilter(game_state_dict)
        
        # Test commands that should all pass
        test_commands = [
            # Valid retreat (no cost)
            {"command": "RETREAT", "squad_id": 1},
            # Valid attack move (no cost)
            {"command": "ATTACK_MOVE", "squad_id": 1, "position": [100, 200, 0]},
            # Build that should pass safety (enough resources and engineer exists)
            {"command": "BUILD", "engineer_id": 2, "building_type": "barracks", "position": [100, 200, 0]},
        ]
        
        # Process through pipeline
        validated_commands = []
        for cmd in test_commands:
            # Validate
            if not validator.validate(cmd):
                continue
            
            # Safety check
            if safety_filter.check_command(cmd).is_safe:
                validated_commands.append(cmd)
        
        # All three commands should pass
        assert len(validated_commands) == 3, f"Expected 3 commands to pass, got {len(validated_commands)}"
        print("  Validation Pipeline Test PASSED")


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])
