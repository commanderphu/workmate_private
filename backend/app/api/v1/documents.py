"""
Document endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...api.dependencies import get_current_active_user
from ...db.session import get_db
from ...models.user import User
from ...models.document import Document as DocumentModel
from ...models.file import File as FileModel
from ...schemas.document import DocumentResponse, DocumentWithFileResponse, DocumentUpdate
from ...services.file_storage import FileStorageService
from ...core.config import settings

router = APIRouter()
file_storage = FileStorageService()


@router.post("/", response_model=DocumentWithFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    type: str = Form(default="other"),
    title: Optional[str] = Form(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload a new document

    Args:
        file: File to upload (image or PDF)
        type: Document type (invoice, reminder, contract, receipt, other)
        title: Optional title for the document
    """
    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed: {', '.join(allowed_types)}"
        )

    # Save file
    file_path, checksum, size_bytes = await file_storage.save_file(
        file_content=file_content,
        filename=file.filename or "upload",
        user_id=current_user.id,
    )

    # Create File record
    db_file = FileModel(
        user_id=current_user.id,
        path=file_path,
        original_filename=file.filename or "upload",
        size_bytes=size_bytes,
        mime_type=file.content_type or "application/octet-stream",
        checksum=checksum,
        storage_backend="local",
    )
    db.add(db_file)
    db.flush()

    # Create Document record
    db_document = DocumentModel(
        user_id=current_user.id,
        file_id=db_file.id,
        type=type,
        title=title or file.filename,
        processing_status="pending",
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    # TODO: Trigger background processing (OCR + AI analysis)
    # This will be done via Celery task

    return db_document


@router.get("/", response_model=List[DocumentWithFileResponse])
def list_documents(
    skip: int = 0,
    limit: int = 50,
    type: Optional[str] = None,
    processing_status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List user's documents

    Args:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        type: Filter by document type
        processing_status: Filter by processing status
    """
    query = db.query(DocumentModel).filter(DocumentModel.user_id == current_user.id)

    if type:
        query = query.filter(DocumentModel.type == type)
    if processing_status:
        query = query.filter(DocumentModel.processing_status == processing_status)

    documents = query.order_by(DocumentModel.uploaded_at.desc()).offset(skip).limit(limit).all()
    return documents


@router.get("/{document_id}", response_model=DocumentWithFileResponse)
def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific document"""
    document = db.query(DocumentModel).filter(
        DocumentModel.id == document_id,
        DocumentModel.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: UUID,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a document"""
    document = db.query(DocumentModel).filter(
        DocumentModel.id == document_id,
        DocumentModel.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update fields
    if document_update.title is not None:
        document.title = document_update.title
    if document_update.type is not None:
        document.type = document_update.type
    if document_update.doc_metadata is not None:
        document.doc_metadata = document_update.doc_metadata

    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a document and its file"""
    document = db.query(DocumentModel).filter(
        DocumentModel.id == document_id,
        DocumentModel.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from storage
    try:
        await file_storage.delete_file(document.file.path)
    except Exception as e:
        # Log error but continue with deletion
        print(f"Error deleting file: {e}")

    # Delete from database (cascade will delete file record)
    db.delete(document)
    db.commit()

    return None
