"""Models for challenges management."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date as date_type


class ChallengeBase(BaseModel):
    """Base model for a challenge."""
    matiere: str = Field(..., description="Subject involved in the challenge")
    date: str = Field(..., description="Challenge date (YYYY-MM-DD)")

class ChallengeCreate(ChallengeBase):
    """Model for creating a new challenge."""
    question: str = Field(..., description="Challenge question")

class ChallengeResponse(ChallengeBase):
    """Model for challenge response."""
    challenge_id: str = Field(..., description="Unique challenge ID")
    question: str = Field(..., description="Challenge question")
    
class ChallengeUserResponse(BaseModel):
    """Model for a user's response to a challenge."""
    user_id: str = Field(..., description="User ID")
    response: str = Field(..., description="User's answer to the challenge")

class LeaderboardEntry(BaseModel):
    """Model for a leaderboard entry."""
    user_id: str = Field(..., description="User ID")
    username: Optional[str] = Field(None, description="Username")
    score: int = Field(..., description="User's score")
    rank: int = Field(..., description="User's ranking position") 