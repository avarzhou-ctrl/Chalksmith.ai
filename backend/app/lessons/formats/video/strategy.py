from dataclasses import replace

from backend.app.lessons.formats.code import CodeLessonStrategy
from backend.app.lessons.formats.code import parse_generated_lesson
from backend.app.lessons.formats.contracts import FormatRequest, PreparedLesson
from backend.app.lessons.formats.video.compiler import (
    VIDEO_COMPILER_VERSION,
    VIDEO_RUNTIME_VERSION,
    compile_video,
    strip_video_runtime,
)
from backend.app.lessons.formats.video.prompt import VIDEO_RULES


class VideoStrategy(CodeLessonStrategy):
    repair_message = "Repairing the video scene…"

    def __init__(self) -> None:
        super().__init__("video", VIDEO_RULES)

    def build_prompt(self, request: FormatRequest) -> str:
        if request.previous_code:
            request = replace(request, previous_code=strip_video_runtime(request.previous_code))
        return super().build_prompt(request)

    def prepare(self, response: str) -> PreparedLesson:
        generated = parse_generated_lesson(response, self.lesson_format)
        return PreparedLesson(
            summary=generated.summary,
            source_code=compile_video(generated.code),
            runtime_version=VIDEO_RUNTIME_VERSION,
            compiler_version=VIDEO_COMPILER_VERSION,
        )
