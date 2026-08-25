"""Custom HTML Block contract, security policy, sanitization, and rendering."""

import re
from hashlib import sha1
from html import escape, unescape
from html.parser import HTMLParser
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition, BlockGuide

SCOPE_PLACEHOLDER = "__CS_SCOPE__"
MAX_HTML_LENGTH = 6000
PROMPT_HTML_LENGTH_TARGET = 5000
MAX_STYLE_LENGTH = 2500
MAX_NODES = 300
MAX_DEPTH = 12

ALLOWED_HTML_TAGS = frozenset(
    {
        "div", "span", "p", "article", "header", "footer", "aside",
        "figure", "figcaption", "ul", "ol", "li", "dl", "dt", "dd",
        "table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption",
        "h3", "h4", "h5", "strong", "em", "b", "i", "u", "s", "small",
        "code", "pre", "kbd", "samp", "var", "sub", "sup", "abbr", "mark",
        "time", "blockquote", "q", "del", "ins", "br", "hr", "style",
    }
)
ALLOWED_SVG_TAGS = frozenset(
    {
        "svg", "g", "defs", "marker", "path", "circle", "ellipse", "rect", "line",
        "polyline", "polygon", "text", "tspan", "title", "desc", "lineargradient",
        "radialgradient", "stop", "clippath", "textpath", "symbol", "pattern",
    }
)
FORBIDDEN_TAGS = frozenset(
    {
        "script", "iframe", "object", "embed", "applet", "form", "input", "button",
        "textarea", "select", "option", "label", "link", "meta", "base", "template",
        "slot", "noscript", "frame", "frameset", "audio", "video", "source", "track",
        "canvas", "img", "picture", "a", "map", "area", "dialog", "details",
        "foreignobject", "animate", "animatemotion", "animatetransform", "set",
        "filter", "feimage", "use", "image", "math",
    }
)
VOID_TAGS = frozenset({"br", "hr"})

_GLOBAL_ATTRIBUTES = frozenset({"class", "style", "id", "title", "lang", "dir", "role"})
_HTML_ATTRIBUTES = {
    "td": frozenset({"colspan", "rowspan", "headers"}),
    "th": frozenset({"colspan", "rowspan", "scope", "headers"}),
    "time": frozenset({"datetime"}),
    "ol": frozenset({"start", "reversed"}),
}
_SVG_ATTRIBUTES = frozenset(
    {
        "viewbox", "width", "height", "fill", "stroke", "stroke-width", "stroke-linecap",
        "stroke-linejoin", "stroke-dasharray", "stroke-dashoffset", "fill-opacity",
        "stroke-opacity", "opacity", "d", "cx", "cy", "r", "rx", "ry", "x", "y", "dx",
        "dy", "x1", "y1", "x2", "y2", "fx", "fy", "points", "transform", "text-anchor",
        "dominant-baseline", "alignment-baseline", "font-size", "font-weight",
        "font-family", "font-style", "letter-spacing", "offset", "stop-color",
        "stop-opacity", "gradientunits", "gradienttransform", "spreadmethod",
        "marker-start", "marker-mid", "marker-end", "markerwidth", "markerheight",
        "markerunits", "refx", "refy", "orient", "preserveaspectratio", "patternunits",
        "clippathunits", "clip-path", "clip-rule", "fill-rule", "vector-effect",
        "paint-order", "shape-rendering", "text-rendering", "xmlns", "pathlength",
    }
)
# HTMLParser lowercases names; canonical spelling keeps artifacts readable by XML tools.
_SVG_CASED_NAMES = {
    "lineargradient": "linearGradient",
    "radialgradient": "radialGradient",
    "clippath": "clipPath",
    "textpath": "textPath",
    "viewbox": "viewBox",
    "preserveaspectratio": "preserveAspectRatio",
    "gradientunits": "gradientUnits",
    "gradienttransform": "gradientTransform",
    "spreadmethod": "spreadMethod",
    "markerwidth": "markerWidth",
    "markerheight": "markerHeight",
    "markerunits": "markerUnits",
    "refx": "refX",
    "refy": "refY",
    "patternunits": "patternUnits",
    "clippathunits": "clipPathUnits",
    "pathlength": "pathLength",
}
ALLOWED_CSS_PROPERTIES = frozenset(
    {
        "color", "background", "background-color", "background-image", "border",
        "border-top", "border-right", "border-bottom", "border-left", "border-color",
        "border-style", "border-width", "border-radius", "box-shadow", "outline",
        "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
        "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
        "display", "flex", "flex-direction", "flex-wrap", "flex-grow", "flex-shrink",
        "flex-basis", "order", "gap", "row-gap", "column-gap", "grid-template-columns",
        "grid-template-rows", "grid-template-areas", "grid-area", "grid-column",
        "grid-row", "grid-auto-flow", "grid-auto-rows", "grid-auto-columns",
        "align-items", "align-content", "align-self", "justify-items",
        "justify-content", "justify-self", "place-items", "place-content",
        "width", "min-width", "max-width", "height", "min-height", "max-height",
        "aspect-ratio", "box-sizing", "overflow", "overflow-x", "overflow-y",
        "font-size", "font-weight", "font-family", "font-style", "font-variant",
        "line-height", "letter-spacing", "word-spacing", "text-align",
        "text-transform", "text-decoration", "text-shadow", "white-space",
        "word-break", "overflow-wrap", "vertical-align", "list-style",
        "list-style-type", "list-style-position", "opacity", "transform",
        "transform-origin", "writing-mode", "border-collapse", "border-spacing",
        "table-layout", "fill", "stroke", "stroke-width", "stroke-dasharray",
        "stroke-linecap", "text-anchor", "dominant-baseline",
    }
)

_BANNED_ATTRIBUTES = frozenset({"href", "src", "srcset", "xlink:href", "formaction"})
_CLASS_TOKEN = re.compile(r"^[A-Za-z][\w-]*$")
_IDENTIFIER = re.compile(r"^[A-Za-z][\w-]*$")
_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_CSS_CLASS_SELECTOR = re.compile(r"\.([A-Za-z][\w-]*)")
_CSS_ID_SELECTOR = re.compile(r"#([A-Za-z][\w-]*)")
_SELECTOR_CHARACTERS = re.compile(r"^[\w .#>+~:()\[\]\"'=^$*|-]+$")
_LOCAL_REFERENCE = re.compile(r"url\(\s*['\"]?#([A-Za-z_][\w-]*)['\"]?\s*\)")
_BLOCKED_VALUE = re.compile(r"url\(|expression\(|javascript:|@import|\\", re.IGNORECASE)
_FORBIDDEN_SELECTOR_TARGETS = ("html", "body", ":root", ".reveal", ".cs-")


def allowlist_prompt() -> str:
    """Keep the generation rules and the validator on one source of truth."""
    svg_tags = ", ".join(
        sorted(_SVG_CASED_NAMES.get(tag, tag) for tag in ALLOWED_SVG_TAGS)
    )
    forbidden = ", ".join(sorted(FORBIDDEN_TAGS))
    return (
        "Write the markup for a 16:9 slot the compiler sizes and centers; the block always "
        "occupies the slide body alone. Only these are kept:\n"
        "- Standard text, list, and table elements plus div, span, figure, and figcaption.\n"
        f"- Inline SVG for drawings: {svg_tags}.\n"
        "- One <style> element whose selectors the compiler automatically scopes to this "
        "block, and style attributes. Class names and ids are automatically namespaced. "
        "Layout, spacing, color, border, transform, and "
        "typography properties are kept; position, z-index, float, animation, filter, and "
        "url() to anything but a local #id are removed.\n"
        f"Never use: {forbidden}. Never use event handlers, href, src, or any external "
        "resource; the artifact must render offline. Reference gradients and markers with "
        "url(#id) and the compiler rewrites the id.\n"
        "Inherit the deck theme with var(--cs-text), var(--cs-muted), var(--cs-accent), "
        "var(--cs-accent-soft), var(--cs-surface), var(--cs-surface-raised), "
        "var(--cs-border), and var(--cs-success); add other colors only when the color "
        "itself carries meaning, such as coding DNA bases or charge signs. Size text in rem "
        f"and keep the markup under {PROMPT_HTML_LENGTH_TARGET} characters so validation has "
        f"a safe margin below the {MAX_HTML_LENGTH}-character hard limit."
    )


def sanitize_slide_html(html: str) -> str:
    """Return scoped, allowlisted markup or raise ValueError with a repairable reason."""
    if len(html) > MAX_HTML_LENGTH:
        raise ValueError(
            f"custom-html exceeds {MAX_HTML_LENGTH} characters ({len(html)} given)"
        )
    sanitizer = _SlideHtmlSanitizer()
    sanitizer.feed(html)
    sanitizer.close()
    sanitized = sanitizer.markup()
    if not visible_text(sanitized) and "<svg" not in sanitized:
        raise ValueError("custom-html contains no renderable content")
    return sanitized


def visible_text(html: str) -> str:
    """Learner-visible characters only, so style and markup never consume slide capacity."""
    without_style = re.sub(r"<style\b.*?</style\s*>", " ", html, flags=re.DOTALL | re.I)
    return unescape(" ".join(re.sub(r"<[^>]*>", " ", without_style).split()))


class _SlideHtmlSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        # Each level holds (source tag, emitted tag); None unwraps unsupported tags.
        self._stack: list[tuple[str, str | None]] = []
        self._style_buffer: list[str] = []
        self._in_style = False
        self._nodes = 0

    def markup(self) -> str:
        while self._stack:
            self._close_one()
        return "".join(self._parts)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in FORBIDDEN_TAGS:
            raise ValueError(f"custom-html may not contain <{tag}>")
        self._count_node()
        if tag == "style":
            self._in_style = True
            self._stack.append((tag, None))
            return
        in_svg = self._in_svg() or tag == "svg"
        allowed = tag in ALLOWED_SVG_TAGS if in_svg else tag in ALLOWED_HTML_TAGS
        if not allowed:
            self._stack.append((tag, None))
            return
        name = _SVG_CASED_NAMES.get(tag, tag) if in_svg else tag
        self._parts.append(f"<{name}{_clean_attributes(tag, attrs, in_svg=in_svg)}>")
        if tag not in VOID_TAGS:
            self._stack.append((tag, name))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "style":
            self._flush_style()
            self._in_style = False
        if not any(source == tag for source, _ in self._stack):
            return
        while self._stack:
            if self._close_one() == tag:
                return

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self._style_buffer.append(data)
            return
        self._parts.append(escape(data, quote=False))

    def _in_svg(self) -> bool:
        return any(source == "svg" for source, _ in self._stack)

    def _count_node(self) -> None:
        self._nodes += 1
        if self._nodes > MAX_NODES:
            raise ValueError(f"custom-html exceeds {MAX_NODES} elements")
        if len(self._stack) >= MAX_DEPTH:
            raise ValueError(f"custom-html nests deeper than {MAX_DEPTH} levels")

    def _close_one(self) -> str:
        source, emitted = self._stack.pop()
        if emitted:
            self._parts.append(f"</{emitted}>")
        return source

    def _flush_style(self) -> None:
        css = "".join(self._style_buffer)
        self._style_buffer = []
        if not css.strip():
            return
        if len(css) > MAX_STYLE_LENGTH:
            raise ValueError(f"custom-html CSS exceeds {MAX_STYLE_LENGTH} characters")
        scoped = _scope_stylesheet(css)
        if scoped:
            self._parts.append(f"<style>{scoped}</style>")


def _clean_attributes(
    tag: str, attrs: list[tuple[str, str | None]], *, in_svg: bool
) -> str:
    cleaned: list[str] = []
    for raw_name, raw_value in attrs:
        name = raw_name.lower()
        value = raw_value or ""
        if name.startswith("on") or name in _BANNED_ATTRIBUTES:
            raise ValueError(f"custom-html may not use the {name} attribute")
        if name == "class":
            tokens = [token for token in value.split() if _is_safe_class(token)]
            if tokens:
                scoped = " ".join(_scope_class(token) for token in tokens)
                cleaned.append(f'class="{escape(scoped)}"')
        elif name == "id":
            scoped = _scope_identifier(value)
            if scoped:
                cleaned.append(f'id="{escape(scoped)}"')
        elif name == "style":
            declarations = _clean_declarations(value)
            if declarations:
                cleaned.append(f'style="{escape(declarations)}"')
        elif _is_allowed_attribute(tag, name, in_svg=in_svg):
            resolved = _resolve_local_references(value)
            output_name = _SVG_CASED_NAMES.get(name, name) if in_svg else name
            cleaned.append(f'{output_name}="{escape(resolved)}"')
    return "".join(f" {attribute}" for attribute in cleaned)


def _is_allowed_attribute(tag: str, name: str, *, in_svg: bool) -> bool:
    if name in _GLOBAL_ATTRIBUTES:
        return True
    if in_svg:
        return name in _SVG_ATTRIBUTES
    return name in _HTML_ATTRIBUTES.get(tag, frozenset())


def _is_safe_class(token: str) -> bool:
    candidate = (
        token.removeprefix(f"{SCOPE_PLACEHOLDER}-")
        if token.startswith(f"{SCOPE_PLACEHOLDER}-")
        else token
    )
    if not _CLASS_TOKEN.match(candidate):
        return False
    return not candidate.startswith(("cs-", "reveal"))


def _scope_class(value: str) -> str:
    if value.startswith(f"{SCOPE_PLACEHOLDER}-"):
        return value
    return f"{SCOPE_PLACEHOLDER}-{value}"


def _scope_identifier(value: str) -> str:
    if value.startswith(SCOPE_PLACEHOLDER):
        return value
    if not _IDENTIFIER.match(value):
        return ""
    return f"{SCOPE_PLACEHOLDER}-{value}"


def _resolve_local_references(value: str) -> str:
    if _BLOCKED_VALUE.search(_LOCAL_REFERENCE.sub("", value)):
        raise ValueError("custom-html may not reference external or dynamic values")
    return _LOCAL_REFERENCE.sub(
        lambda match: f"url(#{_scope_identifier(match.group(1))})", value
    )


def _scope_stylesheet(css: str) -> str:
    css = _CSS_COMMENT.sub("", css)
    if "@" in css:
        raise ValueError("custom-html CSS may not use at-rules")
    rules: list[str] = []
    for chunk in css.split("}"):
        if not chunk.strip():
            continue
        selector, brace, body = chunk.partition("{")
        if not brace:
            raise ValueError("custom-html contains malformed CSS")
        declarations = _clean_declarations(body)
        if declarations:
            rules.append(f"{_scope_selector(selector)}{{{declarations}}}")
    return "".join(rules)


def _scope_selector(selector: str) -> str:
    scoped: list[str] = []
    for part in selector.split(","):
        candidate = " ".join(part.split())
        if not candidate:
            continue
        if not _SELECTOR_CHARACTERS.match(candidate):
            raise ValueError(f"custom-html CSS selector is not supported: {candidate}")
        lowered = candidate.lower()
        if any(target in lowered for target in _FORBIDDEN_SELECTOR_TARGETS):
            raise ValueError(
                "custom-html CSS may only style elements inside its own block"
            )
        already_scoped = candidate.startswith(f".{SCOPE_PLACEHOLDER}")
        candidate = _CSS_CLASS_SELECTOR.sub(
            lambda match: f".{_scope_class(match.group(1))}", candidate
        )
        candidate = _CSS_ID_SELECTOR.sub(
            lambda match: f"#{_scope_identifier(match.group(1))}", candidate
        )
        if already_scoped:
            scoped.append(candidate)
        else:
            scoped.append(f".{SCOPE_PLACEHOLDER} {candidate}")
    if not scoped:
        raise ValueError("custom-html contains a CSS rule without a selector")
    return ",".join(scoped)


def _clean_declarations(body: str) -> str:
    declarations: list[str] = []
    for declaration in body.split(";"):
        property_name, separator, value = declaration.partition(":")
        if not separator:
            continue
        property_name = property_name.strip().lower()
        value = value.replace("!important", "").strip()
        if property_name not in ALLOWED_CSS_PROPERTIES or not value:
            continue
        declarations.append(f"{property_name}:{_resolve_local_references(value)}")
    return ";".join(declarations)

_MATH_DELIMITERS = ("$", "\\(", "\\[")


class CustomHtmlBlock(StrictSpecModel):
    type: Literal["custom-html"]
    description: str = Field(min_length=1, max_length=120)
    html: str = Field(min_length=1, max_length=MAX_HTML_LENGTH)

    @model_validator(mode="after")
    def sanitize(self) -> "CustomHtmlBlock":
        self.html = sanitize_slide_html(self.html)
        return self


def custom_html_visible_length(block: CustomHtmlBlock) -> int:
    # description is an accessibility label, not on-slide copy.
    return len(visible_text(block.html))


def custom_html_uses_math(block: CustomHtmlBlock) -> bool:
    return any(delimiter in block.html for delimiter in _MATH_DELIMITERS)


def render_custom_html(block: CustomHtmlBlock) -> str:
    # The scope class isolates author CSS and element ids from every other block.
    scope = f"csx-{sha1(block.html.encode('utf-8')).hexdigest()[:10]}"
    markup = block.html.replace(SCOPE_PLACEHOLDER, scope)
    return (
        f'<figure class="cs-card cs-custom {scope}" '
        f'aria-label="{escape(block.description)}">{markup}</figure>'
    )


CUSTOM_BLOCKS = (
    BlockDefinition(
        CustomHtmlBlock,
        BlockGuide(
            "custom-html",
            "visual",
            "a representation that no other Block can express",
            "author-written HTML and inline SVG inside a compiler-sized, style-scoped slot",
            "the teaching representation is not a listed relationship, figure, or dataset; "
            "prefer any semantic Block that fits and use this as the only body block",
            '{"type":"custom-html","description":"Complementary DNA strands","html":'
            '"<style>.row{display:flex;gap:.5rem;align-items:center}'
            '.base{padding:.25rem .75rem;border-radius:.4rem;font-weight:700}'
            '.a{background:#ef4444;color:#fff}.t{background:#22c55e;color:#000}</style>'
            '<div class=\\"row\\"><span class=\\"base a\\">A</span>'
            '<span class=\\"base t\\">T</span></div>"}',
            standalone=True,
        ),
        render_custom_html,
    ),
)
