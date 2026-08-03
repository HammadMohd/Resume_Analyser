"""Parser schemas — Pydantic models for parsed resume data.

This module defines the data structures for parsed resume content.
These schemas represent the normalized output from all parsers.

Responsibilities:
    - Defining parsed text structure
    - Defining coordinate/bounding box data
    - Defining layout elements
"""

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box for a text element on the page."""

    x0: float = Field(..., description="Left x coordinate")
    y0: float = Field(..., description="Top y coordinate")
    x1: float = Field(..., description="Right x coordinate")
    y1: float = Field(..., description="Bottom y coordinate")

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


class TextBlock(BaseModel):
    """A block of text with its position on the page."""

    text: str = Field(..., description="Text content")
    page: int = Field(..., description="Page number (1-indexed)")
    bbox: BoundingBox | None = Field(None, description="Bounding box coordinates")
    font_name: str | None = Field(None, description="Font name")
    font_size: float | None = Field(None, description="Font size in points")
    is_bold: bool = Field(False, description="Whether text is bold")
    is_header: bool = Field(False, description="Whether this is a header element")


class ParsedPage(BaseModel):
    """Parsed content from a single page."""

    page_number: int = Field(..., description="Page number (1-indexed)")
    text: str = Field(..., description="Full page text")
    text_blocks: list[TextBlock] = Field(default_factory=list, description="Individual text blocks")
    width: float | None = Field(None, description="Page width in points")
    height: float | None = Field(None, description="Page height in points")


class ParsedResume(BaseModel):
    """Fully parsed resume with all pages and metadata."""

    filename: str = Field(..., description="Original filename")
    total_pages: int = Field(..., description="Number of pages")
    pages: list[ParsedPage] = Field(default_factory=list, description="Parsed pages")
    full_text: str = Field("", description="Complete text from all pages")
    parser_used: str = Field(..., description="Which parser was used")
    parsing_time_ms: float = Field(0, description="Time taken to parse in milliseconds")
