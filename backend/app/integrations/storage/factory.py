from fastapi import Request

from backend.app.core.config import Settings
from backend.app.integrations.storage.base import Storage
from backend.app.integrations.storage.gcp import GCSStorage
from backend.app.integrations.storage.local import LocalStorage


def create_storage(settings: Settings) -> Storage:
    if settings.local_storage_dir:
        return LocalStorage(settings)
    return GCSStorage(settings)


def get_storage(request: Request) -> Storage:
    if not hasattr(request.app.state, "storage"):
        request.app.state.storage = create_storage(request.app.state.settings)
    return request.app.state.storage
