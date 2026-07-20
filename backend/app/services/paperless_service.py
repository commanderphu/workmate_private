"""
Paperless-ngx API client and sync service
"""

import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from uuid import UUID

from ..core.config import settings

logger = logging.getLogger(__name__)


class PaperlessClient:
    """Async Paperless-ngx REST API client"""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

    async def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}/api{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def _patch(self, endpoint: str, data: dict) -> dict:
        url = f"{self.base_url}/api{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=self.headers, json=data) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def _post(self, endpoint: str, data: dict) -> dict:
        url = f"{self.base_url}/api{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def test_connection(self) -> Dict:
        """Test API connection and return basic stats"""
        result = await self._get("/documents/", params={"page_size": 1})
        return {"ok": True, "total_documents": result.get("count", 0)}

    async def get_documents(
        self,
        created_after: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict:
        params = {"page": page, "page_size": page_size, "ordering": "-created"}
        if created_after:
            params["created__date__gte"] = created_after.strftime("%Y-%m-%d")
        return await self._get("/documents/", params=params)

    async def get_document(self, document_id: int) -> Dict:
        return await self._get(f"/documents/{document_id}/")

    async def get_tags(self) -> List[Dict]:
        result = await self._get("/tags/", params={"page_size": 100})
        return result.get("results", [])

    async def create_tag(self, name: str, color: str = "#0066cc") -> Dict:
        return await self._post("/tags/", data={"name": name, "color": color})

    async def get_custom_fields(self) -> List[Dict]:
        result = await self._get("/custom_fields/", params={"page_size": 100})
        return result.get("results", [])

    async def create_custom_field(self, name: str, data_type: str = "string") -> Dict:
        return await self._post("/custom_fields/", data={"name": name, "data_type": data_type})

    async def update_document(
        self,
        document_id: int,
        tags: Optional[List[int]] = None,
        custom_fields: Optional[List[Dict]] = None,
        notes: Optional[str] = None,
    ) -> Dict:
        data = {}
        if tags is not None:
            data["tags"] = tags
        if custom_fields is not None:
            data["custom_fields"] = custom_fields
        if notes is not None:
            data["notes"] = notes
        return await self._patch(f"/documents/{document_id}/", data=data)

    async def get_or_create_tag(self, name: str) -> Dict:
        tags = await self.get_tags()
        for tag in tags:
            if tag["name"].lower() == name.lower():
                return tag
        return await self.create_tag(name)

    async def get_or_create_custom_field(self, name: str, data_type: str = "string") -> Dict:
        fields = await self.get_custom_fields()
        for field in fields:
            if field["name"].lower() == name.lower():
                return field
        return await self.create_custom_field(name, data_type)


def get_paperless_client() -> Optional[PaperlessClient]:
    """Get configured Paperless client from settings, or None if not configured"""
    if not settings.PAPERLESS_URL or not settings.PAPERLESS_TOKEN:
        return None
    return PaperlessClient(base_url=settings.PAPERLESS_URL, token=settings.PAPERLESS_TOKEN)


class PaperlessSyncService:
    """Sync documents between Paperless-ngx and Workmate"""

    def __init__(self, db, user_id: UUID):
        self.db = db
        self.user_id = user_id
        self.client = get_paperless_client()

    async def import_new_documents(self, since: Optional[datetime] = None) -> Dict:
        """
        Pull new documents from Paperless since last sync.
        Returns summary of what was imported.
        """
        if not self.client:
            raise RuntimeError("Paperless not configured (PAPERLESS_URL / PAPERLESS_TOKEN missing)")

        from ..models.document import Document as DocumentModel
        from ..models.file import File as FileModel
        from ..tasks.document_processing import process_document

        lookback = since or (datetime.utcnow() - timedelta(days=30))
        imported = 0
        skipped = 0
        page = 1

        while True:
            result = await self.client.get_documents(created_after=lookback, page=page)
            docs = result.get("results", [])

            if not docs:
                break

            for pdoc in docs:
                paperless_id = str(pdoc["id"])

                # Skip if already imported
                existing = (
                    self.db.query(DocumentModel)
                    .filter(
                        DocumentModel.user_id == self.user_id,
                        DocumentModel.doc_metadata["paperless_id"].astext == paperless_id,
                    )
                    .first()
                )
                if existing:
                    skipped += 1
                    continue

                # Create stub document — OCR text already available from Paperless
                db_doc = DocumentModel(
                    user_id=self.user_id,
                    type="other",
                    title=pdoc.get("title") or pdoc.get("original_file_name", "Untitled"),
                    processing_status="pending",
                    extracted_text=pdoc.get("content", ""),
                    doc_metadata={
                        "paperless_id": paperless_id,
                        "paperless_created": pdoc.get("created"),
                        "paperless_tags": pdoc.get("tags", []),
                        "source": "paperless_ngx",
                    },
                )
                self.db.add(db_doc)
                self.db.flush()

                process_document.delay(str(db_doc.id))
                imported += 1

            if not result.get("next"):
                break
            page += 1

        self.db.commit()
        logger.info(f"Paperless sync: {imported} imported, {skipped} skipped")
        return {"imported": imported, "skipped": skipped}

    async def write_back(self, document_id: UUID) -> bool:
        """
        Write Workmate analysis results back to the Paperless document
        (tags, custom fields, notes).
        """
        if not self.client:
            return False

        from ..models.document import Document as DocumentModel
        from ..models.task import Task as TaskModel

        doc = self.db.query(DocumentModel).filter(
            DocumentModel.id == document_id,
            DocumentModel.user_id == self.user_id,
        ).first()

        if not doc or not doc.doc_metadata:
            return False

        paperless_id = doc.doc_metadata.get("paperless_id")
        if not paperless_id:
            return False

        # Build tags
        processed_tag = await self.client.get_or_create_tag("workmate-processed")
        tags = [processed_tag["id"]]

        if doc.type and doc.type != "other":
            type_tag = await self.client.get_or_create_tag(f"type:{doc.type}")
            tags.append(type_tag["id"])

        # Build custom fields
        custom_fields = []

        if doc.doc_metadata.get("due_date"):
            field = await self.client.get_or_create_custom_field("workmate_due_date", "date")
            custom_fields.append({"field": field["id"], "value": doc.doc_metadata["due_date"]})

        if doc.doc_metadata.get("amount"):
            field = await self.client.get_or_create_custom_field("workmate_amount", "monetary")
            custom_fields.append({"field": field["id"], "value": doc.doc_metadata["amount"]})

        # Build notes
        tasks = (
            self.db.query(TaskModel)
            .filter(TaskModel.document_id == document_id)
            .all()
        )

        notes_lines = [
            f"Verarbeitet von Workmate Private am {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            f"Typ: {doc.type}",
        ]
        if tasks:
            notes_lines.append("\nErstelle Tasks:")
            for t in tasks:
                notes_lines.append(f"- {t.title} (Priorität: {t.priority}, Fällig: {t.due_date})")

        await self.client.update_document(
            document_id=int(paperless_id),
            tags=tags,
            custom_fields=custom_fields if custom_fields else None,
            notes="\n".join(notes_lines),
        )

        logger.info(f"Write-back to Paperless doc {paperless_id} done")
        return True
