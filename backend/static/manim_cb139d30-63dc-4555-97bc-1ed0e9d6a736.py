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
        self.introduction()
        self.unit_square_concept()
        self.rectangle_area()
        self.triangle_area()
        self.circle_area_formula()
        self.conclusion()

    def introduction(self):
        title = Text("Introduction to Area", color=BLUE).scale(1.2)
        definition = Text(
            "Area is the measure of how much space\nis inside a 2D shape.",
            font_size=36,
            t2c={"Area": YELLOW}
        ).shift(DOWN * 0.5)

        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        self.play(FadeIn(definition))
        self.wait(2)

        example_rect = Rectangle(width=4, height=2, color=WHITE)
        example_rect.set_fill(BLUE, opacity=0.5)
        label = Text("Space Inside", font_size=24).move_to(example_rect.get_center())

        self.play(FadeOut(definition))
        self.play(Create(example_rect))
        self.play(FadeIn(label))
        self.wait(1)
        self.play(Indicate(example_rect))
        self.wait(1)

        self.play(FadeOut(VGroup(title, example_rect, label)))
        self.wait(0.5)

    def unit_square_concept(self):
        title = Text("The Unit Square", color=GREEN).to_edge(UP)
        sq = Square(side_length=2, color=WHITE)
        sq.set_fill(GREEN, opacity=0.3)
        
        label_side1 = Text("1 unit", font_size=24).next_to(sq, LEFT)
        label_side2 = Text("1 unit", font_size=24).next_to(sq, DOWN)
        
        formula = MathTex(r"\text{Area} = 1 \times 1 = 1 \text{ unit}^2", color=YELLOW).shift(RIGHT * 4)

        self.play(Write(title))
        self.play(Create(sq))
        self.play(Write(label_side1), Write(label_side2))
        self.wait(1)
        self.play(Write(formula))
        self.wait(2)

        self.play(FadeOut(VGroup(title, sq, label_side1, label_side2, formula)))
        self.wait(0.5)

    def rectangle_area(self):
        title = Text("Rectangle Area", color=BLUE).to_edge(UP)
        rect = Rectangle(width=4, height=3, color=WHITE)
        rect.set_fill(BLUE, opacity=0.2)
        
        # Manually create grid lines to represent 4x3 area
        v_lines = VGroup(*[Line(rect.get_top() + RIGHT * i, rect.get_bottom() + RIGHT * i, stroke_width=1) 
                          for i in range(-1, 2)])
        h_lines = VGroup(*[Line(rect.get_left() + UP * i * 0.75, rect.get_right() + UP * i * 0.75, stroke_width=1) 
                          for i in range(-1, 2)])
        grid = VGroup(v_lines, h_lines)

        brace_w = Brace(rect, LEFT, color=WHITE)
        label_w = Text("3 units", font_size=24).next_to(brace_w, LEFT)
        
        brace_l = Brace(rect, DOWN, color=WHITE)
        label_l = Text("4 units", font_size=24).next_to(brace_l, DOWN)

        formula = MathTex(r"\text{Area} = \text{Length} \times \text{Width}", color=YELLOW).shift(UP * 2)
        calculation = MathTex(r"\text{Area} = 4 \times 3 = 12 \text{ units}^2", color=YELLOW).next_to(formula, DOWN)

        self.play(Write(title))
        self.play(Create(rect))
        self.play(FadeIn(grid))
        self.play(Create(brace_w), Write(label_w))
        self.play(Create(brace_l), Write(label_l))
        self.wait(1)
        self.play(Write(formula))
        self.play(Write(calculation))
        self.wait(2)

        self.play(FadeOut(VGroup(title, rect, grid, brace_w, label_w, brace_l, label_l, formula, calculation)))
        self.wait(0.5)

    def triangle_area(self):
        title = Text("Triangle Area", color=ORANGE).to_edge(UP)
        
        # Show a rectangle first
        base_rect = Rectangle(width=4, height=3, color=WHITE)
        rect = DashedVMobject(base_rect)
        
        # Define the triangle
        points = [
            base_rect.get_corner(DL),
            base_rect.get_corner(DR),
            base_rect.get_corner(UR)
        ]
        triangle = Polygon(*points, color=ORANGE)
        triangle.set_fill(ORANGE, opacity=0.4)

        brace_b = Brace(triangle, DOWN, color=WHITE)
        label_b = Text("Base", font_size=24).next_to(brace_b, DOWN)
        
        line_h = Line(base_rect.get_corner(DR), base_rect.get_corner(UR), color=RED)
        label_h = Text("Height", font_size=24, color=RED).next_to(line_h, RIGHT)

        formula = MathTex(
            r"\text{Area} = \frac{1}{2} \times \text{Base} \times \text{Height}",
            color=YELLOW
        ).shift(UP * 1.5 + LEFT * 3)

        self.play(Write(title))
        self.play(Create(rect))
        self.wait(0.5)
        self.play(Create(triangle))
        self.play(Create(brace_b), Write(label_b))
        self.play(Create(line_h), Write(label_h))
        self.wait(1)
        self.play(Write(formula))
        self.play(Wiggle(triangle))
        self.wait(2)

        self.play(FadeOut(VGroup(title, rect, triangle, brace_b, label_b, line_h, label_h, formula)))
        self.wait(0.5)

    def circle_area_formula(self):
        title = Text("Circle Area", color=PURPLE).to_edge(UP)
        circle = Circle(radius=2, color=WHITE)
        circle.set_fill(PURPLE, opacity=0.3)
        
        center_dot = Dot(circle.get_center())
        radius_line = Line(circle.get_center(), circle.get_right(), color=YELLOW)
        radius_label = MathTex("r", color=YELLOW).next_to(radius_line, UP)

        formula = MathTex(r"\text{Area} = \pi r^2", color=YELLOW).scale(1.5).shift(RIGHT * 4)

        self.play(Write(title))
        self.play(Create(circle))
        self.play(Create(center_dot), Create(radius_line))
        self.play(Write(radius_label))
        self.wait(1)
        self.play(Write(formula))
        self.play(Circumscribe(formula))
        self.wait(2)

        self.play(FadeOut(VGroup(title, circle, center_dot, radius_line, radius_label, formula)))
        self.wait(0.5)

    def conclusion(self):
        summary_title = Text("Summary", color=WHITE).to_edge(UP)
        
        rectangle_f = MathTex(r"\text{Rectangle: } A = l \times w").scale(0.8)
        triangle_f = MathTex(r"\text{Triangle: } A = \frac{1}{2} b \times h").scale(0.8)
        circle_f = MathTex(r"\text{Circle: } A = \pi r^2").scale(0.8)
        
        formulas = VGroup(rectangle_f, triangle_f, circle_f).arrange(DOWN, buff=0.5)
        
        final_text = Text("Area measures the surface inside a shape.", font_size=32, color=BLUE).shift(DOWN * 2.5)

        self.play(Write(summary_title))
        self.play(FadeIn(formulas, shift=UP))
        self.wait(1)
        self.play(Write(final_text))
        self.wait(3)

        self.play(FadeOut(VGroup(*self.mobjects)))

if __name__ == "__main__":
    import os
    os.system("manim -pql scene.py MainScene")