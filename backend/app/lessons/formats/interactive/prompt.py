INTERACTIVE_RULES = """
<DELIVERABLE>
Return one complete HTML document using p5.js from one of these approved paths:
https://cdn.jsdelivr.net/npm/p5@<version>/lib/p5.min.js or
https://cdnjs.cloudflare.com/ajax/libs/p5.js/<version>/p5.min.js.
Choose any compatible p5.js version needed by the lesson and keep that version unchanged; do not
mix p5.js versions. The platform validates the path and injects its default only when p5.js is
missing.
</DELIVERABLE>

<TEACHING_AND_INTERACTION>
Build a focused hands-on model with clear instructions, labeled controls, visible units, and
immediate feedback. Keep the scientific relationships accurate and choose sensible control
ranges. Make the lesson keyboard-accessible where practical.
</TEACHING_AND_INTERACTION>

<VISUAL_LAYOUT>
The lesson must fit a 16:9 frame and remain legible on a classroom display.
Keep text, labels, lines, plots, controls, feedback, and other visible elements within their
intended regions and free from unintended overlap with each other. Use consistent spacing,
alignment, margins, and visual density throughout the lesson; do not crowd one area while leaving
another unnecessarily sparse. Reflow, resize, or simplify content rather than allowing collisions
or cramped regions.
</VISUAL_LAYOUT>

<MATH_RENDERING>
When learner-visible mathematical notation is needed, load KaTeX CSS, katex.min.js, and
contrib/auto-render.min.js from the approved jsDelivr or cdnjs KaTeX paths. Any compatible KaTeX
version is allowed; use one version consistently for all three files and keep the URLs unchanged.
The platform default is KaTeX 0.16.9 only when all KaTeX files are missing; otherwise it supplies
missing files using the version and CDN already present. Typeset static formulas
after the DOM and KaTeX scripts are ready by calling `renderMathInElement(document.body, ...)`
directly, configuring auto-render to recognize `$...$`, `$$...$$`, `\\(...\\)`, and `\\[...\\]`.
After dynamically inserting or changing a formula, typeset that formula's container again with the
same delimiters; do not repeat typesetting on every animation frame when the expression has not
changed. Never leave raw LaTeX delimiters visible to learners. Use plain text or HTML for rapidly
changing numeric values that do not need mathematical typesetting.
</MATH_RENDERING>

<POINTER_COORDINATES>
Make pointer interactions work after responsive scaling.
When responsiveness is implemented only by resizing a p5.js canvas with CSS, use `mouseX` and
`mouseY` directly because p5.js already reports logical canvas coordinates; do not divide them
by a CSS scale factor. Apply inverse pointer transforms only when drawing coordinates are also
explicitly transformed with p5.js `scale()` or an equivalent canvas transform.
</POINTER_COORDINATES>

<STATE_AND_MODE_CHECKS>
Use one explicit source of truth for the active mode or tab. Every mode switch must update its
active control, corresponding HTML panel, and a deliberate p5.js canvas state or render branch;
do not leave two lesson modes with accidentally identical canvas output. Ensure draw() reads the
current mode and continues running after every switch.

Before returning the code, trace the initial state and every mode, tab, button, and input handler.
Verify that each referenced function and DOM id exists, each state value reaches the render logic,
and each branch uses valid p5.js APIs with compatible arguments. Do not name variables or function
parameters after p5.js functions that the same scope calls, such as vertex, line, text, image,
map, color, or select. Check that switching through every mode in sequence cannot throw an
exception, freeze draw(), or leave visible text, controls, feedback, and the canvas out of sync.
</STATE_AND_MODE_CHECKS>

<RUNTIME_SAFETY>
For every counter loop, make the update move toward its stopping condition: increment toward an
upper bound and decrement toward a lower bound. Never create an unbounded animation-frame loop.
</RUNTIME_SAFETY>

<SECURITY_RULES>
Load scripts and styles only over HTTPS from cdn.jsdelivr.net or cdnjs.cloudflare.com. Prefer p5.js
and the optional KaTeX assets above, but another library from those CDNs is allowed when it is
necessary for the lesson. Avoid eval, Function, and document.write because the platform CSP blocks
dynamic code evaluation and document replacement makes lessons unreliable. Do not require a build
step.
</SECURITY_RULES>
"""
