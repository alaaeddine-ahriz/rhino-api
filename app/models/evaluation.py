"""Models for student response evaluation."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class EvaluationRequest(BaseModel):
    """Model for evaluating a student's response."""
    matiere: str = Field(..., description="Subject (e.g. 'MATH')")
    question: str = Field(..., description="Question that was asked")
    student_response: str = Field(..., description="Student's answer to evaluate")
    save_output: bool = Field(True, description="Whether to save the evaluation output")

class EvaluationResponse(BaseModel):
    """Model for the evaluation result."""
    note: int = Field(..., description="Score (0-100)")
    points_forts: List[str] = Field(..., description="Strengths of the response")
    points_ameliorer: List[str] = Field(..., description="Areas for improvement")
    reponse_modele: str = Field(..., description="Model answer")
    justification_note: str = Field(..., description="Explanation of the score")
    conseil_personnalise: str = Field(..., description="Personalized advice")
    base_sur_examen: bool = Field(False, description="Whether based on exam materials") 