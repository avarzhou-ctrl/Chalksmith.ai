from fastapi import Request

from backend.app.core.config import Settings
from backend.app.integrations.storage.base import Storage


def create_storage(settings: Settings) -> Storage:
    if settings.local_storage_dir:
        from backend.app.integrations.storage.local import LocalStorage

        return LocalStorage(settings)
    from backend.app.integrations.storage.gcp import GCSStorage

    return GCSStorage(settings)


def get_storage(request: Request) -> Storage:
    if not hasattr(request.app.state, "storage"):
        request.app.state.storage = create_storage(request.app.state.settings)
    return request.app.state.storage
