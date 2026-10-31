"""
CoH1 × Mistral AI Mod - Fallback Mechanism

Provides graceful degradation to reflex-only mode when Mistral AI is unavailable.
This ensures the AI continues to function even when cloud services are unreachable.

Responsibilities:
- Detect Mistral API unavailability
- Switch to reflex-only mode
- Maintain AI functionality without cloud calls
- Log fallback events for debugging
- Provide recovery mechanism when API becomes available again

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-18

Usage:
    from orchestrator.fallback import FallbackManager, FallbackMode
    
    # Create fallback manager
    fallback = FallbackManager()
    
    # Check if in fallback mode
    if fallback.is_in_fallback():
        # Use reflex-only logic
        pass
    else:
        # Use Mistral AI
        pass
    
    # Manually trigger fallback
    fallback.trigger_fallback("API timeout")
    
    # Attempt recovery
    fallback.attempt_recovery()
"""

import logging
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from threading import Lock


# ============================================
# Fallback Mode
# ============================================

class FallbackMode(Enum):
    """Current fallback mode."""
    NORMAL = auto()        # Mistral AI available, using full capabilities
    FALLBACK = auto()       # Mistral AI unavailable, using reflex-only mode
    DEGRADED = auto()      # Partial functionality available


class FallbackReason(Enum):
    """Reasons for entering fallback mode."""
    API_TIMEOUT = "api_timeout"
    CONNECTION_ERROR = "connection_error"
    AUTH_ERROR = "auth_error"
    RATE_LIMITED = "rate_limited"
    SERVICE_UNAVAILABLE = "service_unavailable"
    MANUAL_OVERRIDE = "manual_override"
    UNKNOWN = "unknown"


# ============================================
# Data Classes
# ============================================

@dataclass
class FallbackStats:
    """Statistics for fallback mechanism."""
    fallback_activations: int = 0
    recovery_attempts: int = 0
    successful_recoveries: int = 0
    time_in_fallback: float = 0.0  # Total seconds in fallback mode
    last_fallback_time: Optional[float] = None
    last_recovery_time: Optional[float] = None
    fallback_reasons: Dict[str, int] = field(default_factory=dict)
    
    def record_fallback(self, reason: FallbackReason) -> None:
        """Record a fallback activation."""
        self.fallback_activations += 1
        self.last_fallback_time = time.time()
        self.fallback_reasons[reason.value] = self.fallback_reasons.get(reason.value, 0) + 1
    
    def record_recovery(self, success: bool) -> None:
        """Record a recovery attempt."""
        self.recovery_attempts += 1
        self.last_recovery_time = time.time()
        if success:
            self.successful_recoveries += 1
    
    def update_time_in_fallback(self, delta: float) -> None:
        """Update time spent in fallback mode."""
        self.time_in_fallback += delta
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "fallback_activations": self.fallback_activations,
            "recovery_attempts": self.recovery_attempts,
            "successful_recoveries": self.successful_recoveries,
            "time_in_fallback": self.time_in_fallback,
            "last_fallback_time": self.last_fallback_time,
            "last_recovery_time": self.last_recovery_time,
            "fallback_reasons": self.fallback_reasons,
        }


@dataclass
class FallbackEvent:
    """Represents a fallback-related event."""
    timestamp: float
    event_type: str  # "fallback_activated", "recovery_attempt", "recovery_success", "recovery_failed"
    mode: FallbackMode
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "mode": self.mode.name,
            "reason": self.reason,
            "details": self.details,
        }


# ============================================
# Fallback Manager
# ============================================

class FallbackManager:
    """
    Manages fallback to reflex-only mode when Mistral AI is unavailable.
    
    Features:
    - Automatic detection of Mistral API failures
    - Manual fallback triggering
    - Automatic recovery attempts
    - Comprehensive logging and statistics
    - Configurable thresholds and timeouts
    """
    
    def __init__(self, 
                 api_check_interval: float = 5.0,
                 max_api_failures: int = 3,
                 recovery_check_interval: float = 10.0,
                 min_fallback_duration: float = 30.0):
        """
        Initialize fallback manager.
        
        Args:
            api_check_interval: How often to check API availability (seconds)
            max_api_failures: Number of consecutive failures before fallback
            recovery_check_interval: How often to check for recovery (seconds)
            min_fallback_duration: Minimum time to stay in fallback before recovery attempt (seconds)
        """
        self.logger = logging.getLogger(__name__)
        self._mode = FallbackMode.NORMAL
        self._lock = Lock()
        
        # Configuration
        self.api_check_interval = api_check_interval
        self.max_api_failures = max_api_failures
        self.recovery_check_interval = recovery_check_interval
        self.min_fallback_duration = min_fallback_duration
        
        # State tracking
        self._api_failure_count = 0
        self._last_api_check = 0.0
        self._last_api_failure_time = None
        self._fallback_start_time = None
        self._last_recovery_check = 0.0
        
        # Statistics
        self.stats = FallbackStats()
        
        # Event history
        self._event_history: List[FallbackEvent] = []
        self.max_history_size = 100
        
        # Callbacks
        self._on_fallback_callbacks: List[Callable[[FallbackMode, str], None]] = []
        self._on_recovery_callbacks: List[Callable[[FallbackMode], None]] = []
        
        # API checker function (can be overridden for testing)
        self._api_checker: Optional[Callable[[], bool]] = None
        
        self.logger.info("FallbackManager initialized in NORMAL mode")
    
    @property
    def mode(self) -> FallbackMode:
        """Get current fallback mode."""
        with self._lock:
            return self._mode
    
    def is_in_fallback(self) -> bool:
        """Check if currently in fallback mode."""
        return self.mode == FallbackMode.FALLBACK
    
    def is_in_degraded(self) -> bool:
        """Check if currently in degraded mode."""
        return self.mode == FallbackMode.DEGRADED
    
    def is_normal(self) -> bool:
        """Check if currently in normal mode."""
        return self.mode == FallbackMode.NORMAL
    
    def trigger_fallback(self, reason: str = "unknown", 
                       fallback_reason: Optional[FallbackReason] = None) -> bool:
        """
        Manually trigger fallback mode.
        
        Args:
            reason: Human-readable reason for fallback
            fallback_reason: Enum reason (auto-detected if not provided)
            
        Returns:
            True if fallback was triggered, False if already in fallback
        """
        with self._lock:
            if self._mode == FallbackMode.FALLBACK:
                self.logger.warning(f"Already in fallback mode, ignoring trigger: {reason}")
                return False
            
            # Determine fallback reason
            if fallback_reason is None:
                fallback_reason = self._classify_fallback_reason(reason)
            
            # Record event
            event = FallbackEvent(
                timestamp=time.time(),
                event_type="fallback_activated",
                mode=FallbackMode.FALLBACK,
                reason=reason,
                details={"trigger": "manual"}
            )
            self._record_event(event)
            
            # Update state
            old_mode = self._mode
            self._mode = FallbackMode.FALLBACK
            self._fallback_start_time = time.time()
            self._api_failure_count = self.max_api_failures  # Ensure we don't exit immediately
            
            # Record statistics
            self.stats.record_fallback(fallback_reason)
            
            # Log
            self.logger.warning(f"Fallback mode activated: {reason}")
            
            # Notify callbacks
            self._notify_fallback_callbacks(old_mode, reason)
            
            return True
    
    def exit_fallback(self) -> bool:
        """
        Manually exit fallback mode.
        
        Returns:
            True if fallback was exited, False if not in fallback
        """
        with self._lock:
            if self._mode != FallbackMode.FALLBACK:
                self.logger.warning("Not in fallback mode, cannot exit")
                return False
            
            # Record event
            event = FallbackEvent(
                timestamp=time.time(),
                event_type="recovery_success",
                mode=FallbackMode.NORMAL,
                reason="manual_exit",
                details={"trigger": "manual"}
            )
            self._record_event(event)
            
            # Update statistics
            if self._fallback_start_time:
                duration = time.time() - self._fallback_start_time
                self.stats.update_time_in_fallback(duration)
            
            # Update state
            old_mode = self._mode
            self._mode = FallbackMode.NORMAL
            self._fallback_start_time = None
            self._api_failure_count = 0
            
            # Record statistics
            self.stats.record_recovery(True)
            
            # Log
            self.logger.info("Fallback mode exited manually")
            
            # Notify callbacks
            self._notify_recovery_callbacks(FallbackMode.NORMAL)
            
            return True
    
    def attempt_recovery(self) -> bool:
        """
        Attempt to recover from fallback mode.
        
        Checks if Mistral API is available and if minimum fallback duration has passed.
        
        Returns:
            True if recovery was successful, False otherwise
        """
        with self._lock:
            # Check if we should attempt recovery
            if self._mode != FallbackMode.FALLBACK:
                self.logger.debug("Not in fallback mode, no recovery needed")
                return False
            
            # Check minimum fallback duration
            if self._fallback_start_time:
                duration = time.time() - self._fallback_start_time
                if duration < self.min_fallback_duration:
                    self.logger.debug(
                        f"Minimum fallback duration not met: {duration:.1f}s < {self.min_fallback_duration}s"
                    )
                    return False
            
            # Check if API is available
            if not self._check_api_available():
                self.logger.debug("API still unavailable, cannot recover")
                self._last_recovery_check = time.time()
                
                # Record failed recovery attempt
                self.stats.record_recovery(False)
                
                # Record event
                event = FallbackEvent(
                    timestamp=time.time(),
                    event_type="recovery_failed",
                    mode=FallbackMode.FALLBACK,
                    reason="api_unavailable",
                    details={"next_check": self._last_recovery_check + self.recovery_check_interval}
                )
                self._record_event(event)
                
                return False
            
            # API is available, recover
            event = FallbackEvent(
                timestamp=time.time(),
                event_type="recovery_success",
                mode=FallbackMode.NORMAL,
                reason="api_available",
                details={"trigger": "automatic"}
            )
            self._record_event(event)
            
            # Update statistics
            if self._fallback_start_time:
                duration = time.time() - self._fallback_start_time
                self.stats.update_time_in_fallback(duration)
            
            # Update state
            old_mode = self._mode
            self._mode = FallbackMode.NORMAL
            self._fallback_start_time = None
            self._api_failure_count = 0
            self._last_api_failure_time = None
            
            # Record statistics
            self.stats.record_recovery(True)
            
            # Log
            self.logger.info("Successfully recovered from fallback mode - Mistral API available")
            
            # Notify callbacks
            self._notify_recovery_callbacks(FallbackMode.NORMAL)
            
            return True
    
    def check_api_status(self) -> bool:
        """
        Check if Mistral API is available.
        
        This method can be called periodically to monitor API status.
        
        Returns:
            True if API is available, False otherwise
        """
        should_trigger_fallback = False
        return_value = None
        
        with self._lock:
            # Check if we should perform an API check
            now = time.time()
            if now - self._last_api_check < self.api_check_interval:
                # Too soon since last check
                return_value = self._api_failure_count < self.max_api_failures
            else:
                self._last_api_check = now
                
                # Perform API check
                if self._check_api_available():
                    self._api_failure_count = 0
                    self._last_api_failure_time = None
                    self.logger.debug("API check: Available")
                    return_value = True
                else:
                    self._api_failure_count += 1
                    self._last_api_failure_time = now
                    self.logger.warning(f"API check: Failure #{self._api_failure_count}")
                    
                    # Auto-trigger fallback if threshold reached
                    if self._api_failure_count >= self.max_api_failures:
                        self.logger.warning("API failure threshold reached, triggering fallback")
                        should_trigger_fallback = True
                    
                    return_value = False
        
        # Trigger fallback outside the lock to avoid deadlock
        if should_trigger_fallback:
            self.trigger_fallback(
                reason=f"{self._api_failure_count} consecutive API failures",
                fallback_reason=FallbackReason.CONNECTION_ERROR
            )
        
        return return_value
    
    def _check_api_available(self) -> bool:
        """
        Internal method to check if API is available.
        
        Can be overridden for testing or custom implementations.
        
        Returns:
            True if API is available, False otherwise
        """
        # Use custom checker if provided
        if self._api_checker is not None:
            return self._api_checker()
        
        # Default implementation: assume available
        # In real implementation, this would call Mistral API
        return True
    
    def set_api_checker(self, checker: Callable[[], bool]) -> None:
        """
        Set a custom API checker function.
        
        Useful for testing or custom API implementations.
        
        Args:
            checker: Function that returns True if API is available
        """
        self._api_checker = checker
        self.logger.info("Custom API checker set")
    
    def clear_api_checker(self) -> None:
        """Clear custom API checker, use default."""
        self._api_checker = None
        self.logger.info("Custom API checker cleared")
    
    def _classify_fallback_reason(self, reason: str) -> FallbackReason:
        """Classify fallback reason string into enum."""
        if reason is None:
            return FallbackReason.UNKNOWN
        reason_lower = reason.lower()
        
        if "timeout" in reason_lower:
            return FallbackReason.API_TIMEOUT
        elif "connection" in reason_lower or "network" in reason_lower:
            return FallbackReason.CONNECTION_ERROR
        elif "auth" in reason_lower or "token" in reason_lower or "key" in reason_lower:
            return FallbackReason.AUTH_ERROR
        elif "rate" in reason_lower or "limit" in reason_lower:
            return FallbackReason.RATE_LIMITED
        elif "unavailable" in reason_lower or "down" in reason_lower:
            return FallbackReason.SERVICE_UNAVAILABLE
        elif "manual" in reason_lower:
            return FallbackReason.MANUAL_OVERRIDE
        else:
            return FallbackReason.UNKNOWN
    
    def _record_event(self, event: FallbackEvent) -> None:
        """Record an event in history."""
        self._event_history.append(event)
        
        # Trim history if too large
        if len(self._event_history) > self.max_history_size:
            self._event_history = self._event_history[-self.max_history_size:]
    
    def get_event_history(self) -> List[FallbackEvent]:
        """Get fallback event history."""
        with self._lock:
            return self._event_history.copy()
    
    def clear_event_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
    
    def on_fallback(self, callback: Callable[[FallbackMode, str], None]) -> None:
        """
        Register a callback to be called when entering fallback mode.
        
        Args:
            callback: Function(mode, reason) to call on fallback
        """
        self._on_fallback_callbacks.append(callback)
        self.logger.debug("Registered fallback callback")
    
    def on_recovery(self, callback: Callable[[FallbackMode], None]) -> None:
        """
        Register a callback to be called when exiting fallback mode.
        
        Args:
            callback: Function(mode) to call on recovery
        """
        self._on_recovery_callbacks.append(callback)
        self.logger.debug("Registered recovery callback")
    
    def _notify_fallback_callbacks(self, old_mode: FallbackMode, reason: str) -> None:
        """Notify all fallback callbacks."""
        for callback in self._on_fallback_callbacks:
            try:
                callback(self._mode, reason)
            except Exception as e:
                self.logger.error(f"Error in fallback callback: {e}")
    
    def _notify_recovery_callbacks(self, new_mode: FallbackMode) -> None:
        """Notify all recovery callbacks."""
        for callback in self._on_recovery_callbacks:
            try:
                callback(new_mode)
            except Exception as e:
                self.logger.error(f"Error in recovery callback: {e}")
    
    def get_stats(self) -> FallbackStats:
        """Get fallback statistics."""
        with self._lock:
            # Update time in fallback if currently in fallback
            if self._fallback_start_time:
                duration = time.time() - self._fallback_start_time
                self.stats.update_time_in_fallback(duration)
            
            return self.stats
    
    def reset_stats(self) -> None:
        """Reset fallback statistics."""
        with self._lock:
            self.stats = FallbackStats()
            self._api_failure_count = 0
            self._last_api_check = 0.0
            self._last_api_failure_time = None
            self._fallback_start_time = None
            self._last_recovery_check = 0.0
    
    def get_current_mode_info(self) -> Dict[str, Any]:
        """Get information about current mode."""
        with self._lock:
            info = {
                "mode": self._mode.name,
                "is_fallback": self._mode == FallbackMode.FALLBACK,  # Direct check instead of self.is_in_fallback()
                "is_normal": self._mode == FallbackMode.NORMAL,      # Direct check instead of self.is_normal()
            }
            
            if self._fallback_start_time:
                info["fallback_duration"] = time.time() - self._fallback_start_time
            
            if self._last_api_failure_time:
                info["time_since_last_failure"] = time.time() - self._last_api_failure_time
            
            info["api_failure_count"] = self._api_failure_count
            
            return info


# ============================================
# Fallback Context Manager
# ============================================

class FallbackContext:
    """
    Context manager for temporary fallback mode.
    
    Useful for testing or specific operations that should use fallback mode.
    """
    
    def __init__(self, fallback_manager: FallbackManager):
        """Initialize context manager."""
        self.fallback_manager = fallback_manager
        self._was_in_fallback = False
    
    def __enter__(self) -> FallbackManager:
        """Enter fallback mode."""
        self._was_in_fallback = self.fallback_manager.is_in_fallback()
        if not self._was_in_fallback:
            self.fallback_manager.trigger_fallback("context_manager")
        return self.fallback_manager
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit fallback mode if we entered it."""
        if not self._was_in_fallback:
            self.fallback_manager.exit_fallback()


# ============================================
# Factory Functions
# ============================================

_default_fallback_manager: Optional[FallbackManager] = None


def get_fallback_manager() -> FallbackManager:
    """Get the default fallback manager instance (singleton)."""
    global _default_fallback_manager
    if _default_fallback_manager is None:
        _default_fallback_manager = FallbackManager()
    return _default_fallback_manager


def reset_fallback_manager() -> None:
    """Reset the default fallback manager instance."""
    global _default_fallback_manager
    if _default_fallback_manager is not None:
        _default_fallback_manager.exit_fallback()
    _default_fallback_manager = None


def create_fallback_manager(
    api_check_interval: float = 5.0,
    max_api_failures: int = 3,
    recovery_check_interval: float = 10.0,
    min_fallback_duration: float = 30.0
) -> FallbackManager:
    """
    Create a new fallback manager instance.
    
    Args:
        api_check_interval: How often to check API availability
        max_api_failures: Number of failures before fallback
        recovery_check_interval: How often to check for recovery
        min_fallback_duration: Minimum time in fallback before recovery
        
    Returns:
        New FallbackManager instance
    """
    return FallbackManager(
        api_check_interval=api_check_interval,
        max_api_failures=max_api_failures,
        recovery_check_interval=recovery_check_interval,
        min_fallback_duration=min_fallback_duration
    )


def is_in_fallback() -> bool:
    """Check if in fallback mode using default manager."""
    return get_fallback_manager().is_in_fallback()


def trigger_fallback(reason: str = "unknown") -> bool:
    """Trigger fallback mode using default manager."""
    return get_fallback_manager().trigger_fallback(reason)


def exit_fallback() -> bool:
    """Exit fallback mode using default manager."""
    return get_fallback_manager().exit_fallback()
