"""Routes for evaluations management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.evaluation import EvaluationRequest
from app.api.deps import get_current_user_simple
from app.services.evaluations import evaluer_reponse
from app.db.session import get_session

# Config du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Evaluations"])

@router.post("/evaluation/response", response_model=ApiResponse)
async def evaluate_response(
    user_id: int = Query(..., description="User ID for authentication"),
    evaluation: EvaluationRequest = Body(...),
    session=Depends(get_session)
):
    """
    Évalue la réponse d'un étudiant et retourne un feedback détaillé.
    """
    current_user = await get_current_user_simple(user_id, session)
    logger.info(f"Évaluation d'une réponse par {current_user.username}")
    
    try:
        result = evaluer_reponse(
            evaluation.question,
            evaluation.reponse_etudiant,
            evaluation.reponse_attendue,
            evaluation.matiere,
            evaluation.criteres
        )
        
        result["user_info"] = {
            "user_id": current_user.id,
            "username": current_user.username
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'évaluation: {str(e)}"
        )