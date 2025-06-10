"""Routes for document management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Path, Query
from typing import List, Optional
from datetime import datetime

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.document import DocumentCreate, DocumentResponse, DocumentList
from app.api.deps import get_current_user_simple
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
from app.db.session import get_session

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Documents"])

@router.get("/matieres/{matiere}/documents", response_model=ApiResponse)
async def get_documents(
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    session=Depends(get_session)
):
    """
    List all documents for a specific subject.
    """
    try:
        current_user = await get_current_user_simple(user_id, session)
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
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    file: UploadFile = File(...),
    is_exam: bool = Form(False),
    session=Depends(get_session)
):
    """
    Upload a new document for a subject (teacher or admin only).
    """
    try:
        current_user = await get_current_user_simple(user_id, session)
        
        # Check if user has teacher or admin role
        if current_user.role not in ["teacher", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource. Teacher or admin role required.",
            )
        
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
            index_success, index_message = process_and_index_new_document(
                matiere=matiere,
                document_info=document_info
            )
            
            if index_success:
                logger.info(f"Document {file.filename} successfully indexed into vector database")
                message += f". Document indexed successfully: {index_message}"
            else:
                logger.warning(f"Document uploaded but indexing failed: {index_message}")
                message += f". Warning - indexing failed: {index_message}"
                
        except Exception as index_error:
            logger.error(f"Error during automatic indexing: {str(index_error)}")
            message += f". Warning - indexing error: {str(index_error)}"
        
        return {
            "success": True,
            "message": message,
            "data": {
                "document": document_info,
                "matiere": matiere
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
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    document_id: str = Path(..., description="Document ID"),
    session=Depends(get_session)
):
    """
    Delete a document from a subject (teacher or admin only).
    """
    try:
        current_user = await get_current_user_simple(user_id, session)
        
        # Check if user has teacher or admin role
        if current_user.role not in ["teacher", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource. Teacher or admin role required.",
            )
        
        logger.info(f"User {current_user.username} is deleting document {document_id} from subject {matiere}")
        
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
                "deleted_document": target_document,
                "matiere": matiere
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id} from subject {matiere}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )

@router.get("/matieres/{matiere}/documents/{document_id}/content", response_model=ApiResponse)
async def get_document_content_endpoint(
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    document_id: str = Path(..., description="Document ID"),
    session=Depends(get_session)
):
    """
    Get the content of a specific document.
    """
    try:
        current_user = await get_current_user_simple(user_id, session)
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
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    session=Depends(get_session)
):
    """
    Manually trigger re-indexing of all documents for a subject (teacher or admin only).
    Useful for maintenance or after system updates.
    """
    try:
        current_user = await get_current_user_simple(user_id, session)
        
        # Check if user has teacher or admin role
        if current_user.role not in ["teacher", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource. Teacher or admin role required.",
            )
        
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
        
        for document in documents:
            try:
                logger.info(f"Re-indexing document: {document['filename']}")
                
                # Process and index the document
                index_success, index_message = process_and_index_new_document(
                    matiere=matiere,
                    document_info=document
                )
                
                result = {
                    "document_id": document["id"],
                    "filename": document["filename"],
                    "success": index_success,
                    "message": index_message
                }
                
                indexing_results.append(result)
                
                if index_success:
                    success_count += 1
                    logger.info(f"Successfully re-indexed: {document['filename']}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to re-index {document['filename']}: {index_message}")
                    
            except Exception as doc_error:
                failed_count += 1
                error_msg = f"Error processing document: {str(doc_error)}"
                logger.error(f"Error re-indexing {document['filename']}: {error_msg}")
                
                indexing_results.append({
                    "document_id": document["id"],
                    "filename": document["filename"],
                    "success": False,
                    "message": error_msg
                })
        
        return {
            "success": True,
            "message": f"Re-indexing completed. {success_count} successful, {failed_count} failed",
            "data": {
                "processed_count": len(documents),
                "success_count": success_count,
                "failed_count": failed_count,
                "details": indexing_results
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during re-indexing for subject {matiere}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during re-indexing: {str(e)}"
        )