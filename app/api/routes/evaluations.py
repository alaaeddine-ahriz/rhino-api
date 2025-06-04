"""Routes for student response evaluation."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.evaluation import EvaluationRequest, EvaluationResponse
from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Évaluations"])

@router.post("/evaluation/response", response_model=ApiResponse)
async def evaluate_student_response(
    request: EvaluationRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Evaluate a student's response to a question.
    """
    logger.info(
        f"Évaluation demandée par l'utilisateur {current_user.username} pour la matière '{request.matiere}' "
        f"et la réponse de l'étudiant {request.user_id}"
    )

    # This will be implemented to call evaluer_reponse_etudiant
    # For now, return a placeholder
    evaluation_data = {
        "note": 75,
        "points_forts": [
            "Bonne compréhension des concepts de base",
            "Structure claire de la réponse",
            "Exemples pertinents"
        ],
        "points_ameliorer": [
            "Approfondir l'analyse critique",
            "Développer davantage les implications",
            "Citer plus de références du cours"
        ],
        "reponse_modele": "Une réponse modèle concise qui démontre les points clés...",
        "justification_note": "La note de 75/100 reflète une bonne maîtrise des concepts fondamentaux, mais manque d'analyse approfondie.",
        "conseil_personnalise": "Pour améliorer votre réponse, essayez d'établir plus de liens entre les concepts et leurs applications pratiques.",
        "base_sur_examen": False
    }

    logger.info(
        f"Évaluation terminée pour l'étudiant {request.user_id} sur la matière {request.matiere} - Note: {evaluation_data['note']}"
    )

    return {
        "success": True,
        "message": "Évaluation générée avec succès",
        "data": {
            "evaluation": evaluation_data,
            "matiere": request.matiere,
            "logs": "Évaluation effectuée avec succès"
        }
    }