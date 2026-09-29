from pathlib import Path
from typing import BinaryIO
from uuid import UUID

class FileSizeLimitExceeded(ValueError):
    """Raised when a streamed document exceeds the configured size limit."""

class DocumentStorage:
    def __init__(self, root: Path):
        self.root = root

    def create_temp_path(self, document_id: UUID) -> Path:
        document_dir = self._document_dir(document_id)
        document_dir.mkdir(parents=True, exist_ok=True)

        return document_dir / "upload.tmp"

    def finalize(self, document_id: UUID) -> Path:
        document_dir = self._document_dir(document_id)

        temp_path = document_dir / "upload.tmp"
        final_path = document_dir / "original"

        temp_path.replace(final_path)

        return final_path

    def delete(self, document_id: UUID) -> None:
        document_dir = self._document_dir(document_id)

        if not document_dir.exists():
            return

        for path in document_dir.iterdir():
            path.unlink()

        document_dir.rmdir()

    def write_stream(
        self,
        document_id: UUID,
        stream: BinaryIO,
        max_size: int,
    ) -> int:
        temp_path = self.create_temp_path(document_id)

        total_size = 0

        try:
            with temp_path.open("wb") as destination:
                while chunk := stream.read(1024 * 1024):
                    total_size += len(chunk)

                    if total_size > max_size:
                        raise FileSizeLimitExceeded("File size exceeds maximum allowed size")

                    destination.write(chunk)

        except Exception:
            self.delete(document_id)
            raise

        return total_size

    def _document_dir(self, document_id: UUID) -> Path:
        document_dir = (self.root / str(document_id)).resolve()
        root = self.root.resolve()

        try:
            document_dir.relative_to(root)
        except ValueError as exc:
            raise ValueError("document storage path escapes storage root.") from exc

        return document_dir