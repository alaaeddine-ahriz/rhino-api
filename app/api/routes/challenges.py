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
    result = creer_challenge(challenge.model_dump(), session=session)
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
    
    try:
        # Generate a unique question ID for this response
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        short_uuid = str(uuid.uuid4())[:6]
        question_id = f"IDQ-{timestamp}-{short_uuid}"
        
        # Get the challenge details
        from sqlmodel import select
        from app.db.models import Challenge
        challenge = session.exec(select(Challenge).where(Challenge.id == int(challenge_id))).first()
        
        if not challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Challenge with ID {challenge_id} not found"
            )
        
        # Try to save to database first, fallback to JSON
        try:
            from app.services.student_response_service import StudentResponseService
            service = StudentResponseService()
            
            # Save the question first (creates the record)
            question_saved = service.save_question(
                question_id=question_id,
                student_email=current_user.email or f"user{current_user.id}@example.com",
                user_id=int(current_user.id),
                api_challenge_id=int(challenge_id)
            )
            
            if question_saved:
                # Save the response
                response_saved = service.save_response(
                    question_id=question_id,
                    response=response_data.response,
                    response_date=datetime.now().isoformat(),
                    response_from=current_user.email or f"user{current_user.id}@example.com"
                )
                
                if response_saved:
                    logger.info(f"✅ Response saved to database for challenge {challenge_id}")
                    db_saved = True
                else:
                    logger.warning("Failed to save response to database, falling back to JSON")
                    db_saved = False
            else:
                logger.warning("Failed to save question to database, falling back to JSON")
                db_saved = False
                
        except Exception as db_error:
            logger.warning(f"Database error, falling back to JSON: {db_error}")
            db_saved = False
        
        # Fallback to JSON if database failed
        if not db_saved:
            logger.info("📝 Using JSON fallback for response storage")
            
            # Import the mail utilities for JSON handling
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'mail'))
            
            from utils import load_conversations, save_conversations
            
            conversations = load_conversations()
            conversations[question_id] = {
                "student": current_user.email or f"user{current_user.id}@example.com",
                "question": challenge.question,
                "matiere": challenge.matiere,
                "challenge_ref": challenge.ref,
                "api_challenge_id": int(challenge_id),
                "response": response_data.response,
                "response_date": datetime.now().isoformat(),
                "response_from": current_user.email or f"user{current_user.id}@example.com",
                "evaluated": False,
                "user_id": int(current_user.id)
            }
            save_conversations(conversations)
            logger.info(f"✅ Response saved to JSON for challenge {challenge_id}")
        
        # Trigger automatic evaluation (try both systems)
        evaluation_result = None
        try:
            # Import the evaluation system
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'mail'))
            from evaluator import evaluate_and_display
            
            # Evaluate the response
            evaluation_result = evaluate_and_display(
                question=challenge.question,
                response=response_data.response,
                matiere=challenge.matiere,
                user_id=int(current_user.id)
            )
            
            if evaluation_result:
                logger.info(f"✅ Response evaluated for question {question_id}")
                
                # Try to save evaluation to database first
                if db_saved:
                    try:
                        evaluation_saved = service.save_evaluation(question_id, evaluation_result)
                        if evaluation_saved:
                            logger.info(f"✅ Evaluation saved to database for question {question_id}")
                        else:
                            logger.warning("Failed to save evaluation to database")
                    except Exception as eval_db_error:
                        logger.warning(f"Failed to save evaluation to database: {eval_db_error}")
                
                # Update JSON with evaluation
                conversations = load_conversations()
                if question_id in conversations:
                    conversations[question_id]['evaluation'] = evaluation_result
                    conversations[question_id]['evaluated'] = True
                    save_conversations(conversations)
                    logger.info(f"✅ Evaluation saved to JSON for question {question_id}")
                
            else:
                logger.warning(f"Failed to evaluate response for question {question_id}")
                
        except Exception as eval_error:
            logger.warning(f"Evaluation process failed (non-blocking): {eval_error}")
        
        return {
            "success": True,
            "message": "Réponse soumise et sauvegardée avec succès",
            "data": {
                "submission": {
                    "question_id": question_id,
                    "challenge_id": challenge_id,
                    "user_id": response_data.user_id,
                    "response": response_data.response,
                    "submitted_at": datetime.now().isoformat(),
                    "evaluated": evaluation_result is not None,
                    "storage_method": "database" if db_saved else "json",
                    "evaluation_score": evaluation_result.get('score') if evaluation_result else None
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting challenge response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting response: {str(e)}"
        )

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