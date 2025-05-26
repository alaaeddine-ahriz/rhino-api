"""Models for document management."""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class DocumentType(str, Enum):
    """Enum for document types."""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    TXT = "txt"
    MD = "md"
    EXAM = "exam"  # Special type for exam documents

class DocumentBase(BaseModel):
    """Base model for a document."""
    filename: str
    matiere: str
    document_type: DocumentType
    is_exam: bool = False

class DocumentCreate(BaseModel):
    """Model for creating/uploading a new document."""
    matiere: str = Field(..., description="Subject the document belongs to")
    is_exam: bool = Field(False, description="Whether this document is an exam")
    
    # The file itself will be handled by FastAPI's UploadFile

class DocumentResponse(DocumentBase):
    """Model for document response."""
    id: str
    file_path: str
    file_size: int
    upload_date: str
    last_indexed: Optional[str] = None
    
class DocumentList(BaseModel):
    """Model for a list of documents."""
    documents: List[DocumentResponse] = [] 