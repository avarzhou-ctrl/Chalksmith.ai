from manim import *
# Compatibility layer for LLM-hallucinated colors and classes
BROWN = "#8B4513"
SANDY_BROWN = "#F4A460"
MAGENTA = "#FF00FF"
CYAN = "#00FFFF"
DARK_GRAY = "#A9A9A9"
LIGHT_GRAY = "#D3D3D3"
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

# Monkey-patch Line to prevent crashes on hallucinated .bend() method
Line.bend = lambda self, *args, **kwargs: self



class MainScene(Scene):
    def construct(self):
        self.intro_section()
        self.unit_square_section()
        self.rectangle_section()
        self.triangle_section()
        self.summary_section()

    def intro_section(self):
        title = Text("Understanding Area", font_size=48, color=WHITE).to_edge(UP)
        underline = Line(LEFT, RIGHT, color=BLUE).scale(4).next_to(title, DOWN)
        
        definition = Text(
            "Area is the measure of space inside a 2D shape.",
            font_size=32
        ).shift(UP * 0.5)
        
        demo_shape = RegularPolygon(n=6, radius=1.5, color=TEAL).shift(DOWN * 1.5)
        
        self.play(Write(title), Create(underline))
        self.wait(0.5)
        self.play(Write(definition))
        self.play(Create(demo_shape))
        self.play(demo_shape.animate.set_fill(TEAL, opacity=0.5))
        self.wait(2)
        
        self.play(
            FadeOut(title), 
            FadeOut(underline), 
            FadeOut(definition), 
            FadeOut(demo_shape)
        )

    def unit_square_section(self):
        title = Text("The Unit Square", font_size=40, color=GOLD).to_edge(UP)
        
        unit_square = Square(side_length=2, color=WHITE)
        unit_square.set_fill(YELLOW, opacity=0.3)
        
        label_bottom = MathTex("1 \\text{ unit}").next_to(unit_square, DOWN)
        label_left = MathTex("1 \\text{ unit}").next_to(unit_square, LEFT)
        
        area_label = MathTex("Area = 1 \\text{ unit}^2").next_to(unit_square, RIGHT, buff=1)
        
        explanation = Text(
            "We measure area by counting how many\nunit squares fit inside a shape.",
            font_size=24
        ).to_edge(DOWN, buff=1)
        
        self.play(Write(title))
        self.play(Create(unit_square))
        self.play(Write(label_bottom), Write(label_left))
        self.wait(1)
        self.play(Write(area_label))
        self.play(Write(explanation))
        self.wait(3)
        
        self.play(FadeOut(VGroup(*self.mobjects)))

    def rectangle_section(self):
        title = Text("Area of a Rectangle", font_size=40, color=BLUE).to_edge(UP)
        
        # Create a 4x3 grid manually using VGroup and Squares
        rows = 3
        cols = 4
        side = 1.0
        grid = VGroup()
        
        for r in range(rows):
            for c in range(cols):
                sq = Square(side_length=side, color=GRAY, stroke_width=2)
                sq.move_to(np.array([c * side, -r * side, 0]))
                grid.add(sq)
        
        grid.center().shift(LEFT * 1)
        
        # Labels for dimensions
        brace_bottom = Brace(grid, DOWN, color=WHITE)
        label_width = MathTex("4 \\text{ units}").next_to(brace_bottom, DOWN)
        
        brace_left = Brace(grid, LEFT, color=WHITE)
        label_height = MathTex("3 \\text{ units}").next_to(brace_left, LEFT)
        
        formula = MathTex("Area", "=", "Length", "\\times", "Width").scale(1.2)
        formula.to_edge(RIGHT, buff=0.5).shift(UP * 0.5)
        calculation = MathTex("Area", "=", "4", "\\times", "3", "=", "12").scale(1.2)
        calculation.next_to(formula, DOWN, buff=0.5)
        
        self.play(Write(title))
        self.play(Create(grid, run_time=2))
        self.play(Create(brace_bottom), Write(label_width))
        self.play(Create(brace_left), Write(label_height))
        self.wait(1)
        
        # Fill squares one by one to show counting
        for sq in grid:
            sq.set_fill(BLUE, opacity=0.5)
        
        self.play(LaggedStart(*[FadeIn(sq.copy().set_fill(BLUE, opacity=0.5)) for sq in grid], lag_ratio=0.05))
        self.play(Write(formula))
        self.wait(1)
        self.play(Write(calculation))
        self.wait(3)
        
        self.play(FadeOut(VGroup(*self.mobjects)))

    def triangle_section(self):
        title = Text("Area of a Triangle", font_size=40, color=ORANGE).to_edge(UP)
        
        # Draw a rectangle first to show relationship
        rect_color = GRAY
        rect = Rectangle(width=4, height=3, color=rect_color).set_stroke(opacity=0.5)
        rect.shift(LEFT * 2)
        
        # Draw the triangle inside
        vertices = [
            rect.get_corner(DL),
            rect.get_corner(DR),
            rect.get_corner(UR)
        ]
        triangle = Polygon(*vertices, color=ORANGE, stroke_width=4)
        triangle.set_fill(ORANGE, opacity=0.4)
        
        base_label = MathTex("b").next_to(rect, DOWN)
        height_label = MathTex("h").next_to(rect, RIGHT)
        
        formula_tri = MathTex(
            "Area = \\frac{1}{2} \\times \\text{base} \\times \\text{height}"
        ).scale(0.9).to_edge(RIGHT, buff=1)
        
        logic_text = Text(
            "A triangle is half of a rectangle\nwith the same base and height.",
            font_size=22
        ).next_to(formula_tri, DOWN, buff=1)
        
        self.play(Write(title))
        self.play(Create(rect))
        self.play(Write(base_label), Write(height_label))
        self.wait(1)
        
        self.play(Create(triangle))
        self.play(Write(logic_text))
        self.wait(1)
        self.play(Write(formula_tri))
        
        # Show the "other half" to emphasize
        other_triangle = Polygon(
            rect.get_corner(DL),
            rect.get_corner(UL),
            rect.get_corner(UR),
            color=WHITE,
            stroke_width=2
        ).set_stroke(dash_length=0.1)
        
        self.play(Create(other_triangle))
        self.wait(3)
        
        self.play(FadeOut(VGroup(*self.mobjects)))

    def summary_section(self):
        title = Text("Summary", font_size=44, color=PURPLE).to_edge(UP)
        
        summary_items = VGroup(
            Text("• Area is the space inside a 2D boundary.", font_size=28),
            Text("• Measured in square units (e.g., cm², m²).", font_size=28),
            MathTex("\\text{Rectangle: } A = l \\times w", font_size=38, color=BLUE),
            MathTex("\\text{Triangle: } A = \\frac{1}{2} b \\times h", font_size=38, color=ORANGE),
            MathTex("\\text{Circle: } A = \\pi r^2", font_size=38, color=TEAL)
        ).arrange(DOWN, center=True, buff=0.5).shift(DOWN * 0.5)
        
        self.play(Write(title))
        for item in summary_items:
            self.play(FadeIn(item, shift=UP * 0.2))
            self.wait(0.5)
            
        self.wait(4)
        self.play(FadeOut(VGroup(*self.mobjects)))
        
        final_text = Text("Keep Exploring Geometry!", font_size=40, color=GOLD)
        self.play(Write(final_text))
        self.play(final_text.animate.scale(1.2), run_time=1)
        self.play(FadeOut(final_text))
        self.wait(1)

# Execution command: manim -pql scene.py MainScene
# Note: Ensure manim is installed and the environment is active.