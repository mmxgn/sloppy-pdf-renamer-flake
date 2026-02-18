"""Command-line interface for PDF renaming tool."""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from sloppy_pdf_renamer.renamer import rename_pdf

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


# ---------------------------------------------------------------------------
# GNOME / zenity helpers
# ---------------------------------------------------------------------------


def _pick_file_zenity() -> Optional[str]:
    """Open a GTK file-chooser via zenity. Returns the chosen path or None."""
    try:
        result = subprocess.run(
            [
                "zenity",
                "--file-selection",
                "--title=Sloppy PDF Renamer — select a PDF",
                "--file-filter=PDF files (*.pdf) | *.pdf",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except FileNotFoundError:
        pass
    return None


def _show_result_zenity(message: str, *, error: bool = False) -> None:
    """Show a zenity info/error dialog with the rename result."""
    dialog_type = "--error" if error else "--info"
    try:
        subprocess.run(
            [
                "zenity",
                dialog_type,
                "--title=Sloppy PDF Renamer",
                f"--text={message}",
                "--width=400",
            ],
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _running_in_gui() -> bool:
    """True when stdout is not a TTY (launched from a file manager, not a terminal)."""
    return not sys.stdout.isatty()


# ---------------------------------------------------------------------------
# Processing helpers
# ---------------------------------------------------------------------------


def find_pdfs(path: Path, recursive: bool = False) -> List[Path]:
    """Find all PDF files in a directory."""
    if recursive:
        return sorted(path.rglob("*.pdf"))
    return sorted(path.glob("*.pdf"))


def process_file(pdf_path: Path, dry_run: bool) -> Tuple[bool, str]:
    """Process a single PDF file."""
    return rename_pdf(str(pdf_path), dry_run=dry_run)


def process_directory(
    dir_path: Path, dry_run: bool, recursive: bool
) -> Tuple[int, int, int]:
    """Process all PDF files in a directory. Returns (renamed, skipped, errors)."""
    pdfs = find_pdfs(dir_path, recursive)

    if not pdfs:
        logger.warning(f"No PDF files found in {dir_path}")
        return 0, 0, 0

    logger.info(f"Found {len(pdfs)} PDF file(s)")

    renamed = 0
    skipped = 0
    errors = 0

    for pdf_path in pdfs:
        success, message = process_file(pdf_path, dry_run)

        if success:
            logger.info(message)
            renamed += 1
        else:
            if "already has the correct name" in message.lower():
                logger.debug(message)
                skipped += 1
            else:
                logger.warning(message)
                errors += 1

    return renamed, skipped, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Rename PDF files based on their titles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sloppy-pdf-renamer document.pdf
  sloppy-pdf-renamer ~/Documents/papers --dry-run
  sloppy-pdf-renamer ~/Downloads --recursive
  sloppy-pdf-renamer . -r --verbose
  sloppy-pdf-renamer           # opens a file-chooser dialog
        """,
    )

    parser.add_argument(
        "path",
        nargs="?",
        type=str,
        default=None,
        help="PDF file or directory to process. Opens a file-chooser when omitted.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without actually renaming files",
    )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process subdirectories recursively",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed logging output",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    gui = _running_in_gui()

    # No path supplied — open GTK file chooser (GNOME "Open With" or bare launch)
    if args.path is None:
        chosen = _pick_file_zenity()
        if not chosen:
            if gui:
                _show_result_zenity("No file selected.", error=True)
            else:
                parser.print_help()
            return 1
        args.path = chosen

    path = Path(args.path).resolve()

    if not path.exists():
        msg = f"Path not found: {args.path}"
        logger.error(msg)
        if gui:
            _show_result_zenity(msg, error=True)
        return 1

    if path.is_file():
        success, message = process_file(path, args.dry_run)
        if success:
            logger.info(message)
        else:
            logger.error(message)
        if gui:
            _show_result_zenity(message, error=not success)
        return 0 if success else 1

    if path.is_dir():
        renamed, skipped, errors = process_directory(path, args.dry_run, args.recursive)
        mode = "Would rename" if args.dry_run else "Renamed"
        summary = f"{mode} {renamed}, Skipped {skipped}, Errors {errors}"
        logger.info(f"\nSummary: {summary}")
        if gui:
            _show_result_zenity(summary, error=(errors > 0 and renamed == 0))
        return 0 if renamed > 0 else 1

    msg = f"Invalid path: {args.path}"
    logger.error(msg)
    if gui:
        _show_result_zenity(msg, error=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
