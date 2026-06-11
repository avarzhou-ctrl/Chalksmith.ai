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
        self.unit_square_concept()
        self.rectangle_area()
        self.triangle_area()
        self.summary_section()

    def intro_section(self):
        title = Text("Understanding Area", font_size=48, color=BLUE)
        subtitle = Text("Measuring 2D Space", font_size=32, color=GRAY)
        VGroup(title, subtitle).arrange(DOWN)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))

    def unit_square_concept(self):
        # Header
        header = Text("What is Area?", font_size=36).to_edge(UP)
        self.play(Write(header))

        # Create a unit square
        unit_square = Square(side_length=1.0, color=WHITE)
        unit_label = Text("1 Unit", font_size=24).next_to(unit_square, DOWN)
        unit_label_side = Text("1 Unit", font_size=24).next_to(unit_square, LEFT)
        
        unit_group = VGroup(unit_square, unit_label, unit_label_side).center()
        
        self.play(Create(unit_square))
        self.play(Write(unit_label), Write(unit_label_side))
        self.wait(1)
        
        explanation = Text("Area is the number of 'unit squares'\nthat fit inside a shape.", 
                          font_size=28, t2c={"'unit squares'": YELLOW}).next_to(unit_group, RIGHT, buff=1)
        
        self.play(Write(explanation))
        self.wait(2)
        
        # Cleanup
        self.play(FadeOut(unit_group), FadeOut(explanation), FadeOut(header))

    def rectangle_area(self):
        header = Text("Area of a Rectangle", font_size=36, color=BLUE).to_edge(UP)
        self.play(Write(header))

        # Create a 4x3 rectangle
        rect = Rectangle(width=4, height=3, color=WHITE)
        rect.shift(LEFT * 2)
        
        label_w = MathTex("w = 4", color=GREEN).next_to(rect, DOWN)
        label_h = MathTex("h = 3", color=RED).next_to(rect, LEFT)
        
        self.play(Create(rect))
        self.play(Write(label_w), Write(label_h))
        self.wait(1)

        # Create a grid of unit squares to fill the rectangle
        grid = VGroup()
        for x in range(4):
            for y in range(3):
                s = Square(side_length=1.0, color=YELLOW, fill_opacity=0.3)
                s.move_to(rect.get_corner(DL) + RIGHT * (x + 0.5) + UP * (y + 0.5))
                grid.add(s)

        self.play(LaggedStart(*[FadeIn(s) for s in grid], lag_ratio=0.05))
        
        # Calculation text
        calc = VGroup(
            MathTex(r"\text{Area} = \text{width} \times \text{height}", color=YELLOW),
            MathTex(r"\text{Area} = 4 \times 3"),
            MathTex(r"\text{Area} = 12 \text{ units}^2", color=GREEN)
        ).arrange(DOWN, aligned_edge=LEFT).shift(RIGHT * 3)

        self.play(Write(calc[0]))
        self.wait(1)
        self.play(Write(calc[1]))
        self.play(Write(calc[2]))
        self.play(Indicate(calc[2]))
        self.wait(2)

        # Cleanup
        self.play(FadeOut(rect), FadeOut(grid), FadeOut(label_w), FadeOut(label_h), FadeOut(calc), FadeOut(header))

    def triangle_area(self):
        header = Text("Area of a Triangle", font_size=36, color=BLUE).to_edge(UP)
        self.play(Write(header))

        # Base Rectangle for context
        base_rect = Rectangle(width=4, height=3, color=GRAY, stroke_style=DASHED)
        base_rect.shift(LEFT * 2)
        
        # Points for triangle
        p1 = base_rect.get_corner(DL)
        p2 = base_rect.get_corner(DR)
        p3 = base_rect.get_corner(UR)
        
        triangle = Polygon(p1, p2, p3, color=ORANGE, fill_opacity=0.5)
        
        label_b = MathTex("b", color=GREEN).next_to(base_rect, DOWN)
        label_h = MathTex("h", color=RED).next_to(base_rect, RIGHT)
        
        self.play(Create(base_rect))
        self.play(Write(label_b), Write(label_h))
        self.play(Create(triangle))
        self.wait(1)

        # Show that triangle is half
        explanation = Text("A triangle is exactly half\nof a rectangle.", font_size=28).shift(RIGHT * 3 + UP * 1)
        formula = MathTex(r"\text{Area} = \frac{1}{2} \times b \times h", color=ORANGE).next_to(explanation, DOWN, buff=0.5)

        self.play(Write(explanation))
        self.wait(1)
        self.play(Write(formula))
        self.play(Indicate(formula))
        self.wait(2)

        # Cleanup
        self.play(FadeOut(base_rect), FadeOut(triangle), FadeOut(label_b), FadeOut(label_h), FadeOut(explanation), FadeOut(formula), FadeOut(header))

    def summary_section(self):
        summary_title = Text("Key Concepts", font_size=40, color=BLUE).to_edge(UP)
        
        line1 = Text("• Area measures the interior space of a shape.", font_size=30)
        line2 = Text("• Measured in square units (e.g., m², cm²).", font_size=30)
        line3 = MathTex(r"\text{Rectangle: } A = w \times h", font_size=36, color=YELLOW)
        line4 = MathTex(r"\text{Triangle: } A = \frac{1}{2} \times b \times h", font_size=36, color=ORANGE)
        
        summary_items = VGroup(line1, line2, line3, line4).arrange(DOWN, buff=0.5, aligned_edge=LEFT).center()
        
        self.play(Write(summary_title))
        for item in summary_items:
            self.play(FadeIn(item, shift=RIGHT))
            self.wait(0.5)
            
        self.wait(3)
        
        # Final cleanup
        self.play(FadeOut(VGroup(*self.mobjects)))
        
        thank_you = Text("Happy Learning!", font_size=48, color=WHITE)
        self.play(DrawBorderThenFill(thank_you))
        self.wait(2)
        self.play(FadeOut(thank_you))

---CODE_END---