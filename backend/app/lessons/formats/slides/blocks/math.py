from collections.abc import Callable
from html import escape
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition, BlockGuide


class EquationBlock(StrictSpecModel):
    type: Literal["equation"]
    expression: str = Field(min_length=1, max_length=160)
    explanation: str | None = Field(default=None, min_length=1, max_length=180)

    @model_validator(mode="after")
    def validate_expression(self) -> "EquationBlock":
        if "$" in self.expression:
            raise ValueError("equation expressions must not include dollar delimiters")
        return self


class FractionModelBlock(StrictSpecModel):
    type: Literal["fraction-model"]
    numerator: int = Field(ge=0, le=12)
    denominator: int = Field(ge=2, le=12)
    label: str | None = Field(default=None, min_length=1, max_length=48)

    @model_validator(mode="after")
    def validate_fraction(self) -> "FractionModelBlock":
        if self.numerator > self.denominator:
            raise ValueError("fraction numerator cannot exceed its denominator")
        return self


class NumberLineMarker(StrictSpecModel):
    value: float = Field(ge=-100, le=100)
    label: str | None = Field(default=None, min_length=1, max_length=24)


class NumberLineBlock(StrictSpecModel):
    type: Literal["number-line"]
    min_value: float = Field(ge=-100, le=100)
    max_value: float = Field(ge=-100, le=100)
    markers: list[NumberLineMarker] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def validate_number_line(self) -> "NumberLineBlock":
        if self.min_value >= self.max_value:
            raise ValueError("number-line min_value must be less than max_value")
        values = sorted(marker.value for marker in self.markers)
        if values[0] < self.min_value or values[-1] > self.max_value:
            raise ValueError("number-line markers must stay inside its range")
        if len(values) != len(set(values)):
            raise ValueError("number-line marker values must be unique")
        span = self.max_value - self.min_value
        if any((right - left) / span < 0.06 for left, right in zip(values, values[1:])):
            raise ValueError(
                "number-line markers are too close to label without overlap"
            )
        return self


class BarModelPart(StrictSpecModel):
    label: str = Field(min_length=1, max_length=24)
    value: float = Field(gt=0, le=1000)


class BarModelBlock(StrictSpecModel):
    type: Literal["bar-model"]
    parts: list[BarModelPart] = Field(min_length=2, max_length=6)
    total_label: str | None = Field(default=None, min_length=1, max_length=32)


class CoordinatePoint(StrictSpecModel):
    x: float = Field(ge=-20, le=20)
    y: float = Field(ge=-20, le=20)
    label: str | None = Field(default=None, min_length=1, max_length=16)


class CoordinatePlotBlock(StrictSpecModel):
    type: Literal["coordinate-plot"]
    x_min: float = Field(default=-10, ge=-20, le=20)
    x_max: float = Field(default=10, ge=-20, le=20)
    y_min: float = Field(default=-10, ge=-20, le=20)
    y_max: float = Field(default=10, ge=-20, le=20)
    points: list[CoordinatePoint] = Field(min_length=1, max_length=8)
    x_label: str | None = Field(default=None, min_length=1, max_length=16)
    y_label: str | None = Field(default=None, min_length=1, max_length=16)

    @model_validator(mode="after")
    def validate_plot(self) -> "CoordinatePlotBlock":
        if self.x_min >= self.x_max or self.y_min >= self.y_max:
            raise ValueError("coordinate-plot axis minima must be less than maxima")
        if any(
            point.x < self.x_min
            or point.x > self.x_max
            or point.y < self.y_min
            or point.y > self.y_max
            for point in self.points
        ):
            raise ValueError("coordinate-plot points must stay inside its axes")
        return self


class FunctionSeries(StrictSpecModel):
    label: str = Field(min_length=1, max_length=24)
    points: list[CoordinatePoint] = Field(min_length=2, max_length=9)


class FunctionGraphBlock(StrictSpecModel):
    type: Literal["function-graph"]
    x_min: float = Field(default=-10, ge=-20, le=20)
    x_max: float = Field(default=10, ge=-20, le=20)
    y_min: float = Field(default=-10, ge=-20, le=20)
    y_max: float = Field(default=10, ge=-20, le=20)
    series: list[FunctionSeries] = Field(min_length=1, max_length=3)
    x_label: str | None = Field(default=None, min_length=1, max_length=16)
    y_label: str | None = Field(default=None, min_length=1, max_length=16)

    @model_validator(mode="after")
    def validate_series(self) -> "FunctionGraphBlock":
        if self.x_min >= self.x_max or self.y_min >= self.y_max:
            raise ValueError("function-graph axis minima must be less than maxima")
        labels = [series.label.strip().casefold() for series in self.series]
        if len(labels) != len(set(labels)):
            raise ValueError("function-graph series labels must be unique")
        for series in self.series:
            if any(
                point.x < self.x_min
                or point.x > self.x_max
                or point.y < self.y_min
                or point.y > self.y_max
                for point in series.points
            ):
                raise ValueError("function-graph points must stay inside its axes")
            x_values = [point.x for point in series.points]
            if any(left >= right for left, right in zip(x_values, x_values[1:])):
                raise ValueError(
                    "function-graph points must have strictly increasing x values"
                )
        return self


class GeometryLabel(StrictSpecModel):
    position: Literal["top", "right", "bottom", "left", "center"]
    text: str = Field(min_length=1, max_length=32)


GeometryPosition = Literal[
    "top",
    "top-left",
    "top-right",
    "right",
    "bottom-right",
    "bottom",
    "bottom-left",
    "left",
    "center",
]


class GeometryPoint(StrictSpecModel):
    position: GeometryPosition
    label: str = Field(min_length=1, max_length=16)


class GeometrySegment(StrictSpecModel):
    start: GeometryPosition
    end: GeometryPosition
    style: Literal["solid", "dashed"] = "solid"
    label: str | None = Field(default=None, min_length=1, max_length=24)


class GeometryModelBlock(StrictSpecModel):
    type: Literal["geometry-model"]
    shape: Literal["triangle", "rectangle", "circle"]
    triangle_type: Literal["scalene", "right", "isosceles", "equilateral"] | None = None
    labels: list[GeometryLabel] = Field(default_factory=list, max_length=5)
    points: list[GeometryPoint] = Field(default_factory=list, max_length=9)
    segments: list[GeometrySegment] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def validate_geometry(self) -> "GeometryModelBlock":
        label_positions = [label.position for label in self.labels]
        if len(label_positions) != len(set(label_positions)):
            raise ValueError("geometry-model label positions must be unique")
        point_positions = [point.position for point in self.points]
        if len(point_positions) != len(set(point_positions)):
            raise ValueError("geometry-model point positions must be unique")
        if self.shape != "triangle" and self.triangle_type is not None:
            raise ValueError("triangle_type is only valid for triangle geometry")
        allowed_positions = {
            "triangle": {
                "top",
                "right",
                "bottom-right",
                "bottom",
                "bottom-left",
                "left",
                "center",
            },
            "rectangle": {
                "top",
                "top-left",
                "top-right",
                "right",
                "bottom-right",
                "bottom",
                "bottom-left",
                "left",
                "center",
            },
            "circle": {"top", "right", "bottom", "left", "center"},
        }[self.shape]
        used_positions = {
            *(point.position for point in self.points),
            *(segment.start for segment in self.segments),
            *(segment.end for segment in self.segments),
        }
        if not used_positions.issubset(allowed_positions):
            raise ValueError(
                f"geometry-model positions must be valid anchors for a {self.shape}"
            )
        segment_pairs: set[tuple[str, str]] = set()
        for segment in self.segments:
            if segment.start == segment.end:
                raise ValueError("geometry-model segments require two different anchors")
            pair = tuple(sorted((segment.start, segment.end)))
            if pair in segment_pairs:
                raise ValueError("geometry-model segments must be unique")
            segment_pairs.add(pair)
        return self


def render_equation(block: EquationBlock) -> str:
    explanation = (
        f'<p class="cs-equation__explanation">{escape(block.explanation)}</p>'
        if block.explanation
        else ""
    )
    return (
        '<article class="cs-card cs-equation">'
        f'<p class="cs-equation__formula">$${escape(block.expression)}$$</p>'
        f"{explanation}</article>"
    )


def render_fraction(block: FractionModelBlock) -> str:
    segments = "".join(
        f'<span class="cs-fraction__segment{" is-filled" if index < block.numerator else ""}"></span>'
        for index in range(block.denominator)
    )
    label = block.label or f"{block.numerator}/{block.denominator}"
    return f"""
      <figure class="cs-card cs-fraction">
        <figcaption>{escape(label)}</figcaption>
        <span class="cs-fraction__bar" style="--cs-parts: {block.denominator}">{segments}</span>
        <strong>{block.numerator}/{block.denominator}</strong>
      </figure>"""


def render_number_line(block: NumberLineBlock) -> str:
    span = block.max_value - block.min_value
    markers = "".join(
        '<span class="cs-number-line__marker" '
        f'style="--cs-position: {((marker.value - block.min_value) / span) * 100:.3f}%">'
        f"<strong>{escape(marker.label or _format_number(marker.value))}</strong>"
        f'<i aria-hidden="true"></i></span>'
        for marker in block.markers
    )
    return f"""
      <figure class="cs-card cs-number-line" aria-label="Number line from {_format_number(block.min_value)} to {_format_number(block.max_value)}">
        <div class="cs-number-line__axis">{markers}</div>
        <figcaption>
          <span>{_format_number(block.min_value)}</span>
          <span>{_format_number(block.max_value)}</span>
        </figcaption>
      </figure>"""


def render_bar_model(block: BarModelBlock) -> str:
    parts = "".join(
        '<span class="cs-bar-model__part" '
        f'style="--cs-part: {_format_number(part.value)}">'
        f"<strong>{escape(part.label)}</strong><small>{_format_number(part.value)}</small></span>"
        for part in block.parts
    )
    total = (
        f"<figcaption>{escape(block.total_label)}</figcaption>"
        if block.total_label
        else ""
    )
    return f'<figure class="cs-card cs-bar-model"><div>{parts}</div>{total}</figure>'


def render_coordinate_plot(block: CoordinatePlotBlock) -> str:
    left, right, top, bottom = 56.0, 604.0, 28.0, 292.0

    def x_position(value: float) -> float:
        return left + ((value - block.x_min) / (block.x_max - block.x_min)) * (
            right - left
        )

    def y_position(value: float) -> float:
        return bottom - ((value - block.y_min) / (block.y_max - block.y_min)) * (
            bottom - top
        )

    vertical_grid = "".join(
        f'<line class="cs-plot__grid" x1="{left + (right - left) * index / 5:.2f}" y1="{top}" '
        f'x2="{left + (right - left) * index / 5:.2f}" y2="{bottom}" />'
        for index in range(6)
    )
    horizontal_grid = "".join(
        f'<line class="cs-plot__grid" x1="{left}" y1="{top + (bottom - top) * index / 5:.2f}" '
        f'x2="{right}" y2="{top + (bottom - top) * index / 5:.2f}" />'
        for index in range(6)
    )
    axis_x = y_position(0) if block.y_min <= 0 <= block.y_max else bottom
    axis_y = x_position(0) if block.x_min <= 0 <= block.x_max else left
    points = "".join(
        f'<g class="cs-plot__point"><circle cx="{x_position(point.x):.2f}" '
        f'cy="{y_position(point.y):.2f}" r="7" />'
        f'<text x="{x_position(point.x) + 11:.2f}" y="{y_position(point.y) - 10:.2f}">'
        f"{escape(point.label or f'({_format_number(point.x)}, {_format_number(point.y)})')}</text></g>"
        for point in block.points
    )
    x_label = escape(block.x_label or "x")
    y_label = escape(block.y_label or "y")
    return f"""
      <figure class="cs-card cs-coordinate-plot">
        <svg viewBox="0 0 640 320" role="img" aria-label="Coordinate plot">
          {vertical_grid}{horizontal_grid}
          <line class="cs-plot__axis" x1="{left}" y1="{axis_x:.2f}" x2="{right}" y2="{axis_x:.2f}" />
          <line class="cs-plot__axis" x1="{axis_y:.2f}" y1="{top}" x2="{axis_y:.2f}" y2="{bottom}" />
          <text class="cs-plot__axis-label" x="{right - 8}" y="{axis_x - 9:.2f}">{x_label}</text>
          <text class="cs-plot__axis-label" x="{axis_y + 10:.2f}" y="{top + 14}">{y_label}</text>
          <text class="cs-plot__bound" x="{left}" y="{bottom + 20}">{_format_number(block.x_min)}</text>
          <text class="cs-plot__bound" x="{right}" y="{bottom + 20}" text-anchor="end">{_format_number(block.x_max)}</text>
          {points}
        </svg>
      </figure>"""


def render_function_graph(block: FunctionGraphBlock) -> str:
    left, right, top, bottom = 56.0, 604.0, 28.0, 292.0

    def x_position(value: float) -> float:
        return left + ((value - block.x_min) / (block.x_max - block.x_min)) * (
            right - left
        )

    def y_position(value: float) -> float:
        return bottom - ((value - block.y_min) / (block.y_max - block.y_min)) * (
            bottom - top
        )

    vertical_grid = "".join(
        f'<line class="cs-plot__grid" x1="{left + (right - left) * index / 5:.2f}" y1="{top}" '
        f'x2="{left + (right - left) * index / 5:.2f}" y2="{bottom}" />'
        for index in range(6)
    )
    horizontal_grid = "".join(
        f'<line class="cs-plot__grid" x1="{left}" y1="{top + (bottom - top) * index / 5:.2f}" '
        f'x2="{right}" y2="{top + (bottom - top) * index / 5:.2f}" />'
        for index in range(6)
    )
    axis_x = y_position(0) if block.y_min <= 0 <= block.y_max else bottom
    axis_y = x_position(0) if block.x_min <= 0 <= block.x_max else left
    series_paths = "".join(
        _render_function_series(series, index, x_position, y_position)
        for index, series in enumerate(block.series, start=1)
    )
    legend = "".join(
        f'<li class="cs-function-graph__legend--{index}">{escape(series.label)}</li>'
        for index, series in enumerate(block.series, start=1)
    )
    return f"""
      <figure class="cs-card cs-function-graph">
        <svg viewBox="0 0 640 320" role="img" aria-label="Function graph">
          {vertical_grid}{horizontal_grid}
          <line class="cs-plot__axis" x1="{left}" y1="{axis_x:.2f}" x2="{right}" y2="{axis_x:.2f}" />
          <line class="cs-plot__axis" x1="{axis_y:.2f}" y1="{top}" x2="{axis_y:.2f}" y2="{bottom}" />
          <text class="cs-plot__axis-label" x="{right - 8}" y="{axis_x - 9:.2f}">{escape(block.x_label or "x")}</text>
          <text class="cs-plot__axis-label" x="{axis_y + 10:.2f}" y="{top + 14}">{escape(block.y_label or "y")}</text>
          {series_paths}
        </svg>
        <figcaption><ul>{legend}</ul></figcaption>
      </figure>"""


def _render_function_series(
    series: FunctionSeries,
    index: int,
    x_position: Callable[[float], float],
    y_position: Callable[[float], float],
) -> str:
    points = " ".join(
        f"{x_position(point.x):.2f},{y_position(point.y):.2f}"
        for point in series.points
    )
    markers = "".join(
        f'<circle cx="{x_position(point.x):.2f}" cy="{y_position(point.y):.2f}" r="4" />'
        for point in series.points
    )
    return (
        f'<g class="cs-function-graph__series cs-function-graph__series--{index}">'
        f'<polyline points="{points}" />{markers}</g>'
    )


def render_geometry(block: GeometryModelBlock) -> str:
    coordinates = _geometry_coordinates(block)
    shape = _render_geometry_shape(block, coordinates)
    constructions = "".join(
        _render_geometry_segment(segment, coordinates, index)
        for index, segment in enumerate(block.segments)
    )
    right_angle = (
        _render_right_angle(coordinates)
        if block.shape == "triangle" and block.triangle_type == "right"
        else ""
    )
    congruence_marks = _render_congruence_marks(block, coordinates)
    points = "".join(
        _render_geometry_point(point, coordinates) for point in block.points
    )
    label_offsets = {
        "top": (0, -25, "middle"),
        "right": (28, 5, "start"),
        "bottom": (0, 34, "middle"),
        "left": (-28, 5, "end"),
        "center": (0, 6, "middle"),
    }
    labels = "".join(
        '<text class="cs-geometry__label" '
        f'x="{coordinates[label.position][0] + label_offsets[label.position][0]:.1f}" '
        f'y="{coordinates[label.position][1] + label_offsets[label.position][1]:.1f}" '
        f'text-anchor="{label_offsets[label.position][2]}">{escape(label.text)}</text>'
        for label in block.labels
    )
    variant = (
        f" {block.triangle_type} triangle" if block.triangle_type else f" {block.shape}"
    )
    return f"""
      <figure class="cs-card cs-geometry">
        <svg viewBox="0 0 640 350" role="img" aria-label="{escape(variant.strip())} geometry model">
          <g class="cs-geometry__shape cs-geometry__shape--{block.shape}">{shape}</g>
          <g class="cs-geometry__constructions">{constructions}{right_angle}{congruence_marks}</g>
          <g class="cs-geometry__points">{points}</g>
          <g class="cs-geometry__labels">{labels}</g>
        </svg>
      </figure>"""


def _geometry_coordinates(
    block: GeometryModelBlock,
) -> dict[GeometryPosition, tuple[float, float]]:
    if block.shape == "triangle":
        triangle_vertices = {
            "right": ((135.0, 45.0), (135.0, 285.0), (540.0, 285.0)),
            "isosceles": ((320.0, 45.0), (115.0, 285.0), (525.0, 285.0)),
            "equilateral": ((320.0, 33.9), (175.0, 285.0), (465.0, 285.0)),
            "scalene": ((285.0, 45.0), (95.0, 285.0), (540.0, 285.0)),
        }
        top, bottom_left, bottom_right = triangle_vertices[
            block.triangle_type or "scalene"
        ]
        left = _midpoint(top, bottom_left)
        right = _midpoint(top, bottom_right)
        bottom = _midpoint(bottom_left, bottom_right)
        center = (
            (top[0] + bottom_left[0] + bottom_right[0]) / 3,
            (top[1] + bottom_left[1] + bottom_right[1]) / 3,
        )
        return {
            "top": top,
            "right": right,
            "bottom-right": bottom_right,
            "bottom": bottom,
            "bottom-left": bottom_left,
            "left": left,
            "center": center,
        }
    if block.shape == "rectangle":
        return {
            "top": (320.0, 55.0),
            "top-left": (105.0, 55.0),
            "top-right": (535.0, 55.0),
            "right": (535.0, 170.0),
            "bottom-right": (535.0, 285.0),
            "bottom": (320.0, 285.0),
            "bottom-left": (105.0, 285.0),
            "left": (105.0, 170.0),
            "center": (320.0, 170.0),
        }
    return {
        "top": (320.0, 45.0),
        "right": (445.0, 170.0),
        "bottom": (320.0, 295.0),
        "left": (195.0, 170.0),
        "center": (320.0, 170.0),
    }


def _render_geometry_shape(
    block: GeometryModelBlock,
    coordinates: dict[GeometryPosition, tuple[float, float]],
) -> str:
    if block.shape == "triangle":
        return '<polygon points="{}" />'.format(
            " ".join(
                f"{coordinates[position][0]:.1f},{coordinates[position][1]:.1f}"
                for position in ("top", "bottom-left", "bottom-right")
            )
        )
    if block.shape == "rectangle":
        return '<rect x="105" y="55" width="430" height="230" rx="8" />'
    return '<circle cx="320" cy="170" r="125" />'


def _render_geometry_segment(
    segment: GeometrySegment,
    coordinates: dict[GeometryPosition, tuple[float, float]],
    index: int,
) -> str:
    start = coordinates[segment.start]
    end = coordinates[segment.end]
    label = ""
    if segment.label:
        label_offset = -12 if index % 2 == 0 else 23
        label = (
            '<text class="cs-geometry__segment-label" '
            f'x="{(start[0] + end[0]) / 2:.1f}" '
            f'y="{(start[1] + end[1]) / 2 + label_offset:.1f}">'
            f"{escape(segment.label)}</text>"
        )
    return (
        f'<g class="cs-geometry__segment cs-geometry__segment--{segment.style}">'
        f'<line x1="{start[0]:.1f}" y1="{start[1]:.1f}" '
        f'x2="{end[0]:.1f}" y2="{end[1]:.1f}" />{label}</g>'
    )


def _render_geometry_point(
    point: GeometryPoint,
    coordinates: dict[GeometryPosition, tuple[float, float]],
) -> str:
    x, y = coordinates[point.position]
    offsets = {
        "top": (0, -14, "middle"),
        "top-left": (-10, -12, "end"),
        "top-right": (10, -12, "start"),
        "right": (14, 5, "start"),
        "bottom-right": (10, 24, "start"),
        "bottom": (0, 25, "middle"),
        "bottom-left": (-10, 24, "end"),
        "left": (-14, 5, "end"),
        "center": (13, -11, "start"),
    }
    offset_x, offset_y, anchor = offsets[point.position]
    return (
        f'<g class="cs-geometry__point"><circle cx="{x:.1f}" cy="{y:.1f}" r="6" />'
        f'<text x="{x + offset_x:.1f}" y="{y + offset_y:.1f}" '
        f'text-anchor="{anchor}">{escape(point.label)}</text></g>'
    )


def _render_right_angle(
    coordinates: dict[GeometryPosition, tuple[float, float]],
) -> str:
    x, y = coordinates["bottom-left"]
    return (
        f'<path class="cs-geometry__right-angle" '
        f'd="M {x:.1f} {y - 27:.1f} H {x + 27:.1f} V {y:.1f}" />'
    )


def _render_congruence_marks(
    block: GeometryModelBlock,
    coordinates: dict[GeometryPosition, tuple[float, float]],
) -> str:
    if block.shape != "triangle" or block.triangle_type not in {
        "isosceles",
        "equilateral",
    }:
        return ""
    sides = [("top", "bottom-left"), ("top", "bottom-right")]
    if block.triangle_type == "equilateral":
        sides.append(("bottom-left", "bottom-right"))
    return "".join(
        _render_congruence_mark(coordinates[start], coordinates[end])
        for start, end in sides
    )


def _render_congruence_mark(
    start: tuple[float, float], end: tuple[float, float]
) -> str:
    midpoint = _midpoint(start, end)
    delta_x, delta_y = end[0] - start[0], end[1] - start[1]
    length = (delta_x**2 + delta_y**2) ** 0.5
    offset_x, offset_y = (-delta_y / length * 9, delta_x / length * 9)
    return (
        '<line class="cs-geometry__congruence" '
        f'x1="{midpoint[0] - offset_x:.1f}" y1="{midpoint[1] - offset_y:.1f}" '
        f'x2="{midpoint[0] + offset_x:.1f}" y2="{midpoint[1] + offset_y:.1f}" />'
    )


def _midpoint(
    first: tuple[float, float], second: tuple[float, float]
) -> tuple[float, float]:
    return ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)


def _format_number(value: float) -> str:
    return (
        str(int(value))
        if value.is_integer()
        else f"{value:.2f}".rstrip("0").rstrip(".")
    )


MATH_BLOCKS = (
    BlockDefinition(
        EquationBlock,
        BlockGuide(
            "equation",
            "symbolic",
            "mathematical or scientific symbolic reasoning",
            "a large typeset formula with an optional explanation",
            "the notation itself carries the teaching meaning",
            '{"type":"equation","expression":"F = ma","explanation":"Force equals mass times acceleration."}',
            orientation="horizontal",
            preferred_width="wide",
        ),
        render_equation,
    ),
    BlockDefinition(
        FractionModelBlock,
        BlockGuide(
            "fraction-model",
            "visual",
            "a part-to-whole fraction",
            "an equal-segment bar with the numerator segments filled",
            "showing a proper fraction or one whole",
            '{"type":"fraction-model","numerator":3,"denominator":4,"label":"Three fourths"}',
        ),
        render_fraction,
    ),
    BlockDefinition(
        NumberLineBlock,
        BlockGuide(
            "number-line",
            "visual",
            "positions, order, intervals, and magnitude on a number line",
            "a horizontal axis with proportionally placed labeled markers",
            "teaching integers, decimals, fractions, ranges, or measurement",
            '{"type":"number-line","min_value":-5,"max_value":5,"markers":[{"value":-2,"label":"-2"},{"value":3,"label":"3"}]}',
        ),
        render_number_line,
    ),
    BlockDefinition(
        BarModelBlock,
        BlockGuide(
            "bar-model",
            "visual",
            "part-whole, ratio, and word-problem quantities",
            "one proportional bar divided into labeled parts",
            "the relative size of two to six positive quantities matters",
            '{"type":"bar-model","parts":[{"label":"Read","value":30},{"label":"Left","value":10}],"total_label":"40 pages"}',
        ),
        render_bar_model,
    ),
    BlockDefinition(
        CoordinatePlotBlock,
        BlockGuide(
            "coordinate-plot",
            "visual",
            "points and spatial relationships on a coordinate plane",
            "a bounded x-y grid with labeled plotted points",
            "teaching coordinates, transformations, or measured pairs",
            '{"type":"coordinate-plot","x_min":-5,"x_max":5,"y_min":-5,"y_max":5,"points":[{"x":2,"y":3,"label":"A"}]}',
        ),
        render_coordinate_plot,
    ),
    BlockDefinition(
        FunctionGraphBlock,
        BlockGuide(
            "function-graph",
            "visual",
            "one to three mathematical relationships shown as connected sampled points",
            "a bounded coordinate grid with compiler-connected series and a color legend",
            "comparing linear, quadratic, or other functions when curve shape and rate of change matters; provide ordered sampled points",
            '{"type":"function-graph","x_min":-2,"x_max":2,"y_min":-1,"y_max":4,"series":[{"label":"y = x²","points":[{"x":-2,"y":4},{"x":-1,"y":1},{"x":0,"y":0},{"x":1,"y":1},{"x":2,"y":4}]}]}',
        ),
        render_function_graph,
    ),
    BlockDefinition(
        GeometryModelBlock,
        BlockGuide(
            "geometry-model",
            "visual",
            "a geometric figure with meaningful sides, points, and construction lines",
            "a platform-drawn triangle, rectangle, or circle with semantic anchors, accurate right-angle markings, and optional internal segments",
            "the figure, its measurements, or relationships such as diagonals, radii, cevians, and concurrency are central to the explanation",
            '{"type":"geometry-model","shape":"triangle","triangle_type":"right","labels":[{"position":"left","text":"leg b"},{"position":"bottom","text":"leg a"},{"position":"right","text":"hypotenuse c"}],"points":[{"position":"bottom-left","label":"C"}]}',
        ),
        render_geometry,
    ),
)
