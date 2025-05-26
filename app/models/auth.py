"""Authentication models."""
from pydantic import BaseModel, Field
from typing import Optional

class TokenAuthRequest(BaseModel):
    """Model for authenticating with a pre-generated token."""
    token: str = Field(..., description="Pre-generated authentication token")

class TokenResponse(BaseModel):
    """Model for access token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour in seconds
    user_info: dict = Field(..., description="User information")
    
class UserInDB(BaseModel):
    """Model representing a user stored in the database."""
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    role: str = "student"  # "student", "teacher", "admin"
    auth_token: str = Field(..., description="Pre-generated authentication token")

class TokenInDB(BaseModel):
    """Model representing a valid token in the database."""
    token: str = Field(..., description="The authentication token")
    user_id: str = Field(..., description="Associated user ID")
    is_active: bool = Field(True, description="Whether the token is active")
    role: str = Field(..., description="User role")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = None
    email: Optional[str] = None 