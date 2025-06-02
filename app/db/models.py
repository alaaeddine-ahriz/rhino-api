from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    role: str
    subscriptions: Optional[str] = Field(default="", description="Liste des matières auxquelles l'utilisateur est abonné, séparées par des virgules")

class Matiere(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    granularite: str = Field(default="semaine", description="jour|semaine|mois|2jours...")

class Challenge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ref: str  # ex: "SYD-001"
    question: str
    matiere: str
    date: str

class ChallengeServed(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    matiere: str
    granularite: str
    challenge_ref: str
    tick: int

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