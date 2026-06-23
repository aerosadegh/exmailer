import logging
import os
from collections.abc import (
    Iterator,
    Sequence,
)
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)

MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25MB Exchange limit


class AttachmentData(TypedDict):
    name: str
    content: bytes
    content_type: str
    size: int
    path: Path


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


def validate_attachments(attachment_paths: Sequence[str] | None) -> Iterator[AttachmentData]:
    """
    Validate and prepare attachments for sending.

    Args:
        attachment_paths: A sequence (list, tuple) of file paths to attach.

    Yields:
        AttachmentData: A dictionary containing validated file metadata and binary content.
    """
    if not attachment_paths:
        return

    for path_str in attachment_paths:
        try:
            path = Path(path_str).expanduser().resolve()

            # Reject directories or missing files
            if not path.is_file():
                logger.warning(f"Skipping missing or invalid file: {path_str}")
                continue

            # Explicitly convert size to int to prevent mock leakage
            size = int(path.stat().st_size)

            if size == 0:
                logger.warning(f"Skipping empty file: {path_str}")
                continue

            if size > MAX_ATTACHMENT_SIZE:
                logger.warning(
                    f"Attachment {path.name} is {size / 1024 / 1024:.1f}MB "
                    f"(exceeds {MAX_ATTACHMENT_SIZE / 1024 / 1024}MB limit). "
                    "Might be rejected by Exchange server."
                )

            content_type = get_content_type(path.name)

            with open(path, "rb") as f:
                content = f.read()

            yield AttachmentData(
                name=path.name,
                content=content,
                content_type=content_type,
                size=size,
                path=path,
            )

        except PermissionError:
            logger.error(f"Permission denied when accessing attachment: {path_str}")
        except OSError as e:
            logger.error(f"I/O error processing attachment {path_str}: {e}")
