from dataclasses import dataclass
from pathlib import Path


MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
}


@dataclass(frozen=True)
class FileValidationResult:
    valid: bool
    error_code: str | None = None
    reason: str | None = None


def _validate_filename(filename: str) -> FileValidationResult | None:
    if not filename:
        return FileValidationResult(
            valid=False,
            error_code="INVALID_FILENAME",
            reason="Filename is required",
        )

    path = Path(filename)

    if (
        path.is_absolute()
        or path.name != filename
        or "/" in filename
        or "\\" in filename
    ):
        return FileValidationResult(
            valid=False,
            error_code="INVALID_FILENAME",
            reason="Filename must not contain path components",
        )

    if any(ord(character) < 32 for character in filename):
        return FileValidationResult(
            valid=False,
            error_code="INVALID_FILENAME",
            reason="Filename contains invalid control characters",
        )

    return None

def validate_file(
    filename: str,
    size_bytes: int,
) -> FileValidationResult:

    filename_error = _validate_filename(filename)

    if filename_error is not None:
        return filename_error

    if size_bytes <= 0:
        return FileValidationResult(
            valid=False,
            error_code="EMPTY_FILE",
            reason="File is empty",
        )

    if size_bytes > MAX_FILE_SIZE:
        return FileValidationResult(
            valid=False,
            error_code="FILE_TOO_LARGE",
            reason="File size exceeds the maximum allowed size",
        )

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return FileValidationResult(
            valid=False,
            error_code="UNSUPPORTED_TYPE",
            reason="Unsupported file type",
        )

    return FileValidationResult(
        valid=True,
    )