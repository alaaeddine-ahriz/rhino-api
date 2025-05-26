"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from datetime import timedelta
from typing import List

from app.core.security import create_access_token
from app.models.auth import TokenAuthRequest, TokenResponse, UserInDB, TokenInDB
from app.models.base import ApiResponse
from app.api.deps import get_user_from_token, get_admin_user, VALID_TOKENS_DB
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/token", response_model=TokenResponse)
async def authenticate_with_token(request: TokenAuthRequest):
    """
    Authenticate using a pre-generated token and get a JWT access token.
    
    Args:
        request: Contains the pre-generated authentication token
        
    Returns:
        JWT access token and user information
    """
    # Validate the pre-generated token
    user = get_user_from_token(request.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Create a JWT access token
    access_token_expires = timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username, 
            "user_id": user.id,
            "role": user.role
        }, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "user_info": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role
        }
    }

@router.get("/tokens", response_model=ApiResponse)
async def list_valid_tokens(current_user: UserInDB = Depends(get_admin_user)):
    """
    List all valid authentication tokens (admin only).
    
    Returns:
        List of all valid tokens with user information
    """
    tokens_info = []
    for token, token_data in VALID_TOKENS_DB.items():
        tokens_info.append({
            "token": token,
            "user_id": token_data.user_id,
            "username": token_data.username,
            "role": token_data.role,
            "full_name": token_data.full_name,
            "email": token_data.email,
            "is_active": token_data.is_active
        })
    
    return {
        "success": True,
        "message": f"{len(tokens_info)} tokens trouvés",
        "data": {"tokens": tokens_info}
    } 