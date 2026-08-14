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
REVEAL_FALLBACK_STYLE = """<style data-chalksmith-reveal-fallback>
html, body {
  width: 100%;
  height: 100%;
  margin: 0;
  background: #191919;
}
.reveal {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  color: #fff;
}
.reveal.chalksmith-reveal-fallback .slides {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  padding: 4%;
  overflow: auto;
}
.reveal.chalksmith-reveal-fallback .slides > section {
  display: none !important;
}
.reveal.chalksmith-reveal-fallback .slides > section:first-child {
  position: relative !important;
  display: block !important;
  width: 100% !important;
  height: auto !important;
  transform: none !important;
  visibility: visible !important;
}
</style>"""
REVEAL_FALLBACK_SCRIPT = """<script data-chalksmith-reveal-fallback>
window.addEventListener("load", () => {
  window.setTimeout(() => {
    const deck = document.querySelector(".reveal");
    const firstSlide = deck?.querySelector(".slides > section");
    if (!deck || !firstSlide) return;
    const style = window.getComputedStyle(firstSlide);
    const bounds = firstSlide.getBoundingClientRect();
    if (!deck.classList.contains("ready") || style.display === "none" ||
        style.visibility === "hidden" || bounds.width === 0 || bounds.height === 0) {
      deck.classList.add("chalksmith-reveal-fallback");
    }
  }, 1000);
}, { once: true });
</script>"""

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
    """Pin Reveal assets and keep slides visible if the CDN runtime fails."""
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
    normalized = _inject_into_head(normalized, "".join(missing_head_assets))
    normalized = _inject_into_head(normalized, REVEAL_FALLBACK_STYLE, before_close=True)
    return _inject_before_body_close(normalized, REVEAL_FALLBACK_SCRIPT)


def _inject_into_head(code: str, content: str, *, before_close: bool = False) -> str:
    if not content:
        return code
    if before_close:
        head_end = re.search(r"</head\s*>", code, re.IGNORECASE)
        if head_end:
            return f"{code[:head_end.start()]}{content}{code[head_end.start():]}"
    head_start = re.search(r"<head\b[^>]*>", code, re.IGNORECASE)
    if head_start:
        return f"{code[:head_start.end()]}{content}{code[head_start.end():]}"
    html_start = re.search(r"<html\b[^>]*>", code, re.IGNORECASE)
    if html_start:
        return f"{code[:html_start.end()]}<head>{content}</head>{code[html_start.end():]}"
    return f"<head>{content}</head>{code}"


def _inject_before_body_close(code: str, content: str) -> str:
    body_end = re.search(r"</body\s*>", code, re.IGNORECASE)
    if body_end:
        return f"{code[:body_end.start()]}{content}{code[body_end.start():]}"
    return f"{code}{content}"


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
