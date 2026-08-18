from typing import Annotated

from pydantic import Field

from backend.app.lessons.formats.slides.blocks.biology import (
    CellDiagramBlock,
    CellFeature,
)
from backend.app.lessons.formats.slides.blocks.chemistry import (
    ParticleDiagramBlock,
    ParticleSample,
    ParticleSpecies,
    ReactionDiagramBlock,
    ReactionTerm,
)
from backend.app.lessons.formats.slides.blocks.content import (
    BulletsBlock,
    CalloutBlock,
    StatementBlock,
    StepsBlock,
)
from backend.app.lessons.formats.slides.blocks.custom import (
    CustomHtmlBlock,
)
from backend.app.lessons.formats.slides.blocks.data import (
    BarChartBlock,
    BarChartItem,
    TimelineBlock,
    TimelineEvent,
)
from backend.app.lessons.formats.slides.blocks.diagrams import (
    CauseEffectDiagramBlock,
    CauseGroup,
    ComparisonBlock,
    ConcentricDiagramBlock,
    ConcentricRing,
    CycleBlock,
    DiagramLayer,
    DiagramNode,
    FlowDiagramBlock,
    FlowStage,
    HierarchyBranch,
    HierarchyTreeBlock,
    LabeledDiagramBlock,
    LayerDiagramBlock,
    MatrixDiagramBlock,
    NetworkDiagramBlock,
    NetworkEdge,
    NetworkLayer,
    NetworkNode,
    ProcessBlock,
    PyramidDiagramBlock,
    PyramidLevel,
    QuadrantDiagramBlock,
    QuadrantRegion,
    SpectrumBand,
    SpectrumDiagramBlock,
    VennDiagramBlock,
)
from backend.app.lessons.formats.slides.blocks.math import (
    BarModelBlock,
    BarModelPart,
    CoordinatePlotBlock,
    CoordinatePoint,
    EquationBlock,
    FractionModelBlock,
    FunctionGraphBlock,
    FunctionSeries,
    GeometryLabel,
    GeometryModelBlock,
    GeometryPoint,
    GeometrySegment,
    NumberLineBlock,
    NumberLineMarker,
)
from backend.app.lessons.formats.slides.blocks.physics import (
    ForceArrow,
    ForceDiagramBlock,
    WaveDiagramBlock,
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
    | CycleBlock
    | PyramidDiagramBlock
    | HierarchyTreeBlock
    | FlowDiagramBlock
    | VennDiagramBlock
    | CauseEffectDiagramBlock
    | LayerDiagramBlock
    | NetworkDiagramBlock
    | QuadrantDiagramBlock
    | SpectrumDiagramBlock
    | ConcentricDiagramBlock
    | MatrixDiagramBlock
    | FunctionGraphBlock
    | ForceDiagramBlock
    | WaveDiagramBlock
    | ParticleDiagramBlock
    | ReactionDiagramBlock
    | CellDiagramBlock
    | CustomHtmlBlock,
    Field(discriminator="type"),
]


__all__ = [
    "BarChartBlock",
    "BarChartItem",
    "BarModelBlock",
    "BarModelPart",
    "BulletsBlock",
    "CalloutBlock",
    "CellDiagramBlock",
    "CellFeature",
    "CauseEffectDiagramBlock",
    "CauseGroup",
    "ConcentricDiagramBlock",
    "ConcentricRing",
    "ComparisonBlock",
    "CoordinatePlotBlock",
    "CoordinatePoint",
    "CustomHtmlBlock",
    "CycleBlock",
    "DiagramNode",
    "DiagramLayer",
    "EquationBlock",
    "FlowDiagramBlock",
    "FlowStage",
    "FractionModelBlock",
    "FunctionGraphBlock",
    "FunctionSeries",
    "ForceArrow",
    "ForceDiagramBlock",
    "GeometryLabel",
    "GeometryModelBlock",
    "GeometryPoint",
    "GeometrySegment",
    "HierarchyBranch",
    "HierarchyTreeBlock",
    "LayerDiagramBlock",
    "LabeledDiagramBlock",
    "MatrixDiagramBlock",
    "NumberLineBlock",
    "NumberLineMarker",
    "ParticleDiagramBlock",
    "ParticleSample",
    "ParticleSpecies",
    "NetworkDiagramBlock",
    "NetworkEdge",
    "NetworkLayer",
    "NetworkNode",
    "ProcessBlock",
    "PyramidDiagramBlock",
    "PyramidLevel",
    "QuadrantDiagramBlock",
    "QuadrantRegion",
    "ReactionDiagramBlock",
    "ReactionTerm",
    "SlideBlock",
    "StatementBlock",
    "StepsBlock",
    "SpectrumBand",
    "SpectrumDiagramBlock",
    "TimelineBlock",
    "TimelineEvent",
    "VennDiagramBlock",
    "WaveDiagramBlock",
]
