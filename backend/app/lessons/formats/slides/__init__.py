from backend.app.lessons.formats.slides.compiler import (
    SLIDES_COMPILER_VERSION,
    SLIDES_RUNTIME_VERSION,
    compile_slides,
)
from backend.app.lessons.formats.slides.spec import SlidesLessonSpec
from backend.app.lessons.formats.slides.strategy import StructuredSlidesStrategy

__all__ = [
    "SLIDES_COMPILER_VERSION",
    "SLIDES_RUNTIME_VERSION",
    "SlidesLessonSpec",
    "StructuredSlidesStrategy",
    "compile_slides",
]
