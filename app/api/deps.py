"""Dependencies for API endpoints."""
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional, Dict, Any

from app.core.security import decode_token
from app.core.exceptions import AuthenticationError
from app.models.auth import UserInDB, TokenInDB

# HTTPBearer for token authentication
security = HTTPBearer()

# Mock token database - in a real app, this would be a database
VALID_TOKENS_DB = {
    # Student tokens
    "student_token_123": TokenInDB(
        token="student_token_123",
        user_id="1",
        is_active=True,
        role="student",
        username="student1",
        full_name="Student One",
        email="student1@example.com"
    ),
    "student_token_456": TokenInDB(
        token="student_token_456",
        user_id="4",
        is_active=True,
        role="student",
        username="student2",
        full_name="Student Two",
        email="student2@example.com"
    ),
    
    # Teacher tokens
    "teacher_token_789": TokenInDB(
        token="teacher_token_789",
        user_id="2",
        is_active=True,
        role="teacher",
        username="teacher1",
        full_name="Teacher One",
        email="teacher1@example.com"
    ),
    "teacher_token_101": TokenInDB(
        token="teacher_token_101",
        user_id="5",
        is_active=True,
        role="teacher",
        username="teacher2",
        full_name="Teacher Two",
        email="teacher2@example.com"
    ),
    
    # Admin tokens
    "admin_token_999": TokenInDB(
        token="admin_token_999",
        user_id="3",
        is_active=True,
        role="admin",
        username="admin1",
        full_name="Admin One",
        email="admin1@example.com"
    ),
}

def get_user_from_token(token: str) -> Optional[UserInDB]:
    """
    Get user information from a pre-generated token.
    
    Args:
        token (str): Pre-generated authentication token
        
    Returns:
        UserInDB: User object if token is valid, None otherwise
    """
    token_data = VALID_TOKENS_DB.get(token)
    if not token_data or not token_data.is_active:
        return None
        
    return UserInDB(
        id=token_data.user_id,
        username=token_data.username,
        email=token_data.email,
        full_name=token_data.full_name,
        role=token_data.role,
        disabled=False,
        auth_token=token_data.token
    )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """
    Validate pre-generated token and return current user.
    
    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token credentials
        
    Returns:
        UserInDB: Current user object
        
    Raises:
        AuthenticationError: If token is invalid or user not found
    """
    token = credentials.credentials
    
    user = get_user_from_token(token)
    if user is None:
        raise AuthenticationError("Invalid or expired token")
        
    return user
    
async def get_teacher_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Check if the current user is a teacher or admin.
    
    Args:
        current_user (UserInDB): Current user from token
        
    Returns:
        UserInDB: Current user if they're a teacher or admin
        
    Raises:
        HTTPException: If user doesn't have required permissions
    """
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource. Teacher or admin role required.",
        )
    return current_user
    
async def get_admin_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Check if the current user is an admin.
    
    Args:
        current_user (UserInDB): Current user from token
        
    Returns:
        UserInDB: Current user if they're an admin
        
    Raises:
        HTTPException: If user doesn't have required permissions
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user 