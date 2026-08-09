"""OCR Engine module for extracting text from scanned PDF documents and images.

Uses pytesseract with Pillow image processing if available, with graceful fallback.
"""

from pathlib import Path

from backend.utils.logging import get_logger

logger = get_logger(__name__)

try:
    import pytesseract
    from PIL import Image

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.info("pytesseract or PIL not available for OCR processing.")


class OCREngine:
    """OCR engine for image-based PDFs and PNG/JPG resumes."""

    def __init__(self) -> None:
        self.available = TESSERACT_AVAILABLE

    def extract_text_from_image(self, image_path: str | Path) -> str:
        """Extract text from an image file (PNG, JPG, TIFF)."""
        if not self.available:
            logger.warning("OCR requested but pytesseract/Pillow is not installed.")
            return ""

        try:
            image = Image.open(image_path)
            # Convert to grayscale for better OCR precision
            gray_image = image.convert("L")
            text = pytesseract.image_to_string(gray_image)
            return text.strip()
        except Exception as e:
            logger.error("OCR extraction failed for %s: %s", image_path, str(e))
            return ""

    def process_pdf_page_image(self, page_image_bytes: bytes) -> str:
        """Process raw image bytes from a PDF page."""
        if not self.available:
            return ""

        try:
            import io
            image = Image.open(io.BytesIO(page_image_bytes))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error("Failed OCR on PDF page image: %s", str(e))
            return ""
