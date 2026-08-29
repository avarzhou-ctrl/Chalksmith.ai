import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from backend.app.lessons.render.base import (
    GeneratedCodeError,
    PolicyViolationError,
    RenderedAsset,
)

# The parser-level allowlist narrows supported libraries; host-level CSP keeps arbitrary approved versions loadable.
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
_KNOWN_P5_URL = re.compile(
    r"https://(?:cdn\.jsdelivr\.net/npm/p5@[^/]+/lib/p5\.min\.js|"
    r"cdnjs\.cloudflare\.com/ajax/libs/p5\.js/[^/]+/p5\.min\.js)",
    re.IGNORECASE,
)
_KNOWN_KATEX_URL = re.compile(
    r"https://(?:cdn\.jsdelivr\.net/npm/katex@[^/]+/dist/|"
    r"cdnjs\.cloudflare\.com/ajax/libs/KaTeX/[^/]+/)(?:katex\.min\.css|"
    r"katex\.min\.js|contrib/auto-render\.min\.js)",
    re.IGNORECASE,
)
_KNOWN_REVEAL_SCRIPT_URL = re.compile(
    r"https://(?:cdn\.jsdelivr\.net/npm/reveal\.js@[^/?#]+/dist/reveal(?:\.min)?\.js|"
    r"cdnjs\.cloudflare\.com/ajax/libs/reveal\.js/[^/?#]+/reveal\.min\.js)",
    re.IGNORECASE,
)
_UNRELIABLE_SCRIPT_APIS = re.compile(
    r"\b(?:eval\s*\(|new\s+Function\s*\(|document\s*\.\s*write\s*\()",
    re.IGNORECASE,
)
_COUNTER_FOR_LOOP = re.compile(
    r"\bfor\s*\(\s*(?:let|var)\s+"
    r"(?P<counter>[$A-Za-z_][$\w]*)\s*=\s*[^;]+;\s*"
    r"(?P=counter)\s*(?P<comparison>>=|>|<=|<)\s*[^;]+;\s*"
    r"(?P<update>(?:(?P=counter)\s*(?:\+\+|--)|(?:\+\+|--)\s*(?P=counter)))\s*\)"
)
_VISIBLE_LATEX = re.compile(
    r"\$\$.+?\$\$|(?<!\\)\$(?!\$).+?(?<!\\)\$(?!\$)|\\\(.+?\\\)|\\\[.+?\\\]",
    re.DOTALL,
)
_GLOBAL_MATH_RENDER = re.compile(
    r"\b(?:renderMathInElement|typesetMath|renderMath)\s*\(\s*"
    r"document\.(?:body|documentElement)\b",
    re.IGNORECASE,
)
_NON_VISIBLE_TAGS = {"head", "script", "style", "template", "textarea", "noscript"}
P5_SCRIPT = "https://cdn.jsdelivr.net/npm/p5@1.11.0/lib/p5.min.js"
KATEX_STYLESHEET = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"
KATEX_SCRIPT = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"
KATEX_AUTO_RENDER_SCRIPT = (
    "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
)
_APPROVED_CDN_HOSTS = frozenset({"cdn.jsdelivr.net", "cdnjs.cloudflare.com"})
_KATEX_TYPESET_SCRIPT = r'''<script data-chalksmith-katex>
window.addEventListener("load", () => {
  if (typeof renderMathInElement !== "function") return;
  renderMathInElement(document.body, {
    delimiters: [
      { left: "$$", right: "$$", display: true },
      { left: "\\[", right: "\\]", display: true },
      { left: "$", right: "$", display: false },
      { left: "\\(", right: "\\)", display: false },
    ],
    ignoredTags: ["script", "noscript", "style", "textarea", "pre", "option"],
    throwOnError: false,
  });
}, { once: true });
</script>'''


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._hidden_depth = 0
        self.text: list[str] = []

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in _NON_VISIBLE_TAGS:
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _NON_VISIBLE_TAGS and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._hidden_depth:
            self.text.append(data)


class _DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.start_tags: dict[str, int] = {}
        self.end_tags: dict[str, int] = {}
        self.remote_assets: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        self.start_tags[normalized_tag] = self.start_tags.get(normalized_tag, 0) + 1
        normalized_attrs = {name.lower(): value for name, value in attrs}
        attribute = "src" if normalized_tag == "script" else "href"
        url = normalized_attrs.get(attribute) if normalized_tag in {"script", "link"} else None
        if url and urlparse(url).scheme in {"http", "https"}:
            self.remote_assets.add(url)

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        self.end_tags[normalized_tag] = self.end_tags.get(normalized_tag, 0) + 1


class HTMLRenderer:
    def __init__(self, *, required_marker: str) -> None:
        self.required_marker = required_marker

    async def render(self, code: str, workdir: Path) -> RenderedAsset:
        document = _parse_html_document(code)
        _validate_html_structure(document)
        _validate_remote_assets(document)
        _validate_executable_script_reliability(code)
        _validate_counter_loops(code)
        code = _ensure_required_runtime(code, document, self.required_marker)
        if self.required_marker == "p5":
            code = _prepare_interactive_math(code)
        secured = secure_html_document(code)
        output = workdir / "lesson.html"
        output.write_text(secured, encoding="utf-8")
        return RenderedAsset(
            path=output, content_type="text/html; charset=utf-8", extension="html"
        )


def secure_html_document(code: str) -> str:
    # Inject the platform CSP before the lesson can be served in a sandboxed iframe.
    meta = f'<meta http-equiv="Content-Security-Policy" content="{CONTENT_SECURITY_POLICY}">'
    lowered = code.lower()
    head_end = lowered.find(">", lowered.find("<head"))
    if head_end >= 0:
        return f"{code[: head_end + 1]}{meta}{code[head_end + 1 :]}"
    html_end = lowered.find(">", lowered.find("<html"))
    if html_end < 0:
        return f"{meta}{code}"
    return f"{code[: html_end + 1]}<head>{meta}</head>{code[html_end + 1 :]}"


def _parse_html_document(code: str) -> _DocumentParser:
    # Parse real tags and attributes once so validation does not rely on marker substrings.
    parser = _DocumentParser()
    parser.feed(code)
    parser.close()
    return parser


def _validate_html_structure(document: _DocumentParser) -> None:
    # Require one closed HTML document with a body before attempting any repair or render.
    for tag in ("html", "body"):
        if document.start_tags.get(tag) != 1 or document.end_tags.get(tag) != 1:
            raise GeneratedCodeError(
                f"Generated HTML must contain exactly one complete <{tag}> element."
            )


def _validate_remote_assets(document: _DocumentParser) -> None:
    # Reject executable resources outside the two HTTPS CDN origins constrained by the CSP.
    rejected = sorted(
        asset
        for asset in document.remote_assets
        if not _is_approved_remote_asset(asset)
    )
    if rejected:
        raise PolicyViolationError(
            "Generated HTML loads an unapproved remote script or stylesheet: "
            f"{rejected[0]}"
        )


def _validate_executable_script_reliability(code: str) -> None:
    # Treat APIs blocked by the CSP or destructive to the document as repairable code errors.
    for script in _SCRIPT_BLOCK.finditer(code):
        if _SRC_ATTRIBUTE.search(script.group("attrs")):
            continue
        executable = _mask_js_non_code(script.group("body"))
        if _UNRELIABLE_SCRIPT_APIS.search(executable):
            raise GeneratedCodeError(
                "Generated HTML uses eval, new Function, or document.write; dynamic code "
                "evaluation is blocked by the platform CSP and document replacement is unsupported."
            )


def _validate_counter_loops(code: str) -> None:
    # Reject obvious counter-direction mistakes that can freeze the preview iframe.
    bad_loop = _find_nonterminating_counter_loop(code)
    if bad_loop:
        raise GeneratedCodeError(
            "Generated HTML contains a counter loop whose update moves away from its "
            f"stopping condition: {bad_loop}"
        )


def _ensure_required_runtime(
    code: str,
    document: _DocumentParser,
    required_marker: str,
) -> str:
    # Inject p5 when absent while accepting any approved model-selected runtime version.
    if required_marker == "p5":
        if not any(_KNOWN_P5_URL.fullmatch(asset) for asset in document.remote_assets):
            return _inject_into_head(code, f'<script src="{P5_SCRIPT}"></script>')
        return code
    if required_marker == "reveal":
        if not any(_KNOWN_REVEAL_SCRIPT_URL.fullmatch(asset) for asset in document.remote_assets):
            raise GeneratedCodeError("Generated HTML is missing the approved Reveal.js runtime.")
        return code
    raise GeneratedCodeError(f"Generated HTML requires an unknown runtime: {required_marker}.")


def _find_nonterminating_counter_loop(code: str) -> str | None:
    # Locate the first obvious counter-direction mistake in executable inline JavaScript.
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


def _prepare_interactive_math(code: str) -> str:
    # Apply platform-owned math resources only when the lesson exposes LaTeX to learners.
    if not _has_visible_latex(code):
        return code
    code = _ensure_katex_assets(code)
    return _ensure_global_math_typesetting(code)


def _has_visible_latex(code: str) -> bool:
    # Check visible document text so formulas inside scripts and examples do not trigger KaTeX.
    parser = _VisibleTextParser()
    parser.feed(code)
    return _VISIBLE_LATEX.search(" ".join(parser.text)) is not None


def _ensure_katex_assets(code: str) -> str:
    # Inject only missing KaTeX files and match an existing version/CDN when possible.
    document = _parse_html_document(code)
    assets = {
        "css": next((url for url in sorted(document.remote_assets) if _katex_asset_kind(url) == "css"), None),
        "js": next((url for url in sorted(document.remote_assets) if _katex_asset_kind(url) == "js"), None),
        "auto": next((url for url in sorted(document.remote_assets) if _katex_asset_kind(url) == "auto"), None),
    }
    if all(assets.values()):
        return code

    template = _katex_asset_template(next((url for url in assets.values() if url), None))
    missing_markup = "\n".join(
        item
        for item in (
            f'<link rel="stylesheet" href="{template["css"]}">' if not assets["css"] else "",
            f'<script src="{template["js"]}"></script>' if not assets["js"] else "",
            f'<script src="{template["auto"]}"></script>' if not assets["auto"] else "",
        )
        if item
    )
    if missing_markup.strip():
        code = _inject_into_head(code, missing_markup)
    return code


def _is_approved_remote_asset(url: str) -> bool:
    # Allow optional lesson libraries without opening arbitrary network origins.
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in _APPROVED_CDN_HOSTS


def _katex_asset_kind(url: str) -> str | None:
    # Identify which KaTeX file a URL provides without imposing a version.
    if not _KNOWN_KATEX_URL.fullmatch(url):
        return None
    lower_url = url.lower()
    if lower_url.endswith("katex.min.css"):
        return "css"
    if lower_url.endswith("katex.min.js"):
        return "js"
    return "auto"


def _katex_asset_template(existing_url: str | None) -> dict[str, str]:
    # Build missing KaTeX URLs from the first model-selected version when available.
    if existing_url:
        jsdelivr_match = re.match(
            r"(https://cdn\.jsdelivr\.net/npm/katex@[^/]+)/dist/", existing_url, re.IGNORECASE
        )
        cdnjs_match = re.match(
            r"(https://cdnjs\.cloudflare\.com/ajax/libs/KaTeX/[^/]+)/", existing_url,
            re.IGNORECASE,
        )
        if jsdelivr_match:
            root = jsdelivr_match.group(1) + "/dist/"
            return {
                "css": root + "katex.min.css",
                "js": root + "katex.min.js",
                "auto": root + "contrib/auto-render.min.js",
            }
        if cdnjs_match:
            root = cdnjs_match.group(1) + "/"
            return {
                "css": root + "katex.min.css",
                "js": root + "katex.min.js",
                "auto": root + "contrib/auto-render.min.js",
            }
    return {
        "css": KATEX_STYLESHEET,
        "js": KATEX_SCRIPT,
        "auto": KATEX_AUTO_RENDER_SCRIPT,
    }


def _ensure_global_math_typesetting(code: str) -> str:
    # Add a trusted document-wide typesetting pass unless executable lesson code already has one.
    executable_scripts = "\n".join(
        _mask_js_non_code(script.group("body"))
        for script in _SCRIPT_BLOCK.finditer(code)
        if not _SRC_ATTRIBUTE.search(script.group("attrs"))
    )
    if _GLOBAL_MATH_RENDER.search(executable_scripts):
        return code

    return _inject_before_body_end(code, _KATEX_TYPESET_SCRIPT)


def _inject_into_head(code: str, markup: str) -> str:
    # Place platform-owned runtime assets in head without requiring model regeneration.
    lowered = code.lower()
    head_end = lowered.find(">", lowered.find("<head"))
    if head_end >= 0:
        return f"{code[: head_end + 1]}{markup}\n{code[head_end + 1 :]}"
    html_end = lowered.find(">", lowered.find("<html"))
    return f"{code[: html_end + 1]}<head>{markup}</head>{code[html_end + 1 :]}"


def _inject_before_body_end(code: str, markup: str) -> str:
    # Place platform-owned startup code before the document closes.
    body_end = code.lower().rfind("</body>")
    return f"{code[:body_end]}{markup}\n{code[body_end:]}"


def _mask_js_non_code(script: str) -> str:
    # Mask comments and literals so lesson text is not mistaken for executable JavaScript.
    masked = list(script)

    def hide(index: int) -> None:
        masked[index] = "\n" if script[index] == "\n" else " "

    def mask_comment(index: int) -> int:
        multiline = script[index + 1] == "*"
        hide(index)
        hide(index + 1)
        index += 2
        while index < len(script):
            if not multiline and script[index] == "\n":
                return index
            closing = (
                multiline
                and script[index] == "*"
                and index + 1 < len(script)
                and script[index + 1] == "/"
            )
            hide(index)
            index += 1
            if closing:
                hide(index)
                return index + 1
        return index

    def mask_string(index: int) -> int:
        delimiter = script[index]
        hide(index)
        index += 1
        while index < len(script):
            current = script[index]
            if current == "\\":
                hide(index)
                index += 1
                if index < len(script):
                    hide(index)
                    index += 1
                continue
            if (
                delimiter == "`"
                and current == "$"
                and index + 1 < len(script)
                and script[index + 1] == "{"
            ):
                hide(index)
                hide(index + 1)
                index = scan_code(index + 2, brace_depth=1)
                continue
            hide(index)
            index += 1
            if current == delimiter:
                return index
        return index

    def scan_code(index: int, brace_depth: int | None = None) -> int:
        while index < len(script):
            current = script[index]
            if current in {"'", '"', "`"}:
                index = mask_string(index)
                continue
            if (
                current == "/"
                and index + 1 < len(script)
                and script[index + 1] in {"/", "*"}
            ):
                index = mask_comment(index)
                continue
            if brace_depth is not None:
                if current == "{":
                    brace_depth += 1
                elif current == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        hide(index)
                        return index + 1
            index += 1
        return index

    scan_code(0)
    return "".join(masked)
