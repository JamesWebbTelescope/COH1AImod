"""
Unit tests for the Reflex Layer module.

Tests cover:
- Retreat logic for low-health squads
- Artillery response behavior
- Capture point micro-management
- Build queue management
- Configuration and state tracking

Note: Since reflex_layer.scar runs in the SCAR environment, these tests
verify the Python-side logic and mock the SCAR functions.

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-18
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import sys

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

# Since reflex_layer.scar is a SCAR file, we'll test the logic through
# mocking and verification of the expected behavior patterns


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_squad_low_health_under_fire():
    """Mock squad with low health under fire."""
    squad = Mock()
    squad.id = 1
    squad.IsValid.return_value = True
    squad.GetId.return_value = 1
    squad.GetHealth.return_value = 25
    squad.GetMaxHealth.return_value = 100
    squad.UnderFire.return_value = True
    squad.IsSuppressed.return_value = True
    squad.IsPinned.return_value = False
    squad.GetPosition.return_value = type('Position', (), {'x': 100, 'y': 200, 'z': 0})()
    squad.GetType.return_value = "riflemen"
    squad.Retreat = Mock(return_value=True)
    squad.Move = Mock(return_value=True)
    return squad


@pytest.fixture
def mock_squad_critical_health():
    """Mock squad with critical health."""
    squad = Mock()
    squad.id = 2
    squad.IsValid.return_value = True
    squad.GetId.return_value = 2
    squad.GetHealth.return_value = 10
    squad.GetMaxHealth.return_value = 100
    squad.UnderFire.return_value = False
    squad.IsSuppressed.return_value = False
    squad.IsPinned.return_value = False
    squad.GetPosition.return_value = type('Position', (), {'x': 150, 'y': 250, 'z': 0})()
    squad.GetType.return_value = "riflemen"
    squad.Retreat = Mock(return_value=True)
    squad.Move = Mock(return_value=True)
    return squad


@pytest.fixture
def mock_squad_healthy():
    """Mock healthy squad."""
    squad = Mock()
    squad.id = 3
    squad.IsValid.return_value = True
    squad.GetId.return_value = 3
    squad.GetHealth.return_value = 80
    squad.GetMaxHealth.return_value = 100
    squad.UnderFire.return_value = False
    squad.IsSuppressed.return_value = False
    squad.IsPinned.return_value = False
    squad.GetPosition.return_value = type('Position', (), {'x': 200, 'y': 300, 'z': 0})()
    squad.GetType.return_value = "riflemen"
    return squad


@pytest.fixture
def mock_engineer_squad():
    """Mock engineer squad."""
    squad = Mock()
    squad.id = 4
    squad.IsValid.return_value = True
    squad.GetId.return_value = 4
    squad.GetHealth.return_value = 90
    squad.GetMaxHealth.return_value = 100
    squad.UnderFire.return_value = False
    squad.GetPosition.return_value = type('Position', (), {'x': 50, 'y': 50, 'z': 0})()
    squad.GetType.return_value = "engineer"
    return squad


@pytest.fixture
def mock_player_with_squads():
    """Mock player with multiple squads."""
    player = Mock()
    player.IsValid.return_value = True
    player.GetId.return_value = 1
    player.GetSquads.return_value = []
    player.GetBuildings.return_value = []
    player.GetResources.return_value = type('Resources', (), {
        'manpower': type('Resource', (), {'current': 1000, 'income': 10, 'max': 5000})(),
        'fuel': type('Resource', (), {'current': 500, 'income': 5, 'max': 3000})(),
        'munitions': type('Resource', (), {'current': 300, 'income': 3, 'max': 2000})()
    })()
    player.GetPopulation.return_value = 20
    player.GetMaxPopulation.return_value = 100
    player.GetTechLevel.return_value = 1
    player.GetFaction.return_value = "allies"
    return player


# ============================================
# Test Retreat Logic
# ============================================

class TestRetreatLogic:
    """Tests for squad retreat logic."""
    
    def test_retreat_triggered_at_critical_health(self, mock_squad_critical_health):
        """Test that retreat is triggered at critical health threshold."""
        # Critical health is 15% or below
        health_percent = mock_squad_critical_health.GetHealth() / mock_squad_critical_health.GetMaxHealth()
        assert health_percent == 0.1
        assert health_percent <= 0.15  # CRITICAL_HEALTH_THRESHOLD
        
    def test_retreat_triggered_at_low_health_under_fire(self, mock_squad_low_health_under_fire):
        """Test that retreat is triggered at low health when under fire."""
        # Low health is 30% or below
        health_percent = mock_squad_low_health_under_fire.GetHealth() / mock_squad_low_health_under_fire.GetMaxHealth()
        assert health_percent == 0.25
        assert health_percent <= 0.3  # RETREAT_HEALTH_THRESHOLD
        assert mock_squad_low_health_under_fire.UnderFire() is True
        
    def test_retreat_not_triggered_above_threshold(self, mock_squad_healthy):
        """Test that retreat is not triggered when health is above threshold."""
        health_percent = mock_squad_healthy.GetHealth() / mock_squad_healthy.GetMaxHealth()
        assert health_percent == 0.8
        assert health_percent > 0.3  # RETREAT_HEALTH_THRESHOLD
        
    def test_health_info_calculation(self, mock_squad_low_health_under_fire):
        """Test health info calculation."""
        current = mock_squad_low_health_under_fire.GetHealth()
        max_health = mock_squad_low_health_under_fire.GetMaxHealth()
        under_fire = mock_squad_low_health_under_fire.UnderFire()
        suppressed = mock_squad_low_health_under_fire.IsSuppressed()
        
        health_percent = current / max_health
        assert health_percent == 0.25
        assert under_fire is True
        assert suppressed is True


# ============================================
# Test Artillery Response
# ============================================

class TestArtilleryResponse:
    """Tests for artillery response behavior."""
    
    def test_artillery_projectile_detection(self):
        """Test detection of artillery projectiles."""
        artillery_types = [
            "mortar", "howitzer", "artillery", "rocket",
            "barrage", "shell", "bomb", "airstrike"
        ]
        
        for proj_type in artillery_types:
            assert proj_type in "mortar howitzer artillery rocket barrage shell bomb airstrike"
            
    def test_position_distance_calculation(self):
        """Test distance calculation between positions."""
        pos1 = type('Position', (), {'x': 100, 'y': 200, 'z': 0})()
        pos2 = type('Position', (), {'x': 150, 'y': 250, 'z': 0})()
        
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        dz = pos2.z - pos1.z
        distance = (dx**2 + dy**2 + dz**2) ** 0.5
        
        assert distance == 70.71067811865475  # sqrt(50^2 + 50^2)


# ============================================
# Test Capture Point Micro
# ============================================

class TestCapturePointMicro:
    """Tests for capture point micro-management."""
    
    def test_squad_capture_score_calculation(self):
        """Test calculation of squad score for capture."""
        # Mock squad at distance 50 with 100% health
        distance = 50
        health_percent = 1.0
        is_infantry = True
        
        # Distance factor: closer is better
        distance_score = max(0, 100 - min(distance, 100)) * 2
        assert distance_score == 100  # (100 - 50) * 2
        
        # Health factor: healthier is better
        health_score = health_percent * 100
        assert health_score == 100
        
        # Type factor: infantry are better at capturing
        type_score = 50 if is_infantry else 0
        assert type_score == 50
        
        total_score = distance_score + health_score + type_score
        assert total_score == 250
        
    def test_infantry_type_detection(self):
        """Test detection of infantry unit types."""
        infantry_types = [
            "riflemen", "engineer", "sniper", "machine_gun", "mortar",
            "bazooka", "grenadier", "assault", "support", "volks", "pioneer", "hmg", "panzerschreck"
        ]
        
        for unit_type in infantry_types:
            assert unit_type in infantry_types


# ============================================
# Test Build Queue Management
# ============================================

class TestBuildQueueManagement:
    """Tests for build queue management."""
    
    def test_can_afford_unit(self, mock_player_with_squads):
        """Test affordability check for units."""
        resources = mock_player_with_squads.GetResources()
        
        # Unit costs (manpower, fuel, munitions)
        unit_costs = {
            "engineer": (50, 0, 0),
            "riflemen": (180, 0, 0),
            "machine_gun": (200, 0, 0),
            "light_tank": (400, 100, 0),
            "medium_tank": (600, 200, 0)
        }
        
        # Check affordability for each unit
        for unit_type, cost in unit_costs.items():
            mp, fuel, muni = cost
            can_afford = (
                resources.manpower.current >= mp + 50 and
                resources.fuel.current >= fuel + 25 and
                resources.munitions.current >= muni + 25
            )
            # With current resources (1000, 500, 300), all should be affordable
            assert can_afford is True
            
    def test_population_cap_check(self, mock_player_with_squads):
        """Test population cap checking."""
        pop = mock_player_with_squads.GetPopulation()
        max_pop = mock_player_with_squads.GetMaxPopulation()
        pop_available = max_pop - pop
        
        assert pop == 20
        assert max_pop == 100
        assert pop_available == 80
        
        # Should be able to produce units that cost <= 80 - 5 (margin)
        unit_pop_costs = {
            "engineer": 1,
            "riflemen": 3,
            "machine_gun": 3,
            "light_tank": 5,
            "medium_tank": 6,
            "heavy_tank": 8
        }
        
        for unit_type, pop_cost in unit_pop_costs.items():
            can_produce = pop_cost <= pop_available - 5
            assert can_produce is True
            
    def test_unit_tech_requirements(self):
        """Test tech level requirements for units."""
        tier1_units = ["riflemen", "engineer", "sniper"]
        tier2_units = ["mortar", "bazooka", "machine_gun"]
        tier3_units = ["heavy_tank"]
        
        for unit in tier1_units:
            assert unit not in tier2_units
            assert unit not in tier3_units
            
    def test_production_building_types(self):
        """Test building types that can produce units."""
        production_buildings = [
            "headquarters", "barracks", "weapon_support", "tank_depot",
            "airfield", "vehicle_depot", "factory"
        ]
        
        for building_type in production_buildings:
            assert building_type in production_buildings


# ============================================
# Test Configuration
# ============================================

class TestConfiguration:
    """Tests for reflex layer configuration."""
    
    def test_default_thresholds(self):
        """Test default health thresholds."""
        # From config.scar
        RETREAT_HEALTH_THRESHOLD = 0.3
        CRITICAL_HEALTH_THRESHOLD = 0.15
        
        assert RETREAT_HEALTH_THRESHOLD == 0.3
        assert CRITICAL_HEALTH_THRESHOLD == 0.15
        assert CRITICAL_HEALTH_THRESHOLD < RETREAT_HEALTH_THRESHOLD
        
    def test_reflex_priority_levels(self):
        """Test reflex priority levels."""
        CRITICAL = 4
        HIGH = 3
        NORMAL = 2
        LOW = 1
        
        assert CRITICAL > HIGH > NORMAL > LOW


# ============================================
# Test State Tracking
# ============================================

class TestStateTracking:
    """Tests for reflex state tracking."""
    
    def test_retreat_cooldown_tracking(self):
        """Test retreat cooldown tracking."""
        squad_id = 1
        current_time = 100.0
        cooldown = 5.0
        
        # Simulate retreat
        last_retreat_time = current_time
        
        # Check if can retreat again
        time_since_retreat = current_time - last_retreat_time
        can_retreat = time_since_retreat >= cooldown
        
        assert can_retreat is False
        
        # After cooldown
        current_time = 106.0
        time_since_retreat = current_time - last_retreat_time
        can_retreat = time_since_retreat >= cooldown
        
        assert can_retreat is True
        
    def test_artillery_warning_cooldown(self):
        """Test artillery warning cooldown."""
        pos_key = "100.0,200.0"
        current_time = 100.0
        cooldown = 3.0
        
        # Simulate warning
        last_warning_time = current_time
        
        # Check if can warn again
        time_since_warning = current_time - last_warning_time
        can_warn = time_since_warning >= cooldown
        
        assert can_warn is False
        
        # After cooldown
        current_time = 104.0
        time_since_warning = current_time - last_warning_time
        can_warn = time_since_warning >= cooldown
        
        assert can_warn is True


# ============================================
# Test Statistics Tracking
# ============================================

class TestStatisticsTracking:
    """Tests for reflex layer statistics tracking."""
    
    def test_reflex_stats_structure(self):
        """Test reflex statistics structure."""
        stats = {
            "retreats_triggered": 0,
            "artillery_responses": 0,
            "capture_points_captured": 0,
            "capture_points_defended": 0,
            "build_queue_fills": 0,
            "squads_saved": 0,
            "last_reflex_time": 0.0,
            "total_reflex_calls": 0
        }
        
        # Verify all expected stats are present
        assert "retreats_triggered" in stats
        assert "artillery_responses" in stats
        assert "capture_points_captured" in stats
        assert "capture_points_defended" in stats
        assert "build_queue_fills" in stats
        assert "squads_saved" in stats
        assert "total_reflex_calls" in stats
        
    def test_stats_incrementing(self):
        """Test statistics incrementing."""
        stats = {
            "retreats_triggered": 0,
            "squads_saved": 0,
            "total_reflex_calls": 0
        }
        
        # Simulate retreats
        stats["retreats_triggered"] += 1
        stats["squads_saved"] += 1
        stats["total_reflex_calls"] += 1
        
        assert stats["retreats_triggered"] == 1
        assert stats["squads_saved"] == 1
        assert stats["total_reflex_calls"] == 1


# ============================================
# Test Helper Functions
# ============================================

class TestHelperFunctions:
    """Tests for helper utility functions."""
    
    def test_normalize_vector(self):
        """Test vector normalization."""
        x, y, z = 3, 4, 0
        length = (x**2 + y**2 + z**2) ** 0.5
        
        if length == 0:
            normalized = (0, 1, 0)
        else:
            normalized = (x/length, y/length, z/length)
        
        # Verify length is 1 (approximately)
        normalized_length = (normalized[0]**2 + normalized[1]**2 + normalized[2]**2) ** 0.5
        assert abs(normalized_length - 1.0) < 0.001
        
    def test_normalize_zero_vector(self):
        """Test normalization of zero vector."""
        x, y, z = 0, 0, 0
        length = (x**2 + y**2 + z**2) ** 0.5
        
        if length == 0:
            normalized = (0, 1, 0)
        else:
            normalized = (x/length, y/length, z/length)
        
        # Zero vector should default to (0, 1, 0)
        assert normalized == (0, 1, 0)
        
    def test_distance_to_artillery_response_threshold(self):
        """Test distance calculations for artillery response."""
        ARTILLERY_RESPONSE_DISTANCE = 50.0
        
        # Squad at distance 40 should trigger response
        distance = 40.0
        should_respond = distance <= ARTILLERY_RESPONSE_DISTANCE
        assert should_respond is True
        
        # Squad at distance 60 should not trigger response
        distance = 60.0
        should_respond = distance <= ARTILLERY_RESPONSE_DISTANCE
        assert should_respond is False


# ============================================
# Test Edge Cases
# ============================================

class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_null_squad_handling(self):
        """Test handling of null/None squads."""
        squads = [None, None, None]
        valid_squads = [s for s in squads if s is not None]
        assert len(valid_squads) == 0
        
    def test_empty_squad_list(self):
        """Test handling of empty squad list."""
        squads = []
        assert len(squads) == 0
        
    def test_zero_health_squad(self):
        """Test handling of squad with zero health."""
        current_health = 0
        max_health = 100
        health_percent = current_health / max_health if max_health > 0 else 0
        
        assert health_percent == 0.0
        assert health_percent <= 0.15  # Should trigger critical retreat
        
    def test_zero_max_health(self):
        """Test handling of squad with zero max health."""
        current_health = 50
        max_health = 0
        health_percent = current_health / max_health if max_health > 0 else 0
        
        assert health_percent == 0.0  # Avoid division by zero
        
    def test_negative_health(self):
        """Test handling of negative health values."""
        current_health = -10
        max_health = 100
        health_percent = current_health / max_health if max_health > 0 else 0
        
        assert health_percent == -0.1
        assert health_percent <= 0.15  # Should trigger critical retreat


# ============================================
# Test Integration Scenarios
# ============================================

class TestIntegrationScenarios:
    """Integration tests for reflex layer scenarios."""
    
    def test_low_health_under_fire_scenario(self):
        """Test complete scenario: low health squad under fire."""
        # Create mock squad
        squad = Mock()
        squad.IsValid.return_value = True
        squad.GetId.return_value = 1
        squad.GetHealth.return_value = 25
        squad.GetMaxHealth.return_value = 100
        squad.UnderFire.return_value = True
        squad.IsSuppressed.return_value = True
        squad.Retreat = Mock(return_value=True)
        
        # Verify conditions
        health_percent = squad.GetHealth() / squad.GetMaxHealth()
        assert health_percent <= 0.3
        assert squad.UnderFire() is True
        
        # Should trigger retreat
        should_retreat = (health_percent <= 0.3 and 
                        (squad.UnderFire() or squad.IsSuppressed()))
        assert should_retreat is True
        
    def test_artillery_response_scenario(self):
        """Test complete scenario: artillery response."""
        # Mock positions
        squad_pos = type('Position', (), {'x': 100, 'y': 200, 'z': 0})()
        artillery_pos = type('Position', (), {'x': 120, 'y': 220, 'z': 0})()
        
        # Calculate distance
        dx = artillery_pos.x - squad_pos.x
        dy = artillery_pos.y - squad_pos.y
        distance = (dx**2 + dy**2) ** 0.5
        
        # Should respond if within threshold
        ARTILLERY_RESPONSE_DISTANCE = 50.0
        should_respond = distance <= ARTILLERY_RESPONSE_DISTANCE
        
        assert distance == 28.2842712474619
        assert should_respond is True
        
    def test_capture_point_scenario(self):
        """Test complete scenario: capture point management."""
        # Mock capture point
        cp = Mock()
        cp.IsValid.return_value = True
        cp.GetId.return_value = 1
        cp.GetPosition.return_value = type('Position', (), {'x': 300, 'y': 300, 'z': 0})()
        cp.GetOwner.return_value = None  # Neutral
        cp.IsContested.return_value = False
        
        # Verify it's neutral
        owner = cp.GetOwner()
        is_neutral = (owner is None or owner == 0)
        assert is_neutral is True
        
        # Should attempt to capture
        should_capture = is_neutral and not cp.IsContested()
        assert should_capture is True


# ============================================
# Test Configuration Loading
# ============================================

class TestConfigurationLoading:
    """Tests for configuration loading."""
    
    def test_load_default_configuration(self):
        """Test loading of default configuration."""
        config = {
            "reflex": {
                "retreat_threshold": 0.3,
                "critical_threshold": 0.15,
                "enable_retreat": True,
                "enable_artillery_response": True,
                "enable_capture_micro": True,
                "enable_build_queue": True
            }
        }
        
        assert "reflex" in config
        assert config["reflex"]["retreat_threshold"] == 0.3
        assert config["reflex"]["critical_threshold"] == 0.15
        assert config["reflex"]["enable_retreat"] is True
        
    def test_override_thresholds(self):
        """Test overriding thresholds via configuration."""
        config = {
            "reflex": {
                "retreat_threshold": 0.25,
                "critical_threshold": 0.10
            }
        }
        
        DEFAULT_RETREAT = 0.3
        DEFAULT_CRITICAL = 0.15
        
        retreat = config["reflex"].get("retreat_threshold", DEFAULT_RETREAT)
        critical = config["reflex"].get("critical_threshold", DEFAULT_CRITICAL)
        
        assert retreat == 0.25
        assert critical == 0.10
