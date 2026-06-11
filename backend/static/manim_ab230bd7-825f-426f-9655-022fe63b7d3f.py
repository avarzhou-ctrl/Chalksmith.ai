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
        self.radius_diameter_section()
        self.circumference_definition()
        self.rolling_demo_section()
        self.formula_summary()

    def intro_section(self):
        title = Text("Understanding Circumference", color=BLUE)
        self.play(Write(title))
        self.wait(1.5)
        self.play(FadeOut(title))

    def radius_diameter_section(self):
        # Create Circle
        circle = Circle(radius=2, color=WHITE)
        center_dot = Dot(color=YELLOW)
        
        # Show Radius
        radius_line = Line(ORIGIN, [2, 0, 0], color=BLUE)
        r_label = MathTex("r", color=BLUE).next_to(radius_line, UP)
        radius_text = Text("Radius (r): Center to Edge", font_size=24).to_edge(UP)
        
        self.play(Create(circle), FadeIn(center_dot))
        self.play(Create(radius_line), Write(r_label), Write(radius_text))
        self.wait(1.5)
        
        # Show Diameter
        diameter_line = Line([-2, 0, 0], [2, 0, 0], color=RED)
        d_label = MathTex("d = 2r", color=RED).next_to(diameter_line, DOWN)
        diameter_text = Text("Diameter (d): Across the center", font_size=24).to_edge(UP)
        
        self.play(
            Transform(radius_text, diameter_text),
            Create(diameter_line),
            Write(d_label),
            radius_line.animate.set_opacity(0),
            r_label.animate.set_opacity(0)
        )
        self.wait(2)
        
        # Cleanup
        self.play(FadeOut(radius_text), FadeOut(diameter_line), FadeOut(d_label), FadeOut(center_dot))
        self.circle = circle # Keep for next section

    def circumference_definition(self):
        circle = self.circle
        
        # Define Circumference
        circ_text = Text("Circumference (C): The distance around the circle", font_size=28).to_edge(UP)
        
        # Highlight boundary
        highlight_circle = circle.copy().set_color(YELLOW).set_stroke(width=8)
        
        self.play(Write(circ_text))
        self.play(Create(highlight_circle), run_time=2)
        self.wait(1)
        self.play(FadeOut(highlight_circle))
        
        # Transition to rolling
        self.play(
            circle.animate.scale(0.5).to_edge(LEFT).shift(UP*1),
            circ_text.animate.shift(UP*0.5)
        )
        self.circle_small = circle
        self.circ_text = circ_text

    def rolling_demo_section(self):
        circle = self.circle_small
        radius = circle.radius
        circumference_len = 2 * np.pi * radius
        
        # Ground line
        start_point = circle.get_bottom()
        ground = Line(start_point, start_point + RIGHT * circumference_len, color=GRAY)
        
        # A marker on the circle to see it rotate
        marker = Line(circle.get_center(), circle.get_bottom(), color=RED)
        rolling_group = VGroup(circle, marker)
        
        self.play(Create(ground))
        self.wait(0.5)
        
        # Path trace (the unrolled circumference)
        path = Line(start_point, start_point, color=YELLOW, stroke_width=6)
        
        def update_path(obj):
            current_bottom = circle.get_bottom()
            obj.put_start_and_end_on(start_point, [current_bottom[0], start_point[1], 0])

        path.add_updater(update_path)
        self.add(path)
        
        # Rolling animation
        # Distance = circumference, Rotation = 360 degrees (2*pi)
        self.play(
            rolling_group.animate.shift(RIGHT * circumference_len),
            Rotate(rolling_group, angle=-2 * np.pi, about_point=rolling_group.get_center()),
            run_time=4,
            rate_func=linear
        )
        path.remove_updater(update_path)
        self.wait(1)
        
        # Label the length
        brace = Brace(path, DOWN)
        brace_text = MathTex("C = \pi \cdot d", color=YELLOW).next_to(brace, DOWN)
        
        self.play(Create(brace), Write(brace_text))
        self.wait(2)
        
        # Clear section
        self.play(FadeOut(VGroup(rolling_group, ground, path, brace, brace_text, self.circ_text)))

    def formula_summary(self):
        title = Text("The Formulas", color=BLUE).to_edge(UP)
        
        formula1 = MathTex("C", "=", "\\pi", "d")
        formula1.set_color_by_tex("C", YELLOW)
        formula1.set_color_by_tex("d", RED)
        
        formula2 = MathTex("C", "=", "2", "\\pi", "r")
        formula2.set_color_by_tex("C", YELLOW)
        formula2.set_color_by_tex("r", BLUE)
        
        vgroup = VGroup(formula1, formula2).arrange(DOWN, buff=1)
        
        label1 = Text("Using Diameter:", font_size=24).next_to(formula1, LEFT, buff=1)
        label2 = Text("Using Radius:", font_size=24).next_to(formula2, LEFT, buff=1)
        
        pi_note = MathTex("\\pi \\approx 3.14159", color=PURPLE).next_to(vgroup, DOWN, buff=1)
        
        self.play(Write(title))
        self.play(FadeIn(label1), Write(formula1))
        self.wait(0.5)
        self.play(FadeIn(label2), Write(formula2))
        self.wait(1)
        self.play(Write(pi_note))
        self.play(Indicate(pi_note))
        
        self.wait(3)
        
        # Final cleanup
        self.play(FadeOut(VGroup(*self.mobjects)))
        
        final_text = Text("Mathematics of Circles", color=BLUE).scale(1.2)
        self.play(Write(final_text))
        self.wait(1)
        self.play(FadeOut(final_text))