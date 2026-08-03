"""OCR fallback parser — extracts text from scanned documents.

This module handles OCR for scanned PDFs and image-based documents
using Tesseract as fallback when text extraction fails.

Responsibilities:
    - Converting PDF pages to images
    - Running Tesseract OCR
    - Extracting text from scanned documents

NOT responsible for:
    - Text-based PDF parsing (belongs to PDF parser)
    - DOCX parsing (belongs to DOCX parser)
    - Text analysis (belongs to extractor)

Note:
    Requires Tesseract OCR installed on the system:
    - Windows: Install from https://github.com/UB-Mannheim/tesseract/wiki
    - Linux: sudo apt install tesseract-ocr
    - macOS: brew install tesseract
"""

import time

import pymupdf
import pytesseract
from PIL import Image

from backend.schemas.parsed import ParsedPage, ParsedResume
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class OCRParser:
    """Parse scanned documents using OCR."""

    def parse(self, file_path: str, filename: str) -> ParsedResume:
        """Parse a scanned document using OCR.

        Args:
            file_path: Path to the PDF/image file.
            filename: Original filename for metadata.

        Returns:
            ParsedResume with OCR-extracted content.
        """
        start = time.time()
        logger.info("Starting OCR parse: %s", filename)

        pages = []
        full_text_parts = []

        doc = pymupdf.open(file_path)
        for i in range(len(doc)):
            page = doc[i]
            page_num = i + 1

            # Convert page to image
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            # Run OCR
            text = pytesseract.image_to_string(img)
            full_text_parts.append(text)

            parsed_page = ParsedPage(
                page_number=page_num,
                text=text,
                width=float(page.rect.width),
                height=float(page.rect.height),
            )
            pages.append(parsed_page)

        doc.close()

        result = ParsedResume(
            filename=filename,
            total_pages=len(pages),
            pages=pages,
            full_text="\n".join(full_text_parts),
            parser_used="tesseract-ocr",
            parsing_time_ms=(time.time() - start) * 1000,
        )

        logger.info(
            "OCR parsed: %s (%d pages, %.1fms)",
            filename,
            result.total_pages,
            result.parsing_time_ms,
        )
        return result
