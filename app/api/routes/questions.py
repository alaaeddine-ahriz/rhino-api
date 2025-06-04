"""Routes for questions and RAG interactions."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.question import QuestionRequest, ReflectionQuestionRequest
from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Questions"])

@router.post("/question", response_model=ApiResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Ask a question about a specific subject and get an answer using RAG.
    """
    logger.info(f"[{current_user.username}] Question posée sur '{request.matiere}': \"{request.query}\"")
    return {
        "success": True,
        "message": "Réponse générée avec succès",
        "data": {
            "response": f"Voici la réponse à votre question sur {request.matiere}: {request.query}",
            "sources": [
                {
                    "document": 1,
                    "source": f"cours/{request.matiere}/document1.pdf",
                    "section": "Introduction",
                    "contenu": "Extrait du contenu...",
                    "is_exam": False
                }
            ],
            "matiere": request.matiere,
            "query": request.query
        }
    }

@router.post("/question/reflection", response_model=ApiResponse)
async def generate_reflection_question(
    request: ReflectionQuestionRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate a reflection question about a key concept in a subject.
    """
    # This will be implemented to call generer_question_reflexion
    # For now, return a placeholder
    concept = request.concept_cle if request.concept_cle else "concept général"
    
    logger.info(f"[{current_user.username}] Génération de question de réflexion sur '{concept}' pour '{request.matiere}'")

    return {
        "success": True,
        "message": "Question de réflexion générée avec succès",
        "data": {
            "question": f"Comment expliquer l'importance de {concept} dans le contexte de {request.matiere}?",
            "matiere": request.matiere,
            "concept": concept,
            "format": request.output_format,
            "metadata": {
                "concepts_abordes": [concept, "analyse critique", "application pratique"],
                "niveau_difficulte": "intermédiaire",
                "base_sur_examen": False
            }
        }
    }