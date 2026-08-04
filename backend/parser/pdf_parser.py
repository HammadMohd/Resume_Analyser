"""PDF parser — extracts text and coordinates from PDF files.

This module handles PDF parsing using PDFPlumber as primary
and PyMuPDF as fallback.

Responsibilities:
    - Extracting text from PDF pages
    - Extracting text blocks with coordinates
    - Detecting fonts and font sizes
    - Falling back to PyMuPDF if PDFPlumber fails

NOT responsible for:
    - OCR (belongs to OCR fallback)
    - Text analysis (belongs to extractor)
    - Layout reconstruction (belongs to layout module)
"""

import statistics
import time

import pdfplumber
import pymupdf

from backend.schemas.parsed import BoundingBox, ParsedPage, ParsedResume, TextBlock
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class PDFParser:
    """Parse PDF files and extract text with coordinates."""

    def parse(self, file_path: str, filename: str) -> ParsedResume:
        """Parse a PDF file and return structured content.

        Args:
            file_path: Path to the PDF file.
            filename: Original filename for metadata.

        Returns:
            ParsedResume with extracted content.
        """
        start = time.time()
        logger.info("Starting PDF parse: %s", filename)

        try:
            result = self._parse_with_pdfplumber(file_path, filename)
        except Exception as e:
            logger.warning("PDFPlumber failed, trying PyMuPDF: %s", e)
            result = self._parse_with_pymupdf(file_path, filename)

        result.parsing_time_ms = (time.time() - start) * 1000
        logger.info(
            "PDF parsed: %s (%d pages, %.1fms)",
            filename,
            result.total_pages,
            result.parsing_time_ms,
        )
        return result

    def _parse_with_pdfplumber(self, file_path: str, filename: str) -> ParsedResume:
        """Parse PDF using PDFPlumber."""
        pages = []
        full_text_parts = []

        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                text = page.extract_text() or ""
                full_text_parts.append(text)

                text_blocks = []
                words = page.extract_words()

                # Collect font sizes for header detection
                font_sizes = []
                for word in words:
                    height = word.get("bottom", 0) - word.get("top", 0)
                    if height > 0:
                        font_sizes.append(round(height * 0.75, 1))

                median_size = (
                    statistics.median(font_sizes) if font_sizes else 12.0
                )
                header_threshold = median_size * 1.3

                for word in words:
                    height = word.get("bottom", 0) - word.get("top", 0)
                    font_size = round(height * 0.75, 1) if height > 0 else 12.0
                    font_name = word.get("fontname", "")
                    is_bold = self._detect_bold_plumber(font_name)
                    is_header = font_size >= header_threshold and font_size > 0

                    block = TextBlock(
                        text=word["text"],
                        page=page_num,
                        bbox=BoundingBox(
                            x0=word["x0"],
                            y0=word["top"],
                            x1=word["x1"],
                            y1=word["bottom"],
                        ),
                        font_name=font_name,
                        font_size=font_size,
                        is_bold=is_bold,
                        is_header=is_header,
                    )
                    text_blocks.append(block)

                parsed_page = ParsedPage(
                    page_number=page_num,
                    text=text,
                    text_blocks=text_blocks,
                    width=float(page.width),
                    height=float(page.height),
                )
                pages.append(parsed_page)

        return ParsedResume(
            filename=filename,
            total_pages=len(pages),
            pages=pages,
            full_text="\n".join(full_text_parts),
            parser_used="pdfplumber",
            parsing_time_ms=0,
        )

    def _parse_with_pymupdf(self, file_path: str, filename: str) -> ParsedResume:
        """Parse PDF using PyMuPDF as fallback."""
        pages = []
        full_text_parts = []

        doc = pymupdf.open(file_path)
        try:
            for i in range(len(doc)):
                page = doc[i]
                page_num = i + 1
                text = page.get_text()
                full_text_parts.append(text)

                text_blocks = []
                blocks = page.get_text("dict")["blocks"]

                # Collect font sizes for header detection
                font_sizes = []
                for block in blocks:
                    if block["type"] == 0:
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                sz = span.get("size", 0)
                                if sz > 0:
                                    font_sizes.append(sz)

                median_size = (
                    statistics.median(font_sizes) if font_sizes else 12.0
                )
                header_threshold = median_size * 1.3

                for block in blocks:
                    if block["type"] == 0:  # Text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                bbox = span["bbox"]
                                font_name = span.get("font", "")
                                font_size = span.get("size", 0)
                                is_bold = "Bold" in font_name
                                is_header = (
                                    font_size >= header_threshold and font_size > 0
                                )

                                block_obj = TextBlock(
                                    text=span["text"],
                                    page=page_num,
                                    bbox=BoundingBox(
                                        x0=bbox[0],
                                        y0=bbox[1],
                                        x1=bbox[2],
                                        y1=bbox[3],
                                    ),
                                    font_name=font_name,
                                    font_size=font_size,
                                    is_bold=is_bold,
                                    is_header=is_header,
                                )
                                text_blocks.append(block_obj)

                parsed_page = ParsedPage(
                    page_number=page_num,
                    text=text,
                    text_blocks=text_blocks,
                    width=float(page.rect.width),
                    height=float(page.rect.height),
                )
                pages.append(parsed_page)
        finally:
            doc.close()

        return ParsedResume(
            filename=filename,
            total_pages=len(pages),
            pages=pages,
            full_text="\n".join(full_text_parts),
            parser_used="pymupdf",
            parsing_time_ms=0,
        )

    @staticmethod
    def _detect_bold_plumber(font_name: str) -> bool:
        """Detect bold from PDFPlumber font name."""
        if not font_name:
            return False
        lower = font_name.lower()
        return any(tag in lower for tag in ("bold", "bd", "heavy", "black"))

    @staticmethod
    def _estimate_font_size(word: dict) -> float:
        """Estimate font size from word metrics."""
        height = word.get("bottom", 0) - word.get("top", 0)
        return round(height * 0.75, 1) if height > 0 else 12.0
