"""
Phase 3: Cost/Rate Limiter Unit Tests

Tests for the rate_limiter module (already exists from Phase 2, but adding Phase 3 tests).

Author: Generated for Phase 3 pytest integration
Version: 1.0.0
Date: 2026-11-21
"""

import os
import sys
import json
import pytest
import time
from pathlib import Path
from unittest.mock import patch

# Add project root and python directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python"))


@pytest.fixture
def rate_limiter():
    """Create a rate limiter for testing."""
    from rate_limiter import CostRateLimiter
    
    limiter = CostRateLimiter(
        budget=1000,
        time_window=60.0,
        max_calls_per_window=100
    )
    yield limiter


@pytest.fixture
def strategist_rate_limiter():
    """Create a rate limiter with strategist settings."""
    from rate_limiter import CostRateLimiter, CallType
    
    limiter = CostRateLimiter(
        budget=200,  # Max calls per match
        time_window=10.0,  # Strategic tick interval
        max_calls_per_window=10
    )
    yield limiter


class TestRateLimiterInitialization:
    """Tests for rate limiter initialization."""
    
    def test_default_initialization(self, rate_limiter):
        """Test default rate limiter initialization."""
        assert rate_limiter.budget == 1000
        assert rate_limiter.time_window == 60.0
        assert rate_limiter.max_calls_per_window == 100
    
    def test_custom_initialization(self):
        """Test custom rate limiter initialization."""
        from rate_limiter import CostRateLimiter
        
        limiter = CostRateLimiter(
            budget=500,
            time_window=30.0,
            max_calls_per_window=50
        )
        
        assert limiter.budget == 500
        assert limiter.time_window == 30.0
        assert limiter.max_calls_per_window == 50
    
    def test_initial_stats(self, rate_limiter):
        """Test initial statistics."""
        stats = limiter.get_stats()
        
        assert stats['calls_made'] == 0
        assert stats['calls_allowed'] == 0
        assert stats['calls_blocked'] == 0
        assert stats['tokens_used'] == 0


class TestRateLimiterCallChecking:
    """Tests for rate limiter call checking."""
    
    def test_check_call_allowed(self, rate_limiter):
        """Test that calls are allowed within budget."""
        from rate_limiter import CallType
        
        result = rate_limiter.check_call(CallType.STRATEGIC)
        assert result == "allowed"
    
    def test_check_call_budget_exceeded(self, rate_limiter):
        """Test that calls are blocked when budget exceeded."""
        from rate_limiter import CallType
        
        # Use up all budget
        for _ in range(100):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=10, latency=0.1, success=True)
        
        result = rate_limiter.check_call(CallType.STRATEGIC)
        assert result == "budget_exceeded"
    
    def test_check_call_rate_limited(self, rate_limiter):
        """Test that calls are rate limited."""
        from rate_limiter import CallType
        
        # Make max calls in window
        for _ in range(100):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=1, latency=0.1, success=True)
        
        # Next call should be rate limited
        result = rate_limiter.check_call(CallType.STRATEGIC)
        assert result == "rate_limited"
    
    def test_urgent_calls_always_allowed(self, rate_limiter):
        """Test that urgent calls are always allowed."""
        from rate_limiter import CallType
        
        # Use up all budget
        for _ in range(100):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=10, latency=0.1, success=True)
        
        # Urgent call should still be allowed
        result = rate_limiter.check_call(CallType.URGENT)
        assert result == "allowed"


class TestRateLimiterRecording:
    """Tests for recording calls."""
    
    def test_record_call_success(self, rate_limiter):
        """Test recording a successful call."""
        from rate_limiter import CallType
        
        rate_limiter.record_call(
            call_type=CallType.STRATEGIC,
            tokens_used=10,
            latency=0.5,
            success=True
        )
        
        stats = rate_limiter.get_stats()
        assert stats['calls_made'] == 1
        assert stats['calls_allowed'] == 1
        assert stats['tokens_used'] == 10
    
    def test_record_call_failure(self, rate_limiter):
        """Test recording a failed call."""
        from rate_limiter import CallType
        
        rate_limiter.record_call(
            call_type=CallType.STRATEGIC,
            tokens_used=0,
            latency=0.1,
            success=False
        )
        
        stats = rate_limiter.get_stats()
        assert stats['calls_made'] == 1
        assert stats['calls_blocked'] == 1
    
    def test_record_multiple_calls(self, rate_limiter):
        """Test recording multiple calls."""
        from rate_limiter import CallType
        
        for i in range(10):
            rate_limiter.record_call(
                call_type=CallType.STRATEGIC,
                tokens_used=5,
                latency=0.1,
                success=True
            )
        
        stats = rate_limiter.get_stats()
        assert stats['calls_made'] == 10
        assert stats['calls_allowed'] == 10
        assert stats['tokens_used'] == 50


class TestRateLimiterStats:
    """Tests for rate limiter statistics."""
    
    def test_get_stats(self, rate_limiter):
        """Test getting statistics."""
        from rate_limiter import CallType
        
        rate_limiter.record_call(CallType.STRATEGIC, 10, 0.5, True)
        rate_limiter.record_call(CallType.STRATEGIC, 20, 0.3, True)
        rate_limiter.record_call(CallType.STRATEGIC, 0, 0.1, False)
        
        stats = rate_limiter.get_stats()
        
        assert stats['calls_made'] == 3
        assert stats['calls_allowed'] == 2
        assert stats['calls_blocked'] == 1
        assert stats['tokens_used'] == 30
    
    def test_reset_stats(self, rate_limiter):
        """Test resetting statistics."""
        from rate_limiter import CallType
        
        rate_limiter.record_call(CallType.STRATEGIC, 10, 0.5, True)
        rate_limiter.reset_stats()
        
        stats = rate_limiter.get_stats()
        
        assert stats['calls_made'] == 0
        assert stats['calls_allowed'] == 0
        assert stats['tokens_used'] == 0


class TestRateLimiterCallTypes:
    """Tests for different call types."""
    
    def test_strategic_call_type(self, rate_limiter):
        """Test strategic call type."""
        from rate_limiter import CallType
        
        result = rate_limiter.check_call(CallType.STRATEGIC)
        assert result == "allowed"
    
    def test_urgent_call_type(self, rate_limiter):
        """Test urgent call type."""
        from rate_limiter import CallType
        
        result = rate_limiter.check_call(CallType.URGENT)
        assert result == "allowed"
    
    def test_test_call_type(self, rate_limiter):
        """Test test call type."""
        from rate_limiter import CallType
        
        result = rate_limiter.check_call(CallType.TEST)
        assert result == "allowed"


class TestRateLimiterBudgetManagement:
    """Tests for budget management."""
    
    def test_budget_depletion(self, rate_limiter):
        """Test budget depletion."""
        from rate_limiter import CallType
        
        # Use up budget
        for _ in range(100):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=10, latency=0.1, success=True)
        
        # Budget should be exhausted
        stats = rate_limiter.get_stats()
        assert stats['tokens_used'] == 1000
    
    def test_budget_reset(self, rate_limiter):
        """Test budget reset."""
        from rate_limiter import CallType
        
        # Use up budget
        for _ in range(100):
            rate_limiter.record_call(CallType.STRATEGIC, tokens_used=10, latency=0.1, success=True)
        
        # Reset
        rate_limiter.reset_budget()
        
        # Budget should be reset
        result = rate_limiter.check_call(CallType.STRATEGIC)
        assert result == "allowed"


class TestRateLimiterTimeWindow:
    """Tests for time window functionality."""
    
    def test_time_window_tracking(self, rate_limiter):
        """Test time window tracking."""
        from rate_limiter import CallType
        
        # Make calls
        for _ in range(10):
            rate_limiter.record_call(CallType.STRATEGIC, 10, 0.1, True)
        
        # Check window stats
        window_stats = rate_limiter.get_window_stats()
        assert window_stats['calls_in_window'] == 10
    
    def test_time_window_reset(self, rate_limiter):
        """Test time window reset."""
        from rate_limiter import CallType
        
        # Make calls
        for _ in range(10):
            rate_limiter.record_call(CallType.STRATEGIC, 10, 0.1, True)
        
        # Reset window
        rate_limiter.reset_window()
        
        # Window should be reset
        window_stats = rate_limiter.get_window_stats()
        assert window_stats['calls_in_window'] == 0


class TestRateLimiterNotification:
    """Tests for rate limiter notifications."""
    
    def test_notification_callback(self, rate_limiter):
        """Test notification callback."""
        from rate_limiter import CallType
        
        notifications = []
        
        def notification_callback(event, message):
            notifications.append((event, message))
        
        rate_limiter.set_notification_callback(notification_callback)
        
        # Trigger a notification
        rate_limiter.record_call(CallType.STRATEGIC, 10, 0.5, True)
        
        # Should have notification
        assert len(notifications) > 0
    
    def test_notification_on_budget_exceeded(self, rate_limiter):
        """Test notification when budget exceeded."""
        from rate_limiter import CallType
        
        notifications = []
        
        def notification_callback(event, message):
            notifications.append((event, message))
        
        rate_limiter.set_notification_callback(notification_callback)
        
        # Use up budget
        for _ in range(100):
            rate_limiter.record_call(CallType.STRATEGIC, 10, 0.1, True)
        
        # Next call should trigger notification
        result = rate_limiter.check_call(CallType.STRATEGIC)
        
        # Should have budget exceeded notification
        assert any(event == "budget_exceeded" for event, _ in notifications)


class TestFactoryFunctions:
    """Tests for factory functions."""
    
    def test_get_rate_limiter_singleton(self):
        """Test get_rate_limiter singleton."""
        from rate_limiter import get_rate_limiter, reset_rate_limiter
        
        # Reset to ensure clean state
        reset_rate_limiter()
        
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        # Should return the same instance
        assert limiter1 is limiter2
        
        # Clean up
        reset_rate_limiter()
    
    def test_create_rate_limiter(self):
        """Test create_rate_limiter factory function."""
        from rate_limiter import create_rate_limiter
        
        limiter = create_rate_limiter(
            budget=500,
            time_window=30.0,
            max_calls_per_window=50
        )
        
        assert limiter is not None
        assert limiter.budget == 500


class TestRateLimiterWithStrategistConfig:
    """Tests for rate limiter with strategist configuration."""
    
    def test_strategist_rate_limit_settings(self, strategist_rate_limiter):
        """Test rate limiter with strategist settings."""
        from rate_limiter import CallType
        
        # Should allow calls within budget
        for _ in range(10):
            result = strategist_rate_limiter.check_call(CallType.STRATEGIC)
            assert result == "allowed"
        
        # 11th call should be rate limited
        result = strategist_rate_limiter.check_call(CallType.STRATEGIC)
        assert result == "rate_limited"
    
    def test_urgent_calls_bypass_limit(self, strategist_rate_limiter):
        """Test that urgent calls bypass rate limit."""
        from rate_limiter import CallType
        
        # Use up all calls in window
        for _ in range(10):
            strategist_rate_limiter.record_call(CallType.STRATEGIC, 10, 0.1, True)
        
        # Urgent call should still be allowed
        result = strategist_rate_limiter.check_call(CallType.URGENT)
        assert result == "allowed"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
