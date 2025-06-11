"""Routes for document management."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Path, Query
from typing import List, Optional
from datetime import datetime
from fastapi.responses import FileResponse
import os

from app.models.base import ApiResponse
from app.models.auth import UserInDB
from app.models.document import DocumentCreate, DocumentResponse, DocumentList
from app.api.deps import get_current_user_simple
from app.core.exceptions import NotFoundError
from app.services.rag.documents import (
    delete_document_from_subject,
    get_document_content,
    process_and_index_new_document,
    initialiser_structure_dossiers
)
from app.services.documents import lister_documents, upload_document_with_tracking, get_document_changes_since_last_index, mark_document_as_indexed
from app.services.rag.embeddings import delete_documents
from app.services.rag.core import initialize_pinecone
from app.db.session import get_session
from app.core.config import settings

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
        
        # Get documents for the subject from database
        result = lister_documents(matiere)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Documents for subject {matiere} retrieved successfully",
                "data": {
                    "documents": result["data"],
                    "count": len(result["data"])
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Error retrieving documents")
            )
        
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
        
        # Upload the document with database tracking
        success, message, document_info = upload_document_with_tracking(
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
            # Map database document format to expected format for indexing
            indexing_document_info = {
                "file_hash": document_info["file_hash"],
                "filename": document_info["filename"],
                "file_path": document_info["file_path"],
                "document_type": document_info["document_type"],
                "is_exam": document_info["is_exam"],
                "upload_date": document_info["upload_date"]
            }
            
            index_success, index_message = process_and_index_new_document(
                matiere=matiere,
                document_info=indexing_document_info
            )
            
            if index_success:
                logger.info(f"Document {file.filename} successfully indexed into vector database")
                message += f". Document indexed successfully: {index_message}"
                
                # If indexing was successful, mark document as indexed in database
                try:
                    with next(get_session()) as db_session:
                        mark_document_as_indexed(db_session, document_info["file_hash"])
                except Exception as db_error:
                    logger.warning(f"Document indexed but failed to update database: {db_error}")
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
        result = lister_documents(matiere)
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Error retrieving documents")
            )
        
        documents = result["data"]
        target_document = None
        resolved_file_hash = None
        for doc in documents:
            if str(doc["id"]) == str(document_id):
                target_document = doc
                resolved_file_hash = doc["file_hash"]
                break
            if doc.get("file_hash") == document_id:
                target_document = doc
                resolved_file_hash = doc["file_hash"]
                break
        
        # If we resolved a file hash via numeric id, use it for deletion
        if resolved_file_hash:
            document_id_for_deletion = resolved_file_hash
        else:
            document_id_for_deletion = document_id
        
        # Delete the document from filesystem
        success, message = delete_document_from_subject(matiere, document_id_for_deletion)
        
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

@router.get("/matieres/{matiere}/documents/{document_id}/content", response_class=FileResponse)
async def get_document_file_endpoint(
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    document_id: str = Path(..., description="Document ID (numeric id or file hash)"),
    session=Depends(get_session)
):
    """
    Serve the **raw file** for the requested document so the caller can download it.
    The caller may supply either the numeric `id` stored in the database or the
    `file_hash`. The function resolves the hash and then returns a `FileResponse`.
    """
    try:
        current_user = await get_current_user_simple(user_id, session)
        logger.info(
            f"User {current_user.username} is downloading document {document_id} in subject {matiere}"
        )

        # Resolve numeric id → file_hash if necessary
        file_hash_param = str(document_id)
        try:
            list_result = lister_documents(matiere)
            if list_result.get("success"):
                for d in list_result["data"]:
                    if str(d["id"]) == str(document_id):
                        file_hash_param = d["file_hash"]
                        break
        except Exception:
            pass

        # Find document data
        doc_path = None
        filename = None
        list_result = lister_documents(matiere)
        if not list_result.get("success"):
            raise HTTPException(status_code=500, detail="Unable to list documents")

        for d in list_result["data"]:
            if d["file_hash"] == file_hash_param:
                doc_path = os.path.join(settings.COURS_DIR, d["file_path"])
                filename = d["filename"]
                break

        if not doc_path or not os.path.exists(doc_path):
            raise HTTPException(status_code=404, detail="Document not found")

        # Return the file as attachment
        return FileResponse(
            path=doc_path,
            filename=filename,
            media_type="application/octet-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error sending file for document {document_id} in subject {matiere}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document file: {str(e)}",
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
        
        # Get all documents for the subject from database
        result = lister_documents(matiere)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Error retrieving documents")
            )
        
        documents = result["data"]
        
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
                
                # Map database document format to expected format for indexing
                document_info = {
                    "file_hash": document["file_hash"],
                    "filename": document["filename"],
                    "file_path": document["file_path"],
                    "document_type": document["document_type"],
                    "is_exam": document["is_exam"],
                    "upload_date": document["upload_date"]
                }
                
                # Process and index the document
                index_success, index_message = process_and_index_new_document(
                    matiere=matiere,
                    document_info=document_info
                )
                
                # If indexing was successful, mark document as indexed in database
                if index_success:
                    try:
                        with next(get_session()) as db_session:
                            mark_document_as_indexed(db_session, document["file_hash"])
                    except Exception as db_error:
                        logger.warning(f"Document indexed but failed to update database: {db_error}")
                
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

@router.get("/matieres/{matiere}/documents/changes", response_model=ApiResponse)
async def get_document_changes(
    user_id: int = Query(..., description="User ID for authentication"),
    matiere: str = Path(..., description="Subject code (e.g. 'MATH')"),
    session=Depends(get_session)
):
    """
    Get documents that have changed since last indexing (new or modified).
    """
    try:
        current_user = await get_current_user_simple(user_id, session)
        logger.info(f"User {current_user.username} is checking document changes for subject {matiere}")
        
        # Get document changes
        result = get_document_changes_since_last_index(matiere)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Document changes for subject {matiere} retrieved successfully",
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Error checking document changes")
            )
        
    except Exception as e:
        logger.error(f"Error checking document changes for subject {matiere}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking document changes: {str(e)}"
        )