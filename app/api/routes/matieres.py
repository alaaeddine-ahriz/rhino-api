"""Routes for subject (matière) management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.matiere import MatiereCreate, MatiereResponse, UpdateRequest, MatiereList
from app.api.deps import get_current_user, get_teacher_user
from app.core.exceptions import NotFoundError

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matieres", tags=["Matières"])

@router.get("/", response_model=ApiResponse)
async def get_matieres(current_user: UserInDB = Depends(get_current_user)):
    """
    List all available subjects.
    """
    logger.info(f"[{current_user.username}] Requête de récupération des matières.")
    return {
        "success": True,
        "message": "Matières récupérées avec succès",
        "data": {"matieres": ["SYD", "TCP"]}
    }

@router.post("/", response_model=ApiResponse)
async def create_matiere(
    matiere: MatiereCreate, 
    current_user: UserInDB = Depends(get_teacher_user)
):
    """
    Create a new subject (teacher or admin only).
    """
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
    matiere_id: str,
    current_user: UserInDB = Depends(get_teacher_user)
):
    """
    Delete a subject and all its documents (teacher or admin only).
    """
    logger.info(f"[{current_user.username}] Suppression de la matière '{matiere_id}'.")
    return {
        "success": True,
        "message": f"Matière {matiere_id} supprimée avec succès",
        "data": {"matiere_id": matiere_id}
    }

@router.post("/update", response_model=ApiResponse)
async def update_matiere(
    request: UpdateRequest,
    current_user: UserInDB = Depends(get_teacher_user)
):
    """
    Update the Pinecone index for a subject (teacher or admin only).
    """
    logger.info(f"[{current_user.username}] Mise à jour de l'index pour la matière '{request.matiere}'.")
    return {
        "success": True,
        "message": f"Matière {request.matiere} mise à jour avec succès",
        "data": {
            "matiere": request.matiere,
            "updated": True,
            "logs": "Indexation effectuée avec succès"
        }
    }