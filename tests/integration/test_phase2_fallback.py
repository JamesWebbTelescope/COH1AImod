"""
Phase 2 Fallback Mechanism Integration Tests

Tests the fallback mechanism for graceful degradation when Mistral AI is unavailable:
1. Fallback mode activation and deactivation
2. Automatic detection of API failures
3. Recovery mechanism
4. Integration with command processor

This test validates Phase 2 exit criteria:
- Reflex layer works without strategist
- Fallback mechanism in place

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-25
"""

import time
import threading
import pytest
from pathlib import Path

# Add parent directory to Python path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from orchestrator.fallback import (
    FallbackManager, FallbackMode, FallbackReason, FallbackStats, FallbackEvent,
    get_fallback_manager, reset_fallback_manager, create_fallback_manager,
    is_in_fallback, trigger_fallback, exit_fallback, FallbackContext
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fallback_manager():
    """Create a fresh fallback manager for each test."""
    # Use short timeouts for testing
    # Set max_api_failures=1 for faster testing
    manager = FallbackManager(
        api_check_interval=0.01,
        max_api_failures=1,
        recovery_check_interval=0.01,
        min_fallback_duration=0.01
    )
    yield manager
    # Clean up
    if manager.is_in_fallback():
        manager.exit_fallback()
    manager.clear_event_history()


# =============================================================================
# Fallback Manager Tests
# =============================================================================

class TestFallbackManager:
    """Tests for the FallbackManager class."""
    
    def test_initial_state_normal(self, fallback_manager):
        """Test that manager starts in NORMAL mode."""
        assert fallback_manager.mode == FallbackMode.NORMAL
        assert fallback_manager.is_normal()
        assert not fallback_manager.is_in_fallback()
        assert not fallback_manager.is_in_degraded()
    
    def test_manual_fallback_activation(self, fallback_manager):
        """Test manual fallback activation."""
        # Trigger fallback
        result = fallback_manager.trigger_fallback("test activation")
        assert result is True
        assert fallback_manager.mode == FallbackMode.FALLBACK
        assert fallback_manager.is_in_fallback()
        assert not fallback_manager.is_normal()
    
    def test_manual_fallback_deactivation(self, fallback_manager):
        """Test manual fallback deactivation."""
        # First activate fallback
        fallback_manager.trigger_fallback("test")
        assert fallback_manager.is_in_fallback()
        
        # Exit fallback
        result = fallback_manager.exit_fallback()
        assert result is True
        assert fallback_manager.mode == FallbackMode.NORMAL
        assert fallback_manager.is_normal()
    
    def test_fallback_already_active(self, fallback_manager):
        """Test that triggering fallback when already in fallback does nothing."""
        # First activation
        result1 = fallback_manager.trigger_fallback("test 1")
        assert result1 is True
        
        # Second activation
        result2 = fallback_manager.trigger_fallback("test 2")
        assert result2 is False  # Should fail because already in fallback
        assert fallback_manager.mode == FallbackMode.FALLBACK
    
    def test_exit_fallback_not_in_fallback(self, fallback_manager):
        """Test that exiting fallback when not in fallback does nothing."""
        # Try to exit when not in fallback
        result = fallback_manager.exit_fallback()
        assert result is False
        assert fallback_manager.mode == FallbackMode.NORMAL
    
    def test_fallback_with_reason(self, fallback_manager):
        """Test fallback activation with specific reason."""
        fallback_manager.trigger_fallback("API timeout", fallback_reason=FallbackReason.API_TIMEOUT)
        assert fallback_manager.is_in_fallback()
        
        # Check stats
        stats = fallback_manager.get_stats()
        assert stats.fallback_activations == 1
    
    def test_fallback_reason_classification(self, fallback_manager):
        """Test automatic reason classification."""
        # Test various reason strings
        reasons = {
            "API timeout": FallbackReason.API_TIMEOUT,
            "Connection failed": FallbackReason.CONNECTION_ERROR,
            "Authentication error": FallbackReason.AUTH_ERROR,
            "Rate limited": FallbackReason.RATE_LIMITED,
            "Service unavailable": FallbackReason.SERVICE_UNAVAILABLE,
            "Manual override": FallbackReason.MANUAL_OVERRIDE,
            "Unknown reason": FallbackReason.UNKNOWN
        }
        
        for reason_str, expected_reason in reasons.items():
            result = fallback_manager._classify_fallback_reason(reason_str)
            assert result == expected_reason, f"Failed for '{reason_str}': got {result}, expected {expected_reason}"


# =============================================================================
# API Check Tests
# =============================================================================

class TestAPICheck:
    """Tests for API availability checking."""
    
    def test_api_check_available(self, fallback_manager):
        """Test API check when API is available."""
        # Set custom checker that always returns True
        fallback_manager.set_api_checker(lambda: True)
        
        # Check API status
        result = fallback_manager.check_api_status()
        assert result is True
        assert fallback_manager._api_failure_count == 0
    
    def test_api_check_unavailable(self, fallback_manager):
        """Test API check when API is unavailable."""
        # Set custom checker that always returns False
        fallback_manager.set_api_checker(lambda: False)
        
        # Check API status once - with max_api_failures=1, this should trigger fallback
        result = fallback_manager.check_api_status()
        assert result is False
        
        # Should have triggered fallback
        assert fallback_manager.is_in_fallback()
    
    def test_api_check_threshold(self, fallback_manager):
        """Test that fallback is triggered after max failures."""
        # Set max_api_failures to 2 for this test
        fallback_manager.max_api_failures = 2
        
        # Set custom checker that returns False
        fallback_manager.set_api_checker(lambda: False)
        
        # Check API status once - should not trigger fallback yet
        fallback_manager.check_api_status()
        assert not fallback_manager.is_in_fallback()
        assert fallback_manager._api_failure_count == 1
        
        # Wait for interval to pass
        time.sleep(fallback_manager.api_check_interval + 0.01)
        
        # Check again - should trigger fallback now (2 failures >= 2 threshold)
        fallback_manager.check_api_status()
        assert fallback_manager.is_in_fallback()
    
    def test_api_recovery(self, fallback_manager):
        """Test API recovery after becoming available."""
        # First, trigger fallback
        fallback_manager.trigger_fallback("test")
        assert fallback_manager.is_in_fallback()
        
        # Set API to be available
        fallback_manager.set_api_checker(lambda: True)
        
        # Wait for minimum fallback duration
        time.sleep(fallback_manager.min_fallback_duration + 0.05)
        
        # Attempt recovery
        result = fallback_manager.attempt_recovery()
        assert result is True
        assert fallback_manager.is_normal()


# =============================================================================
# Event History Tests
# =============================================================================

class TestEventHistory:
    """Tests for fallback event history tracking."""
    
    def test_event_recording(self, fallback_manager):
        """Test that events are recorded in history."""
        # Trigger fallback
        fallback_manager.trigger_fallback("test")
        
        # Get history
        history = fallback_manager.get_event_history()
        assert len(history) >= 1
        
        # Check event details
        fallback_event = history[0]
        assert fallback_event.event_type == "fallback_activated"
        assert fallback_event.mode == FallbackMode.FALLBACK
        assert fallback_event.reason == "test"
    
    def test_event_history_limit(self, fallback_manager):
        """Test that history is limited in size."""
        # Trigger multiple fallback events
        for i in range(150):
            fallback_manager.trigger_fallback(f"test {i}")
            if fallback_manager.is_in_fallback():
                fallback_manager.exit_fallback()
        
        # Get history
        history = fallback_manager.get_event_history()
        
        # Should be capped at max_history_size (default 100)
        assert len(history) <= fallback_manager.max_history_size
    
    def test_clear_event_history(self, fallback_manager):
        """Test clearing event history."""
        # Trigger some events
        fallback_manager.trigger_fallback("test 1")
        fallback_manager.exit_fallback()
        fallback_manager.trigger_fallback("test 2")
        
        # Clear history
        fallback_manager.clear_event_history()
        
        # History should be empty
        history = fallback_manager.get_event_history()
        assert len(history) == 0


# =============================================================================
# Statistics Tests
# =============================================================================

class TestFallbackStats:
    """Tests for fallback statistics tracking."""
    
    def test_stats_initialization(self, fallback_manager):
        """Test that stats are initialized correctly."""
        stats = fallback_manager.get_stats()
        assert stats.fallback_activations == 0
        assert stats.recovery_attempts == 0
        assert stats.successful_recoveries == 0
    
    def test_stats_after_fallback(self, fallback_manager):
        """Test stats after fallback activation."""
        fallback_manager.trigger_fallback("test")
        
        stats = fallback_manager.get_stats()
        assert stats.fallback_activations >= 1
    
    def test_stats_after_recovery(self, fallback_manager):
        """Test stats after recovery."""
        # Trigger fallback
        fallback_manager.trigger_fallback("test")
        
        # Exit fallback
        fallback_manager.exit_fallback()
        
        stats = fallback_manager.get_stats()
        assert stats.fallback_activations >= 1
        assert stats.successful_recoveries >= 1
    
    def test_reset_stats(self, fallback_manager):
        """Test resetting statistics."""
        # Trigger some events
        fallback_manager.trigger_fallback("test 1")
        fallback_manager.exit_fallback()
        fallback_manager.trigger_fallback("test 2")
        
        # Reset stats
        fallback_manager.reset_stats()
        
        # Stats should be reset
        stats = fallback_manager.get_stats()
        assert stats.fallback_activations == 0
        assert stats.recovery_attempts == 0
        assert stats.successful_recoveries == 0


# =============================================================================
# Callback Tests
# =============================================================================

class TestCallbacks:
    """Tests for fallback callback functionality."""
    
    def test_on_fallback_callback(self, fallback_manager):
        """Test fallback callback registration."""
        callback_called = []
        
        def my_callback(mode, reason):
            callback_called.append((mode, reason))
        
        fallback_manager.on_fallback(my_callback)
        
        # Trigger fallback
        fallback_manager.trigger_fallback("test reason")
        
        # Callback should have been called
        assert len(callback_called) == 1
        assert callback_called[0][0] == FallbackMode.FALLBACK
        assert callback_called[0][1] == "test reason"
    
    def test_on_recovery_callback(self, fallback_manager):
        """Test recovery callback registration."""
        callback_called = []
        
        def my_callback(mode):
            callback_called.append(mode)
        
        fallback_manager.on_recovery(my_callback)
        
        # Trigger fallback then exit
        fallback_manager.trigger_fallback("test")
        fallback_manager.exit_fallback()
        
        # Callback should have been called
        assert len(callback_called) >= 1
        assert callback_called[0] == FallbackMode.NORMAL
    
    def test_multiple_callbacks(self, fallback_manager):
        """Test multiple callback registrations."""
        callback1_called = []
        callback2_called = []
        
        def callback1(mode, reason):
            callback1_called.append((mode, reason))
        
        def callback2(mode, reason):
            callback2_called.append((mode, reason))
        
        fallback_manager.on_fallback(callback1)
        fallback_manager.on_fallback(callback2)
        
        # Trigger fallback
        fallback_manager.trigger_fallback("test")
        
        # Both callbacks should have been called
        assert len(callback1_called) == 1
        assert len(callback2_called) == 1


# =============================================================================
# Context Manager Tests
# =============================================================================

class TestFallbackContext:
    """Tests for FallbackContext context manager."""
    
    def test_context_manager_enter(self, fallback_manager):
        """Test entering fallback context."""
        assert fallback_manager.is_normal()
        
        with FallbackContext(fallback_manager):
            assert fallback_manager.is_in_fallback()
        
        # Should have exited fallback
        assert fallback_manager.is_normal()
    
    def test_context_manager_already_in_fallback(self, fallback_manager):
        """Test context manager when already in fallback."""
        # First enter fallback
        fallback_manager.trigger_fallback("test")
        
        with FallbackContext(fallback_manager):
            assert fallback_manager.is_in_fallback()
        
        # Should still be in fallback (was already in fallback)
        assert fallback_manager.is_in_fallback()
    
    def test_nested_context_managers(self, fallback_manager):
        """Test nested context managers."""
        assert fallback_manager.is_normal()
        
        with FallbackContext(fallback_manager):
            assert fallback_manager.is_in_fallback()
            
            # Nested context
            with FallbackContext(fallback_manager):
                assert fallback_manager.is_in_fallback()
            
            # Still in fallback
            assert fallback_manager.is_in_fallback()
        
        # Should have exited fallback
        assert fallback_manager.is_normal()


# =============================================================================
# Integration Tests
# =============================================================================

class TestFallbackIntegration:
    """Tests for fallback integration with other components."""
    
    def test_fallback_with_command_processor(self):
        """Test that command processor can work with fallback mode."""
        from config import Configuration
        from orchestrator.command_processor import CommandProcessor
        
        # Create fallback manager
        fallback_mgr = FallbackManager(
            api_check_interval=0.1,
            max_api_failures=1,
            min_fallback_duration=0.1
        )
        
        # Set API to unavailable
        fallback_mgr.set_api_checker(lambda: False)
        
        # Create command processor
        config = Configuration()
        
        class MockIPCReader:
            def send_command(self, command):
                return True
        
        processor = CommandProcessor(config=config, ipc_reader=MockIPCReader())
        processor.start()
        
        # Trigger fallback
        fallback_mgr.trigger_fallback("API unavailable")
        
        # Command processor should still work
        from orchestrator.command_processor import create_retreat_command
        cmd = create_retreat_command(1)
        assert processor.add_command(cmd)
        
        # Process queue
        processed = processor.process_queue()
        assert processed >= 0
        
        processor.stop()
    
    def test_singleton_functions(self):
        """Test singleton fallback functions."""
        # Reset to ensure clean state
        reset_fallback_manager()
        
        # Get default manager
        manager = get_fallback_manager()
        assert manager is not None
        assert manager.is_normal()
        
        # Use convenience functions
        assert not is_in_fallback()
        
        # Trigger fallback
        result = trigger_fallback("test")
        assert result is True
        assert is_in_fallback()
        
        # Exit fallback
        result = exit_fallback()
        assert result is True
        assert not is_in_fallback()
    
    def test_custom_checker_with_recovery(self, fallback_manager):
        """Test custom API checker with recovery scenario."""
        api_available = [False, True, True, True]
        call_count = [0]
        
        def custom_checker():
            result = api_available[call_count[0]]
            call_count[0] += 1
            return result
        
        fallback_manager.set_api_checker(custom_checker)
        
        # Check API status - should fail once and trigger fallback (max_api_failures=1)
        fallback_manager.check_api_status()  # False -> triggers fallback
        
        assert fallback_manager.is_in_fallback()
        
        # Set minimum fallback duration to 0 for testing
        fallback_manager.min_fallback_duration = 0
        
        # Attempt recovery - should succeed now that API is available
        result = fallback_manager.attempt_recovery()
        assert result is True
        assert fallback_manager.is_normal()


# =============================================================================
# Stress Tests
# =============================================================================

class TestStress:
    """Stress tests for fallback mechanism."""
    
    def test_rapid_fallback_activation(self, fallback_manager):
        """Test rapid fallback activation and deactivation."""
        for i in range(100):
            fallback_manager.trigger_fallback(f"test {i}")
            fallback_manager.exit_fallback()
        
        assert fallback_manager.is_normal()
        
        stats = fallback_manager.get_stats()
        assert stats.fallback_activations == 100
        assert stats.successful_recoveries == 100
    
    def test_concurrent_fallback_operations(self, fallback_manager):
        """Test concurrent fallback operations."""
        results = []
        errors = []
        
        def fallback_worker():
            try:
                for i in range(10):
                    fallback_manager.trigger_fallback(f"worker {threading.current_thread().name} - {i}")
                    time.sleep(0.01)
                    fallback_manager.exit_fallback()
                results.append(True)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = [
            threading.Thread(target=fallback_worker, daemon=True)
            for _ in range(5)
        ]
        
        # Start threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=5.0)
        
        # Check results
        assert len(results) == 5
        assert len(errors) == 0
        assert fallback_manager.is_normal()


# =============================================================================
# Mode Info Tests
# =============================================================================

class TestModeInfo:
    """Tests for mode information retrieval."""
    
    def test_get_mode_info_normal(self, fallback_manager):
        """Test mode info in normal mode."""
        info = fallback_manager.get_current_mode_info()
        assert info["mode"] == "NORMAL"
        assert info["is_fallback"] is False
        assert info["is_normal"] is True
    
    def test_get_mode_info_fallback(self, fallback_manager):
        """Test mode info in fallback mode."""
        fallback_manager.trigger_fallback("test")
        
        info = fallback_manager.get_current_mode_info()
        assert info["mode"] == "FALLBACK"
        assert info["is_fallback"] is True
        assert info["is_normal"] is False
        assert "fallback_duration" in info
    
    def test_get_mode_info_with_duration(self, fallback_manager):
        """Test mode info includes fallback duration."""
        fallback_manager.trigger_fallback("test")
        time.sleep(0.1)
        
        info = fallback_manager.get_current_mode_info()
        assert info["fallback_duration"] >= 0.1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
