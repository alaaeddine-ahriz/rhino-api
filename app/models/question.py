"""Models for questions management."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ReflectionQuestionRequest(BaseModel):
    """Model for requesting a reflection question."""
    matiere: str = Field(..., description="Subject to generate question for")
    concept_cle: str = Field(..., description="Key concept to generate question about")

class Source(BaseModel):
    """Model for a document source in a response."""
    document: int
    source: str
    section: Optional[str] = None
    contenu: Optional[str] = None
    is_exam: bool = False

class QuestionResponse(BaseModel):
    """Model for RAG system response."""
    response: str = Field(..., description="The answer to the question")
    confidence_level: float = Field(0.0, description="Confidence level of the answer (0.0 to 1.0)")
    key_concepts: List[str] = Field(default_factory=list, description="Key concepts identified in the answer")
    timestamp: str = Field(..., description="When the response was generated (ISO format)")
    user_info: Dict[str, Any] = Field(..., description="Information about the user who asked the question")

class ReflectionQuestion(BaseModel):
    """Model for a generated reflection question."""
    question: str = Field(..., description="The reflection question")
    concepts_abordes: Optional[List[str]] = Field(None, description="Concepts addressed in the question")
    niveau_difficulte: Optional[str] = Field(None, description="Difficulty level")
    competences_visees: Optional[List[str]] = Field(None, description="Skills targeted by the question")
    elements_reponse: Optional[List[str]] = Field(None, description="Expected elements in an answer")
    base_sur_examen: Optional[bool] = Field(None, description="Whether based on examination materials")
    originalite: Optional[str] = Field(None, description="Explanation of question's originality")

class ApiResponse(BaseModel):
    """Model for API response wrapper."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[QuestionResponse] = Field(None, description="Response data if successful")
    error: Optional[str] = Field(None, description="Error message if unsuccessful") 