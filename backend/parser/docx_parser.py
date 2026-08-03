"""DOCX parser — extracts text from Word documents.

This module handles DOCX parsing using python-docx.

Responsibilities:
    - Extracting text from DOCX paragraphs
    - Detecting headers and bold text
    - Preserving paragraph structure

NOT responsible for:
    - PDF parsing (belongs to PDF parser)
    - OCR (belongs to OCR fallback)
    - Text analysis (belongs to extractor)
"""

import time

from docx import Document

from backend.schemas.parsed import ParsedPage, ParsedResume, TextBlock
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class DOCXParser:
    """Parse DOCX files and extract text content."""

    def parse(self, file_path: str, filename: str) -> ParsedResume:
        """Parse a DOCX file and return structured content.

        Args:
            file_path: Path to the DOCX file.
            filename: Original filename for metadata.

        Returns:
            ParsedResume with extracted content.
        """
        start = time.time()
        logger.info("Starting DOCX parse: %s", filename)

        doc = Document(file_path)
        text_blocks = []
        full_text_parts = []

        for para in doc.paragraphs:
            if not para.text.strip():
                continue

            is_header = para.style.name.startswith("Heading")
            is_bold = any(run.bold for run in para.runs if run.bold is not None)
            font_name = None
            font_size = None

            if para.runs:
                first_run = para.runs[0]
                if first_run.font.name:
                    font_name = first_run.font.name
                if first_run.font.size:
                    font_size = first_run.font.size.pt

            block = TextBlock(
                text=para.text,
                page=1,  # DOCX doesn't have page numbers
                font_name=font_name,
                font_size=font_size,
                is_bold=is_bold,
                is_header=is_header,
            )
            text_blocks.append(block)
            full_text_parts.append(para.text)

        parsed_page = ParsedPage(
            page_number=1,
            text="\n".join(full_text_parts),
            text_blocks=text_blocks,
        )

        result = ParsedResume(
            filename=filename,
            total_pages=1,
            pages=[parsed_page],
            full_text="\n".join(full_text_parts),
            parser_used="python-docx",
            parsing_time_ms=(time.time() - start) * 1000,
        )

        logger.info(
            "DOCX parsed: %s (%d blocks, %.1fms)",
            filename,
            len(text_blocks),
            result.parsing_time_ms,
        )
        return result
