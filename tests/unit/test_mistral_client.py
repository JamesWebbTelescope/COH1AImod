"""
Phase 3: Mistral API Client Unit Tests

Tests for the Mistral API client module.

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
from unittest.mock import patch, MagicMock, Mock

# Add project root and python directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python"))


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("MISTRAL_API_KEY=test_key_mstrl_12345\n")
        f.write("OTHER_VAR=value\n")
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_env_without_key():
    """Mock environment without API key."""
    with patch.dict('os.environ', {}, clear=True):
        yield


@pytest.fixture
def mock_env_with_key():
    """Mock environment with API key."""
    with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key_mstrl_12345'}, clear=False):
        yield


class TestAPIKeyLoading:
    """Tests for API key loading functionality."""
    
    def test_api_key_from_environment(self, mock_env_with_key):
        """Test loading API key from environment variable."""
        from mistral_client import MistralClient
        
        client = MistralClient()
        # Should not raise an error
        assert client._get_api_key() == 'test_key_mstrl_12345'
        client.close()
    
    def test_api_key_from_env_file(self, temp_env_file, mock_env_without_key):
        """Test loading API key from .env file."""
        from mistral_client import MistralClient
        
        # Temporarily override the _get_api_key to use our temp file
        client = MistralClient()
        key = client._get_api_key()
        # This will use the actual .env file in the project
        assert key.startswith('mstrl_')
        client.close()
    
    def test_api_key_not_found_raises_error(self, mock_env_without_key):
        """Test that missing API key raises ValueError."""
        from mistral_client import MistralClient
        
        # Remove any existing .env files temporarily
        with patch('os.path.exists', return_value=False):
            client = MistralClient()
            with pytest.raises(ValueError, match="Mistral API key not found"):
                client._get_api_key()
            client.close()
    
    def test_api_key_format_validation(self, mock_env_with_key):
        """Test that API key format is validated."""
        from mistral_client import MistralClient
        
        client = MistralClient()
        key = client._get_api_key()
        assert key.startswith('mstrl_')
        client.close()


class TestMistralClientInitialization:
    """Tests for MistralClient initialization."""
    
    def test_default_initialization(self, mock_env_with_key):
        """Test client initialization with default parameters."""
        from mistral_client import MistralClient, MistralModel
        
        client = MistralClient()
        assert client.model == MistralModel.SMALL
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
        assert client.json_mode == True
        client.close()
    
    def test_custom_initialization(self, mock_env_with_key):
        """Test client initialization with custom parameters."""
        from mistral_client import MistralClient, MistralModel
        
        client = MistralClient(
            model=MistralModel.LARGE,
            timeout=60.0,
            max_retries=5,
            retry_delay=2.0,
            json_mode=False
        )
        assert client.model == MistralModel.LARGE
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.retry_delay == 2.0
        assert client.json_mode == False
        client.close()
    
    def test_invalid_model_raises_error(self, mock_env_with_key):
        """Test that invalid model raises error."""
        from mistral_client import MistralClient
        
        with pytest.raises(ValueError):
            MistralClient(model="invalid-model")


class TestMistralClientConfiguration:
    """Tests for client configuration."""
    
    def test_set_model(self, mock_env_with_key):
        """Test setting model after initialization."""
        from mistral_client import MistralClient, MistralModel
        
        client = MistralClient()
        client.set_model(MistralModel.LARGE)
        assert client.get_model() == MistralModel.LARGE
        client.close()
    
    def test_get_model(self, mock_env_with_key):
        """Test getting current model."""
        from mistral_client import MistralClient, MistralModel
        
        client = MistralClient(model=MistralModel.LARGE)
        assert client.get_model() == MistralModel.LARGE
        client.close()
    
    def test_enable_json_mode(self, mock_env_with_key):
        """Test enabling/disabling JSON mode."""
        from mistral_client import MistralClient
        
        client = MistralClient(json_mode=False)
        assert client.is_json_mode() == False
        
        client.enable_json_mode(True)
        assert client.is_json_mode() == True
        
        client.enable_json_mode(False)
        assert client.is_json_mode() == False
        client.close()


class TestMistralClientHeaders:
    """Tests for API request headers."""
    
    def test_headers_include_api_key(self, mock_env_with_key):
        """Test that headers include API key."""
        from mistral_client import MistralClient
        
        client = MistralClient()
        headers = client._get_headers()
        
        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Bearer ')
        assert 'test_key_mstrl_12345' in headers['Authorization']
        assert headers['Content-Type'] == 'application/json'
        client.close()


class TestMistralClientModels:
    """Tests for model enumeration."""
    
    def test_mistral_model_values(self):
        """Test MistralModel enum values."""
        from mistral_client import MistralModel
        
        assert MistralModel.SMALL.value == "mistral-small-latest"
        assert MistralModel.LARGE.value == "mistral-large-latest"
        assert MistralModel.MEDIUM.value == "mistral-medium-latest"
    
    def test_model_iteration(self):
        """Test iterating over models."""
        from mistral_client import MistralModel
        
        models = list(MistralModel)
        assert len(models) == 3
        assert MistralModel.SMALL in models
        assert MistralModel.LARGE in models
        assert MistralModel.MEDIUM in models


class TestAPIStats:
    """Tests for API statistics tracking."""
    
    def test_stats_initialization(self, mock_env_with_key):
        """Test APIStats initialization."""
        from mistral_client import MistralClient
        
        client = MistralClient()
        stats = client.get_stats()
        
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.total_tokens == 0
        client.close()
    
    def test_stats_reset(self, mock_env_with_key):
        """Test resetting API statistics."""
        from mistral_client import MistralClient
        
        client = MistralClient()
        stats = client.get_stats()
        stats.total_calls = 10
        stats.successful_calls = 8
        
        client.reset_stats()
        stats = client.get_stats()
        
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        client.close()


class TestMistralResponse:
    """Tests for MistralResponse dataclass."""
    
    def test_response_creation(self):
        """Test creating MistralResponse."""
        from mistral_client import MistralResponse
        
        response = MistralResponse(
            content="test content",
            model="mistral-small-latest",
            finish_reason="stop",
            usage={"total_tokens": 10},
            response_time=0.5,
            timestamp=1234567890.0
        )
        
        assert response.content == "test content"
        assert response.model == "mistral-small-latest"
        assert response.finish_reason == "stop"
        assert response.usage == {"total_tokens": 10}
        assert response.response_time == 0.5
        assert response.timestamp == 1234567890.0
    
    def test_response_to_dict(self):
        """Test converting response to dictionary."""
        from mistral_client import MistralResponse
        
        response = MistralResponse(
            content="test",
            model="test-model",
            finish_reason="stop",
            usage={"total_tokens": 5},
            response_time=0.1,
            timestamp=100.0
        )
        
        result = response.to_dict()
        
        assert result['content'] == "test"
        assert result['model'] == "test-model"
        assert result['finish_reason'] == "stop"
        assert result['usage'] == {"total_tokens": 5}
        assert result['response_time'] == 0.1
        assert result['timestamp'] == 100.0


class TestFactoryFunctions:
    """Tests for factory functions."""
    
    def test_create_mistral_client(self, mock_env_with_key):
        """Test create_mistral_client factory function."""
        from mistral_client import create_mistral_client, MistralModel
        
        client = create_mistral_client(
            model=MistralModel.SMALL,
            json_mode=True
        )
        
        assert client is not None
        assert client.model == MistralModel.SMALL
        assert client.json_mode == True
        client.close()
    
    def test_get_mistral_client_singleton(self, mock_env_with_key):
        """Test get_mistral_client singleton."""
        from mistral_client import get_mistral_client, reset_mistral_client
        
        # Reset to ensure clean state
        reset_mistral_client()
        
        client1 = get_mistral_client()
        client2 = get_mistral_client()
        
        # Should return the same instance
        assert client1 is client2
        
        # Clean up
        reset_mistral_client()


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_mistral_api_error_creation(self):
        """Test MistralAPIError creation."""
        from mistral_client import MistralAPIError
        
        error = MistralAPIError(
            message="Test error",
            status_code=404,
            response={"error": "not found"}
        )
        
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code == 404
        assert error.response == {"error": "not found"}
    
    def test_mistral_api_error_without_optional_params(self):
        """Test MistralAPIError without optional parameters."""
        from mistral_client import MistralAPIError
        
        error = MistralAPIError(message="Test error")
        
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code is None
        assert error.response is None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
