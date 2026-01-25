"""
OCR Service using Tesseract
"""

import pytesseract
from PIL import Image
from pathlib import Path
from typing import Optional


class OCRService:
    """Service for extracting text from images using Tesseract OCR"""

    def __init__(self):
        # Configure Tesseract (assumes it's installed in the system)
        # For German language support
        self.languages = 'deu+eng'

    def extract_text(self, image_path: Path) -> tuple[str, float]:
        """
        Extract text from an image file

        Args:
            image_path: Path to the image file

        Returns:
            tuple: (extracted_text, confidence_score)
        """
        try:
            # Open image
            image = Image.open(image_path)

            # Get detailed OCR data for confidence
            data = pytesseract.image_to_data(
                image,
                lang=self.languages,
                output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=self.languages
            )

            # Calculate average confidence (excluding -1 values)
            confidences = [
                float(conf) for conf in data['conf']
                if conf != -1
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return text.strip(), avg_confidence / 100.0  # Normalize to 0-1

        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")

    def extract_from_pdf(self, pdf_path: Path) -> tuple[str, float]:
        """
        Extract text from PDF (first page only for now)

        Args:
            pdf_path: Path to the PDF file

        Returns:
            tuple: (extracted_text, confidence_score)
        """
        try:
            from pdf2image import convert_from_path

            # Convert first page to image
            images = convert_from_path(pdf_path, first_page=1, last_page=1)

            if not images:
                return "", 0.0

            # OCR the first page
            return self.extract_text_from_pil_image(images[0])

        except ImportError:
            raise Exception("pdf2image not installed. Install: pip install pdf2image")
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")

    def extract_text_from_pil_image(self, image: Image) -> tuple[str, float]:
        """
        Extract text from PIL Image object

        Args:
            image: PIL Image object

        Returns:
            tuple: (extracted_text, confidence_score)
        """
        try:
            # Get detailed OCR data for confidence
            data = pytesseract.image_to_data(
                image,
                lang=self.languages,
                output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=self.languages
            )

            # Calculate average confidence
            confidences = [
                float(conf) for conf in data['conf']
                if conf != -1
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return text.strip(), avg_confidence / 100.0

        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
