from abc import ABC, abstractmethod
import os
from fastapi.responses import FileResponse
from backend.services.render import STATIC_DIR
from urllib.parse import urlparse

class ExportStrategy(ABC):
    @abstractmethod
    def export(self, file_path: str, filename: str) -> FileResponse:
        pass

class FileExportStrategy(ExportStrategy):
    def export(self, file_path: str, filename: str) -> FileResponse:
        """
        Generic file export strategy for serving files from the static directory.
        """
        # file_path is something like /static/remotion_xxx.mp4
        # We need the absolute path on the filesystem.
        # STATIC_DIR is /.../backend/static
        
        # Remove the /static/ prefix to get the filename
        base_filename = os.path.basename(file_path)
        actual_path = os.path.join(STATIC_DIR, base_filename)

        if not os.path.exists(actual_path):
            # Try searching in media/ too if it's a manim video
            media_path = os.path.join(STATIC_DIR, "media", "videos", base_filename.replace(".mp4", ""), "720p30", base_filename)
            if os.path.exists(media_path):
                actual_path = media_path
            else:
                raise FileNotFoundError(f"File not found at: {actual_path}")

        # Set media type based on extension
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
    
class PDFExportStrategy(ExportStrategy):
    def export(self, file_path: str, filename: str) -> FileResponse:
        """
        Converts an HTML file from the static directory to a PDF and serves it.
        """
        base_filename = os.path.basename(file_path)
        html_path = os.path.join(STATIC_DIR, base_filename)

        if not os.path.exists(html_path):
            raise FileNotFoundError(f"HTML file not found at: {html_path}")
        
        # Path for the PDF output - reuse the same ID as the HTML but change extension
        pdf_path = html_path.replace(".html", ".pdf")

        # Convert HTML to PDF using Playwright (sync)
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
                page = browser.new_page()

                # Use file:// protocol for local file access
                absolute_html_path = os.path.abspath(html_path)
                # Add ?print-pdf to reveal.js URL to help it render correctly
                page.goto(f"file://{absolute_html_path}?print-pdf")

                # Wait for any potential scripts to run
                page.wait_for_timeout(2000)

                page.pdf(path=pdf_path, format="A4", print_background=True)
                browser.close()
            except Exception as e:
                print(f"PDF Export error: {e}")
                # Fallback to serving the HTML if PDF fails
                return FileResponse(path=html_path, filename=filename.replace(".pdf", ".html"))

        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
class ExportService:
    def __init__(self):
        # We can map formats to strategies here if we need specific logic for some
        self.strategies = {
            "remotion": FileExportStrategy(),
            "manim": FileExportStrategy(),
            "p5js": FileExportStrategy(),
            "reveal.js": PDFExportStrategy()
        }
        self._default_strategy = FileExportStrategy()

    def get_strategy(self, format_type: str) -> ExportStrategy:
        return self.strategies.get(format_type, self._default_strategy)
    
    def prepare_export(self, file_url: str, format_type: str, topic: str) -> FileResponse:
        """
        Prepares a fileResponse for exporting a lesson.
        """
        # Determine extension and sanitized filename
        if format_type == "remotion":
            # Check if we actually have an mp4 or just the json fallback
            if ".json" in file_url:
                extension = ".json"
            else:
                extension = ".mp4"
        elif format_type == "manim":
            extension = ".mp4"
        elif format_type == "reveal.js":
            extension = ".pdf"
        else: # p5.js or others
            extension = ".html"

        sanitized_topic = "".join(c if c.isalnum() else "_" for c in topic)
        filename = f"{sanitized_topic}{extension}"

        parsed_url = urlparse(file_url)
        path_to_file = parsed_url.path # e.g. /static/remotion_...mp4

        strategy = self.get_strategy(format_type)
        return strategy.export(path_to_file, filename)
    
# Singleton instance
export_service = ExportService()