from functools import lru_cache
from html import escape
from pathlib import Path

from backend.app.lessons.formats.slides.spec import (
    BulletsBlock,
    CalloutBlock,
    ComparisonBlock,
    EquationBlock,
    FractionModelBlock,
    ProcessBlock,
    SlideBlock,
    SlidesLessonSpec,
    StatementBlock,
    StepsBlock,
)
from backend.app.lessons.render.html import (
    REVEAL_CORE_STYLESHEET,
    REVEAL_SCRIPT,
    REVEAL_THEME_STYLESHEET,
)

SLIDES_RUNTIME_VERSION = "slides-runtime.v1.1"
SLIDES_COMPILER_VERSION = "slides-compiler.v1.1"
_RUNTIME_PATH = Path(__file__).resolve().parent / "assets" / "v1" / "runtime.css"


@lru_cache(maxsize=1)
def _slides_styles() -> str:
    return _RUNTIME_PATH.read_text(encoding="utf-8")


def compile_slides(spec: SlidesLessonSpec) -> str:
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
  <style data-chalksmith-runtime="{SLIDES_RUNTIME_VERSION}">{_slides_styles()}</style>
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
</body>
</html>"""


def _render_slide(slide, number: int, total: int, grade_band: str) -> str:
    kind_label = slide.kind.replace("-", " ").title()
    if slide.kind == "comprehension-check":
        content = _render_check(slide)
    else:
        content = _render_blocks(slide.body)
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
    rendered = "".join(_render_block(block) for block in arranged)
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
    fraction_count = sum(isinstance(block, FractionModelBlock) for block in blocks)
    if len(blocks) == 2 and fraction_count == 1:
        arranged = sorted(blocks, key=lambda block: isinstance(block, FractionModelBlock))
        return "visual-split", arranged
    if len(blocks) == 2:
        return "split", blocks
    return "thirds", blocks


def _render_block(block: SlideBlock) -> str:
    if isinstance(block, StatementBlock):
        return f'<article class="cs-card cs-statement"><p>{escape(block.text)}</p></article>'
    if isinstance(block, BulletsBlock):
        items = "".join(f"<li>{escape(item)}</li>" for item in block.items)
        return f'<article class="cs-card cs-list"><ul>{items}</ul></article>'
    if isinstance(block, CalloutBlock):
        return (
            '<aside class="cs-card cs-callout">'
            f'<p class="cs-card__label">{escape(block.label)}</p>'
            f"<p>{escape(block.text)}</p></aside>"
        )
    if isinstance(block, EquationBlock):
        explanation = (
            f'<p class="cs-equation__explanation">{escape(block.explanation)}</p>'
            if block.explanation
            else ""
        )
        return (
            '<article class="cs-card cs-equation">'
            f'<p class="cs-equation__formula">$${escape(block.expression)}$$</p>'
            f"{explanation}</article>"
        )
    if isinstance(block, StepsBlock):
        items = "".join(f"<li>{escape(item)}</li>" for item in block.items)
        return f'<article class="cs-card cs-steps"><ol>{items}</ol></article>'
    if isinstance(block, ComparisonBlock):
        return _render_comparison(block)
    if isinstance(block, FractionModelBlock):
        return _render_fraction(block)
    if isinstance(block, ProcessBlock):
        return _render_process(block)
    raise TypeError(f"Unsupported slide block: {type(block).__name__}")


def _render_comparison(block: ComparisonBlock) -> str:
    left = "".join(f"<li>{escape(item)}</li>" for item in block.left_items)
    right = "".join(f"<li>{escape(item)}</li>" for item in block.right_items)
    return f"""
      <article class="cs-comparison">
        <div class="cs-card">
          <h3>{escape(block.left_title)}</h3>
          <ul>{left}</ul>
        </div>
        <div class="cs-card">
          <h3>{escape(block.right_title)}</h3>
          <ul>{right}</ul>
        </div>
      </article>"""


def _render_fraction(block: FractionModelBlock) -> str:
    segments = "".join(
        f'<span class="cs-fraction__segment{" is-filled" if index < block.numerator else ""}"></span>'
        for index in range(block.denominator)
    )
    label = block.label or f"{block.numerator}/{block.denominator}"
    return f"""
      <figure class="cs-card cs-fraction">
        <figcaption>{escape(label)}</figcaption>
        <span class="cs-fraction__bar" style="--cs-parts: {block.denominator}">{segments}</span>
        <strong>{block.numerator}/{block.denominator}</strong>
      </figure>"""


def _render_process(block: ProcessBlock) -> str:
    steps = "".join(
        f'<li><span>{index}</span><p>{escape(step)}</p></li>'
        for index, step in enumerate(block.steps, start=1)
    )
    return f'<article class="cs-card cs-process"><ol>{steps}</ol></article>'


def _render_check(slide) -> str:
    choices = "".join(
        f'<li class="{"is-answer" if index == slide.answer_index else ""}">'
        f'<span>{chr(65 + index)}</span><p>{escape(choice)}</p></li>'
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
