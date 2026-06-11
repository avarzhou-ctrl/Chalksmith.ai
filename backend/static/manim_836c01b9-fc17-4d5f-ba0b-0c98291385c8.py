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
        self.square_unit_section()
        self.rectangle_section()
        self.triangle_section()
        self.summary_section()

    def intro_section(self):
        title = Text("What is Area?", font_size=48, color=BLUE)
        definition = Text(
            "Area is the amount of space inside\na 2-dimensional shape.",
            font_size=32,
            t2c={"2-dimensional": YELLOW}
        )
        definition.next_to(title, DOWN, buff=1)
        
        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(definition, shift=UP))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(definition))

    def square_unit_section(self):
        header = Text("The Unit Square", color=GOLD).to_edge(UP)
        unit_square = Square(side_length=2, color=WHITE)
        unit_square.set_fill(BLUE, opacity=0.5)
        
        label_side = MathTex("1", font_size=36).next_to(unit_square, DOWN)
        label_side_2 = MathTex("1", font_size=36).next_to(unit_square, LEFT)
        
        area_label = MathTex("Area = 1 \times 1 = 1", font_size=40)
        area_label.next_to(unit_square, RIGHT, buff=1)

        self.play(Create(header))
        self.play(Create(unit_square))
        self.play(Write(label_side), Write(label_side_2))
        self.wait(1)
        self.play(Write(area_label))
        self.wait(2)
        
        self.play(FadeOut(header), FadeOut(unit_square), FadeOut(label_side), FadeOut(label_side_2), FadeOut(area_label))

    def rectangle_section(self):
        header = Text("Area of a Rectangle", color=GOLD).to_edge(UP)
        rect = Rectangle(width=4, height=3, color=WHITE)
        rect.set_fill(TEAL, opacity=0.3)
        
        width_label = MathTex("4", font_size=36).next_to(rect, DOWN)
        height_label = MathTex("3", font_size=36).next_to(rect, LEFT)
        
        # Create a grid to show units
        grid = VGroup()
        for i in range(4):
            for j in range(3):
                sq = Square(side_length=1, color=GRAY, stroke_width=1)
                sq.move_to(rect.get_corner(DL) + np.array([i + 0.5, j + 0.5, 0]))
                grid.add(sq)

        formula = MathTex("Area = Base \\times Height", color=YELLOW).shift(UP * 2.5)
        calc = MathTex("Area = 4 \\times 3 = 12", font_size=42).shift(DOWN * 2.5)

        self.play(Create(header))
        self.play(Create(rect))
        self.play(Write(width_label), Write(height_label))
        self.wait(1)
        
        self.play(LaggedStart(*[Create(s) for s in grid], lag_ratio=0.05))
        self.play(Write(formula))
        self.wait(1)
        self.play(Write(calc))
        self.wait(3)
        
        self.play(FadeOut(header), FadeOut(rect), FadeOut(grid), FadeOut(width_label), FadeOut(height_label), FadeOut(formula), FadeOut(calc))

    def triangle_section(self):
        header = Text("Area of a Triangle", color=GOLD).to_edge(UP)
        
        # Define rectangle base for context
        rect = Rectangle(width=4, height=3, color=GRAY, stroke_style=DASHED)
        
        # Define triangle points
        p1 = rect.get_corner(DL)
        p2 = rect.get_corner(DR)
        p3 = rect.get_corner(UR)
        
        triangle = Polygon(p1, p2, p3, color=ORANGE)
        triangle.set_fill(ORANGE, opacity=0.5)
        
        base_label = MathTex("b", font_size=36).next_to(rect, DOWN)
        height_label = MathTex("h", font_size=36).next_to(rect, RIGHT)
        
        formula = MathTex("Area = \\frac{1}{2} \\times Base \\times Height", color=YELLOW).shift(UP * 2.5)
        explanation = Text("A triangle is half of a rectangle.", font_size=24).next_to(formula, DOWN)

        self.play(Create(header))
        self.play(Create(rect))
        self.wait(1)
        self.play(Create(triangle))
        self.play(Write(base_label), Write(height_label))
        self.wait(1)
        self.play(Write(formula))
        self.play(FadeIn(explanation))
        self.wait(3)
        
        self.play(FadeOut(header), FadeOut(rect), FadeOut(triangle), FadeOut(base_label), FadeOut(height_label), FadeOut(formula), FadeOut(explanation))

    def summary_section(self):
        title = Text("Summary", color=BLUE).to_edge(UP)
        
        rect_formula = MathTex("Rectangle: Area = w \\times h", color=TEAL)
        tri_formula = MathTex("Triangle: Area = \\frac{1}{2} b \\times h", color=ORANGE)
        circle_formula = MathTex("Circle: Area = \\pi r^2", color=PURPLE)
        
        formulas = VGroup(rect_formula, tri_formula, circle_formula).arrange(DOWN, buff=0.5)
        
        self.play(Write(title))
        for f in formulas:
            self.play(FadeIn(f, shift=RIGHT))
            self.wait(0.5)
            
        final_text = Text("Area is measured in square units (e.g. m², cm²)", font_size=28, color=GRAY)
        final_text.next_to(formulas, DOWN, buff=1)
        
        self.play(Write(final_text))
        self.wait(4)
        
        self.play(FadeOut(VGroup(*self.mobjects)))

# Command to run: manim -pql scene.py MainScene
# Ensure you have manim installed: pip install manim
# The output will be a video file demonstrating area concepts.

# END OF SCRIPT