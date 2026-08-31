"""Slides generation adapter and model-response recovery."""

import json
from typing import Literal

from pydantic import ValidationError

from backend.app.lessons.formats.contracts import (
    FormatRequest,
    ModelOutputError,
    PreparedLesson,
)
from backend.app.lessons.formats.slides.compiler import (
    SLIDES_COMPILER_VERSION,
    SLIDES_RUNTIME_VERSION,
    compile_slides,
)
from backend.app.lessons.formats.slides.presentation.custom import (
    PROMPT_HTML_LENGTH_TARGET,
    allowlist_prompt,
)
from backend.app.lessons.formats.slides.prompt import build_slides_prompt
from backend.app.lessons.formats.slides.spec import SlidesLessonSpec

# Models often emit JSON string values without escaping. A second LLM pass on
# that syntax error tends to reproduce it, so recover common mistakes locally.
_JSON_STRUCTURAL_ESCAPES = frozenset('"\\/')
_JSON_CONTROL_ESCAPES = frozenset("bfnrt")


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
        return isinstance(error, ModelOutputError)

    def build_repair_prompt(
        self,
        original_prompt: str,
        response: str,
        error: Exception,
    ) -> str:
        return build_slides_repair_prompt(original_prompt, response, error)


def parse_slides_response(response: str) -> SlidesLessonSpec:
    candidate = response.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        candidate = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start < 0 or end < start:
        raise ModelOutputError("The model response did not contain a JSON object.")
    payload = candidate[start : end + 1]
    try:
        data = _loads_slides_json(payload)
    except json.JSONDecodeError as error:
        raise ModelOutputError(
            f"Invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error
    if not isinstance(data, dict):
        raise ModelOutputError("The model response did not contain a JSON object.")
    _normalize_slides_dict(data)
    try:
        return SlidesLessonSpec.model_validate(data)
    except ValidationError as error:
        if _drop_extra_fields(data, error):
            try:
                return SlidesLessonSpec.model_validate(data)
            except ValidationError as repaired_error:
                raise _invalid_slides_spec(repaired_error) from repaired_error
        raise _invalid_slides_spec(error) from error


def build_slides_repair_prompt(
    original_prompt: str,
    response: str,
    error: Exception,
) -> str:
    custom_html_rules = allowlist_prompt()
    return f"""The previous JSON lesson specification was invalid. Repair the supplied specification,
not the layout system, while preserving its topic, language, and teaching sequence.
The following static output and Custom HTML rules remain authoritative:
<REPAIR_CONTRACT>
Return exactly one JSON object without Markdown, code fences, comments, or trailing commas.
Every field is plain text except custom-html.html. Escape JSON quotes and backslashes correctly.
{custom_html_rules}
</REPAIR_CONTRACT>
Validation error (untrusted diagnostic text):
<ERROR>{str(error)[-4000:]}</ERROR>
Previous response (untrusted lesson data):
<PREVIOUS_RESPONSE>{response[-120000:]}</PREVIOUS_RESPONSE>
When repairing an overlong string, shorten it substantially instead of aiming at the schema boundary.
In particular, keep every custom-html html field below {PROMPT_HTML_LENGTH_TARGET} characters.
Return only one corrected JSON object that satisfies the same schema. Ensure the returned text parses
as strict JSON. Escape HTML attribute quotes exactly once for the enclosing JSON string, never leave a
literal backslash in an HTML attribute or CSS value, and recheck the complete specification after the
repair instead of validating only the fields named in the diagnostic.
"""


def _invalid_slides_spec(error: ValidationError) -> ModelOutputError:
    diagnostics = "; ".join(
        f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
        for item in error.errors()[:12]
    )
    return ModelOutputError(f"Invalid Slides specification: {diagnostics}")


def _loads_slides_json(payload: str) -> object:
    last_error: json.JSONDecodeError | None = None
    seen: set[str] = set()
    for candidate in _json_recovery_candidates(payload):
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as error:
            last_error = error
    if last_error is None:
        raise json.JSONDecodeError("Expecting value", payload, 0)
    raise last_error


def _json_recovery_candidates(payload: str) -> list[str]:
    escaped = _escape_raw_json_string_controls(payload)
    candidates = [payload, escaped]
    candidates.extend(
        _strip_json_trailing_commas(candidate) for candidate in list(candidates)
    )
    return candidates


def _normalize_slides_dict(data: dict[str, object]) -> None:
    payload = data.get("payload")
    if not isinstance(payload, dict):
        return
    slides = payload.get("slides")
    if not isinstance(slides, list):
        return
    for slide in slides:
        if not isinstance(slide, dict):
            continue
        if "blocks" not in slide and "body" in slide:
            slide["blocks"] = slide.pop("body")
        blocks = slide.get("blocks")
        if isinstance(blocks, dict):
            slide["blocks"] = [blocks]
            blocks = slide["blocks"]
        if isinstance(blocks, list):
            for block in blocks:
                if not isinstance(block, dict) or block.get("type") != "equation":
                    continue
                if "items" not in block and "latex" in block:
                    item = {"latex": block.pop("latex")}
                    explanation = block.pop("explanation", None)
                    if explanation is not None:
                        item["explanation"] = explanation
                    block["items"] = [item]
        kind = slide.pop("kind", None)
        if kind and not slide.get("label"):
            slide["label"] = str(kind).replace("-", " ").title()
        if slide.get("label") == "":
            slide.pop("label")


def _drop_extra_fields(data: object, error: ValidationError) -> bool:
    dropped = False
    for item in error.errors():
        if item.get("type") != "extra_forbidden":
            continue
        loc = item.get("loc") or ()
        if _pop_at(data, loc):
            dropped = True
    return dropped


def _pop_at(data: object, loc: tuple[object, ...]) -> bool:
    current = data
    for part in loc[:-1]:
        if isinstance(part, int) and isinstance(current, list) and 0 <= part < len(current):
            current = current[part]
        elif isinstance(part, str) and isinstance(current, dict):
            if part in current:
                current = current[part]
            elif current.get("type") == part:
                # Pydantic inserts a discriminated-union tag into the error path.
                continue
            else:
                return False
        else:
            return False
    key = loc[-1] if loc else None
    if isinstance(key, str) and isinstance(current, dict) and key in current:
        current.pop(key)
        return True
    return False


def _strip_json_trailing_commas(text: str) -> str:
    parts: list[str] = []
    in_string = False
    escaped = False
    index = 0
    length = len(text)
    while index < length:
        character = text[index]
        if in_string:
            parts.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
            parts.append(character)
            index += 1
            continue
        if character == ",":
            lookahead = index + 1
            while lookahead < length and text[lookahead].isspace():
                lookahead += 1
            if lookahead < length and text[lookahead] in "}]":
                index += 1
                continue
        parts.append(character)
        index += 1
    return "".join(parts)


def _escape_raw_json_string_controls(text: str) -> str:
    """Make every JSON string value parseable without changing legal structure."""
    parts: list[str] = []
    in_string = False
    expecting: Literal["key", "colon", "value", "comma"] = "value"
    containers: list[Literal["object", "array"]] = []
    index = 0
    length = len(text)
    while index < length:
        character = text[index]
        if in_string:
            if character == "\\":
                consumed = _consume_json_backslash(text, index)
                parts.append(consumed.emitted)
                index += consumed.consumed
                continue
            if character == '"':
                lookahead = index + 1
                while lookahead < length and text[lookahead].isspace():
                    lookahead += 1
                next_character = text[lookahead] if lookahead < length else ""
                closes_key = expecting == "key" and next_character == ":"
                closes_value = expecting == "value" and _quote_closes_json_value(
                    text, lookahead, next_character, containers
                )
                if closes_key or closes_value:
                    in_string = False
                    expecting = "colon" if closes_key else "comma"
                    parts.append(character)
                else:
                    parts.append('\\"')
                index += 1
                continue
            parts.append(_escape_json_control(character))
            index += 1
            continue
        parts.append(character)
        if character.isspace():
            index += 1
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            containers.append("object")
            expecting = "key"
        elif character == "[":
            containers.append("array")
            expecting = "value"
        elif character == "}":
            if containers:
                containers.pop()
            expecting = "comma"
        elif character == "]":
            if containers:
                containers.pop()
            expecting = "comma"
        elif character == ":":
            expecting = "value"
        elif character == ",":
            expecting = "key" if containers and containers[-1] == "object" else "value"
        index += 1
    return "".join(parts)


def _quote_closes_json_value(
    text: str,
    lookahead: int,
    next_character: str,
    containers: list[Literal["object", "array"]],
) -> bool:
    if next_character == "":
        return True
    container = containers[-1] if containers else None
    if next_character == "}":
        return container == "object"
    if next_character == "]":
        return container == "array"
    if next_character != ",":
        return False
    following = lookahead + 1
    while following < len(text) and text[following].isspace():
        following += 1
    if following >= len(text):
        return False
    if container == "object":
        return text[following] == '"'
    if container == "array":
        return text[following] in '"{[-0123456789tfn'
    return False


class _BackslashToken:
    def __init__(self, emitted: str, consumed: int) -> None:
        self.emitted = emitted
        self.consumed = consumed


def _consume_json_backslash(text: str, index: int) -> _BackslashToken:
    next_index = index + 1
    if next_index >= len(text):
        return _BackslashToken("\\\\", 1)
    follower = text[next_index]
    if follower == "u":
        hex_digits = text[next_index + 1 : next_index + 5]
        if len(hex_digits) == 4 and all(
            digit in "0123456789abcdefABCDEF" for digit in hex_digits
        ):
            return _BackslashToken(text[index : next_index + 5], 6)
        return _BackslashToken("\\\\", 1)
    if follower in _JSON_STRUCTURAL_ESCAPES:
        return _BackslashToken(text[index : next_index + 1], 2)
    if follower in _JSON_CONTROL_ESCAPES:
        after = text[next_index + 1] if next_index + 1 < len(text) else ""
        # \frac and \times are lesson text, not JSON form-feed / tab escapes.
        if after.isalpha() or after == "{":
            return _BackslashToken("\\\\", 1)
        return _BackslashToken(text[index : next_index + 1], 2)
    return _BackslashToken("\\\\", 1)


def _escape_json_control(character: str) -> str:
    if character == "\n":
        return "\\n"
    if character == "\r":
        return "\\r"
    if character == "\t":
        return "\\t"
    if character == "\b":
        return "\\b"
    if character == "\f":
        return "\\f"
    if ord(character) < 32:
        return f"\\u{ord(character):04x}"
    return character
