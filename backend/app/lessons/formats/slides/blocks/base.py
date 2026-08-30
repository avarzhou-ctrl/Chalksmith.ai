from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from backend.app.lessons.formats.contracts import StrictSpecModel


BlockCategory = Literal["text", "symbolic", "structural", "visual"]


@dataclass(frozen=True)
class BlockGuide:
    type: str
    category: BlockCategory
    purpose: str
    renders_as: str
    use_when: str
    example: str


@dataclass(frozen=True)
class BlockDefinition:
    model: type[StrictSpecModel]
    guide: BlockGuide
    renderer: Callable[[Any], str]

    def render(self, block: StrictSpecModel) -> str:
        if not isinstance(block, self.model):
            raise TypeError(
                f"Block {self.guide.type} requires {self.model.__name__}, "
                f"not {type(block).__name__}"
            )
        return self.renderer(block)
