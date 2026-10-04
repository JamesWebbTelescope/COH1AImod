"""
CoH1 × Mistral AI Mod - JSON Schema Definitions

Defines the schema for all JSON data exchanged between SCAR mod and Python orchestrator.

Author: Generated via planner skill
Version: 0.1.0
Date: 2026-10-04
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import re


# ============================================
# Schema Versions
# ============================================

SCHEMA_VERSION = "1.0"


# ============================================
# Game State Schema
# ============================================

class ResourceType(Enum):
    """Game resource types."""
    MANPOWER = "manpower"
    FUEL = "fuel"
    MUNITIONS = "munitions"


class SquadType(Enum):
    """Game squad types."""
    RIFLEMEN = "riflemen"
    ENGINEER = "engineer"
    SCOUT = "scout_car"
    GRENADIER = "grenadier"
    MORTAR = "mortar"
    MG = "machine_gun"
    SNIPER = "sniper"
    BAZOOKA = "bazooka"
    LIGHT_TANK = "light_tank"
    MEDIUM_TANK = "medium_tank"
    HEAVY_TANK = "heavy_tank"


class Posture(Enum):
    """Squad postures."""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    RETREAT = "retreat"
    HOLD = "hold"


class Faction(Enum):
    """Game factions."""
    ALLIES = "allies"
    AXIS = "axis"


class GamePhase(Enum):
    """Game phases."""
    EARLY = "early"
    MID = "mid"
    LATE = "late"


class Difficulty(Enum):
    """AI difficulty levels."""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class ResourceData:
    """Player resource data."""
    current: int
    income: int
    max: int
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "current": self.current,
            "income": self.income,
            "max": self.max
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceData":
        return cls(
            current=data.get("current", 0),
            income=data.get("income", 0),
            max=data.get("max", 0)
        )


@dataclass
class Position:
    """3D position in game world."""
    x: float
    y: float
    z: float
    
    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z
        }
    
    @classmethod
    def from_list(cls, data: List[float]) -> "Position":
        return cls(
            x=data[0] if len(data) > 0 else 0.0,
            y=data[1] if len(data) > 1 else 0.0,
            z=data[2] if len(data) > 2 else 0.0
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Position":
        return cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            z=data.get("z", 0.0)
        )
    
    def distance_to(self, other: "Position") -> float:
        """Calculate Euclidean distance to another position."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return (dx*dx + dy*dy + dz*dz) ** 0.5


@dataclass
class SquadData:
    """Data for a single squad/unit."""
    id: int
    type: str
    health: float
    max_health: float
    vet_level: int
    position: Position
    posture: str
    target: Optional[int]
    in_combat: bool = False
    under_fire: bool = False
    suppressed: bool = False
    pinned: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "health": self.health,
            "max_health": self.max_health,
            "vet_level": self.vet_level,
            "position": self.position.to_list(),
            "posture": self.posture,
            "target": self.target,
            "in_combat": self.in_combat,
            "under_fire": self.under_fire,
            "suppressed": self.suppressed,
            "pinned": self.pinned
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SquadData":
        return cls(
            id=data.get("id", 0),
            type=data.get("type", "unknown"),
            health=data.get("health", 1.0),
            max_health=data.get("max_health", 1.0),
            vet_level=data.get("vet", data.get("vet_level", 0)),
            position=Position.from_list(data.get("pos", data.get("position", [0, 0, 0]))),
            posture=data.get("posture", "defensive"),
            target=data.get("target"),
            in_combat=data.get("in_combat", False),
            under_fire=data.get("under_fire", False),
            suppressed=data.get("suppressed", False),
            pinned=data.get("pinned", False)
        )
    
    def health_percentage(self) -> float:
        """Get health as percentage."""
        if self.max_health > 0:
            return self.health / self.max_health
        return 0.0


@dataclass
class CapturePointData:
    """Data for a capture point."""
    id: int
    position: Position
    owner: Optional[int]
    capture_progress: float
    is_neutral: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "position": self.position.to_list(),
            "owner": self.owner,
            "capture_progress": self.capture_progress,
            "is_neutral": self.is_neutral
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapturePointData":
        return cls(
            id=data.get("id", 0),
            position=Position.from_list(data.get("pos", data.get("position", [0, 0, 0]))),
            owner=data.get("owner"),
            capture_progress=data.get("progress", data.get("capture_progress", 0.0)),
            is_neutral=data.get("is_neutral", False)
        )


@dataclass
class EnemyData:
    """Data for visible enemy units."""
    id: int
    type: str
    health: float
    position: Position
    posture: str
    distance: float
    in_combat: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "health": self.health,
            "position": self.position.to_list(),
            "posture": self.posture,
            "distance": self.distance,
            "in_combat": self.in_combat
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnemyData":
        return cls(
            id=data.get("id", 0),
            type=data.get("type", "unknown"),
            health=data.get("health", 1.0),
            position=Position.from_list(data.get("pos", data.get("position", [0, 0, 0]))),
            posture=data.get("posture", "aggressive"),
            distance=data.get("distance", 0.0),
            in_combat=data.get("in_combat", False)
        )


@dataclass
class TechTreeData:
    """Tech tree state."""
    tier_1: bool = False
    tier_2: bool = False
    tier_3: bool = False
    abilities: List[str] = field(default_factory=list)
    tier_1_progress: float = 0.0
    tier_2_progress: float = 0.0
    tier_3_progress: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier_1": self.tier_1,
            "tier_2": self.tier_2,
            "tier_3": self.tier_3,
            "abilities": self.abilities,
            "t1_progress": self.tier_1_progress,
            "t2_progress": self.tier_2_progress,
            "t3_progress": self.tier_3_progress
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TechTreeData":
        return cls(
            tier_1=data.get("t1", data.get("tier_1", False)),
            tier_2=data.get("t2", data.get("tier_2", False)),
            tier_3=data.get("t3", data.get("tier_3", False)),
            abilities=data.get("abilities", []),
            tier_1_progress=data.get("t1_progress", data.get("tier_1_progress", 0.0)),
            tier_2_progress=data.get("t2_progress", data.get("tier_2_progress", 0.0)),
            tier_3_progress=data.get("t3_progress", data.get("tier_3_progress", 0.0))
        )


@dataclass
class BuildQueueItem:
    """Item in the build queue."""
    item_type: str  # "unit", "building", "ability"
    name: str
    progress: float  # 0.0 - 1.0
    estimated_time: float  # seconds remaining
    cost: Dict[str, int]  # {"manpower": X, "fuel": Y, "munitions": Z}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.item_type,
            "name": self.name,
            "progress": self.progress,
            "time": self.estimated_time,
            "cost": [self.cost.get("manpower", 0), self.cost.get("fuel", 0), self.cost.get("munitions", 0)]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildQueueItem":
        cost_list = data.get("cost", [0, 0, 0])
        cost = {
            "manpower": cost_list[0] if len(cost_list) > 0 else 0,
            "fuel": cost_list[1] if len(cost_list) > 1 else 0,
            "munitions": cost_list[2] if len(cost_list) > 2 else 0
        }
        
        return cls(
            item_type=data.get("type", "unit"),
            name=data.get("name", "unknown"),
            progress=data.get("progress", 0.0),
            estimated_time=data.get("time", data.get("estimated_time", 0.0)),
            cost=cost
        )


@dataclass
class PopulationData:
    """Population data."""
    current: int
    max: int
    
    def to_list(self) -> List[int]:
        return [self.current, self.max]
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "current": self.current,
            "max": self.max
        }
    
    @classmethod
    def from_list(cls, data: List[int]) -> "PopulationData":
        return cls(
            current=data[0] if len(data) > 0 else 0,
            max=data[1] if len(data) > 1 else 100
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PopulationData":
        return cls(
            current=data.get("current", 0),
            max=data.get("max", 100)
        )
    
    def percentage(self) -> float:
        """Get population usage as percentage."""
        if self.max > 0:
            return self.current / self.max
        return 0.0


@dataclass
class GameState:
    """
    Complete game state snapshot.
    
    This is the main data structure exchanged between SCAR mod and Python orchestrator.
    """
    version: str = SCHEMA_VERSION
    player_id: int = 1
    timestamp: float = 0.0
    game_time: float = 0.0
    game_phase: str = "early"
    resources: Dict[str, ResourceData] = field(default_factory=dict)
    squads: List[SquadData] = field(default_factory=list)
    capture_points: List[CapturePointData] = field(default_factory=list)
    visible_enemies: List[EnemyData] = field(default_factory=list)
    tech_tree: TechTreeData = field(default_factory=TechTreeData)
    build_queue: List[BuildQueueItem] = field(default_factory=list)
    population: PopulationData = field(default_factory=PopulationData)
    faction: str = "allies"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to dictionary for JSON serialization."""
        return {
            "v": self.version,
            "player": self.player_id,
            "time": self.timestamp,
            "game_time": self.game_time,
            "phase": self.game_phase,
            "resources": {
                "manpower": self.resources.get("manpower", ResourceData(0, 0, 0)).to_dict(),
                "fuel": self.resources.get("fuel", ResourceData(0, 0, 0)).to_dict(),
                "munitions": self.resources.get("munitions", ResourceData(0, 0, 0)).to_dict()
            },
            "squads": [squad.to_dict() for squad in self.squads],
            "cps": [cp.to_dict() for cp in self.capture_points],
            "enemies": [enemy.to_dict() for enemy in self.visible_enemies],
            "tech": self.tech_tree.to_dict(),
            "queue": [item.to_dict() for item in self.build_queue],
            "pop": self.population.to_list(),
            "faction": self.faction
        }
    
    def to_json(self) -> str:
        """Convert game state to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        """Create GameState from dictionary."""
        # Handle both full and compact formats
        resources = {}
        if "resources" in data:
            if isinstance(data["resources"], dict):
                # Full format
                for key, value in data["resources"].items():
                    if isinstance(value, dict):
                        resources[key] = ResourceData.from_dict(value)
                    elif isinstance(value, list) and len(value) >= 3:
                        resources[key] = ResourceData(value[0], value[1], value[2])
        
        return cls(
            version=data.get("v", data.get("version", SCHEMA_VERSION)),
            player_id=data.get("player", data.get("player_id", 1)),
            timestamp=data.get("time", data.get("timestamp", 0.0)),
            game_time=data.get("game_time", data.get("time", 0.0)),
            game_phase=data.get("phase", data.get("game_phase", "early")),
            resources=resources,
            squads=[SquadData.from_dict(squad) for squad in data.get("squads", [])],
            capture_points=[CapturePointData.from_dict(cp) for cp in data.get("cps", data.get("capture_points", []))],
            visible_enemies=[EnemyData.from_dict(enemy) for enemy in data.get("enemies", data.get("visible_enemies", []))],
            tech_tree=TechTreeData.from_dict(data.get("tech", data.get("tech_tree", {}))),
            build_queue=[BuildQueueItem.from_dict(item) for item in data.get("queue", data.get("build_queue", []))],
            population=PopulationData.from_list(data.get("pop", data.get("population", [0, 100]))),
            faction=data.get("faction", "allies")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "GameState":
        """Create GameState from JSON string."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")


# ============================================
# Command Schema
# ============================================

class CommandType(Enum):
    """Supported command types."""
    BUILD = "BUILD"
    CAPTURE = "CAPTURE"
    ATTACK_MOVE = "ATTACK_MOVE"
    SET_POSTURE = "SET_POSTURE"
    PRODUCE = "PRODUCE"
    RETREAT = "RETREAT"
    STOP = "STOP"
    HOLD = "HOLD"
    PING = "PING"  # For testing
    PONG = "PONG"  # For testing


@dataclass
class Command:
    """Base command class."""
    command: str = "UNKNOWN"
    timestamp: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Command":
        return cls(
            command=data.get("command", "UNKNOWN"),
            timestamp=data.get("timestamp", 0.0)
        )


@dataclass
class BuildCommand(Command):
    """Build a structure."""
    engineer_id: int = 0
    building_type: str = ""
    position: Position = field(default_factory=Position)
    
    def __post_init__(self):
        self.command = CommandType.BUILD.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "engineer_id": self.engineer_id,
            "building_type": self.building_type,
            "position": self.position.to_list()
        }


@dataclass
class CaptureCommand(Command):
    """Capture a point."""
    squad_id: int = 0
    point_id: int = 0
    
    def __post_init__(self):
        self.command = CommandType.CAPTURE.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "squad_id": self.squad_id,
            "point_id": self.point_id
        }


@dataclass
class AttackMoveCommand(Command):
    """Attack move to position."""
    squad_id: int = 0
    position: Position = field(default_factory=Position)
    
    def __post_init__(self):
        self.command = CommandType.ATTACK_MOVE.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "squad_id": self.squad_id,
            "position": self.position.to_list()
        }


@dataclass
class SetPostureCommand(Command):
    """Set squad posture."""
    squad_id: int = 0
    posture: str = "defensive"
    
    def __post_init__(self):
        self.command = CommandType.SET_POSTURE.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "squad_id": self.squad_id,
            "posture": self.posture
        }


@dataclass
class ProduceCommand(Command):
    """Produce a unit."""
    building_id: int = 0
    unit_type: str = ""
    
    def __post_init__(self):
        self.command = CommandType.PRODUCE.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "building_id": self.building_id,
            "unit_type": self.unit_type
        }


@dataclass
class RetreatCommand(Command):
    """Retreat a squad."""
    squad_id: int = 0
    
    def __post_init__(self):
        self.command = CommandType.RETREAT.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "squad_id": self.squad_id
        }


@dataclass
class StopCommand(Command):
    """Stop a squad."""
    squad_id: int = 0
    
    def __post_init__(self):
        self.command = CommandType.STOP.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "squad_id": self.squad_id
        }


@dataclass
class HoldCommand(Command):
    """Hold position."""
    squad_id: int = 0
    
    def __post_init__(self):
        self.command = CommandType.HOLD.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "squad_id": self.squad_id
        }


# Command factory for creating commands from dictionaries
def create_command(data: Dict[str, Any]) -> Command:
    """Create appropriate command object from dictionary."""
    command_type = data.get("command", "UNKNOWN")
    timestamp = data.get("timestamp", 0.0)
    
    try:
        cmd_type = CommandType(command_type)
    except ValueError:
        # Unknown command type, return base command
        return Command(command=command_type, timestamp=timestamp)
    
    switch = {
        CommandType.BUILD: lambda d: BuildCommand(
            timestamp=d.get("timestamp", 0.0),
            engineer_id=d.get("engineer_id", 0),
            building_type=d.get("building_type", ""),
            position=Position.from_list(d.get("position", [0, 0, 0]))
        ),
        CommandType.CAPTURE: lambda d: CaptureCommand(
            timestamp=d.get("timestamp", 0.0),
            squad_id=d.get("squad_id", 0),
            point_id=d.get("point_id", 0)
        ),
        CommandType.ATTACK_MOVE: lambda d: AttackMoveCommand(
            timestamp=d.get("timestamp", 0.0),
            squad_id=d.get("squad_id", 0),
            position=Position.from_list(d.get("position", [0, 0, 0]))
        ),
        CommandType.SET_POSTURE: lambda d: SetPostureCommand(
            timestamp=d.get("timestamp", 0.0),
            squad_id=d.get("squad_id", 0),
            posture=d.get("posture", "defensive")
        ),
        CommandType.PRODUCE: lambda d: ProduceCommand(
            timestamp=d.get("timestamp", 0.0),
            building_id=d.get("building_id", 0),
            unit_type=d.get("unit_type", "")
        ),
        CommandType.RETREAT: lambda d: RetreatCommand(
            timestamp=d.get("timestamp", 0.0),
            squad_id=d.get("squad_id", 0)
        ),
        CommandType.STOP: lambda d: StopCommand(
            timestamp=d.get("timestamp", 0.0),
            squad_id=d.get("squad_id", 0)
        ),
        CommandType.HOLD: lambda d: HoldCommand(
            timestamp=d.get("timestamp", 0.0),
            squad_id=d.get("squad_id", 0)
        ),
        CommandType.PING: lambda d: Command(command=CommandType.PING.value, timestamp=d.get("timestamp", 0.0)),
        CommandType.PONG: lambda d: Command(command=CommandType.PONG.value, timestamp=d.get("timestamp", 0.0)),
    }
    
    # Get the command creator function, default to base Command if not found
    creator = switch.get(cmd_type, lambda d: Command(command=command_type, timestamp=d.get("timestamp", 0.0)))
    return creator(data)


# ============================================
# Intent Schema (for Mistral responses)
# ============================================

class IntentType(Enum):
    """Types of AI intents from Mistral."""
    BUILD = "BUILD"
    TECH = "TECH"
    PRODUCE = "PRODUCE"
    ATTACK = "ATTACK"
    DEFEND = "DEFEND"
    RETREAT = "RETREAT"
    CAPTURE = "CAPTURE"
    EXPAND = "EXPAND"
    REINFORCE = "REINFORCE"
    FALLBACK = "FALLBACK"


@dataclass
class Intent:
    """Base intent class for Mistral AI responses."""
    intent: str
    confidence: float = 1.0
    reasoning: str = ""
    priority: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "priority": self.priority
        }


@dataclass
class BuildIntent(Intent):
    """Intent to build a structure."""
    intent: str = IntentType.BUILD.value
    building_type: str = ""
    confidence: float = 1.0
    reasoning: str = ""
    priority: int = 1
    position: Optional[Position] = None
    engineer_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "building_type": self.building_type,
            "position": self.position.to_list() if self.position else None,
            "engineer_id": self.engineer_id
        })
        return result


@dataclass
class TechIntent(Intent):
    """Intent to research tech."""
    intent: str = IntentType.TECH.value
    tech_name: str = ""
    confidence: float = 1.0
    reasoning: str = ""
    priority: int = 1
    building_id: Optional[int] = None


@dataclass
class ProduceIntent(Intent):
    """Intent to produce a unit."""
    intent: str = IntentType.PRODUCE.value
    unit_type: str = ""
    confidence: float = 1.0
    reasoning: str = ""
    priority: int = 1
    building_id: Optional[int] = None
    count: int = 1


@dataclass
class StrategicPlan:
    """Complete strategic plan from Mistral."""
    version: str = "1.0"
    timestamp: float = 0.0
    game_time: float = 0.0
    intentions: List[Intent] = field(default_factory=list)
    reasoning: str = ""
    confidence: float = 1.0
    next_decision_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "game_time": self.game_time,
            "intentions": [intent.to_dict() for intent in self.intentions],
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "next_decision_time": self.next_decision_time
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategicPlan":
        return cls(
            version=data.get("version", "1.0"),
            timestamp=data.get("timestamp", 0.0),
            game_time=data.get("game_time", 0.0),
            intentions=[],  # TODO: Implement intent parsing
            reasoning=data.get("reasoning", ""),
            confidence=data.get("confidence", 1.0),
            next_decision_time=data.get("next_decision_time", 0.0)
        )


# ============================================
# Validation Functions
# ============================================

def validate_game_state(state: GameState) -> bool:
    """Validate a game state object."""
    if state.player_id < 1:
        return False
    
    if state.timestamp <= 0:
        return False
    
    # Validate resources
    for resource_type in ["manpower", "fuel", "munitions"]:
        if resource_type in state.resources:
            resource = state.resources[resource_type]
            if resource.current < 0 or resource.max < 0:
                return False
    
    # Validate squads
    for squad in state.squads:
        if squad.id <= 0 or squad.health < 0:
            return False
    
    return True


def validate_command(command: Dict[str, Any]) -> bool:
    """Validate a command dictionary."""
    if "command" not in command:
        return False
    
    command_type = command["command"]
    
    # Check required fields for each command type
    required_fields = {
        "BUILD": ["engineer_id", "building_type", "position"],
        "CAPTURE": ["squad_id", "point_id"],
        "ATTACK_MOVE": ["squad_id", "position"],
        "SET_POSTURE": ["squad_id", "posture"],
        "PRODUCE": ["building_id", "unit_type"],
        "RETREAT": ["squad_id"],
        "STOP": ["squad_id"],
        "HOLD": ["squad_id"]
    }
    
    if command_type in required_fields:
        for field in required_fields[command_type]:
            if field not in command:
                return False
    
    return True


if __name__ == "__main__":
    # Test schema functionality
    print("Testing Game State Schema...")
    
    # Create a test game state
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
    
    # Test serialization
    json_data = state.to_json()
    print(f"Serialized state: {len(json_data)} bytes")
    
    # Test deserialization
    parsed_state = GameState.from_json(json_data)
    print(f"Parsed state: player {parsed_state.player_id}, {len(parsed_state.squads)} squads")
    
    # Test validation
    assert validate_game_state(state)
    print("[OK] Game state validation passed")
    
    # Test command creation
    build_cmd = BuildCommand(engineer_id=1, building_type="barracks", position=Position(100, 200, 0))
    cmd_dict = build_cmd.to_dict()
    print(f"Build command: {cmd_dict}")
    
    assert validate_command(cmd_dict)
    print("[OK] Command validation passed")
    
    print("Schema tests completed successfully!")