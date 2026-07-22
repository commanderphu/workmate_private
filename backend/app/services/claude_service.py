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
        if "suggested_task" in metadata and metadata["suggested_task"]:
            return metadata["suggested_task"]

        doc_type = metadata.get("type", "document")

        # Contracts always get a task (Kündigungsfrist must not be missed)
        if doc_type != "contract" and not metadata.get("action_required", False):
            return None
        title = metadata.get("title", "Unbekanntes Dokument")
        amount = metadata.get("amount")

        if doc_type == "invoice" and amount:
            task_title = f"{title} bezahlen ({amount} {metadata.get('currency', 'EUR')})"
            task_description = f"Rechnung von {metadata.get('sender', {}).get('name', 'Unbekannt')} bezahlen"
        elif doc_type == "reminder":
            task_title = f"DRINGEND: {title} bezahlen"
            task_description = f"Mahnung! Sofort bezahlen: {amount} {metadata.get('currency', 'EUR')}"
        elif doc_type == "contract":
            partner = metadata.get("contract_partner") or metadata.get("sender", {}).get("name", "Unbekannt")
            deadline = metadata.get("cancellation_deadline") or metadata.get("due_date")
            monthly = metadata.get("monthly_cost")
            cost_hint = f" ({monthly} EUR/Monat)" if monthly else ""
            renewal_hint = " – Achtung: automatische Verlängerung!" if metadata.get("auto_renewal") else ""
            task_title = f"Kündigung prüfen: {partner}{cost_hint}"
            task_description = (
                f"Kündigungsfrist für Vertrag mit {partner} endet am {deadline}.{renewal_hint} "
                f"Kündigung rechtzeitig schriftlich einreichen."
            )
            return {
                "title": task_title,
                "description": task_description,
                "due_date": deadline,
                "priority": metadata.get("priority", "medium"),
                "amount": monthly,
            }
        elif doc_type == "identity_document":
            due_date = metadata.get("due_date")
            task_title = f"{title} verlängern / erneuern"
            task_description = f"Dokument läuft ab: {due_date}. Rechtzeitig Termin beim Bürgeramt buchen."
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
  "type": "invoice|reminder|contract|receipt|tax_document|payslip|insurance|bank_statement|letter|identity_document|other",
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
  "ocr_quality": "high|medium|low",
  "contract_start": "YYYY-MM-DD or null (only for contract type)",
  "contract_end": "YYYY-MM-DD or null (only for contract type)",
  "notice_period_days": number or null,
  "cancellation_deadline": "YYYY-MM-DD or null (contract_end minus notice_period)",
  "auto_renewal": true|false|null,
  "monthly_cost": number or null,
  "contract_partner": "company name or null"
}}

Type guide: invoice=Rechnung, reminder=Mahnung, contract=Vertrag, receipt=Quittung/Kassenbon,
tax_document=Steuerbescheid/Lohnsteuerbescheinigung/Steuererklärung, payslip=Gehaltsabrechnung/Lohnabrechnung,
insurance=Versicherungspolice/Schadensmeldung, bank_statement=Kontoauszug, letter=Behördenpost/Brief,
identity_document=Personalausweis/Reisepass/Führerschein/Krankenversicherungskarte (use due_date for expiry date),
other=rest.
Rules: Return ONLY JSON. Use null for missing values. Extract ALL visible text.
For identity_document: set action_required=true if expiry within 6 months, priority=high if within 3 months.
Priority: critical=Mahnung/overdue, high=due soon, medium=invoice/tax, low=receipt/statement."""

    def analyze_for_paperless(self, text: str) -> dict:
        """Analyze Paperless-ngx document: return summary + suggested tags."""
        prompt = f"""Analysiere den folgenden Dokumententext und gib strukturierte Informationen zurück.

DOKUMENTTEXT:
---
{text[:6000]}
---

Antworte NUR mit einem gültigen JSON-Objekt:
{{
  "type": "Rechnung|Mahnung|Vertrag|Quittung|Behörde|Versicherung|Bank|Sonstiges",
  "summary": "2-3 Sätze Zusammenfassung auf Deutsch: Was ist das Dokument, von wem, worum geht es?",
  "tags": ["maximal 5 Tags als kurze Strings, z.B. Absendername, Kategorie, Jahr"],
  "sender": "Firmen- oder Absendername oder null",
  "amount": Zahl oder null,
  "currency": "EUR",
  "due_date": "YYYY-MM-DD oder null",
  "action_required": true|false
}}

Regeln: Nur JSON. Deutsche Dokumente sind üblich. Tags sollen kurz und nützlich sein (z.B. "Telekom", "Rechnung", "2026", "Offen").
"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return self._parse_ai_response(response.content[0].text)

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
  "type": "invoice|reminder|contract|receipt|tax_document|payslip|insurance|bank_statement|letter|identity_document|other",
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
  "suggested_task": {{"title": "...", "description": "...", "due_date": "YYYY-MM-DD or null"}},
  "contract_start": "YYYY-MM-DD or null",
  "contract_end": "YYYY-MM-DD or null",
  "notice_period_days": number or null,
  "cancellation_deadline": "YYYY-MM-DD or null",
  "auto_renewal": true|false|null,
  "monthly_cost": number or null,
  "contract_partner": "company name or null"
}}

Type guide: invoice=Rechnung, reminder=Mahnung, contract=Vertrag, receipt=Quittung,
tax_document=Steuerbescheid/Lohnsteuerbescheinigung, payslip=Gehaltsabrechnung,
insurance=Versicherung, bank_statement=Kontoauszug, letter=Behördenpost/Brief,
identity_document=Personalausweis/Reisepass/Führerschein (use due_date for expiry), other=rest.
For contract: extract Kündigungsfrist, calculate cancellation_deadline=contract_end-notice_period_days, action_required=true if cancellation_deadline within 60 days.
For identity_document: action_required=true if expiry within 6 months.
Rules: Return ONLY JSON. Use null for missing values. German documents are common."""
