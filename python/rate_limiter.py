"""
CoH1 × Mistral AI Mod - Cost/Rate Limiter

Budget management for API calls with configurable rate limiting.
This module ensures that the AI stays within its API call budget while
maintaining responsiveness for critical decisions.

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-26
"""

import time
import threading
import logging
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import warnings


# ============================================
# Enums
# ============================================

class CallType(Enum):
    """Types of API calls."""
    STRATEGIC = "strategic"      # Regular strategic decisions
    URGENT = "urgent"            # Urgent decisions that bypass normal rate limiting
    TEST = "test"                # Test/diagnostic calls


class RateLimitResult(Enum):
    """Result of a rate limit check."""
    ALLOWED = "allowed"          # Call is allowed
    RATE_LIMITED = "rate_limited"  # Call is rate limited
    BUDGET_EXCEEDED = "budget_exceeded"  # Budget exceeded
    DISABLED = "disabled"        # Rate limiting is disabled


class BudgetResetPolicy(Enum):
    """Policy for resetting the budget."""
    NEVER = "never"              # Budget never resets (match-based)
    PER_MATCH = "per_match"      # Budget resets at start of each match
    PER_MINUTE = "per_minute"    # Budget resets every minute
    PER_HOUR = "per_hour"        # Budget resets every hour
    DAILY = "daily"              # Budget resets daily


# ============================================
# Data Classes
# ============================================

@dataclass
class CallRecord:
    """
    Record of a single API call.
    
    Attributes:
        call_type: Type of the call (strategic, urgent, test)
        timestamp: Unix timestamp when call was made
        game_time: In-game time in seconds
        call_id: Unique identifier for this call
        model: Model used for the call
        tokens_used: Number of tokens used (input + output)
        latency: Call latency in seconds
        success: Whether the call succeeded
        error: Error message if call failed
    """
    call_type: str
    timestamp: float
    game_time: float
    call_id: str
    model: str = ""
    tokens_used: int = 0
    latency: float = 0.0
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "call_type": self.call_type,
            "timestamp": self.timestamp,
            "game_time": self.game_time,
            "call_id": self.call_id,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "latency": self.latency,
            "success": self.success,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CallRecord":
        """Create from dictionary."""
        return cls(
            call_type=data.get("call_type", "strategic"),
            timestamp=data.get("timestamp", time.time()),
            game_time=data.get("game_time", 0.0),
            call_id=data.get("call_id", ""),
            model=data.get("model", ""),
            tokens_used=data.get("tokens_used", 0),
            latency=data.get("latency", 0.0),
            success=data.get("success", True),
            error=data.get("error")
        )


@dataclass
class BudgetStats:
    """
    Statistics about budget usage.
    
    Attributes:
        total_calls: Total number of calls made
        strategic_calls: Number of strategic calls
        urgent_calls: Number of urgent calls
        test_calls: Number of test calls
        total_tokens: Total tokens used
        total_latency: Total latency in seconds
        avg_latency: Average latency in seconds
        success_rate: Success rate (0.0 - 1.0)
        remaining_budget: Remaining calls in current budget
        remaining_tokens: Remaining tokens in current budget
    """
    total_calls: int = 0
    strategic_calls: int = 0
    urgent_calls: int = 0
    test_calls: int = 0
    total_tokens: int = 0
    total_latency: float = 0.0
    avg_latency: float = 0.0
    success_rate: float = 1.0
    remaining_budget: int = 0
    remaining_tokens: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_calls": self.total_calls,
            "strategic_calls": self.strategic_calls,
            "urgent_calls": self.urgent_calls,
            "test_calls": self.test_calls,
            "total_tokens": self.total_tokens,
            "total_latency": self.total_latency,
            "avg_latency": self.avg_latency,
            "success_rate": self.success_rate,
            "remaining_budget": self.remaining_budget,
            "remaining_tokens": self.remaining_tokens
        }


@dataclass
class RateLimitConfig:
    """
    Configuration for rate limiting.
    
    Attributes:
        enabled: Whether rate limiting is enabled
        max_calls_per_match: Maximum API calls per match
        max_tokens_per_match: Maximum tokens per match
        max_calls_per_minute: Maximum calls per minute (0 = unlimited)
        max_calls_per_second: Maximum calls per second (0 = unlimited)
        urgent_calls_share_budget: Whether urgent calls share the main budget
        token_cost_per_call: Estimated tokens per call (for budgeting)
        budget_reset_policy: Policy for resetting budget
        min_interval: Minimum interval between calls in seconds
        urgent_min_interval: Minimum interval for urgent calls
        adaptive_rate_limiting: Whether to use adaptive rate limiting
        cooldown_factor: Factor for adaptive cooldown (multiplier for min_interval after rate limit)
    """
    enabled: bool = True
    max_calls_per_match: int = 200
    max_tokens_per_match: int = 100000
    max_calls_per_minute: int = 30
    max_calls_per_second: int = 1
    urgent_calls_share_budget: bool = True
    token_cost_per_call: int = 1000
    budget_reset_policy: str = BudgetResetPolicy.PER_MATCH.value
    min_interval: float = 0.5
    urgent_min_interval: float = 0.1
    adaptive_rate_limiting: bool = True
    cooldown_factor: float = 2.0
    
    @classmethod
    def from_config(cls, config: Any) -> "RateLimitConfig":
        """
        Create RateLimitConfig from main configuration.
        
        Args:
            config: Main configuration object or dict
            
        Returns:
            RateLimitConfig instance
        """
        # Handle Configuration objects
        if hasattr(config, "get") and hasattr(config, "_config"):
            mistral_config = config.get("mistral") or {}
            rate_limiter_config = config.get("rate_limiter") or {}
        else:
            mistral_config = config.get("mistral", {}) if isinstance(config, dict) else {}
            rate_limiter_config = config.get("rate_limiter", {}) if isinstance(config, dict) else {}
        
        return cls(
            enabled=rate_limiter_config.get("enabled", True),
            max_calls_per_match=rate_limiter_config.get("max_calls_per_match", 
                                                       mistral_config.get("max_calls_per_match", 200)),
            max_tokens_per_match=rate_limiter_config.get("max_tokens_per_match", 100000),
            max_calls_per_minute=rate_limiter_config.get("max_calls_per_minute", 30),
            max_calls_per_second=rate_limiter_config.get("max_calls_per_second", 1),
            urgent_calls_share_budget=rate_limiter_config.get("urgent_calls_share_budget", True),
            token_cost_per_call=rate_limiter_config.get("token_cost_per_call", 1000),
            budget_reset_policy=rate_limiter_config.get("budget_reset_policy", 
                                                       BudgetResetPolicy.PER_MATCH.value),
            min_interval=rate_limiter_config.get("min_interval", 0.5),
            urgent_min_interval=rate_limiter_config.get("urgent_min_interval", 0.1),
            adaptive_rate_limiting=rate_limiter_config.get("adaptive_rate_limiting", True),
            cooldown_factor=rate_limiter_config.get("cooldown_factor", 2.0)
        )


# ============================================
# Rate Limiter Implementation
# ============================================

class CostRateLimiter:
    """
    Budget management and rate limiting for Mistral API calls.
    
    This class provides:
    - Configurable call budget per match
    - Rate limiting (calls per second, per minute)
    - Token-based budgeting
    - Urgent call support
    - Adaptive rate limiting
    - Comprehensive statistics tracking
    - Thread-safe operations
    
    Features:
    - Configurable call budget (100-200 strategist calls per match)
    - Urgent calls draw from same budget (configurable)
    - Rate limiting enforced
    - Budget usage logged
    
    Example:
        >>> limiter = CostRateLimiter()
        >>> 
        >>> # Check if call is allowed
        >>> if limiter.check_call(CallType.STRATEGIC):
        ...     result = make_api_call()
        ...     limiter.record_call(CallType.STRATEGIC, tokens_used=1000)
        >>> 
        >>> # Check budget status
        >>> stats = limiter.get_stats()
        >>> print(f"Remaining: {stats.remaining_budget} calls")
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize the rate limiter.
        
        Args:
            config: Optional configuration. Uses defaults if None.
        """
        self.config = config or RateLimitConfig()
        self._lock = threading.Lock()
        self._logger = logging.getLogger(__name__)
        
        # Call tracking
        self._calls: deque = deque(maxlen=1000)  # Recent calls for rate limiting
        self._call_history: List[CallRecord] = []  # Full call history
        
        # Budget tracking
        self._match_start_time: float = time.time()
        self._budget_used: int = 0
        self._tokens_used: int = 0
        self._last_reset_time: float = time.time()
        
        # Rate limit tracking
        self._last_call_time: Dict[str, float] = {}
        self._minute_call_count: int = 0
        self._minute_start_time: float = time.time()
        self._second_call_count: int = 0
        self._second_start_time: float = time.time()
        
        # Rate limited flag (for adaptive limiting)
        self._rate_limited: bool = False
        self._rate_limit_end_time: float = 0.0
        
        # Call ID counter
        self._call_id_counter: int = 0
        
        # Initialize
        self._initialized = False
        self._init()
    
    def _init(self):
        """Initialize the rate limiter."""
        if self._initialized:
            return
        
        # Set up logger
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)
        
        self._initialized = True
    
    def check_call(self, call_type: Union[CallType, str], tokens: int = 0, 
                   game_time: Optional[float] = None) -> RateLimitResult:
        """
        Check if a call is allowed based on rate limiting and budget.
        
        This method checks:
        1. If rate limiting is enabled
        2. If the call is within rate limits (per second, per minute)
        3. If the budget allows the call
        4. If enough time has passed since last call of this type
        
        Args:
            call_type: Type of call (CallType enum or string)
            tokens: Number of tokens this call will use
            game_time: Optional in-game time
            
        Returns:
            RateLimitResult indicating whether the call is allowed
        """
        if not self.config.enabled:
            return RateLimitResult.DISABLED
        
        # Convert string to enum if needed
        if isinstance(call_type, str):
            try:
                call_type = CallType(call_type)
            except ValueError:
                # Invalid call type, treat as disabled
                return RateLimitResult.DISABLED
        
        game_time = game_time or 0.0
        
        with self._lock:
            return self._check_call_locked(call_type, tokens, game_time)
    
    def _check_call_locked(self, call_type: CallType, tokens: int, game_time: float) -> RateLimitResult:
        """
        Check call with lock already held.
        
        Args:
            call_type: Type of call
            tokens: Number of tokens
            game_time: In-game time
            
        Returns:
            RateLimitResult
        """
        # Check if we're in a rate-limited cooldown period
        if self._rate_limited and time.time() < self._rate_limit_end_time:
            return RateLimitResult.RATE_LIMITED
        
        # Check per-second rate limit
        current_time = time.time()
        if self.config.max_calls_per_second > 0:
            if current_time - self._second_start_time < 1.0:
                if self._second_call_count >= self.config.max_calls_per_second:
                    return RateLimitResult.RATE_LIMITED
            else:
                # Reset second counter
                self._second_call_count = 0
                self._second_start_time = current_time
        
        # Check per-minute rate limit
        if self.config.max_calls_per_minute > 0:
            if current_time - self._minute_start_time < 60.0:
                if self._minute_call_count >= self.config.max_calls_per_minute:
                    return RateLimitResult.RATE_LIMITED
            else:
                # Reset minute counter
                self._minute_call_count = 0
                self._minute_start_time = current_time
        
        # Check minimum interval
        call_type_str = call_type.value
        last_time = self._last_call_time.get(call_type_str, 0.0)
        min_interval = (self.config.urgent_min_interval if call_type == CallType.URGENT 
                       else self.config.min_interval)
        
        if current_time - last_time < min_interval:
            return RateLimitResult.RATE_LIMITED
        
        # Check budget (unless urgent calls have separate budget)
        if call_type != CallType.TEST:
            # Check if budget is exceeded
            if self._budget_used >= self.config.max_calls_per_match:
                return RateLimitResult.BUDGET_EXCEEDED
            
            # Check if tokens are exceeded
            estimated_tokens = tokens or self.config.token_cost_per_call
            if self._tokens_used + estimated_tokens > self.config.max_tokens_per_match:
                return RateLimitResult.BUDGET_EXCEEDED
        
        return RateLimitResult.ALLOWED
    
    def record_call(self, call_type: Union[CallType, str], tokens_used: int = 0,
                    latency: float = 0.0, success: bool = True, error: Optional[str] = None,
                    model: str = "", game_time: Optional[float] = None) -> str:
        """
        Record a call that has been made.
        
        This should be called after a successful check_call() and API call.
        It updates all counters and statistics.
        
        Args:
            call_type: Type of call
            tokens_used: Number of tokens used in this call
            latency: Call latency in seconds
            success: Whether the call succeeded
            error: Error message if call failed
            model: Model used for the call
            game_time: Optional in-game time
            
        Returns:
            Unique call ID for this call
        """
        # Convert string to enum if needed
        if isinstance(call_type, str):
            call_type = CallType(call_type)
        
        game_time = game_time or 0.0
        current_time = time.time()
        
        # Generate call ID
        with self._lock:
            self._call_id_counter += 1
            call_id = f"call_{self._call_id_counter:06d}_{current_time:.3f}"
        
        with self._lock:
            # Update call counters
            self._last_call_time[call_type.value] = current_time
            
            if call_type != CallType.TEST:
                self._minute_call_count += 1
                self._second_call_count += 1
            
            # Update budget
            if call_type != CallType.TEST:
                self._budget_used += 1
                # Update tokens, ensuring we don't go negative
                new_tokens = self._tokens_used + tokens_used
                self._tokens_used = max(0, new_tokens)
            
            # Record the call
            record = CallRecord(
                call_type=call_type.value,
                timestamp=current_time,
                game_time=game_time,
                call_id=call_id,
                model=model,
                tokens_used=tokens_used,
                latency=latency,
                success=success,
                error=error
            )
            self._calls.append(record)
            self._call_history.append(record)
            
            # Log the call
            self._logger.debug(
                f"API call recorded: {call_type.value} | "
                f"Call ID: {call_id} | "
                f"Tokens: {tokens_used} | "
                f"Latency: {latency:.3f}s | "
                f"Success: {success}"
            )
        
        return call_id
    
    def check_and_record(self, call_type: Union[CallType, str], tokens: int = 0,
                         game_time: Optional[float] = None, **kwargs) -> Optional[str]:
        """
        Convenience method to check and record a call in one operation.
        
        Args:
            call_type: Type of call
            tokens: Number of tokens this call will use
            game_time: Optional in-game time
            **kwargs: Additional arguments for record_call
            
        Returns:
            Call ID if call is allowed, None otherwise
        """
        result = self.check_call(call_type, tokens, game_time)
        
        if result != RateLimitResult.ALLOWED:
            return None
        
        return self.record_call(call_type, tokens_used=tokens, game_time=game_time, **kwargs)
    
    def is_allowed(self, call_type: Union[CallType, str], tokens: int = 0,
                   game_time: Optional[float] = None) -> bool:
        """
        Convenience method to check if a call is allowed.
        
        Args:
            call_type: Type of call
            tokens: Number of tokens
            game_time: Optional in-game time
            
        Returns:
            True if call is allowed, False otherwise
        """
        return self.check_call(call_type, tokens, game_time) == RateLimitResult.ALLOWED
    
    def wait_for_available(self, call_type: Union[CallType, str], tokens: int = 0,
                           timeout: float = 30.0, game_time: Optional[float] = None) -> bool:
        """
        Wait until a call is allowed, with timeout.
        
        This method will block until either:
        - The call is allowed
        - The timeout is reached
        - Rate limiting is disabled
        
        Args:
            call_type: Type of call
            tokens: Number of tokens
            timeout: Maximum time to wait in seconds
            game_time: Optional in-game time
            
        Returns:
            True if call became available, False if timeout reached
        """
        if not self.config.enabled:
            return True
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.check_call(call_type, tokens, game_time)
            
            if result == RateLimitResult.ALLOWED:
                return True
            elif result == RateLimitResult.DISABLED:
                return True
            elif result == RateLimitResult.BUDGET_EXCEEDED:
                # Budget exceeded won't resolve with waiting
                return False
            
            # Calculate wait time based on rate limit
            if isinstance(call_type, str):
                call_type = CallType(call_type)
            
            min_interval = (self.config.urgent_min_interval if call_type == CallType.URGENT 
                           else self.config.min_interval)
            
            # If we were rate limited, wait longer
            if self._rate_limited and time.time() < self._rate_limit_end_time:
                wait_time = self._rate_limit_end_time - time.time()
            else:
                wait_time = min_interval
            
            time.sleep(min(wait_time, 1.0))  # Max 1 second per iteration
        
        return False
    
    def notify_rate_limited(self, retry_after: float = 0.0):
        """
        Notify the rate limiter that a rate limit was hit.
        
        This is called when the API returns a rate limit error.
        It enables adaptive rate limiting.
        
        Args:
            retry_after: Seconds to wait before retry (from API response)
        """
        if not self.config.adaptive_rate_limiting:
            return
        
        with self._lock:
            self._rate_limited = True
            self._rate_limit_end_time = time.time() + max(retry_after, 10.0)  # Min 10 seconds
            
            # Log the rate limit event
            self._logger.warning(
                f"Rate limit hit! Adaptive limiting enabled. "
                f"Retry after: {retry_after:.1f}s, "
                f"Cooldown until: {self._rate_limit_end_time:.2f}"
            )
    
    def clear_rate_limit(self):
        """Clear the rate limited state."""
        with self._lock:
            self._rate_limited = False
            self._rate_limit_end_time = 0.0
    
    def reset_budget(self, policy: Optional[str] = None):
        """
        Reset the budget according to the configured policy.
        
        Args:
            policy: Optional policy override (uses config if None)
        """
        policy = policy or self.config.budget_reset_policy
        
        with self._lock:
            if policy == BudgetResetPolicy.NEVER.value:
                # Never reset
                pass
            elif policy == BudgetResetPolicy.PER_MATCH.value:
                # Reset for new match
                self._reset_match_budget()
            elif policy == BudgetResetPolicy.PER_MINUTE.value:
                # Reset budget (time-based reset handled separately)
                self._reset_match_budget()
            elif policy == BudgetResetPolicy.PER_HOUR.value:
                # Reset budget (time-based reset handled separately)
                self._reset_match_budget()
            elif policy == BudgetResetPolicy.DAILY.value:
                # Reset budget (time-based reset handled separately)
                self._reset_match_budget()
    
    def _reset_match_budget(self):
        """Reset budget for a new match."""
        self._budget_used = 0
        self._tokens_used = 0
        self._match_start_time = time.time()
        self._last_reset_time = time.time()
        self._minute_call_count = 0
        self._minute_start_time = time.time()
        self._second_call_count = 0
        self._second_start_time = time.time()
        self._call_history = []
        self._calls.clear()
        self._last_call_time.clear()
        self._rate_limited = False
        self._rate_limit_end_time = 0.0
        
        self._logger.info("Budget reset for new match")
    
    def start_match(self):
        """Start a new match, resetting budget and statistics."""
        self.reset_budget(BudgetResetPolicy.PER_MATCH.value)
    
    def end_match(self):
        """End the current match."""
        # Log final statistics
        stats = self.get_stats()
        self._logger.info(
            f"Match ended. Total calls: {stats.total_calls}, "
            f"Tokens used: {stats.total_tokens}, "
            f"Success rate: {stats.success_rate:.2%}"
        )
    
    def get_stats(self) -> BudgetStats:
        """
        Get current budget statistics.
        
        Returns:
            BudgetStats object with all statistics
        """
        with self._lock:
            total_calls = len(self._call_history)
            strategic_calls = sum(1 for r in self._call_history if r.call_type == CallType.STRATEGIC.value)
            urgent_calls = sum(1 for r in self._call_history if r.call_type == CallType.URGENT.value)
            test_calls = sum(1 for r in self._call_history if r.call_type == CallType.TEST.value)
            
            total_tokens = sum(r.tokens_used for r in self._call_history)
            total_latency = sum(r.latency for r in self._call_history)
            
            avg_latency = total_latency / total_calls if total_calls > 0 else 0.0
            
            successful_calls = sum(1 for r in self._call_history if r.success)
            success_rate = successful_calls / total_calls if total_calls > 0 else 1.0
            
            remaining_budget = max(0, self.config.max_calls_per_match - self._budget_used)
            remaining_tokens = max(0, self.config.max_tokens_per_match - self._tokens_used)
            
            return BudgetStats(
                total_calls=total_calls,
                strategic_calls=strategic_calls,
                urgent_calls=urgent_calls,
                test_calls=test_calls,
                total_tokens=total_tokens,
                total_latency=total_latency,
                avg_latency=avg_latency,
                success_rate=success_rate,
                remaining_budget=remaining_budget,
                remaining_tokens=remaining_tokens
            )
    
    def get_remaining_budget(self) -> int:
        """Get remaining call budget."""
        with self._lock:
            return max(0, self.config.max_calls_per_match - self._budget_used)
    
    def get_remaining_tokens(self) -> int:
        """Get remaining token budget."""
        with self._lock:
            return max(0, self.config.max_tokens_per_match - self._tokens_used)
    
    def get_budget_used(self) -> int:
        """Get number of calls used so far."""
        with self._lock:
            return self._budget_used
    
    def get_tokens_used(self) -> int:
        """Get tokens used so far."""
        with self._lock:
            return self._tokens_used
    
    def get_recent_calls(self, count: int = 10) -> List[CallRecord]:
        """
        Get recent call records.
        
        Args:
            count: Number of recent calls to retrieve
            
        Returns:
            List of CallRecord objects
        """
        with self._lock:
            return list(self._call_history)[-count:]
    
    def get_call_by_id(self, call_id: str) -> Optional[CallRecord]:
        """
        Get a call record by its ID.
        
        Args:
            call_id: Call ID to look up
            
        Returns:
            CallRecord or None if not found
        """
        with self._lock:
            for record in self._call_history:
                if record.call_id == call_id:
                    return record
            return None
    
    def clear_history(self):
        """Clear all call history."""
        with self._lock:
            self._call_history.clear()
            self._calls.clear()
    
    def get_config(self) -> RateLimitConfig:
        """Get the current configuration."""
        return self.config
    
    def set_config(self, config: RateLimitConfig):
        """Update the configuration."""
        with self._lock:
            self.config = config
            # Re-initialize if needed
            self._initialized = False
            self._init()
    
    def is_rate_limited(self) -> bool:
        """Check if we're currently in a rate-limited state."""
        with self._lock:
            if not self._rate_limited:
                return False
            if time.time() >= self._rate_limit_end_time:
                self._rate_limited = False
                return False
            return True
    
    def get_rate_limit_end_time(self) -> float:
        """Get the time when rate limiting will end."""
        with self._lock:
            return self._rate_limit_end_time
    
    def __enter__(self):
        """Context manager entry."""
        self._context_call_id = None
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


# ============================================
# Factory Functions
# ============================================

_default_rate_limiter: Optional[CostRateLimiter] = None


def create_rate_limiter(config: Optional[RateLimitConfig] = None) -> CostRateLimiter:
    """
    Create a new CostRateLimiter instance.
    
    Args:
        config: Optional configuration
        
    Returns:
        New CostRateLimiter instance
    """
    return CostRateLimiter(config)


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> CostRateLimiter:
    """
    Get or create the default CostRateLimiter singleton.
    
    Args:
        config: Optional configuration for new instance
        
    Returns:
        Default CostRateLimiter instance
    """
    global _default_rate_limiter
    if _default_rate_limiter is None:
        _default_rate_limiter = create_rate_limiter(config)
    return _default_rate_limiter


def reset_rate_limiter() -> None:
    """Reset the default CostRateLimiter singleton."""
    global _default_rate_limiter
    if _default_rate_limiter is not None:
        _default_rate_limiter.clear_history()
        _default_rate_limiter.clear_rate_limit()
    _default_rate_limiter = None


# ============================================
# Convenience Functions
# ============================================

def check_rate_limit(call_type: Union[CallType, str], tokens: int = 0,
                     game_time: Optional[float] = None) -> bool:
    """Check if a call is allowed using the default rate limiter."""
    return get_rate_limiter().is_allowed(call_type, tokens, game_time)


def record_api_call(call_type: Union[CallType, str], tokens_used: int = 0,
                    latency: float = 0.0, success: bool = True, error: Optional[str] = None,
                    model: str = "", game_time: Optional[float] = None) -> str:
    """Record an API call using the default rate limiter."""
    return get_rate_limiter().record_call(call_type, tokens_used, latency, success, error, model, game_time)


def check_and_record_call(call_type: Union[CallType, str], tokens: int = 0,
                           game_time: Optional[float] = None, **kwargs) -> Optional[str]:
    """Check and record an API call using the default rate limiter."""
    return get_rate_limiter().check_and_record(call_type, tokens, game_time, **kwargs)


def get_rate_limit_stats() -> BudgetStats:
    """Get rate limit statistics using the default rate limiter."""
    return get_rate_limiter().get_stats()


def start_new_match():
    """Start a new match, resetting the default rate limiter."""
    get_rate_limiter().start_match()


def end_current_match():
    """End the current match for the default rate limiter."""
    get_rate_limiter().end_match()
