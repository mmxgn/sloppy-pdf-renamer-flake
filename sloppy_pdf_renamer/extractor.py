"""PDF title extraction from metadata and content."""

import logging
from pathlib import Path
from typing import Optional

import pdfplumber
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_title(pdf_path: str) -> Optional[str]:
    """
    Extract title from PDF file.

    Tries metadata first, then falls back to content parsing.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted title or None if extraction fails
    """
    path = Path(pdf_path)

    if not path.exists():
        logger.error(f"File not found: {pdf_path}")
        return None

    if not path.is_file():
        logger.error(f"Not a file: {pdf_path}")
        return None

    # Try metadata first
    title = _extract_from_metadata(path)
    if title:
        logger.info(f"Extracted title from metadata: {title}")
        return title

    # Fallback to content parsing
    title = _extract_from_content(path)
    if title:
        logger.info(f"Extracted title from content: {title}")
        return title

    logger.warning(f"Could not extract title from: {pdf_path}")
    return None


def _extract_from_metadata(path: Path) -> Optional[str]:
    """
    Extract title from PDF metadata.

    Args:
        path: Path to the PDF file

    Returns:
        Title from metadata or None
    """
    try:
        reader = PdfReader(str(path))
        metadata = reader.metadata

        if metadata and metadata.title:
            title = metadata.title.strip()
            if title:
                return title

    except FileNotFoundError:
        logger.error(f"File not found: {path}")
    except PermissionError:
        logger.error(f"Permission denied: {path}")
    except Exception as e:
        logger.debug(f"Failed to extract metadata from {path}: {e}")

    return None


def _extract_from_content(path: Path) -> Optional[str]:
    """
    Extract title from PDF content using heuristics.

    Looks for title in the first page, typically the first non-empty line
    or text before the first paragraph break.

    Args:
        path: Path to the PDF file

    Returns:
        Best title candidate from content or None
    """
    try:
        with pdfplumber.open(str(path)) as pdf:
            if not pdf.pages:
                return None

            # Get text from first page
            first_page = pdf.pages[0]
            text = first_page.extract_text()

            if not text:
                return None

            # Split into lines and find first non-empty line
            lines = [line.strip() for line in text.split('\n')]
            non_empty_lines = [line for line in lines if line]

            if not non_empty_lines:
                return None

            # Use first non-empty line as title
            # This is a simple heuristic that works for most PDFs
            title = non_empty_lines[0]

            # If the first line is very short (< 3 chars), it might be a page number
            # Try the second line instead
            if len(title) < 3 and len(non_empty_lines) > 1:
                title = non_empty_lines[1]

            return title

    except FileNotFoundError:
        logger.error(f"File not found: {path}")
    except PermissionError:
        logger.error(f"Permission denied: {path}")
    except Exception as e:
        logger.debug(f"Failed to extract content from {path}: {e}")

    return None
