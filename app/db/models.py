from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    hashed_password: str
    role: str

class Challenge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str
    matiere: str
    date: str

class LeaderboardEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    challenge_id: int
    user_id: int
    score: int
    rank: int

class Token(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    token: str
    is_active: bool = True 