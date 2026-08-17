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


class GeometryLabel(StrictSpecModel):
    position: Literal["top", "right", "bottom", "left", "center"]
    text: str = Field(min_length=1, max_length=32)


class GeometryModelBlock(StrictSpecModel):
    type: Literal["geometry-model"]
    shape: Literal["triangle", "rectangle", "circle"]
    labels: list[GeometryLabel] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def validate_labels(self) -> "GeometryModelBlock":
        positions = [label.position for label in self.labels]
        if len(positions) != len(set(positions)):
            raise ValueError("geometry-model label positions must be unique")
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


def render_geometry(block: GeometryModelBlock) -> str:
    shapes = {
        "triangle": '<polygon points="320,45 115,255 525,255" />',
        "rectangle": '<rect x="125" y="65" width="390" height="190" rx="8" />',
        "circle": '<circle cx="320" cy="155" r="110" />',
    }
    label_positions = {
        "top": (320, 28, "middle"),
        "right": (620, 160, "end"),
        "bottom": (320, 292, "middle"),
        "left": (20, 160, "start"),
        "center": (320, 162, "middle"),
    }
    labels = "".join(
        f'<text class="cs-geometry__label" x="{label_positions[label.position][0]}" '
        f'y="{label_positions[label.position][1]}" '
        f'text-anchor="{label_positions[label.position][2]}">{escape(label.text)}</text>'
        for label in block.labels
    )
    return f"""
      <figure class="cs-card cs-geometry">
        <svg viewBox="0 0 640 310" role="img" aria-label="{escape(block.shape)} geometry model">
          <g class="cs-geometry__shape cs-geometry__shape--{block.shape}">{shapes[block.shape]}</g>
          {labels}
        </svg>
      </figure>"""


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
        GeometryModelBlock,
        BlockGuide(
            "geometry-model",
            "visual",
            "a geometric shape and named measurements or features",
            "a platform-drawn triangle, rectangle, or circle with labels in named slots",
            "the shape and its dimensions are central to the explanation",
            '{"type":"geometry-model","shape":"triangle","labels":[{"position":"bottom","text":"base = 8 cm"},{"position":"right","text":"height = 5 cm"}]}',
        ),
        render_geometry,
    ),
)
