from backend.app.lessons.formats.contracts import FormatRequest, PreparedLesson
from backend.app.lessons.formats.slides.compiler import (
    SLIDES_COMPILER_VERSION,
    SLIDES_RUNTIME_VERSION,
    compile_slides,
)
from backend.app.lessons.formats.slides.prompt import build_slides_prompt
from backend.app.lessons.formats.slides.response import (
    build_slides_repair_prompt,
    parse_slides_response,
)


class StructuredSlidesStrategy:
    lesson_format = "slides"
    repair_message = "Repairing the slide specification…"

    def build_prompt(self, request: FormatRequest) -> str:
        return build_slides_prompt(request)

    def prepare(self, response: str) -> PreparedLesson:
        spec = parse_slides_response(response)
        return PreparedLesson(
            summary=spec.summary,
            source_code=compile_slides(spec),
            lesson_spec=spec.model_dump_json(),
            spec_version=spec.schema_version,
            runtime_version=SLIDES_RUNTIME_VERSION,
            compiler_version=SLIDES_COMPILER_VERSION,
        )

    def can_repair(self, error: Exception) -> bool:
        return isinstance(error, ValueError)

    def build_repair_prompt(self, original_prompt: str, response: str, error: Exception) -> str:
        return build_slides_repair_prompt(original_prompt, response, error)
