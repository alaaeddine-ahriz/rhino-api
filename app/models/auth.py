"""Authentication models."""
from pydantic import BaseModel, Field
from typing import Optional

class UserInDB(BaseModel):
    """Model representing a user stored in the database."""
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    role: str = "student"  # "student", "teacher", "admin"
    auth_token: str = Field(default="simple_auth", description="Authentication method identifier")
    subscriptions: str = Field(default="", description="Comma-separated list of subscribed subjects") 