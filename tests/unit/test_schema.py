"""
Unit Tests for Schema Module

Tests all JSON schema definitions and serialization/deserialization.
"""

import json
import pytest
from pathlib import Path
import sys

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from schema import (
    SCHEMA_VERSION,
    ResourceType, SquadType, Posture, Faction, GamePhase, Difficulty,
    ResourceData, Position, SquadData, CapturePointData, EnemyData,
    TechTreeData, BuildQueueItem, PopulationData, GameState,
    CommandType, Command, BuildCommand, CaptureCommand, AttackMoveCommand,
    SetPostureCommand, ProduceCommand, RetreatCommand, StopCommand, HoldCommand,
    create_command, validate_game_state, validate_command,
    IntentType, Intent, BuildIntent, TechIntent, ProduceIntent, StrategicPlan
)


class TestEnums:
    """Test enum definitions."""
    
    def test_resource_type_enum(self):
        """Test resource type enum values."""
        assert ResourceType.MANPOWER.value == "manpower"
        assert ResourceType.FUEL.value == "fuel"
        assert ResourceType.MUNITIONS.value == "munitions"
    
    def test_squad_type_enum(self):
        """Test squad type enum values."""
        assert SquadType.RIFLEMEN.value == "riflemen"
        assert SquadType.ENGINEER.value == "engineer"
        assert SquadType.LIGHT_TANK.value == "light_tank"
        assert SquadType.HEAVY_TANK.value == "heavy_tank"
    
    def test_posture_enum(self):
        """Test posture enum values."""
        assert Posture.AGGRESSIVE.value == "aggressive"
        assert Posture.DEFENSIVE.value == "defensive"
        assert Posture.RETREAT.value == "retreat"
        assert Posture.HOLD.value == "hold"
    
    def test_faction_enum(self):
        """Test faction enum values."""
        assert Faction.ALLIES.value == "allies"
        assert Faction.AXIS.value == "axis"
    
    def test_game_phase_enum(self):
        """Test game phase enum values."""
        assert GamePhase.EARLY.value == "early"
        assert GamePhase.MID.value == "mid"
        assert GamePhase.LATE.value == "late"
    
    def test_difficulty_enum(self):
        """Test difficulty enum values."""
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.NORMAL.value == "normal"
        assert Difficulty.HARD.value == "hard"
        assert Difficulty.EXPERT.value == "expert"
    
    def test_command_type_enum(self):
        """Test command type enum values."""
        assert CommandType.BUILD.value == "BUILD"
        assert CommandType.CAPTURE.value == "CAPTURE"
        assert CommandType.ATTACK_MOVE.value == "ATTACK_MOVE"
        assert CommandType.SET_POSTURE.value == "SET_POSTURE"
        assert CommandType.PRODUCE.value == "PRODUCE"
        assert CommandType.RETREAT.value == "RETREAT"
        assert CommandType.STOP.value == "STOP"
        assert CommandType.HOLD.value == "HOLD"
        assert CommandType.PING.value == "PING"
        assert CommandType.PONG.value == "PONG"
    
    def test_intent_type_enum(self):
        """Test intent type enum values."""
        assert IntentType.BUILD.value == "BUILD"
        assert IntentType.TECH.value == "TECH"
        assert IntentType.PRODUCE.value == "PRODUCE"
        assert IntentType.ATTACK.value == "ATTACK"
        assert IntentType.DEFEND.value == "DEFEND"


class TestResourceData:
    """Test resource data class."""
    
    def test_resource_data_creation(self):
        """Test creating resource data."""
        resource = ResourceData(current=500, income=10, max=1000)
        assert resource.current == 500
        assert resource.income == 10
        assert resource.max == 1000
    
    def test_resource_data_to_dict(self):
        """Test resource data to dictionary."""
        resource = ResourceData(current=500, income=10, max=1000)
        result = resource.to_dict()
        
        assert result["current"] == 500
        assert result["income"] == 10
        assert result["max"] == 1000
    
    def test_resource_data_from_dict(self):
        """Test resource data from dictionary."""
        data = {"current": 600, "income": 15, "max": 1200}
        resource = ResourceData.from_dict(data)
        
        assert resource.current == 600
        assert resource.income == 15
        assert resource.max == 1200
    
    def test_resource_data_partial_dict(self):
        """Test resource data from partial dictionary."""
        data = {"current": 700, "max": 1500}
        resource = ResourceData.from_dict(data)
        
        assert resource.current == 700
        assert resource.income == 0  # Default
        assert resource.max == 1500


class TestPosition:
    """Test position class."""
    
    def test_position_creation(self):
        """Test creating position."""
        pos = Position(x=100.0, y=200.0, z=50.0)
        assert pos.x == 100.0
        assert pos.y == 200.0
        assert pos.z == 50.0
    
    def test_position_to_list(self):
        """Test position to list."""
        pos = Position(x=100.0, y=200.0, z=50.0)
        result = pos.to_list()
        
        assert result == [100.0, 200.0, 50.0]
    
    def test_position_to_dict(self):
        """Test position to dictionary."""
        pos = Position(x=100.0, y=200.0, z=50.0)
        result = pos.to_dict()
        
        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert result["z"] == 50.0
    
    def test_position_from_list(self):
        """Test position from list."""
        pos = Position.from_list([100.0, 200.0, 50.0])
        assert pos.x == 100.0
        assert pos.y == 200.0
        assert pos.z == 50.0
    
    def test_position_from_list_partial(self):
        """Test position from partial list."""
        pos = Position.from_list([100.0])
        assert pos.x == 100.0
        assert pos.y == 0.0
        assert pos.z == 0.0
    
    def test_position_from_dict(self):
        """Test position from dictionary."""
        data = {"x": 100.0, "y": 200.0, "z": 50.0}
        pos = Position.from_dict(data)
        
        assert pos.x == 100.0
        assert pos.y == 200.0
        assert pos.z == 50.0
    
    def test_position_distance_to(self):
        """Test distance calculation between positions."""
        pos1 = Position(x=0.0, y=0.0, z=0.0)
        pos2 = Position(x=3.0, y=4.0, z=0.0)
        
        distance = pos1.distance_to(pos2)
        assert abs(distance - 5.0) < 0.001  # sqrt(3^2 + 4^2) = 5


class TestSquadData:
    """Test squad data class."""
    
    def test_squad_data_creation(self):
        """Test creating squad data."""
        pos = Position(x=100.0, y=200.0, z=0.0)
        squad = SquadData(
            id=1,
            type="riflemen",
            health=0.8,
            max_health=1.0,
            vet_level=2,
            position=pos,
            posture="defensive",
            target=None
        )
        
        assert squad.id == 1
        assert squad.type == "riflemen"
        assert squad.health == 0.8
        assert squad.max_health == 1.0
        assert squad.vet_level == 2
        assert squad.posture == "defensive"
        assert squad.target is None
    
    def test_squad_data_to_dict(self):
        """Test squad data to dictionary."""
        pos = Position(x=100.0, y=200.0, z=0.0)
        squad = SquadData(
            id=1,
            type="riflemen",
            health=0.8,
            max_health=1.0,
            vet_level=2,
            position=pos,
            posture="defensive",
            target=None
        )
        
        result = squad.to_dict()
        assert result["id"] == 1
        assert result["type"] == "riflemen"
        assert result["health"] == 0.8
        assert result["max_health"] == 1.0
        assert result["vet_level"] == 2
        assert result["position"] == [100.0, 200.0, 0.0]
        assert result["posture"] == "defensive"
    
    def test_squad_data_from_dict(self):
        """Test squad data from dictionary."""
        data = {
            "id": 2,
            "type": "machine_gun",
            "health": 0.5,
            "max_health": 1.0,
            "vet": 3,  # Note: uses 'vet' key
            "pos": [150.0, 250.0, 0.0],
            "posture": "aggressive",
            "target": 3
        }
        
        squad = SquadData.from_dict(data)
        assert squad.id == 2
        assert squad.type == "machine_gun"
        assert squad.health == 0.5
        assert squad.vet_level == 3
        assert squad.position.x == 150.0
    
    def test_squad_health_percentage(self):
        """Test squad health percentage calculation."""
        squad = SquadData(
            id=1,
            type="riflemen",
            health=0.6,
            max_health=0.8,
            vet_level=0,
            position=Position(x=0, y=0, z=0),
            posture="defensive",
            target=None
        )
        
        percentage = squad.health_percentage()
        assert abs(percentage - 0.75) < 0.001  # 0.6 / 0.8 = 0.75


class TestCapturePointData:
    """Test capture point data class."""
    
    def test_capture_point_creation(self):
        """Test creating capture point data."""
        pos = Position(x=500.0, y=500.0, z=0.0)
        cp = CapturePointData(
            id=1,
            position=pos,
            owner=1,
            capture_progress=0.5,
            is_neutral=False
        )
        
        assert cp.id == 1
        assert cp.position == pos
        assert cp.owner == 1
        assert cp.capture_progress == 0.5
        assert cp.is_neutral == False
    
    def test_capture_point_to_dict(self):
        """Test capture point to dictionary."""
        pos = Position(x=500.0, y=500.0, z=0.0)
        cp = CapturePointData(
            id=1,
            position=pos,
            owner=1,
            capture_progress=0.5,
            is_neutral=False
        )
        
        result = cp.to_dict()
        assert result["id"] == 1
        assert result["position"] == [500.0, 500.0, 0.0]
        assert result["owner"] == 1
        assert result["capture_progress"] == 0.5
    
    def test_capture_point_from_dict(self):
        """Test capture point from dictionary."""
        data = {
            "id": 2,
            "position": [600.0, 600.0, 0.0],
            "owner": None,
            "progress": 0.3,  # Note: uses 'progress' key
            "is_neutral": True
        }
        
        cp = CapturePointData.from_dict(data)
        assert cp.id == 2
        assert cp.position.x == 600.0
        assert cp.owner is None
        assert cp.capture_progress == 0.3


class TestEnemyData:
    """Test enemy data class."""
    
    def test_enemy_data_creation(self):
        """Test creating enemy data."""
        pos = Position(x=800.0, y=800.0, z=0.0)
        enemy = EnemyData(
            id=1,
            type="riflemen",
            health=0.7,
            position=pos,
            posture="aggressive",
            distance=500.0,
            in_combat=True
        )
        
        assert enemy.id == 1
        assert enemy.type == "riflemen"
        assert enemy.health == 0.7
        assert enemy.distance == 500.0
    
    def test_enemy_data_to_dict(self):
        """Test enemy data to dictionary."""
        pos = Position(x=800.0, y=800.0, z=0.0)
        enemy = EnemyData(
            id=1,
            type="riflemen",
            health=0.7,
            position=pos,
            posture="aggressive",
            distance=500.0
        )
        
        result = enemy.to_dict()
        assert result["id"] == 1
        assert result["type"] == "riflemen"
        assert result["position"] == [800.0, 800.0, 0.0]


class TestTechTreeData:
    """Test tech tree data class."""
    
    def test_tech_tree_creation(self):
        """Test creating tech tree data."""
        tech = TechTreeData(
            tier_1=True,
            tier_2=False,
            tier_3=False,
            abilities=["scout", "riflemen"],
            tier_1_progress=1.0,
            tier_2_progress=0.0,
            tier_3_progress=0.0
        )
        
        assert tech.tier_1 == True
        assert tech.tier_2 == False
        assert tech.tier_3 == False
        assert tech.abilities == ["scout", "riflemen"]
    
    def test_tech_tree_to_dict(self):
        """Test tech tree to dictionary."""
        tech = TechTreeData(
            tier_1=True,
            tier_2=False,
            tier_3=False,
            abilities=["scout", "riflemen"]
        )
        
        result = tech.to_dict()
        assert result["tier_1"] == True
        assert result["tier_2"] == False
        assert result["abilities"] == ["scout", "riflemen"]
    
    def test_tech_tree_from_dict(self):
        """Test tech tree from dictionary."""
        data = {
            "t1": True,  # Note: uses 't1' key
            "t2": True,
            "t3": False,
            "abilities": ["barracks", "tank_depot"],
            "t1_progress": 0.8,
            "t2_progress": 0.5
        }
        
        tech = TechTreeData.from_dict(data)
        assert tech.tier_1 == True
        assert tech.tier_2 == True
        assert tech.abilities == ["barracks", "tank_depot"]


class TestBuildQueueItem:
    """Test build queue item class."""
    
    def test_build_queue_item_creation(self):
        """Test creating build queue item."""
        item = BuildQueueItem(
            item_type="unit",
            name="riflemen",
            progress=0.5,
            estimated_time=30.0,
            cost={"manpower": 300, "fuel": 0, "munitions": 0}
        )
        
        assert item.item_type == "unit"
        assert item.name == "riflemen"
        assert item.progress == 0.5
        assert item.estimated_time == 30.0
        assert item.cost["manpower"] == 300
    
    def test_build_queue_item_to_dict(self):
        """Test build queue item to dictionary."""
        item = BuildQueueItem(
            item_type="building",
            name="barracks",
            progress=0.8,
            estimated_time=45.0,
            cost={"manpower": 500, "fuel": 100, "munitions": 0}
        )
        
        result = item.to_dict()
        assert result["type"] == "building"
        assert result["name"] == "barracks"
        assert result["progress"] == 0.8
        assert result["time"] == 45.0
        assert result["cost"] == [500, 100, 0]
    
    def test_build_queue_item_from_dict(self):
        """Test build queue item from dictionary."""
        data = {
            "type": "unit",
            "name": "engineer",
            "progress": 0.2,
            "time": 20.0,
            "cost": [200, 0, 0]
        }
        
        item = BuildQueueItem.from_dict(data)
        assert item.item_type == "unit"
        assert item.name == "engineer"
        assert item.cost["manpower"] == 200


class TestPopulationData:
    """Test population data class."""
    
    def test_population_creation(self):
        """Test creating population data."""
        pop = PopulationData(current=20, max=100)
        
        assert pop.current == 20
        assert pop.max == 100
    
    def test_population_to_list(self):
        """Test population to list."""
        pop = PopulationData(current=20, max=100)
        result = pop.to_list()
        
        assert result == [20, 100]
    
    def test_population_to_dict(self):
        """Test population to dictionary."""
        pop = PopulationData(current=20, max=100)
        result = pop.to_dict()
        
        assert result["current"] == 20
        assert result["max"] == 100
    
    def test_population_from_list(self):
        """Test population from list."""
        pop = PopulationData.from_list([30, 120])
        
        assert pop.current == 30
        assert pop.max == 120
    
    def test_population_from_dict(self):
        """Test population from dictionary."""
        data = {"current": 40, "max": 80}
        pop = PopulationData.from_dict(data)
        
        assert pop.current == 40
        assert pop.max == 80
    
    def test_population_percentage(self):
        """Test population percentage calculation."""
        pop = PopulationData(current=50, max=100)
        assert pop.percentage() == 0.5
        
        pop2 = PopulationData(current=0, max=100)
        assert pop2.percentage() == 0.0


class TestGameState:
    """Test game state class."""
    
    def test_game_state_creation(self):
        """Test creating a game state."""
        state = GameState(
            version="1.0",
            player_id=1,
            timestamp=123.456,
            game_time=300.0,
            game_phase="mid",
            population=PopulationData(current=0, max=100)
        )
        
        assert state.version == "1.0"
        assert state.player_id == 1
        assert state.timestamp == 123.456
        assert state.game_time == 300.0
        assert state.game_phase == "mid"
    
    def test_game_state_full_creation(self):
        """Test creating a complete game state."""
        state = GameState(
            version="1.0",
            player_id=1,
            timestamp=123.456,
            game_time=300.0,
            game_phase="mid",
            resources={
                "manpower": ResourceData(500, 10, 1000),
                "fuel": ResourceData(300, 5, 800),
                "munitions": ResourceData(200, 3, 600)
            },
            squads=[
                SquadData(
                    id=1,
                    type="riflemen",
                    health=0.8,
                    max_health=1.0,
                    vet_level=2,
                    position=Position(100, 200, 0),
                    posture="defensive",
                    target=None
                )
            ],
            capture_points=[
                CapturePointData(
                    id=1,
                    position=Position(500, 500, 0),
                    owner=1,
                    capture_progress=0.5,
                    is_neutral=False
                )
            ],
            visible_enemies=[],
            tech_tree=TechTreeData(
                tier_1=True,
                tier_2=False,
                abilities=["scout", "riflemen"]
            ),
            build_queue=[
                BuildQueueItem(
                    item_type="unit",
                    name="riflemen",
                    progress=0.5,
                    estimated_time=30,
                    cost={"manpower": 300, "fuel": 0, "munitions": 0}
                )
            ],
            population=PopulationData(current=20, max=100)
        )
        
        assert len(state.squads) == 1
        assert len(state.capture_points) == 1
        assert state.tech_tree.tier_1 == True
    
    def test_game_state_to_dict(self):
        """Test game state to dictionary."""
        state = GameState(
            version="1.0",
            player_id=1,
            timestamp=123.456,
            game_time=300.0,
            game_phase="mid",
            resources={
                "manpower": ResourceData(500, 10, 1000),
                "fuel": ResourceData(300, 5, 800),
                "munitions": ResourceData(200, 3, 600)
            },
            squads=[],
            capture_points=[],
            population=PopulationData(current=20, max=100)
        )
        
        result = state.to_dict()
        assert result["v"] == "1.0"
        assert result["player"] == 1
        assert result["time"] == 123.456
        assert result["game_time"] == 300.0
        assert result["phase"] == "mid"
    
    def test_game_state_to_json(self):
        """Test game state to JSON string."""
        state = GameState(
            version="1.0",
            player_id=1,
            timestamp=123.456,
            game_time=300.0,
            game_phase="mid",
            population=PopulationData(current=20, max=100)
        )
        
        json_str = state.to_json()
        assert isinstance(json_str, str)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["v"] == "1.0"
    
    def test_game_state_from_dict(self):
        """Test game state from dictionary."""
        data = {
            "v": "1.0",
            "player": 1,
            "time": 123.456,
            "game_time": 300.0,
            "phase": "mid",
            "resources": {
                "manpower": {"current": 500, "income": 10, "max": 1000},
                "fuel": {"current": 300, "income": 5, "max": 800},
                "munitions": {"current": 200, "income": 3, "max": 600}
            },
            "squads": [
                {
                    "id": 1,
                    "type": "riflemen",
                    "health": 0.8,
                    "max_health": 1.0,
                    "vet_level": 2,
                    "pos": [100, 200, 0],
                    "posture": "defensive"
                }
            ],
            "cps": [
                {
                    "id": 1,
                    "pos": [500, 500, 0],
                    "owner": 1,
                    "capture_progress": 0.5,
                    "is_neutral": False
                }
            ],
            "enemies": [],
            "tech": {
                "tier_1": True,
                "tier_2": False,
                "abilities": ["scout", "riflemen"]
            },
            "queue": [],
            "pop": [20, 100],
            "faction": "allies"
        }
        
        state = GameState.from_dict(data)
        assert state.player_id == 1
        assert state.game_time == 300.0
        assert len(state.squads) == 1
        assert state.squads[0].id == 1
    
    def test_game_state_from_json(self):
        """Test game state from JSON string."""
        json_str = json.dumps({
            "v": "1.0",
            "player": 1,
            "time": 123.456,
            "game_time": 300.0,
            "phase": "mid",
            "resources": {
                "manpower": {"current": 500, "income": 10, "max": 1000}
            },
            "squads": [],
            "cps": [],
            "enemies": [],
            "tech": {},
            "queue": [],
            "pop": [0, 100],
            "faction": "allies"
        })
        
        state = GameState.from_json(json_str)
        assert state.version == "1.0"
        assert state.player_id == 1
    
    def test_game_state_roundtrip(self):
        """Test game state serialization and deserialization roundtrip."""
        # Create a complex state
        original_state = GameState(
            version="1.0",
            player_id=1,
            timestamp=123.456,
            game_time=300.0,
            game_phase="mid",
            resources={
                "manpower": ResourceData(500, 10, 1000),
                "fuel": ResourceData(300, 5, 800),
                "munitions": ResourceData(200, 3, 600)
            },
            squads=[
                SquadData(
                    id=1,
                    type="riflemen",
                    health=0.8,
                    max_health=1.0,
                    vet_level=2,
                    position=Position(100, 200, 0),
                    posture="defensive",
                    target=None
                )
            ],
            capture_points=[
                CapturePointData(
                    id=1,
                    position=Position(500, 500, 0),
                    owner=1,
                    capture_progress=0.5,
                    is_neutral=False
                )
            ],
            visible_enemies=[],
            tech_tree=TechTreeData(
                tier_1=True,
                tier_2=False,
                abilities=["scout", "riflemen"]
            ),
            build_queue=[],
            population=PopulationData(current=20, max=100)
        )
        
        # Serialize to JSON
        json_data = original_state.to_json()
        
        # Deserialize back
        restored_state = GameState.from_json(json_data)
        
        # Verify
        assert restored_state.player_id == original_state.player_id
        assert restored_state.game_time == original_state.game_time
        assert len(restored_state.squads) == len(original_state.squads)
        assert restored_state.squads[0].id == original_state.squads[0].id


class TestCommands:
    """Test command classes."""
    
    def test_base_command(self):
        """Test base command."""
        cmd = Command(command="TEST", timestamp=123.456)
        assert cmd.command == "TEST"
        assert cmd.timestamp == 123.456
    
    def test_build_command(self):
        """Test build command."""
        cmd = BuildCommand(
            engineer_id=1,
            building_type="barracks",
            position=Position(100, 200, 0)
        )
        
        assert cmd.command == "BUILD"
        assert cmd.engineer_id == 1
        assert cmd.building_type == "barracks"
        
        result = cmd.to_dict()
        assert result["command"] == "BUILD"
        assert result["engineer_id"] == 1
        assert result["building_type"] == "barracks"
    
    def test_capture_command(self):
        """Test capture command."""
        cmd = CaptureCommand(squad_id=1, point_id=2)
        
        assert cmd.command == "CAPTURE"
        assert cmd.squad_id == 1
        assert cmd.point_id == 2
        
        result = cmd.to_dict()
        assert result["command"] == "CAPTURE"
        assert result["squad_id"] == 1
        assert result["point_id"] == 2
    
    def test_attack_move_command(self):
        """Test attack move command."""
        cmd = AttackMoveCommand(
            squad_id=1,
            position=Position(300, 400, 0)
        )
        
        assert cmd.command == "ATTACK_MOVE"
        assert cmd.squad_id == 1
        
        result = cmd.to_dict()
        assert result["command"] == "ATTACK_MOVE"
        assert result["squad_id"] == 1
        assert result["position"] == [300, 400, 0]
    
    def test_set_posture_command(self):
        """Test set posture command."""
        cmd = SetPostureCommand(squad_id=1, posture="aggressive")
        
        assert cmd.command == "SET_POSTURE"
        assert cmd.squad_id == 1
        assert cmd.posture == "aggressive"
        
        result = cmd.to_dict()
        assert result["command"] == "SET_POSTURE"
        assert result["posture"] == "aggressive"
    
    def test_produce_command(self):
        """Test produce command."""
        cmd = ProduceCommand(building_id=1, unit_type="riflemen")
        
        assert cmd.command == "PRODUCE"
        assert cmd.building_id == 1
        assert cmd.unit_type == "riflemen"
        
        result = cmd.to_dict()
        assert result["command"] == "PRODUCE"
        assert result["building_id"] == 1
        assert result["unit_type"] == "riflemen"
    
    def test_retreat_command(self):
        """Test retreat command."""
        cmd = RetreatCommand(squad_id=1)
        
        assert cmd.command == "RETREAT"
        assert cmd.squad_id == 1
        
        result = cmd.to_dict()
        assert result["command"] == "RETREAT"
        assert result["squad_id"] == 1
    
    def test_stop_command(self):
        """Test stop command."""
        cmd = StopCommand(squad_id=1)
        
        assert cmd.command == "STOP"
        assert cmd.squad_id == 1
    
    def test_hold_command(self):
        """Test hold command."""
        cmd = HoldCommand(squad_id=1)
        
        assert cmd.command == "HOLD"
        assert cmd.squad_id == 1
    
    def test_create_command(self):
        """Test command factory."""
        data = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        
        cmd = create_command(data)
        assert isinstance(cmd, BuildCommand)
        assert cmd.engineer_id == 1
    
    def test_create_unknown_command(self):
        """Test creating unknown command type."""
        data = {"command": "UNKNOWN_COMMAND", "timestamp": 123.456}
        
        cmd = create_command(data)
        assert isinstance(cmd, Command)
        assert cmd.command == "UNKNOWN_COMMAND"


class TestValidation:
    """Test validation functions."""
    
    def test_validate_game_state_valid(self):
        """Test validation of valid game state."""
        state = GameState(
            version="1.0",
            player_id=1,
            timestamp=123.456,
            game_time=300.0,
            game_phase="mid",
            resources={
                "manpower": ResourceData(500, 10, 1000),
                "fuel": ResourceData(300, 5, 800),
                "munitions": ResourceData(200, 3, 600)
            },
            squads=[
                SquadData(
                    id=1,
                    type="riflemen",
                    health=0.8,
                    max_health=1.0,
                    vet_level=2,
                    position=Position(100, 200, 0),
                    posture="defensive",
                    target=None
                )
            ],
            population=PopulationData(current=20, max=100)
        )
        
        assert validate_game_state(state) == True
    
    def test_validate_game_state_invalid_player(self):
        """Test validation of state with invalid player_id."""
        state = GameState(
            version="1.0",
            player_id=0,  # Invalid
            timestamp=123.456,
            population=PopulationData(current=0, max=100)
        )
        
        assert validate_game_state(state) == False
    
    def test_validate_game_state_invalid_timestamp(self):
        """Test validation of state with invalid timestamp."""
        state = GameState(
            version="1.0",
            player_id=1,
            timestamp=0,  # Invalid
            population=PopulationData(current=0, max=100)
        )
        
        assert validate_game_state(state) == False
    
    def test_validate_game_state_negative_resources(self):
        """Test validation of state with negative resources."""
        state = GameState(
            version="1.0",
            player_id=1,
            timestamp=123.456,
            resources={
                "manpower": ResourceData(-100, 10, 1000)  # Negative current
            },
            population=PopulationData(current=0, max=100)
        )
        
        assert validate_game_state(state) == False
    
    def test_validate_command_valid(self):
        """Test validation of valid command."""
        cmd = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        
        assert validate_command(cmd) == True
    
    def test_validate_command_missing_field(self):
        """Test validation of command with missing field."""
        cmd = {
            "command": "BUILD",
            "engineer_id": 1
            # Missing building_type and position
        }
        
        assert validate_command(cmd) == False
    
    def test_validate_command_unknown_type(self):
        """Test validation of unknown command type."""
        cmd = {
            "command": "UNKNOWN",
            "some_field": "value"
        }
        
        # Unknown commands don't have required fields, so they pass
        assert validate_command(cmd) == True
    
    def test_validate_command_no_command_field(self):
        """Test validation of command without command field."""
        cmd = {"some_field": "value"}
        
        assert validate_command(cmd) == False


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
