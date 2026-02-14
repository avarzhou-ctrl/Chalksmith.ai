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


import numpy as np

class MainScene(Scene):
    def construct(self):
        # Set up logical sections
        self.introduction()
        self.setup_triangle()
        self.visual_proof()
        self.example_calculation()
        self.conclusion()

    def introduction(self):
        title = Text("The Pythagorean Theorem", font_size=48, color=BLUE)
        subtitle = Text("Relating the sides of a right triangle", font_size=32)
        group = VGroup(title, subtitle).arrange(DOWN)
        
        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(2)
        
        formula = MathTex("a^2 + b^2 = c^2", font_size=72, color=YELLOW)
        formula.next_to(group, DOWN, buff=1)
        
        self.play(Write(formula))
        self.wait(2)
        self.play(FadeOut(group), FadeOut(formula))

    def setup_triangle(self):
        # Define vertices for a 3-4-5 triangle (scaled)
        # Leg a = 1.5, Leg b = 2.0, Hypotenuse c = 2.5
        a_len = 1.5
        b_len = 2.0
        
        p1 = np.array([0, 0, 0])
        p2 = np.array([b_len, 0, 0])
        p3 = np.array([0, a_len, 0])
        
        triangle = Polygon(p1, p2, p3, color=WHITE)
        triangle.set_fill(GRAY, opacity=0.2)
        
        # Right angle symbol
        right_angle = RightAngle(
            Line(p1, p2), Line(p1, p3), 
            length=0.3, quadrant=(1, 1), color=WHITE
        )
        
        # Labels
        label_a = MathTex("a", color=RED).next_to(Line(p1, p3), LEFT, buff=0.2)
        label_b = MathTex("b", color=GREEN).next_to(Line(p1, p2), DOWN, buff=0.2)
        label_c = MathTex("c", color=GOLD).next_to(Line(p3, p2), UR, buff=-0.5).shift(UP*0.3 + RIGHT*0.3)
        
        self.triangle_group = VGroup(triangle, right_angle, label_a, label_b, label_c)
        self.triangle_group.move_to(ORIGIN).shift(LEFT * 1.5 + DOWN * 0.5)
        
        self.play(Create(triangle))
        self.play(Create(right_angle))
        self.play(Write(label_a), Write(label_b), Write(label_c))
        self.wait(2)
        
        self.p1, self.p2, self.p3 = p1, p2, p3 # Local refs for squares
        self.a_len, self.b_len = a_len, b_len

    def visual_proof(self):
        # Square on side a (vertical leg)
        sq_a = Square(side_length=self.a_len)
        sq_a.set_stroke(RED, opacity=1)
        sq_a.set_fill(RED, opacity=0.4)
        sq_a.next_to(self.triangle_group[0], LEFT, buff=0)
        sq_a.align_to(self.triangle_group[0], DOWN)
        
        # Square on side b (horizontal leg)
        sq_b = Square(side_length=self.b_len)
        sq_b.set_stroke(GREEN, opacity=1)
        sq_b.set_fill(GREEN, opacity=0.4)
        sq_b.next_to(self.triangle_group[0], DOWN, buff=0)
        sq_b.align_to(self.triangle_group[0], LEFT)
        
        # Square on side c (hypotenuse)
        hypot_len = np.sqrt(self.a_len**2 + self.b_len**2)
        sq_c = Square(side_length=hypot_len)
        sq_c.set_stroke(GOLD, opacity=1)
        sq_c.set_fill(GOLD, opacity=0.4)
        
        # Calculate rotation for square c
        angle = np.arctan2(self.p3[1] - self.p2[1], self.p3[0] - self.p2[0])
        sq_c.rotate(angle + np.pi/2)
        
        # Position square c on the hypotenuse
        # Midpoint of hypotenuse
        mid_hypot = (self.triangle_group[0].get_vertices()[1] + self.triangle_group[0].get_vertices()[2]) / 2
        # Normal vector to hypotenuse
        v_hypot = self.triangle_group[0].get_vertices()[2] - self.triangle_group[0].get_vertices()[1]
        normal = np.array([-v_hypot[1], v_hypot[0], 0])
        normal = normal / np.linalg.norm(normal)
        sq_c.move_to(mid_hypot + normal * (hypot_len / 2))
        
        # Labels for areas
        area_a = MathTex("a^2", color=RED).move_to(sq_a.get_center())
        area_b = MathTex("b^2", color=GREEN).move_to(sq_b.get_center())
        area_c = MathTex("c^2", color=GOLD).move_to(sq_c.get_center())
        
        self.play(FadeIn(sq_a), Write(area_a))
        self.wait(0.5)
        self.play(FadeIn(sq_b), Write(area_b))
        self.wait(0.5)
        self.play(FadeIn(sq_c), Write(area_c))
        self.wait(2)
        
        # Relationship text
        relationship = MathTex(
            "\\text{Area } a^2 + \\text{Area } b^2 = \\text{Area } c^2",
            font_size=36
        ).to_edge(UP, buff=0.5)
        
        self.play(Write(relationship))
        self.wait(2)
        
        # Clean up for example
        self.play(
            FadeOut(sq_a), FadeOut(sq_b), FadeOut(sq_c),
            FadeOut(area_a), FadeOut(area_b), FadeOut(area_c),
            FadeOut(relationship)
        )

    def example_calculation(self):
        # Shift triangle to side
        self.play(self.triangle_group.animate.to_edge(LEFT, buff=1.5))
        
        # Example values
        val_a = MathTex("a = 3", color=RED)
        val_b = MathTex("b = 4", color=GREEN)
        val_c = MathTex("c = ?", color=GOLD)
        
        vals = VGroup(val_a, val_b, val_c).arrange(DOWN, aligned_edge=LEFT)
        vals.to_edge(RIGHT, buff=2).shift(UP * 1.5)
        
        self.play(Write(vals))
        self.wait(1)
        
        # Steps
        step1 = MathTex("3^2 + 4^2 = c^2")
        step2 = MathTex("9 + 16 = c^2")
        step3 = MathTex("25 = c^2")
        step4 = MathTex("\\sqrt{25} = c")
        step5 = MathTex("5 = c", color=GOLD)
        
        steps = VGroup(step1, step2, step3, step4, step5).arrange(DOWN)
        steps.next_to(vals, DOWN, buff=0.5).align_to(vals, LEFT)
        
        for step in steps:
            self.play(Write(step))
            self.wait(0.8)
            
        self.wait(2)
        
        # Clear screen
        self.play(FadeOut(self.triangle_group), FadeOut(vals), FadeOut(steps))

    def conclusion(self):
        final_text = Text("The Pythagorean Theorem is fundamental", font_size=36)
        final_text2 = Text("to geometry and trigonometry.", font_size=36)
        summary = VGroup(final_text, final_text2).arrange(DOWN)
        
        box = SurroundingRectangle(summary, color=YELLOW, buff=0.5)
        
        self.play(Write(summary))
        self.play(Create(box))
        self.wait(3)
        self.play(FadeOut(summary), FadeOut(box))
        
        end_screen = Text("Thank You!", font_size=60, color=BLUE)
        self.play(DrawBorderThenFill(end_screen))
        self.wait(2)