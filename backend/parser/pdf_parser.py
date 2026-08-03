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
                for word in words:
                    block = TextBlock(
                        text=word["text"],
                        page=page_num,
                        bbox=BoundingBox(
                            x0=word["x0"],
                            y0=word["top"],
                            x1=word["x1"],
                            y1=word["bottom"],
                        ),
                        font_name=word.get("fontname"),
                        font_size=self._estimate_font_size(word),
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
        )

    def _parse_with_pymupdf(self, file_path: str, filename: str) -> ParsedResume:
        """Parse PDF using PyMuPDF as fallback."""
        pages = []
        full_text_parts = []

        doc = pymupdf.open(file_path)
        for i in range(len(doc)):
            page = doc[i]
            page_num = i + 1
            text = page.get_text()
            full_text_parts.append(text)

            text_blocks = []
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block["type"] == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            bbox = span["bbox"]
                            block_obj = TextBlock(
                                text=span["text"],
                                page=page_num,
                                bbox=BoundingBox(
                                    x0=bbox[0],
                                    y0=bbox[1],
                                    x1=bbox[2],
                                    y1=bbox[3],
                                ),
                                font_name=span.get("font"),
                                font_size=span.get("size"),
                                is_bold="Bold" in (span.get("font") or ""),
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

        doc.close()
        return ParsedResume(
            filename=filename,
            total_pages=len(pages),
            pages=pages,
            full_text="\n".join(full_text_parts),
            parser_used="pymupdf",
        )

    @staticmethod
    def _estimate_font_size(word: dict) -> float:
        """Estimate font size from word metrics."""
        height = word.get("bottom", 0) - word.get("top", 0)
        return round(height * 0.75, 1) if height > 0 else 12.0
