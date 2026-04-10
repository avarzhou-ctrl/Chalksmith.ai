#!/usr/bin/env python3
"""
Course/Slide Generator using various LLM providers.

Supports:
- Models: gpt-* (OpenAI), glm-* (ZhipuAI), deepseek, gemini-* (Google), ark-deepseek-* (ARK)
- Formats: manim, reveal.js, p5.js
- Output: to specified file

Environment variables required:
- OPENAI_API_KEY: For gpt-* models
- ZAI_API_KEY: For glm-* models
- DEEPSEEK_API_KEY: For deepseek models
- GEMINI_API_KEY: For gemini-* models
- ARK_API_KEY: For ark-deepseek-* models
"""

import argparse
import os
import re
import subprocess
import sys
import time
from rich.console import Console
from typing import Optional
from dotenv import load_dotenv

console = Console()
load_dotenv()  # Load environment variables from .env file if present

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

    # Disable proxy for ZhipuAI
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

    # Disable proxy for DeepSeek
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

    # Check for proxy settings
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    if proxy:
        print(f"Using proxy for Gemini: {proxy}", file=sys.stderr)
        # Ensure standard env vars are set for underlying libraries (httpx/grpc)
        os.environ["HTTPS_PROXY"] = proxy
        os.environ["HTTP_PROXY"] = proxy

    # Initialize client (relying on env vars for proxy)
    client = genai.Client(api_key=api_key)

    prompt = raw_prompt if raw_prompt else get_prompt_for_format(topic, format_type)

    # Configure generation - thinking_config is only supported in google-genai >= 1.56.0
    # config = types.GenerateContentConfig(
    #     thinking_config=types.ThinkingConfig(thinking_level="high")
    # )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        # config=config
    )

    return response.text

def generate_content_with_ark(topic: str, model: str, format_type: str, raw_prompt: str = None) -> str:
    """Generate content using ARK Engine (DeepSeek 3.2)."""
    from volcenginesdkarkruntime import Ark

    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        raise ValueError("ARK_API_KEY environment variable not set")

    # Disable proxy for ARK
    os.environ['NO_PROXY'] = 'ark.cn-beijing.volces.com'

    # Determine thinking mode based on model variant
    if model == "ark-deepseek-reasoner":
        thinking_type = "enabled"
        timeout = 1800  # 30 minutes for reasoning mode
    else:  # ark-deepseek-chat
        thinking_type = "disabled"
        timeout = 300  # 5 minutes for chat mode

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


def get_prompt_for_format(topic: str, format_type: str) -> str:
    """Generate appropriate prompt based on output format."""

    if format_type == "manim":
        return f"""
Create a COMPLETE, EXECUTABLE Python script using **Manim Community Edition (manim>=0.17)** to teach "{topic}".

STRICT REQUIREMENTS (must follow exactly):
- **STRICT STANDARD LIBRARY ONLY:** Use ONLY classes and methods available in standard Manim Community Edition. DO NOT use third-party plugins or hypothetical classes.
- **NO Hallucinations:** If you need a complex object (like a list), build it from primitives (`VGroup`, `Text`, etc.).
- Use **Manim Community Edition**, NOT legacy manimlib
- Import ONLY with: `from manim import *`
- Target the **Cairo renderer** (default)
- Code must run with: `manim -pql scene.py MainScene`
- Output ONLY valid Python code (no explanations, no markdown)

STRICT CODE STRUCTURE:
- **Indentation:** Use exactly 4 spaces for indentation. NO tabs.
- **Method Definitions:** Ensure all methods are defined at the class level (inside the class, but not nested inside other methods).
- **Execution:** Ensure `construct` calls these methods in order.

FORBIDDEN (do NOT use):
- **NO Hyphenated Attributes:** Never use hyphens in Python attributes or parameters (e.g., do NOT use `curve-interpolation`). Python uses underscores (`_`).
- **NO Hallucinated Parameters:** Do not guess parameter names. If unsure, stick to basic parameters like `color`, `font_size`, `radius`, `width`, `height`, `fill_opacity`.
- `np.PI` or `numpy.PI` (DO NOT USE UPPERCASE PI). **ALWAYS use `np.pi`**.
- `BulletList`, `Capsule`, `Table` (these are NOT standard Manim Community classes).
- `.bend()`, `.point_at_angle()` (non-existent methods).
- TextMobject, TexMobject
- ShowCreation, ApplyMethod, ReplacementTransform (legacy usage)
- manimlib imports
- Code mobject
- Non-standard colors (e.g., `BROWN`, `CYAN`, `MAGENTA` are NOT defined in Manim Community by default).
  - Use ONLY: `BLUE`, `GREEN`, `YELLOW`, `RED`, `ORANGE`, `PURPLE`, `GOLD`, `TEAL`, `WHITE`, `BLACK`, `GRAY`.
  - If you need other colors, define them as hex strings (e.g., `BROWN = "#8B4513"`) at the top of the script.

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

def clean_code_fences(content: str) -> str:
    """Remove code fences (```python, ```html, ```) from LLM output."""
    content = content.strip()

    # Remove leading code fence with optional language specifier (only at start of string)
    if content.startswith('```'):
        # Find the end of the first line
        first_newline = content.find('\n')
        if first_newline != -1:
            content = content[first_newline + 1:]
        else:
            # Just ``` with no newline, remove it
            content = content[3:]

    # Remove trailing code fence (only at end of string)
    if content.rstrip().endswith('```'):
        content = content.rstrip()[:-3].rstrip()

    return content

def detect_provider(model: str) -> str:
    """Detect which provider to use based on model name."""
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
    """A simple spinner for console output."""
    return console.status(description, spinner="dots")

def generate_lesson(topic: str, model: str, format_type: str, previous_code: str = None, edit_prompt: str = None) -> str:
    """Generate educational content using specified model and format."""
    if previous_code and edit_prompt:
        return get_edit_prompt(previous_code, topic, edit_prompt, format_type, model)

    provider = detect_provider(model)
    with _spinner(f"Generating lesson about '{topic}' using {model} ({provider}) in {format_type} format..."):
        time.sleep(0.1)  # Allow spinner to start
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

    # Clean code fences from output
    content = clean_code_fences(content)

    if format_type == "manim":
        content = ensure_manim_compatibility(content)

    return content

def get_edit_prompt(current_code: str, original_prompt: str, edit_prompt: str, format_type: str, model: str) -> str:
    """Generate a prompt for code editing based on the current code and edit instructions."""
    base_instructions = f"""
    You are an expert code editor specializing in {format_type}. 
    You will be given the original topic, the current code, and a request to edit the code.

    Your task is to generate the COMPLETE edited code that incorporates the requested changes.

    Guidelines:
    - Make ONLY the changes requested in the edit prompt.
    - Preserve all other functionality and structure.
    - Ensure the code remains complete, valid, and executable.
    - Maintain the same coding style and conventions.
    - Output ONLY the complete updated source code, no explanations or markdown.
    """

    full_prompt = f"""
    {base_instructions}

    ORIGINAL TOPIC: {original_prompt}

    CURRENT CODE:
    {current_code}

    EDIT REQUEST: {edit_prompt}
    
    Generate the COMPLETE edited code:
    """

    provider = detect_provider(model)
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
    
    # Clean code fences from output
    content = clean_code_fences(content)

    if format_type == "manim":
        content = ensure_manim_compatibility(content)

    return content

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
        "# Monkey-patch Line to prevent crashes on hallucinated .bend() method",
        "Line.bend = lambda self, *args, **kwargs: self",
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
    ]
    
    compat_block = "\n# Compatibility layer for LLM-hallucinated colors and classes\n" + \
                   "\n".join(extra_colors) + "\n" + \
                   "\n".join(extra_compat) + "\n"

    # Check for imports to insert after
    if "from manim import *" in code:
        parts = code.split("from manim import *")
        return parts[0] + "from manim import *" + compat_block + parts[1]
    elif "import manim" in code:
        parts = code.split("import manim")
        return parts[0] + "import manim" + compat_block + parts[1]
    else:
        # No standard import found, prepend compatibility block at the top
        return compat_block + "\n" + code

def render_manim(script_path: str) -> str:
    """Render a Manim script to video. Returns the path to the rendered video."""
    import shutil
    from pathlib import Path

    # Determine output video name from script name
    script_path_obj = Path(script_path).resolve()
    output_video = script_path_obj.with_suffix('.mp4')

    print(f"Rendering Manim script to video: {output_video}", file=sys.stderr)

    # Get the scene class name from the script
    with open(script_path, 'r') as f:
        script_content = f.read()

    # Find scene class (looks for "class XYZ(...Scene...):")
    # Matches: class MainScene(Scene):, class Shape3D(ThreeDScene):, etc.
    scene_match = re.search(r'class\s+(\w+)\s*\([^\)]*Scene[^\)]*\)', script_content)
    if not scene_match:
        # Fallback: Try to find ANY class definition if strict check fails
        scene_match = re.search(r'class\s+(\w+)\s*\(', script_content)
        
    if not scene_match:
        raise ValueError("Could not find Scene class in Manim script")

    scene_name = scene_match.group(1)

    # Get the directory containing the script and the script name
    script_dir = script_path_obj.parent
    script_name = script_path_obj.name

    # Determine Manim executable
    manim_exe = None
    
    # 1. Check environment variable
    env_exe = os.getenv("MANIM_EXECUTABLE")
    if env_exe and os.access(env_exe, os.X_OK):
        manim_exe = env_exe
    
    # 2. Check current python environment
    if not manim_exe:
        python_dir = Path(sys.executable).parent
        possible_exe = python_dir / "manim"
        if possible_exe.exists() and os.access(possible_exe, os.X_OK):
            manim_exe = str(possible_exe)
            
    # 3. Fallback to system path
    if not manim_exe:
        manim_exe = "manim"

    # Command: manim -qm (medium quality) script.py SceneName
    # Using -qm ensures 720p output which is faster than default (sometimes 1080p) but better than preview (-ql)
    cmd = [manim_exe, "-qm", script_name, scene_name]

    print(f"Running in {script_dir}: {' '.join(cmd)}", file=sys.stderr)

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)

    if result.returncode != 0:
        error_msg = f"Manim rendering failed with code {result.returncode}.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        print(error_msg, file=sys.stderr)
        raise RuntimeError(error_msg)

    # Find the rendered video recursively in media/videos/
    # Manim structure: media/videos/<script_stem>/<quality>/<scene_name>.mp4
    media_dir = script_dir / "media" / "videos"
    
    if not media_dir.exists():
        raise RuntimeError(f"Expected output directory not found: {media_dir}")

    # Recursively find all mp4 files
    mp4_files = list(media_dir.rglob("*.mp4"))
    
    # Filter out partial movie files (temp files)
    mp4_files = [f for f in mp4_files if "partial_movie_files" not in str(f)]
    
    if not mp4_files:
        raise RuntimeError(f"No mp4 files found in {media_dir}")

    # Get the most recent file
    source_video = max(mp4_files, key=lambda p: p.stat().st_mtime)

    # Move the video to the desired location
    shutil.move(str(source_video), str(output_video))

    print(f"Successfully rendered and moved video to: {output_video}", file=sys.stderr)
    return str(output_video)

def main():
    parser = argparse.ArgumentParser(
        description="Generate educational content/slides using various LLM providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Pythagorean theorem" -m gpt-4o-mini -f reveal.js -o slides.html
  %(prog)s "Quicksort algorithm" -m deepseek-chat -f manim -o animation.py
  %(prog)s "Binary search" -m glm-4.7 -f p5.js -o visualization.html
  %(prog)s "Neural networks" -m gemini-3-flash-preview -f p5.js -o course.html
  %(prog)s "Machine learning" -m ark-deepseek-chat -f manim -o ml.py
  %(prog)s "Quantum computing" -m ark-deepseek-reasoner -f reveal.js -o quantum.html

Note: Manim format automatically renders to video (generates both .py and .mp4 files)

Environment variables:
  DEEPSEEK_API_KEY  - For deepseek* models
  OPENAI_API_KEY    - For gpt-* models
  ZAI_API_KEY       - For glm-* models
  GEMINI_API_KEY    - For gemini-* models
  ARK_API_KEY       - For ark-deepseek-* models (DeepSeek 3.2 via ARK Engine)
        """
    )

    parser.add_argument(
        "topic",
        required=True,
        help="Topic to teach (e.g., 'Pythagorean theorem', 'Quicksort algorithm')"
    )

    parser.add_argument(
        "-m", "--model",
        required=True,
        help="Model to use (gpt-4o, glm-4-flash, deepseek-chat, deepseek-reasoner, gemini-3-flash-preview, ark-deepseek-chat, ark-deepseek-reasoner, etc.)"
    )

    parser.add_argument(
        "-f", "--format",
        required=True,
        choices=["manim", "reveal.js", "p5.js"],
        help="Output format"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: ./static/<topic> with appropriate extension)"
    )

    args = parser.parse_args()

    # Determine default output if not provided
    if not args.output:
        extension = "py" if args.format == "manim" else "html"
        # Sanitize topic for filename
        safe_topic = re.sub(r'[^a-zA-Z0-9_\-]', '_', args.topic)
        args.output = os.path.join("static", f"{safe_topic}.{extension}")
    
    args.output = os.path.abspath(args.output)

    try:
        # Generate content
        content = generate_lesson(args.topic, args.model, args.format)

        # Write to file
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Successfully generated content and saved to: {args.output}", file=sys.stderr)
        print(f"File size: {len(content)} bytes", file=sys.stderr)

        # Auto-render manim video
        if args.format == "manim":
            video_path = render_manim(args.output)
            print(f"Video rendered: {video_path}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()