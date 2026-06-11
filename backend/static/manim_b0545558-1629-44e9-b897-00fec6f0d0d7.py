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

# Corrected BulletList and helper definitions for modern Manim
class BulletList(VGroup):
    def __init__(self, *items, **kwargs):
        line_spacing = kwargs.pop('line_spacing', 0.5)
        dot_color = kwargs.pop('dot_color', WHITE)
        mobjects = []
        for item in items:
            dot = MathTex(r"\bullet", color=dot_color)
            if isinstance(item, str):
                text = Text(item, **kwargs)
            else:
                text = item
            item_group = VGroup(dot, text).arrange(RIGHT, buff=0.2)
            mobjects.append(item_group)
        super().__init__(*mobjects)
        self.arrange(DOWN, aligned_edge=LEFT, buff=line_spacing)

class MainScene(Scene):
    def construct(self):
        # Set up titles and sequence
        self.intro_scene()
        self.parallelogram_area_derivation()
        self.triangle_area_derivation()
        self.summary_scene()

    def intro_scene(self):
        title = Text("Area of Parallelograms and Triangles", font_size=40)
        underline = Underline(title, color=BLUE)
        intro_grp = VGroup(title, underline).center()
        
        self.play(Write(title))
        self.play(Create(underline))
        self.wait(2)
        self.play(FadeOut(intro_grp))

    def parallelogram_area_derivation(self):
        # Section Title
        sec_title = Text("1. Area of a Parallelogram", color=BLUE).to_edge(UP)
        self.play(Write(sec_title))

        # Define points for parallelogram (Base=4, Height=2)
        p1 = np.array([-2, -1, 0])
        p2 = np.array([2, -1, 0])
        p3 = np.array([3, 1, 0])
        p4 = np.array([-1, 1, 0])
        
        parallelogram = Polygon(p1, p2, p3, p4, color=WHITE)
        parallelogram.set_fill(BLUE, opacity=0.5)
        
        # Labels
        base_line = Line(p1, p2, color=YELLOW)
        base_text = MathTex("b").next_to(base_line, DOWN)
        
        # Height logic: height line at x = -1
        height_line = DashedLine([-1, -1, 0], [-1, 1, 0], color=RED)
        height_text = MathTex("h").next_to(height_line, LEFT)
        
        self.play(Create(parallelogram))
        self.play(Create(base_line), Write(base_text))
        self.wait(1)
        self.play(Create(height_line), Write(height_text))
        self.wait(1)

        # Transformation: Split into a triangle and a trapezoid
        # Triangle: Left part (p1 to [-1, -1] to p4)
        cut_tri = Polygon(p1, [-1, -1, 0], p4, color=WHITE, stroke_width=2)
        cut_tri.set_fill(BLUE, opacity=0.8)
        
        # Main trapezoid: The rest
        main_trap = Polygon([-1, -1, 0], p2, p3, p4, color=WHITE, stroke_width=2)
        main_trap.set_fill(BLUE, opacity=0.5)
        
        self.remove(parallelogram)
        self.add(cut_tri, main_trap)
        
        self.play(Indicate(cut_tri))
        self.wait(1)
        
        # Move the triangle to the right side to form a rectangle
        # The base is 4 units wide. Moving the cut triangle 4 units right aligns it with p3.
        self.play(
            cut_tri.animate.shift(RIGHT * 4),
            run_time=2
        )
        self.wait(1)
        
        # The resulting shape is a rectangle
        rect_text = Text("Area = base × height", font_size=32).to_edge(DOWN).shift(UP*0.5)
        formula = MathTex("A = b \\cdot h", color=YELLOW).next_to(rect_text, DOWN)
        
        self.play(Write(rect_text))
        self.play(Write(formula))
        self.wait(2)
        
        # Cleanup
        self.play(FadeOut(VGroup(cut_tri, main_trap, base_text, height_line, height_text, sec_title, rect_text, formula)))

    def triangle_area_derivation(self):
        # Section Title
        sec_title = Text("2. Area of a Triangle", color=GREEN).to_edge(UP)
        self.play(Write(sec_title))

        # Triangle vertices
        t1 = np.array([-1.5, -1, 0])
        t2 = np.array([1.5, -1, 0])
        t3 = np.array([0, 1, 0])
        
        triangle = Polygon(t1, t2, t3, color=WHITE)
        triangle.set_fill(GREEN, opacity=0.5)
        
        base_line = Line(t1, t2, color=YELLOW)
        base_text = MathTex("b").next_to(base_line, DOWN)
        
        # Projection of top vertex to base for height
        height_line = DashedLine([0, -1, 0], [0, 1, 0], color=RED)
        height_text = MathTex("h").next_to(height_line, RIGHT)

        self.play(Create(triangle))
        self.play(Write(base_text), Create(height_line), Write(height_text))
        self.wait(1)

        # Clone and rotate triangle to form parallelogram
        triangle_copy = triangle.copy()
        triangle_copy.set_fill(ORANGE, opacity=0.4)
        triangle_copy.set_stroke(ORANGE)
        
        # Rotate 180 degrees around the midpoint of one of the sides
        midpoint = (t2 + t3) / 2
        
        self.play(
            Rotate(triangle_copy, angle=PI, about_point=midpoint),
            run_time=2
        )
        self.wait(1)
        
        full_shape_label = Text("Two triangles form one parallelogram", font_size=28).to_edge(DOWN).shift(UP*1)
        self.play(Write(full_shape_label))
        
        para_area = MathTex(r"\text{Total Area} = b \cdot h").next_to(full_shape_label, DOWN)
        tri_area = MathTex(r"\text{Triangle Area} = \frac{1}{2} b \cdot h", color=GREEN).next_to(para_area, DOWN)
        
        self.play(Write(para_area))
        self.wait(1)
        self.play(Indicate(triangle))
        self.play(Write(tri_area))
        self.wait(2)
        
        # Cleanup
        self.play(FadeOut(VGroup(triangle, triangle_copy, base_text, height_line, height_text, sec_title, full_shape_label, para_area, tri_area)))

    def summary_scene(self):
        summary_title = Text("Summary", font_size=40, color=YELLOW).to_edge(UP)
        
        p_formula = MathTex(r"\text{Parallelogram: } A = b \times h", color=BLUE)
        t_formula = MathTex(r"\text{Triangle: } A = \frac{1}{2} \times b \times h", color=GREEN)
        
        box = Rectangle(height=2.5, width=8, color=WHITE)
        content = VGroup(p_formula, t_formula).arrange(DOWN, buff=0.5)
        summary_box = VGroup(box, content)
        
        self.play(Write(summary_title))
        self.play(Create(box))
        self.play(Write(content))
        self.wait(3)
        
        # Safe cleanup of all remaining mobjects
        self.play(*[FadeOut(m) for m in self.mobjects])