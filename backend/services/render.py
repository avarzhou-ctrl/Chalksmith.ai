import uuid
import os
import asyncio
import subprocess
import json
import re
import shutil
import sys
from pathlib import Path
from backend.services.llm import generate_lesson

# Get the path to the backend/static directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

async def render_manim(script_path: str) -> str:
    """Render a Manim script to video. Returns the path to the rendered video."""
    # Build the target .mp4 path based on the input .py script name
    script_path_obj = Path(script_path).resolve()
    output_video = script_path_obj.with_suffix('.mp4')

    print(f"Rendering Manim script to video: {output_video}", file=sys.stderr)

    # Load script content to identify the target class for the Manim CLI
    with open(script_path, 'r') as f:
        script_content = f.read()

    # Use regex to find the Scene class name so we know what to tell Manim to animate
    scene_match = re.search(r'class\s+(\w+)\s*\([^\)]*Scene[^\)]*\)', script_content)
    if not scene_match:
        # Fallback to any class if strict 'Scene' inheritance check fails
        scene_match = re.search(r'class\s+(\w+)\s*\(', script_content)
        
    if not scene_match:
        raise ValueError("Could not find Scene class in Manim script")

    scene_name = scene_match.group(1)
    script_dir = script_path_obj.parent
    script_name = script_path_obj.name

    # Priority search for Manim binary to support local, venv, and global installs
    manim_exe = None
    env_exe = os.getenv("MANIM_EXECUTABLE")
    if env_exe and os.access(env_exe, os.X_OK):
        manim_exe = env_exe
    
    if not manim_exe:
        # Check current python environment's bin folder
        python_dir = Path(sys.executable).parent
        possible_exe = python_dir / "manim"
        # Support Windows
        if os.name == 'nt':
            possible_exe = possible_exe.with_suffix('.exe')
            
        if possible_exe.exists() and os.access(possible_exe, os.X_OK):
            manim_exe = str(possible_exe)
            
    if not manim_exe:
        # Check project-relative .venv/bin folder as a fallback
        project_root = Path(BASE_DIR).parent
        venv_bin = project_root / ".venv" / ("Scripts" if os.name == 'nt' else "bin")
        possible_exe = venv_bin / "manim"
        if os.name == 'nt':
            possible_exe = possible_exe.with_suffix('.exe')
            
        if possible_exe.exists() and os.access(possible_exe, os.X_OK):
            manim_exe = str(possible_exe)

    if not manim_exe:
        # Fallback to system-wide 'manim' command using shutil.which for robustness
        manim_exe = shutil.which("manim") or "manim"

    # Execute Manim CLI at medium quality (qm) for a balance of speed and resolution
    cmd = [manim_exe, "-qm", script_name, scene_name]
    print(f"Running in {script_dir}: {' '.join(cmd)}", file=sys.stderr)

    # Use asyncio.create_subprocess_exec to allow for task cancellation
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=script_dir
    )

    try:
        stdout, stderr = await process.communicate()
    except asyncio.CancelledError:
        # If the client disconnects, terminate the subprocess immediately
        process.terminate()
        await process.wait()
        raise

    if process.returncode != 0:
        # Capture stderr to provide debugging context for the LLM self-correction loop
        error_msg = f"Manim rendering failed with code {process.returncode}.\nSTDOUT: {stdout.decode()}\nSTDERR: {stderr.decode()}"
        print(error_msg, file=sys.stderr)
        raise RuntimeError(error_msg)

    # Manim creates a deep 'media/videos' structure; we need to find the final .mp4
    media_dir = script_dir / "media" / "videos"
    if not media_dir.exists():
        raise RuntimeError(f"Expected output directory not found: {media_dir}")

    # Recursively search for the final video file, ignoring temporary partial frames
    mp4_files = list(media_dir.rglob("*.mp4"))
    mp4_files = [f for f in mp4_files if "partial_movie_files" not in str(f)]
    
    if not mp4_files:
        raise RuntimeError(f"No mp4 files found in {media_dir}")

    # Select the newest file to ensure we don't pick up leftovers from previous runs
    source_video = max(mp4_files, key=lambda p: p.stat().st_mtime)
    
    # Move the file from the messy Manim structure to our clean static/ folder
    shutil.move(str(source_video), str(output_video))

    print(f"Successfully rendered and moved video to: {output_video}", file=sys.stderr)
    return str(output_video)

def extract_traceback(error_output: str) -> str:
    """Extracts only the relevant Python traceback or error message from Manim output."""
    # Look for the standard Python traceback start
    if "Traceback (most recent call last):" in error_output:
        return "Traceback (most recent call last):" + error_output.split("Traceback (most recent call last):")[-1]
    
    # Fallback: Look for specific Manim Error lines in stderr
    lines = error_output.splitlines()
    error_lines = [l for l in lines if "ERROR" in l or "Exception" in l or "Error" in l]
    if error_lines:
        # Return the last few error-related lines for context
        return "\n".join(error_lines[-5:])
        
    # Final fallback: Return the last 1000 characters
    return error_output[-1000:]

async def render_manim_lesson(topic: str, model: str, manim_code: str, session=None, on_progress=None) -> str:
    unique_id = str(uuid.uuid4())
    script_path = os.path.join(STATIC_DIR, f"manim_{unique_id}.py")
    
    max_retries = 2
    current_code = manim_code

    for attempt in range(max_retries + 1):
        if on_progress:
            if attempt == 0:
                on_progress("Writing Manim script...", 65)
            else:
                on_progress(f"Auto-correcting Manim syntax error (Attempt {attempt}/{max_retries})...", 70 + (attempt * 10))

        with open(script_path, "w") as f:
            f.write(current_code)
            
        try:
            if on_progress:
                on_progress("Rendering video frames with Manim...", 70 + (attempt * 5))
            await render_manim(script_path)
            return f"/static/manim_{unique_id}.mp4"
        except RuntimeError as e:
            if attempt >= max_retries:
                print(f"Manim failed after {max_retries} retries: {str(e)}")
                raise RuntimeError(f"Manim failed after {max_retries} retries. Final error: {extract_traceback(str(e))}")
            
            # SELF-CORRECTION: Extract relevant traceback and send back to LLM
            error_msg = str(e)
            traceback = extract_traceback(error_msg)
            print(f"Manim Attempt {attempt+1} Failed. Traceback extracted: {traceback}")
            
            from backend.services.llm import generate_lesson
            
            # Specific guiderails for Manim Community v0.18+
            retry_prompt = (
                f"The previous Manim code failed with this error:\n\n{traceback}\n\n"
                "Please fix the code. CRITICAL: Ensure you are using Manim Community (v0.18+) syntax. "
                "Common fixes to apply:\n"
                "- Use 'Create' instead of 'ShowCreation'\n"
                "- Use 'Uncreate' instead of 'UnshowCreation'\n"
                "- Use 'FadeIn' / 'FadeOut' instead of 'FadeInFrom', etc.\n"
                "- Use 'ReplacementTransform' instead of 'Transform' if swapping objects\n"
                "- Ensure all imports are 'from manim import *'\n"
                "Return only the corrected, full Python script."
            )
            
            try:
                loop = asyncio.get_event_loop()
                lesson_result = await loop.run_in_executor(
                    None, 
                    lambda: generate_lesson(topic, model, "manim", previous_code=current_code, edit_prompt=retry_prompt)
                )
                current_code = lesson_result["code"]
            except Exception as llm_err:
                print(f"LLM failed to generate a fix: {str(llm_err)}")
                raise RuntimeError(f"Failed to generate fix: {str(llm_err)}")

async def render_remotion_lesson(topic: str, model: str, remotion_json: str, on_progress=None) -> str:
    unique_id = str(uuid.uuid4())
    video_filename = f"remotion_{unique_id}.mp4"
    video_path = os.path.join(STATIC_DIR, video_filename)
    
    # ALWAYS save the JSON props first (for the frontend player)
    props_filename = f"remotion_{unique_id}.json"
    props_path = os.path.join(STATIC_DIR, props_filename)
    
    if on_progress:
        # Notify UI before starting Remotion data preparation
        on_progress("Preparing video blueprints...", 65)

    with open(props_path, "w") as f:
        f.write(remotion_json)
        
    # Remotion CLI configuration
    frontend_dir = os.path.join(os.path.dirname(BASE_DIR), "frontend")
    # Entry point relative to frontend_dir
    entry_point = "src/remotion/Root.tsx"
    
    # Calculate duration (Remotion needs this to know when to stop)
    try:
        data = json.loads(remotion_json)
        total_seconds = sum(scene.get("durationInSeconds", 5) for scene in data.get("scenes", []))
        duration_frames = int(total_seconds * 30) + 15 # +0.5s buffer
    except Exception:
        duration_frames = 300 # Fallback 10s

    # Build the 'npx remotion render' command
    # Using the props_path FILE instead of the raw string for stability
    cmd = [
        "npx", "remotion", "render",
        entry_point,
        "Main",
        video_path,
        "--props", props_path,
        "--frames", f"0-{duration_frames}",
        "--browser", "chromium"
    ]

    print(f"--- STARTING REMOTION RENDER ---", flush=True)
    print(f"Target: {video_path}", flush=True)

    if on_progress:
        # Report lengthy encoding phase with estimated frame count for user context
        on_progress(f"Encoding MP4 video ({duration_frames} frames)...", 75)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=frontend_dir
        )
        
        try:
            # 3 minute timeout
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)
        except asyncio.TimeoutError:
            process.terminate()
            await process.wait()
            raise RuntimeError("Remotion render timed out")
        except asyncio.CancelledError:
            process.terminate()
            await process.wait()
            raise

        if process.returncode == 0 and os.path.exists(video_path):
            print(f"RENDER SUCCESS: {video_filename}", flush=True)
            return f"/static/{video_filename}"
        else:
            print(f"RENDER FAILED (Code {process.returncode})", flush=True)
            print(f"STDERR: {stderr.decode()}", flush=True)
            # Fallback: Serve the JSON so the frontend player can still work
            return f"/static/{props_filename}"
            
    except Exception as e:
        print(f"RENDER EXCEPTION: {str(e)}", flush=True)
        return f"/static/{props_filename}"

async def render_p5js_lesson(topic: str, model: str, p5js_code: str, on_progress=None) -> str:
    unique_id = str(uuid.uuid4())

    if on_progress:
        # Notify client of lightweight static generation phase
        on_progress("Creating interactive p5.js canvas...", 70)

    # Save code to a file first
    file_path = os.path.join(STATIC_DIR, f"p5js_{unique_id}.html")
    with open(file_path, "w") as f:
        f.write(p5js_code)
    
    return f"/static/p5js_{unique_id}.html"

async def render_revealjs_lesson(topic: str, model: str, revealjs_code: str, on_progress=None) -> str:
    unique_id = str(uuid.uuid4())

    if on_progress:
        # Notify client of lightweight static generation phase
        on_progress("Compiling presentation slides...", 70)

    # Save code to a file first
    file_path = os.path.join(STATIC_DIR, f"revealjs_{unique_id}.html")

    with open(file_path, "w") as f:

        f.write(revealjs_code)

    return f"/static/revealjs_{unique_id}.html"
