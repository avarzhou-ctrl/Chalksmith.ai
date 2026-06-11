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


import numpy as np

class CircumferenceLesson(Scene):
    def construct(self):
        # Setup common colors
        self.circumference_color = YELLOW
        self.radius_color = GREEN
        self.diameter_color = RED
        
        self.intro_section()
        self.parts_of_circle()
        self.defining_pi()
        self.formula_derivation()
        self.summary_section()

    def intro_section(self):
        # Title
        title = Text("Understanding Circumference", color=BLUE).scale(1.1)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        self.title_obj = title

        # Define Circumference
        circle = Circle(radius=2, color=WHITE)
        definition = Text("The distance around a circle.", font_size=28).next_to(circle, DOWN, buff=0.5)
        
        self.play(Create(circle))
        self.play(Write(definition))
        self.wait(1)

        # Highlight the perimeter
        highlight = circle.copy().set_color(self.circumference_color).set_stroke(width=8)
        self.play(Create(highlight), run_time=2)
        self.wait(1)
        
        self.play(FadeOut(definition), FadeOut(highlight))
        self.main_circle = circle

    def parts_of_circle(self):
        # Labels for Radius and Diameter
        center_dot = Dot(color=WHITE)
        radius_line = Line(ORIGIN, RIGHT * 2, color=self.radius_color)
        radius_text = MathTex("r", color=self.radius_color).next_to(radius_line, UP, buff=0.1)
        
        diameter_line = Line(LEFT * 2, RIGHT * 2, color=self.diameter_color)
        diameter_text = MathTex("d", color=self.diameter_color).next_to(diameter_line, DOWN, buff=0.1)

        self.play(FadeIn(center_dot))
        self.play(Create(radius_line), Write(radius_text))
        self.wait(1)
        
        # Transform radius to diameter
        self.play(
            ReplacementTransform(radius_line, diameter_line),
            ReplacementTransform(radius_text, diameter_text)
        )
        self.wait(1)
        
        # Explain relationship
        relation = MathTex("d = 2r", color=ORANGE).to_edge(RIGHT, buff=1.5)
        self.play(Write(relation))
        self.wait(2)
        
        # Cleanup
        self.play(FadeOut(center_dot), FadeOut(diameter_line), FadeOut(diameter_text), FadeOut(relation))

    def defining_pi(self):
        # Visualizing the unrolling
        circle = self.main_circle
        
        # Length is 2 * pi * radius (radius is 2)
        c_length = 2 * np.pi * 2
        flat_line = Line(LEFT * (c_length / 2), RIGHT * (c_length / 2), color=self.circumference_color).shift(DOWN * 1.5)
        
        explanation = Text("If we 'unroll' the circle...", font_size=24).to_edge(UP, buff=1.5)
        
        self.play(Write(explanation))
        self.wait(1)

        # Transform circle into a flat line to represent circumference
        self.play(
            circle.animate.become(flat_line),
            run_time=2.5
        )
        
        label_c = MathTex("Circumference (C)", color=self.circumference_color).next_to(circle, UP)
        self.play(Write(label_c))
        self.wait(1)

        # Compare to Diameter
        d_line = Line(LEFT * 2, RIGHT * 2, color=self.diameter_color).next_to(circle, DOWN, buff=0.5)
        d_label = MathTex("d", color=self.diameter_color).next_to(d_line, DOWN)
        
        self.play(Create(d_line), Write(d_label))
        self.wait(1)

        # Illustrate Pi ratio
        pi_formula = MathTex(r"\frac{C}{d} = \pi", color=GOLD).scale(1.2).shift(UP * 0.5)
        pi_approx = MathTex(r"\pi \approx 3.14", color=GOLD).next_to(pi_formula, RIGHT, buff=1)
        
        self.play(Write(pi_formula))
        self.play(Write(pi_approx))
        self.wait(2)

        # Cleanup specific mobjects to clear the scene
        self.play(
            *[FadeOut(m) for m in [circle, label_c, d_line, d_label, explanation, pi_formula, pi_approx, self.title_obj]]
        )

    def formula_derivation(self):
        title = Text("The Formulas", color=BLUE).to_edge(UP)
        self.play(Write(title))

        # Formula 1: C = pi * d
        formula1 = MathTex("C", "=", r"\pi", "d").scale(1.5)
        formula1.set_color_by_tex("C", self.circumference_color)
        formula1.set_color_by_tex("d", self.diameter_color)
        
        self.play(Write(formula1))
        self.wait(1)
        self.play(formula1.animate.shift(UP * 1.2))

        # Formula 2: C = 2 * pi * r
        sub_text = Text("Since d = 2r...", font_size=24).next_to(formula1, DOWN, buff=0.5)
        self.play(Write(sub_text))
        
        formula2 = MathTex("C", "=", "2", r"\pi", "r").scale(1.5)
        formula2.set_color_by_tex("C", self.circumference_color)
        formula2.set_color_by_tex("r", self.radius_color)
        formula2.next_to(sub_text, DOWN, buff=0.5)

        self.play(Write(formula2))
        self.wait(1)

        # Highlight formulas
        box = SurroundingRectangle(VGroup(formula1, formula2), color=WHITE, buff=0.4)
        self.play(Create(box))
        self.wait(2)

        self.play(FadeOut(title), FadeOut(formula1), FadeOut(sub_text), FadeOut(formula2), FadeOut(box))

    def summary_section(self):
        summary_title = Text("Summary", color=BLUE).to_edge(UP)
        
        line1 = Text("• Circumference is the distance around a circle", font_size=28)
        line2 = Text("• The ratio of C to d is always Pi", font_size=28)
        line3 = MathTex("C = \\pi d", color=self.circumference_color).scale(1.2)
        line4 = MathTex("C = 2 \\pi r", color=self.circumference_color).scale(1.2)

        summary_vgroup = VGroup(line1, line2, line3, line4).arrange(DOWN, buff=0.5).center()

        self.play(Write(summary_title))
        for line in summary_vgroup:
            self.play(FadeIn(line, shift=UP*0.3))
            self.wait(0.5)

        self.wait(3)

        # Safe Final Cleanup
        self.play(*[FadeOut(mobj) for mobj in self.mobjects])
        
        thank_you = Text("Geometry: Circumference Complete", color=BLUE).scale(0.8)
        self.play(Write(thank_you))
        self.wait(2)
        self.play(FadeOut(thank_you))