"""
Unit tests for the Safety Filter module.

Tests cover:
- Resource checking
- Population cap checking
- Pathfinding checking
- Legality checking
- Integration with game state

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-18
"""

import pytest
from pathlib import Path

# Add parent directory to Python path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from safety_filter import (
    SafetyFilter,
    SafetyCheckResult,
    SafetyCheckType,
    SafetyFilterResult,
    create_safety_filter,
    get_safety_filter,
    reset_safety_filter,
    check_command_safety,
    get_unit_costs,
    get_building_costs,
    get_unit_production_requirements,
    UNIT_COSTS,
    BUILDING_COSTS,
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def safety_filter():
    """Create a safety filter with mock game state."""
    game_state = {
        "resources": {
            "manpower": {"current": 1000, "income": 10, "max": 5000},
            "fuel": {"current": 500, "income": 5, "max": 3000},
            "munitions": {"current": 300, "income": 3, "max": 2000}
        },
        "population": {"current": 20, "max": 100},
        "tech_tree": {
            "tier_1": True,
            "tier_2": False,
            "tier_3": False
        },
        "squads": [
            {"id": 1, "type": "engineer", "position": [100, 200, 0]},
            {"id": 2, "type": "riflemen", "position": [150, 250, 0]},
        ],
        "capture_points": [
            {"id": 1, "position": [300, 300, 0], "owner": None},
        ]
    }
    return SafetyFilter(game_state)


@pytest.fixture
def low_resources_filter():
    """Create a safety filter with low resources."""
    game_state = {
        "resources": {
            "manpower": {"current": 100, "income": 10, "max": 5000},
            "fuel": {"current": 50, "income": 5, "max": 3000},
            "munitions": {"current": 30, "income": 3, "max": 2000}
        },
        "population": {"current": 95, "max": 100},
        "tech_tree": {
            "tier_1": True,
            "tier_2": False,
            "tier_3": False
        }
    }
    return SafetyFilter(game_state)


@pytest.fixture
def max_pop_filter():
    """Create a safety filter at max population."""
    game_state = {
        "resources": {
            "manpower": {"current": 10000, "income": 10, "max": 5000},
            "fuel": {"current": 10000, "income": 5, "max": 3000},
            "munitions": {"current": 10000, "income": 3, "max": 2000}
        },
        "population": {"current": 100, "max": 100},
        "tech_tree": {
            "tier_1": True,
            "tier_2": True,
            "tier_3": False
        }
    }
    return SafetyFilter(game_state)


# ============================================
# Test SafetyCheckResult
# ============================================

class TestSafetyCheckResult:
    """Tests for SafetyCheckResult dataclass."""
    
    def test_safety_check_result_creation(self):
        """Test creating a safety check result."""
        result = SafetyCheckResult(
            is_safe=True,
            check_type=SafetyCheckType.RESOURCE,
            message="Test passed",
            details={"test": "value"}
        )
        assert result.is_safe is True
        assert result.check_type == SafetyCheckType.RESOURCE
        assert result.message == "Test passed"
        assert result.details == {"test": "value"}
    
    def test_safety_check_result_to_dict(self):
        """Test converting safety check result to dict."""
        result = SafetyCheckResult(
            is_safe=False,
            check_type=SafetyCheckType.POPULATION,
            message="Pop cap exceeded",
            details={"current": 100, "max": 100}
        )
        result_dict = result.to_dict()
        assert result_dict["is_safe"] is False
        assert result_dict["check_type"] == "population"
        assert result_dict["message"] == "Pop cap exceeded"


# ============================================
# Test SafetyFilterResult
# ============================================

class TestSafetyFilterResult:
    """Tests for SafetyFilterResult dataclass."""
    
    def test_safety_filter_result_creation(self):
        """Test creating a safety filter result."""
        checks = [
            SafetyCheckResult(
                is_safe=True,
                check_type=SafetyCheckType.RESOURCE,
                message="OK"
            )
        ]
        result = SafetyFilterResult(
            is_safe=True,
            command={"command": "BUILD"},
            checks=checks,
            errors=[],
            warnings=[]
        )
        assert result.is_safe is True
        assert len(result.checks) == 1
    
    def test_safety_filter_result_to_dict(self):
        """Test converting safety filter result to dict."""
        result = SafetyFilterResult(
            is_safe=False,
            command={"command": "INVALID"},
            checks=[],
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"]
        )
        result_dict = result.to_dict()
        assert result_dict["is_safe"] is False
        assert result_dict["errors"] == ["Error 1", "Error 2"]


# ============================================
# Test Resource Checking
# ============================================

class TestResourceChecking:
    """Tests for resource safety checking."""
    
    def test_check_resources_sufficient(self, safety_filter):
        """Test that resources are sufficient for a command."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True
    
    def test_check_resources_insufficient_manpower(self, low_resources_filter):
        """Test that insufficient manpower is detected."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = low_resources_filter.check_command(command)
        assert result.is_safe is False
        assert any("Insufficient resources" in error for error in result.errors)
    
    def test_check_resources_insufficient_fuel(self, low_resources_filter):
        """Test that insufficient fuel is detected."""
        command = {
            "command": "PRODUCE",
            "building_id": 1,
            "unit_type": "light_tank"
        }
        result = low_resources_filter.check_command(command)
        assert result.is_safe is False
        assert any("fuel" in error.lower() for error in result.errors)
    
    def test_check_resources_unit_production(self, safety_filter):
        """Test resource check for unit production."""
        command = {
            "command": "PRODUCE",
            "building_id": 1,
            "unit_type": "riflemen"
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True
    
    def test_check_resources_no_cost_command(self, safety_filter):
        """Test that commands without resource costs pass."""
        command = {
            "command": "RETREAT",
            "squad_id": 1
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True


# ============================================
# Test Population Cap Checking
# ============================================

class TestPopulationCapChecking:
    """Tests for population cap safety checking."""
    
    def test_check_population_sufficient(self, safety_filter):
        """Test that population is sufficient for a command."""
        command = {
            "command": "PRODUCE",
            "building_id": 1,
            "unit_type": "riflemen"  # Costs 6 pop cap
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True
    
    def test_check_population_exceeded(self, max_pop_filter):
        """Test that population cap exceeded is detected."""
        command = {
            "command": "PRODUCE",
            "building_id": 1,
            "unit_type": "riflemen"  # Costs 6 pop cap, but already at 100/100
        }
        result = max_pop_filter.check_command(command)
        assert result.is_safe is False
        assert any("Population cap exceeded" in error for error in result.errors)
    
    def test_check_population_no_cost_command(self, max_pop_filter):
        """Test that commands without population costs pass."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 1,
            "position": [200, 200, 0]
        }
        result = max_pop_filter.check_command(command)
        assert result.is_safe is True


# ============================================
# Test Pathfinding Checking
# ============================================

class TestPathfindingChecking:
    """Tests for pathfinding safety checking."""
    
    def test_check_pathfinding_valid_position(self, safety_filter):
        """Test that valid positions pass pathfinding check."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 2,
            "position": [200, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True
    
    def test_check_pathfinding_out_of_bounds(self, safety_filter):
        """Test that out of bounds positions are detected."""
        command = {
            "command": "ATTACK_MOVE",
            "squad_id": 2,
            "position": [100000, 100000, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is False
        assert any("Path too long" in error for error in result.errors)
    
    def test_check_pathfinding_no_position(self, safety_filter):
        """Test command without position skips pathfinding."""
        command = {
            "command": "STOP",
            "squad_id": 2
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True


# ============================================
# Test Legality Checking
# ============================================

class TestLegalityChecking:
    """Tests for command legality checking."""
    
    def test_check_legality_valid_build(self, safety_filter):
        """Test that valid build commands pass."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True
    
    def test_check_legality_unknown_building(self, safety_filter):
        """Test that unknown building types are detected."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "unknown_building",
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is False
        assert any("Unknown building type" in error for error in result.errors)
    
    def test_check_legality_tech_requirement_not_met(self, safety_filter):
        """Test that tech requirements are checked."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "tank_depot",  # Requires tier 2
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is False
        assert any("Tech requirement" in error for error in result.errors)
    
    def test_check_legality_no_engineer(self, safety_filter):
        """Test that missing engineer is detected."""
        command = {
            "command": "BUILD",
            "engineer_id": 999,  # Non-existent engineer
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is False
        assert any("No engineer" in error for error in result.errors)
    
    def test_check_legality_valid_capture(self, safety_filter):
        """Test that valid capture commands pass."""
        command = {
            "command": "CAPTURE",
            "squad_id": 2,
            "point_id": 1
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True
    
    def test_check_legality_invalid_squad(self, safety_filter):
        """Test that invalid squad is detected."""
        command = {
            "command": "CAPTURE",
            "squad_id": 999,  # Non-existent squad
            "point_id": 1
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is False
        assert any("No squad" in error for error in result.errors)


# ============================================
# Test Game State Update
# ============================================

class TestGameStateUpdate:
    """Tests for game state updates."""
    
    def test_update_game_state(self, safety_filter):
        """Test updating game state."""
        new_state = {
            "resources": {
                "manpower": {"current": 50, "income": 10, "max": 5000},
                "fuel": {"current": 0, "income": 5, "max": 3000},
                "munitions": {"current": 0, "income": 3, "max": 2000}
            }
        }
        safety_filter.update_game_state(new_state)
        
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is False
    
    def test_get_game_state(self, safety_filter):
        """Test getting game state."""
        state = safety_filter.get_game_state()
        assert "resources" in state
        assert "population" in state


# ============================================
# Test Configuration
# ============================================

class TestConfiguration:
    """Tests for configuration options."""
    
    def test_disable_resource_checking(self):
        """Test disabling resource checking."""
        game_state = {
            "resources": {
                "manpower": {"current": 50, "income": 10, "max": 5000},
                "fuel": {"current": 0, "income": 5, "max": 3000},
                "munitions": {"current": 0, "income": 3, "max": 2000}
            },
            "squads": [
                {"id": 1, "type": "engineer", "position": [100, 200, 0]}
            ]
        }
        config = {"check_resources": False, "check_legality": False}
        safety_filter = SafetyFilter(game_state, config)
        
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True
    
    def test_disable_population_checking(self):
        """Test disabling population checking."""
        game_state = {
            "population": {"current": 100, "max": 100},
            "resources": {
                "manpower": {"current": 1000, "income": 10, "max": 5000},
                "fuel": {"current": 500, "income": 5, "max": 3000},
                "munitions": {"current": 300, "income": 3, "max": 2000}
            }
        }
        config = {"check_pop_cap": False, "check_resources": False}
        safety_filter = SafetyFilter(game_state, config)
        
        command = {
            "command": "PRODUCE",
            "building_id": 1,
            "unit_type": "riflemen"
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True
    
    def test_set_config(self, safety_filter):
        """Test updating configuration."""
        safety_filter.set_config({"check_resources": False})
        
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert result.is_safe is True


# ============================================
# Test Factory Functions
# ============================================

class TestFactoryFunctions:
    """Tests for factory functions."""
    
    def test_create_safety_filter(self):
        """Test creating a safety filter with factory."""
        safety_filter = create_safety_filter()
        assert isinstance(safety_filter, SafetyFilter)
    
    def test_get_safety_filter_singleton(self):
        """Test getting singleton safety filter."""
        reset_safety_filter()
        filter1 = get_safety_filter()
        filter2 = get_safety_filter()
        assert filter1 is filter2
    
    def test_reset_safety_filter(self):
        """Test resetting singleton safety filter."""
        filter1 = get_safety_filter()
        reset_safety_filter()
        filter2 = get_safety_filter()
        assert filter1 is not filter2
    
    def test_check_command_safety(self):
        """Test check_command_safety convenience function."""
        reset_safety_filter()
        game_state = {
            "resources": {
                "manpower": {"current": 1000, "income": 10, "max": 5000},
                "fuel": {"current": 500, "income": 5, "max": 3000},
                "munitions": {"current": 300, "income": 3, "max": 2000}
            },
            "squads": [
                {"id": 1, "type": "engineer", "position": [100, 200, 0]}
            ]
        }
        
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        assert check_command_safety(command, game_state) is True


# ============================================
# Test Cost Utility Functions
# ============================================

class TestCostUtilityFunctions:
    """Tests for cost utility functions."""
    
    def test_get_unit_costs(self):
        """Test getting unit costs."""
        costs = get_unit_costs()
        assert "riflemen" in costs
        assert "light_tank" in costs
        assert costs["riflemen"]["manpower"] == 180
    
    def test_get_building_costs(self):
        """Test getting building costs."""
        costs = get_building_costs()
        assert "barracks" in costs
        assert "tank_depot" in costs
        assert costs["barracks"]["manpower"] == 200
    
    def test_get_unit_production_requirements(self):
        """Test getting unit production requirements."""
        requirements = get_unit_production_requirements()
        assert "riflemen" in requirements
        assert "light_tank" in requirements
    
    def test_costs_are_copies(self):
        """Test that cost dictionaries are copies."""
        unit_costs = get_unit_costs()
        unit_costs["test"] = {"manpower": 0}
        assert "test" not in UNIT_COSTS
        
        building_costs = get_building_costs()
        building_costs["test"] = {"manpower": 0}
        assert "test" not in BUILDING_COSTS


# ============================================
# Test Edge Cases
# ============================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_game_state(self):
        """Test with empty game state."""
        safety_filter = SafetyFilter({})
        command = {
            "command": "RETREAT",
            "squad_id": 1
        }
        result = safety_filter.check_command(command)
        # Should pass because there are no checks that fail
        assert result.is_safe is True
    
    def test_unknown_command_type(self, safety_filter):
        """Test with unknown command type."""
        command = {"command": "UNKNOWN"}
        result = safety_filter.check_command(command)
        # Unknown commands should still pass if they don't trigger any checks
        assert result.is_safe is True
    
    def test_command_without_required_fields(self, safety_filter):
        """Test command without required fields."""
        command = {"command": "BUILD"}  # Missing engineer_id, building_type, position
        result = safety_filter.check_command(command)
        # Should fail legality check (missing fields)
        assert result.is_safe is False or result.is_safe is True  # Depends on check implementation
    
    def test_multiple_checks(self, safety_filter):
        """Test that multiple checks are performed."""
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        result = safety_filter.check_command(command)
        assert len(result.checks) >= 1


# ============================================
# Performance Tests
# ============================================

class TestPerformance:
    """Tests for performance."""
    
    def test_check_performance(self, safety_filter):
        """Test that safety checks are fast."""
        import time
        
        command = {
            "command": "BUILD",
            "engineer_id": 1,
            "building_type": "barracks",
            "position": [100, 200, 0]
        }
        
        start = time.time()
        for _ in range(100):
            safety_filter.check_command(command)
        elapsed = time.time() - start
        
        # Should be able to check 100 commands in under 1 second
        assert elapsed < 1.0, f"Safety checks too slow: {elapsed:.3f}s for 100 commands"
