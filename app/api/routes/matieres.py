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
    List all available subjects.
    """
    current_user = await get_current_user_simple(user_id, session)
    logger.info(f"[{current_user.username}] Requête de récupération des matières.")
    return {
        "success": True,
        "message": "Matières récupérées avec succès",
        "data": {"matieres": ["SYD", "TCP"]}
    }

@router.post("/", response_model=ApiResponse)
async def create_matiere(
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: MatiereCreate = Body(...),
    session=Depends(get_session)
):
    """
    Create a new subject (teacher or admin only).
    """
    current_user = await get_current_user_simple(user_id, session)
    
    # Check if user has teacher or admin role
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource. Teacher or admin role required.",
        )
    
    logger.info(f"[{current_user.username}] Création de la matière '{matiere.name}'.")
    return {
        "success": True,
        "message": f"Matière {matiere.name} créée avec succès",
        "data": {
            "matiere": {
                "name": matiere.name,
                "description": matiere.description,
                "document_count": 0,
                "last_update": None
            }
        }
    }

@router.delete("/{matiere_id}", response_model=ApiResponse)
async def delete_matiere(
    user_id: int = Query(..., description="User ID for authentication"),
    matiere_id: str = Path(..., description="Subject ID to delete"),
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
    
    logger.info(f"[{current_user.username}] Suppression de la matière '{matiere_id}'.")
    return {
        "success": True,
        "message": f"Matière {matiere_id} supprimée avec succès",
        "data": {"matiere_id": matiere_id}
    }

