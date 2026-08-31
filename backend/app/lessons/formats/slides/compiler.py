import re
from html import escape
from pathlib import Path

from backend.app.lessons.formats.slides.presentation import render_block
from backend.app.lessons.formats.slides.spec import SlideSpec, SlidesLessonSpec


SLIDES_RUNTIME_VERSION = "slides-runtime.v2.0"
SLIDES_COMPILER_VERSION = "slides-compiler.v2.0"
REVEAL_CORE_STYLESHEET = (
    "https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.css"
)
REVEAL_THEME_STYLESHEET = (
    "https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/theme/black.min.css"
)
REVEAL_SCRIPT = "https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.js"
KATEX_STYLESHEET = "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css"
KATEX_SCRIPT = "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"
KATEX_AUTO_RENDER_SCRIPT = (
    "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"
)
_VISIBLE_MATH = re.compile(
    r"\$\$.+?\$\$|(?<!\\)\$(?!\$).+?(?<!\\)\$(?![\d$])|\\\(.+?\\\)|\\\[.+?\\\]",
    re.DOTALL,
)
REVEAL_FALLBACK_SCRIPT = """<script data-chalksmith-reveal-fallback>
window.addEventListener("load", () => {
  window.setTimeout(() => {
    const deck = document.querySelector(".reveal");
    const visibleSlide = deck?.querySelector(".slides > section.present") ??
      deck?.querySelector(".slides > section");
    if (!deck || !visibleSlide) return;
    const style = window.getComputedStyle(visibleSlide);
    const bounds = visibleSlide.getBoundingClientRect();
    if (!deck.classList.contains("ready") || style.display === "none" ||
        style.visibility === "hidden" || bounds.width === 0 || bounds.height === 0) {
      deck.classList.add("chalksmith-reveal-fallback");
    }
  }, 1000);
}, { once: true });
</script>"""
KATEX_TYPESET_SCRIPT = r"""<script data-chalksmith-katex>
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
  if (window.Reveal && typeof window.Reveal.layout === "function") {
    window.Reveal.layout();
  }
}, { once: true });
</script>"""
TABLE_FIT_SCRIPT = """<script data-chalksmith-table-fit>
window.addEventListener("load", () => {
  const fitTables = () => window.requestAnimationFrame(() => {
    document.querySelectorAll(".cs-table__viewport").forEach((viewport) => {
      const table = viewport.querySelector("table");
      if (!table || viewport.clientWidth === 0 || viewport.clientHeight === 0) return;
      table.style.setProperty("--cs-table-scale", "1");
      const widthScale = viewport.clientWidth / table.offsetWidth;
      const heightScale = viewport.clientHeight / table.offsetHeight;
      const scale = Math.max(0.1, Math.min(1, widthScale, heightScale));
      table.style.setProperty("--cs-table-scale", scale.toFixed(4));
    });
  });

  fitTables();
  document.fonts?.ready.then(fitTables);
  if (window.Reveal && typeof window.Reveal.on === "function") {
    window.Reveal.on("ready", fitTables);
    window.Reveal.on("slidechanged", fitTables);
    window.Reveal.on("resize", fitTables);
  }
  if (typeof ResizeObserver === "function") {
    const observer = new ResizeObserver(fitTables);
    document.querySelectorAll(".cs-table__viewport").forEach((viewport) => observer.observe(viewport));
  }
}, { once: true });
</script>"""

_ASSETS_PATH = Path(__file__).resolve().parent / "assets"
_STYLE_PATHS = tuple(
    _ASSETS_PATH / name
    for name in ("core.css", "layouts.css", "blocks.css", "custom.css")
)


def compile_slides(spec: SlidesLessonSpec) -> str:
    slides = "".join(
        _render_slide(slide, index + 1, len(spec.payload.slides), spec.grade_band)
        for index, slide in enumerate(spec.payload.slides)
    )
    # Detect math in rendered text so titles and every Block receive the same owned runtime.
    uses_katex = bool(_VISIBLE_MATH.search(slides))
    katex_head = (
        f'  <link rel="stylesheet" href="{KATEX_STYLESHEET}">\n'
        f'  <script defer src="{KATEX_SCRIPT}"></script>\n'
        f'  <script defer src="{KATEX_AUTO_RENDER_SCRIPT}"></script>\n'
        if uses_katex
        else ""
    )
    katex_typeset = KATEX_TYPESET_SCRIPT if uses_katex else ""
    styles = "\n".join(path.read_text(encoding="utf-8") for path in _STYLE_PATHS)
    return f"""<!doctype html>
<html lang="{escape(spec.language)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(spec.title)}</title>
  <link rel="stylesheet" href="{REVEAL_CORE_STYLESHEET}">
  <link rel="stylesheet" href="{REVEAL_THEME_STYLESHEET}">
{katex_head}  <style data-chalksmith-runtime="{SLIDES_RUNTIME_VERSION}">{styles}</style>
</head>
<body>
  <main class="reveal" aria-label="{escape(spec.title)}">
    <div class="slides">{slides}</div>
  </main>
  <script src="{REVEAL_SCRIPT}"></script>
  <script>
    Reveal.initialize({{
      embedded: true,
      hash: false,
      controls: true,
      progress: true,
      center: false,
      width: 1280,
      height: 720,
      margin: 0,
      minScale: 0.2,
      maxScale: 2
    }});
  </script>
  {katex_typeset}
  {TABLE_FIT_SCRIPT}
  {REVEAL_FALLBACK_SCRIPT}
</body>
</html>"""


def _render_slide(slide: SlideSpec, number: int, total: int, grade_band: str) -> str:
    label = (
        f'<p class="cs-eyebrow">{escape(slide.label)}</p>' if slide.label else ""
    )
    blocks = "".join(render_block(block) for block in slide.blocks)
    return f"""
      <section class="cs-slide cs-slide--{escape(slide.background)}" data-grade-band="{escape(grade_band)}">
        <header class="cs-slide__header">
          {label}
          <h2>{escape(slide.title)}</h2>
        </header>
        <div class="cs-slide__body cs-layout--{escape(slide.layout)}" data-chalksmith-layout="{escape(slide.layout)}">{blocks}</div>
        <footer class="cs-slide__footer">
          <span>Chalksmith</span>
          <span>{number} / {total}</span>
        </footer>
      </section>"""
