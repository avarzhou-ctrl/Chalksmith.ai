from pathlib import Path
from typing import Protocol


class Storage(Protocol):
    """Lesson artifact store. Object keys are identical across backends, so a
    lesson row only resolves against the backend that wrote it."""

    def upload_file(self, source: Path, object_key: str, content_type: str) -> None: ...

    def upload_bytes(self, data: bytes, object_key: str, content_type: str) -> None: ...

    def delete(self, object_key: str) -> None: ...

    def delete_prefix(self, prefix: str) -> None: ...

    def signed_url(self, object_key: str, *, download_name: str | None = None) -> str: ...
