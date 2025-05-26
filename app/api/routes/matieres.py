"""Routes for subject (matière) management."""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.matiere import MatiereCreate, MatiereResponse, UpdateRequest, MatiereList
from app.api.deps import get_current_user, get_teacher_user
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/matieres", tags=["Matières"])

@router.get("/", response_model=ApiResponse)
async def get_matieres(current_user: UserInDB = Depends(get_current_user)):
    """
    List all available subjects.
    """
    # This will be implemented to use the actual function
    # For now, return a placeholder
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
    # This will be implemented to use the actual function
    # For now, return a placeholder
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
    # This will be implemented to use the actual function
    # For now, return a placeholder
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
    # This will be implemented to call mettre_a_jour_matiere
    # For now, return a placeholder
    return {
        "success": True,
        "message": f"Matière {request.matiere} mise à jour avec succès",
        "data": {
            "matiere": request.matiere,
            "updated": True,
            "logs": "Indexation effectuée avec succès"
        }
    } 