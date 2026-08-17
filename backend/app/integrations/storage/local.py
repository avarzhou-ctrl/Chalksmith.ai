from pathlib import Path
from shutil import copyfile, rmtree
from urllib.parse import quote

from backend.app.core.config import Settings
from backend.app.core.errors import AppError

# There is no storage.googleapis.com equivalent on disk, so the API serves its
# own objects under this route.
LOCAL_OBJECT_ROUTE = "/local-storage"


class LocalStorage:
    """Filesystem artifact store for debugging without a usable link to GCS.

    Object keys become paths under LOCAL_STORAGE_DIR, so lessons written here
    exist on this machine only.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.local_storage_dir:
            raise AppError(
                code="storage_not_configured",
                message="LOCAL_STORAGE_DIR is not configured.",
                status_code=503,
            )
        self.settings = settings
        self.root = Path(settings.local_storage_dir).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def object_path(self, object_key: str) -> Path:
        path = (self.root / object_key).resolve()
        # The serving route passes a client-supplied key straight to here.
        if path == self.root or not path.is_relative_to(self.root):
            raise AppError(code="object_not_found", message="Object not found.", status_code=404)
        return path

    # Content types go unrecorded; the serving route derives one from the extension.
    def upload_file(self, source: Path, object_key: str, content_type: str) -> None:
        copyfile(source, self._prepared_path(object_key))

    def upload_bytes(self, data: bytes, object_key: str, content_type: str) -> None:
        self._prepared_path(object_key).write_bytes(data)

    def delete(self, object_key: str) -> None:
        self.object_path(object_key).unlink(missing_ok=True)

    def delete_prefix(self, prefix: str) -> None:
        # Callers pass directory-shaped prefixes, which map to a subtree on disk.
        rmtree(self.object_path(prefix), ignore_errors=True)

    def signed_url(self, object_key: str, *, download_name: str | None = None) -> str:
        query = f"?download={quote(download_name)}" if download_name else ""
        base_url = self.settings.local_storage_base_url
        return f"{base_url}{LOCAL_OBJECT_ROUTE}/{quote(object_key)}{query}"

    def _prepared_path(self, object_key: str) -> Path:
        path = self.object_path(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
