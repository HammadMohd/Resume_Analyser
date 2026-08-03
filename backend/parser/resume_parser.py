"""Parser module — coordinates parsing of different file formats.

This module provides a unified interface for parsing resumes.
It automatically selects the appropriate parser based on file type.

Responsibilities:
    - Routing to correct parser (PDF, DOCX, OCR)
    - Handling parser failures with fallbacks
    - Providing unified parsing interface

Usage:
    parser = ResumeParser()
    result = parser.parse("resume.pdf", "resume.pdf")
"""

from pathlib import Path

from backend.parser.docx_parser import DOCXParser
from backend.parser.ocr_parser import OCRParser
from backend.parser.pdf_parser import PDFParser
from backend.schemas.parsed import ParsedResume
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ParseError(Exception):
    """Raised when parsing fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ResumeParser:
    """Parse resumes of different formats."""

    def __init__(self) -> None:
        self.pdf_parser = PDFParser()
        self.docx_parser = DOCXParser()
        self.ocr_parser = OCRParser()

    def parse(self, file_path: str, filename: str) -> ParsedResume:
        """Parse a resume file and return structured content.

        Automatically selects parser based on file extension:
        - .pdf → PDFPlumber (fallback: PyMuPDF, then OCR)
        - .docx → python-docx

        Args:
            file_path: Path to the resume file.
            filename: Original filename.

        Returns:
            ParsedResume with extracted content.

        Raises:
            ParseError: If parsing fails for all methods.
        """
        ext = Path(filename).suffix.lower()
        logger.info("Parsing resume: %s (type: %s)", filename, ext)

        if ext == ".pdf":
            return self._parse_pdf(file_path, filename)
        elif ext == ".docx":
            return self._parse_docx(file_path, filename)
        else:
            raise ParseError(f"Unsupported file type: {ext}")

    def _parse_pdf(self, file_path: str, filename: str) -> ParsedResume:
        """Parse PDF with fallback chain."""
        try:
            result = self.pdf_parser.parse(file_path, filename)
            if result.full_text.strip():
                return result
            logger.warning("PDFPlumber extracted no text, trying OCR")
        except Exception as e:
            logger.warning("PDFPlumber failed: %s", e)

        # Fallback to OCR
        try:
            return self.ocr_parser.parse(file_path, filename)
        except Exception as e:
            raise ParseError(f"All PDF parsing methods failed: {e}") from e

    def _parse_docx(self, file_path: str, filename: str) -> ParsedResume:
        """Parse DOCX file."""
        try:
            return self.docx_parser.parse(file_path, filename)
        except Exception as e:
            raise ParseError(f"DOCX parsing failed: {e}") from e
