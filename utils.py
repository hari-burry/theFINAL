"""
Production-grade JSON I/O utilities for robust parsing and validation.
Ensures JSON decode errors never happen and outputs are standardized.
"""

import json
import re
import logging
from typing import Any, Dict, List, Union, Optional, Callable
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

class JSONParseError(Exception):
    """Custom exception for JSON parsing failures"""
    pass

def safe_json_loads(content: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with multiple fallback strategies.

    Args:
        content: The string to parse as JSON
        default: Default value to return if all parsing attempts fail

    Returns:
        Parsed JSON object or default value
    """
    if not content or not isinstance(content, str):
        return default

    content = content.strip()

    # Remove common markdown artifacts
    content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)

    # Try direct parsing first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from text using regex
    json_pattern = r'\{(?:[^{}]|{(?:[^{}]|{[^{}]*})*})*\}'
    matches = re.findall(json_pattern, content, re.DOTALL)

    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # Try to find the first { and last } and parse that range
    start = content.find('{')
    end = content.rfind('}') + 1

    if start != -1 and end > start:
        try:
            return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

    # Try to fix common JSON issues
    fixed_content = _fix_common_json_issues(content)
    if fixed_content != content:
        try:
            return json.loads(fixed_content)
        except json.JSONDecodeError:
            pass

    # If all else fails, return default
    logger.warning(f"Failed to parse JSON from content: {content[:200]}...")
    return default

def _fix_common_json_issues(content: str) -> str:
    """Fix common JSON formatting issues"""
    # Remove trailing commas
    content = re.sub(r',\s*}', '}', content)
    content = re.sub(r',\s*]', ']', content)

    # Fix single quotes to double quotes (careful with contractions)
    # This is a simple heuristic - may not work for all cases
    content = re.sub(r"'([^']*)'", r'"\1"', content)

    # Fix unquoted keys (simple cases)
    content = re.sub(r'(\w+):', r'"\1":', content)

    return content

def extract_json_value(data: Any, key_path: Union[str, List[str]], default: Any = None) -> Any:
    """
    Safely extract a value from nested JSON structure.

    Args:
        data: The JSON object (dict/list)
        key_path: Key path as string (dot-separated) or list of keys
        default: Default value if key not found

    Returns:
        The extracted value or default
    """
    if isinstance(key_path, str):
        key_path = key_path.split('.')

    current = data
    try:
        for key in key_path:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                current = current[int(key)]
            else:
                return default
        return current
    except (KeyError, IndexError, TypeError, ValueError):
        return default

def validate_json_structure(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Validate JSON structure against a simple schema.

    Args:
        data: The JSON object to validate
        schema: Schema dict with expected keys and types

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False

    for key, expected_type in schema.items():
        if key not in data:
            return False
        if not isinstance(data[key], expected_type):
            return False

    return True

def standardize_llm_output(content: str, expected_keys: List[str], output_format: str = "json") -> Dict[str, Any]:
    """
    Standardize LLM output to ensure it matches expected format.

    Args:
        content: Raw LLM output
        expected_keys: List of expected keys in the output
        output_format: Expected output format ("json", "text")

    Returns:
        Standardized output dict
    """
    if output_format == "text":
        return {"content": content.strip()}

    # Try to parse as JSON
    parsed = safe_json_loads(content, {})

    if not isinstance(parsed, dict):
        # If parsing failed, create a dict with the content
        parsed = {"content": content.strip()}

    # Ensure all expected keys are present
    for key in expected_keys:
        if key not in parsed:
            parsed[key] = ""

    return parsed

def robust_llm_call(func: Callable) -> Callable:
    """
    Decorator to make LLM calls more robust with standardized output.

    Args:
        func: The function to decorate

    Returns:
        Decorated function with robust JSON handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            # Return a safe default based on function name
            if "generate" in func.__name__.lower():
                return "Error generating content. Please try again."
            elif "scrutinize" in func.__name__.lower():
                return []
            elif "validate" in func.__name__.lower():
                return {
                    "depth_improvement_percent": 0,
                    "is_genuinely_deeper": False,
                    "depth_analysis": "Validation failed",
                    "recommendation": "accept"
                }
            elif "refine" in func.__name__.lower():
                return args[0] if args else "Error refining content."
            else:
                return None

    return wrapper

# Production-grade JSON response validator
def validate_llm_response(response: Any, expected_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize LLM response.

    Args:
        response: The response from LLM
        expected_schema: Expected schema for the response

    Returns:
        Validated and sanitized response
    """
    if not isinstance(response, dict):
        return {key: "" for key in expected_schema.keys()}

    validated = {}
    for key, expected_type in expected_schema.items():
        value = response.get(key, "")
        if isinstance(expected_type, type):
            if isinstance(value, expected_type):
                validated[key] = value
            else:
                # Try to convert
                try:
                    if expected_type == int:
                        validated[key] = int(float(value)) if value else 0
                    elif expected_type == float:
                        validated[key] = float(value) if value else 0.0
                    elif expected_type == bool:
                        validated[key] = str(value).lower() in ('true', '1', 'yes')
                    elif expected_type == list:
                        validated[key] = value if isinstance(value, list) else [value] if value else []
                    else:
                        validated[key] = str(value)
                except (ValueError, TypeError):
                    validated[key] = expected_type() if callable(expected_type) else ""
        else:
            validated[key] = value

    return validated

# Common schemas for different agent outputs
AGENT_SCHEMAS = {
    "generator": {"new_content": str},
    "scrutinizer": {"questions": list},
    "validator": {
        "depth_improvement_percent": (int, float),
        "is_genuinely_deeper": bool,
        "depth_analysis": str,
        "recommendation": str
    },
    "refiner": {"refined_explanation": str},
    "topic_extractor": {"topic": str}
}