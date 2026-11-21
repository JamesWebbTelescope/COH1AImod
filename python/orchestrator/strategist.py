"""
CoH1 × Mistral AI Mod - Strategist Integration

Connects the orchestrator to Mistral AI for strategic decision-making.
This module handles the complete strategic cycle: state analysis → Mistral call → 
intent parsing → command generation → validation → execution.

Features:
- Full strategic cycle integration
- Intent validation and execution
- Error handling with fallback to reflex layer
- Rate limiting awareness
- Game history integration for context

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-11-21
"""

import json
import time
import logging
import threading
from typing import Optional, Dict, Any, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque

try:
    # Try relative imports first (for package mode)
    from ..mistral_client import MistralClient, MistralModel, MistralResponse, create_mistral_client
    from ..prompts import PromptEngine, Faction, Difficulty, GamePhase, create_prompt_engine
    from ..schema import GameState, create_command
    from ..validator import ActionValidator, get_validator
    from ..safety_filter import SafetyFilter, get_safety_filter
    from ..history import GameHistoryManager, get_history_manager
    from ..rate_limiter import CostRateLimiter, get_rate_limiter, CallType
    from ..orchestrator.command_processor import CommandProcessor, AICommand, CommandPriority
    from .fallback import FallbackManager, get_fallback_manager
    from .state_manager import StateManager
except ImportError:
    # Fallback to absolute imports (for direct execution or testing)
    try:
        from mistral_client import MistralClient, MistralModel, MistralResponse, create_mistral_client
        from prompts import PromptEngine, Faction, Difficulty, GamePhase, create_prompt_engine
        from schema import GameState, create_command
        from validator import ActionValidator, get_validator
        from safety_filter import SafetyFilter, get_safety_filter
        from history import GameHistoryManager, get_history_manager
        from rate_limiter import CostRateLimiter, get_rate_limiter, CallType
        from orchestrator.command_processor import CommandProcessor, AICommand, CommandPriority
        from orchestrator.fallback import FallbackManager, get_fallback_manager
        from orchestrator.state_manager import StateManager
    except ImportError as e:
        logging.getLogger(__name__).error(f"Failed to import dependencies: {e}")
        raise


# ============================================
# Enums
# ============================================

class StrategistState(Enum):
    """States for the strategist."""
    IDLE = auto()          # Waiting for next strategic tick
    PROCESSING = auto()     # Processing game state
    CALLING_AI = auto()     # Calling Mistral API
    PARSE_INTENTS = auto()  # Parsing AI response
    EXECUTING = auto()      # Executing commands
    ERROR = auto()          # Error state
    FALLBACK = auto()       # Fallback to reflex-only mode


class IntentType(Enum):
    """Types of AI intents."""
    BUILD = "BUILD"
    TECH = "TECH"
    PRODUCE = "PRODUCE"
    ATTACK = "ATTACK"
    DEFEND = "DEFEND"
    RETREAT = "RETREAT"
    CAPTURE = "CAPTURE"
    EXPAND = "EXPAND"
    REINFORCE = "REINFORCE"
    FALLBACK = "FALLBACK"
    HOLD = "HOLD"
    STOP = "STOP"


# ============================================
# Data Classes
# ============================================

@dataclass
class StrategicIntent:
    """Represents a strategic intent from Mistral AI."""
    intent: str
    confidence: float = 1.0
    reasoning: str = ""
    priority: int = 1
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "priority": self.priority,
            "parameters": self.parameters,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategicIntent":
        return cls(
            intent=data.get("intent", "UNKNOWN"),
            confidence=data.get("confidence", 1.0),
            reasoning=data.get("reasoning", ""),
            priority=data.get("priority", 1),
            parameters=data.get("parameters", {}),
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class StrategistStats:
    """Statistics for the strategist."""
    total_cycles: int = 0
    successful_cycles: int = 0
    failed_cycles: int = 0
    total_intents: int = 0
    executed_intents: int = 0
    failed_intents: int = 0
    avg_processing_time: float = 0.0
    avg_ai_response_time: float = 0.0
    last_cycle_time: float = 0.0
    last_error_time: float = 0.0
    last_error: str = ""
    
    def record_cycle(self, success: bool, processing_time: float, 
                     ai_response_time: float, error: str = "") -> None:
        """Record a strategic cycle."""
        self.total_cycles += 1
        if success:
            self.successful_cycles += 1
        else:
            self.failed_cycles += 1
            self.last_error = error
            self.last_error_time = time.time()
        
        self.last_cycle_time = time.time()
        
        # Update averages
        if self.total_cycles > 0:
            self.avg_processing_time = (
                (self.avg_processing_time * (self.total_cycles - 1)) + processing_time
            ) / self.total_cycles
            self.avg_ai_response_time = (
                (self.avg_ai_response_time * (self.total_cycles - 1)) + ai_response_time
            ) / self.total_cycles
    
    def record_intent(self, success: bool) -> None:
        """Record an intent execution."""
        self.total_intents += 1
        if success:
            self.executed_intents += 1
        else:
            self.failed_intents += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_cycles": self.total_cycles,
            "successful_cycles": self.successful_cycles,
            "failed_cycles": self.failed_cycles,
            "total_intents": self.total_intents,
            "executed_intents": self.executed_intents,
            "failed_intents": self.failed_intents,
            "avg_processing_time": self.avg_processing_time,
            "avg_ai_response_time": self.avg_ai_response_time,
            "last_cycle_time": self.last_cycle_time,
            "last_error_time": self.last_error_time,
            "last_error": self.last_error
        }


@dataclass
class StrategistConfig:
    """Configuration for the strategist."""
    # Strategic cycle settings
    tick_interval: float = 10.0  # Seconds between strategic decisions
    enabled: bool = True
    
    # Mistral settings
    model: str = "mistral-small-latest"
    temperature: float = 0.7
    max_tokens: int = 2048
    json_mode: bool = True
    
    # Intent processing
    max_intents_per_cycle: int = 5
    min_confidence: float = 0.5
    min_priority: int = 1
    
    # Context
    include_history: bool = True
    history_depth: int = 5
    
    # Fallback
    fallback_on_error: bool = True
    fallback_on_rate_limit: bool = True
    
    # Logging
    log_intents: bool = True
    log_responses: bool = False  # Don't log full AI responses (may contain sensitive data)


# ============================================
# Intent to Command Mapping
# ============================================

# Maps intent types to command types and parameter mappings
INTENT_TO_COMMAND = {
    IntentType.BUILD: {
        "command": "BUILD",
        "required_params": ["building_type", "position"],
        "optional_params": ["engineer_id"]
    },
    IntentType.TECH: {
        "command": "TECH",
        "required_params": ["tech_name"],
        "optional_params": ["building_id"]
    },
    IntentType.PRODUCE: {
        "command": "PRODUCE",
        "required_params": ["unit_type"],
        "optional_params": ["building_id", "count"]
    },
    IntentType.ATTACK: {
        "command": "ATTACK_MOVE",
        "required_params": ["position"],
        "optional_params": ["squad_id"]
    },
    IntentType.DEFEND: {
        "command": "SET_POSTURE",
        "required_params": ["position"],
        "optional_params": ["squad_id"],
        "default_posture": "defensive"
    },
    IntentType.RETREAT: {
        "command": "RETREAT",
        "required_params": ["squad_id"],
        "optional_params": ["position"]
    },
    IntentType.CAPTURE: {
        "command": "CAPTURE",
        "required_params": ["squad_id", "point_id"],
        "optional_params": []
    },
    IntentType.EXPAND: {
        "command": "ATTACK_MOVE",
        "required_params": ["position"],
        "optional_params": ["squad_id"]
    },
    IntentType.REINFORCE: {
        "command": "ATTACK_MOVE",
        "required_params": ["position"],
        "optional_params": ["squad_id"]
    },
    IntentType.FALLBACK: {
        "command": "RETREAT",
        "required_params": [],
        "optional_params": ["squad_id", "position"]
    },
    IntentType.HOLD: {
        "command": "HOLD",
        "required_params": ["squad_id"],
        "optional_params": []
    },
    IntentType.STOP: {
        "command": "STOP",
        "required_params": ["squad_id"],
        "optional_params": []
    }
}


# ============================================
# Strategist
# ============================================

class Strategist:
    """
    Manages strategic decision-making using Mistral AI.
    
    This class handles the complete strategic cycle:
    1. Receive game state from state manager
    2. Generate prompts using prompt engine
    3. Call Mistral API for strategic intents
    4. Parse and validate intents
    5. Convert intents to commands
    6. Validate and execute commands via command processor
    
    Features:
    - Thread-safe operation
    - Rate limiting awareness
    - Fallback to reflex layer on errors
    - Game history integration for context
    - Comprehensive logging and statistics
    """
    
    def __init__(self, config: Optional[StrategistConfig] = None,
                 state_manager: Optional[StateManager] = None,
                 command_processor: Optional[CommandProcessor] = None,
                 mistral_client: Optional[MistralClient] = None,
                 prompt_engine: Optional[PromptEngine] = None,
                 history_manager: Optional[GameHistoryManager] = None,
                 validator: Optional[ActionValidator] = None,
                 safety_filter: Optional[SafetyFilter] = None,
                 fallback_manager: Optional[FallbackManager] = None,
                 rate_limiter: Optional[CostRateLimiter] = None):
        """
        Initialize the strategist.
        
        Args:
            config: Configuration
            state_manager: State manager for game state
            command_processor: Command processor for execution
            mistral_client: Mistral API client
            prompt_engine: Prompt engine for generating prompts
            history_manager: History manager for context
            validator: Action validator
            safety_filter: Safety filter
            fallback_manager: Fallback manager
            rate_limiter: Rate limiter
        """
        self.config = config or StrategistConfig()
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.state_manager = state_manager
        self.command_processor = command_processor
        self._mistral_client = mistral_client
        self._prompt_engine = prompt_engine
        self._history_manager = history_manager
        self.validator = validator or get_validator()
        self.safety_filter = safety_filter or get_safety_filter()
        self.fallback_manager = fallback_manager or get_fallback_manager()
        self.rate_limiter = rate_limiter or get_rate_limiter()
        
        # State
        self.state = StrategistState.IDLE
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        
        # Statistics
        self.stats = StrategistStats()
        
        # Initialize components if not provided
        self._init_components()
        
        self.logger.info("Strategist initialized")
    
    def _init_components(self) -> None:
        """Initialize components that weren't provided."""
        if self._mistral_client is None:
            try:
                model = MistralModel(self.config.model) if self.config.model else MistralModel.SMALL
                self._mistral_client = create_mistral_client(
                    model=model,
                    json_mode=self.config.json_mode
                )
                self.logger.info(f"Mistral client created with model: {self.config.model}")
            except Exception as e:
                self.logger.error(f"Failed to create Mistral client: {e}")
                self._mistral_client = None
        
        if self._prompt_engine is None:
            self._prompt_engine = create_prompt_engine()
            self.logger.info("Prompt engine created")
        
        if self._history_manager is None:
            self._history_manager = get_history_manager()
            self.logger.info("History manager created")
    
    def start(self) -> bool:
        """Start the strategist."""
        if self._running:
            self.logger.warning("Strategist is already running")
            return False
        
        if not self._mistral_client:
            self.logger.error("Mistral client not available, cannot start strategist")
            return False
        
        self._running = True
        self.state = StrategistState.IDLE
        self.logger.info("Strategist started")
        return True
    
    def stop(self) -> bool:
        """Stop the strategist."""
        if not self._running:
            return True
        
        self._running = False
        self.state = StrategistState.IDLE
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self.logger.warning("Strategist thread did not stop gracefully")
        
        if self._mistral_client:
            self._mistral_client.close()
        
        self.logger.info("Strategist stopped")
        return True
    
    def run_cycle(self) -> bool:
        """
        Run a complete strategic cycle.
        
        This is the main method that:
        1. Gets current game state
        2. Generates prompts
        3. Calls Mistral API
        4. Parses and validates intents
        5. Executes commands
        
        Returns:
            True if cycle completed successfully, False otherwise
        """
        if not self._running:
            self.logger.warning("Strategist is not running")
            return False
        
        if self.state != StrategistState.IDLE:
            self.logger.warning(f"Strategist is busy ({self.state.name})")
            return False
        
        start_time = time.time()
        processing_start = time.time()
        ai_call_time = 0.0
        
        try:
            with self._lock:
                self.state = StrategistState.PROCESSING
            
            # Step 1: Get current game state
            self.logger.info("Strategist: Starting strategic cycle")
            game_state = self._get_current_state()
            
            if not game_state:
                self.logger.warning("No game state available, skipping cycle")
                self.stats.record_cycle(False, time.time() - start_time, 0, "No game state")
                self.state = StrategistState.IDLE
                return False
            
            # Step 2: Check if we should use fallback
            if self.fallback_manager.is_in_fallback():
                self.logger.info("Strategist: In fallback mode, using reflex-only")
                self.state = StrategistState.FALLBACK
                return False
            
            # Step 3: Check rate limiting
            if not self._check_rate_limit():
                self.logger.info("Strategist: Rate limited, skipping cycle")
                self.stats.record_cycle(False, time.time() - start_time, 0, "Rate limited")
                self.state = StrategistState.IDLE
                return False
            
            # Step 4: Generate prompts
            self.logger.debug("Strategist: Generating prompts")
            system_prompt, user_prompt = self._generate_prompts(game_state)
            
            # Step 5: Call Mistral API
            with self._lock:
                self.state = StrategistState.CALLING_AI
            
            self.logger.debug("Strategist: Calling Mistral API")
            ai_start = time.time()
            
            try:
                response = self._call_mistral(system_prompt, user_prompt)
                ai_call_time = time.time() - ai_start
            except Exception as e:
                self.logger.error(f"Strategist: Mistral API call failed: {e}")
                self.stats.record_cycle(False, time.time() - start_time, ai_call_time, str(e))
                
                # Trigger fallback if configured
                if self.config.fallback_on_error:
                    self.fallback_manager.trigger_fallback(f"Mistral API error: {e}")
                
                self.state = StrategistState.IDLE
                return False
            
            # Step 6: Parse intents from response
            with self._lock:
                self.state = StrategistState.PARSE_INTENTS
            
            self.logger.debug("Strategist: Parsing intents")
            intents = self._parse_intents(response)
            
            if not intents:
                self.logger.warning("Strategist: No valid intents parsed from response")
                self.stats.record_cycle(False, time.time() - start_time, ai_call_time, "No intents")
                self.state = StrategistState.IDLE
                return False
            
            # Step 7: Filter and prioritize intents
            intents = self._filter_intents(intents)
            
            if not intents:
                self.logger.warning("Strategist: No intents passed filtering")
                self.stats.record_cycle(False, time.time() - start_time, ai_call_time, "Filtered out")
                self.state = StrategistState.IDLE
                return False
            
            # Step 8: Convert intents to commands and execute
            with self._lock:
                self.state = StrategistState.EXECUTING
            
            self.logger.debug(f"Strategist: Executing {len(intents)} intents")
            executed_count = self._execute_intents(intents, game_state)
            
            # Record statistics
            processing_time = time.time() - processing_start
            self.stats.record_cycle(
                True, processing_time, ai_call_time
            )
            self.stats.total_intents += len(intents)
            self.stats.executed_intents += executed_count
            self.stats.failed_intents += (len(intents) - executed_count)
            
            self.logger.info(
                f"Strategist: Cycle complete - {len(intents)} intents, "
                f"{executed_count} executed, {processing_time:.2f}s"
            )
            
            self.state = StrategistState.IDLE
            return True
            
        except Exception as e:
            self.logger.error(f"Strategist: Cycle failed with error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            self.stats.record_cycle(
                False, time.time() - start_time, ai_call_time, str(e)
            )
            self.state = StrategistState.ERROR
            
            # Trigger fallback if configured
            if self.config.fallback_on_error:
                self.fallback_manager.trigger_fallback(f"Strategist error: {e}")
            
            return False
    
    def _get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get the current game state."""
        if self.state_manager:
            state = self.state_manager.get_current_state()
            if state:
                return state
        
        # Fallback: try to get state from history
        if self._history_manager:
            recent = self._history_manager.get_recent_states(1)
            if recent:
                return recent[0].to_dict() if hasattr(recent[0], 'to_dict') else recent[0]
        
        return None
    
    def _generate_prompts(self, game_state: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate system and user prompts for Mistral.
        
        Args:
            game_state: Current game state
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Update prompt engine with current game info
        faction = Faction(game_state.get("faction", "allies"))
        phase_str = game_state.get("phase", "early")
        
        try:
            phase = GamePhase(phase_str)
        except ValueError:
            phase = GamePhase.EARLY
        
        self._prompt_engine.set_faction(faction)
        self._prompt_engine.set_game_phase(phase)
        
        # Generate system prompt
        system_prompt = self._prompt_engine.generate_system_prompt()
        
        # Generate user prompt with game state
        user_prompt = self._prompt_engine.generate_user_prompt(
            game_state,
            self._get_history()
        )
        
        return system_prompt, user_prompt
    
    def _get_history(self) -> List[Dict[str, Any]]:
        """Get game history for context."""
        if self._history_manager and self.config.include_history:
            return self._history_manager.get_all_entries()
        return []
    
    def _check_rate_limit(self) -> bool:
        """Check if we're rate limited."""
        if not self.rate_limiter:
            return True
        
        # Check if call is allowed
        result = self.rate_limiter.check_call(CallType.STRATEGIC)
        
        if result == "rate_limited" or result == "budget_exceeded":
            self.logger.warning(f"Strategist: Rate limited - {result.value}")
            
            if self.config.fallback_on_rate_limit:
                self.fallback_manager.trigger_fallback(f"Rate limited: {result.value}")
            
            return False
        
        return True
    
    def _call_mistral(self, system_prompt: str, user_prompt: str) -> MistralResponse:
        """
        Call Mistral API with prompts.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            
        Returns:
            MistralResponse
        """
        if not self._mistral_client:
            raise RuntimeError("Mistral client not available")
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Call API
        response = self._mistral_client.chat_completion(
            messages=messages,
            model=self._mistral_client.get_model(),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        # Record the call in rate limiter
        if self.rate_limiter:
            self.rate_limiter.record_call(
                CallType.STRATEGIC,
                tokens_used=response.usage.get("total_tokens", 0),
                latency=response.response_time,
                success=True
            )
        
        return response
    
    def _parse_intents(self, response: MistralResponse) -> List[StrategicIntent]:
        """
        Parse intents from Mistral response.
        
        Args:
            response: Mistral API response
            
        Returns:
            List of StrategicIntent objects
        """
        intents = []
        
        try:
            # Parse JSON response
            content = response.content.strip()
            
            # Try to parse as JSON
            if content.startswith("{") or content.startswith("["):
                data = json.loads(content)
            else:
                # Try to extract JSON from response
                # Sometimes Mistral wraps JSON in markdown code blocks
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    self.logger.warning(f"Strategist: Could not parse JSON from response: {content[:200]}")
                    return intents
            
            # Extract intents array
            if isinstance(data, dict):
                intents_data = data.get("intentions", [])
                if not intents_data and "choices" in data:
                    # Handle chat completion format
                    for choice in data.get("choices", []):
                        message = choice.get("message", {})
                        content = message.get("content", "")
                        try:
                            intent_data = json.loads(content)
                            intents_data = intent_data.get("intentions", [])
                        except:
                            pass
            elif isinstance(data, list):
                intents_data = data
            else:
                return intents
            
            # Parse each intent
            for intent_data in intents_data:
                try:
                    intent = StrategicIntent.from_dict(intent_data)
                    intents.append(intent)
                    
                    if self.config.log_intents:
                        self.logger.debug(f"Strategist: Parsed intent: {intent.intent} (confidence={intent.confidence})")
                except Exception as e:
                    self.logger.warning(f"Strategist: Failed to parse intent: {e}")
                    continue
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Strategist: JSON parse error: {e}")
            self.logger.debug(f"Response content: {response.content[:500]}")
        except Exception as e:
            self.logger.error(f"Strategist: Error parsing intents: {e}")
        
        return intents
    
    def _filter_intents(self, intents: List[StrategicIntent]) -> List[StrategicIntent]:
        """
        Filter intents based on confidence and priority thresholds.
        
        Args:
            intents: List of raw intents
            
        Returns:
            List of filtered intents
        """
        filtered = []
        
        for intent in intents:
            # Check confidence threshold
            if intent.confidence < self.config.min_confidence:
                self.logger.debug(f"Strategist: Filtered intent (low confidence): {intent.intent}")
                continue
            
            # Check priority threshold
            if intent.priority < self.config.min_priority:
                self.logger.debug(f"Strategist: Filtered intent (low priority): {intent.intent}")
                continue
            
            filtered.append(intent)
        
        # Sort by priority (highest first)
        filtered.sort(key=lambda x: x.priority, reverse=True)
        
        # Limit to max intents per cycle
        if len(filtered) > self.config.max_intents_per_cycle:
            self.logger.debug(
                f"Strategist: Truncating intents from {len(filtered)} to {self.config.max_intents_per_cycle}"
            )
            filtered = filtered[:self.config.max_intents_per_cycle]
        
        return filtered
    
    def _execute_intents(self, intents: List[StrategicIntent], 
                         game_state: Dict[str, Any]) -> int:
        """
        Execute strategic intents by converting to commands.
        
        Args:
            intents: List of intents to execute
            game_state: Current game state for validation
            
        Returns:
            Number of successfully executed intents
        """
        executed_count = 0
        
        if not self.command_processor:
            self.logger.error("Strategist: No command processor available")
            return 0
        
        # Update safety filter with current game state
        if self.safety_filter:
            self.safety_filter.update_game_state(game_state)
        
        for intent in intents:
            try:
                # Convert intent to command(s)
                commands = self._intent_to_commands(intent)
                
                if not commands:
                    self.logger.warning(f"Strategist: No commands generated for intent: {intent.intent}")
                    continue
                
                # Add commands to processor
                for cmd in commands:
                    # Validate command
                    if not self._validate_command(cmd, game_state):
                        self.logger.warning(f"Strategist: Command validation failed: {cmd}")
                        continue
                    
                    # Add to command processor
                    if self.command_processor.add_command(cmd):
                        executed_count += 1
                        self.logger.info(
                            f"Strategist: Added command {cmd.command_type} "
                            f"(intent: {intent.intent}, confidence: {intent.confidence:.2f})"
                        )
                    else:
                        self.logger.warning(f"Strategist: Failed to add command: {cmd.command_type}")
                
            except Exception as e:
                self.logger.error(f"Strategist: Error executing intent {intent.intent}: {e}")
                continue
        
        return executed_count
    
    def _intent_to_commands(self, intent: StrategicIntent) -> List[AICommand]:
        """
        Convert a strategic intent to AICommand objects.
        
        Args:
            intent: Strategic intent
            
        Returns:
            List of AICommand objects
        """
        commands = []
        
        # Get intent type mapping
        intent_type_str = intent.intent.upper()
        
        try:
            intent_type = IntentType(intent_type_str)
        except ValueError:
            self.logger.warning(f"Strategist: Unknown intent type: {intent_type_str}")
            return commands
        
        mapping = INTENT_TO_COMMAND.get(intent_type)
        if not mapping:
            self.logger.warning(f"Strategist: No command mapping for intent: {intent_type_str}")
            return commands
        
        command_type = mapping["command"]
        required_params = mapping.get("required_params", [])
        optional_params = mapping.get("optional_params", [])
        
        # Build command parameters
        cmd_params = {}
        
        # Copy intent parameters
        for key, value in intent.parameters.items():
            cmd_params[key] = value
        
        # Check required parameters
        missing = [p for p in required_params if p not in cmd_params]
        if missing:
            self.logger.warning(
                f"Strategist: Missing required parameters for {intent_type_str}: {missing}"
            )
            return commands
        
        # Create command
        try:
            cmd = AICommand(
                command_type=command_type,
                target=None,
                parameters=cmd_params,
                priority=self._intent_priority_to_command_priority(intent.priority),
                timestamp=time.time()
            )
            commands.append(cmd)
        except Exception as e:
            self.logger.error(f"Strategist: Failed to create command for intent {intent_type_str}: {e}")
        
        return commands
    
    def _intent_priority_to_command_priority(self, intent_priority: int) -> CommandPriority:
        """Convert intent priority to command priority."""
        if intent_priority >= 8:
            return CommandPriority.URGENT
        elif intent_priority >= 6:
            return CommandPriority.HIGH
        elif intent_priority >= 4:
            return CommandPriority.NORMAL
        else:
            return CommandPriority.LOW
    
    def _validate_command(self, command: AICommand, game_state: Dict[str, Any]) -> bool:
        """
        Validate a command before execution.
        
        Args:
            command: Command to validate
            game_state: Current game state
            
        Returns:
            True if valid, False otherwise
        """
        # Convert command to dict for validation
        cmd_dict = self._command_to_dict(command)
        
        # Validate with action validator
        if self.validator:
            result = self.validator.validate(cmd_dict)
            if not result.is_valid:
                self.logger.warning(f"Strategist: Validation failed: {result.errors}")
                return False
        
        # Validate with safety filter
        if self.safety_filter:
            result = self.safety_filter.check_command(cmd_dict)
            if not result.is_safe:
                self.logger.warning(f"Strategist: Safety check failed: {result.errors}")
                return False
        
        return True
    
    def _command_to_dict(self, command: AICommand) -> Dict[str, Any]:
        """Convert AICommand to dictionary for validation."""
        cmd_dict = {
            "command": command.command_type,
            "timestamp": command.timestamp
        }
        
        # Add parameters
        for key, value in command.parameters.items():
            cmd_dict[key] = value
        
        return cmd_dict
    
    def get_stats(self) -> StrategistStats:
        """Get strategist statistics."""
        return self.stats
    
    def reset_stats(self) -> None:
        """Reset strategist statistics."""
        self.stats = StrategistStats()
    
    def set_config(self, config: StrategistConfig) -> None:
        """Set strategist configuration."""
        self.config = config
        
        # Update Mistral client if model changed
        if self._mistral_client and hasattr(self.config, 'model'):
            try:
                model = MistralModel(self.config.model)
                self._mistral_client.set_model(model)
            except:
                pass
        
        self.logger.info("Strategist configuration updated")
    
    def get_config(self) -> StrategistConfig:
        """Get current configuration."""
        return self.config


# ============================================
# Factory Functions
# ============================================

_default_strategist: Optional[Strategist] = None


def get_strategist(state_manager: Optional[StateManager] = None,
                   command_processor: Optional[CommandProcessor] = None,
                   config: Optional[StrategistConfig] = None) -> Strategist:
    """
    Get or create the default Strategist singleton.
    
    Args:
        state_manager: Optional state manager
        command_processor: Optional command processor
        config: Optional configuration
        
    Returns:
        Strategist instance
    """
    global _default_strategist
    if _default_strategist is None:
        _default_strategist = Strategist(
            config=config,
            state_manager=state_manager,
            command_processor=command_processor
        )
    return _default_strategist


def reset_strategist() -> None:
    """Reset the default Strategist singleton."""
    global _default_strategist
    if _default_strategist is not None:
        _default_strategist.stop()
    _default_strategist = None


def create_strategist(config: Optional[StrategistConfig] = None,
                      state_manager: Optional[StateManager] = None,
                      command_processor: Optional[CommandProcessor] = None) -> Strategist:
    """
    Create a new Strategist instance.
    
    Args:
        config: Optional configuration
        state_manager: Optional state manager
        command_processor: Optional command processor
        
    Returns:
        New Strategist instance
    """
    return Strategist(
        config=config,
        state_manager=state_manager,
        command_processor=command_processor
    )


if __name__ == "__main__":
    # Test the strategist
    print("Testing Strategist...")
    
    try:
        from orchestrator.state_manager import StateManager
        from orchestrator.command_processor import CommandProcessor
        from config import Configuration
        
        # Create configuration
        config = Configuration()
        
        # Create state manager
        state_manager = StateManager(config)
        
        # Create command processor
        command_processor = CommandProcessor(config)
        
        # Create strategist
        strategist = create_strategist(
            config=StrategistConfig(
                enabled=True,
                model="mistral-small-latest",
                temperature=0.7,
                max_tokens=2048,
                json_mode=True
            ),
            state_manager=state_manager,
            command_processor=command_processor
        )
        
        if strategist.start():
            print("Strategist started successfully")
            
            # Test with mock state
            test_state = {
                "game_time": 120.5,
                "phase": "early",
                "faction": "allies",
                "player_id": 1,
                "resources": {
                    "manpower": {"current": 500, "income": 10, "max": 1000},
                    "fuel": {"current": 300, "income": 5, "max": 800},
                    "munitions": {"current": 200, "income": 3, "max": 600}
                },
                "squads": [
                    {"id": 1, "type": "riflemen", "health": 0.8, "max_health": 1.0, 
                     "pos": [100, 200, 0], "posture": "defensive"}
                ],
                "cps": [
                    {"id": 1, "pos": [500, 500, 0], "owner": 1, "capture_progress": 1.0}
                ],
                "tech": {
                    "tier_1": True,
                    "tier_2": False,
                    "tier_3": False,
                    "abilities": []
                },
                "queue": [],
                "pop": [11, 100]
            }
            
            # Add state to state manager
            state_manager.update_state(test_state)
            
            # Run a cycle (this will fail if API key is not set)
            try:
                success = strategist.run_cycle()
                if success:
                    print("Strategist cycle completed successfully")
                else:
                    print("Strategist cycle failed (expected if API key not configured)")
            except Exception as e:
                print(f"Strategist cycle error (expected): {e}")
            
            # Get stats
            stats = strategist.get_stats()
            print(f"Stats: {stats.total_cycles} cycles, {stats.total_intents} intents")
            
            strategist.stop()
        
        print("\nStrategist test completed")
        
    except Exception as e:
        print(f"Strategist test failed: {e}")
        import traceback
        traceback.print_exc()
