"""Tests for PDF renaming and filename sanitization."""

from unittest.mock import patch

from sloppy_pdf_renamer.renamer import rename_pdf, sanitize_filename


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_remove_invalid_characters(self):
        """Test removal of invalid filename characters."""
        assert sanitize_filename("Title/With\\Invalid:Chars") == "Title-With-Invalid-Chars"
        assert sanitize_filename('Title*With?"Bad<Chars>|') == "Title-With--Bad-Chars-"

    def test_normalize_whitespace(self):
        """Test collapsing multiple spaces into one."""
        assert sanitize_filename("Title   with    spaces") == "Title with spaces"
        assert sanitize_filename("Title\t\twith\ttabs") == "Title with tabs"

    def test_length_limit(self):
        """Test limiting filename length to 200 characters."""
        long_title = "A" * 300
        result = sanitize_filename(long_title)
        assert len(result) <= 200

    def test_length_limit_word_boundary(self):
        """Test that length limiting breaks at word boundary."""
        long_title = "Word " * 50  # 250 characters
        result = sanitize_filename(long_title)
        assert len(result) <= 200
        assert not result.endswith(" ")  # Should not end with space

    def test_strip_leading_trailing(self):
        """Test stripping leading/trailing spaces, dots, hyphens."""
        assert sanitize_filename("  Title  ") == "Title"
        assert sanitize_filename("..Title..") == "Title"
        assert sanitize_filename("--Title--") == "Title"
        assert sanitize_filename(" .-Title-. ") == "Title"

    def test_complex_sanitization(self):
        """Test complex title with multiple issues."""
        title = "  Invalid/Char*Title:  With   Spaces...  "
        result = sanitize_filename(title)
        assert result == "Invalid-Char-Title- With Spaces"

    def test_unicode_preservation(self):
        """Test that Unicode characters are preserved."""
        assert sanitize_filename("Título en Español") == "Título en Español"
        assert sanitize_filename("文档标题") == "文档标题"
        assert sanitize_filename("Заголовок документа") == "Заголовок документа"


class TestRenamePdf:
    """Test PDF file renaming."""

    @patch('sloppy_pdf_renamer.renamer.extract_title')
    def test_successful_rename(self, mock_extract, tmp_path):
        """Test successful file renaming."""
        # Create test PDF
        pdf_path = tmp_path / "original.pdf"
        pdf_path.touch()

        mock_extract.return_value = "New Title"

        success, message = rename_pdf(str(pdf_path), dry_run=False)

        assert success is True
        assert "Renamed" in message
        assert not pdf_path.exists()
        assert (tmp_path / "New Title.pdf").exists()

    @patch('sloppy_pdf_renamer.renamer.extract_title')
    def test_dry_run_mode(self, mock_extract, tmp_path):
        """Test dry-run mode doesn't actually rename."""
        pdf_path = tmp_path / "original.pdf"
        pdf_path.touch()

        mock_extract.return_value = "New Title"

        success, message = rename_pdf(str(pdf_path), dry_run=True)

        assert success is True
        assert "Would rename" in message
        assert pdf_path.exists()  # Original still exists
        assert not (tmp_path / "New Title.pdf").exists()  # New doesn't exist

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        success, message = rename_pdf("/nonexistent/file.pdf")

        assert success is False
        assert "not found" in message.lower()

    def test_not_a_file(self, tmp_path):
        """Test handling of directory path."""
        success, message = rename_pdf(str(tmp_path))

        assert success is False
        assert "not a file" in message.lower()

    def test_not_a_pdf(self, tmp_path):
        """Test handling of non-PDF file."""
        txt_path = tmp_path / "document.txt"
        txt_path.touch()

        success, message = rename_pdf(str(txt_path))

        assert success is False
        assert "not a pdf" in message.lower()

    @patch('sloppy_pdf_renamer.renamer.extract_title')
    def test_no_title_found(self, mock_extract, tmp_path):
        """Test handling when title extraction fails."""
        pdf_path = tmp_path / "original.pdf"
        pdf_path.touch()

        mock_extract.return_value = None

        success, message = rename_pdf(str(pdf_path))

        assert success is False
        assert "no title" in message.lower()

    @patch('sloppy_pdf_renamer.renamer.extract_title')
    def test_duplicate_handling(self, mock_extract, tmp_path):
        """Test handling of duplicate filenames."""
        # Create original PDF
        pdf_path = tmp_path / "original.pdf"
        pdf_path.touch()

        # Create file with target name
        existing = tmp_path / "New Title.pdf"
        existing.touch()

        mock_extract.return_value = "New Title"

        success, message = rename_pdf(str(pdf_path), dry_run=False)

        assert success is True
        assert (tmp_path / "New Title (1).pdf").exists()

    @patch('sloppy_pdf_renamer.renamer.extract_title')
    def test_multiple_duplicates(self, mock_extract, tmp_path):
        """Test handling of multiple duplicate filenames."""
        pdf_path = tmp_path / "original.pdf"
        pdf_path.touch()

        # Create multiple files with target name
        (tmp_path / "New Title.pdf").touch()
        (tmp_path / "New Title (1).pdf").touch()
        (tmp_path / "New Title (2).pdf").touch()

        mock_extract.return_value = "New Title"

        success, message = rename_pdf(str(pdf_path), dry_run=False)

        assert success is True
        assert (tmp_path / "New Title (3).pdf").exists()

    @patch('sloppy_pdf_renamer.renamer.extract_title')
    def test_already_correct_name(self, mock_extract, tmp_path):
        """Test when file already has the correct name."""
        pdf_path = tmp_path / "Correct Title.pdf"
        pdf_path.touch()

        mock_extract.return_value = "Correct Title"

        success, message = rename_pdf(str(pdf_path))

        assert success is False
        assert "already has the correct name" in message.lower()

    @patch('sloppy_pdf_renamer.renamer.extract_title')
    def test_sanitized_title_empty(self, mock_extract, tmp_path):
        """Test handling when sanitized title is empty."""
        pdf_path = tmp_path / "original.pdf"
        pdf_path.touch()

        # Title with only invalid characters
        mock_extract.return_value = "///***???"

        success, message = rename_pdf(str(pdf_path))

        assert success is False
        assert "could not be sanitized" in message.lower()

    @patch('sloppy_pdf_renamer.renamer.extract_title')
    def test_permission_error(self, mock_extract, tmp_path):
        """Test handling of permission errors."""
        pdf_path = tmp_path / "original.pdf"
        pdf_path.touch()

        mock_extract.return_value = "New Title"

        # Make directory read-only
        tmp_path.chmod(0o444)

        try:
            success, message = rename_pdf(str(pdf_path))

            assert success is False
            assert "permission denied" in message.lower()
        finally:
            tmp_path.chmod(0o755)

    @patch('sloppy_pdf_renamer.renamer.extract_title')
    def test_special_characters_in_title(self, mock_extract, tmp_path):
        """Test renaming with special characters in title."""
        pdf_path = tmp_path / "original.pdf"
        pdf_path.touch()

        mock_extract.return_value = "Title: With Special / Characters"

        success, message = rename_pdf(str(pdf_path), dry_run=False)

        assert success is True
        # Special chars should be sanitized
        expected = tmp_path / "Title- With Special - Characters.pdf"
        assert expected.exists()
