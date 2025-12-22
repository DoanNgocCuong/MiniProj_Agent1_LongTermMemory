"""
Security utilities for authentication and authorization.
"""
from typing import Optional
import hashlib
import secrets


def generate_api_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure API key.
    
    Args:
        length: Length of the API key in characters
        
    Returns:
        Random API key string
    """
    return secrets.token_urlsafe(length)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256.
    
    Args:
        api_key: The API key to hash
        
    Returns:
        Hashed API key (hex digest)
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash.
    
    Args:
        api_key: The API key to verify
        hashed_key: The stored hash
        
    Returns:
        True if the key matches, False otherwise
    """
    return hash_api_key(api_key) == hashed_key

