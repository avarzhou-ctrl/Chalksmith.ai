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
        self.intro_section()
        self.visualize_unit_squares()
        self.derive_formula()
        self.summary_section()

    def intro_section(self):
        title = Text("What is Area?", color=BLUE).scale(1.5)
        definition = Text(
            "Area is the measure of the space\ninside a 2D shape.",
            font_size=36,
            t2c={"Area": YELLOW}
        ).next_to(title, DOWN, buff=1)

        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(definition, shift=UP))
        self.wait(3)
        
        self.play(FadeOut(title), FadeOut(definition))
        self.wait(0.5)

    def visualize_unit_squares(self):
        heading = Text("Counting Unit Squares", color=BLUE).to_edge(UP)
        self.play(Write(heading))

        # Create a rectangle container
        rect_outline = Rectangle(width=4, height=3, color=WHITE)
        rect_outline.shift(LEFT * 2)
        self.play(Create(rect_outline))

        # Create a grid of squares inside the rectangle
        grid = VGroup()
        for x in range(4):
            for y in range(3):
                # Calculate positions relative to the rectangle's bottom-left corner
                pos = rect_outline.get_corner(DL) + np.array([x + 0.5, y + 0.5, 0])
                sq = Square(side_length=1, stroke_width=2, color=GRAY)
                sq.move_to(pos)
                grid.add(sq)

        # Illustrate a "Unit Square"
        single_sq = grid[0].copy().set_color(YELLOW).set_fill(YELLOW, opacity=0.5)
        unit_label = Text("1 Unit Square", font_size=24, color=YELLOW).next_to(single_sq, DOWN)
        
        self.play(FadeIn(single_sq), Write(unit_label))
        self.wait(1)
        self.play(FadeOut(unit_label), single_sq.animate.set_fill(opacity=0))

        # Fill the grid one by one to show counting
        self.play(
            AnimationGroup(
                *[sq.animate.set_fill(BLUE, opacity=0.3) for sq in grid],
                lag_ratio=0.1,
                run_time=3
            )
        )

        counter_text = Text("Total: 12 Units", font_size=36).next_to(rect_outline, RIGHT, buff=1)
        self.play(Write(counter_text))
        self.wait(2)

        # Cleanup
        self.play(FadeOut(grid), FadeOut(rect_outline), FadeOut(counter_text), FadeOut(heading), FadeOut(single_sq))
        self.wait(0.5)

    def derive_formula(self):
        title = Text("The Rectangle Formula", color=BLUE).to_edge(UP)
        self.play(Write(title))

        # Create a clean rectangle
        shape = Rectangle(width=5, height=3, color=WHITE).shift(DOWN * 0.5)
        shape.set_fill(GREEN, opacity=0.2)
        self.play(Create(shape))

        # Dimension labels
        length_label = MathTex("Length = 5").next_to(shape, DOWN)
        width_label = MathTex("Width = 3").next_to(shape, RIGHT)
        
        self.play(Write(length_label))
        self.play(Write(width_label))
        self.wait(1)

        # Area Formula
        formula = MathTex("Area", "=", "Length", "\\times", "Width", color=YELLOW)
        formula.next_to(title, DOWN, buff=0.5)
        
        self.play(Write(formula))
        self.wait(1)

        # Substitution
        calc = MathTex("Area", "=", "5", "\\times", "3", "=", "15", color=YELLOW)
        calc.move_to(formula.get_center())
        
        self.play(ReplacementTransform(formula, calc))
        self.play(Indicate(calc[6]))
        self.wait(3)

        # Cleanup
        self.play(FadeOut(Group(*self.mobjects)))

    def summary_section(self):
        summary_title = Text("Summary", color=BLUE).scale(1.2).to_edge(UP)
        
        point1 = Text("• Area is the 2D surface space.", font_size=32).shift(UP * 1)
        point2 = Text("• Measured in 'square units'.", font_size=32).next_to(point1, DOWN, buff=0.5).align_to(point1, LEFT)
        point3 = Text("• Rectangle Area = Length x Width", font_size=32).next_to(point2, DOWN, buff=0.5).align_to(point1, LEFT)
        
        summary_group = VGroup(point1, point2, point3)
        
        self.play(Write(summary_title))
        for point in summary_group:
            self.play(FadeIn(point, shift=RIGHT))
            self.wait(1.5)

        thanks = Text("Happy Learning!", color=GOLD).next_to(summary_group, DOWN, buff=1)
        self.play(GrowFromCenter(thanks))
        self.wait(3)

        # Final cleanup
        self.play(FadeOut(Group(*self.mobjects)))
        self.wait(1)