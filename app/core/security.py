"""Security utilities for JWT authentication."""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Union, Any
from app.core.config import settings

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.TOKEN_SECRET_KEY, 
        algorithm=settings.TOKEN_ALGORITHM
    )
    
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload
    """
    return jwt.decode(
        token,
        settings.TOKEN_SECRET_KEY,
        algorithms=[settings.TOKEN_ALGORITHM]
    ) 