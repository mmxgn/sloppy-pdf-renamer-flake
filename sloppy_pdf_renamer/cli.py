"""Command-line interface for PDF renaming tool."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Tuple

from sloppy_pdf_renamer.renamer import rename_pdf

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.

    Args:
        verbose: If True, show debug messages
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def find_pdfs(path: Path, recursive: bool = False) -> List[Path]:
    """
    Find all PDF files in a directory.

    Args:
        path: Directory to search
        recursive: If True, search subdirectories

    Returns:
        List of PDF file paths
    """
    if recursive:
        return sorted(path.rglob('*.pdf'))
    return sorted(path.glob('*.pdf'))


def process_file(pdf_path: Path, dry_run: bool) -> Tuple[bool, str]:
    """
    Process a single PDF file.

    Args:
        pdf_path: Path to PDF file
        dry_run: If True, preview changes without renaming

    Returns:
        Tuple of (success, message)
    """
    return rename_pdf(str(pdf_path), dry_run=dry_run)


def process_directory(dir_path: Path, dry_run: bool, recursive: bool) -> Tuple[int, int, int]:
    """
    Process all PDF files in a directory.

    Args:
        dir_path: Directory path
        dry_run: If True, preview changes without renaming
        recursive: If True, process subdirectories

    Returns:
        Tuple of (renamed_count, skipped_count, error_count)
    """
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


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    parser = argparse.ArgumentParser(
        description='Rename PDF files based on their titles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sloppy-pdf-renamer document.pdf
  sloppy-pdf-renamer ~/Documents/papers --dry-run
  sloppy-pdf-renamer ~/Downloads --recursive
  sloppy-pdf-renamer . -r --verbose
        """
    )

    parser.add_argument(
        'path',
        type=str,
        help='PDF file or directory to process'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without actually renaming files'
    )

    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Process subdirectories recursively'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed logging output'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    path = Path(args.path).resolve()

    if not path.exists():
        logger.error(f"Path not found: {args.path}")
        return 1

    if path.is_file():
        # Process single file
        success, message = process_file(path, args.dry_run)
        if success:
            logger.info(message)
            return 0
        else:
            logger.error(message)
            return 1

    elif path.is_dir():
        # Process directory
        renamed, skipped, errors = process_directory(path, args.dry_run, args.recursive)

        # Print summary
        mode = "Would rename" if args.dry_run else "Renamed"
        logger.info(f"\nSummary: {mode} {renamed}, Skipped {skipped}, Errors {errors}")

        # Return 0 if any files were successfully renamed, 1 if all failed
        return 0 if renamed > 0 else 1

    else:
        logger.error(f"Invalid path: {args.path}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
