"""Routes for questions management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from datetime import datetime

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.question import ReflectionQuestionRequest
from app.api.deps import get_current_user_simple
from app.services.rag.questions import generer_question_reflexion
from app.db.session import get_session

# Config du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Questions"])

@router.post("/question/reflection", response_model=ApiResponse)
async def generate_reflection_question(
    user_id: int = Query(..., description="User ID for authentication"),
    request: ReflectionQuestionRequest = Body(...),
    session=Depends(get_session)
):
    """
    Génère une question de réflexion sur un concept donné.
    """
    current_user = await get_current_user_simple(user_id, session)
    
    logger.info(f"Génération de question de réflexion par {current_user.username} pour le concept: {request.concept_cle} en {request.matiere}")
    
    try:
        result = generer_question_reflexion(request.matiere, request.concept_cle)
        
        # If result is successful, add user info
        if isinstance(result, dict) and not result.get("error"):
            result["user_info"] = {
                "user_id": current_user.id,
                "username": current_user.username
            }
        
        return {
            "success": True,
            "message": "Question de réflexion générée avec succès",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de la question: {str(e)}"
        )