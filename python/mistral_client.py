"""
CoH1 × Mistral AI Mod - Mistral API Client

Provides Python client for connecting to Mistral API with support for Large and Small models.
Implements secure API key handling via environment variables.

Features:
- API connection and authentication via environment variable
- Model selection (Large/Small)
- Error handling for API failures
- JSON mode configuration
- Rate limiting awareness

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-11-21

Security Note:
- API key is loaded from .env file ONLY
- Never hardcoded in source
- Never logged or outputted
"""

import os
import json
import time
import logging
import requests
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# ============================================
# Configuration
# ============================================

class MistralModel(Enum):
    """Supported Mistral models."""
    SMALL = "mistral-small-latest"
    LARGE = "mistral-large-latest"
    MEDIUM = "mistral-medium-latest"  # If available


class MistralAPIError(Exception):
    """Exception raised for Mistral API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


@dataclass
class MistralResponse:
    """Container for Mistral API response."""
    content: str
    model: str
    finish_reason: str
    usage: Dict[str, int]
    response_time: float
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "response_time": self.response_time,
            "timestamp": self.timestamp
        }


@dataclass
class APIStats:
    """Statistics for API usage tracking."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_tokens: int = 0
    total_response_time: float = 0.0
    last_call_time: float = 0.0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    
    def record_call(self, success: bool, tokens: int, response_time: float, 
                   error_type: Optional[str] = None):
        """Record a call to the statistics."""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error_type:
                self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        self.total_tokens += tokens
        self.total_response_time += response_time
        self.last_call_time = time.time()
    
    def get_avg_response_time(self) -> float:
        """Get average response time."""
        if self.total_calls == 0:
            return 0.0
        return self.total_response_time / self.total_calls
    
    def get_success_rate(self) -> float:
        """Get success rate."""
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls


# ============================================
# Mistral API Client
# ============================================

class MistralClient:
    """
    Client for Mistral AI API.
    
    Handles all communication with the Mistral API, including:
    - Authentication via API key from environment
    - Model selection
    - Chat completions
    - JSON mode configuration
    - Error handling
    - Rate limiting awareness
    
    Security:
    - API key loaded from MISTRAL_API_KEY environment variable ONLY
    - Key is never stored in the object
    - Key is never logged
    """
    
    # API endpoints
    API_BASE_URL = "https://api.mistral.ai/v1"
    CHAT_COMPLETIONS_ENDPOINT = "/chat/completions"
    MODELS_ENDPOINT = "/models"
    
    # Default settings
    DEFAULT_MODEL = MistralModel.SMALL
    DEFAULT_TIMEOUT = 30.0  # seconds
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0  # seconds
    
    def __init__(self, model: MistralModel = DEFAULT_MODEL, 
                 timeout: float = DEFAULT_TIMEOUT,
                 max_retries: int = DEFAULT_MAX_RETRIES,
                 retry_delay: float = DEFAULT_RETRY_DELAY,
                 json_mode: bool = True):
        """
        Initialize Mistral API client.
        
        Args:
            model: Mistral model to use (SMALL, LARGE, MEDIUM)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
            retry_delay: Delay between retries in seconds
            json_mode: Whether to request JSON output format
        """
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.json_mode = json_mode
        
        self.logger = logging.getLogger(__name__)
        self.stats = APIStats()
        self._session = requests.Session()
        
        # Validate API key is available
        self._validate_api_key()
        
        self.logger.info(f"MistralClient initialized with model: {self.model.value}")
        if json_mode:
            self.logger.info("JSON mode enabled")
    
    def _validate_api_key(self) -> None:
        """Validate that API key is available in environment."""
        api_key = self._get_api_key()
        if not api_key or not api_key.startswith("mstrl_"):
            raise ValueError(
                "Mistral API key not found or invalid. "
                "Please set MISTRAL_API_KEY in your .env file."
            )
    
    def _get_api_key(self) -> str:
        """
        Get API key from environment variable.
        
        Returns:
            API key string
            
        Raises:
            ValueError: If API key is not set
        """
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            # Try multiple locations for .env file
            env_paths = [
                Path(__file__).parent.parent / ".env",  # Project root
                Path(__file__).parent.parent.parent / ".env",  # Parent of project root
                Path.cwd() / ".env",  # Current working directory
                Path.cwd().parent / ".env",  # Parent of current directory
            ]
            
            for env_path in env_paths:
                if env_path.exists():
                    try:
                        from dotenv import load_dotenv
                        load_dotenv(env_path)
                        api_key = os.getenv("MISTRAL_API_KEY")
                        if api_key:
                            break
                    except ImportError:
                        # dotenv not installed, try manual loading
                        try:
                            with open(env_path, 'r') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#'):
                                        if '=' in line:
                                            key, value = line.split('=', 1)
                                            if key.strip() == "MISTRAL_API_KEY":
                                                api_key = value.strip()
                                                break
                            if api_key:
                                break
                        except:
                            pass
        
        if not api_key:
            raise ValueError(
                "Mistral API key not found. "
                "Please set MISTRAL_API_KEY in your .env file at the project root."
            )
        return api_key
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self._get_api_key()}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(self, messages: List[Dict[str, Any]], 
                        model: Optional[MistralModel] = None,
                        temperature: float = 0.7,
                        max_tokens: int = 2048,
                        top_p: float = 0.9,
                        **kwargs) -> MistralResponse:
        """
        Send a chat completion request to Mistral API.
        
        Args:
            messages: List of message dictionaries (role, content)
            model: Override default model
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens in response
            top_p: Nucleus sampling parameter
            **kwargs: Additional parameters
            
        Returns:
            MistralResponse with the completion
            
        Raises:
            MistralAPIError: If API request fails
        """
        model = model or self.model
        
        # Prepare request body
        request_body = {
            "model": model.value,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        # Add JSON mode if enabled
        if self.json_mode:
            request_body["response_format"] = {"type": "json_object"}
        
        # Add any additional kwargs
        request_body.update(kwargs)
        
        # Make request with retries
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self._session.post(
                    f"{self.API_BASE_URL}{self.CHAT_COMPLETIONS_ENDPOINT}",
                    headers=self._get_headers(),
                    json=request_body,
                    timeout=self.timeout
                )
                
                response_time = time.time() - start_time
                
                # Handle response
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract choice
                    if "choices" not in data or len(data["choices"]) == 0:
                        raise MistralAPIError(
                            "No choices in response",
                            response.status_code,
                            data
                        )
                    
                    choice = data["choices"][0]
                    content = choice.get("message", {}).get("content", "")
                    finish_reason = choice.get("finish_reason", "unknown")
                    usage = data.get("usage", {})
                    
                    # Record statistics
                    tokens_used = usage.get("total_tokens", 0)
                    self.stats.record_call(
                        success=True,
                        tokens=tokens_used,
                        response_time=response_time
                    )
                    
                    # Log success (without API key)
                    self.logger.debug(
                        f"API call successful: model={model.value}, "
                        f"tokens={tokens_used}, time={response_time:.2f}s"
                    )
                    
                    return MistralResponse(
                        content=content,
                        model=model.value,
                        finish_reason=finish_reason,
                        usage=usage,
                        response_time=response_time,
                        timestamp=time.time()
                    )
                
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = response.headers.get("retry-after", self.retry_delay)
                    if attempt < self.max_retries - 1:
                        self.logger.warning(
                            f"Rate limited (attempt {attempt + 1}/{self.max_retries}). "
                            f"Retrying in {retry_after}s..."
                        )
                        time.sleep(float(retry_after))
                        continue
                    else:
                        last_error = MistralAPIError(
                            f"Rate limited after {self.max_retries} attempts",
                            response.status_code,
                            response.json() if response.content else None
                        )
                
                elif response.status_code == 401:
                    # Authentication error
                    last_error = MistralAPIError(
                        "Authentication failed - invalid API key",
                        response.status_code,
                        response.json() if response.content else None
                    )
                    break
                
                else:
                    # Other error
                    error_data = response.json() if response.content else None
                    last_error = MistralAPIError(
                        f"API request failed with status {response.status_code}",
                        response.status_code,
                        error_data
                    )
                    
                    # Record failure
                    self.stats.record_call(
                        success=False,
                        tokens=0,
                        response_time=response_time,
                        error_type=str(response.status_code)
                    )
                    
                    if attempt < self.max_retries - 1:
                        self.logger.warning(
                            f"Attempt {attempt + 1} failed: {last_error.message}. "
                            f"Retrying in {self.retry_delay}s..."
                        )
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        break
                        
            except requests.exceptions.Timeout:
                last_error = MistralAPIError(
                    f"Request timed out after {self.timeout}s",
                    None
                )
                self.stats.record_call(
                    success=False,
                    tokens=0,
                    response_time=time.time() - start_time,
                    error_type="timeout"
                )
                if attempt < self.max_retries - 1:
                    self.logger.warning(
                        f"Attempt {attempt + 1} timed out. Retrying..."
                    )
                    time.sleep(self.retry_delay)
                    continue
                else:
                    break
                    
            except requests.exceptions.RequestException as e:
                last_error = MistralAPIError(f"Request error: {str(e)}")
                self.stats.record_call(
                    success=False,
                    tokens=0,
                    response_time=time.time() - start_time,
                    error_type="request_error"
                )
                break
        
        # If we get here, all attempts failed
        self.logger.error(f"All {self.max_retries} attempts failed")
        raise last_error or MistralAPIError("Unknown error")
    
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from Mistral API.
        
        Returns:
            List of model dictionaries
            
        Raises:
            MistralAPIError: If API request fails
        """
        try:
            response = self._session.get(
                f"{self.API_BASE_URL}{self.MODELS_ENDPOINT}",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                raise MistralAPIError(
                    f"Failed to get models: {response.status_code}",
                    response.status_code,
                    response.json() if response.content else None
                )
        except requests.exceptions.RequestException as e:
            raise MistralAPIError(f"Failed to get models: {str(e)}")
    
    def set_model(self, model: MistralModel) -> None:
        """Set the model to use for subsequent requests."""
        self.model = model
        self.logger.info(f"Model set to: {model.value}")
    
    def get_model(self) -> MistralModel:
        """Get the current model."""
        return self.model
    
    def enable_json_mode(self, enabled: bool = True) -> None:
        """Enable or disable JSON output mode."""
        self.json_mode = enabled
        self.logger.info(f"JSON mode {'enabled' if enabled else 'disabled'}")
    
    def is_json_mode(self) -> bool:
        """Check if JSON mode is enabled."""
        return self.json_mode
    
    def get_stats(self) -> APIStats:
        """Get API statistics."""
        return self.stats
    
    def reset_stats(self) -> None:
        """Reset API statistics."""
        self.stats = APIStats()
    
    def close(self) -> None:
        """Close the client session."""
        self._session.close()
        self.logger.info("MistralClient session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ============================================
# Factory Functions
# ============================================

_default_client: Optional[MistralClient] = None


def get_mistral_client(model: MistralModel = MistralModel.SMALL,
                       json_mode: bool = True) -> MistralClient:
    """
    Get or create the default MistralClient singleton.
    
    Args:
        model: Mistral model to use
        json_mode: Whether to enable JSON mode
        
    Returns:
        MistralClient instance
    """
    global _default_client
    if _default_client is None:
        _default_client = MistralClient(model=model, json_mode=json_mode)
    return _default_client


def reset_mistral_client() -> None:
    """Reset the default MistralClient singleton."""
    global _default_client
    if _default_client is not None:
        _default_client.close()
    _default_client = None


def create_mistral_client(model: MistralModel = MistralModel.SMALL,
                          timeout: float = 30.0,
                          max_retries: int = 3,
                          json_mode: bool = True) -> MistralClient:
    """
    Create a new MistralClient instance.
    
    Args:
        model: Mistral model to use
        timeout: Request timeout
        max_retries: Maximum retries
        json_mode: Enable JSON mode
        
    Returns:
        New MistralClient instance
    """
    return MistralClient(
        model=model,
        timeout=timeout,
        max_retries=max_retries,
        json_mode=json_mode
    )


if __name__ == "__main__":
    # Test the client
    print("Testing MistralClient...")
    
    try:
        # Create client
        client = create_mistral_client(
            model=MistralModel.SMALL,
            json_mode=True
        )
        
        # Test getting models
        print("Fetching available models...")
        models = client.get_models()
        print(f"Found {len(models)} models")
        for model in models[:5]:  # Show first 5
            print(f"  - {model.get('id', 'unknown')}")
        
        # Test a simple chat completion
        print("\nTesting chat completion...")
        messages = [
            {"role": "user", "content": "What is 2+2?"}
        ]
        
        response = client.chat_completion(messages, max_tokens=100)
        print(f"Response: {response.content}")
        print(f"Model: {response.model}")
        print(f"Finish reason: {response.finish_reason}")
        print(f"Tokens used: {response.usage}")
        
        # Get stats
        stats = client.get_stats()
        print(f"\nStats: {stats.total_calls} calls, {stats.successful_calls} successful")
        
        client.close()
        print("\nMistralClient test completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
