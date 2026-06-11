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
        # Section 1: Introduction to Area
        self.intro_area()
        self.clear_screen()
        
        # Section 2: Area of a Rectangle
        self.rectangle_area()
        self.clear_screen()
        
        # Section 3: Area of a Triangle
        self.triangle_area()
        self.clear_screen()
        
        # Section 4: Area of a Circle
        self.circle_area()
        self.clear_screen()
        
        # Section 5: Summary
        self.summary_area()

    def intro_area(self):
        # Title
        title = Text("Area", font_size=60, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Definition
        definition = Text(
            "Area measures the size of a two-dimensional surface.",
            font_size=30,
            color=WHITE
        )
        definition.next_to(title, DOWN, buff=0.8)
        self.play(Write(definition))
        self.wait(1)
        
        # Examples of units
        units = Text("Measured in square units (e.g., cm², m², in²)", font_size=28, color=GRAY)
        units.next_to(definition, DOWN, buff=0.5)
        self.play(Write(units))
        self.wait(2)
        
        # Create a simple grid to visualize area
        grid = VGroup()
        for i in range(4):
            for j in range(4):
                square = Square(side_length=0.5, color=TEAL, fill_opacity=0.3)
                square.move_to(np.array([i*0.5 - 0.75, j*0.5 - 0.75, 0]))
                grid.add(square)
        grid.next_to(units, DOWN, buff=0.8)
        self.play(Create(grid), run_time=2)
        self.wait(1)
        
        # Label the grid
        grid_label = Text("A 4x4 grid = 16 square units", font_size=24, color=GOLD)
        grid_label.next_to(grid, DOWN, buff=0.4)
        self.play(Write(grid_label))
        self.wait(2)

    def rectangle_area(self):
        # Section title
        section_title = Text("Area of a Rectangle", font_size=48, color=BLUE)
        section_title.to_edge(UP)
        self.play(Write(section_title))
        self.wait(1)
        
        # Draw a rectangle
        rect = Rectangle(width=4, height=2.5, color=YELLOW, fill_opacity=0.4)
        rect.move_to(ORIGIN)
        self.play(Create(rect))
        self.wait(0.5)
        
        # Label length and width
        length_label = MathTex(r"\text{length} = 4", font_size=30, color=GREEN)
        length_label.next_to(rect, DOWN, buff=0.3)
        self.play(Write(length_label))
        
        width_label = MathTex(r"\text{width} = 2.5", font_size=30, color=GREEN)
        width_label.next_to(rect, LEFT, buff=0.3).shift(UP*0.5)
        self.play(Write(width_label))
        self.wait(1)
        
        # Formula
        formula = MathTex(r"\text{Area} = \text{length} \times \text{width}", font_size=36, color=WHITE)
        formula.next_to(length_label, DOWN, buff=0.6)
        self.play(Write(formula))
        self.wait(1)
        
        # Calculation
        calc = MathTex(r"\text{Area} = 4 \times 2.5 = 10", font_size=36, color=GOLD)
        calc.next_to(formula, DOWN, buff=0.4)
        self.play(Write(calc))
        self.wait(2)
        
        # Visual: Fill rectangle with unit squares
        unit_squares = VGroup()
        rect_corner = rect.get_corner(UL)
        for i in range(4):
            for j in range(5):
                small_sq = Square(side_length=0.5, color=TEAL, fill_opacity=0.2)
                small_sq.move_to(rect_corner + np.array([i*0.5 + 0.25, -j*0.5 - 0.25, 0]))
                unit_squares.add(small_sq)
        self.play(FadeIn(unit_squares, lag_ratio=0.05), run_time=2)
        self.wait(1)
        
        area_label = Text("10 square units", font_size=28, color=TEAL)
        area_label.next_to(calc, DOWN, buff=0.4)
        self.play(Write(area_label))
        self.wait(2)

    def triangle_area(self):
        # Section title
        section_title = Text("Area of a Triangle", font_size=48, color=BLUE)
        section_title.to_edge(UP)
        self.play(Write(section_title))
        self.wait(1)
        
        # Draw a triangle
        triangle = Polygon(
            [-2, -1.5, 0],
            [2, -1.5, 0],
            [0, 1.5, 0],
            color=ORANGE,
            fill_opacity=0.4
        )
        triangle.move_to(ORIGIN)
        self.play(Create(triangle))
        self.wait(0.5)
        
        # Draw height and base
        base_line = Line(triangle.get_vertices()[0], triangle.get_vertices()[1], color=GREEN)
        height_line = DashedLine(triangle.get_vertices()[2], np.array([0, -1.5, 0]), color=RED)
        right_angle = Rectangle(width=0.2, height=0.2, color=WHITE, fill_opacity=0.5)
        right_angle.move_to(np.array([0, -1.5, 0])).shift(DOWN*0.1 + RIGHT*0.1)
        
        base_label = MathTex(r"\text{base} = 4", font_size=28, color=GREEN)
        base_label.next_to(base_line, DOWN, buff=0.2)
        height_label = MathTex(r"\text{height} = 3", font_size=28, color=RED)
        height_label.next_to(height_line, RIGHT, buff=0.2)
        
        self.play(Create(base_line), Create(height_line), Create(right_angle))
        self.play(Write(base_label), Write(height_label))
        self.wait(1)
        
        # Formula
        formula = MathTex(r"\text{Area} = \frac{1}{2} \times \text{base} \times \text{height}", font_size=36, color=WHITE)
        formula.next_to(triangle, DOWN, buff=0.8)
        self.play(Write(formula))
        self.wait(1)
        
        # Calculation
        calc = MathTex(r"\text{Area} = \frac{1}{2} \times 4 \times 3 = 6", font_size=36, color=GOLD)
        calc.next_to(formula, DOWN, buff=0.4)
        self.play(Write(calc))
        self.wait(2)

    def circle_area(self):
        # Section title
        section_title = Text("Area of a Circle", font_size=48, color=BLUE)
        section_title.to_edge(UP)
        self.play(Write(section_title))
        self.wait(1)
        
        # Draw a circle
        circle = Circle(radius=2, color=PURPLE, fill_opacity=0.4)
        circle.move_to(ORIGIN)
        self.play(Create(circle))
        self.wait(0.5)
        
        # Draw radius
        radius_line = Line(circle.get_center(), circle.get_right(), color=GREEN)
        radius_label = MathTex(r"r = 2", font_size=30, color=GREEN)
        radius_label.next_to(radius_line, UP, buff=0.2)
        self.play(Create(radius_line), Write(radius_label))
        self.wait(1)
        
        # Formula
        formula = MathTex(r"\text{Area} = \pi r^2", font_size=36, color=WHITE)
        formula.next_to(circle, DOWN, buff=0.8)
        self.play(Write(formula))
        self.wait(1)
        
        # Calculation
        calc = MathTex(r"\text{Area} = \pi \times 2^2 = 4\pi \approx 12.57", font_size=36, color=GOLD)
        calc.next_to(formula, DOWN, buff=0.4)
        self.play(Write(calc))
        self.wait(2)
        
        # Visual approximation: inscribe a polygon
        polygon = RegularPolygon(n=8, radius=2, color=TEAL, fill_opacity=0.2)
        polygon.move_to(circle.get_center())
        self.play(FadeIn(polygon))
        self.wait(1)
        
        approx_text = Text("Approximating with polygons", font_size=24, color=GRAY)
        approx_text.next_to(calc, DOWN, buff=0.4)
        self.play(Write(approx_text))
        self.wait(2)

    def summary_area(self):
        # Title
        title = Text("Summary: Key Formulas", font_size=48, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Rectangle formula
        rect_formula = MathTex(r"\text{Rectangle: } A = l \times w", font_size=36, color=YELLOW)
        rect_formula.next_to(title, DOWN, buff=0.8)
        self.play(Write(rect_formula))
        
        # Triangle formula
        tri_formula = MathTex(r"\text{Triangle: } A = \frac{1}{2} \times b \times h", font_size=36, color=ORANGE)
        tri_formula.next_to(rect_formula, DOWN, buff=0.4)
        self.play(Write(tri_formula))
        
        # Circle formula
        circ_formula = MathTex(r"\text{Circle: } A = \pi r^2", font_size=36, color=PURPLE)
        circ_formula.next_to(tri_formula, DOWN, buff=0.4)
        self.play(Write(circ_formula))
        
        self.wait(1)
        
        # Key concept
        concept = Text(
            "Area measures the space inside a 2D shape.\nIt is always measured in square units.",
            font_size=28,
            color=WHITE,
            line_spacing=1.5
        )
        concept.next_to(circ_formula, DOWN, buff=0.8)
        self.play(Write(concept))
        self.wait(2)
        
        # Final message
        final_msg = Text("Practice calculating area with different shapes!", font_size=30, color=GOLD)
        final_msg.next_to(concept, DOWN, buff=0.6)
        self.play(Write(final_msg))
        self.wait(3)

    def clear_screen(self):
        """Fade out all mobjects currently in the scene."""
        mobjects_to_fade = [mob for mob in self.mobjects if isinstance(mob, VMobject)]
        if mobjects_to_fade:
            self.play(FadeOut(VGroup(*mobjects_to_fade)))
        self.wait(0.5)