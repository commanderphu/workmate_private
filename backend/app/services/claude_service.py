"""
AI Service for document analysis with Claude and OpenAI fallback
"""

from anthropic import Anthropic
from openai import OpenAI
from typing import Optional
import json
from datetime import datetime
import base64
from pathlib import Path
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for analyzing documents using Claude AI with OpenAI fallback"""

    def __init__(self):
        self.claude_client = None
        self.openai_client = None

        # Initialize Claude if API key available
        if settings.CLAUDE_API_KEY:
            self.claude_client = Anthropic(api_key=settings.CLAUDE_API_KEY)
            self.claude_model = "claude-sonnet-4-6"

        # Initialize OpenAI if API key available
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.openai_model = "gpt-4o"  # GPT-4 with vision

        if not self.claude_client and not self.openai_client:
            raise ValueError("Neither CLAUDE_API_KEY nor OPENAI_API_KEY set in environment")

        # For backward compatibility
        self.client = self.claude_client
        self.model = self.claude_model if self.claude_client else None

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

        # Try Claude first if available
        if self.claude_client:
            try:
                logger.info("Attempting document analysis with Claude")
                response = self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
                return self._parse_ai_response(result_text, document_type)
            except Exception as e:
                logger.warning(f"Claude analysis failed: {str(e)}")
                if self.openai_client:
                    logger.info("Falling back to OpenAI for text analysis")
                else:
                    raise Exception(f"Claude AI analysis failed and no OpenAI fallback: {str(e)}")

        # Fallback to OpenAI
        if self.openai_client:
            try:
                logger.info("Using OpenAI for text analysis")
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2048
                )
                result_text = response.choices[0].message.content
                return self._parse_ai_response(result_text, document_type)
            except Exception as e:
                raise Exception(f"OpenAI analysis failed: {str(e)}")

        raise Exception("No AI service available for document analysis")

    def analyze_document_image(
        self,
        image_path: Path,
        document_type: Optional[str] = None
    ) -> dict:
        """
        Analyze document image using Vision API with automatic fallback

        Tries Claude first, falls back to OpenAI if Claude fails.

        Args:
            image_path: Path to the image file
            document_type: Hint about document type (invoice, contract, etc.)

        Returns:
            dict: Extracted metadata including type, amounts, dates, OCR text, etc.
        """
        # Try Claude first if available
        if self.claude_client:
            try:
                logger.info("Attempting document analysis with Claude Vision API")
                return self._analyze_with_claude(image_path, document_type)
            except Exception as e:
                logger.warning(f"Claude Vision API failed: {str(e)}")
                # If OpenAI is available, try it as fallback
                if self.openai_client:
                    logger.info("Falling back to OpenAI Vision API")
                    try:
                        return self._analyze_with_openai(image_path, document_type)
                    except Exception as openai_error:
                        logger.error(f"OpenAI Vision API also failed: {str(openai_error)}")
                        raise Exception(f"Both AI services failed. Claude: {str(e)}, OpenAI: {str(openai_error)}")
                else:
                    raise Exception(f"Claude Vision API failed and no OpenAI fallback available: {str(e)}")

        # If Claude not available but OpenAI is, use OpenAI directly
        elif self.openai_client:
            logger.info("Using OpenAI Vision API (Claude not configured)")
            return self._analyze_with_openai(image_path, document_type)

        else:
            raise Exception("No AI service available for document analysis")

    def _analyze_with_claude(self, image_path: Path, document_type: Optional[str] = None) -> dict:
        """Analyze document using Claude Vision API"""
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")

        # Determine media type from file extension
        extension = image_path.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        media_type = media_type_map.get(extension, "image/jpeg")

        prompt = self._build_vision_analysis_prompt(document_type)

        response = self.claude_client.messages.create(
            model=self.claude_model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        # Extract JSON from response
        result_text = response.content[0].text
        return self._parse_ai_response(result_text, document_type)

    def _analyze_with_openai(self, image_path: Path, document_type: Optional[str] = None) -> dict:
        """Analyze document using OpenAI Vision API"""
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")

        # Determine media type from file extension
        extension = image_path.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        media_type = media_type_map.get(extension, "image/jpeg")

        prompt = self._build_vision_analysis_prompt(document_type)

        response = self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096
        )

        # Extract JSON from response
        result_text = response.choices[0].message.content
        return self._parse_ai_response(result_text, document_type)

    def _parse_ai_response(self, result_text: str, document_type: Optional[str] = None) -> dict:
        """Parse AI response and extract JSON"""
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

    def _build_vision_analysis_prompt(self, document_type: Optional[str]) -> str:
        """Build the analysis prompt for Claude Vision"""

        type_hint = f"\nHINT: This is likely a {document_type} document." if document_type else ""

        return f"""Analyze this document image and extract structured information.
{type_hint}

Extract the following information and return it as a JSON object:

{{
  "type": "invoice|reminder|contract|receipt|other",
  "title": "Short descriptive title (e.g., 'Telekom Rechnung Januar 2026')",
  "confidence": 0.0-1.0 (how confident are you in the classification),
  "extracted_text": "Full OCR text extracted from the image",
  "sender": {{
    "name": "Company/Person name",
    "address": "Full address if available",
    "email": "Email if found",
    "phone": "Phone if found"
  }},
  "recipient": {{
    "name": "Recipient name if found",
    "address": "Recipient address if found"
  }},
  "amount": number (total amount if found, e.g., 89.99),
  "currency": "EUR|USD|CHF etc.",
  "due_date": "YYYY-MM-DD format if found",
  "issue_date": "YYYY-MM-DD format if found",
  "invoice_number": "Invoice/reference number if found",
  "iban": "IBAN if found",
  "payment_reference": "Payment reference/purpose if found",
  "description": "Brief summary of what this document is about",
  "action_required": true|false (does this require user action?),
  "priority": "low|medium|high|critical",
  "suggested_task": {{
    "title": "Suggested task title (e.g., 'Telekom Rechnung bezahlen')",
    "description": "Task description with details",
    "due_date": "YYYY-MM-DD (deadline for action, if applicable)"
  }},
  "ocr_quality": "high|medium|low (assessment of text readability)"
}}

IMPORTANT:
- Return ONLY valid JSON, no additional text
- Use null for missing values
- Be accurate with amounts and dates
- Extract ALL visible text in the extracted_text field
- German documents are common, extract accordingly
- For priority: critical if overdue/Mahnung, high if due soon, medium for invoices, low for receipts
- Look for payment details (IBAN, reference) carefully
"""

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
