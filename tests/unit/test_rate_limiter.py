"""
CoH1 × Mistral AI Mod - Unit Tests for Cost/Rate Limiter

Comprehensive unit tests for the rate_limiter.py module.

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-26
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# Add python directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

# Import commonly used classes for convenience
from rate_limiter import (
    CostRateLimiter, CallType, RateLimitResult, RateLimitConfig,
    CallRecord, BudgetStats, BudgetResetPolicy
)


# ============================================
# Test Fixtures
# ============================================

@pytest.fixture
def rate_limit_config():
    """Create a test configuration for rate limiter."""
    from rate_limiter import RateLimitConfig
    return RateLimitConfig(
        enabled=True,
        max_calls_per_match=200,
        max_tokens_per_match=100000,
        max_calls_per_minute=30,
        max_calls_per_second=5,
        urgent_calls_share_budget=True,
        token_cost_per_call=1000,
        budget_reset_policy="per_match",
        min_interval=0.1,
        urgent_min_interval=0.05,
        adaptive_rate_limiting=True,
        cooldown_factor=2.0
    )


@pytest.fixture
def rate_limiter(rate_limit_config):
    """Create a rate limiter for testing."""
    from rate_limiter import CostRateLimiter
    return CostRateLimiter(rate_limit_config)


@pytest.fixture
def disabled_rate_limiter():
    """Create a disabled rate limiter for testing."""
    from rate_limiter import CostRateLimiter, RateLimitConfig
    config = RateLimitConfig(enabled=False)
    return CostRateLimiter(config)


@pytest.fixture
def mock_call_record():
    """Create a mock call record."""
    from rate_limiter import CallRecord
    return CallRecord(
        call_type="strategic",
        timestamp=time.time(),
        game_time=100.0,
        call_id="test_call_001",
        model="mistral-small",
        tokens_used=1000,
        latency=0.5,
        success=True,
        error=None
    )


# ============================================
# Test Classes
# ============================================


# ============================================
# CallRecord Tests
# ============================================

class TestCallRecord:
    """Tests for CallRecord dataclass."""
    
    def test_call_record_creation(self):
        """Test creating a CallRecord."""
        from rate_limiter import CallRecord
        
        record = CallRecord(
            call_type="strategic",
            timestamp=1000.0,
            game_time=120.5,
            call_id="call_001",
            model="mistral-small",
            tokens_used=1000,
            latency=0.5,
            success=True
        )
        
        assert record.call_type == "strategic"
        assert record.timestamp == 1000.0
        assert record.game_time == 120.5
        assert record.call_id == "call_001"
        assert record.model == "mistral-small"
        assert record.tokens_used == 1000
        assert record.latency == 0.5
        assert record.success == True
        assert record.error is None
    
    def test_call_record_with_error(self):
        """Test creating a CallRecord with error."""
        from rate_limiter import CallRecord
        
        record = CallRecord(
            call_type="urgent",
            timestamp=1000.0,
            game_time=120.5,
            call_id="call_002",
            model="mistral-large",
            tokens_used=2000,
            latency=1.0,
            success=False,
            error="Rate limit exceeded"
        )
        
        assert record.success == False
        assert record.error == "Rate limit exceeded"
    
    def test_call_record_to_dict(self):
        """Test converting CallRecord to dictionary."""
        from rate_limiter import CallRecord
        
        record = CallRecord(
            call_type="test",
            timestamp=1000.0,
            game_time=0.0,
            call_id="test_001",
            tokens_used=500
        )
        
        result = record.to_dict()
        
        assert result["call_type"] == "test"
        assert result["timestamp"] == 1000.0
        assert result["game_time"] == 0.0
        assert result["call_id"] == "test_001"
        assert result["tokens_used"] == 500
    
    def test_call_record_from_dict(self):
        """Test creating CallRecord from dictionary."""
        from rate_limiter import CallRecord
        
        data = {
            "call_type": "strategic",
            "timestamp": 2000.0,
            "game_time": 200.0,
            "call_id": "call_003",
            "model": "mistral-small",
            "tokens_used": 1500,
            "latency": 0.3,
            "success": True,
            "error": None
        }
        
        record = CallRecord.from_dict(data)
        
        assert record.call_type == "strategic"
        assert record.timestamp == 2000.0
        assert record.game_time == 200.0
        assert record.tokens_used == 1500


# ============================================
# BudgetStats Tests
# ============================================

class TestBudgetStats:
    """Tests for BudgetStats dataclass."""
    
    def test_budget_stats_defaults(self):
        """Test BudgetStats default values."""
        from rate_limiter import BudgetStats
        
        stats = BudgetStats()
        
        assert stats.total_calls == 0
        assert stats.strategic_calls == 0
        assert stats.urgent_calls == 0
        assert stats.test_calls == 0
        assert stats.total_tokens == 0
        assert stats.total_latency == 0.0
        assert stats.avg_latency == 0.0
        assert stats.success_rate == 1.0
        assert stats.remaining_budget == 0
        assert stats.remaining_tokens == 0
    
    def test_budget_stats_with_values(self):
        """Test BudgetStats with custom values."""
        from rate_limiter import BudgetStats
        
        stats = BudgetStats(
            total_calls=100,
            strategic_calls=80,
            urgent_calls=15,
            test_calls=5,
            total_tokens=100000,
            total_latency=50.0,
            avg_latency=0.5,
            success_rate=0.95,
            remaining_budget=100,
            remaining_tokens=50000
        )
        
        assert stats.total_calls == 100
        assert stats.strategic_calls == 80
        assert stats.remaining_budget == 100
    
    def test_budget_stats_to_dict(self):
        """Test converting BudgetStats to dictionary."""
        from rate_limiter import BudgetStats
        
        stats = BudgetStats(
            total_calls=50,
            strategic_calls=40,
            urgent_calls=10
        )
        
        result = stats.to_dict()
        
        assert result["total_calls"] == 50
        assert result["strategic_calls"] == 40
        assert result["urgent_calls"] == 10


# ============================================
# RateLimitConfig Tests
# ============================================

class TestRateLimitConfig:
    """Tests for RateLimitConfig dataclass."""
    
    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig default values."""
        from rate_limiter import RateLimitConfig
        
        config = RateLimitConfig()
        
        assert config.enabled == True
        assert config.max_calls_per_match == 200
        assert config.max_tokens_per_match == 100000
        assert config.max_calls_per_minute == 30
        assert config.max_calls_per_second == 1
        assert config.urgent_calls_share_budget == True
        assert config.token_cost_per_call == 1000
        assert config.budget_reset_policy == "per_match"
        assert config.min_interval == 0.5
        assert config.urgent_min_interval == 0.1
        assert config.adaptive_rate_limiting == True
        assert config.cooldown_factor == 2.0
    
    def test_rate_limit_config_custom_values(self):
        """Test RateLimitConfig with custom values."""
        from rate_limiter import RateLimitConfig
        
        config = RateLimitConfig(
            enabled=False,
            max_calls_per_match=500,
            max_tokens_per_match=500000,
            max_calls_per_minute=100,
            max_calls_per_second=10
        )
        
        assert config.enabled == False
        assert config.max_calls_per_match == 500
        assert config.max_calls_per_minute == 100
    
    def test_config_from_config_object(self):
        """Test creating config from configuration object."""
        from rate_limiter import RateLimitConfig
        from config import Configuration
        
        # Create a Configuration object
        config_obj = Configuration()
        
        # Create RateLimitConfig from it
        rate_config = RateLimitConfig.from_config(config_obj)
        
        assert rate_config is not None
        assert rate_config.max_calls_per_match > 0


# ============================================
# CostRateLimiter Tests - Basic Operations
# ============================================

class TestCostRateLimiterBasic:
    """Basic tests for CostRateLimiter."""
    
    def test_rate_limiter_creation(self, rate_limiter):
        """Test creating a CostRateLimiter."""
        assert rate_limiter is not None
        assert rate_limiter.config.enabled == True
        assert rate_limiter.get_budget_used() == 0
        assert rate_limiter.get_tokens_used() == 0
    
    def test_check_call_allowed(self, rate_limiter):
        """Test that first call is allowed."""
        from rate_limiter import CallType, RateLimitResult
        
        result = rate_limiter.check_call(CallType.STRATEGIC, tokens=1000, game_time=0.0)
        
        assert result == RateLimitResult.ALLOWED
    
    def test_check_call_disabled(self, disabled_rate_limiter):
        """Test that calls are allowed when rate limiting is disabled."""
        from rate_limiter import CallType, RateLimitResult
        
        result = disabled_rate_limiter.check_call(CallType.STRATEGIC, tokens=1000, game_time=0.0)
        
        assert result == RateLimitResult.DISABLED
    
    def test_is_allowed_convenience(self, rate_limiter):
        """Test is_allowed convenience method."""
        from rate_limiter import CallType
        
        assert rate_limiter.is_allowed(CallType.STRATEGIC) == True
    
    def test_record_call(self, rate_limiter):
        """Test recording a call."""
        from rate_limiter import CallType
        
        call_id = rate_limiter.record_call(
            CallType.STRATEGIC,
            tokens_used=1000,
            latency=0.5,
            success=True,
            model="mistral-small",
            game_time=100.0
        )
        
        assert call_id is not None
        assert len(call_id) > 0
        assert rate_limiter.get_budget_used() == 1
        assert rate_limiter.get_tokens_used() == 1000
    
    def test_check_and_record(self, rate_limiter):
        """Test check_and_record convenience method."""
        from rate_limiter import CallType
        
        call_id = rate_limiter.check_and_record(
            CallType.STRATEGIC,
            tokens=1000,
            game_time=100.0,
            latency=0.5,
            success=True,
            model="mistral-small"
        )
        
        assert call_id is not None
        assert rate_limiter.get_budget_used() == 1
    
    def test_check_and_record_not_allowed(self, rate_limiter):
        """Test check_and_record when call is not allowed."""
        from rate_limiter import CallType
        
        # Use up the budget
        for _ in range(200):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        # Next call should not be allowed
        call_id = rate_limiter.check_and_record(CallType.STRATEGIC, tokens=1000)
        
        assert call_id is None


# ============================================
# CostRateLimiter Tests - Budget Management
# ============================================

class TestCostRateLimiterBudget:
    """Tests for budget management."""
    
    def test_budget_tracking(self, rate_limiter):
        """Test that budget is tracked correctly."""
        from rate_limiter import CallType
        
        # Record some calls
        for _ in range(10):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        assert rate_limiter.get_budget_used() == 10
        assert rate_limiter.get_tokens_used() == 10000
    
    def test_budget_exceeded(self, rate_limit_config):
        """Test that budget exceeded is detected."""
        from rate_limiter import CostRateLimiter, CallType, RateLimitResult, RateLimitConfig
        
        # Use a small budget and disable per-second/per-minute limits
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_match=5,
            max_calls_per_minute=0,
            max_calls_per_second=0,
            max_tokens_per_match=10000,
            token_cost_per_call=1000,
            min_interval=0.0
        )
        limiter = CostRateLimiter(config)
        
        # Use up the budget
        for _ in range(5):
            limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        # Next call should be budget exceeded
        result = limiter.check_call(CallType.STRATEGIC, tokens=1000)
        
        assert result == RateLimitResult.BUDGET_EXCEEDED
    
    def test_token_budget_exceeded(self, rate_limit_config):
        """Test that token budget exceeded is detected."""
        from rate_limiter import CostRateLimiter, CallType, RateLimitResult
        
        # Use a small token budget and disable per-second/per-minute limits
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_match=1000,
            max_calls_per_minute=0,
            max_calls_per_second=0,
            max_tokens_per_match=5000,
            token_cost_per_call=1000,
            min_interval=0.0
        )
        limiter = CostRateLimiter(config)
        
        # Use up the token budget
        for _ in range(5):
            limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        # Next call should be budget exceeded (token-wise)
        result = limiter.check_call(CallType.STRATEGIC, tokens=1000)
        
        assert result == RateLimitResult.BUDGET_EXCEEDED
    
    def test_remaining_budget(self, rate_limiter):
        """Test remaining budget calculation."""
        from rate_limiter import CallType
        
        # Use some budget
        for _ in range(50):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        remaining = rate_limiter.get_remaining_budget()
        
        assert remaining == 150  # 200 - 50 = 150
    
    def test_remaining_tokens(self, rate_limiter):
        """Test remaining tokens calculation."""
        from rate_limiter import CallType
        
        # Use some tokens
        for _ in range(50):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        remaining = rate_limiter.get_remaining_tokens()
        
        assert remaining == 50000  # 100000 - 50000 = 50000


# ============================================
# CostRateLimiter Tests - Rate Limiting
# ============================================

class TestCostRateLimiterRateLimiting:
    """Tests for rate limiting functionality."""
    
    def test_min_interval_rate_limiting(self, rate_limit_config):
        """Test minimum interval rate limiting."""
        from rate_limiter import CostRateLimiter, CallType, RateLimitResult
        
        config = RateLimitConfig(
            enabled=True,
            min_interval=1.0,  # 1 second minimum
            max_calls_per_match=1000
        )
        limiter = CostRateLimiter(config)
        
        # First call should be allowed
        assert limiter.check_call(CallType.STRATEGIC) == RateLimitResult.ALLOWED
        
        # Record the call
        limiter.record_call(CallType.STRATEGIC)
        
        # Immediate second call should be rate limited
        assert limiter.check_call(CallType.STRATEGIC) == RateLimitResult.RATE_LIMITED
    
    def test_per_second_rate_limiting(self, rate_limit_config):
        """Test per-second rate limiting."""
        from rate_limiter import CostRateLimiter, CallType, RateLimitResult
        
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_second=1,
            max_calls_per_match=1000,
            min_interval=0.0  # No minimum interval
        )
        limiter = CostRateLimiter(config)
        
        # Make a call
        limiter.record_call(CallType.STRATEGIC)
        
        # Second call in same second should be rate limited
        result = limiter.check_call(CallType.STRATEGIC)
        
        assert result == RateLimitResult.RATE_LIMITED
    
    def test_per_minute_rate_limiting(self, rate_limit_config):
        """Test per-minute rate limiting."""
        from rate_limiter import CostRateLimiter, CallType, RateLimitResult
        
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_minute=2,
            max_calls_per_match=1000,
            min_interval=0.0
        )
        limiter = CostRateLimiter(config)
        
        # Make 2 calls
        limiter.record_call(CallType.STRATEGIC)
        limiter.record_call(CallType.STRATEGIC)
        
        # Third call should be rate limited
        result = limiter.check_call(CallType.STRATEGIC)
        
        assert result == RateLimitResult.RATE_LIMITED
    
    def test_urgent_call_different_interval(self, rate_limit_config):
        """Test that urgent calls have different minimum interval."""
        from rate_limiter import CostRateLimiter, CallType, RateLimitResult
        import time
        
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_second=0,  # Disable per-second limiting
            max_calls_per_minute=0,  # Disable per-minute limiting
            min_interval=1.0,
            urgent_min_interval=0.0,  # Allow immediate urgent calls
            max_calls_per_match=1000
        )
        limiter = CostRateLimiter(config)
        
        # First urgent call
        assert limiter.check_call(CallType.URGENT) == RateLimitResult.ALLOWED
        limiter.record_call(CallType.URGENT)
        
        # Second urgent call should be allowed (shorter interval)
        assert limiter.check_call(CallType.URGENT) == RateLimitResult.ALLOWED
    
    @patch('time.time')
    def test_minute_reset(self, mock_time, rate_limit_config):
        """Test that minute counter resets after a minute."""
        from rate_limiter import CostRateLimiter, CallType, RateLimitResult
        
        # Set up mock to return a float
        mock_time.return_value = 1000.0
        
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_minute=1,
            max_calls_per_match=1000,
            min_interval=0.0
        )
        limiter = CostRateLimiter(config)
        
        # Make a call
        limiter.record_call(CallType.STRATEGIC)
        
        # Mock time to be 61 seconds later
        mock_time.return_value = 1000.0 + 61.0
        
        # Should be allowed again
        result = limiter.check_call(CallType.STRATEGIC)
        
        assert result == RateLimitResult.ALLOWED


# ============================================
# CostRateLimiter Tests - Budget Reset
# ============================================

class TestCostRateLimiterBudgetReset:
    """Tests for budget reset functionality."""
    
    def test_start_match(self, rate_limiter):
        """Test starting a new match resets budget."""
        from rate_limiter import CallType
        
        # Use some budget
        for _ in range(50):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        assert rate_limiter.get_budget_used() == 50
        assert rate_limiter.get_tokens_used() == 50000
        
        # Start new match
        rate_limiter.start_match()
        
        assert rate_limiter.get_budget_used() == 0
        assert rate_limiter.get_tokens_used() == 0
    
    def test_end_match(self, rate_limiter, caplog):
        """Test ending a match."""
        from rate_limiter import CallType
        
        # Use some budget
        rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000, success=True)
        
        # End match (should log)
        rate_limiter.end_match()
        
        # Check that budget is still there (end_match doesn't reset)
        assert rate_limiter.get_budget_used() == 1
    
    def test_manual_budget_reset(self, rate_limiter):
        """Test manual budget reset."""
        from rate_limiter import CallType, BudgetResetPolicy
        
        # Use some budget
        for _ in range(50):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        # Reset budget
        rate_limiter.reset_budget(BudgetResetPolicy.PER_MATCH.value)
        
        assert rate_limiter.get_budget_used() == 0


# ============================================
# CostRateLimiter Tests - Adaptive Rate Limiting
# ============================================

class TestCostRateLimiterAdaptive:
    """Tests for adaptive rate limiting."""
    
    def test_notify_rate_limited(self, rate_limiter):
        """Test notifying rate limiter of rate limit."""
        assert rate_limiter.is_rate_limited() == False
        
        # Notify of rate limit
        rate_limiter.notify_rate_limited(retry_after=10.0)
        
        assert rate_limiter.is_rate_limited() == True
        assert rate_limiter.get_rate_limit_end_time() > time.time()
    
    def test_clear_rate_limit(self, rate_limiter):
        """Test clearing rate limit state."""
        rate_limiter.notify_rate_limited(retry_after=10.0)
        assert rate_limiter.is_rate_limited() == True
        
        rate_limiter.clear_rate_limit()
        
        assert rate_limiter.is_rate_limited() == False
    
    @patch('rate_limiter.time.time')
    def test_rate_limit_expiry(self, mock_time, rate_limit_config):
        """Test that rate limit expires after time."""
        from rate_limiter import CostRateLimiter
        
        # Set initial time
        initial_time = 1000.0
        mock_time.return_value = initial_time
        
        config = RateLimitConfig()  # Use default config
        limiter = CostRateLimiter(config)
        
        limiter.notify_rate_limited(retry_after=5.0)
        assert limiter.is_rate_limited() == True
        
        # Mock time to be after the cooldown end time
        # Cooldown end time is: current_time + max(retry_after, 10.0)
        # So: 1000.0 + max(5.0, 10.0) = 1000.0 + 10.0 = 1010.0
        # Set time to 1011.0 to be past the cooldown
        mock_time.return_value = 1011.0
        
        # Should no longer be rate limited
        assert limiter.is_rate_limited() == False


# ============================================
# CostRateLimiter Tests - Statistics
# ============================================

class TestCostRateLimiterStats:
    """Tests for statistics tracking."""
    
    def test_get_stats(self, rate_limiter):
        """Test getting statistics."""
        from rate_limiter import CallType
        
        # Record some calls
        rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000, latency=0.5, success=True)
        rate_limiter.record_call(CallType.STRATEGIC, tokens_used=2000, latency=0.3, success=True)
        rate_limiter.record_call(CallType.URGENT, tokens_used=1500, latency=0.2, success=False)
        
        stats = rate_limiter.get_stats()
        
        assert stats.total_calls == 3
        assert stats.strategic_calls == 2
        assert stats.urgent_calls == 1
        assert stats.total_tokens == 4500
        assert stats.total_latency == pytest.approx(1.0, abs=0.01)
        assert stats.avg_latency == pytest.approx(0.333, abs=0.01)
        assert stats.success_rate == pytest.approx(0.666, abs=0.01)
    
    def test_get_recent_calls(self, rate_limiter):
        """Test getting recent calls."""
        from rate_limiter import CallType
        
        # Record some calls
        for i in range(10):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        recent = rate_limiter.get_recent_calls(5)
        
        assert len(recent) == 5
    
    def test_get_call_by_id(self, rate_limiter):
        """Test getting call by ID."""
        from rate_limiter import CallType
        
        call_id = rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        record = rate_limiter.get_call_by_id(call_id)
        
        assert record is not None
        assert record.call_id == call_id
    
    def test_get_call_by_invalid_id(self, rate_limiter):
        """Test getting call by invalid ID."""
        record = rate_limiter.get_call_by_id("invalid_id")
        
        assert record is None
    
    def test_clear_history(self, rate_limiter):
        """Test clearing call history."""
        from rate_limiter import CallType
        
        # Record some calls
        for _ in range(10):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        
        assert rate_limiter.get_stats().total_calls == 10
        
        # Clear history
        rate_limiter.clear_history()
        
        assert rate_limiter.get_stats().total_calls == 0


# ============================================
# CostRateLimiter Tests - Wait Functionality
# ============================================

class TestCostRateLimiterWait:
    """Tests for wait functionality."""
    
    @patch('rate_limiter.time.time')
    @patch('rate_limiter.time.sleep')
    def test_wait_for_available(self, mock_sleep, mock_time, rate_limit_config):
        """Test waiting for available call (min_interval)."""
        from rate_limiter import CostRateLimiter, CallType
        import time as time_module
        
        # Set initial time
        initial_time = 1000.0
        mock_time.return_value = initial_time
        
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_match=1000,  # Large budget so we don't hit it
            min_interval=1.0
        )
        limiter = CostRateLimiter(config)
        
        # Make first call
        limiter.record_call(CallType.STRATEGIC)
        
        # Mock time to return time after interval for check
        mock_time.return_value = initial_time + 2.0
        
        # Should be available since interval has passed
        result = limiter.wait_for_available(CallType.STRATEGIC, timeout=10.0)
        
        assert result == True
    
    def test_wait_for_available_disabled(self, disabled_rate_limiter):
        """Test waiting when rate limiting is disabled."""
        result = disabled_rate_limiter.wait_for_available("strategic", timeout=1.0)
        
        assert result == True
    
    def test_wait_for_available_budget_exceeded(self, rate_limit_config):
        """Test waiting when budget is exceeded."""
        from rate_limiter import CostRateLimiter, CallType
        
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_match=1,
            min_interval=0.0
        )
        limiter = CostRateLimiter(config)
        
        # Use up the budget
        limiter.record_call(CallType.STRATEGIC)
        
        # Should not wait for budget exceeded
        result = limiter.wait_for_available(CallType.STRATEGIC, timeout=10.0)
        
        assert result == False


# ============================================
# CostRateLimiter Tests - Configuration
# ============================================

class TestCostRateLimiterConfiguration:
    """Tests for configuration management."""
    
    def test_get_config(self, rate_limiter):
        """Test getting configuration."""
        config = rate_limiter.get_config()
        
        assert config is not None
        assert config.enabled == True
        assert config.max_calls_per_match == 200
    
    def test_set_config(self, rate_limiter):
        """Test updating configuration."""
        from rate_limiter import RateLimitConfig
        
        new_config = RateLimitConfig(
            enabled=False,
            max_calls_per_match=500
        )
        
        rate_limiter.set_config(new_config)
        
        config = rate_limiter.get_config()
        assert config.enabled == False
        assert config.max_calls_per_match == 500


# ============================================
# CostRateLimiter Tests - Thread Safety
# ============================================

class TestCostRateLimiterThreadSafety:
    """Tests for thread safety."""
    
    def test_concurrent_checks(self, rate_limit_config):
        """Test concurrent check operations."""
        from rate_limiter import CostRateLimiter, CallType, RateLimitResult
        
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_match=1000,
            min_interval=0.0
        )
        limiter = CostRateLimiter(config)
        
        results = []
        errors = []
        
        def check_call(thread_id):
            try:
                for _ in range(10):
                    result = limiter.check_call(CallType.STRATEGIC)
                    results.append(result == RateLimitResult.ALLOWED)
            except Exception as e:
                errors.append(e)
        
        # Create and start threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=check_call, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Check no errors
        assert len(errors) == 0
        assert len(results) == 50
    
    def test_concurrent_records(self, rate_limit_config):
        """Test concurrent record operations."""
        from rate_limiter import CostRateLimiter, CallType
        
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_match=1000,
            min_interval=0.0
        )
        limiter = CostRateLimiter(config)
        
        errors = []
        
        def record_calls(thread_id):
            try:
                for i in range(10):
                    limiter.record_call(
                        CallType.STRATEGIC,
                        tokens_used=1000,
                        latency=0.1,
                        success=True,
                        model="test",
                        game_time=float(thread_id * 100 + i)
                    )
            except Exception as e:
                errors.append(e)
        
        # Create and start threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=record_calls, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Check no errors
        assert len(errors) == 0
        
        # Check calls were recorded
        stats = limiter.get_stats()
        assert stats.total_calls == 50


# ============================================
# CostRateLimiter Tests - Edge Cases
# ============================================

class TestCostRateLimiterEdgeCases:
    """Tests for edge cases."""
    
    def test_zero_max_calls(self, rate_limit_config):
        """Test with zero max calls."""
        from rate_limiter import CostRateLimiter, CallType, RateLimitResult
        
        config = RateLimitConfig(
            enabled=True,
            max_calls_per_match=0,
            max_tokens_per_match=0
        )
        limiter = CostRateLimiter(config)
        
        result = limiter.check_call(CallType.STRATEGIC)
        
        assert result == RateLimitResult.BUDGET_EXCEEDED
    
    def test_negative_budget(self, rate_limiter):
        """Test that negative values are handled."""
        from rate_limiter import CallType
        
        # First record a call with positive tokens
        rate_limiter.record_call(CallType.STRATEGIC, tokens_used=200)
        
        # Then record a call with negative tokens
        rate_limiter.record_call(CallType.STRATEGIC, tokens_used=-100)
        
        # Tokens used should be 100 (200 - 100)
        assert rate_limiter.get_tokens_used() == 100
        # Remaining tokens should be adjusted accordingly
        assert rate_limiter.get_remaining_tokens() == rate_limiter.config.max_tokens_per_match - 100
    
    def test_string_call_type(self, rate_limiter):
        """Test using string call type."""
        result = rate_limiter.check_call("strategic", tokens=1000)
        
        assert result.name == "ALLOWED"
    
    def test_large_token_values(self, rate_limiter):
        """Test with large token values."""
        from rate_limiter import CallType
        
        # Record call with large token count
        rate_limiter.record_call(CallType.STRATEGIC, tokens_used=999999)
        
        assert rate_limiter.get_tokens_used() == 999999
    
    def test_zero_latency(self, rate_limiter):
        """Test with zero latency."""
        from rate_limiter import CallType
        
        call_id = rate_limiter.record_call(
            CallType.STRATEGIC,
            tokens_used=1000,
            latency=0.0
        )
        
        assert call_id is not None
        stats = rate_limiter.get_stats()
        assert stats.total_latency == 0.0


# ============================================
# Factory Function Tests
# ============================================

class TestFactoryFunctions:
    """Tests for factory functions."""
    
    def test_create_rate_limiter(self):
        """Test creating a rate limiter via factory."""
        from rate_limiter import create_rate_limiter
        
        limiter = create_rate_limiter()
        
        assert limiter is not None
        assert limiter.get_budget_used() == 0
    
    def test_get_rate_limiter_singleton(self):
        """Test singleton pattern."""
        from rate_limiter import get_rate_limiter, reset_rate_limiter
        
        # Reset first
        reset_rate_limiter()
        
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        assert limiter1 is limiter2
    
    def test_reset_rate_limiter(self):
        """Test resetting the singleton."""
        from rate_limiter import get_rate_limiter, reset_rate_limiter
        
        limiter1 = get_rate_limiter()
        limiter1.record_call("strategic", tokens_used=1000)
        
        reset_rate_limiter()
        
        limiter2 = get_rate_limiter()
        
        assert limiter2.get_budget_used() == 0
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        from rate_limiter import reset_rate_limiter, check_rate_limit, record_api_call, get_rate_limit_stats, start_new_match, end_current_match
        
        # Reset first
        reset_rate_limiter()
        
        # Check rate limit
        assert check_rate_limit("strategic") == True
        
        # Record call
        call_id = record_api_call("strategic", tokens_used=1000, success=True)
        assert call_id is not None
        
        # Get stats
        stats = get_rate_limit_stats()
        assert stats.total_calls == 1
        
        # Start new match
        start_new_match()
        
        # End current match
        end_current_match()


# ============================================
# Context Manager Tests
# ============================================

class TestContextManager:
    """Tests for context manager support."""
    
    def test_context_manager(self, rate_limiter):
        """Test using rate limiter as context manager."""
        with rate_limiter:
            # Should work inside context
            assert rate_limiter.check_call(CallType.STRATEGIC) == RateLimitResult.ALLOWED
        
        # Should still work outside context
        assert rate_limiter.check_call(CallType.STRATEGIC) == RateLimitResult.ALLOWED
