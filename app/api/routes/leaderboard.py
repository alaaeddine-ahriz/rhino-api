"""Routes for leaderboard management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.leaderboard import LeaderboardRequest
from app.api.deps import get_current_user_simple
from app.services.leaderboard import calculer_classement
from app.db.session import get_session

# Config du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Leaderboard"])

@router.post("/leaderboard/calcule", response_model=ApiResponse)
async def calculate_leaderboard(
    user_id: int = Query(..., description="User ID for authentication"),
    request: LeaderboardRequest = Body(...),
    session=Depends(get_session)
):
    """
    Calcule et retourne le classement pour un challenge donné (teacher or admin only).
    """
    current_user = await get_current_user_simple(user_id, session)
    
    # Check if user has teacher or admin role
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource. Teacher or admin role required.",
        )
    
    logger.info(f"Calcul du classement pour le challenge {request.challenge_id} par {current_user.username}")
    
    try:
        result = calculer_classement(request.challenge_id, request.matiere)
        
        result["user_info"] = {
            "user_id": current_user.id,
            "username": current_user.username
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors du calcul du classement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul du classement: {str(e)}"
        )