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
        """Main execution order of the scene."""
        self.introduction()
        self.explaining_unit_squares()
        self.rectangle_area()
        self.triangle_area()
        self.summary_and_conclusion()

    def introduction(self):
        """Introduction to the concept of area."""
        title = Text("What is Area?", color=BLUE).scale(1.2)
        definition = Text("Area is the measure of the space inside a 2D shape.", font_size=28)
        definition.next_to(title, DOWN, buff=0.5)

        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(definition))
        self.wait(2)

        # Illustrate with a simple square
        sq = Square(side_length=3, color=WHITE)
        sq.shift(DOWN * 1)
        self.play(
            FadeOut(definition),
            title.animate.to_edge(UP).scale(0.8)
        )
        self.play(Create(sq))
        self.wait(0.5)
        
        # Filling the area
        self.play(sq.animate.set_fill(BLUE, opacity=0.5))
        self.wait(1)
        
        area_label = Text("Area", color=WHITE).move_to(sq.get_center())
        self.play(Write(area_label))
        self.wait(2)

        self.play(FadeOut(VGroup(title, sq, area_label)))
        self.wait(1)

    def explaining_unit_squares(self):
        """How we measure area using grid squares."""
        title = Text("Measuring with Unit Squares", color=GREEN).to_edge(UP)
        self.play(Write(title))

        # Create a 3x3 grid
        unit_size = 1.0
        grid = VGroup()
        for i in range(3):
            for j in range(3):
                s = Square(side_length=unit_size, color=GRAY, stroke_width=2)
                s.move_to(np.array([j - 1, i - 1, 0]) * unit_size)
                grid.add(s)
        
        grid.center()
        self.play(Create(grid))
        self.wait(1)

        explainer = Text("We count how many 'unit squares' fit inside.", font_size=24)
        explainer.next_to(grid, DOWN, buff=0.5)
        self.play(Write(explainer))
        
        # Color the squares one by one
        count_labels = VGroup()
        for i, sq in enumerate(grid):
            num = Text(str(i + 1), font_size=24).move_to(sq.get_center())
            count_labels.add(num)
            self.play(
                sq.animate.set_fill(GREEN, opacity=0.5),
                FadeIn(num),
                run_time=0.3
            )
        
        self.wait(1)
        result = MathTex(r"Area = 9 \text{ units}^2", color=YELLOW)
        result.next_to(explainer, DOWN)
        self.play(Write(result))
        self.wait(2)

        self.play(FadeOut(VGroup(title, grid, count_labels, explainer, result)))
        self.wait(1)

    def rectangle_area(self):
        """Area formula for a rectangle."""
        title = Text("The Rectangle Formula", color=ORANGE).to_edge(UP)
        self.play(Write(title))

        rect = Rectangle(width=5, height=3, color=WHITE)
        rect.shift(LEFT * 1)
        self.play(Create(rect))

        # Labels
        width_label = Text("Width (W)", font_size=24).next_to(rect, DOWN)
        height_label = Text("Height (H)", font_size=24).next_to(rect, LEFT)
        
        self.play(Write(width_label), Write(height_label))
        self.play(rect.animate.set_fill(ORANGE, opacity=0.3))
        self.wait(1)

        formula = MathTex(r"Area = Width \times Height", color=WHITE)
        formula.to_edge(RIGHT).shift(UP * 0.5)
        
        formula_symbolic = MathTex(r"A = W \times H", color=ORANGE)
        formula_symbolic.next_to(formula, DOWN, buff=0.5)

        self.play(Write(formula))
        self.wait(1)
        self.play(Write(formula_symbolic))
        self.play(Indicate(formula_symbolic))
        self.wait(2)

        self.play(FadeOut(VGroup(title, rect, width_label, height_label, formula, formula_symbolic)))
        self.wait(1)

    def triangle_area(self):
        """Area of a triangle as half a rectangle."""
        title = Text("Area of a Triangle", color=PURPLE).to_edge(UP)
        self.play(Write(title))

        # Create a rectangle and its diagonal to show the triangle
        base_val = 4
        height_val = 3
        
        rect = DashedVMobject(Rectangle(width=base_val, height=height_val, color=GRAY))
        self.play(Create(rect))
        
        # Create triangle
        tri_points = [
            rect.get_corner(DL),
            rect.get_corner(DR),
            rect.get_corner(UR)
        ]
        triangle = Polygon(*tri_points, color=PURPLE)
        
        self.play(Create(triangle))
        self.play(triangle.animate.set_fill(PURPLE, opacity=0.5))
        self.wait(1)

        explainer = Text("A triangle is half of a rectangle.", font_size=24)
        explainer.next_to(rect, DOWN, buff=1.0)
        self.play(Write(explainer))

        # Formulas
        formula = MathTex(r"Area = \frac{1}{2} \times \text{Base} \times \text{Height}", color=WHITE)
        formula.to_edge(RIGHT, buff=0.5).shift(UP * 1)
        
        base_line_label = Text("Base (b)", font_size=24).next_to(rect, DOWN, buff=0.2)
        height_line_label = Text("Height (h)", font_size=24).next_to(rect, RIGHT, buff=0.2)
        
        self.play(
            FadeIn(base_line_label),
            FadeIn(height_line_label),
            Write(formula)
        )
        self.wait(2)

        self.play(FadeOut(VGroup(title, rect, triangle, explainer, formula, base_line_label, height_line_label)))
        self.wait(1)

    def summary_and_conclusion(self):
        """Recap of the concepts."""
        title = Text("Summary", color=YELLOW).to_edge(UP)
        self.play(Write(title))

        points = VGroup(
            Text("1. Area is the space inside a shape.", font_size=32),
            Text("2. Measured in square units (e.g., m², cm²).", font_size=32),
            Text("3. Rectangle: A = Length × Width", font_size=32),
            Text("4. Triangle: A = ½ × Base × Height", font_size=32)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        
        points.center()
        
        for point in points:
            self.play(Write(point))
            self.wait(0.5)
        
        self.wait(2)
        
        # Final cleanup
        self.play(FadeOut(VGroup(title, points)))
        
        final_text = Text("Keep Exploring Geometry!", color=BLUE).scale(1.2)
        self.play(GrowFromCenter(final_text))
        self.wait(2)
        self.play(FadeOut(final_text))
        self.wait(1)

# Ensure the script ends with a clean empty scene as requested
# End of script. Run with: manim -pql scene.py MainScene