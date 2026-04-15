import uuid
import os
import subprocess
import json
from backend.services.llm import generate_lesson

# Get the path to the backend/static directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

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
