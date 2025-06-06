"""Routes for challenges management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Optional
from datetime import date, datetime

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.challenge import ChallengeCreate, ChallengeResponse, ChallengeUserResponse, LeaderboardEntry
from app.api.deps import get_current_user, get_teacher_user
from app.core.exceptions import NotFoundError
from app.services.challenges import creer_challenge, lister_challenges, get_next_challenge_for_matiere
from app.db.session import get_session

# Config du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Challenges"])

@router.get("/challenges/today", response_model=ApiResponse)
async def get_today_challenge():
    """
    Get today's challenge based on server date.
    """
    today = date.today().isoformat()
    logger.info(f"Récupération du challenge du jour : {today}")
    return {
        "success": True,
        "message": "Challenge du jour récupéré avec succès",
        "data": {
            "challenge": {
                "challenge_id": "chall_1",
                "date": today,
                "question": "Expliquez comment les concepts de TCP/IP s'appliquent dans les réseaux modernes.",
                "matieres": ["TCP", "SYD"]
            }
        }
    }

@router.get("/challenges", response_model=ApiResponse)
async def get_challenges(
    matiere: Optional[str] = Query(None, description="Filter by subject"),
    current_user: UserInDB = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    List all challenges, optionally filtered by subject or date range.
    """
    logger.info(f"Utilisateur {current_user.username} demande la liste des challenges pour la matière: {matiere}")
    result = lister_challenges(matiere=matiere, session=session)
    result["message"] = "Challenges récupérés avec succès"
    return result

@router.post("/challenges", response_model=ApiResponse)
async def create_challenge(
    challenge: ChallengeCreate,
    current_user: UserInDB = Depends(get_teacher_user),
    session=Depends(get_session)
):
    """
    Create a new challenge for one or more subjects (teacher or admin only).
    """
    logger.info(f"Création d'un challenge par {current_user.username} pour les matières : {challenge.matieres}")
    result = creer_challenge(challenge.dict(), session=session)
    result["message"] = "Challenge créé avec succès"
    logger.info(f"Challenge créé avec succès : {result.get('data', {}).get('challenge_id', 'N/A')}")
    return result

@router.post("/challenges/{challenge_id}/response", response_model=ApiResponse)
async def submit_challenge_response(
    challenge_id: str = Path(..., description="Challenge ID"),
    response_data: ChallengeUserResponse = Body(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Submit a user's response to a specific challenge.
    """
    logger.info(f"Soumission de réponse pour le challenge {challenge_id} par utilisateur {response_data.user_id}")
    return {
        "success": True,
        "message": "Réponse soumise avec succès",
        "data": {
            "submission": {
                "challenge_id": challenge_id,
                "user_id": response_data.user_id,
                "submitted_at": datetime.now().isoformat(),
                "evaluated": False
            }
        }
    }

@router.get("/challenges/{challenge_id}/leaderboard", response_model=ApiResponse)
async def get_challenge_leaderboard(
    challenge_id: str = Path(..., description="Challenge ID"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get the leaderboard for a specific challenge.
    """
    logger.info(f"Récupération du classement pour le challenge {challenge_id} par {current_user.username}")
    return {
        "success": True,
        "message": "Classement récupéré avec succès",
        "data": {
            "leaderboard": [
                {"user_id": "1", "username": "student1", "score": 95, "rank": 1},
                {"user_id": "4", "username": "student2", "score": 87, "rank": 2},
                {"user_id": "7", "username": "student3", "score": 80, "rank": 3}
            ],
            "challenge_id": challenge_id
        }
    }

@router.get("/challenges/next", response_model=ApiResponse)
async def get_next_challenge(
    matiere: str,
    session=Depends(get_session)
):
    logger.info(f"Recherche du prochain challenge pour la matière : {matiere}")
    challenge = get_next_challenge_for_matiere(matiere, session)
    if not challenge:
        logger.warning(f"Aucun challenge trouvé pour la matière {matiere}")
        return {"success": False, "message": "Aucun challenge disponible", "data": None}
    
    logger.info(f"Challenge trouvé pour la matière {matiere} : {challenge.id}")
    return {"success": True, "message": "Challenge servi", "data": {"challenge": challenge.dict()}}