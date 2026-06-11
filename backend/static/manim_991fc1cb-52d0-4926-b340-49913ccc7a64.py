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
        self.introduction()
        self.square_units()
        self.rectangle_area()
        self.triangle_area()
        self.circle_area_intro()
        self.summary()

    def introduction(self):
        title = Text("Understanding Area", font_size=48, color=BLUE)
        subtitle = Text("The amount of space inside a 2D shape", font_size=32)
        subtitle.next_to(title, DOWN)
        
        intro_group = VGroup(title, subtitle).center()
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(2)
        self.play(FadeOut(intro_group))

    def square_units(self):
        section_title = Text("1. Square Units", color=YELLOW).to_edge(UP)
        self.play(Write(section_title))

        # Create a single unit square
        unit_square = Square(side_length=1.0, color=WHITE)
        label = Text("1 Unit", font_size=20).next_to(unit_square, DOWN)
        label2 = Text("1 Unit", font_size=20).next_to(unit_square, RIGHT)
        
        unit_group = VGroup(unit_square, label, label2).center()
        
        explanation = Text("Area is measured in square units.", font_size=28).shift(UP * 1.5)
        
        self.play(Create(unit_square), Write(label), Write(label2))
        self.play(Write(explanation))
        self.wait(1)
        
        # Grid formation
        grid = VGroup()
        for i in range(3):
            for j in range(3):
                sq = Square(side_length=1.0, color=GRAY, fill_opacity=0.3)
                sq.shift(RIGHT * i + UP * j)
                grid.add(sq)
        
        grid.center().shift(DOWN * 0.5)
        
        self.play(
            FadeOut(unit_group),
            FadeOut(explanation),
            Create(grid)
        )
        
        count_text = Text("Total Area = 9 Square Units", font_size=36, color=YELLOW)
        count_text.next_to(grid, DOWN, buff=0.5)
        
        self.play(Write(count_text))
        self.wait(2)
        self.play(FadeOut(grid), FadeOut(count_text), FadeOut(section_title))

    def rectangle_area(self):
        section_title = Text("2. Area of a Rectangle", color=BLUE).to_edge(UP)
        self.play(Write(section_title))

        rect = Rectangle(width=5, height=3, color=WHITE)
        rect.set_fill(BLUE, opacity=0.3)
        
        length_label = MathTex("w = 5", color=WHITE).next_to(rect, DOWN)
        width_label = MathTex("h = 3", color=WHITE).next_to(rect, LEFT)
        
        formula = MathTex("Area", "=", "width", "\\times", "height", font_size=42)
        formula.shift(UP * 2.5)
        
        self.play(Create(rect))
        self.play(Write(length_label), Write(width_label))
        self.wait(1)
        
        self.play(Write(formula))
        self.wait(1)
        
        calculation = MathTex("Area", "=", "5", "\\times", "3", "=", "15", font_size=42)
        calculation.next_to(formula, DOWN)
        calculation.set_color(YELLOW)
        
        self.play(Write(calculation))
        self.wait(2)
        
        self.play(FadeOut(rect), FadeOut(length_label), FadeOut(width_label), 
                  FadeOut(formula), FadeOut(calculation), FadeOut(section_title))

    def triangle_area(self):
        section_title = Text("3. Area of a Triangle", color=GREEN).to_edge(UP)
        self.play(Write(section_title))

        # Show how a triangle is half a rectangle
        rect = Rectangle(width=4, height=3, color=GRAY, stroke_style=DASHED)
        diag = Line(rect.get_corner(DL), rect.get_corner(UR), color=WHITE)
        
        triangle = Polygon(
            rect.get_corner(DL), 
            rect.get_corner(DR), 
            rect.get_corner(UR),
            color=GREEN, fill_opacity=0.5
        )
        
        base_label = MathTex("b").next_to(rect, DOWN)
        height_label = MathTex("h").next_to(rect, RIGHT)
        
        self.play(Create(rect))
        self.play(Create(triangle))
        self.play(Write(base_label), Write(height_label))
        
        formula = MathTex("Area", "=", "{1 \\over 2}", "\\times", "base", "\\times", "height")
        formula.shift(UP * 2)
        
        self.play(Write(formula))
        self.wait(2)
        
        self.play(FadeOut(rect), FadeOut(triangle), FadeOut(base_label), 
                  FadeOut(height_label), FadeOut(formula), FadeOut(section_title))

    def circle_area_intro(self):
        section_title = Text("4. Area of a Circle", color=RED).to_edge(UP)
        self.play(Write(section_title))

        circle = Circle(radius=2, color=RED)
        circle.set_fill(RED, opacity=0.3)
        
        radius_line = Line(circle.get_center(), circle.get_right(), color=WHITE)
        radius_label = MathTex("r").next_to(radius_line, UP, buff=0.1)
        
        formula = MathTex("Area", "=", "\\pi", "r^2", font_size=48)
        formula.shift(LEFT * 3)
        
        circle_group = VGroup(circle, radius_line, radius_label).shift(RIGHT * 2)
        
        self.play(Create(circle), Create(radius_line), Write(radius_label))
        self.play(Write(formula))
        self.wait(2)
        
        self.play(FadeOut(circle_group), FadeOut(formula), FadeOut(section_title))

    def summary(self):
        summary_title = Text("Summary of Formulas", color=GOLD).to_edge(UP)
        self.play(Write(summary_title))

        # Create a manual list of formulas
        rect_f = MathTex("\\text{Rectangle: } A = w \\times h")
        tri_f = MathTex("\\text{Triangle: } A = \\frac{1}{2} b \\times h")
        circ_f = MathTex("\\text{Circle: } A = \\pi r^2")
        
        formulas = VGroup(rect_f, tri_f, circ_f).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        formulas.center()
        
        # Drawing small icons next to formulas
        r_icon = Rectangle(width=0.6, height=0.4, color=BLUE).next_to(rect_f, LEFT, buff=0.5)
        t_icon = Triangle(color=GREEN).scale(0.25).next_to(tri_f, LEFT, buff=0.5)
        c_icon = Circle(radius=0.25, color=RED).next_to(circ_f, LEFT, buff=0.5)
        
        icons = VGroup(r_icon, t_icon, c_icon)
        
        self.play(FadeIn(rect_f), Create(r_icon))
        self.play(FadeIn(tri_f), Create(t_icon))
        self.play(FadeIn(circ_f), Create(c_icon))
        
        self.wait(3)
        
        final_text = Text("Area measures the surface space!", font_size=32, color=GOLD)
        final_text.to_edge(DOWN, buff=1)
        self.play(Write(final_text))
        self.wait(3)

if __name__ == "__main__":
    import os
    os.system("manim -pql scene.py MainScene")