from html import escape
import re
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition, BlockGuide


class ParticleSpecies(StrictSpecModel):
    formula: str = Field(min_length=1, max_length=12)
    atoms: list[str] = Field(min_length=1, max_length=4)
    count: int = Field(ge=1, le=6)

    @model_validator(mode="after")
    def validate_atoms(self) -> "ParticleSpecies":
        if any(re.fullmatch(r"[A-Z][a-z]?", atom) is None for atom in self.atoms):
            raise ValueError("particle atoms must use element-symbol notation")
        return self


class ParticleSample(StrictSpecModel):
    label: str = Field(min_length=1, max_length=24)
    species: list[ParticleSpecies] = Field(min_length=1, max_length=3)


class ParticleDiagramBlock(StrictSpecModel):
    type: Literal["particle-diagram"]
    samples: list[ParticleSample] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_capacity(self) -> "ParticleDiagramBlock":
        formula_atoms: dict[str, tuple[str, ...]] = {}
        elements: set[str] = set()
        for sample in self.samples:
            if sum(species.count for species in sample.species) > 9:
                raise ValueError("particle samples support at most nine particles")
            formulas = [
                species.formula.strip().casefold() for species in sample.species
            ]
            if len(formulas) != len(set(formulas)):
                raise ValueError(
                    "particle species formulas must be unique within a sample"
                )
            for species in sample.species:
                elements.update(species.atoms)
                atoms = tuple(species.atoms)
                prior_atoms = formula_atoms.setdefault(species.formula, atoms)
                if prior_atoms != atoms:
                    raise ValueError(
                        "a particle formula must keep the same atom composition"
                    )
        if len(elements) > 6:
            raise ValueError("particle diagrams support at most six element types")
        return self


class ReactionTerm(StrictSpecModel):
    coefficient: int = Field(default=1, ge=1, le=9)
    formula: str = Field(min_length=1, max_length=16)
    name: str | None = Field(default=None, min_length=1, max_length=28)


class ReactionDiagramBlock(StrictSpecModel):
    type: Literal["reaction-diagram"]
    reactants: list[ReactionTerm] = Field(min_length=1, max_length=3)
    products: list[ReactionTerm] = Field(min_length=1, max_length=3)
    condition: str | None = Field(default=None, min_length=1, max_length=32)
    caption: str | None = Field(default=None, min_length=1, max_length=72)


def render_particle_diagram(block: ParticleDiagramBlock) -> str:
    elements = dict.fromkeys(
        atom
        for sample in block.samples
        for species in sample.species
        for atom in species.atoms
    )
    element_colors = {element: index for index, element in enumerate(elements, start=1)}
    samples = "".join(
        _render_particle_sample(sample, element_colors) for sample in block.samples
    )
    return f'<figure class="cs-card cs-particle-diagram"><ol>{samples}</ol></figure>'


def _render_particle_sample(
    sample: ParticleSample, element_colors: dict[str, int]
) -> str:
    particles = "".join(
        _render_particle(species, species_index, copy_index, element_colors)
        for species_index, species in enumerate(sample.species, start=1)
        for copy_index in range(species.count)
    )
    return (
        f"<li><h3>{escape(sample.label)}</h3>"
        f'<div class="cs-particle-diagram__chamber">{particles}</div></li>'
    )


def _render_particle(
    species: ParticleSpecies,
    species_index: int,
    copy_index: int,
    element_colors: dict[str, int],
) -> str:
    atoms = "".join(
        f'<i class="cs-particle-diagram__atom cs-particle-diagram__atom--color-{element_colors[atom]}">{escape(atom)}</i>'
        for atom in species.atoms
    )
    return (
        f'<span class="cs-particle-diagram__particle cs-particle-diagram__particle--{species_index}" '
        f'data-copy="{copy_index + 1}" aria-label="{escape(species.formula)}">{atoms}</span>'
    )


def render_reaction_diagram(block: ReactionDiagramBlock) -> str:
    reactants = _render_reaction_side(block.reactants)
    products = _render_reaction_side(block.products)
    condition = f"<small>{escape(block.condition)}</small>" if block.condition else ""
    caption = (
        f"<figcaption>{escape(block.caption)}</figcaption>" if block.caption else ""
    )
    return f"""
      <figure class="cs-card cs-reaction-diagram">
        <div>{reactants}</div>
        <span class="cs-reaction-diagram__arrow" aria-hidden="true">→{condition}</span>
        <div>{products}</div>
        {caption}
      </figure>"""


def _render_reaction_side(terms: list[ReactionTerm]) -> str:
    return "".join(
        ("<b>+</b>" if index else "") + _render_reaction_term(term)
        for index, term in enumerate(terms)
    )


def _render_reaction_term(term: ReactionTerm) -> str:
    name = f"<small>{escape(term.name)}</small>" if term.name else ""
    return (
        '<span class="cs-reaction-diagram__term">'
        f"<strong>{term.coefficient if term.coefficient > 1 else ''}{escape(term.formula)}</strong>{name}</span>"
    )


CHEMISTRY_BLOCKS = (
    BlockDefinition(
        ParticleDiagramBlock,
        BlockGuide(
            "particle-diagram",
            "visual",
            "particle-level composition of pure substances, compounds, and mixtures",
            "one to three labeled chambers containing repeated atom or molecule models",
            "comparing matter at particle scale; atom symbols and species counts must reflect the intended substance",
            '{"type":"particle-diagram","samples":[{"label":"Element","species":[{"formula":"O₂","atoms":["O","O"],"count":4}]},{"label":"Compound","species":[{"formula":"H₂O","atoms":["H","O","H"],"count":4}]},{"label":"Mixture","species":[{"formula":"N₂","atoms":["N","N"],"count":3},{"formula":"O₂","atoms":["O","O"],"count":2}]}]}',
        ),
        render_particle_diagram,
    ),
    BlockDefinition(
        ReactionDiagramBlock,
        BlockGuide(
            "reaction-diagram",
            "symbolic",
            "reactants transforming into products under an optional condition",
            "balanced formula cards on two sides of a prominent reaction arrow",
            "the reaction structure and coefficients matter more than a calculation",
            '{"type":"reaction-diagram","reactants":[{"coefficient":2,"formula":"H₂","name":"Hydrogen"},{"formula":"O₂","name":"Oxygen"}],"products":[{"coefficient":2,"formula":"H₂O","name":"Water"}],"condition":"spark","caption":"Atoms are rearranged, not created or destroyed."}',
        ),
        render_reaction_diagram,
    ),
)
