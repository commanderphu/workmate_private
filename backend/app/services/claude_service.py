"""
AI Service for document analysis with Claude
"""

from anthropic import Anthropic
from typing import Optional
import json
import base64
from pathlib import Path
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for analyzing documents using Claude AI"""

    def __init__(self):
        if not settings.CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY is not set in environment")
        self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = "claude-sonnet-4-6"

    def analyze_document(self, text: str, document_type: Optional[str] = None) -> dict:
        """Analyze OCR-extracted document text and return structured metadata."""
        prompt = self._build_analysis_prompt(text, document_type)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return self._parse_ai_response(response.content[0].text, document_type)

    def analyze_document_image(self, image_path: Path, document_type: Optional[str] = None) -> dict:
        """Analyze a document image using Claude Vision API."""
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        media_type_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"
        }
        media_type = media_type_map.get(image_path.suffix.lower(), "image/jpeg")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": image_data},
                    },
                    {"type": "text", "text": self._build_vision_analysis_prompt(document_type)}
                ],
            }],
        )
        return self._parse_ai_response(response.content[0].text, document_type)

    def generate_task_suggestion(self, metadata: dict) -> Optional[dict]:
        """Generate a suggested task based on document metadata."""
        if not metadata.get("action_required", False):
            return None

        if "suggested_task" in metadata and metadata["suggested_task"]:
            return metadata["suggested_task"]

        doc_type = metadata.get("type", "document")
        title = metadata.get("title", "Unbekanntes Dokument")
        amount = metadata.get("amount")

        if doc_type == "invoice" and amount:
            task_title = f"{title} bezahlen ({amount} {metadata.get('currency', 'EUR')})"
            task_description = f"Rechnung von {metadata.get('sender', {}).get('name', 'Unbekannt')} bezahlen"
        elif doc_type == "reminder":
            task_title = f"DRINGEND: {title} bezahlen"
            task_description = f"Mahnung! Sofort bezahlen: {amount} {metadata.get('currency', 'EUR')}"
        else:
            task_title = f"{title} bearbeiten"
            task_description = f"Dokument '{title}' bearbeiten"

        return {
            "title": task_title,
            "description": task_description,
            "due_date": metadata.get("due_date"),
            "priority": metadata.get("priority", "medium"),
            "amount": amount,
        }

    def _parse_ai_response(self, result_text: str, document_type: Optional[str] = None) -> dict:
        try:
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                json_str = result_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = result_text
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            return {
                "type": document_type or "other",
                "title": "Unbekanntes Dokument",
                "confidence": 0.3,
                "error": f"Failed to parse AI response: {str(e)}",
                "raw_response": result_text,
            }

    def _build_vision_analysis_prompt(self, document_type: Optional[str]) -> str:
        type_hint = f"\nHINT: This is likely a {document_type} document." if document_type else ""
        return f"""Analyze this document image and extract structured information.
{type_hint}

Return ONLY a valid JSON object with these fields:
{{
  "type": "invoice|reminder|contract|receipt|other",
  "title": "Short descriptive title",
  "confidence": 0.0-1.0,
  "extracted_text": "Full OCR text from the image",
  "sender": {{"name": "...", "address": "...", "email": "...", "phone": "..."}},
  "recipient": {{"name": "...", "address": "..."}},
  "amount": number or null,
  "currency": "EUR|USD|...",
  "due_date": "YYYY-MM-DD or null",
  "issue_date": "YYYY-MM-DD or null",
  "invoice_number": "... or null",
  "iban": "... or null",
  "payment_reference": "... or null",
  "description": "Brief summary",
  "action_required": true|false,
  "priority": "low|medium|high|critical",
  "suggested_task": {{"title": "...", "description": "...", "due_date": "YYYY-MM-DD or null"}},
  "ocr_quality": "high|medium|low"
}}

Rules: Return ONLY JSON. Use null for missing values. Extract ALL visible text.
German documents are common. Priority: critical=Mahnung/overdue, high=due soon, medium=invoice, low=receipt."""

    def _build_analysis_prompt(self, text: str, document_type: Optional[str]) -> str:
        type_hint = f"\nHINT: This is likely a {document_type} document." if document_type else ""
        return f"""Analyze the following document text and extract structured information.
{type_hint}

DOCUMENT TEXT:
---
{text}
---

Return ONLY a valid JSON object with these fields:
{{
  "type": "invoice|reminder|contract|receipt|other",
  "title": "Short descriptive title",
  "confidence": 0.0-1.0,
  "sender": {{"name": "...", "address": "..."}},
  "amount": number or null,
  "currency": "EUR|USD|...",
  "due_date": "YYYY-MM-DD or null",
  "invoice_number": "... or null",
  "description": "Brief summary",
  "action_required": true|false,
  "priority": "low|medium|high|critical",
  "suggested_task": {{"title": "...", "description": "...", "due_date": "YYYY-MM-DD or null"}}
}}

Rules: Return ONLY JSON. Use null for missing values. German documents are common."""
