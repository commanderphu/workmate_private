"""
AI analysis task for Paperless-ngx documents
"""

import logging
from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified

from ..celery import celery_app
from ..db.session import SessionLocal
from ..models.document import Document as DocumentModel
from ..services.claude_service import ClaudeService
from ..services.paperless_service import get_paperless_client

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.analyze_paperless_document", bind=True, max_retries=2)
def analyze_paperless_document(self, document_id: str):
    """
    Run Claude AI analysis on a Paperless-ngx document:
    - Generates a German summary
    - Suggests tags
    - Writes results back to Paperless
    """
    db = SessionLocal()
    try:
        doc = db.query(DocumentModel).filter(DocumentModel.id == UUID(document_id)).first()
        if not doc:
            logger.warning(f"Document {document_id} not found")
            return

        text = doc.extracted_text or ""
        if len(text.strip()) < 20:
            logger.info(f"Document {document_id} has no usable OCR text, skipping AI analysis")
            doc.processing_status = "done"
            db.commit()
            return

        doc.processing_status = "processing"
        db.commit()

        claude = ClaudeService()
        result = claude.analyze_for_paperless(text)

        # Persist metadata — use dict() to create new object so SQLAlchemy detects the change
        meta = dict(doc.doc_metadata or {})
        sender = result.get("sender")
        meta.update({
            # Raw AI fields (used for Paperless writeback)
            "ai_type": result.get("type"),
            "ai_summary": result.get("summary"),
            "ai_tags": result.get("tags", []),
            "ai_action_required": result.get("action_required", False),
            # Flutter-compatible display fields
            "sender": {"name": sender} if sender else None,
            "amount": result.get("amount"),
            "currency": result.get("currency", "EUR"),
            "due_date": result.get("due_date"),
            "description": result.get("summary"),
        })
        doc.doc_metadata = meta
        flag_modified(doc, "doc_metadata")
        doc.type = _map_type(result.get("type", "Sonstiges"))
        doc.processing_status = "done"
        db.commit()

        # Write back to Paperless
        paperless_id = meta.get("paperless_id")
        if paperless_id:
            import asyncio
            asyncio.run(_write_to_paperless(int(paperless_id), result))

        logger.info(f"Paperless AI analysis done for document {document_id}")

    except Exception as exc:
        logger.error(f"Error analyzing Paperless document {document_id}: {exc}")
        db.rollback()
        try:
            doc = db.query(DocumentModel).filter(DocumentModel.id == UUID(document_id)).first()
            if doc:
                doc.processing_status = "failed"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


async def _write_to_paperless(paperless_id: int, result: dict):
    client = get_paperless_client()
    if not client:
        return

    tag_ids = []
    for tag_name in result.get("tags", []):
        if tag_name:
            tag = await client.get_or_create_tag(tag_name)
            tag_ids.append(tag["id"])

    doc_type = result.get("type", "")
    if doc_type and doc_type != "Sonstiges":
        type_tag = await client.get_or_create_tag(doc_type)
        if type_tag["id"] not in tag_ids:
            tag_ids.append(type_tag["id"])

    summary = result.get("summary", "")
    sender = result.get("sender") or ""
    amount = result.get("amount")
    due_date = result.get("due_date") or ""

    note_lines = ["🤖 Workmate AI Analyse"]
    if summary:
        note_lines.append(f"\n{summary}")
    if sender:
        note_lines.append(f"\nAbsender: {sender}")
    if amount:
        note_lines.append(f"Betrag: {amount} {result.get('currency', 'EUR')}")
    if due_date:
        note_lines.append(f"Fällig: {due_date}")
    if result.get("action_required"):
        note_lines.append("⚠️ Handlungsbedarf")

    await client.update_document(
        document_id=paperless_id,
        tags=tag_ids if tag_ids else None,
        notes="\n".join(note_lines),
    )


def _map_type(ai_type: str) -> str:
    mapping = {
        "Rechnung": "invoice",
        "Mahnung": "reminder",
        "Vertrag": "contract",
        "Quittung": "receipt",
    }
    return mapping.get(ai_type, "other")
