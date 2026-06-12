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
        self.show_intro()
        self.show_reflection()
        self.show_refraction()
        self.show_summary()

    def show_intro(self):
        title = Text("Reflection and Refraction", font_size=40, color=GOLD)
        subtitle = Text("The Physics of Light Boundaries", font_size=24, color=WHITE)
        subtitle.next_to(title, DOWN, buff=0.5)
        
        intro_grp = VGroup(title, subtitle).center()
        self.play(FadeIn(intro_grp))
        self.wait(2)
        self.play(FadeOut(intro_grp))
        self.wait(0.5)

    def show_reflection(self):
        # Header text elements to avoid clutter
        law_title = Text("Law of Reflection", font_size=28, color=GOLD).to_edge(UP, buff=0.5)
        law_desc = Text("The angle of incidence equals the angle of reflection.", font_size=18).next_to(law_title, DOWN, buff=0.2)
        law_eq = MathTex(r"\theta_i = \theta_r", font_size=36, color=YELLOW).next_to(law_desc, DOWN, buff=0.2)
        
        self.play(Write(law_title))
        self.play(Write(law_desc))
        self.wait(1)

        # Diagram elements (y limits: -2.0 to 1.0)
        mirror_y = -1.5
        mirror = Line(start=[-4, mirror_y, 0], end=[4, mirror_y, 0], color=GRAY, stroke_width=6)
        mirror_label = Text("Reflective Surface (Mirror)", font_size=16, color=GRAY).next_to(mirror, DOWN, buff=0.2)
        
        normal = DashedLine(start=[0, mirror_y, 0], end=[0, 1.0, 0], color=WHITE)
        normal_label = Text("Normal", font_size=16, color=WHITE).next_to(normal, UP, buff=0.1)

        # Rays
        incident_ray = Arrow(start=[-2.5, 1.0, 0], end=[0, mirror_y, 0], color=YELLOW, buff=0)
        reflected_ray = Arrow(start=[0, mirror_y, 0], end=[2.5, 1.0, 0], color=YELLOW, buff=0)

        inc_label = Text("Incident Ray", font_size=16, color=YELLOW).next_to(incident_ray, UL, buff=0.1).shift(RIGHT * 0.5)
        ref_label = Text("Reflected Ray", font_size=16, color=YELLOW).next_to(reflected_ray, UR, buff=0.1).shift(LEFT * 0.5)

        # Angles
        arc_i = Arc(radius=0.6, start_angle=np.pi/2, angle=np.pi/4, arc_center=[0, mirror_y, 0], color=RED)
        label_theta_i = MathTex(r"\theta_i", font_size=24, color=RED).move_to([-0.3, -0.7, 0])

        arc_r = Arc(radius=0.6, start_angle=np.pi/4, angle=np.pi/4, arc_center=[0, mirror_y, 0], color=GREEN)
        label_theta_r = MathTex(r"\theta_r", font_size=24, color=GREEN).move_to([0.3, -0.7, 0])

        # Animations sequence
        self.play(Create(mirror), FadeIn(mirror_label))
        self.play(Create(normal), FadeIn(normal_label))
        self.wait(0.5)

        self.play(Create(incident_ray), FadeIn(inc_label))
        self.play(Create(arc_i), Write(label_theta_i))
        self.wait(0.5)

        self.play(Create(reflected_ray), FadeIn(ref_label))
        self.play(Create(arc_r), Write(label_theta_r))
        self.wait(1)

        self.play(Write(law_eq))
        self.play(Circumscribe(law_eq, color=GOLD))
        self.wait(2)

        # Clean up scene transition safely
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.5)

    def show_refraction(self):
        # Header elements
        refr_title = Text("Refraction & Snell's Law", font_size=28, color=GOLD).to_edge(UP, buff=0.5)
        refr_desc = Text("Light bends when transitioning between media of different optical densities.", font_size=16).next_to(refr_title, DOWN, buff=0.2)
        snell_eq = MathTex(r"n_1 \sin\theta_1 = n_2 \sin\theta_2", font_size=36, color=YELLOW).next_to(refr_desc, DOWN, buff=0.2)

        self.play(Write(refr_title))
        self.play(Write(refr_desc))
        self.wait(1)

        # Media boundary setup (y = -1.0)
        boundary_y = -1.0
        
        # Transparent medium below boundary
        glass = Rectangle(width=14, height=3, fill_color=BLUE, fill_opacity=0.2, stroke_width=0).move_to([0, -2.5, 0])
        interface = Line(start=[-7, boundary_y, 0], end=[7, boundary_y, 0], color=WHITE, stroke_width=2)
        
        normal2 = DashedLine(start=[0, -2.5, 0], end=[0, 1.0, 0], color=GRAY)
        normal2_label = Text("Normal", font_size=14, color=GRAY).next_to(normal2, UP, buff=0.1)

        m1_label = Text("Medium 1: Air (n₁ = 1.0)", font_size=14, color=WHITE).move_to([-4, 0.5, 0])
        m2_label = Text("Medium 2: Glass (n₂ = 1.5)", font_size=14, color=BLUE).move_to([-4, -2.0, 0])

        # Incident Ray (45 degrees)
        incident_ray2 = Arrow(start=[-2.0, 1.0, 0], end=[0, boundary_y, 0], color=YELLOW, buff=0)
        inc_label2 = Text("Incident Ray", font_size=14, color=YELLOW).next_to(incident_ray2, UL, buff=0.1).shift(RIGHT * 0.4)

        # Refracted Ray (Bends toward the normal, theta2 ~ 28.1 degrees)
        refracted_ray = Arrow(start=[0, boundary_y, 0], end=[0.8, -2.5, 0], color=YELLOW, buff=0)
        ref_label2 = Text("Refracted Ray", font_size=14, color=YELLOW).next_to(refracted_ray, DR, buff=0.1).shift(UP * 0.3)

        # Angles
        arc_theta1 = Arc(radius=0.5, start_angle=np.pi/2, angle=np.pi/4, arc_center=[0, boundary_y, 0], color=RED)
        label_theta1 = MathTex(r"\theta_1", font_size=20, color=RED).move_to([-0.25, -0.4, 0])

        # Angle theta2 (from -90 deg to -61.9 deg)
        arc_theta2 = Arc(radius=0.6, start_angle=-np.pi/2, angle=28.1 * np.pi / 180, arc_center=[0, boundary_y, 0], color=GREEN)
        label_theta2 = MathTex(r"\theta_2", font_size=20, color=GREEN).move_to([0.25, -1.7, 0])

        # Animations sequence
        self.play(FadeIn(glass), Create(interface))
        self.play(Create(normal2), FadeIn(normal2_label))
        self.play(FadeIn(m1_label), FadeIn(m2_label))
        self.wait(0.5)

        self.play(Create(incident_ray2), FadeIn(inc_label2))
        self.play(Create(arc_theta1), Write(label_theta1))
        self.wait(0.5)

        self.play(Create(refracted_ray), FadeIn(ref_label2))
        self.play(Create(arc_theta2), Write(label_theta2))
        self.wait(1)

        self.play(Write(snell_eq))
        self.play(Circumscribe(snell_eq, color=GOLD))
        self.wait(2.5)

        # Clean up scene transition safely
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.5)

    def show_summary(self):
        summary_title = Text("Key Takeaways", font_size=32, color=GOLD).to_edge(UP, buff=0.8)
        
        bullet1 = Text("1. Reflection: Light bounces off at the exact same angle relative to the normal.", font_size=18)
        bullet2 = Text("2. Refraction: Light bends when crossing into a medium with a different optical density.", font_size=18)
        bullet3 = Text("3. Snell's Law mathematically models refraction using refractive indices (n).", font_size=18)
        
        bullets = VGroup(bullet1, bullet2, bullet3).arrange(DOWN, aligned_edge=LEFT, buff=0.5).next_to(summary_title, DOWN, buff=1.0)
        
        self.play(Write(summary_title))
        self.wait(0.5)
        for bullet in bullets:
            self.play(FadeIn(bullet, shift=RIGHT * 0.2))
            self.wait(1)
            
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(1)