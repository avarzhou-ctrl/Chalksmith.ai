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


import numpy as np

# Custom components for the lesson
class BulletList(VGroup):
    def __init__(self, *items, **kwargs):
        line_spacing = kwargs.pop('line_spacing', 0.5)
        dot_symbol = "• "
        mobjects = [Text(f"{dot_symbol}{item}", **kwargs) for item in items]
        super().__init__(*mobjects)
        self.arrange(DOWN, aligned_edge=LEFT, buff=line_spacing)

class MainScene(Scene):
    def construct(self):
        self.intro_section()
        self.unit_square_concept()
        self.grid_method()
        self.formula_derivation()
        self.final_summary()

    def intro_section(self):
        title = Text("Understanding Area", color=BLUE).scale(1.2)
        subtitle = Text("Area of Rectangles", color=WHITE).scale(0.8).next_to(title, DOWN)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(2)
        self.play(FadeOut(*self.mobjects))

        definition_text = Text("Area is the amount of space inside a shape.", font_size=36)
        rect = Rectangle(width=5, height=3, color=YELLOW)
        
        self.play(Write(definition_text))
        self.play(definition_text.animate.to_edge(UP))
        self.play(Create(rect))
        
        rect_filled = rect.copy().set_fill(YELLOW, opacity=0.4)
        self.play(ReplacementTransform(rect, rect_filled))
        self.wait(1)
        self.play(FadeOut(*self.mobjects))

    def unit_square_concept(self):
        header = Text("We measure area using 'Unit Squares'", font_size=36).to_edge(UP)
        unit_square = Square(side_length=1.5, color=GREEN)
        unit_square.set_fill(GREEN, opacity=0.3)
        
        label_top = MathTex("1").next_to(unit_square, UP)
        label_side = MathTex("1").next_to(unit_square, LEFT)
        unit_text = Text("1 Square Unit", font_size=30).next_to(unit_square, DOWN, buff=0.5)

        self.play(Write(header))
        self.play(Create(unit_square))
        self.play(Write(label_top), Write(label_side))
        self.play(FadeIn(unit_text))
        self.wait(2)
        self.play(FadeOut(*self.mobjects))

    def grid_method(self):
        header = Text("Example: A 4x3 Rectangle", font_size=36).to_edge(UP)
        self.play(Write(header))

        rows, cols = 3, 4
        square_size = 1.0
        
        # Create grid of unit squares
        grid = VGroup()
        for r in range(rows):
            for c in range(cols):
                sq = Square(side_length=square_size, color=WHITE, stroke_width=2)
                sq.move_to([c * square_size, r * square_size, 0])
                grid.add(sq)
        
        grid.center().shift(LEFT * 1.5)

        # Main outline
        outline = Rectangle(
            width=cols * square_size, 
            height=rows * square_size, 
            color=BLUE, 
            stroke_width=4
        ).move_to(grid.get_center())
        
        self.play(Create(outline))
        self.wait(0.5)
        
        # Fill squares
        self.play(LaggedStart(*[FadeIn(sq) for sq in grid], lag_ratio=0.05))
        
        counter_text = Text("Total Squares: ", font_size=28)
        counter_num = Integer(0).next_to(counter_text, RIGHT)
        count_group = VGroup(counter_text, counter_num).to_edge(DOWN, buff=1)
        
        self.play(Write(count_group))

        for i, sq in enumerate(grid):
            self.play(
                sq.animate.set_fill(BLUE, opacity=0.5),
                counter_num.animate.set_value(i + 1),
                run_time=0.15
            )
        
        result = Text("Area = 12 Square Units", color=YELLOW, font_size=32).next_to(grid, RIGHT, buff=0.8)
        self.play(Write(result))
        self.wait(2)
        self.play(FadeOut(*self.mobjects))

    def formula_derivation(self):
        rect = Rectangle(width=4, height=2.5, color=WHITE).to_edge(LEFT, buff=1.5).shift(DOWN * 0.5)
        length_label = MathTex("length = 5").next_to(rect, DOWN)
        width_label = MathTex("width = 3").next_to(rect, LEFT)
        
        self.play(Create(rect), Write(length_label), Write(width_label))
        
        formula_header = Text("The Formula", font_size=32, color=BLUE)
        formula = MathTex("Area", "=", "L", "\\times", "W").scale(1.1)
        step1 = MathTex("Area", "=", "5", "\\times", "3").scale(1.1)
        step2 = MathTex("Area", "=", "15").scale(1.1).set_color(YELLOW)
        
        calc_group = VGroup(formula_header, formula, step1, step2).arrange(DOWN, buff=0.6)
        calc_group.to_edge(RIGHT, buff=1.5)
        
        self.play(Write(formula_header))
        self.play(Write(formula))
        self.wait(1)
        self.play(ReplacementTransform(formula.copy(), step1))
        self.wait(1)
        self.play(ReplacementTransform(step1.copy(), step2))
        self.play(Circumscribe(step2))
        self.wait(2)
        self.play(FadeOut(*self.mobjects))

    def final_summary(self):
        summary_title = Text("Key Takeaways", color=BLUE).to_edge(UP)
        
        points = BulletList(
            "Area is the space inside a 2D shape.",
            "Measured in square units (e.g., cm², in²).",
            "For Rectangles: Area = Length × Width",
            line_spacing=0.7,
            font_size=32
        ).center()
        
        points[2].set_color(YELLOW)

        self.play(Write(summary_title))
        self.play(FadeIn(points, shift=RIGHT))
        self.wait(3)
        
        self.play(FadeOut(*self.mobjects))
        thanks = Text("Happy Learning!", color=BLUE_B).scale(1.2)
        self.play(Write(thanks))
        self.wait(2)
        self.play(Unwrite(thanks))