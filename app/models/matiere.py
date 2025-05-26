"""Models for subjects (matières) management."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class MatiereBase(BaseModel):
    """Base model for a subject."""
    name: str = Field(..., description="Subject name (e.g. 'MATH', 'PHYS')")
    description: Optional[str] = Field(None, description="Subject description")

class MatiereCreate(MatiereBase):
    """Model for creating a new subject."""
    pass

class MatiereResponse(MatiereBase):
    """Model for subject response."""
    document_count: int = Field(0, description="Number of documents in the subject")
    last_update: Optional[str] = Field(None, description="Last update timestamp")

class UpdateRequest(BaseModel):
    """Model for updating a subject's index."""
    matiere: str = Field(..., description="Subject name to update (e.g. 'MATH')")

class MatiereList(BaseModel):
    """Model for a list of subjects."""
    matieres: List[str] = Field([], description="List of available subjects") 