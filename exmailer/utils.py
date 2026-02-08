import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25MB Exchange limit


def get_content_type(filename: str) -> str:
    """Map file extensions to MIME types for common corporate files."""
    extensions = {
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".zip": "application/zip",
        ".txt": "text/plain",
        ".csv": "text/csv",
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".rtf": "application/rtf",
        ".msg": "application/vnd.ms-outlook",
    }
    ext = os.path.splitext(filename.lower())[1]
    return extensions.get(ext, "application/octet-stream")


def validate_attachments(attachment_paths):
    """
    Validate and prepare attachments for sending.
    Returns list of dicts with name, content, content_type, size.
    """
    if not attachment_paths:
        return []

    validated = []
    for path_str in attachment_paths:
        try:
            path = Path(path_str).expanduser().resolve()

            if not path.exists():
                logger.warning(f"Skipping missing attachment: {path}")
                continue

            if path.stat().st_size == 0:
                logger.warning(f"Skipping empty file: {path}")
                continue

            # Explicitly convert size to int to prevent mock leakage
            size = int(path.stat().st_size)  # ← Prevent MagicMock comparison errors

            if size > MAX_ATTACHMENT_SIZE:
                logger.warning(
                    f"Attachment {path.name} is {size / 1024 / 1024:.1f}MB "
                    f"(exceeds {MAX_ATTACHMENT_SIZE / 1024 / 1024}MB limit). "
                    "Might be rejected by Exchange server."
                )

            content_type = get_content_type(path.name)

            with open(path, "rb") as f:
                content = f.read()

            validated.append(
                {
                    "name": path.name,
                    "content": content,
                    "content_type": content_type,
                    "size": size,  # Guaranteed int
                    "path": path,
                }
            )

        except Exception as e:  # pragma: no cover
            logger.warning(f"Failed to process attachment {path_str}: {e}")
            continue

    return validated
