from html import escape
from pathlib import Path

from backend.app.lessons.formats.slides.blocks import (
    EquationBlock,
    SlideBlock,
    StepsBlock,
)
from backend.app.lessons.formats.slides.registry import (
    BLOCK_STYLE_GROUP_ORDER,
    VISUAL_BLOCK_TYPES,
    render_block,
    style_group_for,
)
from backend.app.lessons.formats.slides.spec import SlideSpec, SlidesLessonSpec

SLIDES_RUNTIME_VERSION = "slides-runtime.v1.1"
SLIDES_COMPILER_VERSION = "slides-compiler.v1.1"
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
# Typesetting after load lets deferred KaTeX scripts finish first; Reveal then
# remeasures the deterministic slide boxes that the rendered formulas resized.
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
_ASSETS_PATH = Path(__file__).resolve().parent / "assets" / "v1"
_CORE_STYLE_PATH = _ASSETS_PATH / "core.css"
_STYLE_GROUP_ORDER = (*BLOCK_STYLE_GROUP_ORDER, "comprehension")
_BLOCK_STYLE_PATHS = {
    group: _ASSETS_PATH / "blocks" / f"{group}.css" for group in _STYLE_GROUP_ORDER
}


def _slides_styles(style_groups: tuple[str, ...]) -> str:
    unknown_groups = set(style_groups) - _BLOCK_STYLE_PATHS.keys()
    if unknown_groups:
        names = ", ".join(sorted(unknown_groups))
        raise RuntimeError(f"Unknown Slides style groups: {names}")
    paths = (
        _CORE_STYLE_PATH,
        *(
            _BLOCK_STYLE_PATHS[group]
            for group in _STYLE_GROUP_ORDER
            if group in style_groups
        ),
    )
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def _required_assets(spec: SlidesLessonSpec) -> tuple[tuple[str, ...], bool]:
    style_groups: set[str] = set()
    uses_katex = False
    for slide in spec.payload.slides:
        if slide.kind == "comprehension-check":
            style_groups.add("comprehension")
            continue
        for block in slide.body:
            style_groups.add(style_group_for(block))
            uses_katex = uses_katex or isinstance(block, EquationBlock)
    ordered_groups = tuple(
        group for group in _STYLE_GROUP_ORDER if group in style_groups
    )
    return ordered_groups, uses_katex


def compile_slides(spec: SlidesLessonSpec) -> str:
    style_groups, uses_katex = _required_assets(spec)
    katex_head = (
        f'  <link rel="stylesheet" href="{KATEX_STYLESHEET}">\n'
        f'  <script defer src="{KATEX_SCRIPT}"></script>\n'
        f'  <script defer src="{KATEX_AUTO_RENDER_SCRIPT}"></script>\n'
        if uses_katex
        else ""
    )
    katex_typeset = KATEX_TYPESET_SCRIPT if uses_katex else ""
    slides = "".join(
        _render_slide(slide, index + 1, len(spec.payload.slides), spec.grade_band)
        for index, slide in enumerate(spec.payload.slides)
    )
    return f"""<!doctype html>
<html lang="{escape(spec.language)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(spec.title)}</title>
  <link rel="stylesheet" href="{REVEAL_CORE_STYLESHEET}">
  <link rel="stylesheet" href="{REVEAL_THEME_STYLESHEET}">
{katex_head}  <style data-chalksmith-runtime="{SLIDES_RUNTIME_VERSION}" data-style-groups="{','.join(style_groups)}">{_slides_styles(style_groups)}</style>
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
  {REVEAL_FALLBACK_SCRIPT}
</body>
</html>"""


def _render_slide(slide: SlideSpec, number: int, total: int, grade_band: str) -> str:
    kind_label = slide.kind.replace("-", " ").title()
    content = (
        _render_check(slide)
        if slide.kind == "comprehension-check"
        else _render_blocks(slide.body)
    )
    return f"""
      <section class="cs-slide cs-slide--{escape(slide.kind)}" data-grade-band="{grade_band}">
        <header class="cs-slide__header">
          <p class="cs-eyebrow">{escape(kind_label)}</p>
          <h2>{escape(slide.title)}</h2>
        </header>
        {content}
        <footer class="cs-slide__footer">
          <span>Chalksmith</span>
          <span>{number} / {total}</span>
        </footer>
      </section>"""


def _render_blocks(blocks: list[SlideBlock]) -> str:
    layout, arranged = _arrange_blocks(blocks)
    rendered = "".join(render_block(block) for block in arranged)
    # Reveal treats a section nested directly in a slide as a vertical child slide.
    return (
        f'<div class="cs-slide__body cs-layout--{layout}" '
        f'data-chalksmith-layout="{layout}">{rendered}</div>'
    )


def _arrange_blocks(blocks: list[SlideBlock]) -> tuple[str, list[SlideBlock]]:
    if len(blocks) == 1:
        return "single", blocks
    has_steps = any(isinstance(block, StepsBlock) for block in blocks)
    has_equation = any(isinstance(block, EquationBlock) for block in blocks)
    if len(blocks) == 2 and has_steps and has_equation:
        arranged = sorted(blocks, key=lambda block: not isinstance(block, StepsBlock))
        return "solution-split", arranged
    visual_count = sum(block.type in VISUAL_BLOCK_TYPES for block in blocks)
    if len(blocks) == 2 and visual_count == 1:
        arranged = sorted(blocks, key=lambda block: block.type in VISUAL_BLOCK_TYPES)
        return "visual-split", arranged
    if len(blocks) == 2:
        return "split", blocks
    return "thirds", blocks


def _render_check(slide: SlideSpec) -> str:
    choices = "".join(
        f'<li class="{"is-answer" if index == slide.answer_index else ""}">'
        f"<span>{chr(65 + index)}</span><p>{escape(choice)}</p></li>"
        for index, choice in enumerate(slide.choices or [])
    )
    answer = chr(65 + slide.answer_index) if slide.answer_index is not None else ""
    return f"""
      <div class="cs-check">
        <p class="cs-check__question">{escape(slide.question or "")}</p>
        <ol class="cs-check__choices">{choices}</ol>
        <aside class="cs-check__answer fragment">
          <p class="cs-card__label">Answer {answer}</p>
          <p>{escape(slide.explanation or "")}</p>
        </aside>
      </div>"""
