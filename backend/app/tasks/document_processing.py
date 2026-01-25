"""
Document processing background tasks
"""

from pathlib import Path
from datetime import datetime
from uuid import UUID
from typing import Optional

from ..celery import celery_app
from ..db.session import SessionLocal
from ..models.document import Document as DocumentModel
from ..models.task import Task as TaskModel
from ..services.ocr_service import OCRService
from ..services.claude_service import ClaudeService
from ..services.file_storage import FileStorageService


@celery_app.task(name="app.tasks.process_document")
def process_document(document_id: str):
    """
    Process uploaded document: OCR → AI Analysis → Task Creation

    Args:
        document_id: UUID of the document to process
    """
    db = SessionLocal()

    try:
        # Get document from database
        doc_uuid = UUID(document_id)
        document = db.query(DocumentModel).filter(DocumentModel.id == doc_uuid).first()

        if not document:
            raise Exception(f"Document {document_id} not found")

        # Update status to processing
        document.processing_status = "processing"
        db.commit()

        # Get file path
        file_storage = FileStorageService()
        file_path = file_storage.get_absolute_path(document.file.path)

        if not Path(file_path).exists():
            raise Exception(f"File not found: {file_path}")

        # Step 1: OCR - Extract text from image/PDF
        ocr_service = OCRService()

        if document.file.mime_type == "application/pdf":
            extracted_text, ocr_confidence = ocr_service.extract_from_pdf(Path(file_path))
        else:
            extracted_text, ocr_confidence = ocr_service.extract_text(Path(file_path))

        # Save OCR results
        document.extracted_text = extracted_text
        document.confidence_score = ocr_confidence
        db.commit()

        # Step 2: AI Analysis - Use Claude to extract metadata
        claude_service = ClaudeService()
        metadata = claude_service.analyze_document(
            text=extracted_text,
            document_type=document.type if document.type != "other" else None
        )

        # Update document with AI-extracted metadata
        document.doc_metadata = metadata

        # Update document title if AI suggests better one
        if metadata.get("title") and metadata.get("confidence", 0) > 0.6:
            document.title = metadata["title"]

        # Update document type if AI is confident
        if metadata.get("type") and metadata.get("confidence", 0) > 0.7:
            document.type = metadata["type"]

        db.commit()

        # Step 3: Auto-create task if action required
        task_created = False
        if metadata.get("action_required", False):
            task_suggestion = claude_service.generate_task_suggestion(metadata)

            if task_suggestion:
                # Create task from suggestion
                new_task = TaskModel(
                    user_id=document.user_id,
                    document_id=document.id,
                    title=task_suggestion.get("title", "Dokument bearbeiten"),
                    description=task_suggestion.get("description", ""),
                    due_date=_parse_date(task_suggestion.get("due_date")),
                    priority=task_suggestion.get("priority", "medium"),
                    amount=task_suggestion.get("amount"),
                    currency=metadata.get("currency", "EUR"),
                    status="open",
                )
                db.add(new_task)
                db.commit()
                task_created = True

        # Mark processing as complete
        document.processing_status = "done"
        document.processed_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "document_id": str(document.id),
            "ocr_confidence": ocr_confidence,
            "ai_confidence": metadata.get("confidence", 0),
            "task_created": task_created,
        }

    except Exception as e:
        # Mark as failed
        if document:
            document.processing_status = "failed"
            if not document.doc_metadata:
                document.doc_metadata = {}
            document.doc_metadata["error"] = str(e)
            db.commit()

        # Re-raise for Celery to handle
        raise

    finally:
        db.close()


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string from AI response"""
    if not date_str:
        return None

    try:
        # Try YYYY-MM-DD format
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            # Try YYYY-MM-DD HH:MM:SS format
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Give up
            return None
