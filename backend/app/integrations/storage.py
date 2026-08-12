from datetime import timedelta
from pathlib import Path

import google.auth
from google.auth import impersonated_credentials
from google.cloud import storage
from google.api_core.exceptions import NotFound
from fastapi import Request

from backend.app.core.config import Settings
from backend.app.core.errors import AppError


class GCSStorage:
    def __init__(self, settings: Settings) -> None:
        if not settings.gcs_bucket:
            raise AppError(
                code="storage_not_configured",
                message="GCS_BUCKET is not configured.",
                status_code=503,
            )
        self.settings = settings
        self.client = storage.Client(project=settings.gcp_project_id)
        self.bucket = self.client.bucket(settings.gcs_bucket)

    def upload_file(self, source: Path, object_key: str, content_type: str) -> None:
        blob = self.bucket.blob(object_key)
        blob.content_disposition = "inline"
        blob.cache_control = "private, max-age=300"
        blob.upload_from_filename(source, content_type=content_type)

    def upload_bytes(self, data: bytes, object_key: str, content_type: str) -> None:
        self.bucket.blob(object_key).upload_from_string(data, content_type=content_type)

    def delete(self, object_key: str) -> None:
        try:
            self.bucket.blob(object_key).delete(if_generation_match=None)
        except NotFound:
            return

    def delete_prefix(self, prefix: str) -> None:
        for blob in self.client.list_blobs(self.bucket, prefix=prefix):
            try:
                blob.delete()
            except NotFound:
                continue

    def signed_url(self, object_key: str, *, download_name: str | None = None) -> str:
        credentials = self.client._credentials
        signer_email = self.settings.gcs_signer_service_account
        if signer_email and getattr(credentials, "signer_email", None) != signer_email:
            source_credentials, _ = google.auth.default()
            credentials = impersonated_credentials.Credentials(
                source_credentials=source_credentials,
                target_principal=signer_email,
                target_scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
                lifetime=min(self.settings.signed_url_ttl_seconds, 3600),
            )
        disposition = "inline"
        if download_name:
            disposition = f'attachment; filename="{download_name}"'
        return self.bucket.blob(object_key).generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=self.settings.signed_url_ttl_seconds),
            method="GET",
            response_disposition=disposition,
            credentials=credentials,
        )


def get_storage(request: Request) -> GCSStorage:
    if not hasattr(request.app.state, "storage"):
        request.app.state.storage = GCSStorage(request.app.state.settings)
    return request.app.state.storage
