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
        # 1. Introduction
        self.intro_section()
        self.clear_screen()

        # 2. Geometric Setup
        self.triangle_section()
        
        # 3. Area Visualization
        self.area_visualization()
        self.clear_screen()

        # 4. Mathematical Verification
        self.math_proof_section()
        
        # 5. Outro
        self.outro_section()

    def intro_section(self):
        title = Text("The Pythagorean Theorem", font_size=48, color=GOLD)
        subtitle = Text("A fundamental relation in geometry", font_size=32)
        subtitle.next_to(title, DOWN)
        
        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))

    def triangle_section(self):
        # Define vertices for a 3-4-5 triangle
        # B is the right angle
        a_pt = np.array([-1.5, 1.0, 0])
        b_pt = np.array([-1.5, -2.0, 0])
        c_pt = np.array([2.5, -2.0, 0])

        triangle = Polygon(a_pt, b_pt, c_pt, color=WHITE, stroke_width=4)
        
        # Right angle symbol
        l1 = Line(b_pt, a_pt)
        l2 = Line(b_pt, c_pt)
        ra = RightAngle(l1, l2, length=0.3, color=YELLOW)

        # Labels
        label_a = MathTex("a", color=GREEN).next_to(Line(a_pt, b_pt), LEFT, buff=0.2)
        label_b = MathTex("b", color=BLUE).next_to(Line(b_pt, c_pt), DOWN, buff=0.2)
        label_c = MathTex("c", color=RED).shift(np.array([0.7, -0.2, 0]))

        # Explanation text
        explanation = Text("In a right-angled triangle:", font_size=28).to_edge(UP)
        formula = MathTex("a^2 + b^2 = c^2", font_size=48).to_edge(RIGHT, buff=1).shift(UP * 0.5)

        self.play(Write(explanation))
        self.play(Create(triangle), run_time=2)
        self.play(Create(ra))
        self.wait(0.5)
        self.play(Write(label_a), Write(label_b), Write(label_c))
        self.wait(1)
        self.play(Write(formula))
        self.wait(2)

        # Store for next section
        self.triangle_group = VGroup(triangle, ra, label_a, label_b, label_c, formula, explanation)

    def area_visualization(self):
        # Vertices again for squares
        a_pt = np.array([-1.5, 1.0, 0])
        b_pt = np.array([-1.5, -2.0, 0])
        c_pt = np.array([2.5, -2.0, 0])

        # Square on side a (3x3)
        sq_a_verts = [a_pt, b_pt, b_pt + 3*LEFT, a_pt + 3*LEFT]
        sq_a = Polygon(*sq_a_verts, color=GREEN, fill_opacity=0.4)
        
        # Square on side b (4x4)
        sq_b_verts = [b_pt, c_pt, c_pt + 4*DOWN, b_pt + 4*DOWN]
        sq_b = Polygon(*sq_b_verts, color=BLUE, fill_opacity=0.4)
        
        # Square on side c (5x5)
        # Vector AC is [4, -3], Normal vector is [3, 4]
        normal = np.array([3, 4, 0])
        sq_c_verts = [c_pt, a_pt, a_pt + normal, c_pt + normal]
        sq_c = Polygon(*sq_c_verts, color=RED, fill_opacity=0.4)

        # Area labels
        area_a = MathTex("a^2", color=GREEN).move_to(sq_a.get_center())
        area_b = MathTex("b^2", color=BLUE).move_to(sq_b.get_center())
        area_c = MathTex("c^2", color=RED).move_to(sq_c.get_center())

        # Move text out of the way
        self.play(self.triangle_group[5].animate.to_edge(UR)) # Move formula to top right

        self.play(Create(sq_a), FadeIn(area_a))
        self.wait(0.5)
        self.play(Create(sq_b), FadeIn(area_b))
        self.wait(0.5)
        self.play(Create(sq_c), FadeIn(area_c))
        self.wait(2)

    def math_proof_section(self):
        step1 = Text("Let's use a 3-4-5 triangle:", font_size=32).to_edge(UP)
        
        values = MathTex("a = 3, \quad b = 4, \quad c = 5", font_size=40).next_to(step1, DOWN, buff=0.5)
        
        calc1 = MathTex("3^2 + 4^2 = 5^2", font_size=48).shift(UP * 0.5)
        calc2 = MathTex("9 + 16 = 25", font_size=48).next_to(calc1, DOWN, buff=0.5)
        calc3 = MathTex("25 = 25", font_size=48, color=YELLOW).next_to(calc2, DOWN, buff=0.5)
        
        box = SurroundingRectangle(calc3, color=GOLD, buff=0.2)

        self.play(Write(step1))
        self.wait(0.5)
        self.play(Write(values))
        self.wait(1)
        self.play(Write(calc1))
        self.wait(1)
        self.play(TransformMatchingTex(calc1.copy(), calc2))
        self.wait(1)
        self.play(Write(calc3))
        self.play(Create(box))
        self.wait(2)
        
        summary = Text("The sum of the areas of the smaller squares\nequals the area of the largest square.", 
                       font_size=24, line_spacing=1.5).to_edge(DOWN, buff=1)
        self.play(FadeIn(summary))
        self.wait(3)

    def outro_section(self):
        self.clear_screen()
        final_text = Text("Pythagorean Theorem", color=GOLD)
        conclusion = Text("Essential for Trigonometry and Physics", font_size=28).next_to(final_text, DOWN)
        
        self.play(Write(final_text))
        self.play(FadeIn(conclusion, shift=UP))
        self.wait(3)
        self.play(FadeOut(final_text), FadeOut(conclusion))

    def clear_screen(self):
        self.play(FadeOut(*self.mobjects))
        self.wait(0.5)

# To run this script:
# manim -pql scene.py MainScene