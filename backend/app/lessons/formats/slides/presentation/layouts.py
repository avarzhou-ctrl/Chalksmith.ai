from dataclasses import dataclass
from typing import Literal, cast, get_args


LayoutName = Literal[
    "auto",
    "single",
    "row-2",
    "row-3",
    "column-2",
    "grid-2-by-2",
    "grid-3-by-2",
    "top-1-bottom-2",
    "top-1-bottom-3",
    "top-2-bottom-1",
    "top-3-bottom-1",
    "left-wide",
    "right-wide",
    "left-1-right-2",
    "left-2-right-1",
]


@dataclass(frozen=True)
class LayoutDefinition:
    slots: frozenset[int]
    structure: str
    use_when: str


LAYOUTS: dict[str, LayoutDefinition] = {
    "single": LayoutDefinition(frozenset({1}), "one full-width slot", "one dense or focal block"),
    "row-2": LayoutDefinition(frozenset({2}), "one row with two equal columns", "two parallel blocks"),
    "row-3": LayoutDefinition(frozenset({3}), "one row with three equal columns", "three short parallel blocks"),
    "column-2": LayoutDefinition(frozenset({2}), "two full-width rows", "two blocks that both need width"),
    "grid-2-by-2": LayoutDefinition(frozenset({4}), "two columns by two rows", "four short parallel blocks"),
    "grid-3-by-2": LayoutDefinition(frozenset({5, 6}), "three columns by two rows", "five or six very short blocks"),
    "top-1-bottom-2": LayoutDefinition(frozenset({3}), "one full-width slot above two columns", "one overview above two branches"),
    "top-1-bottom-3": LayoutDefinition(frozenset({4}), "one full-width slot above three columns", "one overview above three examples"),
    "top-2-bottom-1": LayoutDefinition(frozenset({3}), "two columns above one full-width slot", "two premises above one conclusion"),
    "top-3-bottom-1": LayoutDefinition(frozenset({4}), "three columns above one full-width slot", "three inputs above one summary"),
    "left-wide": LayoutDefinition(frozenset({2}), "a wide left slot and narrow right slot", "the left block needs more room"),
    "right-wide": LayoutDefinition(frozenset({2}), "a narrow left slot and wide right slot", "the right block needs more room"),
    "left-1-right-2": LayoutDefinition(frozenset({3}), "one tall left slot beside two stacked right slots", "one focal idea with two details"),
    "left-2-right-1": LayoutDefinition(frozenset({3}), "two stacked left slots beside one tall right slot", "two supporting ideas beside one focal result"),
}

if set(LAYOUTS) != set(get_args(LayoutName)) - {"auto"}:
    raise RuntimeError("Slides layout names and definitions must match")


def default_layout(block_count: int) -> LayoutName:
    return cast(LayoutName, {
        1: "single",
        2: "row-2",
        3: "row-3",
        4: "grid-2-by-2",
        5: "grid-3-by-2",
        6: "grid-3-by-2",
    }[block_count])


def normalize_layout(layout: LayoutName, block_count: int) -> LayoutName:
    definition = LAYOUTS.get(layout)
    if definition is None or block_count not in definition.slots:
        return default_layout(block_count)
    return layout


def layout_catalog_prompt() -> str:
    return "\n".join(
        f"- {name}: {definition.structure}; use for {definition.use_when}; "
        f"block_count={_format_counts(definition.slots)}."
        for name, definition in LAYOUTS.items()
    )


def _format_counts(counts: frozenset[int]) -> str:
    return "/".join(str(count) for count in sorted(counts))
