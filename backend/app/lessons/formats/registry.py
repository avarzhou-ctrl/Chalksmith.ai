from backend.app.lessons.formats.contracts import LessonFormatStrategy
from backend.app.lessons.formats.interactive import InteractiveStrategy
from backend.app.lessons.formats.slides.strategy import StructuredSlidesStrategy
from backend.app.lessons.formats.video import VideoStrategy


def get_lesson_format_strategy(lesson_format: str) -> LessonFormatStrategy:
    if lesson_format == "interactive":
        return InteractiveStrategy()
    if lesson_format == "video":
        return VideoStrategy()
    if lesson_format == "slides":
        return StructuredSlidesStrategy()
    raise ValueError(f"Unsupported lesson format: {lesson_format}")
