import uuid
import os
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

def render_manim(script_path: str) -> str:
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
        # Check the current .venv bin/ folder for the 'manim' executable
        python_dir = Path(sys.executable).parent
        possible_exe = python_dir / "manim"
        if possible_exe.exists() and os.access(possible_exe, os.X_OK):
            manim_exe = str(possible_exe)
            
    if not manim_exe:
        # Fallback to system-wide 'manim' command
        manim_exe = "manim"

    # Execute Manim CLI at medium quality (qm) for a balance of speed and resolution
    cmd = [manim_exe, "-qm", script_name, scene_name]
    print(f"Running in {script_dir}: {' '.join(cmd)}", file=sys.stderr)

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)

    if result.returncode != 0:
        # Capture stderr to provide debugging context for the LLM self-correction loop
        error_msg = f"Manim rendering failed with code {result.returncode}.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
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

def render_manim_lesson(topic: str, model: str, manim_code: str, session=None) -> str:
    unique_id = str(uuid.uuid4())
    script_path = os.path.join(STATIC_DIR, f"manim_{unique_id}.py")
    
    with open(script_path, "w") as f:
        f.write(manim_code)
        
    try:
        video_path = render_manim(script_path)
        return f"/static/manim_{unique_id}.mp4"
    except RuntimeError as e:
        print(f"Manim First Attempt Failed: {str(e)}")
        
        # SELF-CORRECTION: Send error back to LLM
        error_msg = str(e)
        from backend.services.llm import generate_lesson
        
        retry_prompt = f"The previous Manim code failed with this error:\n{error_msg}\n\nPlease fix the code and return only the corrected, full Python script."
        
        try:
            fixed_code = generate_lesson(topic, model, "manim", previous_code=manim_code, edit_prompt=retry_prompt)
            
            # Save and try again
            with open(script_path, "w") as f:
                f.write(fixed_code)
            
            video_path = render_manim(script_path)
            return f"/static/manim_{unique_id}.mp4"
        except Exception as retry_err:
            print(f"Manim Self-Correction Failed: {str(retry_err)}")
            raise RuntimeError(f"Self-correction failed: {str(retry_err)}")

def render_remotion_lesson(topic: str, model: str, remotion_json: str) -> str:
    unique_id = str(uuid.uuid4())
    video_filename = f"remotion_{unique_id}.mp4"
    video_path = os.path.join(STATIC_DIR, video_filename)
    
    # ALWAYS save the JSON props first (for the frontend player)
    props_filename = f"remotion_{unique_id}.json"
    props_path = os.path.join(STATIC_DIR, props_filename)
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

    try:
        # In a production app, use BackgroundTasks. Synchronous here for simplicity.
        process = subprocess.run(
            cmd, 
            cwd=frontend_dir, 
            capture_output=True, 
            text=True, 
            timeout=180 # 3 min timeout
        )
        
        if process.returncode == 0 and os.path.exists(video_path):
            print(f"RENDER SUCCESS: {video_filename}", flush=True)
            return f"/static/{video_filename}"
        else:
            print(f"RENDER FAILED (Code {process.returncode})", flush=True)
            print(f"STDERR: {process.stderr}", flush=True)
            # Fallback: Serve the JSON so the frontend player can still work
            return f"/static/{props_filename}"
            
    except Exception as e:
        print(f"RENDER EXCEPTION: {str(e)}", flush=True)
        return f"/static/{props_filename}"

def render_p5js_lesson(topic: str, model: str, p5js_code: str) -> str:
    unique_id = str(uuid.uuid4())

    # Save code to a file first
    file_path = os.path.join(STATIC_DIR, f"p5js_{unique_id}.html")
    with open(file_path, "w") as f:
        f.write(p5js_code)
    
    return f"/static/p5js_{unique_id}.html"

def render_revealjs_lesson(topic: str, model: str, revealjs_code: str) -> str:
    unique_id = str(uuid.uuid4())

    # Save code to a file first
    file_path = os.path.join(STATIC_DIR, f"revealjs_{unique_id}.html")

    with open(file_path, "w") as f:

        f.write(revealjs_code)

    return f"/static/revealjs_{unique_id}.html"
