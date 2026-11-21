"""
Phase 3: JSON Mode Integration Unit Tests

Tests for JSON mode configuration and schema validation.

Author: Generated for Phase 3 pytest integration
Version: 1.0.0
Date: 2026-11-21
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add project root and python directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python"))


class TestJSONModeConfiguration:
    """Tests for JSON mode configuration."""
    
    def test_mistral_client_json_mode_default(self):
        """Test that JSON mode is enabled by default."""
        from mistral_client import MistralClient
        import os
        
        # Set up environment
        os.environ['MISTRAL_API_KEY'] = 'test_key'
        
        client = MistralClient()
        assert client.is_json_mode() == True
        client.close()
        
        del os.environ['MISTRAL_API_KEY']
    
    def test_mistral_client_json_mode_disabled(self):
        """Test disabling JSON mode."""
        from mistral_client import MistralClient
        import os
        
        os.environ['MISTRAL_API_KEY'] = 'test_key'
        
        client = MistralClient(json_mode=False)
        assert client.is_json_mode() == False
        
        client.enable_json_mode(True)
        assert client.is_json_mode() == True
        
        client.enable_json_mode(False)
        assert client.is_json_mode() == False
        
        client.close()
        
        del os.environ['MISTRAL_API_KEY']
    
    def test_json_response_format(self):
        """Test JSON response format from Mistral."""
        from mistral_client import MistralResponse
        
        # Create a response with JSON content
        response = MistralResponse(
            content='{"intentions": [{"intent": "BUILD", "confidence": 0.9}]}',
            model="mistral-small-latest",
            finish_reason="stop",
            usage={"total_tokens": 10},
            response_time=0.5,
            timestamp=1234567890.0
        )
        
        # Should be parseable as JSON
        content = json.loads(response.content)
        assert "intentions" in content
        assert isinstance(content["intentions"], list)


class TestIntentSchema:
    """Tests for intent schema validation."""
    
    def test_valid_intent_structure(self):
        """Test valid intent structure."""
        from orchestrator.strategist import StrategicIntent
        
        intent_data = {
            "intent": "BUILD",
            "confidence": 0.9,
            "reasoning": "Build barracks for infantry",
            "priority": 5,
            "parameters": {
                "building_type": "barracks",
                "position": [200, 200, 0]
            }
        }
        
        intent = StrategicIntent.from_dict(intent_data)
        
        assert intent.intent == "BUILD"
        assert intent.confidence == 0.9
        assert intent.reasoning == "Build barracks for infantry"
        assert intent.priority == 5
        assert intent.parameters == {"building_type": "barracks", "position": [200, 200, 0]}
    
    def test_intent_with_minimal_fields(self):
        """Test intent with minimal required fields."""
        from orchestrator.strategist import StrategicIntent
        
        intent_data = {
            "intent": "RETREAT",
            "confidence": 0.5,
            "priority": 1
        }
        
        intent = StrategicIntent.from_dict(intent_data)
        
        assert intent.intent == "RETREAT"
        assert intent.confidence == 0.5
        assert intent.priority == 1
        assert intent.reasoning == ""
        assert intent.parameters == {}
    
    def test_intent_with_all_fields(self):
        """Test intent with all possible fields."""
        from orchestrator.strategist import StrategicIntent
        import time
        
        intent_data = {
            "intent": "ATTACK",
            "confidence": 0.95,
            "reasoning": "Attack enemy position",
            "priority": 10,
            "parameters": {
                "target_position": [500, 500, 0],
                "units": [1, 2, 3]
            },
            "timestamp": time.time()
        }
        
        intent = StrategicIntent.from_dict(intent_data)
        
        assert intent.intent == "ATTACK"
        assert intent.confidence == 0.95
        assert intent.reasoning == "Attack enemy position"
        assert intent.priority == 10
        assert "target_position" in intent.parameters
        assert "units" in intent.parameters
    
    def test_intent_to_dict_roundtrip(self):
        """Test intent to dict and back."""
        from orchestrator.strategist import StrategicIntent
        
        original_data = {
            "intent": "CAPTURE",
            "confidence": 0.8,
            "reasoning": "Capture point",
            "priority": 7,
            "parameters": {"point_id": 1, "squad_id": 2}
        }
        
        intent = StrategicIntent.from_dict(original_data)
        result = intent.to_dict()
        
        assert result == original_data


class TestJSONParsing:
    """Tests for JSON parsing functionality."""
    
    def test_parse_simple_json_response(self):
        """Test parsing simple JSON response."""
        from orchestrator.strategist import Strategist
        import json
        
        json_content = '{"intentions": [{"intent": "BUILD", "confidence": 0.9, "priority": 5}]}'
        
        # This would be called by the strategist internally
        data = json.loads(json_content)
        intents_data = data.get("intentions", [])
        
        assert len(intents_data) == 1
        assert intents_data[0]["intent"] == "BUILD"
    
    def test_parse_json_with_multiple_intents(self):
        """Test parsing JSON with multiple intents."""
        import json
        
        json_content = '''
        {
            "intentions": [
                {"intent": "BUILD", "confidence": 0.9, "priority": 5},
                {"intent": "PRODUCE", "confidence": 0.8, "priority": 4},
                {"intent": "ATTACK", "confidence": 0.7, "priority": 3}
            ]
        }
        '''
        
        data = json.loads(json_content)
        intents_data = data.get("intentions", [])
        
        assert len(intents_data) == 3
        assert intents_data[0]["intent"] == "BUILD"
        assert intents_data[1]["intent"] == "PRODUCE"
        assert intents_data[2]["intent"] == "ATTACK"
    
    def test_parse_json_with_nested_parameters(self):
        """Test parsing JSON with nested parameters."""
        import json
        
        json_content = '''
        {
            "intentions": [
                {
                    "intent": "BUILD",
                    "confidence": 0.9,
                    "priority": 5,
                    "parameters": {
                        "building_type": "barracks",
                        "position": [200, 200, 0],
                        "engineer_id": 1
                    }
                }
            ]
        }
        '''
        
        data = json.loads(json_content)
        intents_data = data.get("intentions", [])
        
        assert len(intents_data) == 1
        params = intents_data[0]["parameters"]
        assert params["building_type"] == "barracks"
        assert params["position"] == [200, 200, 0]
        assert params["engineer_id"] == 1
    
    def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown."""
        import json
        import re
        
        markdown_content = "Here is the response:\n\n```json\n{\"intentions\": [{\"intent\": \"BUILD\"}]}\n```\n\nEnd of response."
        
        # Extract JSON from markdown
        json_match = re.search(r'\{.*\}', markdown_content, re.DOTALL)
        assert json_match is not None
        
        data = json.loads(json_match.group())
        assert "intentions" in data


class TestJSONValidation:
    """Tests for JSON validation."""
    
    def test_validate_json_structure(self):
        """Test validating JSON structure."""
        import json
        
        valid_json = '{"intentions": [{"intent": "BUILD", "confidence": 0.9}]}'
        
        try:
            data = json.loads(valid_json)
            assert "intentions" in data
            assert isinstance(data["intentions"], list)
            assert len(data["intentions"]) > 0
        except json.JSONDecodeError:
            pytest.fail("Valid JSON should not raise error")
    
    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises error."""
        import json
        
        invalid_json = '{"intentions": [{"intent": "BUILD", "confidence": 0.9}'  # Missing closing braces
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)
    
    def test_empty_json(self):
        """Test empty JSON object."""
        import json
        
        empty_json = '{}'
        data = json.loads(empty_json)
        
        assert data == {}
        assert "intentions" not in data
    
    def test_json_with_extra_fields(self):
        """Test JSON with extra fields."""
        import json
        
        json_with_extras = '''
        {
            "intentions": [{"intent": "BUILD"}],
            "metadata": {"version": "1.0"},
            "timestamp": 1234567890
        }
        '''
        
        data = json.loads(json_with_extras)
        
        assert "intentions" in data
        assert "metadata" in data
        assert "timestamp" in data


class TestJSONModeInPrompts:
    """Tests for JSON mode in prompts."""
    
    def test_prompt_requests_json_format(self):
        """Test that prompts request JSON format."""
        from prompts import create_prompt_engine, PromptConfig
        
        config = PromptConfig()
        engine = create_prompt_engine(config)
        
        system_prompt = engine.generate_system_prompt()
        
        # Should mention JSON format
        assert "JSON" in system_prompt or "json" in system_prompt
    
    def test_prompt_expects_json_response(self):
        """Test that prompts expect JSON response."""
        from prompts import BASE_SYSTEM_PROMPT
        
        # The base prompt should mention JSON format
        assert "JSON" in BASE_SYSTEM_PROMPT or "json" in BASE_SYSTEM_PROMPT
    
    def test_intent_schema_in_prompt(self):
        """Test that intent schema is mentioned in prompt."""
        from prompts import BASE_SYSTEM_PROMPT
        
        # Should mention intentions array
        assert "intentions" in BASE_SYSTEM_PROMPT or "intents" in BASE_SYSTEM_PROMPT


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
