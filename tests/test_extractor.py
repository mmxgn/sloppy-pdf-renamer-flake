"""Tests for PDF title extraction."""

from pathlib import Path
from unittest.mock import Mock, patch

from pypdf import PdfWriter

from sloppy_pdf_renamer.extractor import (
    _extract_from_content,
    _extract_from_metadata,
    extract_title,
)


class TestExtractFromMetadata:
    """Test metadata extraction."""

    def test_extract_title_from_metadata(self, tmp_path):
        """Test extracting title from PDF metadata."""
        # Create a PDF with metadata
        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        writer.add_metadata({"/Title": "Test Document Title"})

        with open(pdf_path, "wb") as f:
            writer.write(f)

        title = _extract_from_metadata(pdf_path)
        assert title == "Test Document Title"

    def test_extract_empty_metadata(self, tmp_path):
        """Test extraction when metadata title is empty."""
        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        writer.add_metadata({"/Title": ""})

        with open(pdf_path, "wb") as f:
            writer.write(f)

        title = _extract_from_metadata(pdf_path)
        assert title is None

    def test_extract_no_metadata(self, tmp_path):
        """Test extraction when no metadata exists."""
        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)

        with open(pdf_path, "wb") as f:
            writer.write(f)

        title = _extract_from_metadata(pdf_path)
        assert title is None

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        title = _extract_from_metadata(Path("/nonexistent/file.pdf"))
        assert title is None

    def test_permission_error(self, tmp_path):
        """Test handling of permission errors."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        pdf_path.chmod(0o000)

        try:
            title = _extract_from_metadata(pdf_path)
            assert title is None
        finally:
            pdf_path.chmod(0o644)

    def test_whitespace_trimming(self, tmp_path):
        """Test that whitespace is trimmed from metadata title."""
        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        writer.add_metadata({"/Title": "  Whitespace Title  "})

        with open(pdf_path, "wb") as f:
            writer.write(f)

        title = _extract_from_metadata(pdf_path)
        assert title == "Whitespace Title"


class TestExtractFromContent:
    """Test content extraction."""

    @patch('pdfplumber.open')
    def test_extract_first_line(self, mock_open, tmp_path):
        """Test extracting title from first line of content."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        # Mock pdfplumber
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Document Title\nSome content here\nMore text"
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_open.return_value = mock_pdf

        title = _extract_from_content(pdf_path)
        assert title == "Document Title"

    @patch('pdfplumber.open')
    def test_extract_with_empty_lines(self, mock_open, tmp_path):
        """Test extracting title when there are empty lines."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "\n\nActual Title\nContent"
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_open.return_value = mock_pdf

        title = _extract_from_content(pdf_path)
        assert title == "Actual Title"

    @patch('pdfplumber.open')
    def test_skip_short_first_line(self, mock_open, tmp_path):
        """Test skipping very short first line (likely page number)."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "1\nReal Title\nContent"
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_open.return_value = mock_pdf

        title = _extract_from_content(pdf_path)
        assert title == "Real Title"

    @patch('pdfplumber.open')
    def test_no_text_content(self, mock_open, tmp_path):
        """Test handling of PDF with no text."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_open.return_value = mock_pdf

        title = _extract_from_content(pdf_path)
        assert title is None

    @patch('pdfplumber.open')
    def test_no_pages(self, mock_open, tmp_path):
        """Test handling of PDF with no pages."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        mock_pdf = Mock()
        mock_pdf.pages = []
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_open.return_value = mock_pdf

        title = _extract_from_content(pdf_path)
        assert title is None

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        title = _extract_from_content(Path("/nonexistent/file.pdf"))
        assert title is None


class TestExtractTitle:
    """Test main extract_title function."""

    def test_metadata_takes_precedence(self, tmp_path):
        """Test that metadata is tried before content."""
        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        writer.add_metadata({"/Title": "Metadata Title"})

        with open(pdf_path, "wb") as f:
            writer.write(f)

        title = extract_title(str(pdf_path))
        assert title == "Metadata Title"

    @patch('sloppy_pdf_renamer.extractor._extract_from_content')
    def test_fallback_to_content(self, mock_content, tmp_path):
        """Test fallback to content when metadata is missing."""
        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)

        with open(pdf_path, "wb") as f:
            writer.write(f)

        mock_content.return_value = "Content Title"

        title = extract_title(str(pdf_path))
        assert title == "Content Title"

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        title = extract_title("/nonexistent/file.pdf")
        assert title is None

    def test_not_a_file(self, tmp_path):
        """Test handling of directory path."""
        title = extract_title(str(tmp_path))
        assert title is None
