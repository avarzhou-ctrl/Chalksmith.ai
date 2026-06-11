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
        self.rectangle_area()
        self.triangle_area()
        self.circle_area_formula()
        self.conclusion()

    def introduction(self):
        title = Text("Introduction to Area", color=BLUE).scale(1.2)
        definition = Text("Area is the measure of how much space\nis inside a 2D shape.", font_size=32)
        definition.next_to(title, DOWN, buff=0.5)
        
        box = Rectangle(width=6, height=3, color=WHITE).shift(DOWN * 1)
        fill_label = Text("Space Inside", color=YELLOW).scale(0.8).move_to(box.get_center())

        self.play(Write(title))
        self.wait(1)
        self.play(Write(definition))
        self.wait(1)
        self.play(Create(box))
        self.play(box.animate.set_fill(YELLOW, opacity=0.3))
        self.play(FadeIn(fill_label))
        self.wait(2)
        
        self.play(FadeOut(VGroup(title, definition, box, fill_label)))
        self.wait(0.5)

    def unit_square_concept(self):
        header = Text("The Unit Square").to_edge(UP)
        unit_sq = Square(side_length=2, color=GREEN)
        unit_sq.set_fill(GREEN, opacity=0.2)
        
        label_side_1 = Text("1 unit").scale(0.6).next_to(unit_sq, LEFT)
        label_side_2 = Text("1 unit").scale(0.6).next_to(unit_sq, DOWN)
        
        area_text = MathTex(r"\text{Area} = 1 \times 1 = 1 \text{ unit}^2")
        area_text.next_to(unit_sq, RIGHT, buff=1)

        self.play(Write(header))
        self.play(Create(unit_sq))
        self.play(Write(label_side_1), Write(label_side_2))
        self.wait(1)
        self.play(Write(area_text))
        self.wait(2)

        self.play(FadeOut(VGroup(header, unit_sq, label_side_1, label_side_2, area_text)))
        self.wait(0.5)

    def rectangle_area(self):
        header = Text("Area of a Rectangle").to_edge(UP)
        
        # Build a 4x3 grid manually using squares
        grid = VGroup()
        for i in range(3): # Rows
            for j in range(4): # Cols
                sq = Square(side_length=1, color=GRAY).shift(RIGHT*j + DOWN*i)
                grid.add(sq)
        
        grid.move_to(ORIGIN)
        
        brace_w = Brace(grid, LEFT, color=WHITE)
        label_w = Text("3 units", color=WHITE).scale(0.6).next_to(brace_w, LEFT)
        
        brace_l = Brace(grid, BOTTOM, color=WHITE)
        label_l = Text("4 units", color=WHITE).scale(0.6).next_to(brace_l, DOWN)

        formula = MathTex(r"\text{Area} = \text{Length} \times \text{Width}")
        formula.shift(UP * 1.5 + RIGHT * 4)
        
        calc = MathTex(r"A = 4 \times 3 = 12 \text{ units}^2")
        calc.next_to(formula, DOWN, buff=0.5)

        self.play(Write(header))
        self.play(LaggedStartMap(Create, grid, run_time=2))
        self.play(Create(brace_w), Write(label_w))
        self.play(Create(brace_l), Write(label_l))
        self.wait(1)
        
        self.play(Write(formula))
        self.play(grid.animate.set_fill(BLUE, opacity=0.4))
        self.play(Write(calc))
        self.wait(3)

        self.play(FadeOut(VGroup(header, grid, brace_w, label_w, brace_l, label_l, formula, calc)))
        self.wait(0.5)

    def triangle_area(self):
        header = Text("Area of a Triangle").to_edge(UP)
        
        # Create a rectangle and a triangle inside it
        rect = Rectangle(width=4, height=3, color=WHITE, stroke_dash_array=[5, 5])
        tri = Polygon([-2, -1.5, 0], [2, -1.5, 0], [2, 1.5, 0], color=RED)
        tri.set_fill(RED, opacity=0.3)
        
        label_base = Text("base", color=WHITE).scale(0.7).next_to(rect, DOWN)
        label_height = Text("height", color=WHITE).scale(0.7).next_to(rect, RIGHT)
        
        formula = MathTex(r"A = \frac{1}{2} \times \text{base} \times \text{height}")
        formula.shift(LEFT * 3)

        self.play(Write(header))
        self.play(Create(rect))
        self.play(Write(label_base), Write(label_height))
        self.wait(1)
        
        self.play(Create(tri))
        self.play(Write(formula))
        
        explanation = Text("A triangle is half\nof its bounding rectangle.", font_size=24)
        explanation.next_to(formula, DOWN, buff=0.5)
        self.play(Write(explanation))
        self.wait(3)

        self.play(FadeOut(VGroup(header, rect, tri, label_base, label_height, formula, explanation)))
        self.wait(0.5)

    def circle_area_formula(self):
        header = Text("Area of a Circle").to_edge(UP)
        
        circle = Circle(radius=2, color=PURPLE)
        circle.set_fill(PURPLE, opacity=0.2)
        
        center_dot = Dot(circle.get_center())
        radius_line = Line(circle.get_center(), circle.get_right(), color=WHITE)
        radius_label = MathTex(r"r").next_to(radius_line, UP, buff=0.1)
        
        formula = MathTex(r"A = \pi r^2").scale(1.5)
        formula.shift(RIGHT * 3.5)

        self.play(Write(header))
        self.play(Create(circle), FadeIn(center_dot))
        self.play(Create(radius_line), Write(radius_label))
        self.wait(1)
        self.play(Write(formula))
        self.play(Indicate(formula))
        self.wait(3)

        self.play(FadeOut(VGroup(header, circle, center_dot, radius_line, radius_label, formula)))
        self.wait(0.5)

    def conclusion(self):
        final_text = Text("Summary", color=GOLD).scale(1.2)
        
        # Build a manual list using VGroup
        summary_points = VGroup(
            Text("• Area measures 2D space inside shapes.", font_size=28),
            Text("• Units are always squared (e.g., cm², m²).", font_size=28),
            Text("• Rectangles: Length × Width.", font_size=28),
            Text("• Triangles: 1/2 × Base × Height.", font_size=28),
            Text("• Circles: π × r².", font_size=28)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        
        summary_points.next_to(final_text, DOWN, buff=0.8)

        self.play(Write(final_text))
        self.play(LaggedStartMap(FadeIn, summary_points, shift=RIGHT, run_time=3))
        self.wait(4)
        
        self.play(FadeOut(VGroup(final_text, summary_points)))
        self.wait(1)
        
        thank_you = Text("Keep Exploring Geometry!", color=WHITE).scale(0.8)
        self.play(Write(thank_you))
        self.play(FadeOut(thank_you))
        self.wait(1)

# To render this scene, run:
# manim -pql scene_file.py MainScene

        # Final Cleanup
        self.play(FadeOut(VGroup(*self.mobjects)))