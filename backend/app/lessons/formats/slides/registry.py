from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition
from backend.app.lessons.formats.slides.blocks.content import CONTENT_BLOCKS
from backend.app.lessons.formats.slides.blocks.data import DATA_BLOCKS
from backend.app.lessons.formats.slides.blocks.diagrams import DIAGRAM_BLOCKS
from backend.app.lessons.formats.slides.blocks.math import MATH_BLOCKS


BLOCK_DEFINITIONS: tuple[BlockDefinition, ...] = (
    *CONTENT_BLOCKS,
    *MATH_BLOCKS,
    *DATA_BLOCKS,
    *DIAGRAM_BLOCKS,
)
BLOCK_REGISTRY = {definition.guide.type: definition for definition in BLOCK_DEFINITIONS}

if len(BLOCK_REGISTRY) != len(BLOCK_DEFINITIONS):
    raise RuntimeError("Slides block types must be unique")

BLOCK_CATALOG = tuple(definition.guide for definition in BLOCK_DEFINITIONS)
BLOCK_TYPES = frozenset(BLOCK_REGISTRY)
VISUAL_BLOCK_TYPES = frozenset(
    guide.type for guide in BLOCK_CATALOG if guide.category == "visual"
)
STANDALONE_BLOCK_TYPES = frozenset(
    guide.type for guide in BLOCK_CATALOG if guide.standalone
)


def block_catalog_prompt() -> str:
    return "\n".join(
        f"- {guide.type} [{guide.category}]: {guide.purpose}. Renders as {guide.renders_as}. "
        f"Use when {guide.use_when}. Example: {guide.example}"
        for guide in BLOCK_CATALOG
    )


def render_block(block: StrictSpecModel) -> str:
    block_type = getattr(block, "type", None)
    definition = BLOCK_REGISTRY.get(block_type)
    if definition is None:
        raise TypeError(f"Unsupported slide block: {type(block).__name__}")
    return definition.render(block)
