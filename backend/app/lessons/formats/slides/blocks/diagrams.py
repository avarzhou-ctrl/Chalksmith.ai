from html import escape
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition, BlockGuide


class ComparisonBlock(StrictSpecModel):
    type: Literal["comparison"]
    left_title: str = Field(min_length=1, max_length=48)
    left_items: list[str] = Field(min_length=1, max_length=4)
    right_title: str = Field(min_length=1, max_length=48)
    right_items: list[str] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def validate_items(self) -> "ComparisonBlock":
        items = [*self.left_items, *self.right_items]
        if any(not item.strip() or len(item) > 100 for item in items):
            raise ValueError("comparison items must contain 1 to 100 characters")
        return self


class ProcessBlock(StrictSpecModel):
    type: Literal["process"]
    steps: list[str] = Field(min_length=2, max_length=5)

    @model_validator(mode="after")
    def validate_steps(self) -> "ProcessBlock":
        if any(not step.strip() or len(step) > 80 for step in self.steps):
            raise ValueError("process steps must contain 1 to 80 characters")
        return self


class LabeledDiagramBlock(StrictSpecModel):
    type: Literal["labeled-diagram"]
    subject: str = Field(min_length=1, max_length=40)
    labels: list[str] = Field(min_length=2, max_length=6)

    @model_validator(mode="after")
    def validate_labels(self) -> "LabeledDiagramBlock":
        if any(not label.strip() or len(label) > 40 for label in self.labels):
            raise ValueError("labeled-diagram labels must contain 1 to 40 characters")
        return self


class CycleBlock(StrictSpecModel):
    type: Literal["cycle"]
    steps: list[str] = Field(min_length=3, max_length=6)

    @model_validator(mode="after")
    def validate_steps(self) -> "CycleBlock":
        if any(not step.strip() or len(step) > 48 for step in self.steps):
            raise ValueError("cycle steps must contain 1 to 48 characters")
        return self


class PyramidLevel(StrictSpecModel):
    label: str = Field(min_length=1, max_length=36)
    detail: str | None = Field(default=None, min_length=1, max_length=64)
    value: str | None = Field(default=None, min_length=1, max_length=24)


class PyramidDiagramBlock(StrictSpecModel):
    type: Literal["pyramid-diagram"]
    levels: list[PyramidLevel] = Field(min_length=3, max_length=5)
    trend_label: str | None = Field(default=None, min_length=1, max_length=72)

    @model_validator(mode="after")
    def validate_levels(self) -> "PyramidDiagramBlock":
        labels = [level.label.strip().casefold() for level in self.levels]
        if any(not label for label in labels):
            raise ValueError("pyramid level labels cannot be blank")
        if len(labels) != len(set(labels)):
            raise ValueError("pyramid level labels must be unique")
        return self


class DiagramNode(StrictSpecModel):
    label: str = Field(min_length=1, max_length=32)
    detail: str | None = Field(default=None, min_length=1, max_length=48)


class HierarchyBranch(StrictSpecModel):
    label: str = Field(min_length=1, max_length=28)
    children: list[DiagramNode] = Field(min_length=1, max_length=3)


class HierarchyTreeBlock(StrictSpecModel):
    type: Literal["hierarchy-tree"]
    root: DiagramNode
    branches: list[HierarchyBranch] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def validate_branches(self) -> "HierarchyTreeBlock":
        labels = [branch.label.strip().casefold() for branch in self.branches]
        if any(not label for label in labels):
            raise ValueError("hierarchy branch labels cannot be blank")
        if len(labels) != len(set(labels)):
            raise ValueError("hierarchy branch labels must be unique")
        return self


class FlowStage(StrictSpecModel):
    label: str = Field(min_length=1, max_length=28)
    nodes: list[DiagramNode] = Field(min_length=1, max_length=3)


class FlowDiagramBlock(StrictSpecModel):
    type: Literal["flow-diagram"]
    stages: list[FlowStage] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def validate_nodes(self) -> "FlowDiagramBlock":
        if sum(len(stage.nodes) for stage in self.stages) > 8:
            raise ValueError("flow diagrams support at most eight nodes")
        return self


class VennDiagramBlock(StrictSpecModel):
    type: Literal["venn-diagram"]
    left_title: str = Field(min_length=1, max_length=28)
    left_items: list[str] = Field(min_length=1, max_length=3)
    right_title: str = Field(min_length=1, max_length=28)
    right_items: list[str] = Field(min_length=1, max_length=3)
    overlap_title: str = Field(min_length=1, max_length=20)
    overlap_items: list[str] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_items(self) -> "VennDiagramBlock":
        zones = [self.left_items, self.overlap_items, self.right_items]
        items = [item for zone in zones for item in zone]
        if any(not item.strip() or len(item) > 38 for item in items):
            raise ValueError("venn items must contain 1 to 38 characters")
        normalized = [item.strip().casefold() for item in items]
        if len(normalized) != len(set(normalized)):
            raise ValueError("venn items must appear in exactly one region")
        if self.left_title.strip().casefold() == self.right_title.strip().casefold():
            raise ValueError("venn set titles must be different")
        return self


class CauseGroup(StrictSpecModel):
    label: str = Field(min_length=1, max_length=28)
    causes: list[str] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_causes(self) -> "CauseGroup":
        if any(not cause.strip() or len(cause) > 42 for cause in self.causes):
            raise ValueError("causes must contain 1 to 42 characters")
        return self


class CauseEffectDiagramBlock(StrictSpecModel):
    type: Literal["cause-effect-diagram"]
    effect_label: str = Field(min_length=1, max_length=20)
    effect: str = Field(min_length=1, max_length=48)
    effect_detail: str | None = Field(default=None, min_length=1, max_length=72)
    groups: list[CauseGroup] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def validate_groups(self) -> "CauseEffectDiagramBlock":
        if sum(len(group.causes) for group in self.groups) > 8:
            raise ValueError("cause-effect diagrams support at most eight causes")
        labels = [group.label.strip().casefold() for group in self.groups]
        if len(labels) != len(set(labels)):
            raise ValueError("cause group labels must be unique")
        causes = [
            cause.strip().casefold() for group in self.groups for cause in group.causes
        ]
        if len(causes) != len(set(causes)):
            raise ValueError("causes must be unique across groups")
        return self


class DiagramLayer(StrictSpecModel):
    label: str = Field(min_length=1, max_length=32)
    detail: str | None = Field(default=None, min_length=1, max_length=64)
    property: str | None = Field(default=None, min_length=1, max_length=28)


class LayerDiagramBlock(StrictSpecModel):
    type: Literal["layer-diagram"]
    layers: list[DiagramLayer] = Field(min_length=3, max_length=6)
    order_label: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_layers(self) -> "LayerDiagramBlock":
        labels = [layer.label.strip().casefold() for layer in self.layers]
        if len(labels) != len(set(labels)):
            raise ValueError("layer labels must be unique")
        return self


class NetworkNode(StrictSpecModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,15}$")
    label: str = Field(min_length=1, max_length=24)
    detail: str | None = Field(default=None, min_length=1, max_length=36)


class NetworkLayer(StrictSpecModel):
    label: str = Field(min_length=1, max_length=22)
    nodes: list[NetworkNode] = Field(min_length=1, max_length=3)


class NetworkEdge(StrictSpecModel):
    from_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,15}$")
    to_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,15}$")


class NetworkDiagramBlock(StrictSpecModel):
    type: Literal["network-diagram"]
    description: str = Field(min_length=1, max_length=100)
    layers: list[NetworkLayer] = Field(min_length=2, max_length=4)
    edges: list[NetworkEdge] = Field(min_length=2, max_length=12)

    @model_validator(mode="after")
    def validate_network(self) -> "NetworkDiagramBlock":
        layer_labels = [layer.label.strip().casefold() for layer in self.layers]
        if len(layer_labels) != len(set(layer_labels)):
            raise ValueError("network layer labels must be unique")
        nodes = [node for layer in self.layers for node in layer.nodes]
        if len(nodes) < 3 or len(nodes) > 10:
            raise ValueError("network diagrams require three to ten nodes")
        node_layers: dict[str, int] = {}
        for layer_index, layer in enumerate(self.layers):
            for node in layer.nodes:
                if node.id in node_layers:
                    raise ValueError("network node ids must be unique")
                node_layers[node.id] = layer_index
        edge_pairs = {(edge.from_id, edge.to_id) for edge in self.edges}
        if len(edge_pairs) != len(self.edges):
            raise ValueError("network edges must be unique")
        for edge in self.edges:
            if edge.from_id not in node_layers or edge.to_id not in node_layers:
                raise ValueError("network edges must reference declared node ids")
            if node_layers[edge.from_id] >= node_layers[edge.to_id]:
                raise ValueError(
                    "network edges must point from an earlier to a later layer"
                )
        return self


class QuadrantRegion(StrictSpecModel):
    label: str = Field(min_length=1, max_length=28)
    items: list[str] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_items(self) -> "QuadrantRegion":
        if any(not item.strip() or len(item) > 32 for item in self.items):
            raise ValueError("quadrant items must contain 1 to 32 characters")
        return self


class QuadrantDiagramBlock(StrictSpecModel):
    type: Literal["quadrant-diagram"]
    x_low_label: str = Field(min_length=1, max_length=24)
    x_high_label: str = Field(min_length=1, max_length=24)
    y_low_label: str = Field(min_length=1, max_length=24)
    y_high_label: str = Field(min_length=1, max_length=24)
    top_left: QuadrantRegion
    top_right: QuadrantRegion
    bottom_left: QuadrantRegion
    bottom_right: QuadrantRegion

    @model_validator(mode="after")
    def validate_axes_and_regions(self) -> "QuadrantDiagramBlock":
        if self.x_low_label.strip().casefold() == self.x_high_label.strip().casefold():
            raise ValueError("quadrant x-axis endpoints must be different")
        if self.y_low_label.strip().casefold() == self.y_high_label.strip().casefold():
            raise ValueError("quadrant y-axis endpoints must be different")
        regions = [self.top_left, self.top_right, self.bottom_left, self.bottom_right]
        labels = [region.label.strip().casefold() for region in regions]
        if len(labels) != len(set(labels)):
            raise ValueError("quadrant region labels must be unique")
        return self


class SpectrumBand(StrictSpecModel):
    label: str = Field(min_length=1, max_length=22)
    detail: str | None = Field(default=None, min_length=1, max_length=36)


class SpectrumDiagramBlock(StrictSpecModel):
    type: Literal["spectrum-diagram"]
    bands: list[SpectrumBand] = Field(min_length=3, max_length=7)
    low_label: str = Field(min_length=1, max_length=28)
    high_label: str = Field(min_length=1, max_length=28)
    trend_label: str | None = Field(default=None, min_length=1, max_length=56)

    @model_validator(mode="after")
    def validate_bands(self) -> "SpectrumDiagramBlock":
        labels = [band.label.strip().casefold() for band in self.bands]
        if len(labels) != len(set(labels)):
            raise ValueError("spectrum band labels must be unique")
        if self.low_label.strip().casefold() == self.high_label.strip().casefold():
            raise ValueError("spectrum endpoint labels must be different")
        return self


class ConcentricRing(StrictSpecModel):
    label: str = Field(min_length=1, max_length=30)
    detail: str | None = Field(default=None, min_length=1, max_length=48)


class ConcentricDiagramBlock(StrictSpecModel):
    type: Literal["concentric-diagram"]
    rings: list[ConcentricRing] = Field(min_length=2, max_length=5)
    direction_label: str | None = Field(default=None, min_length=1, max_length=48)

    @model_validator(mode="after")
    def validate_rings(self) -> "ConcentricDiagramBlock":
        labels = [ring.label.strip().casefold() for ring in self.rings]
        if len(labels) != len(set(labels)):
            raise ValueError("concentric ring labels must be unique")
        return self


class MatrixDiagramBlock(StrictSpecModel):
    type: Literal["matrix-diagram"]
    row_axis_label: str | None = Field(default=None, min_length=1, max_length=28)
    column_axis_label: str | None = Field(default=None, min_length=1, max_length=28)
    row_headers: list[str] = Field(min_length=2, max_length=4)
    column_headers: list[str] = Field(min_length=2, max_length=4)
    cells: list[list[str]] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def validate_matrix(self) -> "MatrixDiagramBlock":
        if len(self.cells) != len(self.row_headers):
            raise ValueError("matrix rows must match the row headers")
        if any(len(row) != len(self.column_headers) for row in self.cells):
            raise ValueError("matrix columns must match the column headers")
        headers = [*self.row_headers, *self.column_headers]
        if any(not header.strip() or len(header) > 28 for header in headers):
            raise ValueError("matrix headers must contain 1 to 28 characters")
        if len({header.strip() for header in self.row_headers}) != len(
            self.row_headers
        ):
            raise ValueError("matrix row headers must be unique")
        if len({header.strip() for header in self.column_headers}) != len(
            self.column_headers
        ):
            raise ValueError("matrix column headers must be unique")
        if any(
            not cell.strip() or len(cell) > 42 for row in self.cells for cell in row
        ):
            raise ValueError("matrix cells must contain 1 to 42 characters")
        return self


def render_comparison(block: ComparisonBlock) -> str:
    left = "".join(f"<li>{escape(item)}</li>" for item in block.left_items)
    right = "".join(f"<li>{escape(item)}</li>" for item in block.right_items)
    return f"""
      <article class="cs-comparison">
        <div class="cs-card">
          <h3>{escape(block.left_title)}</h3>
          <ul>{left}</ul>
        </div>
        <div class="cs-card">
          <h3>{escape(block.right_title)}</h3>
          <ul>{right}</ul>
        </div>
      </article>"""


def render_process(block: ProcessBlock) -> str:
    steps = "".join(
        f"<li><span>{index}</span><p>{escape(step)}</p></li>"
        for index, step in enumerate(block.steps, start=1)
    )
    return f'<article class="cs-card cs-process"><ol>{steps}</ol></article>'


def render_labeled_diagram(block: LabeledDiagramBlock) -> str:
    labels = "".join(f"<li>{escape(label)}</li>" for label in block.labels)
    return f"""
      <figure class="cs-card cs-labeled-diagram">
        <div class="cs-labeled-diagram__subject">{escape(block.subject)}</div>
        <ul>{labels}</ul>
      </figure>"""


def render_cycle(block: CycleBlock) -> str:
    steps = "".join(
        f"<li><span>{index}</span><p>{escape(step)}</p></li>"
        for index, step in enumerate(block.steps, start=1)
    )
    return f"""
      <figure class="cs-card cs-cycle">
        <ol>{steps}</ol>
        <figcaption aria-hidden="true">↺</figcaption>
      </figure>"""


def render_pyramid_diagram(block: PyramidDiagramBlock) -> str:
    level_count = len(block.levels)
    levels = "".join(
        _render_pyramid_level(level, index, level_count)
        for index, level in enumerate(block.levels)
    )
    trend = (
        '<figcaption class="cs-pyramid__trend"><span aria-hidden="true">↑</span>'
        f"<p>{escape(block.trend_label)}</p></figcaption>"
        if block.trend_label
        else ""
    )
    return f"""
      <figure class="cs-card cs-pyramid">
        <ol aria-label="Pyramid levels from top to bottom">{levels}</ol>
        {trend}
      </figure>"""


def _render_pyramid_level(level: PyramidLevel, index: int, level_count: int) -> str:
    width = 38 if level_count == 1 else 38 + (62 * index / (level_count - 1))
    detail = f"<small>{escape(level.detail)}</small>" if level.detail else ""
    value = f"<em>{escape(level.value)}</em>" if level.value else ""
    return (
        f'<li style="--cs-pyramid-width: {width:.1f}%">'
        f"<span><strong>{escape(level.label)}</strong>{detail}</span>{value}</li>"
    )


def render_hierarchy_tree(block: HierarchyTreeBlock) -> str:
    root_detail = (
        f"<small>{escape(block.root.detail)}</small>" if block.root.detail else ""
    )
    branches = "".join(_render_hierarchy_branch(branch) for branch in block.branches)
    return f"""
      <figure class="cs-card cs-hierarchy">
        <div class="cs-hierarchy__root">
          <strong>{escape(block.root.label)}</strong>{root_detail}
        </div>
        <div class="cs-hierarchy__stem" aria-hidden="true"></div>
        <ol class="cs-hierarchy__branches" style="--cs-hierarchy-columns: {len(block.branches)}">
          {branches}
        </ol>
      </figure>"""


def _render_hierarchy_branch(branch: HierarchyBranch) -> str:
    children = "".join(_render_diagram_node(node) for node in branch.children)
    return (
        '<li class="cs-hierarchy__branch">'
        f"<strong>{escape(branch.label)}</strong><ul>{children}</ul></li>"
    )


def render_flow_diagram(block: FlowDiagramBlock) -> str:
    stages = "".join(_render_flow_stage(stage) for stage in block.stages)
    return f"""
      <figure class="cs-card cs-flow-diagram">
        <ol style="--cs-flow-columns: {len(block.stages)}">{stages}</ol>
      </figure>"""


def _render_flow_stage(stage: FlowStage) -> str:
    nodes = "".join(_render_diagram_node(node) for node in stage.nodes)
    return (
        '<li class="cs-flow-diagram__stage">'
        f'<p class="cs-flow-diagram__label">{escape(stage.label)}</p>'
        f"<ul>{nodes}</ul></li>"
    )


def _render_diagram_node(node: DiagramNode) -> str:
    detail = f"<small>{escape(node.detail)}</small>" if node.detail else ""
    return f"<li><strong>{escape(node.label)}</strong>{detail}</li>"


def render_venn_diagram(block: VennDiagramBlock) -> str:
    left_items = "".join(f"<li>{escape(item)}</li>" for item in block.left_items)
    right_items = "".join(f"<li>{escape(item)}</li>" for item in block.right_items)
    overlap_items = "".join(f"<li>{escape(item)}</li>" for item in block.overlap_items)
    return f"""
      <figure class="cs-card cs-venn">
        <div class="cs-venn__region cs-venn__region--left">
          <h3>{escape(block.left_title)}</h3><ul>{left_items}</ul>
        </div>
        <div class="cs-venn__region cs-venn__region--overlap">
          <h3>{escape(block.overlap_title)}</h3><ul>{overlap_items}</ul>
        </div>
        <div class="cs-venn__region cs-venn__region--right">
          <h3>{escape(block.right_title)}</h3><ul>{right_items}</ul>
        </div>
      </figure>"""


def render_cause_effect_diagram(block: CauseEffectDiagramBlock) -> str:
    groups = "".join(_render_cause_group(group) for group in block.groups)
    detail = (
        f"<small>{escape(block.effect_detail)}</small>" if block.effect_detail else ""
    )
    return f"""
      <figure class="cs-card cs-cause-effect">
        <ol>{groups}</ol>
        <div class="cs-cause-effect__arrow" aria-hidden="true">→</div>
        <figcaption><span>{escape(block.effect_label)}</span><strong>{escape(block.effect)}</strong>{detail}</figcaption>
      </figure>"""


def _render_cause_group(group: CauseGroup) -> str:
    causes = "".join(f"<li>{escape(cause)}</li>" for cause in group.causes)
    return f"<li><strong>{escape(group.label)}</strong><ul>{causes}</ul></li>"


def render_layer_diagram(block: LayerDiagramBlock) -> str:
    layers = "".join(_render_layer(layer) for layer in block.layers)
    order = (
        f'<figcaption><span aria-hidden="true">↓</span>{escape(block.order_label)}</figcaption>'
        if block.order_label
        else ""
    )
    return f"""
      <figure class="cs-card cs-layers">
        <ol>{layers}</ol>{order}
      </figure>"""


def _render_layer(layer: DiagramLayer) -> str:
    detail = f"<small>{escape(layer.detail)}</small>" if layer.detail else ""
    property_text = f"<em>{escape(layer.property)}</em>" if layer.property else ""
    return (
        f"<li><span><strong>{escape(layer.label)}</strong>{detail}</span>"
        f"{property_text}</li>"
    )


def render_network_diagram(block: NetworkDiagramBlock) -> str:
    positions = _network_positions(block.layers)
    edges = "".join(_render_network_edge(edge, positions) for edge in block.edges)
    nodes = "".join(
        _render_network_node(node, positions[node.id])
        for layer in block.layers
        for node in layer.nodes
    )
    layer_labels = "".join(
        f'<text class="cs-network__layer-label" x="{positions[layer.nodes[0].id][0]:.1f}" y="30">'
        f"{escape(layer.label)}</text>"
        for layer in block.layers
    )
    return f"""
      <figure class="cs-card cs-network">
        <svg viewBox="0 0 1000 420" role="img" aria-label="{escape(block.description)}">
          <defs>
            <marker id="cs-network-arrow" viewBox="0 0 10 10" refX="9" refY="5"
              markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z"></path>
            </marker>
          </defs>
          <g class="cs-network__edges">{edges}</g>
          <g class="cs-network__labels">{layer_labels}</g>
          <g class="cs-network__nodes">{nodes}</g>
        </svg>
      </figure>"""


def _network_positions(
    layers: list[NetworkLayer],
) -> dict[str, tuple[float, float, float]]:
    layer_count = len(layers)
    node_width = 180 if layer_count < 4 else 150
    positions: dict[str, tuple[float, float, float]] = {}
    for layer_index, layer in enumerate(layers):
        x = 120 + (760 * layer_index / (layer_count - 1))
        node_count = len(layer.nodes)
        for node_index, node in enumerate(layer.nodes):
            y = 220 if node_count == 1 else 100 + (240 * node_index / (node_count - 1))
            positions[node.id] = (x, y, node_width)
    return positions


def _render_network_edge(
    edge: NetworkEdge, positions: dict[str, tuple[float, float, float]]
) -> str:
    from_x, from_y, from_width = positions[edge.from_id]
    to_x, to_y, to_width = positions[edge.to_id]
    start_x = from_x + from_width / 2
    end_x = to_x - to_width / 2 - 6
    midpoint = (start_x + end_x) / 2
    return (
        f'<path d="M {start_x:.1f} {from_y:.1f} C {midpoint:.1f} {from_y:.1f}, '
        f'{midpoint:.1f} {to_y:.1f}, {end_x:.1f} {to_y:.1f}" '
        'marker-end="url(#cs-network-arrow)"></path>'
    )


def _render_network_node(
    node: NetworkNode, position: tuple[float, float, float]
) -> str:
    x, y, width = position
    detail = (
        f'<text class="cs-network__detail" x="{x:.1f}" y="{y + 17:.1f}">{escape(node.detail)}</text>'
        if node.detail
        else ""
    )
    return f"""
      <g class="cs-network__node">
        <rect x="{x - width / 2:.1f}" y="{y - 34:.1f}" width="{width:.1f}" height="68" rx="14"></rect>
        <text class="cs-network__label" x="{x:.1f}" y="{y - (7 if node.detail else -5):.1f}">{escape(node.label)}</text>
        {detail}
      </g>"""


def render_quadrant_diagram(block: QuadrantDiagramBlock) -> str:
    regions = "".join(
        _render_quadrant_region(region, class_name)
        for region, class_name in (
            (block.top_left, "top-left"),
            (block.top_right, "top-right"),
            (block.bottom_left, "bottom-left"),
            (block.bottom_right, "bottom-right"),
        )
    )
    return f"""
      <figure class="cs-card cs-quadrant">
        <div class="cs-quadrant__plot">{regions}</div>
        <span class="cs-quadrant__x-low">{escape(block.x_low_label)}</span>
        <span class="cs-quadrant__x-high">{escape(block.x_high_label)}</span>
        <span class="cs-quadrant__y-low">{escape(block.y_low_label)}</span>
        <span class="cs-quadrant__y-high">{escape(block.y_high_label)}</span>
      </figure>"""


def _render_quadrant_region(region: QuadrantRegion, class_name: str) -> str:
    items = "".join(f"<li>{escape(item)}</li>" for item in region.items)
    return (
        f'<div class="cs-quadrant__region cs-quadrant__region--{class_name}">'
        f"<h3>{escape(region.label)}</h3><ul>{items}</ul></div>"
    )


def render_spectrum_diagram(block: SpectrumDiagramBlock) -> str:
    bands = "".join(_render_spectrum_band(band) for band in block.bands)
    trend = f"<strong>{escape(block.trend_label)}</strong>" if block.trend_label else ""
    return f"""
      <figure class="cs-card cs-spectrum">
        <ol>{bands}</ol>
        <div class="cs-spectrum__axis">
          <span>{escape(block.low_label)}</span>{trend}<span>{escape(block.high_label)}</span>
        </div>
      </figure>"""


def _render_spectrum_band(band: SpectrumBand) -> str:
    detail = f"<small>{escape(band.detail)}</small>" if band.detail else ""
    return f"<li><strong>{escape(band.label)}</strong>{detail}</li>"


def render_concentric_diagram(block: ConcentricDiagramBlock) -> str:
    nested = ""
    last_index = len(block.rings) - 1
    for index in range(last_index, -1, -1):
        ring = block.rings[index]
        detail = f"<small>{escape(ring.detail)}</small>" if ring.detail else ""
        inner_class = " cs-concentric__ring--inner" if index == last_index else ""
        nested = (
            f'<div class="cs-concentric__ring cs-concentric__ring--{index + 1}{inner_class}">'
            f"<span><strong>{escape(ring.label)}</strong>{detail}</span>{nested}</div>"
        )
    direction = (
        f'<figcaption><span aria-hidden="true">→</span>{escape(block.direction_label)}</figcaption>'
        if block.direction_label
        else ""
    )
    return (
        f'<figure class="cs-card cs-concentric"><div>{nested}</div>{direction}</figure>'
    )


def render_matrix_diagram(block: MatrixDiagramBlock) -> str:
    column_headers = "".join(
        f'<th scope="col">{escape(header)}</th>' for header in block.column_headers
    )
    rows = "".join(
        _render_matrix_row(header, cells)
        for header, cells in zip(block.row_headers, block.cells, strict=True)
    )
    row_axis = (
        f'<span class="cs-matrix__row-axis">{escape(block.row_axis_label)}</span>'
        if block.row_axis_label
        else ""
    )
    column_axis = (
        f'<span class="cs-matrix__column-axis">{escape(block.column_axis_label)}</span>'
        if block.column_axis_label
        else ""
    )
    return f"""
      <figure class="cs-card cs-matrix">
        {column_axis}{row_axis}
        <table>
          <thead><tr><td></td>{column_headers}</tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </figure>"""


def _render_matrix_row(header: str, cells: list[str]) -> str:
    values = "".join(f"<td>{escape(cell)}</td>" for cell in cells)
    return f'<tr><th scope="row">{escape(header)}</th>{values}</tr>'


DIAGRAM_BLOCKS = (
    BlockDefinition(
        ComparisonBlock,
        BlockGuide(
            "comparison",
            "structural",
            "two-sided contrast",
            "two matched columns with headings",
            "two concepts need direct similarities or differences",
            '{"type":"comparison","left_title":"Plant cell","left_items":["Cell wall"],"right_title":"Animal cell","right_items":["No cell wall"]}',
        ),
        render_comparison,
    ),
    BlockDefinition(
        ProcessBlock,
        BlockGuide(
            "process",
            "structural",
            "an ordered system or linear process",
            "a horizontal numbered sequence",
            "showing stages that move from a start to an end",
            '{"type":"process","steps":["Evaporation","Condensation","Precipitation"]}',
        ),
        render_process,
    ),
    BlockDefinition(
        LabeledDiagramBlock,
        BlockGuide(
            "labeled-diagram",
            "visual",
            "parts or attributes connected to one central concept",
            "a hub-and-spoke concept diagram with surrounding labels",
            "showing conceptual parts, not precise anatomical positions",
            '{"type":"labeled-diagram","subject":"Cell","labels":["Membrane","Nucleus","Cytoplasm"]}',
        ),
        render_labeled_diagram,
    ),
    BlockDefinition(
        CycleBlock,
        BlockGuide(
            "cycle",
            "visual",
            "a repeating sequence with no final endpoint",
            "a connected loop of three to six stages",
            "the final stage returns to the first",
            '{"type":"cycle","steps":["Evaporation","Condensation","Precipitation","Collection"]}',
        ),
        render_cycle,
    ),
    BlockDefinition(
        PyramidDiagramBlock,
        BlockGuide(
            "pyramid-diagram",
            "visual",
            "ranked or layered quantities that widen toward a foundation",
            "three to five colored trapezoid levels with labels, details, values, and an optional upward trend",
            "teaching energy or food pyramids, needs hierarchies, population structures, or layered priorities; list levels from top to bottom",
            '{"type":"pyramid-diagram","levels":[{"label":"Tertiary consumers","detail":"Apex predators","value":"10 kcal"},{"label":"Primary consumers","detail":"Herbivores","value":"1,000 kcal"},{"label":"Producers","detail":"Plants","value":"10,000 kcal"}],"trend_label":"Available energy decreases upward"}',
        ),
        render_pyramid_diagram,
    ),
    BlockDefinition(
        HierarchyTreeBlock,
        BlockGuide(
            "hierarchy-tree",
            "visual",
            "one root concept branching into grouped categories and examples",
            "a connected top-down tree with a root, two to four branches, and compact child nodes",
            "showing classification, organizational hierarchy, taxonomy, or part families",
            '{"type":"hierarchy-tree","root":{"label":"Matter"},"branches":[{"label":"Pure substances","children":[{"label":"Elements"},{"label":"Compounds"}]},{"label":"Mixtures","children":[{"label":"Homogeneous"},{"label":"Heterogeneous"}]}]}',
        ),
        render_hierarchy_tree,
    ),
    BlockDefinition(
        FlowDiagramBlock,
        BlockGuide(
            "flow-diagram",
            "visual",
            "causal or transformational flow with optional branching inside stages",
            "two to four connected stage columns containing up to eight labeled nodes",
            "showing inputs, transformations, outputs, branching pathways, or cause and effect",
            '{"type":"flow-diagram","stages":[{"label":"Input","nodes":[{"label":"Sunlight"},{"label":"Water"}]},{"label":"Process","nodes":[{"label":"Photosynthesis","detail":"In chloroplasts"}]},{"label":"Output","nodes":[{"label":"Glucose"},{"label":"Oxygen"}]}]}',
        ),
        render_flow_diagram,
    ),
    BlockDefinition(
        VennDiagramBlock,
        BlockGuide(
            "venn-diagram",
            "visual",
            "exclusive and shared properties of two sets",
            "two overlapping circles with left-only, shared, and right-only content regions",
            "comparing two categories where their intersection is instructional",
            '{"type":"venn-diagram","left_title":"Plant cells","left_items":["Cell wall"],"right_title":"Animal cells","right_items":["Centrioles"],"overlap_title":"Both","overlap_items":["Nucleus","Cell membrane"]}',
        ),
        render_venn_diagram,
    ),
    BlockDefinition(
        CauseEffectDiagramBlock,
        BlockGuide(
            "cause-effect-diagram",
            "visual",
            "multiple grouped causes converging on one outcome",
            "two to four cause groups feeding a prominent effect card",
            "explaining why one event or problem occurs, especially when causes belong to categories",
            '{"type":"cause-effect-diagram","effect_label":"Effect","effect":"Algal bloom","effect_detail":"Rapid algae growth","groups":[{"label":"Nutrients","causes":["Fertilizer runoff","Sewage"]},{"label":"Conditions","causes":["Warm water","Strong sunlight"]}]}',
        ),
        render_cause_effect_diagram,
    ),
    BlockDefinition(
        LayerDiagramBlock,
        BlockGuide(
            "layer-diagram",
            "visual",
            "ordered physical or conceptual strata",
            "three to six stacked colored bands with labels, details, properties, and an optional order arrow",
            "showing Earth, atmosphere, tissue, habitat, or system layers where adjacency and order matter; list layers from top to bottom",
            '{"type":"layer-diagram","layers":[{"label":"Crust","detail":"Thin solid surface","property":"5–70 km"},{"label":"Mantle","detail":"Slow-flowing rock","property":"2,900 km"},{"label":"Core","detail":"Iron and nickel","property":"Hottest"}],"order_label":"Surface to center"}',
        ),
        render_layer_diagram,
    ),
    BlockDefinition(
        NetworkDiagramBlock,
        BlockGuide(
            "network-diagram",
            "visual",
            "many-to-many directed relationships across semantic layers",
            "a compiler-positioned SVG network of three to ten nodes and validated forward edges",
            "showing food webs, dependency networks, information transfer, or connected systems that are not a single linear flow; order layers from source to destination",
            '{"type":"network-diagram","description":"Energy links in a grassland food web","layers":[{"label":"Producers","nodes":[{"id":"grass","label":"Grass"},{"id":"seeds","label":"Seeds"}]},{"label":"Consumers","nodes":[{"id":"rabbit","label":"Rabbit"},{"id":"mouse","label":"Mouse"}]},{"label":"Predators","nodes":[{"id":"hawk","label":"Hawk"}]}],"edges":[{"from_id":"grass","to_id":"rabbit"},{"from_id":"seeds","to_id":"mouse"},{"from_id":"rabbit","to_id":"hawk"},{"from_id":"mouse","to_id":"hawk"}]}',
        ),
        render_network_diagram,
    ),
    BlockDefinition(
        QuadrantDiagramBlock,
        BlockGuide(
            "quadrant-diagram",
            "visual",
            "qualitative classification along two independent dimensions",
            "a labeled two-axis matrix with four named regions and item chips",
            "sorting examples by low-to-high conceptual properties rather than numeric coordinates",
            '{"type":"quadrant-diagram","x_low_label":"Low conductivity","x_high_label":"High conductivity","y_low_label":"Weak magnetism","y_high_label":"Strong magnetism","top_left":{"label":"Magnetic insulators","items":["Ferrite"]},"top_right":{"label":"Magnetic conductors","items":["Iron"]},"bottom_left":{"label":"Insulators","items":["Rubber"]},"bottom_right":{"label":"Conductors","items":["Copper"]}}',
        ),
        render_quadrant_diagram,
    ),
    BlockDefinition(
        SpectrumDiagramBlock,
        BlockGuide(
            "spectrum-diagram",
            "visual",
            "ordered categories along a continuous increasing or decreasing property",
            "three to seven adjacent color bands above a directional endpoint axis",
            "teaching electromagnetic bands, acidity ranges, temperature zones, or other ordered continua; list bands from low to high",
            '{"type":"spectrum-diagram","bands":[{"label":"Radio","detail":"Longest wavelength"},{"label":"Microwave"},{"label":"Infrared"},{"label":"Visible"},{"label":"Ultraviolet"},{"label":"X-ray"},{"label":"Gamma","detail":"Shortest wavelength"}],"low_label":"Low frequency","high_label":"High frequency","trend_label":"Frequency increases"}',
        ),
        render_spectrum_diagram,
    ),
    BlockDefinition(
        ConcentricDiagramBlock,
        BlockGuide(
            "concentric-diagram",
            "visual",
            "nested containment or movement from an outer context to an inner core",
            "two to five nested labeled regions with an optional directional caption",
            "showing scales, boundaries, ecological organization, or containment where being inside another level is the key idea; list rings from outermost to innermost",
            '{"type":"concentric-diagram","rings":[{"label":"Organism","detail":"One living individual"},{"label":"Organ system"},{"label":"Organ"},{"label":"Tissue"},{"label":"Cell","detail":"Smallest living unit"}],"direction_label":"Outer organization to inner structure"}',
        ),
        render_concentric_diagram,
    ),
    BlockDefinition(
        MatrixDiagramBlock,
        BlockGuide(
            "matrix-diagram",
            "visual",
            "outcomes or properties at the intersections of two categorical dimensions",
            "a validated two-by-two to four-by-four grid with row and column headers",
            "showing Punnett squares, classification grids, state/property lookup, or other categorical intersections; use quadrant-diagram instead when both axes are qualitative continua",
            '{"type":"matrix-diagram","row_axis_label":"Parent 1","column_axis_label":"Parent 2","row_headers":["B","b"],"column_headers":["B","b"],"cells":[["BB","Bb"],["Bb","bb"]]}',
        ),
        render_matrix_diagram,
    ),
)
