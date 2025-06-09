"""Routes for document management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Path
from typing import List, Optional
from datetime import datetime

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.document import DocumentCreate, DocumentResponse, DocumentList
from app.api.deps import get_current_user, get_teacher_user
from app.core.exceptions import NotFoundError
from app.services.rag.documents import (
    get_documents_for_subject,
    upload_document_to_subject,
    delete_document_from_subject,
    get_document_content,
    process_and_index_new_document,
    initialiser_structure_dossiers
)
from app.services.rag.embeddings import delete_documents
from app.services.rag.core import initialize_pinecone

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Documents"])

@router.get("/matieres/{matiere}/documents", response_model=ApiResponse)
async def get_documents(
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    List all documents for a specific subject.
    """
    try:
        logger.info(f"User {current_user.username} is listing documents for subject {matiere}")
        
        # Ensure folder structure exists
        initialiser_structure_dossiers()
        
        # Get documents for the subject
        documents = get_documents_for_subject(matiere)
        
        return {
            "success": True,
            "message": f"Documents for subject {matiere} retrieved successfully",
            "data": {
                "documents": documents,
                "count": len(documents)
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving documents for subject {matiere}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}"
        )

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
    try:
        logger.info(f"User {current_user.username} is uploading document {file.filename} for subject {matiere}, is_exam={is_exam}")
        
        # Ensure folder structure exists
        initialiser_structure_dossiers()
        
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Upload the document
        success, message, document_info = upload_document_to_subject(
            matiere=matiere,
            filename=file.filename,
            file_content=file_content,
            is_exam=is_exam
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Automatically process and index the document into vector database
        try:
            index_success, index_message = process_and_index_new_document(matiere, document_info)
            if index_success:
                logger.info(f"Document {file.filename} successfully indexed: {index_message}")
                # Add indexing info to response
                document_info["last_indexed"] = datetime.now().isoformat()
                document_info["indexing_status"] = "success"
            else:
                logger.warning(f"Document {file.filename} uploaded but indexing failed: {index_message}")
                # Add indexing failure info to response
                document_info["indexing_status"] = "failed"
                document_info["indexing_error"] = index_message
        except Exception as e:
            logger.error(f"Error during automatic indexing of {file.filename}: {str(e)}")
            document_info["indexing_status"] = "error"
            document_info["indexing_error"] = str(e)
        
        return {
            "success": True,
            "message": message,
            "data": {
                "document": document_info
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document {file.filename} for subject {matiere}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )

@router.delete("/matieres/{matiere}/documents/{document_id}", response_model=ApiResponse)
async def delete_document(
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    document_id: str = Path(..., description="Document ID to delete"),
    current_user: UserInDB = Depends(get_teacher_user)
):
    """
    Delete a document (teacher or admin only).
    """
    try:
        logger.warning(f"User {current_user.username} is deleting document {document_id} for subject {matiere}")
        
        # First, get document info before deletion (for vector database cleanup)
        documents = get_documents_for_subject(matiere)
        target_document = None
        for doc in documents:
            if doc["id"] == document_id:
                target_document = doc
                break
        
        # Delete the document from filesystem
        success, message = delete_document_from_subject(matiere, document_id)
        
        if not success:
            if "not found" in message.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=message
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=message
                )
        
        # Automatically remove document from vector database
        if target_document:
            try:
                pc, index_name, spec = initialize_pinecone()
                vector_delete_success = delete_documents(
                    pc=pc,
                    index_name=index_name,
                    matiere=matiere,
                    file_paths=[target_document["file_path"]]
                )
                if vector_delete_success:
                    logger.info(f"Document {target_document['filename']} successfully removed from vector database")
                else:
                    logger.warning(f"Document {target_document['filename']} deleted from filesystem but may still exist in vector database")
            except Exception as e:
                logger.error(f"Error removing document from vector database: {str(e)}")
        
        return {
            "success": True,
            "message": message,
            "data": {
                "document_id": document_id,
                "matiere": matiere
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id} for subject {matiere}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )

@router.get("/matieres/{matiere}/documents/{document_id}/content", response_model=ApiResponse)
async def get_document_content_endpoint(
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    document_id: str = Path(..., description="Document ID"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get the content of a specific document.
    """
    try:
        logger.info(f"User {current_user.username} is getting content for document {document_id} in subject {matiere}")
        
        # Get document content
        success, message, content = get_document_content(matiere, document_id)
        
        if not success:
            if "not found" in message.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=message
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=message
                )
        
        return {
            "success": True,
            "message": message,
            "data": {
                "document_id": document_id,
                "matiere": matiere,
                "content": content
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content for document {document_id} in subject {matiere}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document content: {str(e)}"
        )

@router.post("/matieres/{matiere}/documents/reindex", response_model=ApiResponse)
async def reindex_subject_documents(
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    current_user: UserInDB = Depends(get_teacher_user)
):
    """
    Manually trigger re-indexing of all documents for a subject (teacher or admin only).
    Useful for maintenance or after system updates.
    """
    try:
        logger.info(f"User {current_user.username} is triggering re-indexing for subject {matiere}")
        
        # Get all documents for the subject
        documents = get_documents_for_subject(matiere)
        
        if not documents:
            return {
                "success": True,
                "message": f"No documents found for subject {matiere} to reindex",
                "data": {
                    "processed_count": 0,
                    "success_count": 0,
                    "failed_count": 0,
                    "details": []
                }
            }
        
        indexing_results = []
        success_count = 0
        failed_count = 0
        
        # Process each document
        for doc in documents:
            try:
                index_success, index_message = process_and_index_new_document(matiere, doc)
                if index_success:
                    success_count += 1
                    indexing_results.append({
                        "filename": doc["filename"],
                        "status": "success",
                        "message": index_message
                    })
                else:
                    failed_count += 1
                    indexing_results.append({
                        "filename": doc["filename"],
                        "status": "failed",
                        "message": index_message
                    })
            except Exception as e:
                failed_count += 1
                indexing_results.append({
                    "filename": doc["filename"],
                    "status": "error",
                    "message": str(e)
                })
        
        return {
            "success": True,
            "message": f"Re-indexing completed for subject {matiere}",
            "data": {
                "processed_count": len(documents),
                "success_count": success_count,
                "failed_count": failed_count,
                "details": indexing_results
            }
        }
        
    except Exception as e:
        logger.error(f"Error during re-indexing for subject {matiere}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during re-indexing: {str(e)}"
        )