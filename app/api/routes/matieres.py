"""Routes for subject (matière) management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from typing import List, Optional

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.matiere import MatiereCreate, MatiereResponse, MatiereList
from app.api.deps import get_current_user_simple
from app.core.exceptions import NotFoundError
from app.db.session import get_session
from app.services import matieres

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matieres", tags=["Matières"])

@router.get("/", response_model=ApiResponse)
async def get_matieres(
    user_id: int = Query(..., description="User ID for authentication"),
    session=Depends(get_session)
):
    """
    List all available subjects by scanning the cours directory.
    """
    current_user = await get_current_user_simple(user_id, session)
    logger.info(f"[{current_user.username}] Requête de récupération des matières.")
    
    # Utiliser le service pour scanner les dossiers
    result = matieres.lister_matieres()
    
    if result["success"]:
        return {
            "success": True,
            "message": "Matières récupérées avec succès",
            "data": {"matieres": result["data"]}
        }
    else:
        logger.error(f"Erreur lors de la récupération des matières: {result.get('message', 'Erreur inconnue')}")
        return {
            "success": False,
            "message": result.get("message", "Erreur lors de la récupération des matières"),
            "data": {"matieres": []}
        }

@router.post("/", response_model=ApiResponse)
async def create_matiere(
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: MatiereCreate = Body(...),
    session=Depends(get_session)
):
    """
    Create a new subject with its folder structure (teacher or admin only).
    """
    current_user = await get_current_user_simple(user_id, session)
    
    # Check if user has teacher or admin role
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource. Teacher or admin role required.",
        )
    
    logger.info(f"[{current_user.username}] Création de la matière '{matiere.name}'.")
    
    # Utiliser le service pour créer la structure de dossiers
    result = matieres.initialiser_structure_dossiers(matiere.name)
    
    if result["success"]:
        # Obtenir les infos détaillées de la matière créée
        info_result = matieres.obtenir_info_matiere(matiere.name)
        matiere_info = info_result["data"] if info_result["success"] else {
            "name": matiere.name,
            "description": matiere.description,
            "document_count": 0,
            "last_update": None
        }
        
        return {
            "success": True,
            "message": result["message"],
            "data": {
                "matiere": {
                    "name": matiere.name,
                    "description": matiere.description,
                    "document_count": matiere_info.get("document_count", 0),
                    "last_update": matiere_info.get("last_update"),
                    "path": result["data"]["path"]
                }
            }
        }
    else:
        if "existe déjà" in result["message"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )

@router.get("/{matiere_name}", response_model=ApiResponse)
async def get_matiere_info(
    user_id: int = Query(..., description="User ID for authentication"),
    matiere_name: str = Path(..., description="Subject name"),
    session=Depends(get_session)
):
    """
    Get detailed information about a specific subject.
    """
    current_user = await get_current_user_simple(user_id, session)
    logger.info(f"[{current_user.username}] Récupération des infos de la matière '{matiere_name}'.")
    
    # Utiliser le service pour obtenir les infos
    result = matieres.obtenir_info_matiere(matiere_name)
    
    if result["success"]:
        return {
            "success": True,
            "message": f"Informations de la matière {matiere_name} récupérées avec succès",
            "data": {"matiere": result["data"]}
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )

@router.delete("/{matiere_name}", response_model=ApiResponse)
async def delete_matiere(
    user_id: int = Query(..., description="User ID for authentication"),
    matiere_name: str = Path(..., description="Subject name to delete"),
    session=Depends(get_session)
):
    """
    Delete a subject and all its documents (teacher or admin only).
    """
    current_user = await get_current_user_simple(user_id, session)
    
    # Check if user has teacher or admin role
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource. Teacher or admin role required.",
        )
    
    logger.info(f"[{current_user.username}] Suppression de la matière '{matiere_name}'.")
    
    # Utiliser le service pour supprimer la matière
    result = matieres.supprimer_matiere(matiere_name)
    
    if result["success"]:
        return {
            "success": True,
            "message": result["message"],
            "data": {"matiere_name": matiere_name}
        }
    else:
        if "n'existe pas" in result["message"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )



