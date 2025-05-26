"""Models for questions management."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class QuestionRequest(BaseModel):
    """Model for asking a general question to the RAG system."""
    matiere: str = Field(..., description="Subject to query (e.g. 'MATH')")
    query: str = Field(..., description="The question to ask")
    output_format: str = Field("text", description="Response format ('text' or 'json')")
    save_output: bool = Field(True, description="Whether to save the output")

class ReflectionQuestionRequest(BaseModel):
    """Model for generating a reflection question."""
    matiere: str = Field(..., description="Subject for the question (e.g. 'MATH')")
    concept_cle: Optional[str] = Field("", description="Key concept to focus on")
    output_format: str = Field("text", description="Response format ('text' or 'json')")
    save_output: bool = Field(True, description="Whether to save the output")

class Source(BaseModel):
    """Model for a document source in a response."""
    document: int
    source: str
    section: Optional[str] = None
    contenu: Optional[str] = None
    is_exam: bool = False

class QuestionResponse(BaseModel):
    """Model for a question response."""
    response: str = Field(..., description="The answer to the question")
    sources: Optional[List[Source]] = Field(None, description="Sources used for the response")
    matiere: str = Field(..., description="Subject of the question")
    query: Optional[str] = Field(None, description="The original query")

class ReflectionQuestion(BaseModel):
    """Model for a generated reflection question."""
    question: str = Field(..., description="The reflection question")
    concepts_abordes: Optional[List[str]] = Field(None, description="Concepts addressed in the question")
    niveau_difficulte: Optional[str] = Field(None, description="Difficulty level")
    competences_visees: Optional[List[str]] = Field(None, description="Skills targeted by the question")
    elements_reponse: Optional[List[str]] = Field(None, description="Expected elements in an answer")
    base_sur_examen: Optional[bool] = Field(None, description="Whether based on examination materials")
    originalite: Optional[str] = Field(None, description="Explanation of question's originality") 