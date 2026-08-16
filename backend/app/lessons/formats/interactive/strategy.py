from backend.app.lessons.formats.code import CodeLessonStrategy
from backend.app.lessons.formats.interactive.prompt import INTERACTIVE_RULES


class InteractiveStrategy(CodeLessonStrategy):
    def __init__(self) -> None:
        super().__init__("interactive", INTERACTIVE_RULES)
