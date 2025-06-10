"""Dependencies for API endpoints."""
from fastapi import Depends, HTTPException, status
from typing import Optional
from sqlmodel import Session

from app.models.auth import UserInDB
from app.db.session import get_session
from app.db.models import User

def get_user_by_id(user_id: int, session: Session) -> Optional[UserInDB]:
    """
    Get user by ID for simple authentication (development only).
    
    Args:
        user_id: User ID
        session: Database session
        
    Returns:
        UserInDB: User object if found, None otherwise
    """
    try:
        db_user = session.get(User, user_id)
        if db_user:
            return UserInDB(
                id=str(db_user.id),
                username=db_user.username,
                email=db_user.email,
                full_name=db_user.username,
                role=db_user.role,
                disabled=False,
                auth_token="simple_auth",
                subscriptions=db_user.subscriptions or ""
            )
    except Exception:
        pass
    return None

async def get_current_user_simple(
    user_id: int,
    session: Session = Depends(get_session)
) -> UserInDB:
    """
    Simple authentication using just user ID (for development).
    
    Args:
        user_id: User ID
        session: Database session
        
    Returns:
        UserInDB: Current user object
        
    Raises:
        HTTPException: If user not found
    """
    user = get_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user 