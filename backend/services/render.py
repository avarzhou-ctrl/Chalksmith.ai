import uuid
import os
from backend.services.llm import generate_lesson, render_manim

# Get the path to the backend/static directory
# __file__ is backend/services/render.py, so we go up two levels to reach backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

def render_manim_lesson(topic: str, model: str, manim_code: str) -> str:
    unique_id = str(uuid.uuid4())
    
    # Save code to a file first
    script_path = os.path.join(STATIC_DIR, f"manim_{unique_id}.py")
    with open(script_path, "w") as f:
        f.write(manim_code)
        
    # render_manim will generate the video at static/manim_{unique_id}.mp4
    video_path = render_manim(script_path)
    
    # Return the URL path
    return f"/static/manim_{unique_id}.mp4"

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
