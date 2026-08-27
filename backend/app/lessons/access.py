import re
from pathlib import Path

from backend.app.api.schemas import AccessURLResponse
from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.db.models import Lesson
from backend.app.integrations.storage import Storage


def sign_lesson_access(
    lesson: Lesson,
    *,
    download: bool,
    storage: Storage,
    settings: Settings,
) -> AccessURLResponse:
    if lesson.status != "ready" or not lesson.object_key:
        raise AppError(code="lesson_not_ready", message="Lesson output is not ready.", status_code=409)
    extension = Path(lesson.object_key).suffix
    safe_topic = re.sub(r"[^\w .()-]", "_", lesson.topic, flags=re.UNICODE).strip()[:80]
    download_name = f"{safe_topic or 'chalksmith-lesson'}{extension}" if download else None
    try:
        url = storage.signed_url(lesson.object_key, download_name=download_name)
    except Exception as error:
        raise AppError(
            code="signed_url_failed",
            message="A temporary lesson URL could not be created.",
            status_code=503,
        ) from error
    return AccessURLResponse(url=url, expires_in=settings.signed_url_ttl_seconds)
