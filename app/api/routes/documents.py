"""Routes for document management."""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Path
from typing import List, Optional

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.document import DocumentCreate, DocumentResponse, DocumentList
from app.api.deps import get_current_user, get_teacher_user
from app.core.exceptions import NotFoundError

router = APIRouter(tags=["Documents"])

@router.get("/matieres/{matiere}/documents", response_model=ApiResponse)
async def get_documents(
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    List all documents for a specific subject.
    """
    # This will be implemented to use the actual function
    # For now, return a placeholder
    return {
        "success": True,
        "message": f"Documents pour la matière {matiere} récupérés avec succès",
        "data": {
            "documents": [
                {
                    "id": "doc1",
                    "filename": "cours_intro.pdf",
                    "matiere": matiere,
                    "document_type": "pdf",
                    "is_exam": False,
                    "file_path": f"cours/{matiere}/cours_intro.pdf",
                    "file_size": 1024,
                    "upload_date": "2023-05-01T10:00:00",
                    "last_indexed": "2023-05-01T10:05:00"
                }
            ]
        }
    }

@router.post("/matieres/{matiere}/documents", response_model=ApiResponse)
async def upload_document(
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    file: UploadFile = File(...),
    is_exam: bool = Form(False),
    current_user: UserInDB = Depends(get_teacher_user)
):
    """
    Upload a new document for a subject (teacher or admin only).
    """
    # This will be implemented to use the actual function
    # For now, return a placeholder
    return {
        "success": True,
        "message": f"Document {file.filename} téléchargé avec succès",
        "data": {
            "document": {
                "id": "new_doc_id",
                "filename": file.filename,
                "matiere": matiere,
                "document_type": file.filename.split(".")[-1],
                "is_exam": is_exam,
                "file_path": f"cours/{matiere}/{file.filename}",
                "file_size": 1024,
                "upload_date": "2023-05-10T14:30:00"
            }
        }
    }

@router.delete("/matieres/{matiere}/documents/{document_id}", response_model=ApiResponse)
async def delete_document(
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    document_id: str = Path(..., description="Document ID to delete"),
    current_user: UserInDB = Depends(get_teacher_user)
):
    """
    Delete a document (teacher or admin only).
    """
    # This will be implemented to use the actual function
    # For now, return a placeholder
    return {
        "success": True,
        "message": f"Document {document_id} supprimé avec succès",
        "data": {
            "document_id": document_id,
            "matiere": matiere
        }
    } 