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
        self.intro()
        self.rectangle_area()
        self.parallelogram_area()
        self.trapezoid_area()
        self.rhombus_kite_area()
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

        self.play(FadeOut(rect), FadeOut(base_label), FadeOut(height_label), FadeOut(formula), FadeOut(header))

    def parallelogram_area(self):
        header = Text("2. The Parallelogram", color=GREEN).to_edge(UP)
        self.play(Write(header))

        # Define points for a parallelogram
        p1 = [-2, -1, 0]
        p2 = [2, -1, 0]
        p3 = [3, 1, 0]
        p4 = [-1, 1, 0]
        
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

        # Create the triangle that will move
        tri_pts = [[-2, -1, 0], [-1, -1, 0], [-1, 1, 0]]
        moving_tri = Polygon(*tri_pts, color=GREEN, stroke_width=0)
        moving_tri.set_fill(GREEN, opacity=0.8)
        
        self.play(FadeIn(moving_tri))
        # Move it to the other side to form a rectangle
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

        # Base 1 = 2, Base 2 = 4
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

        expl = Text("Double it and rotate", font_size=24).to_edge(RIGHT).shift(UP*0.5)
        self.play(Write(expl))

        trap2 = trap1.copy()
        # Rotate and position next to the first one to form a parallelogram
        self.play(
            trap2.animate.rotate(PI).move_to([1, 0, 0]),
            run_time=2
        )
        self.wait(1)

        self.play(FadeOut(expl), FadeOut(b1), FadeOut(b2))

        # Show the combined base
        total_base = MathTex("b_1 + b_2").shift(DOWN * 2)
        brace = BraceBetweenPoints([-2, -1.2, 0], [4, -1.2, 0], DOWN)
        
        self.play(Create(brace), Write(total_base))
        
        full_formula = MathTex("2 \\times Area = (b_1 + b_2)h", color=ORANGE).shift(UP * 2)
        final_formula = MathTex("Area = \\frac{1}{2}(b_1 + b_2)h", color=YELLOW).next_to(full_formula, DOWN)

        self.play(Write(full_formula))
        self.wait(1)
        self.play(Write(final_formula))
        self.play(Circumscribe(final_formula))
        self.wait(2)

        self.play(FadeOut(*self.mobjects))

    def rhombus_kite_area(self):
        header = Text("4. Rhombus & Kite", color=MAGENTA).to_edge(UP)
        self.play(Write(header))

        rho_pts = [[0, 1.5, 0], [2, 0, 0], [0, -1.5, 0], [-2, 0, 0]]
        rhombus = Polygon(*rho_pts, color=WHITE)
        rhombus.set_fill(MAGENTA, opacity=0.3)
        
        d1_line = DashedLine([-2, 0, 0], [2, 0, 0], color=CYAN)
        d2_line = DashedLine([0, 1.5, 0], [0, -1.5, 0], color=YELLOW)
        
        d1_text = MathTex("d_1", color=CYAN).next_to(d1_line, UP, buff=0.1)
        d2_text = MathTex("d_2", color=YELLOW).next_to(d2_line, RIGHT, buff=0.1)

        self.play(Create(rhombus))
        self.play(Create(d1_line), Write(d1_text))
        self.play(Create(d2_line), Write(d2_text))
        self.wait(1)

        expl = Text("Fits inside a rectangle", font_size=24).to_edge(RIGHT).shift(UP)
        self.play(Write(expl))

        # Bounding box
        rect = Rectangle(width=4, height=3, color=WHITE, stroke_opacity=0.5)
        self.play(Create(rect))
        self.wait(1)

        formula = MathTex("Area = \\frac{1}{2} d_1 d_2", color=MAGENTA).shift(DOWN * 2.5)
        self.play(Write(formula))
        self.play(Indicate(formula))
        self.wait(2)

        self.play(FadeOut(*self.mobjects))

    def outro(self):
        summary_title = Text("Summary of Formulas", color=BLUE).shift(UP * 2.5)
        
        line1 = MathTex(r"\text{Rectangle/Parallelogram: } b \times h", font_size=36).shift(UP * 1.0)
        line2 = MathTex(r"\text{Trapezoid: } \frac{1}{2} (b_1 + b_2)h", font_size=36).next_to(line1, DOWN, buff=0.5)
        line3 = MathTex(r"\text{Rhombus/Kite: } \frac{1}{2} d_1 d_2", font_size=36).next_to(line2, DOWN, buff=0.5)
        
        thanks = Text("Geometry is visual!", font_size=36, color=GOLD).shift(DOWN * 2.5)

        self.play(Write(summary_title))
        self.play(FadeIn(line1), FadeIn(line2), FadeIn(line3))
        self.wait(1)
        self.play(Write(thanks))
        self.wait(3)
        
        self.play(FadeOut(*self.mobjects))