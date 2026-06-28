import logging
import mimetypes
from collections.abc import (
    Iterator,
    Sequence,
)
from pathlib import Path
from typing import TypedDict
from typing import TypedDict

logger = logging.getLogger(__name__)

MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25MB Exchange limit


class AttachmentData(TypedDict):
    name: str
    content: bytes
    content_type: str
    size: int
    path: Path


# Types that are absent from or inconsistently reported by the stdlib mimetypes
# module across platforms (e.g. Windows registry vs. Linux /etc/mime.types).
# These entries take priority over whatever the OS reports.
_EXTRA_MIME_TYPES: dict[str, str] = {
    ".msg": "application/vnd.ms-outlook",
    ".rtf": "application/rtf",
    ".zip": "application/zip",  # Windows registry: application/x-zip-compressed
    ".csv": "text/csv",  # Windows registry: application/vnd.ms-excel
}


def get_content_type(filename: str) -> str:
    """Return the MIME type for a filename using the stdlib mimetypes module."""
    ext = Path(filename).suffix.lower()
    if ext in _EXTRA_MIME_TYPES:
        return _EXTRA_MIME_TYPES[ext]
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"


def validate_attachments(attachment_paths: Sequence[str] | None) -> Iterator[AttachmentData]:
def validate_attachments(attachment_paths: Sequence[str] | None) -> Iterator[AttachmentData]:
    """
    Validate and prepare attachments for sending.

    Args:
        attachment_paths: A sequence (list, tuple) of file paths to attach.

    Yields:
        AttachmentData: A dictionary containing validated file metadata and binary content.

    Args:
        attachment_paths: A sequence (list, tuple) of file paths to attach.

    Yields:
        AttachmentData: A dictionary containing validated file metadata and binary content.
    """
    if not attachment_paths:
        return
        return

    for path_str in attachment_paths:
        try:
            path = Path(path_str).expanduser().resolve()

            # Reject directories or missing files
            if not path.is_file():
                logger.warning(f"Skipping missing or invalid file: {path_str}")
            # Reject directories or missing files
            if not path.is_file():
                logger.warning(f"Skipping missing or invalid file: {path_str}")
                continue

            # Explicitly convert size to int to prevent mock leakage
            size = int(path.stat().st_size)

            if size == 0:
                logger.warning(f"Skipping empty file: {path_str}")
                continue
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

            yield AttachmentData(
                name=path.name,
                content=b"",  # Content is read once by the caller to avoid double I/O
                content_type=content_type,
                size=size,
                path=path,
            )

        except PermissionError:
            logger.error(f"Permission denied when accessing attachment: {path_str}")
        except OSError as e:
            logger.error(f"I/O error processing attachment {path_str}: {e}")
        except PermissionError:
            logger.error(f"Permission denied when accessing attachment: {path_str}")
        except OSError as e:
            logger.error(f"I/O error processing attachment {path_str}: {e}")
