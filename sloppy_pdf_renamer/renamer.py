"""PDF file renaming with filename sanitization."""

import logging
import os
import re
from pathlib import Path
from typing import Tuple

from sloppy_pdf_renamer.extractor import extract_title

logger = logging.getLogger(__name__)

# Characters that are invalid in filenames on most systems
INVALID_CHARS = r'[/\\:*?"<>|]'


def sanitize_filename(title: str) -> str:
    """
    Sanitize a title for use as a filename.

    Removes invalid characters, normalizes whitespace, and limits length.

    Args:
        title: The title to sanitize

    Returns:
        Sanitized filename (without extension)
    """
    # Replace invalid characters with hyphens
    sanitized = re.sub(INVALID_CHARS, '-', title)

    # Normalize whitespace: collapse multiple spaces into one
    sanitized = ' '.join(sanitized.split())

    # Limit to 200 characters, break at word boundary
    if len(sanitized) > 200:
        sanitized = sanitized[:200].rsplit(' ', 1)[0]

    # Strip leading/trailing spaces, dots, and hyphens
    sanitized = sanitized.strip(' .-')

    return sanitized


def rename_pdf(pdf_path: str, dry_run: bool = False) -> Tuple[bool, str]:
    """
    Rename a PDF file based on its title.

    Args:
        pdf_path: Path to the PDF file to rename
        dry_run: If True, only preview the change without actually renaming

    Returns:
        Tuple of (success: bool, message: str)
    """
    path = Path(pdf_path)

    if not path.exists():
        return False, f"File not found: {pdf_path}"

    if not path.is_file():
        return False, f"Not a file: {pdf_path}"

    if path.suffix.lower() != '.pdf':
        return False, f"Not a PDF file: {pdf_path}"

    # Extract title
    title = extract_title(str(path))
    if not title:
        return False, "No title found"

    # Sanitize title for use as filename
    sanitized_title = sanitize_filename(title)
    if not sanitized_title:
        return False, "Title could not be sanitized to valid filename"

    # Construct new path
    new_filename = f"{sanitized_title}.pdf"
    new_path = path.parent / new_filename

    # Check if already has the correct name
    if path == new_path:
        return False, "File already has the correct name"

    # Handle duplicates by appending (1), (2), etc.
    if new_path.exists():
        counter = 1
        while new_path.exists():
            new_filename = f"{sanitized_title} ({counter}).pdf"
            new_path = path.parent / new_filename
            counter += 1

    # Preview or rename
    if dry_run:
        return True, f"Would rename: {path.name} -> {new_path.name}"

    try:
        os.rename(str(path), str(new_path))
        return True, f"Renamed: {path.name} -> {new_path.name}"
    except PermissionError:
        return False, f"Permission denied: {pdf_path}"
    except Exception as e:
        return False, f"Failed to rename: {e}"
