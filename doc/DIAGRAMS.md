# Slides Diagram Block Library

> Last reviewed: 2026-08-17

Slides diagrams are organized by the relationship the learner must see, not by a decorative
template name. The LLM selects a semantic Block and supplies bounded teaching data; validation
checks capacity and references; the compiler calculates structure and positions; the versioned
`assets/v1/core.css` and `assets/v1/blocks/*.css` files own every visual style. The compiler embeds
only the style categories used by the lesson. No Block accepts arbitrary HTML, CSS, SVG, or page
coordinates.

“Complete” here means that the library covers the recurring relationship grammars needed for
elementary and middle-school STEM. A specialized scientific illustration can still justify a new
Block, but should not be approximated with generic geometry or free-form drawing code.

## Capability matrix

| Teaching relationship | Block | Rendered form | Best used for |
| :--- | :--- | :--- | :--- |
| Parts around one subject | `labeled-diagram` | Central subject with connected labels | Cell parts, apparatus, anatomy |
| Repeating loop | `cycle` | Ordered nodes with a return arrow | Water, rock, life cycles |
| Chronological change | `timeline` | Events on a horizontal time axis | Discoveries, development stages |
| Ordered procedure | `process` | Numbered linear steps | Algorithms, experiments |
| Staged transformation | `flow-diagram` | Connected stages with branching nodes | Inputs/process/outputs, pathways |
| Two-side contrast | `comparison` | Parallel named columns | Mitosis versus meiosis |
| Exclusive and shared sets | `venn-diagram` | Two overlapping sets with three content regions | Cell types, number sets |
| Many causes to one result | `cause-effect-diagram` | Grouped causes converging on an effect | Erosion, disease, ecosystem change |
| Parent-to-child classification | `hierarchy-tree` | Root, branches, and child nodes | Taxonomy, matter classification |
| Many-to-many directed links | `network-diagram` | Compiler-positioned layered SVG graph | Food webs, dependencies, circuits |
| Top-to-bottom strata | `layer-diagram` | Ordered stacked bands | Earth, atmosphere, tissues |
| Relative levels with width meaning | `pyramid-diagram` | Tapered stacked levels | Energy, biomass, population |
| Two qualitative dimensions | `quadrant-diagram` | Four regions around two labeled axes | Material or organism classification |
| Ordered continuum | `spectrum-diagram` | Adjacent bands and directional axis | EM spectrum, pH zones, temperature |
| Quantitative values | `bar-chart` | Scaled bars on a common baseline | Counts and measurements |
| Position on one numeric axis | `number-line` | Numeric line with markers | Integers, fractions, intervals |
| Position on two numeric axes | `coordinate-plot` | Cartesian grid and points | Coordinates, transformations |
| Proportional whole and parts | `bar-model` / `fraction-model` | Scaled segments or partitioned whole | Ratios, fractions, word problems |
| Geometric shape and construction | `geometry-model` | Deterministic figure with semantic points, sides, internal segments, and theorem markings | Angles, perimeter, area, diagonals, radii, medians, cevians, concurrency |
| Nested containment | `concentric-diagram` | Nested labeled regions from outside to center | Scale, containment, organization |
| Categorical intersections | `matrix-diagram` | Row/column headers with validated cells | Punnett squares, lookup grids |

The distinctions are intentional. `flow-diagram` is a left-to-right stage sequence, while
`network-diagram` supports several nodes connecting to several later nodes. `layer-diagram` shows
adjacent strata of equal semantic status; `pyramid-diagram` adds tapering width to communicate a
quantity or rank. `quadrant-diagram` classifies by two qualitative properties, while
`coordinate-plot` represents numeric coordinates.

## Subject-specific libraries

General relationship grammar remains in `blocks/diagrams.py`. A Block moves into a subject file
when correctness depends on that discipline's notation, compatibility rules, or fixed scientific
geometry:

| Subject file | Current specialized Blocks | Why these are not generic diagrams |
| :--- | :--- | :--- |
| `math.py` | `function-graph` plus equation, fraction, number-line, bar, coordinate, and geometry models | Axes, sampled functions, numeric bounds, and mathematical notation require numeric validation. |
| `physics.py` | `force-diagram`, `wave-diagram` | Arrow direction is a physical vector, and amplitude/wavelength annotations have fixed scientific meaning. |
| `chemistry.py` | `particle-diagram`, `reaction-diagram` | Atom groupings, species counts, coefficients, reactants, and products require chemistry semantics. |
| `biology.py` | `cell-diagram` | Plant, animal, and bacterial cells permit different organelles and need type-aware silhouettes. |

A topic may still reuse a general Block: a food web is a `network-diagram`, a genetics cross is a
`matrix-diagram`, and a life cycle is a `cycle`. Subject modules should not duplicate a general
relationship merely because a discipline frequently uses it. Future circuit symbols, molecular
structures, vector fields, anatomy maps, or other discipline-owned primitives belong in the
corresponding subject file.

## Topics for generation and visual QA

Use the prompts below as separate Slides generation requests. Each deliberately favors one visual
grammar, so a result that substitutes bullets or an unrelated shape also reveals a Block-selection
problem—not only a CSS problem.

| Expected Block | Test topic |
| :--- | :--- |
| `venn-diagram` | Compare plant and animal cells, clearly showing structures unique to each and structures shared by both. |
| `cause-effect-diagram` | Explain why eutrophication causes algal blooms, grouping nutrient sources and environmental conditions. |
| `layer-diagram` | Teach Earth's crust, mantle, outer core, and inner core from surface to center, including composition and thickness or state. |
| `network-diagram` | Build a grassland food web showing energy transfer from grasses and seeds to rabbits and mice, then to hawks and snakes. |
| `quadrant-diagram` | Classify common materials by electrical conductivity from low to high and magnetic response from weak to strong. |
| `spectrum-diagram` | Explain the electromagnetic spectrum from radio waves to gamma rays, showing the wavelength and frequency trend. |
| `pyramid-diagram` | Explain a four-level trophic energy pyramid using the 10 percent rule and energy values at every level. |
| `hierarchy-tree` | Classify matter into pure substances and mixtures, then show the important subtypes under each branch. |
| `flow-diagram` | Show the inputs, cellular process, and outputs of photosynthesis, including where the process occurs. |
| `cycle` | Explain the rock cycle and the transformations among igneous, sedimentary, and metamorphic rock. |
| `labeled-diagram` | Introduce the major parts of a plant cell and give one concise function for each label. |
| `timeline` | Trace how the atomic model changed from Dalton through Thomson, Rutherford, Bohr, and the quantum model. |
| `comparison` | Compare mitosis and meiosis by purpose, number of divisions, daughter cells, and genetic similarity. |
| `bar-chart` | Compare average monthly rainfall across four seasons using a small, clearly labeled dataset. |
| `coordinate-plot` | Teach reflections across the y-axis using four labeled points before and after transformation. |
| `geometry-model` | Explain Ceva's theorem with triangle vertices, three side points, three cevians, and their concurrency point. |
| `geometry-model` | Explain the Pythagorean theorem with a right triangle, named vertices, both legs, the hypotenuse, and a visible right-angle marker. |
| `concentric-diagram` | Show biological organization from organism to organ system, organ, tissue, and cell as nested levels. |
| `matrix-diagram` | Use a two-by-two Punnett square to cross B and b alleles and explain the four genotype outcomes. |
| `function-graph` | Compare y = x and y = x² from x = -2 to x = 2, emphasizing where their rates of change differ. |
| `force-diagram` | Draw and explain all forces on a book resting on a table, then contrast balanced and unbalanced cases. |
| `wave-diagram` | Teach equilibrium, crest, trough, amplitude, and one wavelength on a transverse wave. |
| `particle-diagram` | Compare an element, a compound, and a mixture using particle-level oxygen, water, and air models. |
| `reaction-diagram` | Explain the balanced formation of water from hydrogen and oxygen and show that atoms are conserved. |
| `cell-diagram` | Compare a plant cell with an animal cell, using type-correct organelles and one function per structure. |

For each generated lesson, inspect every slide at the canonical 16:9 size and at the actual preview
panel size. Check title/body separation, text wrapping, connector endpoints, axis labels, maximum
allowed items, first/last bands or layers, navigation, and browser console errors.
