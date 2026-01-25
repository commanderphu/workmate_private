"""
Document schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class DocumentBase(BaseModel):
    """Base document schema"""
    title: Optional[str] = None
    type: str = Field(..., description="Document type: invoice, reminder, contract, receipt, other")


class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    type: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: UUID
    user_id: UUID
    file_id: UUID
    doc_metadata: Dict[str, Any] = {}
    processing_status: str
    confidence_score: Optional[float] = None
    extracted_text: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    """Schema for file response"""
    id: UUID
    original_filename: str
    size_bytes: int
    mime_type: str
    path: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentWithFileResponse(DocumentResponse):
    """Schema for document with file info"""
    file: FileResponse

    class Config:
        from_attributes = True
