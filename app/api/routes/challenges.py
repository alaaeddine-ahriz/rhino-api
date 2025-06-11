"""Routes for challenges management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Optional
from datetime import date, datetime

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.challenge import ChallengeCreate, ChallengeResponse, ChallengeUserResponse, LeaderboardEntry
from app.api.deps import get_current_user_simple
from app.core.exceptions import NotFoundError
from app.services.challenges import creer_challenge, lister_challenges, get_next_challenge_for_matiere, get_today_challenge_for_user
from app.db.session import get_session

# Config du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Challenges"])

@router.get("/challenges/today", response_model=ApiResponse)
async def get_today_challenge(
    user_id: int = Query(..., description="User ID for authentication"),
    session=Depends(get_session)
):
    """
    Get today's challenge based on server date and user subscriptions.
    Uses tick logic to determine which challenge should be served today.
    """
    try:
        current_user = await get_current_user_simple(user_id, session)
        today = date.today().isoformat()
        logger.info(f"User {current_user.username} (ID: {user_id}) requesting today's challenge for {today}")
        
        # Get today's challenge based on user subscriptions
        today_challenge = get_today_challenge_for_user(current_user.subscriptions, session)
        
        if not today_challenge:
            logger.warning(f"No challenge available for user {current_user.username} with subscriptions: {current_user.subscriptions}")
            return {
                "success": False,
                "message": "Aucun challenge disponible pour vos abonnements",
                "data": {
                    "challenge": None,
                    "user_subscriptions": current_user.subscriptions.split(',') if current_user.subscriptions else [],
                    "date": today
                }
            }
        
        logger.info(f"Today's challenge served to {current_user.username}: {today_challenge['ref']} from {today_challenge['matiere']}")
        
        return {
            "success": True,
            "message": "Challenge du jour récupéré avec succès",
            "data": {
                "challenge": {
                    "challenge_id": today_challenge["challenge_id"],
                    "ref": today_challenge["ref"],
                    "date": today,
                    "question": today_challenge["question"],
                    "matiere": today_challenge["matiere"],
                    "matieres": today_challenge["matieres"]
                },
                "user_subscriptions": current_user.subscriptions.split(',') if current_user.subscriptions else []
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting today's challenge for user ID {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving today's challenge: {str(e)}"
        )

@router.get("/challenges", response_model=ApiResponse)
async def get_challenges(
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: Optional[str] = Query(None, description="Filter by subject"),
    session=Depends(get_session)
):
    """
    List all challenges, optionally filtered by subject or date range.
    """
    current_user = await get_current_user_simple(user_id, session)
    logger.info(f"Utilisateur {current_user.username} demande la liste des challenges pour la matière: {matiere}")
    result = lister_challenges(matiere=matiere, session=session)
    result["message"] = "Challenges récupérés avec succès"
    return result

@router.post("/challenges", response_model=ApiResponse)
async def create_challenge(
    user_id: int = Query(..., description="User ID for authentication"),
    challenge: ChallengeCreate = Body(...),
    session=Depends(get_session)
):
    """
    Create a new challenge for one or more subjects (teacher or admin only).
    """
    current_user = await get_current_user_simple(user_id, session)
    
    # Check if user has teacher or admin role
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource. Teacher or admin role required.",
        )
    
    logger.info(f"Création d'un challenge par {current_user.username} pour la matière : {challenge.matiere}")
    result = creer_challenge(challenge.dict(), session=session)
    result["message"] = "Challenge créé avec succès"
    logger.info(f"Challenge créé avec succès : {result.get('data', {}).get('challenge_id', 'N/A')}")
    return result

@router.post("/challenges/{challenge_id}/response", response_model=ApiResponse)
async def submit_challenge_response(
    user_id: int = Query(..., description="User ID for authentication"),
    challenge_id: str = Path(..., description="Challenge ID"),
    response_data: ChallengeUserResponse = Body(...),
    session=Depends(get_session)
):
    """
    Submit a user's response to a specific challenge.
    """
    current_user = await get_current_user_simple(user_id, session)
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
    user_id: int = Query(..., description="User ID for authentication"),
    challenge_id: str = Path(..., description="Challenge ID"),
    session=Depends(get_session)
):
    """
    Get the leaderboard for a specific challenge.
    """
    current_user = await get_current_user_simple(user_id, session)
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
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: str = Query(..., description="Subject to get challenge for"),
    session=Depends(get_session)
):
    current_user = await get_current_user_simple(user_id, session)
    logger.info(f"Recherche du prochain challenge pour la matière : {matiere}")
    challenge = get_next_challenge_for_matiere(matiere, session)
    if not challenge:
        logger.warning(f"Aucun challenge trouvé pour la matière {matiere}")
        return {"success": False, "message": "Aucun challenge disponible", "data": None}
    
    logger.info(f"Challenge trouvé pour la matière {matiere} : {challenge.id}")
    return {"success": True, "message": "Challenge servi", "data": {"challenge": challenge.dict()}}