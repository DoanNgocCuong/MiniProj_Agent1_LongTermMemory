"""
Utility helper functions.
"""
from typing import Any, Dict
import hashlib


def generate_hash(text: str) -> str:
    """
    Generate MD5 hash for text.
    
    Args:
        text: Text to hash
        
    Returns:
        Hex digest of hash
    """
    return hashlib.md5(text.encode()).hexdigest()


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary values.
    
    Args:
        data: Dictionary to search
        *keys: Key path (e.g., "user", "profile", "name")
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key, default)
        else:
            return default
        if result is None:
            return default
    return result

