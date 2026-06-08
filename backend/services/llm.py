#!/usr/bin/env python3
"""
Course/Slide Generator using various LLM providers.

Supports:
- Models: gpt-* (OpenAI), glm-* (ZhipuAI), deepseek, gemini-* (Google), ark-deepseek-* (ARK)
- Formats: manim, remotion, reveal.js, p5.js
- Output: to specified file

Environment variables required:
- OPENAI_API_KEY: For gpt-* models
- ZAI_API_KEY: For glm-* models
- DEEPSEEK_API_KEY: For deepseek models
- GEMINI_API_KEY: For gemini-* models
- ARK_API_KEY: For ark-deepseek-* models
"""

import os
import sys
import time
from rich.console import Console
from typing import Optional
from dotenv import load_dotenv

console = Console()
load_dotenv()  # Load environment variables from .env file if present

LLM_REGION_ERROR_MESSAGE = (
    "This AI model is not available from your current country or region. "
    "Please try a different model, connect from a supported region, or contact Chalksmith support if this seems wrong."
)


class LLMAccessError(RuntimeError):
    """Raised when an LLM provider blocks access because of location or account availability."""


def is_region_access_error(error: Exception) -> bool:
    error_parts = [str(error)]

    for attr in ("message", "body", "response"):
        value = getattr(error, attr, None)
        if value:
            error_parts.append(str(value))

    error_text = " ".join(error_parts).lower()
    region_error_patterns = [
        "unsupported_country_region_territory",
        "unsupported country",
        "unsupported region",
        "country, region, or territory",
        "not available in your country",
        "not available in your region",
        "not supported in your country",
        "user location is not supported",
        "location is not supported",
        "geographic location",
        "geo-restricted",
        "regional restrictions",
    ]

    return any(pattern in error_text for pattern in region_error_patterns)


def raise_llm_error(error: Exception):
    if is_region_access_error(error):
        raise LLMAccessError(LLM_REGION_ERROR_MESSAGE) from error

    raise error

# -----------------------------------------------------------------------------
# LLM PROVIDER IMPLEMENTATIONS
# -----------------------------------------------------------------------------

def generate_content_with_openai(topic: str, model: str, format_type: str, raw_prompt: str = None) -> str:
    """Generate content using OpenAI API (gpt-* models)."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key)

    prompt = raw_prompt if raw_prompt else get_prompt_for_format(topic, format_type)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert educational content creator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content


def generate_content_with_zhipuai(topic: str, model: str, format_type: str, raw_prompt: str = None) -> str:
    """Generate content using ZhipuAI API (glm-* models)."""
    import httpx
    from openai import OpenAI

    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        api_key = os.getenv("ZHIPUAI_API_KEY")
        if not api_key:
            raise ValueError("ZAI_API_KEY environment variable not set")

    # Bypass internal proxies for direct API communication
    os.environ['NO_PROXY'] = 'open.bigmodel.cn'

    client = OpenAI(
        api_key=api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    )

    prompt = raw_prompt if raw_prompt else get_prompt_for_format(topic, format_type)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert educational content creator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content


def generate_content_with_deepseek(topic: str, model: str, format_type: str, raw_prompt: str = None) -> str:
    """Generate content using DeepSeek API."""
    import httpx
    from openai import OpenAI

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable not set")

    # Bypass internal proxies for direct API communication
    os.environ['NO_PROXY'] = 'api.deepseek.com'

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    prompt = raw_prompt if raw_prompt else get_prompt_for_format(topic, format_type)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert educational content creator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content


def generate_content_with_gemini(topic: str, model: str, format_type: str, raw_prompt: str = None) -> str:
    """Generate content using Google Gemini API."""
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    # Configure environment for underlying libraries (httpx/grpc) if proxy is active
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    if proxy:
        os.environ["HTTPS_PROXY"] = proxy
        os.environ["HTTP_PROXY"] = proxy

    # Initialize client (relying on env vars for proxy)
    client = genai.Client(api_key=api_key)

    prompt = raw_prompt if raw_prompt else get_prompt_for_format(topic, format_type)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text

def generate_content_with_ark(topic: str, model: str, format_type: str, raw_prompt: str = None) -> str:
    """Generate content using ARK Engine (DeepSeek 3.2)."""
    from volcenginesdkarkruntime import Ark

    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        raise ValueError("ARK_API_KEY environment variable not set")

    # Bypass internal proxies for direct API communication
    os.environ['NO_PROXY'] = 'ark.cn-beijing.volces.com'

    # Adjust timeout and reasoning flags based on model capability
    if model == "ark-deepseek-reasoner":
        thinking_type = "enabled"
        timeout = 1800  # 30 minutes for deep reasoning
    else:  # ark-deepseek-chat
        thinking_type = "disabled"
        timeout = 300  # 5 minutes for standard chat

    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
        timeout=timeout,
    )

    prompt = raw_prompt if raw_prompt else get_prompt_for_format(topic, format_type)

    # Use the actual model ID for DeepSeek 3.2
    response = client.chat.completions.create(
        model="deepseek-v3-2-251201",
        messages=[
            {"role": "system", "content": "You are an expert educational content creator."},
            {"role": "user", "content": prompt}
        ],
        thinking={"type": thinking_type},
        temperature=0.7
    )

    return response.choices[0].message.content

# -----------------------------------------------------------------------------
# PROMPT GENERATION
# -----------------------------------------------------------------------------

def get_prompt_for_format(topic: str, format_type: str) -> str:

    """Generate appropriate prompt based on output format."""
    
    # Load official documentation context if available
    manim_knowledge = ""
    if format_type == "manim":
        try:
            doc_path = os.path.join(os.path.dirname(__file__), "manim_docs.txt")
            if os.path.exists(doc_path):
                with open(doc_path, "r") as f:
                    # Provide snippet of official docs to help LLM avoid hallucinations
                    # Limit to 2000 chars to avoid hitting model token limits
                    manim_knowledge = f"OFFICIAL MANIM COMMUNITY API REFERENCE (v0.18+):\n{f.read()[:2000]}\n"
        except Exception:
            # If documentation is missing or unreadable, proceed with base prompt
            pass
    
    base_prompt = f"""You are an expert educational content creator. 
    
    Create a concise summary of the key concepts and structure covered in the lesson in 2-3 sentences/bullet points.
    The summary should be factual and capture the essence of the lesson content.
    After the summary, type "---CODE_START---" on a new line, then output the complete, executable source code for the lesson.
    """

    if format_type == "remotion":
        return f"""
Create a structured JSON object to be used as props for a Remotion video template to teach "{topic}".

{base_prompt}

STRICT REQUIREMENTS:
- **Output ONLY valid JSON for the code section.** Do not include markdown code fences (```json ... ```), explanations, or any text outside the JSON object within the code section.
- **KaTeX Support:** Use standard LaTeX for ALL mathematical expressions. Wrap them in double backslashes (e.g., "\\\\frac{{a}}{{b}}") to ensure JSON compatibility.
- **Visual Pacing:** Break the lesson into logical scenes (Introduction, Concepts, Examples, Summary).
- **Aesthetic:** Clean, high-contrast dark theme (Black background, White text).
- **Deterministic Animation:** Each scene can have a "physics" profile to control the animation feel.

JSON SCHEMA:
{{
  "title": "Lesson Title",
  "scenes": [
    {{
      "id": "unique-id",
      "type": "title | text | math | point_list",
      "content": "Main content",
      "physics": "bouncy | smooth | snappy",
      "durationInSeconds": 5
    }}
  ]
}}

CONTENT ACCURACY:
- Strictly ensure all scientific, mathematical, and historical information is factually correct.
- Verify equations and processes. Do not simplify to the point of falsehood.
"""
    elif format_type == "manim":
        return f"""
{manim_knowledge}

Create a COMPLETE, EXECUTABLE Python script using **Manim Community Edition (manim>=0.17)** to teach "{topic}".

{base_prompt}

STRICT REQUIREMENTS (must follow exactly):
- **STRICT STANDARD LIBRARY ONLY:** Use ONLY classes and methods available in standard Manim Community Edition. DO NOT use third-party plugins or hypothetical classes.
- **NO Hallucinations:** If you need a complex object (like a list), build it from primitives (`VGroup`, `Text`, etc.).
- Use **Manim Community Edition**, NOT legacy manimlib
- Import ONLY with: `from manim import *`
- Target the **Cairo renderer** (default)
- Code must run with: `manim -pql scene.py MainScene`
- Output ONLY valid Python code (no explanations, no markdown)

STRICT MANIM COMMUNITY DOCUMENTATION REFERENCE (v0.18+):
- **General Method**: Use `.animate` for transformations. Example: `square.animate.set_fill(WHITE, opacity=0.5)`
- **Color Gradients**: DO NOT use `.set_color_by_gradient()`. Use `Mobject.set_color_by_gradient` ONLY if manually defined. Standard way: `square.set_color([BLUE, GREEN])`.
- **Text & Math**: Use `Text("Hello World")` for simple text, `"\\\\frac{{a}}{{b}}"` for basic LaTeX, and `MathTex(r"x = y^2")` for standalone math.
- **Pacing**: Use `self.wait(1)` frequently for readability.
- **Scene Termination**: Ensure you clean up with `self.play(FadeOut(VGroup(*self.mobjects)))` at the end of sections.

GOLDEN WHITELIST (Use these ONLY):
- Shapes: `Circle`, `Rectangle`, `Square`, `Line`, `Arrow`, `DoubleArrow`, `Dot`, `Arc`, `Polygon`, `RoundedRectangle`, `Ellipse`, `Star`, `Triangle`.
- Text: `Text` (for normal text), `Tex` (for basic equations), `MathTex` (for complex equations), `Paragraph` (for long text).
- Groups/Layout: `VGroup`, `HGroup`, `Group`, `next_to`, `shift`, `scale`, `rotate`, `arrange`.
- Animations: `Create`, `Write`, `FadeIn`, `FadeOut`, `Transform`, `ReplacementTransform`, `GrowFromCenter`, `Indicate`, `Circumscribe`, `Wiggle`.
- Coordinate Systems: `Axes`, `NumberLine`, `NumberPlane`.

STRICT CODE STRUCTURE:
- **Indentation:** Use exactly 4 spaces for indentation. NO tabs.
- **Method Definitions:** Ensure all methods are defined at the class level (inside the class, but not nested inside other methods).
- **Execution:** Ensure `construct` calls these methods in order.

FORBIDDEN (do NOT use):
- `BulletList` (unless you define it yourself), `Capsule`, `Table`, `Code` (manim-community version).
- `.bend()`, `.point_at_angle()`, `.set_color_by_gradient()`.
- `TextMobject`, `TexMobject`, `ShowCreation`, `ApplyMethod`.
- `np.PI` (use `np.pi`).
- Any color NOT in: `BLUE`, `GREEN`, `YELLOW`, `RED`, `ORANGE`, `PURPLE`, `GOLD`, `TEAL`, `WHITE`, `BLACK`, `GRAY`, `BROWN`, `PINK`, `NAVY`.

REQUIRED API STYLE:
- Use `Text`, `MathTex`, `Paragraph`, `VGroup`, etc.
- Use `.animate` syntax for transformations
- Use `Create`, `Write`, `FadeIn`, `FadeOut`, `Transform`
- Use named colors from the ALLOWED list above.

SCENE STRUCTURE:
- Define a class named `MainScene(Scene)`
- Use multiple logical sections (intro → explanation → summary)
- Clear pacing with `self.wait()`
- **Visual Diagrams:** For visual topics (e.g., geometry, biology, physics), create relevant diagrams using geometric primitives, arrows, and labels.
- **Layout Management:** Carefully arrange elements to ensure there is no overlap at all between text, shapes, and labels. Use `VGroup`, `next_to`, and `shift` to ensure everything is clearly separated and legible.
- **TRANSITIONS:** Clean up the screen between sections. Fade out (`FadeOut`) or remove (`Uncreate`) objects that are no longer relevant before introducing new concepts. Prevent screen clutter.

ROBUSTNESS CHECK:
- If you are about to use a deprecated or legacy Manim API,
  STOP and replace it with the correct Manim Community equivalent.

CONTENT ACCURACY:
- **Strictly ensure** all scientific, mathematical, and historical information is factually correct and reflects **modern scientific consensus** (e.g., for biology, use modern 3-domain or 6-kingdom classifications if appropriate, unless the specific 5-kingdom Whittaker system is requested).
- **Verify** equations, chemical formulas, and biological processes. Do not simplify to the point of falsehood.
- **Detailed Diagrams:** Ensure diagrams are anatomically or structurally representative of the topic (e.g., show proper cell organelles, correct molecular geometry, or accurate physics vectors).

Return ONLY the Python source code.
"""
    
    elif format_type == "reveal.js":
        return f"""Create a complete reveal.js HTML presentation to teach "{topic}".

{base_prompt}

GENERAL:
- Include complete HTML structure with reveal.js CDN links (use a modern version)
- Have multiple slides with clear progression

VISUAL DESIGN:
- **High Contrast:** Ensure text is easily readable against the background (e.g., avoid light gray on white).
- **Style:** Use a pleasant, professional color palette. Use colors to emphasize headers or specific sections.
- **Highlights:** **Highlight important terms** and keywords using distinct, contrasting colors or bolding to make them stand out.
- **Diagrams:** For visual topics (e.g., geometry, biology, physics), include relevant diagrams using inline SVG or CSS. Ensure diagrams are clear and accurately labeled.
- **Layout & Overlap:** Ensure there is **NO overlap** between text, diagrams, shapes, or colors. Use proper padding, margins, and alignment to keep elements distinct.

CONTENT STRUCTURE:
- **Definitions:** Explicitly define unclear, technical, or domain-specific terms (e.g., scientific jargon) either immediately when introduced or in a dedicated glossary slide.
- Use animations (fragments) and transitions effectively.
- Include code examples with syntax highlighting if relevant.
- Be a complete, self-contained HTML file.

CONTENT ACCURACY:
- **Strictly ensure** all scientific, mathematical, and historical information is factually correct and reflects **modern scientific consensus** (e.g., for biology, use modern 3-domain or 6-kingdom classifications if appropriate, unless the specific 5-kingdom Whittaker system is requested).
- **Verify** equations, chemical formulas, and biological processes. Do not simplify to the point of falsehood.
- **Detailed Diagrams:** Ensure diagrams (SVG/CSS) are anatomically or structurally representative of the topic (e.g., show proper cell organelles, correct molecular geometry, or accurate physics vectors).

Return ONLY the HTML code, no explanations."""

    elif format_type == "p5.js":
        return f"""Create a COMPLETE interactive p5.js visualization to teach "{topic}".

{base_prompt}

The code should:
- Include complete HTML structure with p5.js CDN
- Have interactive visual elements
- Include clear labels and explanations
- Use animations to demonstrate concepts
- Be visually appealing
- Be a complete, self-contained HTML file with embedded JavaScript

IMPORTANT:
- **Keep the code concise** to avoid hitting output token limits.
- Avoid excessive comments or extremely long text descriptions inside the code.
- Focus on the visual and interactive logic.

CONTENT ACCURACY:
- **Strictly ensure** all scientific, mathematical, and historical information is factually correct and reflects **modern scientific consensus** (e.g., for biology, use modern 3-domain or 6-kingdom classifications if appropriate, unless the specific 5-kingdom Whittaker system is requested).
- **Verify** physics simulations and mathematical logic. Do not simplify to the point of falsehood.
- **Detailed Visuals:** Ensure visualizations are anatomically or structurally representative of the topic (e.g., show proper cell organelles, correct molecular geometry, or accurate physics vectors).

Return ONLY the HTML code with embedded p5.js, no explanations."""

    else:
        raise ValueError(f"Unknown format: {format_type}")

# -----------------------------------------------------------------------------
# POST-PROCESSING & UTILITIES
# -----------------------------------------------------------------------------

def clean_code_fences(content: str) -> str:
    """Strip markdown code block syntax (```lang ... ```) from LLM output."""
    content = content.strip()

    # Handle leading fences (e.g., ```python, ```html)
    if content.startswith('```'):
        first_newline = content.find('\n')
        if first_newline != -1:
            content = content[first_newline + 1:]
        else:
            content = content[3:]

    # Handle trailing fences
    if content.rstrip().endswith('```'):
        content = content.rstrip()[:-3].rstrip()
    
    # Also clean up common trailing markers if they leak into the code section
    if "---CODE_END---" in content:
        content = content.split("---CODE_END---")[0].strip()

    return content

def detect_provider(model: str) -> str:
    """Map model names to their respective API providers."""
    if model.startswith("gpt-"):
        return "openai"
    elif model.startswith("glm-"):
        return "zhipuai"
    elif model.startswith("ark-deepseek-"):
        return "ark"
    elif model.startswith("deepseek"):
        return "deepseek"
    elif model.startswith("gemini-"):
        return "gemini"
    else:
        raise ValueError(f"Unknown model prefix: {model}. Supported: gpt-*, glm-*, deepseek*, gemini-*, ark-deepseek-*")

def _spinner(description: str):
    """Console-only status indicator for background tasks."""
    return console.status(description, spinner="dots")

# -----------------------------------------------------------------------------
# CORE GENERATION LOGIC
# -----------------------------------------------------------------------------

def parse_llm_response(content: str) -> dict:
    """Parses the raw LLM response into a summary and code."""
    content = clean_code_fences(content)
    if "---CODE_START---" in content:
        parts = content.split("---CODE_START---")
        return {
            "summary": parts[0].strip(),
            "code": parts[1].strip()
        }
    else:
        return {
            "summary": "Generated lesson.",
            "code": content.strip()
        }

def generate_lesson(topic: str, model: str, format_type: str, previous_code: str = None, edit_prompt: str = None) -> dict:
    """Entry point for both fresh generation and iterative editing."""
    if previous_code and edit_prompt:
        return get_edit_prompt(previous_code, topic, edit_prompt, format_type, model)

    provider = detect_provider(model)
    try:
        with _spinner(f"Generating lesson about '{topic}' using {model} ({provider}) in {format_type} format..."):
            time.sleep(0.1)
            if provider == "openai":
                content = generate_content_with_openai(topic, model, format_type)
            elif provider == "zhipuai":
                content = generate_content_with_zhipuai(topic, model, format_type)
            elif provider == "deepseek":
                content = generate_content_with_deepseek(topic, model, format_type)
            elif provider == "gemini":
                content = generate_content_with_gemini(topic, model, format_type)
            elif provider == "ark":
                content = generate_content_with_ark(topic, model, format_type)
            else:
                raise ValueError(f"Unknown provider: {provider}")
    except Exception as error:
        raise_llm_error(error)

    lesson = parse_llm_response(content)

    if format_type == "manim":
        lesson["code"] = ensure_manim_compatibility(lesson["code"])

    return lesson

def get_edit_prompt(current_code: str, original_prompt: str, edit_prompt: str, format_type: str, model: str) -> dict:
    """Constructs a targeted editing prompt to modify existing code."""
    
    # Detect if this is an automated fix (system-triggered) or a user-requested change
    is_auto_fix = "Traceback" in edit_prompt or "error" in edit_prompt.lower()
    
    if is_auto_fix:
        mode_instruction = f"""
        ### SELF-CORRECTION MODE ###
        The previous code generated for the topic "{original_prompt}" failed to run.
        Your goal is to FIX the code so it executes perfectly, while keeping the content focused on the original topic.
        Do NOT change the topic. Do NOT treat the error message as a new lesson topic.
        """
    else:
        mode_instruction = f"""
        ### USER EDIT MODE ###
        The user wants to modify the existing lesson about "{original_prompt}".
        Incorporate the requested changes while preserving the rest of the lesson structure.
        """

    base_instructions = f"""
    You are an expert code editor specializing in {format_type}. 
    {mode_instruction}

    Your task is to generate the COMPLETE edited code that incorporates the requested changes and SUMMARY of changes.
    Create a concise summary of the key concepts and structure covered in the edited lesson in 2-3 sentences/bullet points.
    The summary should be factual and capture the essence of the edited lesson.
    After the summary, type "---CODE_START---" on a new line, then output the complete, executable source code for the lesson.
    
    Guidelines:
    - Preserve all other functionality and structure not mentioned in the edit/fix request.
    - Ensure the code remains complete, valid, and executable.
    - Maintain the same coding style and conventions.
    """

    full_prompt = f"""
    {base_instructions}

    ORIGINAL TOPIC: {original_prompt}

    CURRENT CODE:
    {current_code}

    {"SYSTEM ERROR LOG (FIX THIS)" if is_auto_fix else "USER EDIT REQUEST"}: 
    {edit_prompt}
    
    Generate the COMPLETE {"corrected" if is_auto_fix else "edited"} code:
    """

    provider = detect_provider(model)
    try:
        with _spinner(f"Editing lesson using {model} ({provider})..."):
            time.sleep(0.1)
            if provider == "openai":
                content = generate_content_with_openai(original_prompt, model, format_type, raw_prompt=full_prompt)
            elif provider == "zhipuai":
                content = generate_content_with_zhipuai(original_prompt, model, format_type, raw_prompt=full_prompt)
            elif provider == "deepseek":
                content = generate_content_with_deepseek(original_prompt, model, format_type, raw_prompt=full_prompt)
            elif provider == "gemini":
                content = generate_content_with_gemini(original_prompt, model, format_type, raw_prompt=full_prompt)
            elif provider == "ark":
                content = generate_content_with_ark(original_prompt, model, format_type, raw_prompt=full_prompt)
            else:
                raise ValueError(f"Unknown provider: {provider}")
    except Exception as error:
        raise_llm_error(error)
    
    lesson = parse_llm_response(content)
    
    if format_type == "manim":
        lesson["code"] = ensure_manim_compatibility(lesson["code"])

    return lesson

# -----------------------------------------------------------------------------
# COMPATIBILITY LAYERS
# -----------------------------------------------------------------------------

def ensure_manim_compatibility(code: str) -> str:
    """Inject missing color definitions and fix common issues in Manim code."""
    
    # Common missing classes/methods compatibility
    extra_compat = [
        "class BulletList(VGroup):",
        "    def __init__(self, *items, **kwargs):",
        "        line_spacing = kwargs.pop('line_spacing', 0.5)",
        "        dot = '• '",
        "        mobjects = [Text(f'{dot}{item}', **kwargs) for item in items]",
        "        super().__init__(*mobjects)",
        "        self.arrange(DOWN, aligned_edge=LEFT, buff=line_spacing)",
        "",
        "def Capsule(**kwargs):",
        "    width = kwargs.pop('width', 2)",
        "    height = kwargs.pop('height', 1)",
        "    return RoundedRectangle(corner_radius=min(width, height)/2, width=width, height=height, **kwargs)",
        "",
        "# Legacy Compatibility for common LLM hallucinations",
        "TextMobject = Text",
        "TexMobject = Tex",
        "ShowCreation = Create",
        "ApplyMethod = lambda m, *args, **kwargs: m.animate.method(*args, **kwargs) if hasattr(m, 'animate') else m",
        "ReplacementTransform = Transform",
        "",
        "# Monkey-patch Line to prevent crashes on hallucinated .bend() method",
        "Line.bend = lambda self, *args, **kwargs: self",
        "Mobject.set_color_by_gradient = lambda self, *args, **kwargs: self",
        ""
    ]
    
    # Common colors that LLMs use but might be missing in Manim Community
    extra_colors = [
        'BROWN = "#8B4513"',
        'SANDY_BROWN = "#F4A460"',
        'MAGENTA = "#FF00FF"',
        'CYAN = "#00FFFF"',
        'DARK_GRAY = "#A9A9A9"',
        'LIGHT_GRAY = "#D3D3D3"',
        'PINK = "#FFC0CB"',
        'LIME = "#00FF00"',
        'MAROON = "#800000"',
        'NAVY = "#000080"',
        'OLIVE = "#808000"',
    ]
    
    compat_block = "\n# Compatibility layer for LLM-hallucinated colors and classes\n" + \
                   "\n".join(extra_colors) + "\n" + \
                   "\n".join(extra_compat) + "\n"

    # Ensure we don't double-inject if editing
    if "# Compatibility layer" in code:
        return code

    # Check for imports to insert after
    if "from manim import *" in code:
        parts = code.split("from manim import *")
        return parts[0] + "from manim import *" + compat_block + parts[1]
    elif "import manim" in code:
        parts = code.split("import manim")
        return parts[0] + "import manim" + compat_block + parts[1]
    else:
        # No standard import found, prepend compatibility block at the top
        return "from manim import *\n" + compat_block + "\n" + code
