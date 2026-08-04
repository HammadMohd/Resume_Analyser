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

        # Build hyperlink relationship map (rId -> URL)
        hyperlink_map = {}
        try:
            from docx.opc.constants import RELATIONSHIP_TYPE as RT

            for rel in doc.part.rels.values():
                if rel.reltype == RT.HYPERLINK:
                    hyperlink_map[rel.rId] = rel.target_ref
        except Exception:
            pass

        for para in doc.paragraphs:
            if not para.text.strip():
                continue

            style_name = para.style.name if para.style is not None else ""
            is_header = style_name.startswith("Heading")
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
                bbox=None,
                font_name=font_name,
                font_size=font_size,
                is_bold=is_bold,
                is_header=is_header,
            )
            text_blocks.append(block)
            full_text_parts.append(para.text)

            # Extract hyperlink URLs from runs
            for run in para.runs:
                for child in run._element:
                    if child.tag.endswith("}hyperlink"):
                        rel_id = child.get(
                            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id",
                            "",
                        )
                        if rel_id and rel_id in hyperlink_map:
                            url = hyperlink_map[rel_id]
                            if url.startswith("http"):
                                full_text_parts.append(url)

        parsed_page = ParsedPage(
            page_number=1,
            text="\n".join(full_text_parts),
            text_blocks=text_blocks,
            width=None,
            height=None,
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
