"""Routes for questions management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.question import QuestionRequest, QuestionResponse
from app.api.deps import get_current_user_simple
from app.services.questions import repondre_question, generer_question_reflexion
from app.db.session import get_session

# Config du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Questions"])

@router.post("/question", response_model=ApiResponse)
async def ask_question(
    user_id: int = Query(..., description="User ID for authentication"),
    question: QuestionRequest = Body(...),
    session=Depends(get_session)
):
    """
    Pose une question au système et obtient une réponse générée par RAG.
    """
    current_user = await get_current_user_simple(user_id, session)
    logger.info(f"Question posée par {current_user.username}: {question.question[:100]}...")
    
    try:
        result = repondre_question(
            question.question,
            question.matiere,
            question.contexte,
            question.difficulte
        )
        
        result["user_info"] = {
            "user_id": current_user.id,
            "username": current_user.username
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du traitement de la question: {str(e)}"
        )

@router.post("/question/reflection", response_model=ApiResponse)
async def generate_reflection_question(
    user_id: int = Query(..., description="User ID for authentication"),
    request: dict = Body(...),
    session=Depends(get_session)
):
    """
    Génère une question de réflexion sur un concept donné.
    """
    current_user = await get_current_user_simple(user_id, session)
    
    concept = request.get("concept", "")
    matiere = request.get("matiere", "")
    difficulte = request.get("difficulte", "moyen")
    
    logger.info(f"Génération de question de réflexion par {current_user.username} pour le concept: {concept}")
    
    try:
        result = generer_question_reflexion(concept, matiere, difficulte)
        
        result["user_info"] = {
            "user_id": current_user.id,
            "username": current_user.username
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération de question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de question: {str(e)}"
        )