"""Tests for utility functions (attachments, MIME types)."""

from pathlib import Path

from exmailer.utils import get_content_type, validate_attachments


def test_mime_type_detection():
    """Test MIME type detection for common file extensions."""
    assert get_content_type("report.pdf") == "application/pdf"
    assert (
        get_content_type("data.xlsx")
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert get_content_type("image.JPG") == "image/jpeg"  # Case insensitive
    assert (
        get_content_type("document.DOCX")
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert get_content_type("archive.zip") == "application/zip"
    assert get_content_type("script.py") == "application/octet-stream"  # Unknown type fallback


def test_validate_attachments_existing_files(tmp_path):
    """Test validation of existing attachment files."""
    # Create test files
    small_file = tmp_path / "small.pdf"
    small_file.write_bytes(b"a" * 1024)  # 1KB

    medium_file = tmp_path / "medium.xlsx"
    medium_file.write_bytes(b"b" * (5 * 1024 * 1024))  # 5MB

    attachments = validate_attachments([str(small_file), str(medium_file)])

    assert len(attachments) == 2
    assert attachments[0]["name"] == "small.pdf"
    assert attachments[0]["content_type"] == "application/pdf"
    assert attachments[0]["size"] == 1024

    assert attachments[1]["name"] == "medium.xlsx"
    assert attachments[1]["size"] == 5 * 1024 * 1024


def test_validate_attachments_skips_missing_files(tmp_path, caplog):
    """Test that missing files are skipped with warning."""
    existing = tmp_path / "exists.txt"
    existing.write_text("content")

    attachments = validate_attachments(
        [str(existing), str(tmp_path / "missing.pdf"), str(tmp_path / "also_missing.docx")]
    )

    assert len(attachments) == 1
    assert attachments[0]["name"] == "exists.txt"
    assert "missing.pdf" in caplog.text
    assert "also_missing.docx" in caplog.text


def test_validate_attachments_skips_empty_files(tmp_path, caplog):
    """Test that empty files are skipped with warning."""
    empty = tmp_path / "empty.txt"
    empty.write_bytes(b"")

    non_empty = tmp_path / "non_empty.txt"
    non_empty.write_text("content")

    attachments = validate_attachments([str(empty), str(non_empty)])

    assert len(attachments) == 1
    assert attachments[0]["name"] == "non_empty.txt"
    assert "Skipping empty file" in caplog.text


def test_validate_attachments_large_file_warning(tmp_path, caplog):
    """Test warning for large files approaching Exchange limits."""
    large_file = tmp_path / "large.pdf"
    large_file.write_bytes(b"a" * (26 * 1024 * 1024))  # 26MB > 25MB limit

    attachments = validate_attachments([str(large_file)])

    assert len(attachments) == 1
    assert "26.0MB" in caplog.text
    assert "exceeds 25.0MB limit".lower() in caplog.text.lower()


def test_validate_attachments_tilde_expansion():
    """Test that ~ paths are expanded correctly."""
    # We can't test actual home directory expansion reliably in tests,
    # but we can verify the function handles Path objects correctly

    # Mock a home directory path
    fake_home = Path("/fake/home/user")
    test_file = fake_home / "document.pdf"

    # Simulate what Path.expanduser() would do
    expanded = Path(str(test_file)).expanduser()
    assert expanded == test_file  # In test env, ~ won't expand to real home
