"""
CoH1 × Mistral AI Mod - Action Validator

Validates AI commands before execution to ensure they are legal and well-formed.
This module enforces a whitelist of allowed commands and validates their structure.

Responsibilities:
- Maintain whitelist of legal command types
- Validate command structure and required fields
- Validate command parameter types and formats
- Provide custom validation hooks
- Log validation errors for debugging

Author: Generated via developer skill
Version: 1.0.0
Date: 2026-10-18

Usage:
    from validator import ActionValidator, ValidationError
    
    validator = ActionValidator()
    
    # Validate a command
    try:
        is_valid = validator.validate(command)
    except ValidationError as e:
        print(f"Validation failed: {e}")
    
    # Add custom validator
    validator.add_validator("custom_check", my_validation_function)
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum


# ============================================
# Command Types
# ============================================

class CommandType(Enum):
    """Supported command types for the AI."""
    BUILD = "BUILD"
    CAPTURE = "CAPTURE"
    ATTACK_MOVE = "ATTACK_MOVE"
    SET_POSTURE = "SET_POSTURE"
    PRODUCE = "PRODUCE"
    RETREAT = "RETREAT"
    STOP = "STOP"
    HOLD = "HOLD"
    PING = "PING"
    PONG = "PONG"


# Default whitelist of allowed command types
DEFAULT_COMMAND_WHITELIST = [
    CommandType.BUILD,
    CommandType.CAPTURE,
    CommandType.ATTACK_MOVE,
    CommandType.SET_POSTURE,
    CommandType.PRODUCE,
    CommandType.RETREAT,
    CommandType.STOP,
    CommandType.HOLD,
    CommandType.PING,
    CommandType.PONG,
]


@dataclass
class ValidationError(Exception):
    """Exception raised when command validation fails."""
    message: str
    command: Optional[Dict[str, Any]] = None
    field: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    
    def __str__(self) -> str:
        parts = [f"ValidationError: {self.message}"]
        if self.command:
            parts.append(f"Command: {self.command}")
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.expected and self.actual:
            parts.append(f"Expected: {self.expected}, Got: {self.actual}")
        return " | ".join(parts)


@dataclass
class ValidationResult:
    """Result of command validation."""
    is_valid: bool
    command: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "command": self.command,
        }


@dataclass
class ValidatorStats:
    """Statistics for the validator."""
    total_validations: int = 0
    passed: int = 0
    failed: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    warnings_by_type: Dict[str, int] = field(default_factory=dict)
    
    def record_validation(self, result: ValidationResult) -> None:
        """Record a validation result."""
        self.total_validations += 1
        if result.is_valid:
            self.passed += 1
        else:
            self.failed += 1
            for error in result.errors:
                error_type = error.split(":")[0] if ":" in error else "unknown"
                self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
            for warning in result.warnings:
                warning_type = warning.split(":")[0] if ":" in warning else "unknown"
                self.warnings_by_type[warning_type] = self.warnings_by_type.get(warning_type, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_validations": self.total_validations,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": self.passed / self.total_validations if self.total_validations > 0 else 0,
            "errors_by_type": self.errors_by_type,
            "warnings_by_type": self.warnings_by_type,
        }


class ActionValidator:
    """
    Validates AI commands before execution.
    
    Ensures commands are:
    1. In the whitelist of allowed command types
    2. Have all required fields
    3. Have correctly typed parameters
    4. Pass custom validation rules
    """
    
    # Required fields for each command type
    REQUIRED_FIELDS = {
        CommandType.BUILD: ["engineer_id", "building_type", "position"],
        CommandType.CAPTURE: ["squad_id", "point_id"],
        CommandType.ATTACK_MOVE: ["squad_id", "position"],
        CommandType.SET_POSTURE: ["squad_id", "posture"],
        CommandType.PRODUCE: ["building_id", "unit_type"],
        CommandType.RETREAT: ["squad_id"],
        CommandType.STOP: ["squad_id"],
        CommandType.HOLD: ["squad_id"],
        CommandType.PING: ["timestamp"],
        CommandType.PONG: ["timestamp"],
    }
    
    # Valid values for specific fields
    VALID_VALUES = {
        "posture": ["aggressive", "defensive", "retreat", "hold"],
    }
    
    # Expected types for fields
    EXPECTED_TYPES = {
        "engineer_id": int,
        "squad_id": int,
        "point_id": int,
        "building_id": int,
        "building_type": str,
        "unit_type": str,
        "position": (list, tuple),
        "posture": str,
        "timestamp": (int, float),
        "command": str,
    }
    
    def __init__(self, whitelist: Optional[List[CommandType]] = None, 
                 strict_mode: bool = False, log_errors: bool = True):
        """
        Initialize the action validator.
        
        Args:
            whitelist: List of allowed command types (defaults to all supported types)
            strict_mode: If True, raise ValidationError on failure instead of returning False
            log_errors: If True, log validation errors
        """
        self.whitelist = whitelist.copy() if whitelist is not None else DEFAULT_COMMAND_WHITELIST.copy()
        self.strict_mode = strict_mode
        self.log_errors = log_errors
        self.logger = logging.getLogger(__name__)
        
        # Custom validators: dict of name -> validator function
        self.custom_validators: Dict[str, Callable[[Dict[str, Any]], Optional[str]]] = {}
        
        # Statistics
        self.stats = ValidatorStats()
        
        # Type checking cache for performance
        self._type_cache: Dict[str, type] = {}
        
        self.logger.info(f"ActionValidator initialized with {len(self.whitelist)} whitelisted commands")
        if strict_mode:
            self.logger.info("Strict mode enabled - will raise ValidationError on failure")
    
    def validate(self, command: Dict[str, Any]) -> ValidationResult:
        """
        Validate a command.
        
        Args:
            command: The command dictionary to validate
            
        Returns:
            ValidationResult with is_valid, errors, warnings
            
        Raises:
            ValidationError: If strict_mode is True and validation fails
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Check command is a dict
        if not isinstance(command, dict):
            errors.append("Command must be a dictionary")
            result = ValidationResult(is_valid=False, command=command, errors=errors)
            self.stats.record_validation(result)
            if self.log_errors:
                self.logger.error(f"Validation failed: {errors[0]}")
            if self.strict_mode:
                raise ValidationError(errors[0], command=command)
            return result
        
        # Check command type exists
        command_type_str = command.get("command")
        if command_type_str is None:
            errors.append("Command missing 'command' field")
            result = ValidationResult(is_valid=False, command=command, errors=errors)
            self.stats.record_validation(result)
            if self.log_errors:
                self.logger.error(f"Validation failed: {errors[0]}")
            if self.strict_mode:
                raise ValidationError(errors[0], command=command)
            return result
        
        # Check command type is in whitelist
        try:
            command_type = CommandType(command_type_str)
        except ValueError:
            errors.append(f"Unknown command type: {command_type_str}")
            result = ValidationResult(is_valid=False, command=command, errors=errors)
            self.stats.record_validation(result)
            if self.log_errors:
                self.logger.error(f"Validation failed: {errors[0]}")
            if self.strict_mode:
                raise ValidationError(errors[0], command=command, field="command")
            return result
        
        if command_type not in self.whitelist:
            errors.append(f"Command type '{command_type_str}' not in whitelist")
            result = ValidationResult(is_valid=False, command=command, errors=errors)
            self.stats.record_validation(result)
            if self.log_errors:
                self.logger.warning(f"Command not in whitelist: {command_type_str}")
            if self.strict_mode:
                raise ValidationError(errors[0], command=command, field="command")
            return result
        
        # Check required fields
        required_fields = self.REQUIRED_FIELDS.get(command_type, [])
        for field_name in required_fields:
            if field_name not in command:
                errors.append(f"Missing required field '{field_name}' for {command_type_str}")
        
        # Check field types
        for field_name, value in command.items():
            expected_type = self.EXPECTED_TYPES.get(field_name)
            if expected_type is not None:
                if not self._check_type(value, expected_type):
                    errors.append(
                        f"Field '{field_name}' has wrong type. "
                        f"Expected {self._type_to_str(expected_type)}, "
                        f"got {type(value).__name__}"
                    )
        
        # Check valid values for specific fields
        for field_name, valid_values in self.VALID_VALUES.items():
            if field_name in command and command[field_name] not in valid_values:
                errors.append(
                    f"Field '{field_name}' has invalid value '{command[field_name]}'. "
                    f"Valid values: {valid_values}"
                )
        
        # Check position format (should be list/tuple of 3 numbers)
        if "position" in command and command["position"] is not None:
            pos_errors = self._validate_position(command["position"])
            errors.extend(pos_errors)
        
        # Run custom validators
        for validator_name, validator_func in self.custom_validators.items():
            error_msg = validator_func(command)
            if error_msg:
                errors.append(f"Custom validator '{validator_name}': {error_msg}")
        
        # Record result
        is_valid = len(errors) == 0
        result = ValidationResult(
            is_valid=is_valid,
            command=command,
            errors=errors,
            warnings=warnings
        )
        self.stats.record_validation(result)
        
        # Log result
        if self.log_errors:
            if is_valid:
                self.logger.debug(f"Command validated successfully: {command_type_str}")
            else:
                self.logger.warning(f"Command validation failed: {errors}")
        
        # Raise if strict mode
        if not is_valid and self.strict_mode:
            raise ValidationError(
                f"Validation failed with {len(errors)} errors",
                command=command,
                field=", ".join(errors)
            )
        
        return result
    
    def is_valid(self, command: Dict[str, Any]) -> bool:
        """
        Check if a command is valid.
        
        Args:
            command: The command to validate
            
        Returns:
            True if valid, False otherwise
        """
        return self.validate(command).is_valid
    
    def _check_type(self, value: Any, expected_type: Any) -> bool:
        """Check if value matches expected type(s)."""
        if isinstance(expected_type, tuple):
            return any(self._check_type(value, t) for t in expected_type)
        return isinstance(value, expected_type)
    
    def _type_to_str(self, type_obj: Any) -> str:
        """Convert type to string representation."""
        if isinstance(type_obj, tuple):
            return " | ".join(self._type_to_str(t) for t in type_obj)
        return type_obj.__name__
    
    def _validate_position(self, position: Any) -> List[str]:
        """Validate position format."""
        errors: List[str] = []
        
        if not isinstance(position, (list, tuple)):
            errors.append(f"Position must be a list/tuple, got {type(position).__name__}")
            return errors
        
        if len(position) != 3:
            errors.append(f"Position must have 3 elements (x, y, z), got {len(position)}")
            return errors
        
        for i, coord in enumerate(["x", "y", "z"]):
            if not isinstance(position[i], (int, float)):
                errors.append(
                    f"Position {coord} must be a number, got {type(position[i]).__name__}"
                )
        
        return errors
    
    def add_validator(self, name: str, validator_func: Callable[[Dict[str, Any]], Optional[str]]) -> None:
        """
        Add a custom validator function.
        
        Args:
            name: Name of the validator
            validator_func: Function that takes a command dict and returns error message or None
        """
        self.custom_validators[name] = validator_func
        self.logger.info(f"Added custom validator: {name}")
    
    def remove_validator(self, name: str) -> bool:
        """
        Remove a custom validator.
        
        Args:
            name: Name of the validator to remove
            
        Returns:
            True if validator was removed, False if not found
        """
        if name in self.custom_validators:
            del self.custom_validators[name]
            self.logger.info(f"Removed custom validator: {name}")
            return True
        return False
    
    def list_validators(self) -> List[str]:
        """List all validator names."""
        return list(self.custom_validators.keys())
    
    def get_whitelist(self) -> List[CommandType]:
        """Get the current command whitelist."""
        return self.whitelist.copy()
    
    def set_whitelist(self, whitelist: List[CommandType]) -> None:
        """Set the command whitelist."""
        self.whitelist = whitelist
        self.logger.info(f"Updated whitelist to {len(whitelist)} commands")
    
    def add_to_whitelist(self, command_type: CommandType) -> None:
        """Add a command type to the whitelist."""
        if command_type not in self.whitelist:
            self.whitelist.append(command_type)
            self.logger.info(f"Added to whitelist: {command_type.value}")
    
    def remove_from_whitelist(self, command_type: CommandType) -> bool:
        """Remove a command type from the whitelist."""
        if command_type in self.whitelist:
            self.whitelist.remove(command_type)
            self.logger.info(f"Removed from whitelist: {command_type.value}")
            return True
        return False
    
    def get_stats(self) -> ValidatorStats:
        """Get validation statistics."""
        return self.stats
    
    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self.stats = ValidatorStats()


# ============================================
# Factory Functions
# ============================================

_default_validator: Optional[ActionValidator] = None


def get_validator() -> ActionValidator:
    """Get the default validator instance (singleton)."""
    global _default_validator
    if _default_validator is None:
        _default_validator = ActionValidator()
    return _default_validator


def reset_validator() -> None:
    """Reset the default validator instance."""
    global _default_validator
    _default_validator = None


def validate_command(command: Dict[str, Any]) -> bool:
    """Validate a command using the default validator."""
    return get_validator().is_valid(command)


def create_validator(whitelist: Optional[List[CommandType]] = None,
                   strict_mode: bool = False,
                   log_errors: bool = True) -> ActionValidator:
    """
    Create a new validator instance.
    
    Args:
        whitelist: List of allowed command types
        strict_mode: If True, raise ValidationError on failure
        log_errors: If True, log validation errors
        
    Returns:
        New ActionValidator instance
    """
    return ActionValidator(whitelist=whitelist, strict_mode=strict_mode, log_errors=log_errors)


# ============================================
# Convenience Functions
# ============================================


def is_whitelisted(command_type: str) -> bool:
    """Check if a command type is in the default whitelist."""
    try:
        cmd_type = CommandType(command_type)
        return cmd_type in DEFAULT_COMMAND_WHITELIST
    except ValueError:
        return False


def get_supported_commands() -> List[str]:
    """Get list of all supported command type strings."""
    return [ct.value for ct in CommandType]


def get_whitelisted_commands() -> List[str]:
    """Get list of whitelisted command type strings."""
    return [ct.value for ct in DEFAULT_COMMAND_WHITELIST]
