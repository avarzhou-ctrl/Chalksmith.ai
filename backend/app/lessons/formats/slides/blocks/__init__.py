from typing import Annotated

from pydantic import Field

from backend.app.lessons.formats.slides.blocks.content import (
    BulletsBlock,
    CalloutBlock,
    StatementBlock,
    StepsBlock,
)
from backend.app.lessons.formats.slides.blocks.data import (
    BarChartBlock,
    BarChartItem,
    TimelineBlock,
    TimelineEvent,
)
from backend.app.lessons.formats.slides.blocks.diagrams import (
    ComparisonBlock,
    CycleBlock,
    LabeledDiagramBlock,
    ProcessBlock,
)
from backend.app.lessons.formats.slides.blocks.math import (
    BarModelBlock,
    BarModelPart,
    CoordinatePlotBlock,
    CoordinatePoint,
    EquationBlock,
    FractionModelBlock,
    GeometryLabel,
    GeometryModelBlock,
    NumberLineBlock,
    NumberLineMarker,
)


SlideBlock = Annotated[
    StatementBlock
    | BulletsBlock
    | CalloutBlock
    | StepsBlock
    | EquationBlock
    | FractionModelBlock
    | NumberLineBlock
    | BarModelBlock
    | CoordinatePlotBlock
    | GeometryModelBlock
    | BarChartBlock
    | TimelineBlock
    | ComparisonBlock
    | ProcessBlock
    | LabeledDiagramBlock
    | CycleBlock,
    Field(discriminator="type"),
]


__all__ = [
    "BarChartBlock",
    "BarChartItem",
    "BarModelBlock",
    "BarModelPart",
    "BulletsBlock",
    "CalloutBlock",
    "ComparisonBlock",
    "CoordinatePlotBlock",
    "CoordinatePoint",
    "CycleBlock",
    "EquationBlock",
    "FractionModelBlock",
    "GeometryLabel",
    "GeometryModelBlock",
    "LabeledDiagramBlock",
    "NumberLineBlock",
    "NumberLineMarker",
    "ProcessBlock",
    "SlideBlock",
    "StatementBlock",
    "StepsBlock",
    "TimelineBlock",
    "TimelineEvent",
]
