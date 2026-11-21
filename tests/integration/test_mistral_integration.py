"""
Phase 3: Mistral Integration Tests

Integration tests for Mistral API client.

Author: Generated for Phase 3 pytest integration
Version: 1.0.0
Date: 2026-11-21
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root and python directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python"))


@pytest.fixture
def env_with_key():
    """Set up environment with API key."""
    test_key = "test_key_mstrl_1234567890"
    with patch.dict('os.environ', {'MISTRAL_API_KEY': test_key}, clear=False):
        yield test_key


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("MISTRAL_API_KEY=test_key_from_file_12345\n")
        yield f.name
    os.unlink(f.name)


class TestMistralClientIntegration:
    """Integration tests for MistralClient."""
    
    @pytest.mark.skipif(not os.getenv('MISTRAL_API_KEY'), reason="MISTRAL_API_KEY not set")
    def test_real_api_connection(self):
        """Test real API connection (requires valid API key)."""
        from mistral_client import create_mistral_client, MistralModel
        
        client = create_mistral_client(
            model=MistralModel.SMALL,
            json_mode=True
        )
        
        # Test getting models
        models = client.get_models()
        
        assert len(models) > 0
        assert any('codestral' in m.get('id', '') or 'mistral' in m.get('id', '') for m in models)
        
        client.close()
    
    @pytest.mark.skipif(not os.getenv('MISTRAL_API_KEY'), reason="MISTRAL_API_KEY not set")
    def test_real_chat_completion(self):
        """Test real chat completion (requires valid API key)."""
        from mistral_client import create_mistral_client, MistralModel
        
        client = create_mistral_client(
            model=MistralModel.SMALL,
            json_mode=True
        )
        
        messages = [
            {"role": "user", "content": "What is 2+2? Respond with JSON: {\"answer\": number}"}
        ]
        
        response = client.chat_completion(
            messages=messages,
            max_tokens=100
        )
        
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model is not None
        assert response.finish_reason is not None
        assert response.usage is not None
        assert response.response_time > 0
        
        # Try to parse as JSON
        try:
            data = json.loads(response.content)
            assert "answer" in data
            assert data["answer"] == 4
        except json.JSONDecodeError:
            # If not JSON, just check it's a valid response
            pass
        
        client.close()
    
    @pytest.mark.skipif(not os.getenv('MISTRAL_API_KEY'), reason="MISTRAL_API_KEY not set")
    def test_api_latency(self):
        """Test API response latency."""
        from mistral_client import create_mistral_client, MistralModel
        import time
        
        client = create_mistral_client(
            model=MistralModel.SMALL,
            json_mode=True
        )
        
        messages = [
            {"role": "user", "content": "Say 'test'"}
        ]
        
        start_time = time.time()
        response = client.chat_completion(
            messages=messages,
            max_tokens=50
        )
        latency = time.time() - start_time
        
        assert latency > 0
        assert latency < 10.0  # Should be under 10 seconds
        assert response.response_time > 0
        
        client.close()
    
    @pytest.mark.skipif(not os.getenv('MISTRAL_API_KEY'), reason="MISTRAL_API_KEY not set")
    def test_multiple_sequential_calls(self):
        """Test making multiple sequential API calls."""
        from mistral_client import create_mistral_client, MistralModel
        
        client = create_mistral_client(
            model=MistralModel.SMALL,
            json_mode=True
        )
        
        for i in range(3):
            messages = [
                {"role": "user", "content": f"Test message {i+1}"}
            ]
            
            response = client.chat_completion(
                messages=messages,
                max_tokens=50
            )
            
            assert response.content is not None
            assert len(response.content) > 0
        
        client.close()


class TestPromptEngineIntegration:
    """Integration tests for PromptEngine."""
    
    def test_prompt_generation_with_real_state(self):
        """Test prompt generation with realistic game state."""
        from prompts import create_prompt_engine, Faction, Difficulty, GamePhase, PromptConfig
        
        config = PromptConfig(
            faction=Faction.ALLIES,
            difficulty=Difficulty.NORMAL,
            game_phase=GamePhase.EARLY
        )
        
        engine = create_prompt_engine(config)
        
        # Realistic game state
        game_state = {
            "version": "1.0",
            "player_id": 1,
            "timestamp": 1234567890.0,
            "game_time": 120.5,
            "phase": "early",
            "faction": "allies",
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
                    "pos": [100, 200, 0],
                    "posture": "defensive",
                    "in_combat": False,
                    "under_fire": False
                },
                {
                    "id": 2,
                    "type": "engineer",
                    "health": 1.0,
                    "max_health": 1.0,
                    "pos": [150, 250, 0],
                    "posture": "defensive",
                    "in_combat": False,
                    "under_fire": False
                }
            ],
            "cps": [
                {"id": 1, "pos": [500, 500, 0], "owner": 1, "capture_progress": 1.0},
                {"id": 2, "pos": [300, 400, 0], "owner": None, "capture_progress": 0.0}
            ],
            "tech": {
                "tier_1": True,
                "tier_2": False,
                "tier_3": False,
                "abilities": ["scout", "riflemen"]
            },
            "queue": [
                {"type": "build", "name": "barracks", "progress": 0.5, "time": 30}
            ],
            "pop": [11, 100]
        }
        
        system_prompt = engine.generate_system_prompt()
        user_prompt = engine.generate_user_prompt(game_state)
        
        # Verify prompts are generated
        assert len(system_prompt) > 1000
        assert len(user_prompt) > 100
        
        # Verify prompts contain expected content
        assert "Allies" in system_prompt or "allies" in system_prompt
        assert "500" in user_prompt  # Manpower
        assert "300" in user_prompt  # Fuel
        assert "riflemen" in user_prompt
        assert "engineer" in user_prompt
    
    def test_prompt_generation_all_factions(self):
        """Test prompt generation for all factions."""
        from prompts import create_prompt_engine, Faction, Difficulty, GamePhase, PromptConfig
        
        for faction in [Faction.ALLIES, Faction.AXIS]:
            config = PromptConfig(
                faction=faction,
                difficulty=Difficulty.NORMAL,
                game_phase=GamePhase.EARLY
            )
            
            engine = create_prompt_engine(config)
            system_prompt = engine.generate_system_prompt()
            
            assert len(system_prompt) > 1000
            assert faction.value in system_prompt or faction.value.upper() in system_prompt
    
    def test_prompt_generation_all_difficulties(self):
        """Test prompt generation for all difficulties."""
        from prompts import create_prompt_engine, Faction, Difficulty, GamePhase, PromptConfig
        
        for difficulty in [Difficulty.EASY, Difficulty.NORMAL, Difficulty.HARD, Difficulty.EXPERT]:
            config = PromptConfig(
                faction=Faction.ALLIES,
                difficulty=difficulty,
                game_phase=GamePhase.EARLY
            )
            
            engine = create_prompt_engine(config)
            system_prompt = engine.generate_system_prompt()
            
            assert len(system_prompt) > 1000
            assert difficulty.value in system_prompt or difficulty.value.upper() in system_prompt
    
    def test_prompt_generation_all_phases(self):
        """Test prompt generation for all game phases."""
        from prompts import create_prompt_engine, Faction, Difficulty, GamePhase, PromptConfig
        
        for phase in [GamePhase.EARLY, GamePhase.MID, GamePhase.LATE]:
            config = PromptConfig(
                faction=Faction.ALLIES,
                difficulty=Difficulty.NORMAL,
                game_phase=phase
            )
            
            engine = create_prompt_engine(config)
            system_prompt = engine.generate_system_prompt()
            
            assert len(system_prompt) > 1000
            assert phase.value in system_prompt or phase.value.upper() in system_prompt


class TestStrategistIntegration:
    """Integration tests for Strategist."""
    
    def test_strategist_with_mock_client(self):
        """Test strategist with mock Mistral client."""
        from orchestrator.strategist import create_strategist, StrategistConfig
        from unittest.mock import MagicMock
        
        # Create mock client
        mock_client = MagicMock()
        mock_client.get_model.return_value = MagicMock(value="mistral-small-latest")
        mock_client.set_model.return_value = None
        mock_client.close.return_value = None
        mock_client.chat_completion.return_value = MagicMock(
            content='{"intentions": [{"intent": "BUILD", "confidence": 0.9, "priority": 5, "parameters": {"building_type": "barracks"}}]}',
            model="mistral-small-latest",
            finish_reason="stop",
            usage={"total_tokens": 20},
            response_time=0.5,
            timestamp=1234567890.0
        )
        
        # Create mock state manager
        mock_state_manager = MagicMock()
        mock_state_manager.get_current_state.return_value = {
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
        
        # Create mock command processor
        mock_command_processor = MagicMock()
        mock_command_processor.start.return_value = True
        mock_command_processor.stop.return_value = True
        
        config = StrategistConfig(
            enabled=True,
            model="mistral-small-latest",
            temperature=0.7,
            max_tokens=2048,
            json_mode=True
        )
        
        with patch('orchestrator.strategist.create_mistral_client', return_value=mock_client), \
             patch('orchestrator.strategist.create_prompt_engine') as mock_engine, \
             patch('orchestrator.strategist.get_history_manager') as mock_history, \
             patch('orchestrator.strategist.get_validator') as mock_validator, \
             patch('orchestrator.strategist.get_safety_filter') as mock_filter, \
             patch('orchestrator.strategist.get_fallback_manager') as mock_fallback, \
             patch('orchestrator.strategist.get_rate_limiter') as mock_limiter:
            
            mock_engine.return_value = MagicMock()
            mock_engine.return_value.generate_system_prompt.return_value = "System prompt"
            mock_engine.return_value.generate_user_prompt.return_value = "User prompt"
            mock_engine.return_value.set_faction.return_value = None
            mock_engine.return_value.set_game_phase.return_value = None
            
            mock_history.return_value = MagicMock()
            mock_validator.return_value = MagicMock()
            mock_filter.return_value = MagicMock()
            mock_fallback.return_value = MagicMock()
            mock_limiter.return_value = MagicMock()
            mock_limiter.return_value.check_call.return_value = "allowed"
            
            strategist = create_strategist(
                config=config,
                state_manager=mock_state_manager,
                command_processor=mock_command_processor
            )
            
            assert strategist is not None
            assert strategist.config == config
            
            # Test start/stop
            assert strategist.start() == True
            assert strategist.stop() == True
    
    def test_strategist_cycle_with_mock(self):
        """Test strategist cycle with mock components."""
        from orchestrator.strategist import create_strategist, StrategistConfig
        from unittest.mock import MagicMock
        
        # Create mock client with JSON response
        mock_client = MagicMock()
        mock_client.get_model.return_value = MagicMock(value="mistral-small-latest")
        mock_client.set_model.return_value = None
        mock_client.close.return_value = None
        mock_client.chat_completion.return_value = MagicMock(
            content='{"intentions": [{"intent": "BUILD", "confidence": 0.9, "priority": 5, "parameters": {"building_type": "barracks", "position": [200, 200, 0]}}]}',
            model="mistral-small-latest",
            finish_reason="stop",
            usage={"total_tokens": 30},
            response_time=0.5,
            timestamp=1234567890.0
        )
        
        # Create mock state manager
        mock_state_manager = MagicMock()
        mock_state_manager.get_current_state.return_value = {
            "game_time": 120.5,
            "phase": "early",
            "faction": "allies",
            "player_id": 1,
            "resources": {"manpower": {"current": 500}},
            "squads": [],
            "cps": [],
            "tech": {"tier_1": True},
            "queue": [],
            "pop": [11, 100]
        }
        
        # Create mock command processor
        mock_command_processor = MagicMock()
        mock_command_processor.start.return_value = True
        mock_command_processor.stop.return_value = True
        mock_command_processor.add_command.return_value = True
        
        config = StrategistConfig(
            enabled=True,
            model="mistral-small-latest",
            temperature=0.7,
            max_tokens=2048,
            json_mode=True
        )
        
        with patch('orchestrator.strategist.create_mistral_client', return_value=mock_client), \
             patch('orchestrator.strategist.create_prompt_engine') as mock_engine, \
             patch('orchestrator.strategist.get_history_manager') as mock_history, \
             patch('orchestrator.strategist.get_validator') as mock_validator, \
             patch('orchestrator.strategist.get_safety_filter') as mock_filter, \
             patch('orchestrator.strategist.get_fallback_manager') as mock_fallback, \
             patch('orchestrator.strategist.get_rate_limiter') as mock_limiter:
            
            mock_engine.return_value = MagicMock()
            mock_engine.return_value.generate_system_prompt.return_value = "System: You are CoH1 AI"
            mock_engine.return_value.generate_user_prompt.return_value = "User: Current state..."
            mock_engine.return_value.set_faction.return_value = None
            mock_engine.return_value.set_game_phase.return_value = None
            
            mock_history.return_value = MagicMock()
            mock_history.return_value.get_all_entries.return_value = []
            
            mock_validator.return_value = MagicMock()
            mock_validator.return_value.validate.return_value = MagicMock(is_valid=True, errors=[])
            
            mock_filter.return_value = MagicMock()
            mock_filter.return_value.check_command.return_value = MagicMock(is_safe=True, errors=[])
            
            mock_fallback.return_value = MagicMock()
            mock_fallback.return_value.is_in_fallback.return_value = False
            
            mock_limiter.return_value = MagicMock()
            mock_limiter.return_value.check_call.return_value = "allowed"
            mock_limiter.return_value.record_call.return_value = None
            
            strategist = create_strategist(
                config=config,
                state_manager=mock_state_manager,
                command_processor=mock_command_processor
            )
            
            assert strategist.start() == True
            
            # Run a cycle
            result = strategist.run_cycle()
            
            # Should complete successfully
            assert result == True
            
            # Check stats
            stats = strategist.get_stats()
            assert stats.total_cycles >= 1
            
            strategist.stop()


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
