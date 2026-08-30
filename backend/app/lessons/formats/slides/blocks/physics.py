from html import escape
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition, BlockGuide


class ForceArrow(StrictSpecModel):
    direction: Literal["up", "right", "down", "left"]
    label: str = Field(min_length=1, max_length=28)
    magnitude: str | None = Field(default=None, min_length=1, max_length=18)


class ForceDiagramBlock(StrictSpecModel):
    type: Literal["force-diagram"]
    object_label: str = Field(min_length=1, max_length=28)
    description: str = Field(min_length=1, max_length=100)
    forces: list[ForceArrow] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def validate_forces(self) -> "ForceDiagramBlock":
        directions = [force.direction for force in self.forces]
        if len(directions) != len(set(directions)):
            raise ValueError("force-diagram supports one force per direction")
        return self


class WaveDiagramBlock(StrictSpecModel):
    type: Literal["wave-diagram"]
    description: str = Field(min_length=1, max_length=100)
    equilibrium_label: str | None = Field(default=None, min_length=1, max_length=28)
    amplitude_label: str = Field(min_length=1, max_length=28)
    wavelength_label: str = Field(min_length=1, max_length=28)
    crest_label: str | None = Field(default=None, min_length=1, max_length=24)
    trough_label: str | None = Field(default=None, min_length=1, max_length=24)


def render_force_diagram(block: ForceDiagramBlock) -> str:
    forces = "".join(_render_force(force) for force in block.forces)
    return f"""
      <figure class="cs-card cs-force-diagram">
        <svg viewBox="0 0 720 380" role="img" aria-label="{escape(block.description)}">
          <defs>
            <marker id="cs-force-arrow" viewBox="0 0 10 10" refX="9" refY="5"
              markerWidth="8" markerHeight="8" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z"></path>
            </marker>
          </defs>
          <rect class="cs-force-diagram__object" x="285" y="145" width="150" height="90" rx="16"></rect>
          <text class="cs-force-diagram__object-label" x="360" y="197">{escape(block.object_label)}</text>
          {forces}
        </svg>
      </figure>"""


def _render_force(force: ForceArrow) -> str:
    coordinates = {
        "up": (360, 145, 360, 45, 485, 78, "middle"),
        "right": (435, 190, 590, 190, 520, 150, "middle"),
        "down": (360, 235, 360, 335, 485, 320, "middle"),
        "left": (285, 190, 130, 190, 200, 150, "middle"),
    }
    x1, y1, x2, y2, text_x, text_y, anchor = coordinates[force.direction]
    text = force.label
    if force.magnitude:
        text = f"{text} · {force.magnitude}"
    return (
        f'<g class="cs-force-diagram__force cs-force-diagram__force--{force.direction}">'
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"></line>'
        f'<text x="{text_x}" y="{text_y}" text-anchor="{anchor}">{escape(text)}</text></g>'
    )


def render_wave_diagram(block: WaveDiagramBlock) -> str:
    equilibrium = escape(block.equilibrium_label or "Equilibrium")
    crest = (
        f'<text class="cs-wave-diagram__feature" x="88" y="82">{escape(block.crest_label)}</text>'
        if block.crest_label
        else ""
    )
    trough = (
        f'<text class="cs-wave-diagram__feature" x="302" y="326">{escape(block.trough_label)}</text>'
        if block.trough_label
        else ""
    )
    return f"""
      <figure class="cs-card cs-wave-diagram">
        <svg viewBox="0 0 720 360" role="img" aria-label="{escape(block.description)}">
          <line class="cs-wave-diagram__equilibrium" x1="45" y1="180" x2="680" y2="180"></line>
          <text class="cs-wave-diagram__equilibrium-label" x="50" y="170">{equilibrium}</text>
          <path class="cs-wave-diagram__wave" d="M45 180 C100 35 160 35 215 180 S330 325 390 180 S505 35 565 180 S625 325 680 180"></path>
          <line class="cs-wave-diagram__measure" x1="130" y1="180" x2="130" y2="68"></line>
          <text class="cs-wave-diagram__measure-label" x="150" y="125">{escape(block.amplitude_label)}</text>
          <line class="cs-wave-diagram__measure" x1="130" y1="48" x2="477" y2="48"></line>
          <text class="cs-wave-diagram__measure-label" x="304" y="36" text-anchor="middle">{escape(block.wavelength_label)}</text>
          {crest}{trough}
        </svg>
      </figure>"""


PHYSICS_BLOCKS = (
    BlockDefinition(
        ForceDiagramBlock,
        BlockGuide(
            "force-diagram",
            "visual",
            "forces acting on one object with scientifically meaningful directions",
            "a free-body diagram with a central object and one validated arrow per cardinal direction",
            "teaching balanced or unbalanced forces, weight, normal force, friction, or applied force",
            '{"type":"force-diagram","object_label":"Book","description":"Forces on a book resting on a table","forces":[{"direction":"up","label":"Normal force","magnitude":"10 N"},{"direction":"down","label":"Weight","magnitude":"10 N"}]}',
        ),
        render_force_diagram,
    ),
    BlockDefinition(
        WaveDiagramBlock,
        BlockGuide(
            "wave-diagram",
            "visual",
            "the anatomy of a transverse wave",
            "a deterministic transverse wave with equilibrium, amplitude, wavelength, crest, and trough annotations",
            "teaching wave vocabulary or how amplitude and wavelength are measured",
            '{"type":"wave-diagram","description":"Parts of a transverse wave","equilibrium_label":"Rest position","amplitude_label":"Amplitude","wavelength_label":"One wavelength","crest_label":"Crest","trough_label":"Trough"}',
        ),
        render_wave_diagram,
    ),
)
