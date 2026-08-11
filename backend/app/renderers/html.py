from pathlib import Path

from backend.app.renderers.base import RenderError, RenderedAsset

CONTENT_SECURITY_POLICY = (
    "default-src 'none'; "
    "script-src 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "style-src 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "font-src data: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "img-src data: blob:; media-src data: blob:; connect-src 'none'; "
    "object-src 'none'; base-uri 'none'; form-action 'none'"
)


class HTMLRenderer:
    def __init__(self, *, required_marker: str) -> None:
        self.required_marker = required_marker

    async def render(self, code: str, workdir: Path) -> RenderedAsset:
        lowered = code.lower()
        if "<html" not in lowered or self.required_marker not in lowered:
            raise RenderError(f"Generated HTML is missing {self.required_marker}.")
        if any(token in lowered for token in ("document.write(", "eval(", "new function(")):
            raise RenderError("Generated HTML contains a blocked dynamic-execution API.")
        secured = secure_html_document(code)
        output = workdir / "lesson.html"
        output.write_text(secured, encoding="utf-8")
        return RenderedAsset(path=output, content_type="text/html; charset=utf-8", extension="html")


def secure_html_document(code: str) -> str:
    meta = f'<meta http-equiv="Content-Security-Policy" content="{CONTENT_SECURITY_POLICY}">'
    lowered = code.lower()
    head_end = lowered.find(">", lowered.find("<head"))
    if head_end >= 0:
        return f"{code[:head_end + 1]}{meta}{code[head_end + 1:]}"
    html_end = lowered.find(">", lowered.find("<html"))
    if html_end < 0:
        return f"{meta}{code}"
    return f"{code[:html_end + 1]}<head>{meta}</head>{code[html_end + 1:]}"
