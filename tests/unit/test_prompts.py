"""
Phase 3: System Prompt Engine Unit Tests

Tests for the prompts module.

Author: Generated for Phase 3 pytest integration
Version: 1.0.0
Date: 2026-11-21
"""

import os
import sys
import pytest
from pathlib import Path

# Add project root and python directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python"))


@pytest.fixture
def prompt_engine():
    """Create a default prompt engine for testing."""
    from prompts import create_prompt_engine, PromptConfig, Faction, Difficulty, GamePhase
    
    config = PromptConfig(
        faction=Faction.ALLIES,
        difficulty=Difficulty.NORMAL,
        game_phase=GamePhase.EARLY
    )
    engine = create_prompt_engine(config)
    yield engine


@pytest.fixture
def axes_prompt_engine():
    """Create a prompt engine for Axis faction."""
    from prompts import create_prompt_engine, PromptConfig, Faction, Difficulty, GamePhase
    
    config = PromptConfig(
        faction=Faction.AXIS,
        difficulty=Difficulty.HARD,
        game_phase=GamePhase.MID
    )
    engine = create_prompt_engine(config)
    yield engine


class TestFactionEnum:
    """Tests for Faction enumeration."""
    
    def test_faction_values(self):
        """Test faction enum values."""
        from prompts import Faction
        
        assert Faction.ALLIES.value == "allies"
        assert Faction.AXIS.value == "axis"
    
    def test_faction_iteration(self):
        """Test iterating over factions."""
        from prompts import Faction
        
        factions = list(Faction)
        assert len(factions) == 2
        assert Faction.ALLIES in factions
        assert Faction.AXIS in factions


class TestDifficultyEnum:
    """Tests for Difficulty enumeration."""
    
    def test_difficulty_values(self):
        """Test difficulty enum values."""
        from prompts import Difficulty
        
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.NORMAL.value == "normal"
        assert Difficulty.HARD.value == "hard"
        assert Difficulty.EXPERT.value == "expert"
    
    def test_difficulty_iteration(self):
        """Test iterating over difficulties."""
        from prompts import Difficulty
        
        difficulties = list(Difficulty)
        assert len(difficulties) == 4


class TestGamePhaseEnum:
    """Tests for GamePhase enumeration."""
    
    def test_game_phase_values(self):
        """Test game phase enum values."""
        from prompts import GamePhase
        
        assert GamePhase.EARLY.value == "early"
        assert GamePhase.MID.value == "mid"
        assert GamePhase.LATE.value == "late"
    
    def test_game_phase_iteration(self):
        """Test iterating over game phases."""
        from prompts import GamePhase
        
        phases = list(GamePhase)
        assert len(phases) == 3


class TestPromptConfig:
    """Tests for PromptConfig dataclass."""
    
    def test_default_config(self):
        """Test default prompt configuration."""
        from prompts import PromptConfig, Faction, Difficulty, GamePhase
        
        config = PromptConfig()
        
        assert config.faction == Faction.ALLIES
        assert config.difficulty == Difficulty.NORMAL
        assert config.game_phase == GamePhase.EARLY
        assert config.include_context == True
        assert config.max_history_states == 5
        assert config.max_tokens == 2048
        assert config.temperature == 0.7
    
    def test_custom_config(self):
        """Test custom prompt configuration."""
        from prompts import PromptConfig, Faction, Difficulty, GamePhase
        
        config = PromptConfig(
            faction=Faction.AXIS,
            difficulty=Difficulty.HARD,
            game_phase=GamePhase.LATE,
            include_context=False,
            max_history_states=10,
            max_tokens=1024,
            temperature=0.9
        )
        
        assert config.faction == Faction.AXIS
        assert config.difficulty == Difficulty.HARD
        assert config.game_phase == GamePhase.LATE
        assert config.include_context == False
        assert config.max_history_states == 10
        assert config.max_tokens == 1024
        assert config.temperature == 0.9


class TestPromptEngineInitialization:
    """Tests for PromptEngine initialization."""
    
    def test_default_initialization(self, prompt_engine):
        """Test default prompt engine initialization."""
        from prompts import PromptConfig, Faction, Difficulty, GamePhase
        
        config = prompt_engine.get_config()
        
        assert config.faction == Faction.ALLIES
        assert config.difficulty == Difficulty.NORMAL
        assert config.game_phase == GamePhase.EARLY
    
    def test_initialization_with_custom_config(self):
        """Test initialization with custom configuration."""
        from prompts import create_prompt_engine, PromptConfig, Faction, Difficulty, GamePhase
        
        config = PromptConfig(
            faction=Faction.AXIS,
            difficulty=Difficulty.EXPERT,
            game_phase=GamePhase.LATE
        )
        
        engine = create_prompt_engine(config)
        assert engine.get_config().faction == Faction.AXIS
        assert engine.get_config().difficulty == Difficulty.EXPERT
        assert engine.get_config().game_phase == GamePhase.LATE


class TestPromptGeneration:
    """Tests for prompt generation."""
    
    def test_system_prompt_generation(self, prompt_engine):
        """Test system prompt generation."""
        system_prompt = prompt_engine.generate_system_prompt()
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 1000  # Should be substantial
        assert "Company of Heroes" in system_prompt or "CoH1" in system_prompt
        assert "Faction Knowledge" in system_prompt
        assert "Unit Counter Matrix" in system_prompt
    
    def test_system_prompt_contains_faction_info(self, prompt_engine):
        """Test that system prompt contains faction information."""
        system_prompt = prompt_engine.generate_system_prompt()
        
        assert "Allies" in system_prompt or "allies" in system_prompt
    
    def test_system_prompt_contains_difficulty_info(self, prompt_engine):
        """Test that system prompt contains difficulty information."""
        system_prompt = prompt_engine.generate_system_prompt()
        
        assert "Normal" in system_prompt or "normal" in system_prompt
    
    def test_system_prompt_contains_phase_info(self, prompt_engine):
        """Test that system prompt contains game phase information."""
        system_prompt = prompt_engine.generate_system_prompt()
        
        assert "Early" in system_prompt or "early" in system_prompt
    
    def test_user_prompt_generation(self, prompt_engine):
        """Test user prompt generation."""
        game_state = {
            "game_time": 120.5,
            "phase": "early",
            "faction": "allies",
            "player_id": 1,
            "resources": {
                "manpower": {"current": 500, "income": 10, "max": 1000},
                "fuel": {"current": 300, "income": 5, "max": 800}
            },
            "squads": [{"id": 1, "type": "riflemen", "health": 0.8}],
            "cps": [{"id": 1, "owner": 1}],
            "tech": {"tier_1": True, "tier_2": False},
            "queue": [],
            "pop": [11, 100]
        }
        
        user_prompt = prompt_engine.generate_user_prompt(game_state)
        
        assert isinstance(user_prompt, str)
        assert len(user_prompt) > 100
        assert "120.5" in user_prompt or "120" in user_prompt
    
    def test_user_prompt_with_history(self, prompt_engine):
        """Test user prompt generation with history."""
        game_state = {
            "game_time": 120.5,
            "phase": "early",
            "faction": "allies",
            "player_id": 1,
            "resources": {"manpower": {"current": 500, "max": 1000}},
            "squads": [],
            "cps": [],
            "tech": {},
            "queue": [],
            "pop": [11, 100]
        }
        
        history = [
            {"game_time": 60.0, "resources": {"manpower": {"current": 300}}},
            {"game_time": 90.0, "resources": {"manpower": {"current": 400}}}
        ]
        
        user_prompt = prompt_engine.generate_user_prompt(game_state, history)
        
        assert isinstance(user_prompt, str)
        assert len(user_prompt) > 100


class TestPromptEngineConfiguration:
    """Tests for prompt engine configuration."""
    
    def test_set_faction(self, prompt_engine):
        """Test setting faction."""
        from prompts import Faction
        
        prompt_engine.set_faction(Faction.AXIS)
        assert prompt_engine.get_config().faction == Faction.AXIS
    
    def test_set_difficulty(self, prompt_engine):
        """Test setting difficulty."""
        from prompts import Difficulty
        
        prompt_engine.set_difficulty(Difficulty.HARD)
        assert prompt_engine.get_config().difficulty == Difficulty.HARD
    
    def test_set_game_phase(self, prompt_engine):
        """Test setting game phase."""
        from prompts import GamePhase
        
        prompt_engine.set_game_phase(GamePhase.LATE)
        assert prompt_engine.get_config().game_phase == GamePhase.LATE
    
    def test_set_config(self, prompt_engine):
        """Test setting complete configuration."""
        from prompts import PromptConfig, Faction, Difficulty, GamePhase
        
        new_config = PromptConfig(
            faction=Faction.AXIS,
            difficulty=Difficulty.EXPERT,
            game_phase=GamePhase.MID
        )
        
        prompt_engine.set_config(new_config)
        config = prompt_engine.get_config()
        
        assert config.faction == Faction.AXIS
        assert config.difficulty == Difficulty.EXPERT
        assert config.game_phase == GamePhase.MID


class TestFactionKnowledge:
    """Tests for faction-specific knowledge."""
    
    def test_allies_knowledge_exists(self):
        """Test that Allies faction knowledge exists."""
        from prompts import FACTION_KNOWLEDGE, Faction
        
        assert Faction.ALLIES in FACTION_KNOWLEDGE
        allies = FACTION_KNOWLEDGE[Faction.ALLIES]
        
        assert "name" in allies
        assert "strengths" in allies
        assert "weaknesses" in allies
        assert "recommended_openers" in allies
        assert "counter_strategy" in allies
    
    def test_axis_knowledge_exists(self):
        """Test that Axis faction knowledge exists."""
        from prompts import FACTION_KNOWLEDGE, Faction
        
        assert Faction.AXIS in FACTION_KNOWLEDGE
        axis = FACTION_KNOWLEDGE[Faction.AXIS]
        
        assert "name" in axis
        assert "strengths" in axis
        assert "weaknesses" in axis
        assert "recommended_openers" in axis
        assert "counter_strategy" in axis


class TestCounterUnits:
    """Tests for unit counter matrix."""
    
    def test_counter_units_exists(self):
        """Test that counter units dictionary exists."""
        from prompts import COUNTER_UNITS
        
        assert isinstance(COUNTER_UNITS, dict)
        assert len(COUNTER_UNITS) > 0
    
    def test_unit_strengths_exists(self):
        """Test that unit strengths dictionary exists."""
        from prompts import UNIT_STRENGTHS
        
        assert isinstance(UNIT_STRENGTHS, dict)
        assert len(UNIT_STRENGTHS) > 0
    
    def test_riflemen_counter(self):
        """Test riflemen counter relationships."""
        from prompts import UNIT_STRENGTHS
        
        if "riflemen" in UNIT_STRENGTHS:
            riflemen = UNIT_STRENGTHS["riflemen"]
            assert "strong_against" in riflemen or "weak_against" in riflemen


class TestResourceManagement:
    """Tests for resource management rules."""
    
    def test_fuel_cutoffs_exist(self):
        """Test that fuel cutoffs are defined."""
        from prompts import FUEL_CUTOFFS
        
        assert isinstance(FUEL_CUTOFFS, dict)
        assert "build_tank" in FUEL_CUTOFFS
        assert "build_vehicle" in FUEL_CUTOFFS
    
    def test_manpower_cutoffs_exist(self):
        """Test that manpower cutoffs are defined."""
        from prompts import MANPOWER_CUTOFFS
        
        assert isinstance(MANPOWER_CUTOFFS, dict)
        assert "build_infantry" in MANPOWER_CUTOFFS
    
    def test_munitions_cutoffs_exist(self):
        """Test that munitions cutoffs are defined."""
        from prompts import MUNITIONS_CUTOFFS
        
        assert isinstance(MUNITIONS_CUTOFFS, dict)
        assert "use_ability" in MUNITIONS_CUTOFFS


class TestBuildingCosts:
    """Tests for building costs."""
    
    def test_building_costs_exist(self):
        """Test that building costs are defined."""
        from prompts import BUILDING_COSTS
        
        assert isinstance(BUILDING_COSTS, dict)
        assert "barracks" in BUILDING_COSTS
        assert "war_factory" in BUILDING_COSTS
    
    def test_barracks_cost(self):
        """Test barracks cost structure."""
        from prompts import BUILDING_COSTS
        
        barracks = BUILDING_COSTS.get("barracks", {})
        assert "manpower" in barracks
        assert "fuel" in barracks
        assert "time" in barracks


class TestUnitCosts:
    """Tests for unit costs."""
    
    def test_unit_costs_exist(self):
        """Test that unit costs are defined."""
        from prompts import UNIT_COSTS
        
        assert isinstance(UNIT_COSTS, dict)
        assert "riflemen" in UNIT_COSTS
        assert "light_tank" in UNIT_COSTS
    
    def test_riflemen_cost(self):
        """Test riflemen cost structure."""
        from prompts import UNIT_COSTS
        
        riflemen = UNIT_COSTS.get("riflemen", {})
        assert "manpower" in riflemen
        assert "pop" in riflemen


class TestDifficultyDoctrines:
    """Tests for difficulty doctrines."""
    
    def test_difficulty_doctrines_exist(self):
        """Test that difficulty doctrines are defined."""
        from prompts import DIFFICULTY_DOCTRINES
        
        assert isinstance(DIFFICULTY_DOCTRINES, dict)
        assert len(DIFFICULTY_DOCTRINES) == 4
    
    def test_easy_doctrine(self):
        """Test easy difficulty doctrine."""
        from prompts import DIFFICULTY_DOCTRINES, Difficulty
        
        easy = DIFFICULTY_DOCTRINES.get(Difficulty.EASY, {})
        assert "aggression" in easy
        assert "defense" in easy
        assert "economy_focus" in easy
        assert "risk_tolerance" in easy


class TestPhaseStrategies:
    """Tests for game phase strategies."""
    
    def test_phase_strategies_exist(self):
        """Test that phase strategies are defined."""
        from prompts import PHASE_STRATEGIES
        
        assert isinstance(PHASE_STRATEGIES, dict)
        assert len(PHASE_STRATEGIES) == 3
    
    def test_early_phase_strategy(self):
        """Test early game phase strategy."""
        from prompts import PHASE_STRATEGIES, GamePhase
        
        early = PHASE_STRATEGIES.get(GamePhase.EARLY, {})
        assert "focus" in early
        assert "priorities" in early
        assert "avoid" in early


class TestFactoryFunctions:
    """Tests for factory functions."""
    
    def test_create_prompt_engine(self):
        """Test create_prompt_engine factory function."""
        from prompts import create_prompt_engine
        
        engine = create_prompt_engine()
        assert engine is not None
    
    def test_get_prompt_engine_singleton(self):
        """Test get_prompt_engine singleton."""
        from prompts import get_prompt_engine, reset_prompt_engine
        
        # Reset to ensure clean state
        reset_prompt_engine()
        
        engine1 = get_prompt_engine()
        engine2 = get_prompt_engine()
        
        # Should return the same instance
        assert engine1 is engine2
        
        # Clean up
        reset_prompt_engine()


class TestStateFormatting:
    """Tests for game state formatting."""
    
    def test_format_state_for_prompt(self, prompt_engine):
        """Test formatting game state for prompt."""
        game_state = {
            "game_time": 120.5,
            "phase": "early",
            "faction": "allies",
            "player_id": 1,
            "resources": {
                "manpower": {"current": 500, "income": 10, "max": 1000},
                "fuel": {"current": 300, "income": 5, "max": 800}
            },
            "squads": [{"id": 1, "type": "riflemen", "health": 0.8, "max_health": 1.0, "pos": [100, 200, 0]}],
            "cps": [{"id": 1, "pos": [500, 500, 0], "owner": 1, "capture_progress": 1.0}],
            "tech": {"tier_1": True, "tier_2": False, "tier_3": False},
            "queue": [],
            "pop": [11, 100]
        }
        
        formatted = prompt_engine._format_state_for_prompt(game_state)
        
        assert isinstance(formatted, str)
        assert "Game Time" in formatted
        assert "Resources" in formatted
        assert "Squads" in formatted
    
    def test_format_history_for_prompt(self, prompt_engine):
        """Test formatting history for prompt."""
        history = [
            {"game_time": 60.0, "resources": {"manpower": {"current": 300}}, "squads": [], "cps": [], "pop": [5, 100]},
            {"game_time": 90.0, "resources": {"manpower": {"current": 400}}, "squads": [], "cps": [], "pop": [8, 100]}
        ]
        
        formatted = prompt_engine._format_history_for_prompt(history)
        
        assert isinstance(formatted, str)
        assert "RECENT HISTORY" in formatted


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
