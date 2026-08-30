import ast
from textwrap import dedent

from backend.app.lessons.render.base import GeneratedCodeError


VIDEO_RUNTIME_VERSION = "manim-runtime.v1.1"
VIDEO_COMPILER_VERSION = "manim-compiler.v1.0"
VIDEO_RUNTIME_START = "# CHALKSMITH_VIDEO_RUNTIME_START"
VIDEO_RUNTIME_END = "# CHALKSMITH_VIDEO_RUNTIME_END"

_DIRECT_TEXT_OBJECTS = frozenset({"MarkupText", "MathTex", "Paragraph", "Tex", "Text", "Title"})
_RUNTIME_NAMES = frozenset(
    {
        "CS_COLORS",
        "CS_LATIN_FONT",
        "CS_CJK_FONT",
        "CS_TEXT_ROLES",
        "CS_MATH_ROLES",
        "CS_MATH_MIN_SCALE",
        "CS_TEX_TEMPLATE",
        "cs_text",
        "cs_math",
    }
)

VIDEO_RUNTIME_SOURCE = dedent(
    f'''
    {VIDEO_RUNTIME_START}
    CS_COLORS = {{
        "background": "#0c0a09",
        "surface": "#1c1917",
        "text": "#fafaf9",
        "muted": "#a8a29e",
        "accent": "#d97706",
        "accent_bright": "#f59e0b",
        "geometry": "#60a5fa",
        "positive": "#4ade80",
        "warning": "#fb7185",
    }}
    CS_LATIN_FONT = "Inter"
    CS_CJK_FONT = "Noto Sans CJK SC"
    CS_TEXT_ROLES = {{
        "title": (38, BOLD, 11.4),
        "subtitle": (26, NORMAL, 11.2),
        "body": (23, NORMAL, 10.8),
        "label": (19, NORMAL, 5.4),
        "caption": (17, NORMAL, 10.8),
    }}
    CS_MATH_ROLES = {{
        "display": (36, 11.4),
        "equation": (36, 10.8),
        "compact": (28, 6.0),
    }}
    CS_MATH_MIN_SCALE = 0.9
    CS_TEX_TEMPLATE = TexTemplate()


    def _cs_uses_cjk_font(value):
        return any(
            "\\u3400" <= character <= "\\u9fff"
            or "\\u3040" <= character <= "\\u30ff"
            or "\\uac00" <= character <= "\\ud7af"
            for character in value
        )


    def cs_text(value, role="body", color="text"):
        font_size, weight, max_width = CS_TEXT_ROLES[role]
        value = str(value)
        text = Text(
            value,
            font=CS_CJK_FONT if _cs_uses_cjk_font(value) else CS_LATIN_FONT,
            font_size=font_size,
            weight=weight,
            color=CS_COLORS[color],
            line_spacing=0.85,
        )
        if text.width > max_width:
            text.scale_to_fit_width(max_width)
        return text


    def cs_math(latex, role="equation", color="accent"):
        font_size, max_width = CS_MATH_ROLES[role]
        formula = MathTex(
            latex,
            tex_template=CS_TEX_TEMPLATE,
            font_size=font_size,
            color=CS_COLORS[color],
        )
        if formula.width > max_width:
            scale_factor = max_width / formula.width
            if scale_factor < CS_MATH_MIN_SCALE:
                raise ValueError(
                    "Chalksmith math expression is too wide; split it into multiple formulas."
                )
            formula.scale(scale_factor)
        return formula


    config.background_color = CS_COLORS["background"]
    {VIDEO_RUNTIME_END}
    '''
).strip()


def strip_video_runtime(source: str) -> str:
    """Remove a prior compiler-owned runtime before a lesson revision is regenerated."""
    lines = source.splitlines()
    starts = [index for index, line in enumerate(lines) if line.strip() == VIDEO_RUNTIME_START]
    ends = [index for index, line in enumerate(lines) if line.strip() == VIDEO_RUNTIME_END]
    if not starts and not ends:
        return source.strip()
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise GeneratedCodeError("Generated Manim code contains malformed platform style markers.")
    return "\n".join((*lines[: starts[0]], *lines[ends[0] + 1 :])).strip()


def compile_video(source: str) -> str:
    """Inject the audited Chalksmith visual runtime into model-authored Manim code."""
    clean_source = strip_video_runtime(source)
    try:
        tree = ast.parse(clean_source)
    except SyntaxError as error:
        raise GeneratedCodeError(
            f"Generated Manim code has invalid syntax: {error.msg}."
        ) from error

    _validate_style_contract(tree)
    insertion_line = _runtime_insertion_line(tree)
    lines = clean_source.splitlines()
    compiled = "\n".join(
        (
            *lines[:insertion_line],
            "",
            VIDEO_RUNTIME_SOURCE,
            "",
            *lines[insertion_line:],
        )
    ).strip()
    ast.parse(compiled)
    return compiled


def _runtime_insertion_line(tree: ast.Module) -> int:
    insertion_line = 0
    imports_manim = False
    body = tree.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        insertion_line = body[0].end_lineno or body[0].lineno
        body = body[1:]
    for node in body:
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            break
        insertion_line = node.end_lineno or node.lineno
        if isinstance(node, ast.ImportFrom) and node.module == "manim":
            imports_manim = any(alias.name == "*" for alias in node.names)
    if not imports_manim:
        raise GeneratedCodeError(
            "Generated Manim code must begin with `from manim import *`."
        )
    return insertion_line


def _validate_style_contract(tree: ast.Module) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            called_name = None
            if isinstance(node.func, ast.Name):
                called_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called_name = node.func.attr
            if called_name in _DIRECT_TEXT_OBJECTS:
                raise GeneratedCodeError(
                    f"Generated Manim code must use Chalksmith helpers instead of {called_name}()."
                )
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if node.id in _RUNTIME_NAMES or node.id.startswith("_cs_"):
                raise GeneratedCodeError(
                    "Generated Manim code redefines a platform style name."
                )
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and (
            node.name in _RUNTIME_NAMES or node.name.startswith("_cs_")
        ):
            raise GeneratedCodeError(
                "Generated Manim code redefines a platform style helper."
            )
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "config"
                    and target.attr == "background_color"
                ):
                    raise GeneratedCodeError(
                        "Generated Manim code must not override the platform background."
                    )
