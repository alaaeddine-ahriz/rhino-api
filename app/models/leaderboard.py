"""Leaderboard models for the API."""
from pydantic import BaseModel
from typing import Optional

class LeaderboardRequest(BaseModel):
    """Request model for leaderboard operations."""
    matiere: Optional[str] = None
    limit: Optional[int] = 10
    
class LeaderboardEntry(BaseModel):
    """Model representing a leaderboard entry."""
    user_id: int
    username: str
    score: int
    challenges_completed: int
    rank: int
    
class LeaderboardResponse(BaseModel):
    """Response model for leaderboard data."""
    entries: list[LeaderboardEntry]
    total_users: int
    current_user_rank: Optional[int] = None 