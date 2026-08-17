import re
from pathlib import Path

from backend.app.lessons.render.base import RenderError, RenderedAsset

CONTENT_SECURITY_POLICY = (
    "default-src 'none'; "
    "script-src 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "style-src 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "font-src data: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "img-src data: blob:; media-src data: blob:; connect-src 'none'; "
    "object-src 'none'; base-uri 'none'; form-action 'none'"
)

_SCRIPT_BLOCK = re.compile(
    r"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>",
    re.IGNORECASE | re.DOTALL,
)
_SRC_ATTRIBUTE = re.compile(r"\bsrc\s*=", re.IGNORECASE)
_COUNTER_FOR_LOOP = re.compile(
    r"\bfor\s*\(\s*(?:let|var)\s+"
    r"(?P<counter>[$A-Za-z_][$\w]*)\s*=\s*[^;]+;\s*"
    r"(?P=counter)\s*(?P<comparison>>=|>|<=|<)\s*[^;]+;\s*"
    r"(?P<update>(?:(?P=counter)\s*(?:\+\+|--)|(?:\+\+|--)\s*(?P=counter)))\s*\)"
)


class HTMLRenderer:
    def __init__(self, *, required_marker: str) -> None:
        self.required_marker = required_marker

    async def render(self, code: str, workdir: Path) -> RenderedAsset:
        lowered = code.lower()
        if "<html" not in lowered or self.required_marker not in lowered:
            raise RenderError(f"Generated HTML is missing {self.required_marker}.")
        if any(
            token in lowered for token in ("document.write(", "eval(", "new function(")
        ):
            raise RenderError(
                "Generated HTML contains a blocked dynamic-execution API."
            )
        bad_loop = _find_nonterminating_counter_loop(code)
        if bad_loop:
            raise RenderError(
                "Generated HTML contains a counter loop whose update moves away from its "
                f"stopping condition: {bad_loop}"
            )
        secured = secure_html_document(code)
        output = workdir / "lesson.html"
        output.write_text(secured, encoding="utf-8")
        return RenderedAsset(
            path=output, content_type="text/html; charset=utf-8", extension="html"
        )


def secure_html_document(code: str) -> str:
    meta = f'<meta http-equiv="Content-Security-Policy" content="{CONTENT_SECURITY_POLICY}">'
    lowered = code.lower()
    head_end = lowered.find(">", lowered.find("<head"))
    if head_end >= 0:
        return f"{code[: head_end + 1]}{meta}{code[head_end + 1 :]}"
    html_end = lowered.find(">", lowered.find("<html"))
    if html_end < 0:
        return f"{meta}{code}"
    return f"{code[: html_end + 1]}<head>{meta}</head>{code[html_end + 1 :]}"


def _find_nonterminating_counter_loop(code: str) -> str | None:
    """Catch obvious counter-direction mistakes before they freeze the preview iframe."""
    for script in _SCRIPT_BLOCK.finditer(code):
        if _SRC_ATTRIBUTE.search(script.group("attrs")):
            continue
        executable = _mask_js_non_code(script.group("body"))
        for loop in _COUNTER_FOR_LOOP.finditer(executable):
            comparison = loop.group("comparison")
            update = loop.group("update")
            if (comparison.startswith(">") and "++" in update) or (
                comparison.startswith("<") and "--" in update
            ):
                return " ".join(loop.group(0).split())
    return None


def _mask_js_non_code(script: str) -> str:
    """Mask comments and literals so lesson text is not mistaken for executable loops."""
    masked = list(script)
    index = 0
    while index < len(script):
        current = script[index]
        if current in {"'", '"', "`"}:
            delimiter = current
            masked[index] = " "
            index += 1
            while index < len(script):
                current = script[index]
                masked[index] = "\n" if current == "\n" else " "
                index += 1
                if current == "\\" and index < len(script):
                    masked[index] = "\n" if script[index] == "\n" else " "
                    index += 1
                elif current == delimiter:
                    break
            continue
        if current == "/" and index + 1 < len(script) and script[index + 1] == "/":
            masked[index] = masked[index + 1] = " "
            index += 2
            while index < len(script) and script[index] != "\n":
                masked[index] = " "
                index += 1
            continue
        if current == "/" and index + 1 < len(script) and script[index + 1] == "*":
            masked[index] = masked[index + 1] = " "
            index += 2
            while index < len(script):
                current = script[index]
                masked[index] = "\n" if current == "\n" else " "
                index += 1
                if current == "*" and index < len(script) and script[index] == "/":
                    masked[index] = " "
                    index += 1
                    break
            continue
        index += 1
    return "".join(masked)
