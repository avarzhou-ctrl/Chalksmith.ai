from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from backend.app.core.errors import AppError
from backend.app.integrations.storage import Storage, get_storage
from backend.app.integrations.storage.local import LOCAL_OBJECT_ROUTE, LocalStorage

router = APIRouter(tags=["system"])


@router.get(LOCAL_OBJECT_ROUTE + "/{object_key:path}", include_in_schema=False)
def read_local_object(
    object_key: str,
    download: str | None = None,
    storage: Storage = Depends(get_storage),
) -> FileResponse:
    """Serve what a GCS signed URL would. main.py mounts this only when
    LOCAL_STORAGE_DIR is set, so a deployed API has no such route."""
    if not isinstance(storage, LocalStorage):
        raise AppError(code="object_not_found", message="Object not found.", status_code=404)
    path = storage.object_path(object_key)
    if not path.is_file():
        raise AppError(code="object_not_found", message="Object not found.", status_code=404)
    return FileResponse(
        path,
        filename=download,
        content_disposition_type="attachment",
        headers={"X-Content-Type-Options": "nosniff"},
    )
