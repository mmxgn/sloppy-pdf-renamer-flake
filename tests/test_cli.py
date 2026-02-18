"""Tests for CLI GNOME integration (file chooser, GUI detection, dialogs)."""

import subprocess
from unittest.mock import MagicMock, patch

from sloppy_pdf_renamer.cli import (
    _pick_file_zenity,
    _running_in_gui,
    _show_result_zenity,
    main,
)


class TestPickFileZenity:
    """Test the zenity file-chooser helper."""

    def test_returns_chosen_path(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="/tmp/my.pdf\n")
            result = _pick_file_zenity()
        assert result == "/tmp/my.pdf"

    def test_returns_none_on_cancel(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            result = _pick_file_zenity()
        assert result is None

    def test_returns_none_when_zenity_missing(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _pick_file_zenity()
        assert result is None

    def test_returns_none_for_empty_stdout(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="   ")
            result = _pick_file_zenity()
        assert result is None


class TestRunningInGui:
    """Test GUI detection via TTY check."""

    def test_not_gui_when_tty(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            assert _running_in_gui() is False

    def test_gui_when_no_tty(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            assert _running_in_gui() is True


class TestShowResultZenity:
    """Test the result dialog helper."""

    def test_shows_info_dialog(self):
        with patch("subprocess.run") as mock_run:
            _show_result_zenity("All done!")
        args = mock_run.call_args[0][0]
        assert "--info" in args
        assert "--text=All done!" in args

    def test_shows_error_dialog(self):
        with patch("subprocess.run") as mock_run:
            _show_result_zenity("Something went wrong", error=True)
        args = mock_run.call_args[0][0]
        assert "--error" in args

    def test_silent_when_zenity_missing(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            _show_result_zenity("message")  # Must not raise

    def test_silent_on_timeout(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("zenity", 60)):
            _show_result_zenity("message")  # Must not raise


class TestMainGnomeIntegration:
    """Test CLI main() with GNOME-specific paths."""

    def test_opens_file_chooser_when_no_path(self, tmp_path):
        pdf = tmp_path / "original.pdf"
        pdf.touch()

        with (
            patch("sloppy_pdf_renamer.cli._running_in_gui", return_value=True),
            patch("sloppy_pdf_renamer.cli._pick_file_zenity", return_value=str(pdf)),
            patch("sloppy_pdf_renamer.cli._show_result_zenity") as mock_dialog,
            patch("sloppy_pdf_renamer.cli.rename_pdf", return_value=(True, "Renamed: original.pdf -> New Title.pdf")),
            patch("sys.argv", ["sloppy-pdf-renamer"]),
        ):
            rc = main()

        assert rc == 0
        mock_dialog.assert_called_once()

    def test_exits_1_when_chooser_cancelled(self):
        with (
            patch("sloppy_pdf_renamer.cli._running_in_gui", return_value=True),
            patch("sloppy_pdf_renamer.cli._pick_file_zenity", return_value=None),
            patch("sloppy_pdf_renamer.cli._show_result_zenity") as mock_dialog,
            patch("sys.argv", ["sloppy-pdf-renamer"]),
        ):
            rc = main()

        assert rc == 1
        mock_dialog.assert_called_once_with("No file selected.", error=True)

    def test_shows_error_dialog_on_missing_path(self):
        with (
            patch("sloppy_pdf_renamer.cli._running_in_gui", return_value=True),
            patch("sloppy_pdf_renamer.cli._show_result_zenity") as mock_dialog,
            patch("sys.argv", ["sloppy-pdf-renamer", "/nonexistent/file.pdf"]),
        ):
            rc = main()

        assert rc == 1
        mock_dialog.assert_called_once()
        _, kwargs = mock_dialog.call_args
        assert kwargs.get("error") is True
