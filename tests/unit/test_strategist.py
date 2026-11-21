"""
Phase 3: Strategist Unit Tests

Tests for the strategist module.

Author: Generated for Phase 3 pytest integration
Version: 1.0.0
Date: 2026-11-21
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add project root and python directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python"))


@pytest.fixture
def strategist_config():
    """Create a default strategist configuration."""
    from orchestrator.strategist import StrategistConfig
    
    config = StrategistConfig(
        enabled=True,
        model="mistral-small-latest",
        temperature=0.7,
        max_tokens=2048,
        json_mode=True,
        max_intents_per_cycle=5,
        min_confidence=0.5,
        min_priority=1,
        include_history=True,
        history_depth=5,
        fallback_on_error=True,
        fallback_on_rate_limit=True,
        log_intents=True,
        log_responses=False
    )
    yield config


@pytest.fixture
def mock_mistral_client():
    """Create a mock Mistral client."""
    from unittest.mock import MagicMock
    from mistral_client import MistralModel
    
    mock_client = MagicMock()
    mock_client.get_model.return_value = MistralModel.SMALL
    mock_client.set_model.return_value = None
    mock_client.close.return_value = None
    mock_client.chat_completion.return_value = MagicMock(
        content='{"intentions": []}',
        model="mistral-small-latest",
        finish_reason="stop",
        usage={"total_tokens": 10},
        response_time=0.5,
        timestamp=1234567890.0
    )
    
    yield mock_client


@pytest.fixture
def mock_prompt_engine():
    """Create a mock prompt engine."""
    from unittest.mock import MagicMock
    
    mock_engine = MagicMock()
    mock_engine.generate_system_prompt.return_value = "System prompt"
    mock_engine.generate_user_prompt.return_value = "User prompt"
    mock_engine.set_faction.return_value = None
    mock_engine.set_game_phase.return_value = None
    mock_engine.set_config.return_value = None
    mock_engine.get_config.return_value = MagicMock()
    
    yield mock_engine


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager."""
    from unittest.mock import MagicMock
    
    mock_manager = MagicMock()
    mock_manager.get_current_state.return_value = {
        "game_time": 120.5,
        "phase": "early",
        "faction": "allies",
        "player_id": 1,
        "resources": {},
        "squads": [],
        "cps": [],
        "tech": {},
        "queue": [],
        "pop": [11, 100]
    }
    
    yield mock_manager


@pytest.fixture
def mock_command_processor():
    """Create a mock command processor."""
    from unittest.mock import MagicMock
    
    mock_processor = MagicMock()
    mock_processor.start.return_value = True
    mock_processor.stop.return_value = True
    mock_processor.add_command.return_value = True
    mock_processor.update_game_state.return_value = None
    
    yield mock_processor


class TestStrategistConfig:
    """Tests for StrategistConfig dataclass."""
    
    def test_default_config(self, strategist_config):
        """Test default strategist configuration."""
        assert strategist_config.enabled == True
        assert strategist_config.model == "mistral-small-latest"
        assert strategist_config.temperature == 0.7
        assert strategist_config.max_tokens == 2048
        assert strategist_config.json_mode == True
        assert strategist_config.max_intents_per_cycle == 5
        assert strategist_config.min_confidence == 0.5
        assert strategist_config.min_priority == 1
        assert strategist_config.include_history == True
        assert strategist_config.history_depth == 5
        assert strategist_config.fallback_on_error == True
        assert strategist_config.fallback_on_rate_limit == True
        assert strategist_config.log_intents == True
        assert strategist_config.log_responses == False
    
    def test_custom_config(self):
        """Test custom strategist configuration."""
        from orchestrator.strategist import StrategistConfig
        
        config = StrategistConfig(
            enabled=False,
            model="mistral-large-latest",
            temperature=0.9,
            max_tokens=1024,
            json_mode=False
        )
        
        assert config.enabled == False
        assert config.model == "mistral-large-latest"
        assert config.temperature == 0.9
        assert config.max_tokens == 1024
        assert config.json_mode == False


class TestStrategistStats:
    """Tests for StrategistStats dataclass."""
    
    def test_default_stats(self):
        """Test default strategist statistics."""
        from orchestrator.strategist import StrategistStats
        
        stats = StrategistStats()
        
        assert stats.total_cycles == 0
        assert stats.successful_cycles == 0
        assert stats.failed_cycles == 0
        assert stats.total_intents == 0
        assert stats.executed_intents == 0
        assert stats.failed_intents == 0
        assert stats.avg_processing_time == 0.0
        assert stats.avg_ai_response_time == 0.0
    
    def test_record_cycle_success(self):
        """Test recording a successful cycle."""
        from orchestrator.strategist import StrategistStats
        
        stats = StrategistStats()
        stats.record_cycle(True, 1.5, 0.5)
        
        assert stats.total_cycles == 1
        assert stats.successful_cycles == 1
        assert stats.failed_cycles == 0
    
    def test_record_cycle_failure(self):
        """Test recording a failed cycle."""
        from orchestrator.strategist import StrategistStats
        
        stats = StrategistStats()
        stats.record_cycle(False, 1.5, 0.5, "Test error")
        
        assert stats.total_cycles == 1
        assert stats.successful_cycles == 0
        assert stats.failed_cycles == 1
        assert stats.last_error == "Test error"
    
    def test_record_intent_success(self):
        """Test recording a successful intent."""
        from orchestrator.strategist import StrategistStats
        
        stats = StrategistStats()
        stats.record_intent(True)
        
        assert stats.total_intents == 1
        assert stats.executed_intents == 1
        assert stats.failed_intents == 0
    
    def test_record_intent_failure(self):
        """Test recording a failed intent."""
        from orchestrator.strategist import StrategistStats
        
        stats = StrategistStats()
        stats.record_intent(False)
        
        assert stats.total_intents == 1
        assert stats.executed_intents == 0
        assert stats.failed_intents == 1
    
    def test_to_dict(self):
        """Test converting stats to dictionary."""
        from orchestrator.strategist import StrategistStats
        
        stats = StrategistStats()
        stats.record_cycle(True, 1.5, 0.5)
        stats.record_intent(True)
        
        result = stats.to_dict()
        
        assert result['total_cycles'] == 1
        assert result['successful_cycles'] == 1
        assert result['total_intents'] == 1
        assert result['executed_intents'] == 1


class TestStrategicIntent:
    """Tests for StrategicIntent dataclass."""
    
    def test_default_intent(self):
        """Test default strategic intent."""
        from orchestrator.strategist import StrategicIntent
        
        intent = StrategicIntent(
            intent="BUILD",
            confidence=0.8,
            reasoning="Test reasoning",
            priority=5,
            parameters={"building_type": "barracks"}
        )
        
        assert intent.intent == "BUILD"
        assert intent.confidence == 0.8
        assert intent.reasoning == "Test reasoning"
        assert intent.priority == 5
        assert intent.parameters == {"building_type": "barracks"}
    
    def test_intent_to_dict(self):
        """Test converting intent to dictionary."""
        from orchestrator.strategist import StrategicIntent
        
        intent = StrategicIntent(
            intent="ATTACK",
            confidence=0.9,
            reasoning="Attack enemy",
            priority=10,
            parameters={"target": [100, 200, 0]}
        )
        
        result = intent.to_dict()
        
        assert result['intent'] == "ATTACK"
        assert result['confidence'] == 0.9
        assert result['reasoning'] == "Attack enemy"
        assert result['priority'] == 10
        assert result['parameters'] == {"target": [100, 200, 0]}
    
    def test_intent_from_dict(self):
        """Test creating intent from dictionary."""
        from orchestrator.strategist import StrategicIntent
        
        data = {
            "intent": "DEFEND",
            "confidence": 0.7,
            "reasoning": "Defend position",
            "priority": 8,
            "parameters": {"position": [500, 500, 0]}
        }
        
        intent = StrategicIntent.from_dict(data)
        
        assert intent.intent == "DEFEND"
        assert intent.confidence == 0.7
        assert intent.reasoning == "Defend position"
        assert intent.priority == 8
        assert intent.parameters == {"position": [500, 500, 0]}


class TestIntentType:
    """Tests for IntentType enumeration."""
    
    def test_intent_type_values(self):
        """Test intent type enum values."""
        from orchestrator.strategist import IntentType
        
        assert IntentType.BUILD.value == "BUILD"
        assert IntentType.TECH.value == "TECH"
        assert IntentType.PRODUCE.value == "PRODUCE"
        assert IntentType.ATTACK.value == "ATTACK"
        assert IntentType.DEFEND.value == "DEFEND"
        assert IntentType.RETREAT.value == "RETREAT"
        assert IntentType.CAPTURE.value == "CAPTURE"
        assert IntentType.EXPAND.value == "EXPAND"
        assert IntentType.REINFORCE.value == "REINFORCE"
        assert IntentType.FALLBACK.value == "FALLBACK"
        assert IntentType.HOLD.value == "HOLD"
        assert IntentType.STOP.value == "STOP"


class TestStrategistState:
    """Tests for StrategistState enumeration."""
    
    def test_state_values(self):
        """Test strategist state enum values."""
        from orchestrator.strategist import StrategistState
        
        assert StrategistState.IDLE.value == 1
        assert StrategistState.PROCESSING.value == 2
        assert StrategistState.CALLING_AI.value == 3
        assert StrategistState.PARSE_INTENTS.value == 4
        assert StrategistState.EXECUTING.value == 5
        assert StrategistState.ERROR.value == 6
        assert StrategistState.FALLBACK.value == 7


class TestIntentToCommandMapping:
    """Tests for intent to command mapping."""
    
    def test_mapping_exists(self):
        """Test that intent to command mapping exists."""
        from orchestrator.strategist import INTENT_TO_COMMAND
        
        assert isinstance(INTENT_TO_COMMAND, dict)
        assert len(INTENT_TO_COMMAND) > 0
    
    def test_build_mapping(self):
        """Test BUILD intent mapping."""
        from orchestrator.strategist import INTENT_TO_COMMAND, IntentType
        
        build_mapping = INTENT_TO_COMMAND.get(IntentType.BUILD)
        assert build_mapping is not None
        assert "command" in build_mapping
        assert build_mapping["command"] == "BUILD"
        assert "required_params" in build_mapping
    
    def test_attack_mapping(self):
        """Test ATTACK intent mapping."""
        from orchestrator.strategist import INTENT_TO_COMMAND, IntentType
        
        attack_mapping = INTENT_TO_COMMAND.get(IntentType.ATTACK)
        assert attack_mapping is not None
        assert "command" in attack_mapping
        assert attack_mapping["command"] == "ATTACK_MOVE"


class TestFactoryFunctions:
    """Tests for strategist factory functions."""
    
    def test_create_strategist(self, strategist_config):
        """Test create_strategist factory function."""
        from orchestrator.strategist import create_strategist
        
        # Create with mock components
        with patch('orchestrator.strategist.create_mistral_client') as mock_client, \
             patch('orchestrator.strategist.create_prompt_engine') as mock_engine, \
             patch('orchestrator.strategist.get_history_manager') as mock_history, \
             patch('orchestrator.strategist.get_validator') as mock_validator, \
             patch('orchestrator.strategist.get_safety_filter') as mock_filter, \
             patch('orchestrator.strategist.get_fallback_manager') as mock_fallback, \
             patch('orchestrator.strategist.get_rate_limiter') as mock_limiter:
            
            mock_client.return_value = MagicMock()
            mock_engine.return_value = MagicMock()
            mock_history.return_value = MagicMock()
            mock_validator.return_value = MagicMock()
            mock_filter.return_value = MagicMock()
            mock_fallback.return_value = MagicMock()
            mock_limiter.return_value = MagicMock()
            
            strategist = create_strategist(config=strategist_config)
            
            assert strategist is not None
            assert strategist.config == strategist_config
    
    def test_get_strategist_singleton(self, strategist_config):
        """Test get_strategist singleton."""
        from orchestrator.strategist import get_strategist, reset_strategist
        
        # Reset to ensure clean state
        reset_strategist()
        
        with patch('orchestrator.strategist.create_mistral_client') as mock_client, \
             patch('orchestrator.strategist.create_prompt_engine') as mock_engine, \
             patch('orchestrator.strategist.get_history_manager') as mock_history, \
             patch('orchestrator.strategist.get_validator') as mock_validator, \
             patch('orchestrator.strategist.get_safety_filter') as mock_filter, \
             patch('orchestrator.strategist.get_fallback_manager') as mock_fallback, \
             patch('orchestrator.strategist.get_rate_limiter') as mock_limiter:
            
            mock_client.return_value = MagicMock()
            mock_engine.return_value = MagicMock()
            mock_history.return_value = MagicMock()
            mock_validator.return_value = MagicMock()
            mock_filter.return_value = MagicMock()
            mock_fallback.return_value = MagicMock()
            mock_limiter.return_value = MagicMock()
            
            strategist1 = get_strategist(config=strategist_config)
            strategist2 = get_strategist(config=strategist_config)
            
            # Should return the same instance
            assert strategist1 is strategist2
            
            # Clean up
            reset_strategist()


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
