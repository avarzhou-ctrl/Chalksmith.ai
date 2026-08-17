from html import escape
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition, BlockGuide


CellFeatureKind = Literal[
    "cell-wall",
    "cell-membrane",
    "cytoplasm",
    "nucleus",
    "dna",
    "mitochondria",
    "chloroplast",
    "vacuole",
    "ribosomes",
]


class CellFeature(StrictSpecModel):
    feature: CellFeatureKind
    label: str = Field(min_length=1, max_length=24)
    function: str | None = Field(default=None, min_length=1, max_length=48)


class CellDiagramBlock(StrictSpecModel):
    type: Literal["cell-diagram"]
    cell_type: Literal["plant", "animal", "bacterial"]
    cell_label: str = Field(min_length=1, max_length=28)
    features: list[CellFeature] = Field(min_length=3, max_length=7)

    @model_validator(mode="after")
    def validate_features(self) -> "CellDiagramBlock":
        feature_types = [feature.feature for feature in self.features]
        if len(feature_types) != len(set(feature_types)):
            raise ValueError("cell features must be unique")
        disallowed = {
            "plant": {"dna"},
            "animal": {"cell-wall", "chloroplast", "dna"},
            "bacterial": {"nucleus", "mitochondria", "chloroplast", "vacuole"},
        }
        incompatible = set(feature_types) & disallowed[self.cell_type]
        if incompatible:
            raise ValueError(
                f"{self.cell_type} cell does not support: {', '.join(sorted(incompatible))}"
            )
        return self


def render_cell_diagram(block: CellDiagramBlock) -> str:
    feature_types = {feature.feature for feature in block.features}
    organelles = "".join(
        _render_organelle(feature)
        for feature in (
            "nucleus",
            "dna",
            "mitochondria",
            "chloroplast",
            "vacuole",
            "ribosomes",
        )
        if feature in feature_types
    )
    legends = "".join(_render_cell_feature(feature) for feature in block.features)
    return f"""
      <figure class="cs-card cs-cell-diagram cs-cell-diagram--{block.cell_type}">
        <div class="cs-cell-diagram__model" role="img" aria-label="{escape(block.cell_label)}">
          <div class="cs-cell-diagram__interior">{organelles}</div>
          <strong>{escape(block.cell_label)}</strong>
        </div>
        <figcaption><ul>{legends}</ul></figcaption>
      </figure>"""


def _render_organelle(feature: str) -> str:
    copies = 4 if feature in {"mitochondria", "chloroplast", "ribosomes"} else 1
    return "".join(
        f'<i class="cs-cell-diagram__organelle cs-cell-diagram__organelle--{feature} cs-cell-diagram__organelle--copy-{index + 1}"></i>'
        for index in range(copies)
    )


def _render_cell_feature(feature: CellFeature) -> str:
    detail = f"<small>{escape(feature.function)}</small>" if feature.function else ""
    return (
        f'<li data-feature="{feature.feature}"><strong>{escape(feature.label)}</strong>'
        f"{detail}</li>"
    )


BIOLOGY_BLOCKS = (
    BlockDefinition(
        CellDiagramBlock,
        BlockGuide(
            "cell-diagram",
            "visual",
            "type-aware plant, animal, or bacterial cell structure",
            "a platform-drawn cell silhouette with semantic organelles and a keyed function legend",
            "teaching cell structures where plant, animal, and bacterial compatibility matters; use labeled-diagram for a generic concept and use this as the only body block",
            '{"type":"cell-diagram","cell_type":"plant","cell_label":"Plant cell","features":[{"feature":"cell-wall","label":"Cell wall","function":"Rigid support"},{"feature":"cell-membrane","label":"Cell membrane","function":"Controls entry and exit"},{"feature":"nucleus","label":"Nucleus","function":"Stores genetic information"},{"feature":"chloroplast","label":"Chloroplast","function":"Captures light energy"},{"feature":"vacuole","label":"Central vacuole","function":"Stores water"}]}',
            standalone=True,
        ),
        render_cell_diagram,
    ),
)
