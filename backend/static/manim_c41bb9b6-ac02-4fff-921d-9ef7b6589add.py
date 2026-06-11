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

class MainScene(Scene):
    def construct(self):
        self.intro_section()
        self.parts_of_circle()
        self.defining_pi()
        self.formula_derivation()
        self.summary_section()

    def intro_section(self):
        # Title
        title = Text("Understanding Circumference", color=BLUE).scale(1.2)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))

        # Define Circumference
        self.circle = Circle(radius=2, color=WHITE)
        definition = Text("The distance around a circle.", font_size=24).next_to(self.circle, DOWN)
        
        self.play(Create(self.circle))
        self.play(Write(definition))
        self.wait(1)

        # Highlight the perimeter
        highlight = self.circle.copy().set_color(YELLOW).set_stroke(width=8)
        self.play(Create(highlight), run_time=2)
        self.wait(1)
        
        self.play(FadeOut(definition), FadeOut(highlight))

    def parts_of_circle(self):
        # Labels for Radius and Diameter
        center_dot = Dot(color=WHITE)
        radius_line = Line(ORIGIN, RIGHT * 2, color=GREEN)
        radius_text = MathTex("r", color=GREEN).next_to(radius_line, UP, buff=0.1)
        
        diameter_line = Line(LEFT * 2, RIGHT * 2, color=RED)
        diameter_text = MathTex("d", color=RED).next_to(diameter_line, DOWN, buff=0.1)

        self.play(FadeIn(center_dot))
        self.play(Create(radius_line), Write(radius_text))
        self.wait(1)
        
        self.play(
            ReplacementTransform(radius_line, diameter_line),
            ReplacementTransform(radius_text, diameter_text)
        )
        self.wait(1)
        
        # Explain relationship
        relation = MathTex("d = 2r", color=ORANGE).to_edge(RIGHT, buff=1)
        self.play(Write(relation))
        self.wait(2)
        
        # Cleanup
        self.play(FadeOut(center_dot), FadeOut(diameter_line), FadeOut(diameter_text), FadeOut(relation))

    def defining_pi(self):
        # Visualizing the unrolling
        circle = self.circle
        
        # Create a line equal to the circumference length (2 * pi * radius)
        # Radius is 2, so C = 4 * pi
        c_length = 4 * np.pi
        flat_line = Line(LEFT * (c_length / 2), RIGHT * (c_length / 2), color=YELLOW).shift(DOWN * 2)
        
        explanation = Text("If we 'unroll' the circle...", font_size=24).to_edge(UP).shift(DOWN)
        
        self.play(Write(explanation))
        self.wait(1)

        # Transform circle into a flat line
        self.play(
            ReplacementTransform(circle, flat_line),
            run_time=3
        )
        
        label_c = MathTex(r"\text{Circumference } (C)", color=YELLOW).next_to(flat_line, UP)
        self.play(Write(label_c))
        self.wait(1)

        # Compare to Diameter
        # Diameter is 4
        d_line = Line(LEFT * 2, RIGHT * 2, color=RED).next_to(flat_line, DOWN, buff=0.5)
        d_label = MathTex("d", color=RED).next_to(d_line, DOWN)
        
        self.play(Create(d_line), Write(d_label))
        self.wait(1)

        # Show how many diameters fit in C
        # We'll create three full diameters and one small piece
        d_starts = [flat_line.get_left() + RIGHT * (i * 4) for i in range(3)]
        diameters_in_c = VGroup(*[
            Line(start, start + RIGHT * 4, color=PURPLE, stroke_width=6)
            for start in d_starts
        ])
        
        for d_seg in diameters_in_c:
            self.play(Create(d_seg), run_time=0.8)
        
        pi_text = MathTex(r"\pi \approx 3.14", color=GOLD).shift(UP * 1)
        ratio_text = MathTex(r"\frac{C}{d} = \pi").next_to(pi_text, DOWN)
        
        self.play(Write(pi_text))
        self.play(Write(ratio_text))
        self.wait(2)

        # Cleanup
        self.play(
            FadeOut(flat_line), FadeOut(label_c),
            FadeOut(d_line), FadeOut(d_label), FadeOut(diameters_in_c),
            FadeOut(explanation), FadeOut(pi_text), FadeOut(ratio_text)
        )

    def formula_derivation(self):
        title = Text("The Formulas", color=BLUE).to_edge(UP)
        self.play(Write(title))

        # Formula 1: Using Diameter
        formula1 = MathTex("C", "=", r"\pi", "d").scale(1.5)
        formula1.set_color_by_tex("C", YELLOW)
        formula1.set_color_by_tex("d", RED)
        
        self.play(Write(formula1))
        self.wait(1)
        self.play(formula1.animate.shift(UP * 1))

        # Formula 2: Using Radius
        sub_text = Text("Since d = 2r...", font_size=24).next_to(formula1, DOWN, buff=0.5)
        self.play(Write(sub_text))
        self.wait(1)

        formula2 = MathTex("C", "=", "2", r"\pi", "r").scale(1.5)
        formula2.set_color_by_tex("C", YELLOW)
        formula2.set_color_by_tex("r", GREEN)
        formula2.next_to(sub_text, DOWN, buff=0.5)

        self.play(Write(formula2))
        self.wait(2)

        # Visual box
        box = SurroundingRectangle(VGroup(formula1, formula2), color=WHITE, buff=0.4)
        self.play(Create(box))
        self.wait(2)

        self.play(FadeOut(title), FadeOut(formula1), FadeOut(sub_text), FadeOut(formula2), FadeOut(box))

    def summary_section(self):
        summary_title = Text("Summary", color=BLUE).to_edge(UP)
        
        line1 = Text("1. Circumference is the perimeter of a circle.", font_size=28)
        line2 = Text("2. The ratio C / d is always equal to Pi (3.14...).", font_size=28)
        line3 = MathTex("C = \\pi d", color=YELLOW).scale(1.2)
        line4 = MathTex("C = 2 \\pi r", color=YELLOW).scale(1.2)

        lines = VGroup(line1, line2, line3, line4).arrange(DOWN, buff=0.4).center()

        self.play(Write(summary_title))
        for line in lines:
            self.play(FadeIn(line, shift=UP*0.2))
            self.wait(1)

        self.wait(2)

        # Final Cleanup - Using a list comprehension to avoid VGroup non-VMobject issues
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        
        thank_you = Text("Geometry Basics: Circumference", color=BLUE).scale(0.8)
        self.play(Write(thank_you))
        self.wait(2)
        self.play(FadeOut(thank_you))