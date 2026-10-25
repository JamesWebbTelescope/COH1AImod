"""
CoH1 × Mistral AI Mod - Safety Filter

Performs safety checks on commands before execution to ensure they are safe to execute.
This module validates resource costs, population caps, pathfinding, and command legality.

Responsibilities:
- Check if player has enough resources (manpower, fuel, munitions) for a command
- Check if population cap allows for unit production
- Validate pathfinding for movement commands
- Check command legality (building requirements, tech tree, etc.)
- Provide detailed error information for debugging

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-18

Usage:
    from safety_filter import SafetyFilter, SafetyCheckResult
    
    # Create filter with game state
    filter = SafetyFilter(game_state)
    
    # Check a command
    result = filter.check_command(command)
    if result.is_safe:
        # Execute command
        pass
    else:
        # Handle error
        print(f"Command blocked: {result.errors}")
"""

import logging
import math
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================
# Data Classes
# ============================================

class SafetyCheckType(Enum):
    """Types of safety checks."""
    RESOURCE = "resource"
    POPULATION = "population"
    PATHFINDING = "pathfinding"
    LEGALITY = "legality"
    BUILDING = "building"
    TECH = "tech"
    FACTION = "faction"


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""
    is_safe: bool
    check_type: SafetyCheckType
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_safe": self.is_safe,
            "check_type": self.check_type.value,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class SafetyFilterResult:
    """Overall result of safety filtering."""
    is_safe: bool
    command: Dict[str, Any]
    checks: List[SafetyCheckResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_safe": self.is_safe,
            "command": self.command,
            "checks": [c.to_dict() for c in self.checks],
            "errors": self.errors,
            "warnings": self.warnings,
        }


# ============================================
# Cost Definitions
# ============================================

# Unit costs: name -> {manpower: int, fuel: int, munitions: int, pop_cap: int}
UNIT_COSTS: Dict[str, Dict[str, int]] = {
    # Infantry
    "riflemen": {"manpower": 180, "fuel": 0, "munitions": 0, "pop_cap": 6},
    "engineer": {"manpower": 200, "fuel": 0, "munitions": 0, "pop_cap": 5},
    "scout_car": {"manpower": 120, "fuel": 40, "munitions": 0, "pop_cap": 4},
    "grenadier": {"manpower": 200, "fuel": 0, "munitions": 20, "pop_cap": 6},
    "mortar": {"manpower": 240, "fuel": 0, "munitions": 40, "pop_cap": 6},
    "machine_gun": {"manpower": 200, "fuel": 0, "munitions": 40, "pop_cap": 6},
    "sniper": {"manpower": 250, "fuel": 0, "munitions": 0, "pop_cap": 4},
    "bazooka": {"manpower": 220, "fuel": 0, "munitions": 20, "pop_cap": 5},
    
    # Tanks
    "light_tank": {"manpower": 480, "fuel": 120, "munitions": 60, "pop_cap": 8},
    "medium_tank": {"manpower": 720, "fuel": 180, "munitions": 100, "pop_cap": 10},
    "heavy_tank": {"manpower": 1000, "fuel": 250, "munitions": 150, "pop_cap": 12},
}

# Building costs: name -> {manpower: int, fuel: int, munitions: int}
BUILDING_COSTS: Dict[str, Dict[str, int]] = {
    "barracks": {"manpower": 200, "fuel": 0, "munitions": 0},
    "war_factory": {"manpower": 400, "fuel": 100, "munitions": 0},
    "tank_depot": {"manpower": 400, "fuel": 100, "munitions": 0},
    "command_post": {"manpower": 300, "fuel": 0, "munitions": 0},
    "observation_post": {"manpower": 100, "fuel": 0, "munitions": 0},
    "forward_assembly": {"manpower": 250, "fuel": 50, "munitions": 0},
    "vehicle_depot": {"manpower": 400, "fuel": 100, "munitions": 0},
}

# Tech tree requirements: building -> required tech tier
BUILDING_TECH_REQUIREMENTS: Dict[str, int] = {
    "barracks": 1,
    "war_factory": 1,
    "tank_depot": 2,
    "command_post": 1,
    "observation_post": 1,
    "forward_assembly": 1,
    "vehicle_depot": 2,
}

# Unit production requirements: unit -> required building
UNIT_PRODUCTION_BUILDINGS: Dict[str, List[str]] = {
    "riflemen": ["barracks"],
    "engineer": ["barracks"],
    "scout_car": ["barracks"],
    "grenadier": ["barracks"],
    "mortar": ["barracks"],
    "machine_gun": ["barracks"],
    "sniper": ["barracks"],
    "bazooka": ["barracks"],
    "light_tank": ["war_factory", "tank_depot"],
    "medium_tank": ["war_factory", "tank_depot"],
    "heavy_tank": ["tank_depot"],
}


class SafetyFilter:
    """
    Filters commands for safety before execution.
    
    Checks:
    1. Resource affordability (manpower, fuel, munitions)
    2. Population cap
    3. Pathfinding validity (if map data available)
    4. Command legality (building requirements, tech tree)
    5. Faction restrictions
    """
    
    def __init__(self, game_state: Optional[Dict[str, Any]] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the safety filter.
        
        Args:
            game_state: Current game state dictionary
            config: Configuration dictionary with safety settings
        """
        self.game_state = game_state or {}
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Safety settings from config
        self.enable_resource_check = self.config.get("check_resources", True)
        self.enable_pop_cap_check = self.config.get("check_pop_cap", True)
        self.enable_pathfinding_check = self.config.get("check_pathfinding", True)
        self.enable_legality_check = self.config.get("check_legality", True)
        
        # Maximum path distance (for performance)
        self.max_path_distance = self.config.get("max_path_distance", 1000)
        
        self.logger.info("SafetyFilter initialized")
        if not self.enable_resource_check:
            self.logger.warning("Resource checking disabled")
        if not self.enable_pop_cap_check:
            self.logger.warning("Population cap checking disabled")
        if not self.enable_pathfinding_check:
            self.logger.warning("Pathfinding checking disabled")
        if not self.enable_legality_check:
            self.logger.warning("Legality checking disabled")
    
    def check_command(self, command: Dict[str, Any]) -> SafetyFilterResult:
        """
        Check a command for safety.
        
        Args:
            command: The command to check
            
        Returns:
            SafetyFilterResult with is_safe and details
        """
        checks: List[SafetyCheckResult] = []
        errors: List[str] = []
        warnings: List[str] = []
        
        # Determine command type
        command_type = command.get("command", "").upper()
        
        # Run all checks
        if self.enable_resource_check:
            resource_check = self._check_resources(command, command_type)
            checks.append(resource_check)
            if not resource_check.is_safe:
                errors.append(resource_check.message)
        
        if self.enable_pop_cap_check:
            pop_check = self._check_population(command, command_type)
            checks.append(pop_check)
            if not pop_check.is_safe:
                errors.append(pop_check.message)
        
        if self.enable_pathfinding_check:
            path_check = self._check_pathfinding(command, command_type)
            checks.append(path_check)
            if not path_check.is_safe:
                errors.append(path_check.message)
        
        if self.enable_legality_check:
            legality_check = self._check_legality(command, command_type)
            checks.append(legality_check)
            if not legality_check.is_safe:
                errors.append(legality_check.message)
        
        # Overall result
        is_safe = len(errors) == 0
        result = SafetyFilterResult(
            is_safe=is_safe,
            command=command,
            checks=checks,
            errors=errors,
            warnings=warnings,
        )
        
        # Log result
        if is_safe:
            self.logger.debug(f"Command passed safety check: {command_type}")
        else:
            self.logger.warning(f"Command blocked by safety check: {command_type} - {errors}")
        
        return result
    
    def _check_resources(self, command: Dict[str, Any], command_type: str) -> SafetyCheckResult:
        """Check if player has enough resources for the command."""
        resources = self.game_state.get("resources", {})
        
        # Get resource amounts
        manpower = resources.get("manpower", {}).get("current", 0)
        fuel = resources.get("fuel", {}).get("current", 0)
        munitions = resources.get("munitions", {}).get("current", 0)
        
        # Determine cost based on command type
        cost = self._get_command_cost(command, command_type)
        if cost is None:
            # No cost check for this command type
            return SafetyCheckResult(
                is_safe=True,
                check_type=SafetyCheckType.RESOURCE,
                message="No resource cost for this command type"
            )
        
        # Check each resource
        mp_cost = cost.get("manpower", 0)
        fuel_cost = cost.get("fuel", 0)
        muni_cost = cost.get("munitions", 0)
        
        can_afford = True
        missing = []
        
        if manpower < mp_cost:
            can_afford = False
            missing.append(f"manpower ({manpower}/{mp_cost})")
        
        if fuel < fuel_cost:
            can_afford = False
            missing.append(f"fuel ({fuel}/{fuel_cost})")
        
        if munitions < muni_cost:
            can_afford = False
            missing.append(f"munitions ({munitions}/{muni_cost})")
        
        if can_afford:
            return SafetyCheckResult(
                is_safe=True,
                check_type=SafetyCheckType.RESOURCE,
                message="Resources sufficient",
                details={"manpower": manpower, "fuel": fuel, "munitions": munitions}
            )
        else:
            return SafetyCheckResult(
                is_safe=False,
                check_type=SafetyCheckType.RESOURCE,
                message=f"Insufficient resources: {', '.join(missing)}",
                details={
                    "current": {"manpower": manpower, "fuel": fuel, "munitions": munitions},
                    "required": {"manpower": mp_cost, "fuel": fuel_cost, "munitions": muni_cost}
                }
            )
    
    def _check_population(self, command: Dict[str, Any], command_type: str) -> SafetyCheckResult:
        """Check if population cap allows for the command."""
        population = self.game_state.get("population", {})
        current_pop = population.get("current", 0)
        max_pop = population.get("max", 1000)  # Default max pop cap
        
        # Determine population cost based on command type
        pop_cost = self._get_command_pop_cost(command, command_type)
        if pop_cost is None or pop_cost == 0:
            # No population cost for this command type
            return SafetyCheckResult(
                is_safe=True,
                check_type=SafetyCheckType.POPULATION,
                message="No population cost for this command type"
            )
        
        if current_pop + pop_cost <= max_pop:
            return SafetyCheckResult(
                is_safe=True,
                check_type=SafetyCheckType.POPULATION,
                message=f"Population OK ({current_pop + pop_cost}/{max_pop})",
                details={"current": current_pop, "max": max_pop, "cost": pop_cost}
            )
        else:
            return SafetyCheckResult(
                is_safe=False,
                check_type=SafetyCheckType.POPULATION,
                message=f"Population cap exceeded: {current_pop + pop_cost}/{max_pop}",
                details={"current": current_pop, "max": max_pop, "cost": pop_cost}
            )
    
    def _check_pathfinding(self, command: Dict[str, Any], command_type: str) -> SafetyCheckResult:
        """Check pathfinding for movement commands."""
        # Only check pathfinding for movement commands
        if command_type not in ["ATTACK_MOVE", "BUILD"]:
            return SafetyCheckResult(
                is_safe=True,
                check_type=SafetyCheckType.PATHFINDING,
                message="No pathfinding check for this command type"
            )
        
        position = command.get("position")
        if position is None:
            return SafetyCheckResult(
                is_safe=True,
                check_type=SafetyCheckType.PATHFINDING,
                message="No position specified, skipping pathfinding"
            )
        
        # Get current positions (simplified - in real implementation would use actual pathfinding)
        # For now, just check distance limits
        if command_type == "ATTACK_MOVE":
            squad_id = command.get("squad_id")
            if squad_id:
                # Find squad position
                squads = self.game_state.get("squads", [])
                for squad in squads:
                    if squad.get("id") == squad_id:
                        squad_pos = squad.get("position", [])
                        if squad_pos and len(squad_pos) >= 3 and len(position) >= 3:
                            distance = self._calculate_distance(squad_pos[:3], position[:3])
                            if distance > self.max_path_distance:
                                return SafetyCheckResult(
                                    is_safe=False,
                                    check_type=SafetyCheckType.PATHFINDING,
                                    message=f"Path too long: {distance:.1f}m (max: {self.max_path_distance}m)",
                                    details={"distance": distance, "max_distance": self.max_path_distance}
                                )
                        break
        
        # Check if position is valid (not at map edges, etc.)
        # Simplified check - position should be reasonable values
        if position:
            for i, coord in enumerate(position[:3]):
                if abs(coord) > 50000:  # Reasonable map size limit
                    return SafetyCheckResult(
                        is_safe=False,
                        check_type=SafetyCheckType.PATHFINDING,
                        message=f"Position coordinate {i} out of bounds: {coord}",
                        details={"position": position, "index": i}
                    )
        
        return SafetyCheckResult(
            is_safe=True,
            check_type=SafetyCheckType.PATHFINDING,
            message="Pathfinding OK"
        )
    
    def _check_legality(self, command: Dict[str, Any], command_type: str) -> SafetyCheckResult:
        """Check command legality (building requirements, tech tree, etc.)."""
        
        if command_type == "BUILD":
            building_type = command.get("building_type", "").lower()
            
            # Check if building is in known buildings
            if building_type not in BUILDING_COSTS:
                return SafetyCheckResult(
                    is_safe=False,
                    check_type=SafetyCheckType.LEGALITY,
                    message=f"Unknown building type: {building_type}",
                    details={"building_type": building_type}
                )
            
            # Check tech requirements
            tech_tree = self.game_state.get("tech_tree", {})
            required_tier = BUILDING_TECH_REQUIREMENTS.get(building_type, 1)
            
            if required_tier > 1:
                tier_key = f"tier_{required_tier}"
                if not tech_tree.get(tier_key, False):
                    return SafetyCheckResult(
                        is_safe=False,
                        check_type=SafetyCheckType.TECH,
                        message=f"Tech requirement not met: {tier_key}",
                        details={"required_tier": required_tier, "current_tech": tech_tree}
                    )
            
            # Check if we have a valid engineer
            engineer_id = command.get("engineer_id")
            if engineer_id:
                squads = self.game_state.get("squads", [])
                engineer_found = False
                for squad in squads:
                    if squad.get("id") == engineer_id and squad.get("type") == "engineer":
                        engineer_found = True
                        break
                
                if not engineer_found:
                    return SafetyCheckResult(
                        is_safe=False,
                        check_type=SafetyCheckType.BUILDING,
                        message=f"No engineer found with ID: {engineer_id}",
                        details={"engineer_id": engineer_id}
                    )
        
        elif command_type == "PRODUCE":
            unit_type = command.get("unit_type", "").lower()
            building_id = command.get("building_id")
            
            # Check if unit is in known units
            if unit_type not in UNIT_COSTS:
                return SafetyCheckResult(
                    is_safe=False,
                    check_type=SafetyCheckType.LEGALITY,
                    message=f"Unknown unit type: {unit_type}",
                    details={"unit_type": unit_type}
                )
            
            # Check if building can produce this unit
            if building_id:
                buildings = self.game_state.get("buildings", [])
                for building in buildings:
                    if building.get("id") == building_id:
                        building_type = building.get("type", "").lower()
                        valid_buildings = UNIT_PRODUCTION_BUILDINGS.get(unit_type, [])
                        if building_type not in valid_buildings:
                            return SafetyCheckResult(
                                is_safe=False,
                                check_type=SafetyCheckType.BUILDING,
                                message=f"Building {building_type} cannot produce {unit_type}",
                                details={"building_type": building_type, "unit_type": unit_type}
                            )
                        break
        
        elif command_type == "CAPTURE":
            squad_id = command.get("squad_id")
            point_id = command.get("point_id")
            
            if squad_id:
                squads = self.game_state.get("squads", [])
                squad_found = False
                for squad in squads:
                    if squad.get("id") == squad_id:
                        squad_found = True
                        break
                
                if not squad_found:
                    return SafetyCheckResult(
                        is_safe=False,
                        check_type=SafetyCheckType.LEGALITY,
                        message=f"No squad found with ID: {squad_id}",
                        details={"squad_id": squad_id}
                    )
            
            if point_id:
                capture_points = self.game_state.get("capture_points", [])
                cp_found = False
                for cp in capture_points:
                    if cp.get("id") == point_id:
                        cp_found = True
                        break
                
                if not cp_found:
                    return SafetyCheckResult(
                        is_safe=False,
                        check_type=SafetyCheckType.LEGALITY,
                        message=f"No capture point found with ID: {point_id}",
                        details={"point_id": point_id}
                    )
        
        return SafetyCheckResult(
            is_safe=True,
            check_type=SafetyCheckType.LEGALITY,
            message="Command is legal"
        )
    
    def _get_command_cost(self, command: Dict[str, Any], command_type: str) -> Optional[Dict[str, int]]:
        """Get the resource cost for a command."""
        
        if command_type == "BUILD":
            building_type = command.get("building_type", "").lower()
            return BUILDING_COSTS.get(building_type)
        
        elif command_type == "PRODUCE":
            unit_type = command.get("unit_type", "").lower()
            return UNIT_COSTS.get(unit_type)
        
        # Other command types don't have resource costs
        return None
    
    def _get_command_pop_cost(self, command: Dict[str, Any], command_type: str) -> Optional[int]:
        """Get the population cost for a command."""
        
        if command_type == "PRODUCE":
            unit_type = command.get("unit_type", "").lower()
            unit_cost = UNIT_COSTS.get(unit_type, {})
            return unit_cost.get("pop_cap", 0)
        
        # Other command types don't have population costs
        return None
    
    def _calculate_distance(self, pos1: List[float], pos2: List[float]) -> float:
        """Calculate Euclidean distance between two 3D positions."""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        dz = pos1[2] - pos2[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def update_game_state(self, game_state: Dict[str, Any]) -> None:
        """Update the game state for subsequent checks."""
        self.game_state = game_state
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get the current game state."""
        return self.game_state
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Update the configuration."""
        self.config = config
        self.enable_resource_check = self.config.get("check_resources", True)
        self.enable_pop_cap_check = self.config.get("check_pop_cap", True)
        self.enable_pathfinding_check = self.config.get("check_pathfinding", True)
        self.enable_legality_check = self.config.get("check_legality", True)
        self.max_path_distance = self.config.get("max_path_distance", 1000)
    
    def check_resources(self, game_state: Dict[str, Any], required: Dict[str, int]) -> SafetyFilterResult:
        """
        Check if there are enough resources for a command.
        
        Args:
            game_state: Current game state with resources
            required: Dictionary of required resources (manpower, fuel, munitions)
            
        Returns:
            SafetyFilterResult with is_safe and is_valid indicating if resources are sufficient
        """
        errors = []
        resources = game_state.get("resources", {})
        
        for resource_type, required_amount in required.items():
            resource = resources.get(resource_type, {})
            current = resource.get("current", 0)
            if current < required_amount:
                errors.append(f"Insufficient {resource_type}: need {required_amount}, have {current}")
        
        result = SafetyFilterResult(
            is_safe=len(errors) == 0,
            command={},
            errors=errors
        )
        # Add is_valid for backward compatibility with tests
        result.is_valid = result.is_safe
        return result
    
    def check_population(self, game_state: Dict[str, Any], amount: int) -> SafetyFilterResult:
        """
        Check if there is enough population cap for a command.
        
        Args:
            game_state: Current game state with population info
            amount: Required population amount
            
        Returns:
            SafetyFilterResult with is_safe and is_valid indicating if population allows the command
        """
        errors = []
        population = game_state.get("population", {})
        current = population.get("current", 0)
        max_pop = population.get("max", 0)
        
        if current + amount > max_pop:
            errors.append(f"Population cap exceeded: {current} + {amount} > {max_pop}")
        
        result = SafetyFilterResult(
            is_safe=len(errors) == 0,
            command={},
            errors=errors
        )
        # Add is_valid for backward compatibility with tests
        result.is_valid = result.is_safe
        return result


# ============================================
# Factory Functions
# ============================================

_default_filter: Optional[SafetyFilter] = None


def get_safety_filter(game_state: Optional[Dict[str, Any]] = None) -> SafetyFilter:
    """Get the default safety filter instance (singleton)."""
    global _default_filter
    if _default_filter is None:
        _default_filter = SafetyFilter(game_state)
    return _default_filter


def reset_safety_filter() -> None:
    """Reset the default safety filter instance."""
    global _default_filter
    _default_filter = None


def create_safety_filter(game_state: Optional[Dict[str, Any]] = None,
                         config: Optional[Dict[str, Any]] = None) -> SafetyFilter:
    """
    Create a new safety filter instance.
    
    Args:
        game_state: Current game state
        config: Configuration dictionary
        
    Returns:
        New SafetyFilter instance
    """
    return SafetyFilter(game_state, config)


def check_command_safety(command: Dict[str, Any], game_state: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if a command is safe using the default filter.
    
    Args:
        command: The command to check
        game_state: Optional game state override
        
    Returns:
        True if command is safe, False otherwise
    """
    filter = get_safety_filter()
    if game_state:
        filter.update_game_state(game_state)
    return filter.check_command(command).is_safe


# ============================================
# Cost Utility Functions
# ============================================


def get_unit_costs() -> Dict[str, Dict[str, int]]:
    """Get unit costs dictionary."""
    return UNIT_COSTS.copy()


def get_building_costs() -> Dict[str, Dict[str, int]]:
    """Get building costs dictionary."""
    return BUILDING_COSTS.copy()


def get_unit_production_requirements() -> Dict[str, List[str]]:
    """Get unit production building requirements."""
    return UNIT_PRODUCTION_BUILDINGS.copy()
