from manim import *

# Compatibility layer for common color/class hallucinations
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

# Legacy Compatibility
TextMobject = Text
TexMobject = Tex
ShowCreation = Create

class MainScene(Scene):
    def construct(self):
        self.intro()
        self.rectangle_area()
        self.parallelogram_area()
        self.trapezoid_area()
        self.outro()

    def intro(self):
        title = Text("Area of Quadrilaterals", font_size=48, color=BLUE)
        subtitle = Text("Understanding formulas through geometry", font_size=32, color=GRAY)
        VGroup(title, subtitle).arrange(DOWN)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))

    def rectangle_area(self):
        header = Text("1. The Rectangle", color=YELLOW).to_edge(UP)
        self.play(Write(header))

        rect = Rectangle(width=4, height=3, color=WHITE)
        rect.set_fill(BLUE, opacity=0.3)
        
        base_label = MathTex("b").next_to(rect, DOWN)
        height_label = MathTex("h").next_to(rect, LEFT)
        formula = MathTex("Area = b \\times h", color=YELLOW).shift(UP * 2.5)

        self.play(Create(rect))
        self.play(Write(base_label), Write(height_label))
        self.wait(1)
        self.play(Write(formula))
        self.wait(2)

        self.play(FadeOut(*self.mobjects))

    def parallelogram_area(self):
        header = Text("2. The Parallelogram", color=GREEN).to_edge(UP)
        self.play(Write(header))

        # Points: b=4, h=2
        p1, p2, p3, p4 = [-2, -1, 0], [2, -1, 0], [3, 1, 0], [-1, 1, 0]
        para = Polygon(p1, p2, p3, p4, color=WHITE)
        para.set_fill(GREEN, opacity=0.3)
        
        base_line = Line([-2, -1.2, 0], [2, -1.2, 0], color=GRAY)
        base_text = MathTex("b").next_to(base_line, DOWN)
        
        height_dashed = DashedLine([-1, 1, 0], [-1, -1, 0], color=RED)
        height_text = MathTex("h", color=RED).next_to(height_dashed, LEFT)

        self.play(Create(para))
        self.play(Create(base_line), Write(base_text))
        self.wait(1)
        self.play(Create(height_dashed), Write(height_text))
        self.wait(1)

        expl = Text("Cut and move the triangle", font_size=24).to_edge(RIGHT).shift(UP)
        self.play(Write(expl))

        # Create the triangle at the left
        tri_pts = [[-2, -1, 0], [-1, -1, 0], [-1, 1, 0]]
        moving_tri = Polygon(*tri_pts, color=GREEN)
        moving_tri.set_fill(GREEN, opacity=0.8)
        
        self.play(FadeIn(moving_tri))
        # Moving from x=-2 to x=2 (base length = 4)
        self.play(moving_tri.animate.shift(RIGHT * 4))
        self.wait(1)

        formula = MathTex("Area = b \\times h", color=GREEN).shift(DOWN * 2.5)
        self.play(Write(formula))
        self.play(Indicate(formula))
        self.wait(2)

        self.play(FadeOut(*self.mobjects))

    def trapezoid_area(self):
        header = Text("3. The Trapezoid", color=ORANGE).to_edge(UP)
        self.play(Write(header))

        # Trapezoid coordinates: b1=2, b2=4, h=2
        t_pts = [[-2, -1, 0], [2, -1, 0], [1, 1, 0], [-1, 1, 0]]
        trap1 = Polygon(*t_pts, color=WHITE)
        trap1.set_fill(ORANGE, opacity=0.4)

        b1 = MathTex("b_1").next_to(trap1, UP)
        b2 = MathTex("b_2").next_to(trap1, DOWN)
        h_line = DashedLine([-1, 1, 0], [-1, -1, 0], color=RED)
        h_text = MathTex("h", color=RED).next_to(h_line, LEFT)

        self.play(Create(trap1))
        self.play(Write(b1), Write(b2), Create(h_line), Write(h_text))
        self.wait(1)

        expl = Text("Double it and rotate", font_size=24).to_edge(RIGHT).shift(UP)
        self.play(Write(expl))

        trap2 = trap1.copy()
        self.play(trap2.animate.shift(RIGHT * 4))
        self.play(trap2.animate.rotate(PI))
        
        # Calculation for alignment:
        # trap1 right edge is at x=2(bottom) and x=1(top).
        # rotated trap2 left edge is at x=-1(bottom) and x=-2(top).
        # To align, shift trap2 by RIGHT * 3
        self.play(trap2.animate.move_to(ORIGIN).shift(RIGHT * 1.5))
        self.play(trap1.animate.shift(LEFT * 1.5))
        # Re-position labels relative to new location
        self.play(FadeOut(b1), FadeOut(b2), FadeOut(h_text), FadeOut(h_line))

        # Combined Shape Labels
        brace = BraceBetweenPoints([-3.5, -1.5, 0], [2.5, -1.5, 0], DOWN)
        total_base = MathTex("b_1 + b_2").next_to(brace, DOWN)
        
        self.play(Create(brace), Write(total_base))
        
        full_formula = MathTex("2 \\times Area = (b_1 + b_2)h", color=ORANGE).shift(UP * 2.5)
        final_formula = MathTex("Area = \\frac{1}{2}(b_1 + b_2)h", color=YELLOW).next_to(full_formula, DOWN)

        self.play(Write(full_formula))
        self.wait(1)
        self.play(Write(final_formula))
        self.play(Circumscribe(final_formula))
        self.wait(3)

        self.play(FadeOut(*self.mobjects))

    def outro(self):
        summary_title = Text("Summary", color=BLUE).shift(UP * 2)
        
        line1 = Text("- Rectangle: b x h", font_size=30).shift(UP * 0.5)
        line2 = Text("- Parallelogram: b x h", font_size=30).next_to(line1, DOWN)
        line3 = Text("- Trapezoid: 1/2 (b1 + b2) x h", font_size=30).next_to(line2, DOWN)
        
        thanks = Text("Geometry is visual!", font_size=36, color=GOLD).shift(DOWN * 2)

        self.play(Write(summary_title))
        self.play(FadeIn(line1), FadeIn(line2), FadeIn(line3))
        self.wait(1)
        self.play(Write(thanks))
        self.wait(3)
        
        self.play(FadeOut(*self.mobjects))