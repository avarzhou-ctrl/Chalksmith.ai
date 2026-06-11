This lesson introduces the concept of area as the measurement of two-dimensional space within a shape. It visualizes the measurement process by counting individual unit squares and transitions into the formal calculation for rectangles using the length and width formula.

---CODE_START---
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
        self.rectangle_area_formula()
        self.conclusion()

    def introduction(self):
        title = Text("Understanding Area", color=BLUE).scale(1.2)
        definition = Paragraph(
            "Area is the amount of space",
            "inside a 2D shape.",
            alignment="center"
        ).next_to(title, DOWN, buff=0.5)

        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(definition))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(definition))

    def unit_square_concept(self):
        # Create a single unit square
        unit_sq = Square(side_length=2, color=YELLOW, fill_opacity=0.3)
        label = Text("1 Unit").scale(0.6)
        label_bottom = label.copy().next_to(unit_sq, DOWN)
        label_left = label.copy().rotate(90 * DEGREES).next_to(unit_sq, LEFT)
        
        unit_text = Text("This is 1 Square Unit").to_edge(UP)

        self.play(Create(unit_sq), Write(unit_text))
        self.play(Write(label_bottom), Write(label_left))
        self.wait(2)

        # Transition to a grid
        self.play(FadeOut(unit_text), FadeOut(label_bottom), FadeOut(label_left))
        self.play(unit_sq.animate.scale(0.5).to_edge(LEFT, buff=1))
        
        explanation = Text("We measure area by counting squares.", font_size=30).to_edge(UP)
        self.play(Write(explanation))

        # Create a 3x2 grid of squares
        grid = VGroup()
        for i in range(2): # rows
            for j in range(3): # cols
                s = Square(side_length=1, color=BLUE, fill_opacity=0.2)
                s.shift(RIGHT * j + DOWN * i)
                grid.add(s)
        
        grid.move_to(RIGHT * 2)
        
        # Animate the filling of the grid
        for i, sq in enumerate(grid):
            self.play(Create(sq), run_time=0.3)
            count = Text(str(i + 1), font_size=24).move_to(sq.get_center())
            self.add(count)
        
        result_text = Text("Area = 6 Square Units").next_to(grid, DOWN, buff=0.5)
        self.play(Write(result_text))
        self.wait(2)
        
        # Cleanup
        self.play(FadeOut(VGroup(*self.mobjects)))

    def rectangle_area_formula(self):
        # Header
        header = Text("The Rectangle Formula").to_edge(UP)
        self.play(Write(header))

        # Create Rectangle
        rect = Rectangle(width=5, height=3, color=GREEN, fill_opacity=0.1)
        rect.shift(LEFT * 1)
        
        # Length and Width Labels
        length_label = MathTex("L = 5").next_to(rect, DOWN)
        width_label = MathTex("W = 3").next_to(rect, LEFT)

        self.play(Create(rect))
        self.play(Write(length_label), Write(width_label))
        self.wait(1)

        # Show Grid overlay to prove formula
        grid_lines = VGroup()
        for i in range(1, 5):
            line = Line(rect.get_corner(UL) + RIGHT * i, rect.get_corner(DL) + RIGHT * i, color=GRAY, stroke_opacity=0.5)
            grid_lines.add(line)
        for i in range(1, 3):
            line = Line(rect.get_corner(UL) + DOWN * i, rect.get_corner(UR) + DOWN * i, color=GRAY, stroke_opacity=0.5)
            grid_lines.add(line)

        self.play(Create(grid_lines))
        self.wait(1)

        # Formula derivation
        formula = MathTex(
            r"\text{Area}", "=", r"\text{Length}", r"\times", r"\text{Width}"
        ).to_edge(RIGHT).shift(UP * 1)
        
        calc1 = MathTex(r"\text{Area} = 5 \times 3").next_to(formula, DOWN, aligned_edge=LEFT)
        calc2 = MathTex(r"\text{Area} = 15").next_to(calc1, DOWN, aligned_edge=LEFT, buff=0.5)
        calc2.set_color(YELLOW)

        self.play(Write(formula))
        self.wait(1)
        self.play(Write(calc1))
        self.wait(1)
        self.play(Write(calc2), Indicate(calc2))
        self.wait(3)

        self.play(FadeOut(VGroup(*self.mobjects)))

    def conclusion(self):
        summary_title = Text("Summary", color=BLUE).shift(UP * 2)
        
        point1 = Text("- Area measures surface space.", font_size=35).shift(UP * 0.5)
        point2 = Text("- It is measured in square units.", font_size=35).next_to(point1, DOWN, aligned_edge=LEFT)
        point3 = Text("- For rectangles: Area = Length x Width.", font_size=35).next_to(point2, DOWN, aligned_edge=LEFT)
        
        self.play(Write(summary_title))
        self.play(FadeIn(point1))
        self.wait(0.5)
        self.play(FadeIn(point2))
        self.wait(0.5)
        self.play(FadeIn(point3))
        self.wait(3)
        
        # Final screen clear
        self.play(FadeOut(VGroup(*self.mobjects)))