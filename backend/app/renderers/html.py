import re
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

REVEAL_CORE_STYLESHEET = (
    "https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.css"
)
REVEAL_THEME_STYLESHEET = (
    "https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/theme/black.min.css"
)
REVEAL_SCRIPT = "https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.js"

_LINK_TAG = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
_SCRIPT_TAG = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*(['\"])(?P<url>[^'\"]+)\1[^>]*>\s*</script>",
    re.IGNORECASE,
)
_HREF = re.compile(r"\bhref\s*=\s*(['\"])(?P<url>[^'\"]+)\1", re.IGNORECASE)


class HTMLRenderer:
    def __init__(self, *, required_marker: str) -> None:
        self.required_marker = required_marker

    async def render(self, code: str, workdir: Path) -> RenderedAsset:
        lowered = code.lower()
        if "<html" not in lowered or self.required_marker not in lowered:
            raise RenderError(f"Generated HTML is missing {self.required_marker}.")
        if any(token in lowered for token in ("document.write(", "eval(", "new function(")):
            raise RenderError("Generated HTML contains a blocked dynamic-execution API.")
        normalized = normalize_reveal_assets(code) if self.required_marker == "reveal" else code
        secured = secure_html_document(normalized)
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


def normalize_reveal_assets(code: str) -> str:
    """Pin generated slides to CDN assets verified by the renderer."""
    found = {"core": False, "theme": False, "script": False}

    def replace_link(match: re.Match[str]) -> str:
        tag = match.group(0)
        href = _HREF.search(tag)
        if not href:
            return tag
        kind = _reveal_stylesheet_kind(href.group("url"))
        if not kind:
            return tag
        if found[kind]:
            return ""
        found[kind] = True
        url = REVEAL_CORE_STYLESHEET if kind == "core" else REVEAL_THEME_STYLESHEET
        return f'<link rel="stylesheet" href="{url}">'

    def replace_script(match: re.Match[str]) -> str:
        if not _is_reveal_core_script(match.group("url")):
            return match.group(0)
        if found["script"]:
            return ""
        found["script"] = True
        return f'<script src="{REVEAL_SCRIPT}"></script>'

    normalized = _LINK_TAG.sub(replace_link, code)
    normalized = _SCRIPT_TAG.sub(replace_script, normalized)

    missing_head_assets = []
    if not found["core"]:
        missing_head_assets.append(f'<link rel="stylesheet" href="{REVEAL_CORE_STYLESHEET}">')
    if not found["theme"]:
        missing_head_assets.append(f'<link rel="stylesheet" href="{REVEAL_THEME_STYLESHEET}">')
    if not found["script"]:
        missing_head_assets.append(f'<script src="{REVEAL_SCRIPT}"></script>')
    if not missing_head_assets:
        return normalized

    assets = "".join(missing_head_assets)
    head_start = re.search(r"<head\b[^>]*>", normalized, re.IGNORECASE)
    if head_start:
        return f"{normalized[:head_start.end()]}{assets}{normalized[head_start.end():]}"
    html_start = re.search(r"<html\b[^>]*>", normalized, re.IGNORECASE)
    if html_start:
        return f"{normalized[:html_start.end()]}<head>{assets}</head>{normalized[html_start.end():]}"
    return f"<head>{assets}</head>{normalized}"


def _reveal_stylesheet_kind(url: str) -> str | None:
    lowered = url.lower().split("?", 1)[0]
    if "reveal.js" not in lowered or not lowered.endswith(".css"):
        return None
    if "/theme/" in lowered:
        return "theme"
    if lowered.endswith(("/reveal.css", "/reveal.min.css")):
        return "core"
    return None


def _is_reveal_core_script(url: str) -> bool:
    lowered = url.lower().split("?", 1)[0]
    return "reveal.js" in lowered and lowered.endswith(("/reveal.js", "/reveal.min.js"))
