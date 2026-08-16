INTERACTIVE_RULES = """
Return one complete HTML document using p5.js from cdn.jsdelivr.net or cdnjs.cloudflare.com.
Build a focused hands-on model with clear instructions, labeled controls, visible units, and
immediate feedback. Keep the scientific relationships accurate and choose sensible control
ranges. Make pointer interactions work after responsive scaling. The lesson must fit a 16:9
frame, remain legible on a classroom display, and be keyboard-accessible where practical.
When responsiveness is implemented only by resizing a p5.js canvas with CSS, use `mouseX` and
`mouseY` directly because p5.js already reports logical canvas coordinates; do not divide them
by a CSS scale factor. Apply inverse pointer transforms only when drawing coordinates are also
explicitly transformed with p5.js `scale()` or an equivalent canvas transform.
For every counter loop, make the update move toward its stopping condition: increment toward an
upper bound and decrement toward a lower bound. Never create an unbounded animation-frame loop.
Do not load other remote content and do not use eval, Function, document.write, inline event
attributes, forms, or a build step.
"""
