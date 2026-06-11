from abc import ABC, abstractmethod
import os
import asyncio
from fastapi.responses import FileResponse
from backend.services.render import STATIC_DIR
from urllib.parse import urlparse
from playwright.async_api import async_playwright

class ExportStrategy(ABC):
    """Base class to allow swapping export logic (e.g., PDF vs Video) per format"""
    @abstractmethod
    async def export(self, file_path: str, filename: str) -> FileResponse:
        pass

class FileExportStrategy(ExportStrategy):
    """Serves existing static files directly from the server storage"""
    async def export(self, file_path: str, filename: str) -> FileResponse:
        # Extract filename to build an absolute filesystem path
        base_filename = os.path.basename(file_path)
        actual_path = os.path.join(STATIC_DIR, base_filename)

        if not os.path.exists(actual_path):
            # Manim renders to a nested media/ folder; check there as a fallback
            media_path = os.path.join(STATIC_DIR, "media", "videos", base_filename.replace(".mp4", ""), "720p30", base_filename)
            if os.path.exists(media_path):
                actual_path = media_path
            else:
                raise FileNotFoundError(f"File not found at: {actual_path}")

        # Map extensions to MIME types so the browser handles the download correctly
        if filename.endswith(".mp4"):
            media_type = "video/mp4"
        elif filename.endswith(".pdf"):
            media_type = "application/pdf"
        elif filename.endswith(".json"):
            media_type = "application/json"
        else:
            media_type = "text/html"

        return FileResponse(
            path=actual_path,
            filename=filename,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

class ExportService:
    """Orchestrates different export strategies based on lesson format"""
    def __init__(self):
        # Maps format keys to their specialized export behaviors
        self.strategies = {
            "remotion": FileExportStrategy(),
            "manim": FileExportStrategy(),
            "p5js": FileExportStrategy(),
            "reveal.js": FileExportStrategy()
        }
        self._default_strategy = FileExportStrategy()

    def get_strategy(self, format_type: str) -> ExportStrategy:
        return self.strategies.get(format_type, self._default_strategy)
    
    async def prepare_export(self, file_url: str, format_type: str, topic: str) -> FileResponse:
        """Determines the correct extension and triggers the strategy"""
        # Select extension based on the actual file content available
        if format_type == "remotion":
            extension = ".json" if ".json" in file_url else ".mp4"
        elif format_type == "manim":
            extension = ".mp4"
        else:
            # reveal.js and p5.js both export as HTML
            extension = ".html"

        # Sanitize filename to prevent download errors in certain browsers
        sanitized_topic = "".join(c if c.isalnum() else "_" for c in topic)
        filename = f"{sanitized_topic}{extension}"

        parsed_url = urlparse(file_url)
        path_to_file = parsed_url.path 

        strategy = self.get_strategy(format_type)
        return await strategy.export(path_to_file, filename)
    
# Export service singleton for app-wide use
export_service = ExportService()