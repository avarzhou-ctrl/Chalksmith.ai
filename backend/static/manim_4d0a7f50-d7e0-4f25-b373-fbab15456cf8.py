from manim import *
# Compatibility layer for LLM-hallucinated colors and classes
BROWN = "#8B4513"
SANDY_BROWN = "#F4A460"
MAGENTA = "#FF00FF"
CYAN = "#00FFFF"
DARK_GRAY = "#A9A9A9"
LIGHT_GRAY = "#D3D3D3"
PINK = "#FFC0CB"
LIME = "#00FF00"
MAROON = "#800000"
NAVY = "#000080"
OLIVE = "#808000"
class BulletList(VGroup):
    def __init__(self, *items, **kwargs):
        line_spacing = kwargs.pop('line_spacing', 0.5)
        dot = '• '
        mobjects = [Text(f'{dot}{item}', **kwargs) for item in items]
        super().__init__(*mobjects)
        self.arrange(DOWN, aligned_edge=LEFT, buff=line_spacing)

def Capsule(**kwargs):
    width = kwargs.pop('width', 2)
    height = kwargs.pop('height', 1)
    return RoundedRectangle(corner_radius=min(width, height)/2, width=width, height=height, **kwargs)

# Legacy Compatibility for common LLM hallucinations
TextMobject = Text
TexMobject = Tex
ShowCreation = Create
ApplyMethod = lambda m, *args, **kwargs: m.animate.method(*args, **kwargs) if hasattr(m, 'animate') else m
ReplacementTransform = Transform

# Monkey-patch Line to prevent crashes on hallucinated .bend() method
Line.bend = lambda self, *args, **kwargs: self
Mobject.set_color_by_gradient = lambda self, *args, **kwargs: self



class MainScene(Scene):
    def construct(self):
        self.introduction()
        self.unit_square_concept()
        self.rectangle_area_derivation()
        self.conclusion()

    def introduction(self):
        # Title and definition
        title = Text("Understanding Area", color=BLUE).scale(1.2)
        definition = Paragraph(
            "Area is the amount of space",
            "inside a 2D shape.",
            alignment="center"
        ).scale(0.8).next_to(title, DOWN, buff=0.5)

        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(definition))
        self.wait(2)

        # Illustrate with a circle and square
        shapes = VGroup(
            Circle(radius=1, color=GREEN, fill_opacity=0.5),
            Square(side_length=2, color=ORANGE, fill_opacity=0.5)
        ).arrange(RIGHT, buff=2).shift(DOWN * 1.5)

        self.play(Create(shapes))
        self.wait(2)

        # Clear section
        self.play(FadeOut(VGroup(title, definition, shapes)))
        self.wait(1)

    def unit_square_concept(self):
        section_title = Text("The Unit Square", color=YELLOW).to_edge(UP)
        self.play(Write(section_title))

        # Create a single unit square
        unit_sq = Square(side_length=2, color=WHITE)
        unit_sq.set_fill(BLUE, opacity=0.3)
        
        labels = VGroup(
            Text("1 unit", font_size=24).next_to(unit_sq, DOWN),
            Text("1 unit", font_size=24).rotate(90 * DEGREES).next_to(unit_sq, LEFT)
        )

        explanation = Text(
            "We measure area by counting \nhow many unit squares fit inside.",
            font_size=30
        ).to_edge(RIGHT, buff=1)

        self.play(Create(unit_sq), Write(labels))
        self.wait(1)
        self.play(Write(explanation))
        self.wait(3)

        self.play(FadeOut(VGroup(section_title, unit_sq, labels, explanation)))

    def rectangle_area_derivation(self):
        section_title = Text("Calculating Rectangle Area", color=GOLD).to_edge(UP)
        self.play(Write(section_title))

        # Create a 4x3 rectangle grid
        rect_width = 4
        rect_height = 3
        main_rect = Rectangle(width=rect_width, height=rect_height, color=WHITE)
        main_rect.shift(LEFT * 2)

        # Create the grid units
        grid_units = VGroup()
        for i in range(rect_height):
            for j in range(rect_width):
                sq = Square(side_length=1, color=GRAY, stroke_width=1)
                sq.move_to(main_rect.get_corner(UL) + RIGHT * (j + 0.5) + DOWN * (i + 0.5))
                grid_units.add(sq)

        self.play(Create(main_rect))
        self.wait(1)

        # Fill the grid and count
        counter_text = Text("Squares: 0", font_size=36).to_edge(RIGHT, buff=2).shift(UP)
        self.play(Write(counter_text))

        for i, sq in enumerate(grid_units):
            new_counter = Text(f"Squares: {i+1}", font_size=36).move_to(counter_text)
            self.play(
                sq.animate.set_fill(PURPLE, opacity=0.6),
                Transform(counter_text, new_counter),
                run_time=0.15
            )

        self.wait(1)

        # Transition to formula
        dim_labels = VGroup(
            MathTex("4 \\text{ units}").next_to(main_rect, DOWN),
            MathTex("3 \\text{ units}").rotate(90 * DEGREES).next_to(main_rect, LEFT)
        )
        
        formula = MathTex(
            "\\text{Area} = \\text{Width} \\times \\text{Height}",
            color=YELLOW
        ).next_to(counter_text, DOWN, buff=1)

        calculation = MathTex(
            "\\text{Area} = 4 \\times 3 = 12",
            color=GREEN
        ).next_to(formula, DOWN, buff=0.5)

        self.play(Write(dim_labels))
        self.wait(1)
        self.play(Write(formula))
        self.wait(1)
        self.play(Write(calculation))
        self.play(Indicate(calculation))
        self.wait(3)

        self.play(FadeOut(VGroup(section_title, main_rect, grid_units, counter_text, dim_labels, formula, calculation)))

    def conclusion(self):
        final_text = Text("Area = Space Occupied", color=BLUE).scale(1.2)
        summary = Paragraph(
            "1. Define the unit square.",
            "2. Count how many fit inside.",
            "3. Use formulas for efficiency.",
            alignment="left"
        ).scale(0.8).next_to(final_text, DOWN, buff=0.8)

        self.play(Write(final_text))
        self.wait(1)
        self.play(FadeIn(summary))
        self.wait(4)

        # Final Clean up
        self.play(FadeOut(VGroup(*self.mobjects)))
        self.wait(1)