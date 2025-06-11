from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

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

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_hash: str = Field(unique=True, description="MD5 hash of the file content")
    filename: str
    matiere: str
    file_path: str = Field(description="Relative path from cours directory")
    document_type: str = Field(description="File extension without dot (md, pdf, etc.)")
    is_exam: bool = Field(default=False, description="Whether this document is an exam")
    file_size: int = Field(description="File size in bytes")
    upload_date: datetime = Field(default_factory=datetime.now, description="When the document was first added")
    last_modified: datetime = Field(default_factory=datetime.now, description="Last modification time of the file")
    last_indexed: Optional[datetime] = Field(default=None, description="When this document was last indexed in the vector database")
    is_indexed: bool = Field(default=False, description="Whether this document is currently in the vector index")

class Challenge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ref: Optional[str] = Field(default=None)  # ex: "SYD-001"
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