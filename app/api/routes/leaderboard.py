"""Routes for leaderboard management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.challenge import LeaderboardEntry
from app.api.deps import get_current_user, get_teacher_user
from app.core.exceptions import NotFoundError

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Leaderboard"])

@router.post("/leaderboard/calcule", response_model=ApiResponse)
async def calculate_leaderboard(
    challenge_id: str = Body(..., embed=True),
    current_user: UserInDB = Depends(get_teacher_user)
):
    """
    Calculate and return the leaderboard for a specific challenge (teacher or admin only).
    This triggers the evaluation of all submitted responses for a challenge.
    """
    logger.info(f"Début du calcul du leaderboard pour le challenge '{challenge_id}' par l'utilisateur '{current_user.username}'.")

    # Placeholder de la logique réelle
    leaderboard_data = [
        {"user_id": "1", "username": "student1", "score": 95, "rank": 1},
        {"user_id": "4", "username": "student2", "score": 87, "rank": 2},
        {"user_id": "7", "username": "student3", "score": 80, "rank": 3}
    ]

    logger.info(f"Leaderboard calculé pour le challenge '{challenge_id}' avec {len(leaderboard_data)} participants.")

    return {
        "success": True,
        "message": "Classement calculé avec succès",
        "data": {
            "leaderboard": leaderboard_data,
            "challenge_id": challenge_id,
            "total_participants": len(leaderboard_data),
            "evaluated_at": "2023-05-15T14:30:00"
        }
    }