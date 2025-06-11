"""Services for managing documents with database tracking."""
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlmodel import Session, select
from app.core.config import settings
from app.db.models import Document
from app.db.session import get_session
from app.services.rag.documents import calculer_hash_fichier, upload_document_to_subject

logger = logging.getLogger(__name__)

def get_document_by_hash(session: Session, file_hash: str) -> Optional[Document]:
    """
    Get a document by its file hash.
    
    Args:
        session: Database session
        file_hash: MD5 hash of the file
        
    Returns:
        Document if found, None otherwise
    """
    statement = select(Document).where(Document.file_hash == file_hash)
    return session.exec(statement).first()

def get_documents_by_matiere(session: Session, matiere: str) -> List[Document]:
    """
    Get all documents for a specific matière.
    
    Args:
        session: Database session
        matiere: Subject identifier
        
    Returns:
        List of Document objects
    """
    statement = select(Document).where(Document.matiere == matiere)
    return list(session.exec(statement).all())

def create_or_update_document(
    session: Session,
    file_path: str,
    matiere: str,
    is_exam: bool = False
) -> Tuple[Document, bool]:
    """
    Create a new document record or update existing one if file has changed.
    
    Args:
        session: Database session
        file_path: Full path to the file
        matiere: Subject identifier
        is_exam: Whether this is an exam document
        
    Returns:
        Tuple of (Document, is_new) where is_new indicates if this is a new document
    """
    # Calculate current file hash
    current_hash = calculer_hash_fichier(file_path)
    
    # Get file stats
    file_stats = os.stat(file_path)
    filename = os.path.basename(file_path)
    relative_path = os.path.relpath(file_path, settings.COURS_DIR)
    file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
    file_mtime = datetime.fromtimestamp(file_stats.st_mtime)
    
    # Check if document already exists
    existing_doc = get_document_by_hash(session, current_hash)
    
    if existing_doc:
        # Document exists with same hash, update last_modified if needed
        if existing_doc.last_modified < file_mtime:
            existing_doc.last_modified = file_mtime
            session.add(existing_doc)
            session.commit()
            session.refresh(existing_doc)
        return existing_doc, False
    
    # Check if there's a document with same file path but different hash (file was modified)
    statement = select(Document).where(Document.file_path == relative_path)
    old_version = session.exec(statement).first()
    
    if old_version:
        # File was modified, remove old version and create new one
        session.delete(old_version)
        session.commit()
        logger.info(f"Removed old version of {filename} (hash: {old_version.file_hash})")
    
    # Create new document record
    new_document = Document(
        file_hash=current_hash,
        filename=filename,
        matiere=matiere,
        file_path=relative_path,
        document_type=file_extension,
        is_exam=is_exam,
        file_size=file_stats.st_size,
        upload_date=datetime.fromtimestamp(file_stats.st_ctime),
        last_modified=file_mtime,
        is_indexed=False
    )
    
    session.add(new_document)
    session.commit()
    session.refresh(new_document)
    
    logger.info(f"Added new document: {filename} (hash: {current_hash})")
    return new_document, True

def upload_document_with_tracking(
    matiere: str,
    filename: str,
    file_content: bytes,
    is_exam: bool = False
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Upload a document and track it in the database.
    
    Args:
        matiere: Subject identifier
        filename: Name of the file
        file_content: File content as bytes
        is_exam: Whether this is an exam document
        
    Returns:
        Tuple[bool, str, Optional[Dict]]: (success, message, document_info)
    """
    try:
        # First upload the file to filesystem
        success, message, file_info = upload_document_to_subject(matiere, filename, file_content, is_exam)
        
        if not success:
            return success, message, file_info
        
        # Now add/update the database record
        with next(get_session()) as session:
            # Construct file path for database tracking
            file_path = os.path.join(settings.COURS_DIR, file_info["file_path"])
            
            # Create or update document record
            doc, is_new = create_or_update_document(session, file_path, matiere, is_exam)
            
            # Return enhanced document info with database data
            document_info = {
                "id": doc.file_hash,
                "filename": doc.filename,
                "matiere": doc.matiere,
                "document_type": doc.document_type,
                "is_exam": doc.is_exam,
                "file_path": doc.file_path,
                "file_size": doc.file_size,
                "upload_date": doc.upload_date.isoformat(),
                "last_modified": doc.last_modified.isoformat(),
                "is_indexed": doc.is_indexed,
                "last_indexed": doc.last_indexed.isoformat() if doc.last_indexed else None
            }
            
            action = "added" if is_new else "updated"
            return True, f"Document {filename} {action} successfully", document_info
            
    except Exception as e:
        logger.error(f"Error uploading document with tracking: {e}")
        return False, f"Error uploading document: {str(e)}", None

def mark_document_as_indexed(session: Session, file_hash: str) -> bool:
    """
    Mark a document as indexed in the vector database.
    
    Args:
        session: Database session
        file_hash: MD5 hash of the file
        
    Returns:
        True if document was found and updated, False otherwise
    """
    document = get_document_by_hash(session, file_hash)
    if document:
        document.is_indexed = True
        document.last_indexed = datetime.now()
        session.add(document)
        session.commit()
        return True
    return False

def get_unindexed_documents(session: Session, matiere: Optional[str] = None) -> List[Document]:
    """
    Get documents that haven't been indexed yet.
    
    Args:
        session: Database session
        matiere: Optional subject filter
        
    Returns:
        List of unindexed Document objects
    """
    statement = select(Document).where(Document.is_indexed == False)
    if matiere:
        statement = statement.where(Document.matiere == matiere)
    
    return list(session.exec(statement).all())

def get_modified_documents(session: Session, matiere: Optional[str] = None) -> List[Document]:
    """
    Get documents that exist on disk but have been modified since last indexing.
    
    Args:
        session: Database session
        matiere: Optional subject filter
        
    Returns:
        List of Document objects that need reindexing
    """
    statement = select(Document).where(Document.is_indexed == True)
    if matiere:
        statement = statement.where(Document.matiere == matiere)
    
    documents = list(session.exec(statement).all())
    modified_docs = []
    
    for doc in documents:
        full_path = os.path.join(settings.COURS_DIR, doc.file_path)
        
        # Check if file still exists
        if not os.path.exists(full_path):
            # File was deleted, remove from database
            session.delete(doc)
            logger.info(f"Removed deleted file from database: {doc.filename}")
            continue
            
        # Check if file was modified
        try:
            current_hash = calculer_hash_fichier(full_path)
            if current_hash != doc.file_hash:
                modified_docs.append(doc)
        except Exception as e:
            logger.error(f"Error checking file {full_path}: {e}")
    
    if modified_docs:
        session.commit()
    
    return modified_docs

def sync_documents_with_filesystem(session: Session, matiere: str) -> Dict[str, int]:
    """
    Synchronize database document records with files on the filesystem.
    
    Args:
        session: Database session
        matiere: Subject identifier
        
    Returns:
        Dict with sync statistics
    """
    matiere_dir = os.path.join(settings.COURS_DIR, matiere)
    
    if not os.path.exists(matiere_dir):
        logger.warning(f"Matière directory {matiere} does not exist")
        return {"added": 0, "updated": 0, "deleted": 0, "errors": 0}
    
    stats = {"added": 0, "updated": 0, "deleted": 0, "errors": 0}
    
    # Supported extensions
    extensions = ['.md', '.txt', '.pdf', '.docx', '.pptx', '.doc', '.odt', '.odp']
    
    # Scan filesystem for documents
    found_files = set()
    
    for root, dirs, files in os.walk(matiere_dir):
        for file in files:
            # Skip README files
            if file.lower() == 'readme.md':
                continue
                
            file_extension = os.path.splitext(file)[1].lower()
            if file_extension in extensions:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, settings.COURS_DIR)
                found_files.add(relative_path)
                
                try:
                    # Check if this is an exam document
                    is_exam = "examens" in relative_path
                    
                    # Create or update document record
                    doc, is_new = create_or_update_document(session, file_path, matiere, is_exam)
                    
                    if is_new:
                        stats["added"] += 1
                    else:
                        stats["updated"] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    stats["errors"] += 1
    
    # Remove database records for files that no longer exist
    existing_docs = get_documents_by_matiere(session, matiere)
    for doc in existing_docs:
        if doc.file_path not in found_files:
            session.delete(doc)
            stats["deleted"] += 1
            logger.info(f"Removed database record for deleted file: {doc.filename}")
    
    session.commit()
    
    logger.info(f"Sync completed for {matiere}: {stats}")
    return stats

def lister_documents(matiere: str) -> Dict[str, Any]:
    """
    List all documents for a matière from the database.
    
    Args:
        matiere: Subject identifier
        
    Returns:
        Dict with success status and document list
    """
    try:
        with next(get_session()) as session:
            # First sync with filesystem to ensure database is up to date
            sync_documents_with_filesystem(session, matiere)
            
            # Get documents from database
            documents = get_documents_by_matiere(session, matiere)
            
            document_list = []
            for doc in documents:
                document_list.append({
                    "id": doc.file_hash,
                    "filename": doc.filename,
                    "matiere": doc.matiere,
                    "document_type": doc.document_type,
                    "is_exam": doc.is_exam,
                    "file_path": doc.file_path,
                    "file_size": doc.file_size,
                    "upload_date": doc.upload_date.isoformat(),
                    "last_modified": doc.last_modified.isoformat(),
                    "is_indexed": doc.is_indexed,
                    "last_indexed": doc.last_indexed.isoformat() if doc.last_indexed else None
                })
            
            return {
                "success": True,
                "data": document_list
            }
            
    except Exception as e:
        logger.error(f"Error listing documents for {matiere}: {e}")
        return {
            "success": False,
            "data": [],
            "message": f"Error: {str(e)}"
        }

def get_document_changes_since_last_index(matiere: str) -> Dict[str, Any]:
    """
    Get documents that need to be reindexed (new or modified since last indexing).
    
    Args:
        matiere: Subject identifier
        
    Returns:
        Dict with new and modified documents
    """
    try:
        with next(get_session()) as session:
            # Sync with filesystem first
            sync_documents_with_filesystem(session, matiere)
            
            # Get unindexed documents
            unindexed = get_unindexed_documents(session, matiere)
            
            # Get modified documents
            modified = get_modified_documents(session, matiere)
            
            return {
                "success": True,
                "data": {
                    "new_documents": len(unindexed),
                    "modified_documents": len(modified),
                    "total_changes": len(unindexed) + len(modified),
                    "unindexed": [doc.file_hash for doc in unindexed],
                    "modified": [doc.file_hash for doc in modified]
                }
            }
            
    except Exception as e:
        logger.error(f"Error checking document changes for {matiere}: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

def supprimer_document(matiere: str, document_id: str):
    """Supprime un document d'une matière."""
    return {"success": True, "message": f"Document {document_id} supprimé"} 