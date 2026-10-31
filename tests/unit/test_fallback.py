"""
Unit tests for the Fallback Mechanism module.

Tests cover:
- Fallback mode detection
- Fallback activation and deactivation
- Recovery mechanisms
- Statistics tracking
- Event history
- Configuration options
- Callback notifications

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-18
"""

import pytest
import sys
import time
import threading
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to Python path for imports
sys.path.insert(0, str((Path(__file__).parent.parent.parent / "python").resolve()))

from orchestrator.fallback import (
    FallbackManager,
    FallbackMode,
    FallbackReason,
    FallbackStats,
    FallbackEvent,
    FallbackContext,
    create_fallback_manager,
    get_fallback_manager,
    reset_fallback_manager,
    is_in_fallback,
    trigger_fallback,
    exit_fallback,
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def fallback_manager():
    """Create a fresh fallback manager for each test."""
    return FallbackManager(
        api_check_interval=1.0,
        max_api_failures=3,
        recovery_check_interval=5.0,
        min_fallback_duration=10.0
    )


@pytest.fixture
def fallback_manager_fast():
    """Create a fallback manager with fast intervals for testing."""
    return FallbackManager(
        api_check_interval=0.01,
        max_api_failures=2,
        recovery_check_interval=0.01,
        min_fallback_duration=0.01
    )


@pytest.fixture
def fallback_manager_strict():
    """Create a fallback manager with strict settings."""
    return FallbackManager(
        api_check_interval=0.1,
        max_api_failures=1,
        recovery_check_interval=0.1,
        min_fallback_duration=5.0
    )


@pytest.fixture
def mock_api_checker():
    """Mock API checker function."""
    def checker():
        return True  # API available by default
    return checker


@pytest.fixture
def mock_failing_api_checker():
    """Mock API checker that always fails."""
    def checker():
        return False  # API always unavailable
    return checker


# ============================================
# Test FallbackMode Enum
# ============================================

class TestFallbackMode:
    """Tests for FallbackMode enum."""
    
    def test_fallback_mode_values(self):
        """Test that all expected fallback modes exist."""
        assert hasattr(FallbackMode, "NORMAL")
        assert hasattr(FallbackMode, "FALLBACK")
        assert hasattr(FallbackMode, "DEGRADED")
        
    def test_fallback_mode_unique(self):
        """Test that all fallback mode values are unique."""
        modes = [mode.value for mode in FallbackMode]
        assert len(modes) == len(set(modes))
        
    def test_fallback_mode_order(self):
        """Test fallback mode ordering."""
        # NORMAL should be first (lowest value)
        assert FallbackMode.NORMAL.value < FallbackMode.FALLBACK.value
        assert FallbackMode.NORMAL.value < FallbackMode.DEGRADED.value


# ============================================
# Test FallbackReason Enum
# ============================================

class TestFallbackReason:
    """Tests for FallbackReason enum."""
    
    def test_fallback_reason_values(self):
        """Test that all expected fallback reasons exist."""
        expected_reasons = [
            "API_TIMEOUT", "CONNECTION_ERROR", "AUTH_ERROR",
            "RATE_LIMITED", "SERVICE_UNAVAILABLE", "MANUAL_OVERRIDE", "UNKNOWN"
        ]
        for reason in expected_reasons:
            assert hasattr(FallbackReason, reason)
            
    def test_fallback_reason_string_values(self):
        """Test fallback reason string values."""
        assert FallbackReason.API_TIMEOUT.value == "api_timeout"
        assert FallbackReason.CONNECTION_ERROR.value == "connection_error"
        assert FallbackReason.AUTH_ERROR.value == "auth_error"
        assert FallbackReason.RATE_LIMITED.value == "rate_limited"
        assert FallbackReason.SERVICE_UNAVAILABLE.value == "service_unavailable"
        assert FallbackReason.MANUAL_OVERRIDE.value == "manual_override"
        assert FallbackReason.UNKNOWN.value == "unknown"


# ============================================
# Test FallbackStats Dataclass
# ============================================

class TestFallbackStats:
    """Tests for FallbackStats dataclass."""
    
    def test_fallback_stats_creation(self):
        """Test creating fallback stats."""
        stats = FallbackStats()
        assert stats.fallback_activations == 0
        assert stats.recovery_attempts == 0
        assert stats.successful_recoveries == 0
        assert stats.time_in_fallback == 0.0
        
    def test_fallback_stats_record_fallback(self):
        """Test recording a fallback activation."""
        stats = FallbackStats()
        stats.record_fallback(FallbackReason.API_TIMEOUT)
        
        assert stats.fallback_activations == 1
        assert FallbackReason.API_TIMEOUT.value in stats.fallback_reasons
        assert stats.fallback_reasons[FallbackReason.API_TIMEOUT.value] == 1
        
    def test_fallback_stats_multiple_fallbacks(self):
        """Test recording multiple fallback activations."""
        stats = FallbackStats()
        stats.record_fallback(FallbackReason.API_TIMEOUT)
        stats.record_fallback(FallbackReason.CONNECTION_ERROR)
        stats.record_fallback(FallbackReason.API_TIMEOUT)
        
        assert stats.fallback_activations == 3
        assert stats.fallback_reasons[FallbackReason.API_TIMEOUT.value] == 2
        assert stats.fallback_reasons[FallbackReason.CONNECTION_ERROR.value] == 1
        
    def test_fallback_stats_record_recovery(self):
        """Test recording a recovery attempt."""
        stats = FallbackStats()
        stats.record_recovery(True)
        
        assert stats.recovery_attempts == 1
        assert stats.successful_recoveries == 1
        
    def test_fallback_stats_failed_recovery(self):
        """Test recording a failed recovery attempt."""
        stats = FallbackStats()
        stats.record_recovery(False)
        
        assert stats.recovery_attempts == 1
        assert stats.successful_recoveries == 0
        
    def test_fallback_stats_update_time(self):
        """Test updating time spent in fallback."""
        stats = FallbackStats()
        stats.update_time_in_fallback(5.0)
        
        assert stats.time_in_fallback == 5.0
        
        stats.update_time_in_fallback(3.0)
        assert stats.time_in_fallback == 8.0
        
    def test_fallback_stats_to_dict(self):
        """Test converting stats to dictionary."""
        stats = FallbackStats()
        stats.record_fallback(FallbackReason.API_TIMEOUT)
        stats.record_recovery(True)
        stats.update_time_in_fallback(10.0)
        
        result = stats.to_dict()
        
        assert result["fallback_activations"] == 1
        assert result["recovery_attempts"] == 1
        assert result["successful_recoveries"] == 1
        assert result["time_in_fallback"] == 10.0


# ============================================
# Test FallbackEvent Dataclass
# ============================================

class TestFallbackEvent:
    """Tests for FallbackEvent dataclass."""
    
    def test_fallback_event_creation(self):
        """Test creating a fallback event."""
        event = FallbackEvent(
            timestamp=1000.0,
            event_type="fallback_activated",
            mode=FallbackMode.FALLBACK,
            reason="API timeout",
            details={"test": "value"}
        )
        
        assert event.timestamp == 1000.0
        assert event.event_type == "fallback_activated"
        assert event.mode == FallbackMode.FALLBACK
        assert event.reason == "API timeout"
        assert event.details == {"test": "value"}
        
    def test_fallback_event_to_dict(self):
        """Test converting event to dictionary."""
        event = FallbackEvent(
            timestamp=1000.0,
            event_type="fallback_activated",
            mode=FallbackMode.FALLBACK,
            reason="API timeout"
        )
        
        result = event.to_dict()
        
        assert result["timestamp"] == 1000.0
        assert result["event_type"] == "fallback_activated"
        assert result["mode"] == "FALLBACK"
        assert result["reason"] == "API timeout"


# ============================================
# Test FallbackManager Initialization
# ============================================

class TestFallbackManagerInitialization:
    """Tests for FallbackManager initialization."""
    
    def test_fallback_manager_default_creation(self):
        """Test creating fallback manager with defaults."""
        manager = FallbackManager()
        
        assert manager.mode == FallbackMode.NORMAL
        assert manager.api_check_interval == 5.0
        assert manager.max_api_failures == 3
        assert manager.recovery_check_interval == 10.0
        assert manager.min_fallback_duration == 30.0
        
    def test_fallback_manager_custom_creation(self):
        """Test creating fallback manager with custom settings."""
        manager = FallbackManager(
            api_check_interval=2.0,
            max_api_failures=5,
            recovery_check_interval=15.0,
            min_fallback_duration=60.0
        )
        
        assert manager.api_check_interval == 2.0
        assert manager.max_api_failures == 5
        assert manager.recovery_check_interval == 15.0
        assert manager.min_fallback_duration == 60.0
        
    def test_fallback_manager_initial_mode(self):
        """Test that manager starts in NORMAL mode."""
        manager = FallbackManager()
        
        assert manager.is_normal()
        assert not manager.is_in_fallback()
        assert not manager.is_in_degraded()


# ============================================
# Test Mode Checking
# ============================================

class TestModeChecking:
    """Tests for mode checking functions."""
    
    def test_is_normal_mode(self, fallback_manager):
        """Test checking for normal mode."""
        assert fallback_manager.is_normal()
        assert not fallback_manager.is_in_fallback()
        assert not fallback_manager.is_in_degraded()
        
    def test_mode_property(self, fallback_manager):
        """Test mode property access."""
        assert fallback_manager.mode == FallbackMode.NORMAL


# ============================================
# Test Manual Fallback Triggering
# ============================================

class TestManualFallbackTriggering:
    """Tests for manual fallback triggering."""
    
    def test_trigger_fallback_success(self, fallback_manager):
        """Test triggering fallback mode manually."""
        result = fallback_manager.trigger_fallback("Test reason")
        
        assert result is True
        assert fallback_manager.is_in_fallback()
        assert not fallback_manager.is_normal()
        
    def test_trigger_fallback_already_in_fallback(self, fallback_manager):
        """Test triggering fallback when already in fallback."""
        fallback_manager.trigger_fallback("First reason")
        result = fallback_manager.trigger_fallback("Second reason")
        
        assert result is False
        assert fallback_manager.is_in_fallback()
        
    def test_trigger_fallback_with_reason(self, fallback_manager):
        """Test triggering fallback with specific reason."""
        fallback_manager.trigger_fallback(
            reason="connection_error",
            fallback_reason=FallbackReason.CONNECTION_ERROR
        )
        
        assert fallback_manager.is_in_fallback()
        stats = fallback_manager.get_stats()
        assert FallbackReason.CONNECTION_ERROR.value in stats.fallback_reasons
        
    def test_trigger_fallback_auto_reason_classification(self, fallback_manager):
        """Test automatic reason classification."""
        fallback_manager.trigger_fallback(reason="API timeout occurred")
        
        stats = fallback_manager.get_stats()
        assert FallbackReason.API_TIMEOUT.value in stats.fallback_reasons
        
    def test_trigger_fallback_network_error(self, fallback_manager):
        """Test fallback trigger with network error reason."""
        fallback_manager.trigger_fallback(reason="Network connection failed")
        
        stats = fallback_manager.get_stats()
        assert FallbackReason.CONNECTION_ERROR.value in stats.fallback_reasons


# ============================================
# Test Manual Fallback Exit
# ============================================

class TestManualFallbackExit:
    """Tests for manual fallback exit."""
    
    def test_exit_fallback_success(self, fallback_manager):
        """Test exiting fallback mode manually."""
        fallback_manager.trigger_fallback("Test")
        result = fallback_manager.exit_fallback()
        
        assert result is True
        assert fallback_manager.is_normal()
        assert not fallback_manager.is_in_fallback()
        
    def test_exit_fallback_not_in_fallback(self, fallback_manager):
        """Test exiting fallback when not in fallback."""
        result = fallback_manager.exit_fallback()
        
        assert result is False
        assert fallback_manager.is_normal()
        
    def test_exit_fallback_stats_update(self, fallback_manager):
        """Test that exit fallback updates statistics."""
        fallback_manager.trigger_fallback("Test")
        time.sleep(0.01)  # Small delay for duration calculation
        fallback_manager.exit_fallback()
        
        stats = fallback_manager.get_stats()
        assert stats.recovery_attempts == 1
        assert stats.successful_recoveries == 1


# ============================================
# Test API Status Checking
# ============================================

class TestAPIStatusChecking:
    """Tests for API status checking."""
    
    def test_check_api_status_available(self, fallback_manager_fast, mock_api_checker):
        """Test API status check when available."""
        fallback_manager_fast.set_api_checker(mock_api_checker)
        
        result = fallback_manager_fast.check_api_status()
        assert result is True
        
    def test_check_api_status_unavailable(self, fallback_manager_fast, mock_failing_api_checker):
        """Test API status check when unavailable."""
        fallback_manager_fast.set_api_checker(mock_failing_api_checker)
        
        # First check should fail
        result = fallback_manager_fast.check_api_status()
        assert result is False
        
    def test_check_api_status_auto_fallback(self, fallback_manager_strict, mock_failing_api_checker):
        """Test that API failures trigger fallback automatically."""
        fallback_manager_strict.set_api_checker(mock_failing_api_checker)
        fallback_manager_strict.max_api_failures = 1
        
        # Trigger API check which should fail and trigger fallback
        fallback_manager_strict.check_api_status()
        
        # After max failures, should be in fallback
        assert fallback_manager_strict.is_in_fallback()
        
    def test_check_api_status_recovery(self, fallback_manager_fast):
        """Test API status check recovery."""
        # Manually trigger fallback
        fallback_manager_fast.trigger_fallback("Test")
        
        # Set API checker to return True
        fallback_manager_fast.set_api_checker(lambda: True)
        fallback_manager_fast.min_fallback_duration = 0.0
        
        # Attempt recovery
        result = fallback_manager_fast.attempt_recovery()
        assert result is True
        assert fallback_manager_fast.is_normal()


# ============================================
# Test Recovery Mechanism
# ============================================

class TestRecoveryMechanism:
    """Tests for automatic recovery mechanism."""
    
    def test_attempt_recovery_not_in_fallback(self, fallback_manager):
        """Test recovery attempt when not in fallback."""
        result = fallback_manager.attempt_recovery()
        
        assert result is False
        assert fallback_manager.is_normal()
        
    def test_attempt_recovery_api_unavailable(self, fallback_manager):
        """Test recovery attempt when API is still unavailable."""
        fallback_manager.trigger_fallback("Test")
        
        # Set API checker to fail
        fallback_manager.set_api_checker(lambda: False)
        
        result = fallback_manager.attempt_recovery()
        
        assert result is False
        assert fallback_manager.is_in_fallback()
        
    def test_attempt_recovery_min_duration(self, fallback_manager):
        """Test recovery attempt respects minimum duration."""
        fallback_manager.trigger_fallback("Test")
        fallback_manager.set_api_checker(lambda: True)
        
        # min_fallback_duration is 30 seconds by default
        result = fallback_manager.attempt_recovery()
        
        assert result is False
        assert fallback_manager.is_in_fallback()
        
    def test_attempt_recovery_success(self, fallback_manager_fast):
        """Test successful recovery attempt."""
        fallback_manager_fast.trigger_fallback("Test")
        fallback_manager_fast.set_api_checker(lambda: True)
        fallback_manager_fast.min_fallback_duration = 0.0
        
        result = fallback_manager_fast.attempt_recovery()
        
        assert result is True
        assert fallback_manager_fast.is_normal()


# ============================================
# Test Custom API Checker
# ============================================

class TestCustomAPIChecker:
    """Tests for custom API checker functionality."""
    
    def test_set_api_checker(self, fallback_manager, mock_api_checker):
        """Test setting a custom API checker."""
        fallback_manager.set_api_checker(mock_api_checker)
        
        # Verify it's set
        result = fallback_manager.check_api_status()
        assert result is True
        
    def test_clear_api_checker(self, fallback_manager, mock_api_checker):
        """Test clearing custom API checker."""
        fallback_manager.set_api_checker(mock_api_checker)
        fallback_manager.clear_api_checker()
        
        # Default should assume available
        result = fallback_manager.check_api_status()
        assert result is True
        
    def test_custom_api_checker_variations(self, fallback_manager):
        """Test various custom API checker behaviors."""
        # Use a very short interval to ensure both calls go through
        fallback_manager.api_check_interval = 0.0
        
        # Checker that toggles
        call_count = [0]
        def toggling_checker():
            call_count[0] += 1
            return call_count[0] % 2 == 1
        
        fallback_manager.set_api_checker(toggling_checker)
        
        result1 = fallback_manager.check_api_status()
        result2 = fallback_manager.check_api_status()
        
        # First call should be True, second False
        assert result1 is True
        assert result2 is False


# ============================================
# Test Event History
# ============================================

class TestEventHistory:
    """Tests for event history tracking."""
    
    def test_event_history_recording(self, fallback_manager):
        """Test that events are recorded in history."""
        fallback_manager.trigger_fallback("Test 1")
        fallback_manager.exit_fallback()
        
        history = fallback_manager.get_event_history()
        
        assert len(history) >= 2
        assert any(e.event_type == "fallback_activated" for e in history)
        assert any(e.event_type == "recovery_success" for e in history)
        
    def test_event_history_max_size(self, fallback_manager):
        """Test that event history respects max size."""
        fallback_manager.max_history_size = 5
        
        # Trigger many events
        for i in range(10):
            fallback_manager.trigger_fallback(f"Test {i}")
            fallback_manager.exit_fallback()
        
        history = fallback_manager.get_event_history()
        assert len(history) <= 5
        
    def test_clear_event_history(self, fallback_manager):
        """Test clearing event history."""
        fallback_manager.trigger_fallback("Test")
        fallback_manager.clear_event_history()
        
        history = fallback_manager.get_event_history()
        assert len(history) == 0


# ============================================
# Test Statistics
# ============================================

class TestStatistics:
    """Tests for statistics tracking."""
    
    def test_get_stats(self, fallback_manager):
        """Test getting current statistics."""
        stats = fallback_manager.get_stats()
        
        assert isinstance(stats, FallbackStats)
        assert stats.fallback_activations == 0
        
    def test_reset_stats(self, fallback_manager):
        """Test resetting statistics."""
        fallback_manager.trigger_fallback("Test")
        fallback_manager.exit_fallback()
        
        stats = fallback_manager.get_stats()
        assert stats.fallback_activations > 0
        
        fallback_manager.reset_stats()
        
        stats = fallback_manager.get_stats()
        assert stats.fallback_activations == 0
        assert stats.recovery_attempts == 0
        
    def test_stats_time_tracking(self, fallback_manager):
        """Test time in fallback tracking."""
        fallback_manager.trigger_fallback("Test")
        time.sleep(0.1)
        
        stats = fallback_manager.get_stats()
        assert stats.time_in_fallback >= 0.1


# ============================================
# Test Current Mode Info
# ============================================

class TestCurrentModeInfo:
    """Tests for current mode information."""
    
    def test_get_current_mode_info_normal(self, fallback_manager):
        """Test getting mode info in normal mode."""
        info = fallback_manager.get_current_mode_info()
        
        assert info["mode"] == "NORMAL"
        assert info["is_fallback"] is False
        assert info["is_normal"] is True
        
    def test_get_current_mode_info_fallback(self, fallback_manager):
        """Test getting mode info in fallback mode."""
        fallback_manager.trigger_fallback("Test")
        
        info = fallback_manager.get_current_mode_info()
        
        assert info["mode"] == "FALLBACK"
        assert info["is_fallback"] is True
        assert info["is_normal"] is False


# ============================================
# Test Callbacks
# ============================================

class TestCallbacks:
    """Tests for callback registration and notification."""
    
    def test_on_fallback_callback(self, fallback_manager):
        """Test registering a fallback callback."""
        callback_called = [False]
        callback_mode = [None]
        callback_reason = [None]
        
        def my_callback(mode, reason):
            callback_called[0] = True
            callback_mode[0] = mode
            callback_reason[0] = reason
        
        fallback_manager.on_fallback(my_callback)
        fallback_manager.trigger_fallback("Test reason")
        
        assert callback_called[0] is True
        assert callback_mode[0] == FallbackMode.FALLBACK
        assert callback_reason[0] == "Test reason"
        
    def test_on_recovery_callback(self, fallback_manager):
        """Test registering a recovery callback."""
        callback_called = [False]
        callback_mode = [None]
        
        def my_callback(mode):
            callback_called[0] = True
            callback_mode[0] = mode
        
        fallback_manager.on_recovery(my_callback)
        fallback_manager.trigger_fallback("Test")
        fallback_manager.exit_fallback()
        
        assert callback_called[0] is True
        assert callback_mode[0] == FallbackMode.NORMAL
        
    def test_multiple_callbacks(self, fallback_manager):
        """Test multiple callbacks being called."""
        callback1_called = [False]
        callback2_called = [False]
        
        def callback1(mode, reason):
            callback1_called[0] = True
        
        def callback2(mode, reason):
            callback2_called[0] = True
        
        fallback_manager.on_fallback(callback1)
        fallback_manager.on_fallback(callback2)
        fallback_manager.trigger_fallback("Test")
        
        assert callback1_called[0] is True
        assert callback2_called[0] is True


# ============================================
# Test Fallback Context Manager
# ============================================

class TestFallbackContextManager:
    """Tests for FallbackContext context manager."""
    
    def test_fallback_context_enter(self, fallback_manager):
        """Test entering fallback context."""
        context = FallbackContext(fallback_manager)
        
        with context:
            assert fallback_manager.is_in_fallback()
        
    def test_fallback_context_exit(self, fallback_manager):
        """Test exiting fallback context."""
        context = FallbackContext(fallback_manager)
        
        with context:
            assert fallback_manager.is_in_fallback()
        
        assert fallback_manager.is_normal()
        
    def test_fallback_context_nested(self, fallback_manager):
        """Test nested fallback contexts."""
        context1 = FallbackContext(fallback_manager)
        
        with context1:
            assert fallback_manager.is_in_fallback()
            
            context2 = FallbackContext(fallback_manager)
            with context2:
                assert fallback_manager.is_in_fallback()
            
            # Still in fallback from context1
            assert fallback_manager.is_in_fallback()
        
        assert fallback_manager.is_normal()
        
    def test_fallback_context_existing_fallback(self, fallback_manager):
        """Test context manager with existing fallback."""
        fallback_manager.trigger_fallback("Manual")
        context = FallbackContext(fallback_manager)
        
        with context:
            assert fallback_manager.is_in_fallback()
        
        # Should still be in fallback (wasn't in fallback before context)
        assert fallback_manager.is_in_fallback()


# ============================================
# Test Factory Functions
# ============================================

class TestFactoryFunctions:
    """Tests for factory functions."""
    
    def test_create_fallback_manager(self):
        """Test creating a fallback manager via factory."""
        manager = create_fallback_manager(
            api_check_interval=2.0,
            max_api_failures=5,
            recovery_check_interval=15.0,
            min_fallback_duration=60.0
        )
        
        assert isinstance(manager, FallbackManager)
        assert manager.api_check_interval == 2.0
        assert manager.max_api_failures == 5
        
    def test_get_default_fallback_manager(self):
        """Test getting default fallback manager."""
        # Reset first
        reset_fallback_manager()
        
        manager1 = get_fallback_manager()
        manager2 = get_fallback_manager()
        
        assert manager1 is manager2  # Same instance
        assert isinstance(manager1, FallbackManager)
        
    def test_reset_default_fallback_manager(self):
        """Test resetting default fallback manager."""
        manager1 = get_fallback_manager()
        manager1.trigger_fallback("Test")
        
        reset_fallback_manager()
        
        manager2 = get_fallback_manager()
        
        # Should be a new instance
        assert manager1 is not manager2
        assert manager2.is_normal()
        
    def test_global_fallback_functions(self):
        """Test global fallback functions."""
        reset_fallback_manager()
        
        # Initially not in fallback
        assert is_in_fallback() is False
        
        # Trigger fallback
        result = trigger_fallback("Global test")
        assert result is True
        assert is_in_fallback() is True
        
        # Exit fallback
        result = exit_fallback()
        assert result is True
        assert is_in_fallback() is False


# ============================================
# Test Edge Cases
# ============================================

class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_rapid_mode_switching(self, fallback_manager_fast):
        """Test rapid mode switching."""
        for i in range(5):
            fallback_manager_fast.trigger_fallback(f"Test {i}")
            fallback_manager_fast.exit_fallback()
        
        stats = fallback_manager_fast.get_stats()
        assert stats.fallback_activations == 5
        assert stats.successful_recoveries == 5
        
    def test_empty_reason_string(self, fallback_manager):
        """Test fallback with empty reason string."""
        fallback_manager.trigger_fallback("")
        
        stats = fallback_manager.get_stats()
        assert stats.fallback_activations == 1
        assert FallbackReason.UNKNOWN.value in stats.fallback_reasons
        
    def test_none_reason_string(self, fallback_manager):
        """Test fallback with None reason."""
        fallback_manager.trigger_fallback(None)
        
        stats = fallback_manager.get_stats()
        assert stats.fallback_activations == 1
        
    def test_callback_error_handling(self, fallback_manager):
        """Test that callback errors don't crash the manager."""
        def bad_callback(mode, reason):
            raise ValueError("Test error")
        
        fallback_manager.on_fallback(bad_callback)
        
        # Should not raise, just log error
        result = fallback_manager.trigger_fallback("Test")
        assert result is True
        
    def test_recovery_callback_error_handling(self, fallback_manager):
        """Test that recovery callback errors don't crash."""
        def bad_callback(mode):
            raise ValueError("Test error")
        
        fallback_manager.on_recovery(bad_callback)
        
        fallback_manager.trigger_fallback("Test")
        # Should not raise, just log error
        result = fallback_manager.exit_fallback()
        assert result is True


# ============================================
# Test Thread Safety
# ============================================

class TestThreadSafety:
    """Tests for thread safety."""
    
    def test_concurrent_fallback_trigger(self, fallback_manager):
        """Test concurrent fallback triggering."""
        results = []
        
        def trigger_fallback():
            result = fallback_manager.trigger_fallback("Concurrent test")
            results.append(result)
        
        # Trigger multiple times concurrently
        threads = []
        for _ in range(5):
            t = threading.Thread(target=trigger_fallback)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Only one should succeed
        assert sum(results) == 1
        
    def test_concurrent_mode_checks(self, fallback_manager):
        """Test concurrent mode checks."""
        results = []
        
        def check_mode():
            results.append(fallback_manager.mode)
        
        threads = []
        for _ in range(10):
            t = threading.Thread(target=check_mode)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All should return NORMAL
        assert all(mode == FallbackMode.NORMAL for mode in results)
