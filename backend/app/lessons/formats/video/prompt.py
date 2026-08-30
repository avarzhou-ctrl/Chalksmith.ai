from backend.app.lessons.render.manim import ALLOWED_MANIM_IMPORTS


_ALLOWED_IMPORTS = ", ".join(sorted(ALLOWED_MANIM_IMPORTS))

VIDEO_RULES = f"""
<DELIVERABLE>
Return Python for a Manim Community scene. Define exactly one Scene subclass named GeneratedScene
and begin with `from manim import *`. The platform injects its visual runtime after the import; call
the supplied helpers but never define, import, or override them.
</DELIVERABLE>

<TEACHING_SEQUENCE>
Organize the animation into a brief opening, two or three logically connected explanations, and a
recap. Prefer native geometric primitives, graphs, arrows, and concise labels. Build reasoning in
small visible steps and leave enough reading time before replacing or clearing an explanation.
</TEACHING_SEQUENCE>

<PLATFORM_STYLE>
Use `cs_text(value, role, color)` for every learner-visible prose string or label. Allowed text roles
are `title`, `subtitle`, `body`, `label`, and `caption`. Use only these color tokens: `text`, `muted`,
`accent`, `accent_bright`, `geometry`, `positive`, and `warning`. The platform selects Inter or Noto
Sans CJK SC, owns font sizes, constrains text width, and sets the chalkboard background. Never call
Text, MarkupText, Paragraph, Title, or set `config.background_color` directly. Use colors from
`CS_COLORS` for Manim geometry instead of Manim color constants or literal color values.
</PLATFORM_STYLE>

<MATH_RENDERING>
Use `cs_math(r"...", role, color)` for every symbolic mathematical expression. Allowed math roles
are `display`, `equation`, and `compact`. `display` and `equation` share one base font size; use
`display` for a standalone central formula and `equation` for grouped derivation steps. Reserve
`compact` only for short annotations attached to a diagram, never for the main teaching sequence.
Write valid LaTeX, including `\\frac`, superscripts, subscripts, roots, integrals, matrices, Greek
symbols, and relation symbols when appropriate. Keep each expression short enough to retain the
standard size; split a long equality chain or derivation into multiple `cs_math` objects arranged in
a VGroup instead of shrinking it. Never represent a fraction with a slash merely to avoid LaTeX.
Keep natural-language Chinese or English outside the formula as `cs_text`, and arrange prose with
the formula in a VGroup. Never call Tex or MathTex directly and never show raw LaTeX delimiters to
learners.
</MATH_RENDERING>

<LAYOUT_AND_SAFETY>
Keep all objects inside a 16:9 frame, preserve title and caption safe areas, and avoid simultaneous
clutter. Clear or transform obsolete objects before introducing the next teaching beat. Do not use
Code, images, or SVG assets. Do not access the network, filesystem, environment, subprocesses,
runtime internals, or user input. Imports are limited to these audited computation modules:
{_ALLOWED_IMPORTS}. Helper methods declared on GeneratedScene are allowed, including names that
start with one underscore; do not access underscore-prefixed attributes from libraries or runtime
objects.
</LAYOUT_AND_SAFETY>
"""
