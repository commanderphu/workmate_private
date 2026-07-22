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
from ..services.reminder_service import ReminderService


# Quality Assurance Thresholds
CONFIDENCE_THRESHOLDS = {
    "high": 0.85,      # High confidence - auto-approve
    "medium": 0.65,    # Medium confidence - needs review for critical actions
    "low": 0.40        # Low confidence - always needs manual review
}


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
        file_path = file_storage.get_full_path(document.file.path)

        if not Path(file_path).exists():
            raise Exception(f"File not found: {file_path}")

        claude_service = ClaudeService()

        # For images: Use Claude Vision API directly (more accurate)
        if document.file.mime_type.startswith("image/"):
            metadata = claude_service.analyze_document_image(
                image_path=Path(file_path),
                document_type=document.type if document.type != "other" else None
            )

            # Extract text from Vision API response
            extracted_text = metadata.get("extracted_text", "")
            ocr_confidence = 0.9 if metadata.get("ocr_quality") == "high" else (
                0.7 if metadata.get("ocr_quality") == "medium" else 0.5
            )

            # Save OCR results
            document.extracted_text = extracted_text
            document.confidence_score = ocr_confidence
            db.commit()

        # For PDFs: Use traditional OCR + text analysis
        else:
            ocr_service = OCRService()
            extracted_text, ocr_confidence = ocr_service.extract_from_pdf(Path(file_path))

            # Save OCR results
            document.extracted_text = extracted_text
            document.confidence_score = ocr_confidence
            db.commit()

            # Analyze extracted text with Claude
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

        # Step 3: Quality Assurance - Determine if manual review is needed
        ai_confidence = metadata.get("confidence", 0.0)
        needs_review = False
        review_reason = None

        if ai_confidence < CONFIDENCE_THRESHOLDS["low"]:
            needs_review = True
            review_reason = "Low AI confidence - manual review required"
        elif ai_confidence < CONFIDENCE_THRESHOLDS["medium"]:
            # Medium confidence - review needed for critical/high priority items
            if metadata.get("priority") in ["critical", "high"]:
                needs_review = True
                review_reason = "Medium confidence on critical document"
            if metadata.get("amount") and metadata.get("amount") > 500:
                needs_review = True
                review_reason = "Medium confidence on high-value document"
        elif ai_confidence < CONFIDENCE_THRESHOLDS["high"]:
            # Review needed only for critical items with high amounts
            if metadata.get("priority") == "critical" and metadata.get("amount", 0) > 1000:
                needs_review = True
                review_reason = "Critical high-value document requires verification"

        # Store QA decision in metadata
        if not document.doc_metadata:
            document.doc_metadata = {}
        document.doc_metadata["qa_needs_review"] = needs_review
        if review_reason:
            document.doc_metadata["qa_review_reason"] = review_reason

        # Step 4: Auto-create task if action required OR a suggested_task exists
        task_created = False
        doc_type = metadata.get("type", "other")
        always_suggest = doc_type in ("contract", "identity_document")
        task_suggestion = metadata.get("suggested_task") or (
            claude_service.generate_task_suggestion(metadata)
            if (metadata.get("action_required", False) or always_suggest)
            else None
        )

        if task_suggestion:
            # action_required → normal priority; suggested_task only → low priority
            default_priority = task_suggestion.get("priority", "medium") if metadata.get("action_required", False) else "low"

            if ai_confidence >= CONFIDENCE_THRESHOLDS["medium"] or not needs_review:
                new_task = TaskModel(
                    user_id=document.user_id,
                    document_id=document.id,
                    title=task_suggestion.get("title", "Dokument bearbeiten"),
                    description=task_suggestion.get("description", ""),
                    due_date=_parse_date(task_suggestion.get("due_date")),
                    priority=default_priority,
                    amount=task_suggestion.get("amount"),
                    currency=metadata.get("currency", "EUR"),
                    status="open",
                )
                db.add(new_task)
                db.commit()
                db.refresh(new_task)

                if metadata.get("action_required", False) or doc_type in ("contract", "identity_document"):
                    reminder_service = ReminderService()
                    schedule = "contract" if doc_type == "contract" else "priority"
                    reminder_service.create_reminders_for_task(new_task, db, schedule_type=schedule)

                task_created = True
            else:
                document.doc_metadata["suggested_task"] = task_suggestion

        # Mark processing as complete or needs_review
        if needs_review:
            document.processing_status = "needs_review"
        else:
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
