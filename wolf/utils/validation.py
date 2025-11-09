"""
Wolf CLI Validation Utilities

Parameter validation for tools and configuration.
"""

import re
from typing import Any, Dict
from jsonschema import validate, ValidationError as JSONSchemaValidationError


def validate_tool_params(params: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate tool parameters against JSON schema
    
    Args:
        params: Parameters to validate
        schema: JSON Schema for parameters
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        validate(instance=params, schema=schema)
        return True, ""
    except JSONSchemaValidationError as e:
        return False, str(e.message)
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def is_valid_regex(pattern: str) -> bool:
    """
    Check if a string is a valid regex pattern
    
    Args:
        pattern: Regex pattern to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False


def sanitize_command(command: str) -> str:
    """
    Basic sanitization of shell commands (remove dangerous sequences)
    
    Args:
        command: Command to sanitize
        
    Returns:
        Sanitized command
    """
    # This is basic - permission_manager has more comprehensive checks
    # Remove null bytes
    command = command.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    command = command.strip()
    
    return command
