"""
Paperless-ngx integration endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ...api.dependencies import get_current_active_user
from ...db.session import get_db
from ...models.user import User
from ...services.paperless_service import PaperlessClient, PaperlessSyncService, get_paperless_client
from ...core.config import settings

router = APIRouter(prefix="/integrations/paperless", tags=["paperless"])


class PaperlessStatus(BaseModel):
    configured: bool
    url: Optional[str] = None
    total_documents: Optional[int] = None
    error: Optional[str] = None


class SyncResult(BaseModel):
    imported: int
    skipped: int
    started_at: datetime
    finished_at: datetime


class WriteBackResult(BaseModel):
    success: bool
    document_id: str


@router.get("/status", response_model=PaperlessStatus)
async def get_status():
    """Check if Paperless is configured and reachable"""
    client = get_paperless_client()
    if not client:
        return PaperlessStatus(configured=False)

    try:
        info = await client.test_connection()
        return PaperlessStatus(
            configured=True,
            url=settings.PAPERLESS_URL,
            total_documents=info["total_documents"],
        )
    except Exception as e:
        return PaperlessStatus(configured=True, url=settings.PAPERLESS_URL, error=str(e))


@router.post("/sync", response_model=SyncResult)
async def sync_documents(
    since: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Import new documents from Paperless into Workmate.
    Optionally pass ?since=2025-01-01T00:00:00 to limit the lookback window.
    """
    client = get_paperless_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Paperless not configured. Set PAPERLESS_URL and PAPERLESS_TOKEN.",
        )

    started = datetime.utcnow()
    svc = PaperlessSyncService(db=db, user_id=current_user.id)

    try:
        result = await svc.import_new_documents(since=since)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return SyncResult(
        imported=result["imported"],
        skipped=result["skipped"],
        started_at=started,
        finished_at=datetime.utcnow(),
    )


@router.post("/writeback/{document_id}", response_model=WriteBackResult)
async def write_back_to_paperless(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Push Workmate analysis (tags, custom fields, notes) back to the
    corresponding Paperless document.
    """
    from uuid import UUID

    client = get_paperless_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Paperless not configured.",
        )

    try:
        doc_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id")

    svc = PaperlessSyncService(db=db, user_id=current_user.id)
    success = await svc.write_back(doc_uuid)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Document not found or not linked to a Paperless document",
        )

    return WriteBackResult(success=True, document_id=document_id)
