from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition
from backend.app.lessons.formats.slides.blocks.biology import BIOLOGY_BLOCKS
from backend.app.lessons.formats.slides.blocks.chemistry import CHEMISTRY_BLOCKS
from backend.app.lessons.formats.slides.blocks.content import CONTENT_BLOCKS
from backend.app.lessons.formats.slides.blocks.data import DATA_BLOCKS
from backend.app.lessons.formats.slides.blocks.diagrams import DIAGRAM_BLOCKS
from backend.app.lessons.formats.slides.blocks.math import MATH_BLOCKS
from backend.app.lessons.formats.slides.blocks.physics import PHYSICS_BLOCKS


BLOCK_GROUPS: tuple[tuple[str, tuple[BlockDefinition, ...]], ...] = (
    ("content", CONTENT_BLOCKS),
    ("math", MATH_BLOCKS),
    ("data", DATA_BLOCKS),
    ("diagrams", DIAGRAM_BLOCKS),
    ("physics", PHYSICS_BLOCKS),
    ("chemistry", CHEMISTRY_BLOCKS),
    ("biology", BIOLOGY_BLOCKS),
)
BLOCK_STYLE_GROUP_ORDER = (
    "content",
    "data",
    "diagrams",
    "math",
    "physics",
    "chemistry",
    "biology",
)
BLOCK_DEFINITIONS = tuple(
    definition for _, definitions in BLOCK_GROUPS for definition in definitions
)
BLOCK_REGISTRY = {definition.guide.type: definition for definition in BLOCK_DEFINITIONS}
BLOCK_STYLE_GROUPS = {
    definition.guide.type: group
    for group, definitions in BLOCK_GROUPS
    for definition in definitions
}

if len(BLOCK_REGISTRY) != len(BLOCK_DEFINITIONS):
    raise RuntimeError("Slides block types must be unique")
if {group for group, _ in BLOCK_GROUPS} != set(BLOCK_STYLE_GROUP_ORDER):
    raise RuntimeError("Slides block groups and style-group order must match")

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


def style_group_for(block: StrictSpecModel) -> str:
    block_type = getattr(block, "type", None)
    group = BLOCK_STYLE_GROUPS.get(block_type)
    if group is None:
        raise TypeError(f"Unsupported slide block: {type(block).__name__}")
    return group
