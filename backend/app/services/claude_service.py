"""
Claude AI Service for document analysis
"""

from anthropic import Anthropic
from typing import Optional
import json
from datetime import datetime

from ..core.config import settings


class ClaudeService:
    """Service for analyzing documents using Claude AI"""

    def __init__(self):
        if not settings.CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY not set in environment")

        self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"

    def analyze_document(
        self,
        text: str,
        document_type: Optional[str] = None
    ) -> dict:
        """
        Analyze document text and extract metadata

        Args:
            text: OCR extracted text from document
            document_type: Hint about document type (invoice, contract, etc.)

        Returns:
            dict: Extracted metadata including type, amounts, dates, etc.
        """
        prompt = self._build_analysis_prompt(text, document_type)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract JSON from response
            result_text = response.content[0].text

            # Parse JSON response
            try:
                # Try to extract JSON from markdown code blocks
                if "```json" in result_text:
                    json_str = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    json_str = result_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = result_text

                metadata = json.loads(json_str)
                return metadata

            except json.JSONDecodeError as e:
                # Fallback: return basic structure
                return {
                    "type": document_type or "other",
                    "title": "Unbekanntes Dokument",
                    "confidence": 0.3,
                    "error": f"Failed to parse AI response: {str(e)}",
                    "raw_response": result_text
                }

        except Exception as e:
            raise Exception(f"Claude AI analysis failed: {str(e)}")

    def _build_analysis_prompt(self, text: str, document_type: Optional[str]) -> str:
        """Build the analysis prompt for Claude"""

        type_hint = f"\nHINT: This is likely a {document_type} document." if document_type else ""

        return f"""Analyze the following document text and extract structured information.
{type_hint}

DOCUMENT TEXT:
---
{text}
---

Extract the following information and return it as a JSON object:

{{
  "type": "invoice|reminder|contract|receipt|other",
  "title": "Short descriptive title (e.g., 'Telekom Rechnung Januar 2026')",
  "confidence": 0.0-1.0 (how confident are you in the classification),
  "sender": {{
    "name": "Company/Person name",
    "address": "Full address if available"
  }},
  "amount": number (total amount if found, e.g., 89.99),
  "currency": "EUR|USD|CHF etc.",
  "due_date": "YYYY-MM-DD format if found",
  "invoice_number": "Invoice/reference number if found",
  "description": "Brief summary of what this document is about",
  "action_required": true|false (does this require user action?),
  "priority": "low|medium|high|critical",
  "suggested_task": {{
    "title": "Suggested task title (e.g., 'Telekom Rechnung bezahlen')",
    "description": "Task description with details",
    "due_date": "YYYY-MM-DD (deadline for action, if applicable)"
  }}
}}

IMPORTANT:
- Return ONLY valid JSON, no additional text
- Use null for missing values
- Be accurate with amounts and dates
- German documents are common, extract accordingly
- For priority: critical if overdue/Mahnung, high if due soon, medium for invoices, low for receipts
"""

    def generate_task_suggestion(self, metadata: dict) -> Optional[dict]:
        """
        Generate a suggested task based on document metadata

        Args:
            metadata: Document metadata from analyze_document

        Returns:
            dict: Task suggestion or None
        """
        if not metadata.get("action_required", False):
            return None

        # Use suggested_task from AI if available
        if "suggested_task" in metadata and metadata["suggested_task"]:
            return metadata["suggested_task"]

        # Fallback: generate basic task
        doc_type = metadata.get("type", "document")
        title = metadata.get("title", "Unbekanntes Dokument")
        amount = metadata.get("amount")
        due_date = metadata.get("due_date")

        task_title = f"{title} bearbeiten"
        task_description = f"Dokument '{title}' bearbeiten"

        if doc_type == "invoice" and amount:
            task_title = f"{title} bezahlen ({amount} {metadata.get('currency', 'EUR')})"
            task_description = f"Rechnung von {metadata.get('sender', {}).get('name', 'Unbekannt')} bezahlen"

        elif doc_type == "reminder":
            task_title = f"DRINGEND: {title} bezahlen"
            task_description = f"Mahnung! Sofort bezahlen: {amount} {metadata.get('currency', 'EUR')}"

        return {
            "title": task_title,
            "description": task_description,
            "due_date": due_date,
            "priority": metadata.get("priority", "medium"),
            "amount": amount
        }
