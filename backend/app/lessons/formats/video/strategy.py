from backend.app.lessons.formats.code import CodeLessonStrategy
from backend.app.lessons.formats.video.prompt import VIDEO_RULES


class VideoStrategy(CodeLessonStrategy):
    repair_message = "Repairing the video scene…"

    def __init__(self) -> None:
        super().__init__("video", VIDEO_RULES)
