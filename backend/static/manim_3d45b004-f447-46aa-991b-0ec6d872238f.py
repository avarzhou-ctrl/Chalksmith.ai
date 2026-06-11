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
        self.intro_section()
        self.clear_screen()
        self.unit_square_section()
        self.clear_screen()
        self.rectangle_area_section()
        self.clear_screen()
        self.summary_section()

    def clear_screen(self):
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.5)

    def intro_section(self):
        title = Text("What is Area?", font_size=48, color=BLUE)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))

        definition = Text(
            "Area is the measure of how much space\nis inside a 2D shape.",
            font_size=32,
            line_spacing=1.5
        )
        self.play(FadeIn(definition))
        self.wait(2)

        # Illustrate space inside
        circle = Circle(radius=1.5, color=WHITE).shift(DOWN * 1)
        self.play(Create(circle))
        self.play(circle.animate.set_fill(TEAL, opacity=0.5))
        
        label = Text("Space Inside", font_size=24).move_to(circle.get_center())
        self.play(Write(label))
        self.wait(2)

    def unit_square_section(self):
        header = Text("Measuring with Unit Squares", font_size=40, color=YELLOW)
        header.to_edge(UP)
        self.play(Write(header))

        # Create a unit square
        unit_sq = Square(side_length=2, color=ORANGE)
        unit_sq.set_fill(ORANGE, opacity=0.3)
        unit_sq.shift(LEFT * 3)
        
        side_a = Line(unit_sq.get_corner(DL), unit_sq.get_corner(UL), color=WHITE)
        side_b = Line(unit_sq.get_corner(DL), unit_sq.get_corner(DR), color=WHITE)
        
        label_a = MathTex("1", font_size=36).next_to(side_a, LEFT)
        label_b = MathTex("1", font_size=36).next_to(side_b, DOWN)

        self.play(Create(unit_sq), Create(side_a), Create(side_b))
        self.play(Write(label_a), Write(label_b))

        explanation = Text(
            "We measure area by counting\nhow many 'unit squares'\nfit inside a shape.",
            font_size=28
        ).shift(RIGHT * 3)

        unit_label = MathTex("Area = 1 \\times 1 = 1", font_size=36).next_to(unit_sq, UP)
        
        self.play(Write(explanation))
        self.play(Write(unit_label))
        self.wait(3)

    def rectangle_area_section(self):
        header = Text("Area of a Rectangle", font_size=40, color=GREEN)
        header.to_edge(UP)
        self.play(Write(header))

        # Create a 4x3 rectangle
        rect = Rectangle(width=4, height=3, color=WHITE)
        rect.shift(DOWN * 0.5)
        self.play(Create(rect))

        brace_w = Brace(rect, DOWN)
        text_w = brace_w.get_tex("4", " \\text{ units}")
        
        brace_h = Brace(rect, LEFT)
        text_h = brace_h.get_tex("3", " \\text{ units}")

        self.play(
            Create(brace_w), Write(text_w),
            Create(brace_h), Write(text_h)
        )
        self.wait(1)

        # Create the grid to fill the rectangle
        grid = VGroup()
        for i in range(3): # rows
            for j in range(4): # cols
                sq = Square(side_length=1, stroke_width=1, color=GRAY)
                sq.move_to(rect.get_corner(UL) + RIGHT * (j + 0.5) + DOWN * (i + 0.5))
                grid.add(sq)

        self.play(LaggedStart(*[FadeIn(sq) for sq in grid], lag_ratio=0.1))
        self.wait(1)

        # Counting animation
        formula = MathTex("Area", "=", "Length", "\\times", "Width", font_size=44)
        formula.to_edge(DOWN, buff=0.5)
        
        calc = MathTex("Area", "=", "4", "\\times", "3", "=", "12", font_size=44)
        calc.move_to(formula.get_center())

        self.play(Write(formula))
        self.wait(2)
        self.play(Transform(formula, calc))
        
        # Highlight some squares to show counting
        highlights = VGroup(*[s.copy().set_fill(YELLOW, opacity=0.5) for s in grid])
        self.play(LaggedStart(*[FadeIn(h) for h in highlights], lag_ratio=0.05, run_time=2))
        self.wait(3)

    def summary_section(self):
        title = Text("Summary", font_size=48, color=PURPLE).to_edge(UP)
        self.play(Write(title))

        point1 = Text("• Area measures surface space.", font_size=32)
        point2 = Text("• It is measured in square units.", font_size=32)
        point3 = Text("• For rectangles: Area = Length × Width.", font_size=32)
        
        points = VGroup(point1, point2, point3).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        points.next_to(title, DOWN, buff=1)

        for p in points:
            self.play(FadeIn(p, shift=RIGHT))
            self.wait(1.5)

        final_rect = Rectangle(width=2, height=1, color=GOLD, fill_opacity=0.5).next_to(points, DOWN, buff=0.8)
        self.play(Create(final_rect))
        self.wait(3)

if __name__ == "__main__":
    import os
    os.system("manim -pql scene.py MainScene")