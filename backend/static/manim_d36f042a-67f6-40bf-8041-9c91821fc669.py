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
        self.unit_squares_concept()
        self.rectangle_area()
        self.triangle_area()
        self.summary_screen()

    def introduction(self):
        title = Text("Understanding Area", font_size=48, color=BLUE)
        subtitle = Text("Measuring 2D Space", font_size=32, color=GRAY)
        VGroup(title, subtitle).arrange(DOWN)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))

    def unit_squares_concept(self):
        section_title = Text("1. What is Area?", color=YELLOW).to_edge(UP)
        self.play(Write(section_title))

        # Create a large square representing 3x3 units
        big_square = Square(side_length=3, color=WHITE)
        self.play(Create(big_square))

        definition = Text("Area is the number of 'unit squares'\nthat fit inside a shape.", font_size=28)
        definition.next_to(big_square, RIGHT, buff=1)
        self.play(Write(definition))
        self.wait(1)

        # Fill with unit squares
        unit_squares = VGroup()
        count_labels = VGroup()
        
        # Calculate start position (Top-Left)
        start_pos = big_square.get_corner(UL) + RIGHT * 0.5 + DOWN * 0.5
        
        for i in range(3): # Rows
            for j in range(3): # Cols
                sq = Square(side_length=1, color=BLUE, fill_opacity=0.5)
                sq.move_to(start_pos + RIGHT * j + DOWN * i)
                num = MathTex(str(len(unit_squares) + 1), font_size=24).move_to(sq.get_center())
                unit_squares.add(sq)
                count_labels.add(num)
                self.play(FadeIn(sq), Write(num), run_time=0.2)

        total_area = MathTex(r"\text{Area} = 9 \text{ units}^2", color=YELLOW)
        total_area.next_to(big_square, DOWN)
        self.play(Write(total_area))
        self.wait(2)

        self.play(
            *[FadeOut(m) for m in [unit_squares, count_labels, big_square, definition, total_area, section_title]]
        )

    def rectangle_area(self):
        section_title = Text("2. Rectangles", color=YELLOW).to_edge(UP)
        self.play(Write(section_title))

        rect = Rectangle(width=5, height=3, color=WHITE)
        rect.shift(LEFT * 1.5)
        self.play(Create(rect))

        # Dimensions
        w_label = MathTex("w = 5", color=BLUE).next_to(rect, DOWN)
        h_label = MathTex("h = 3", color=BLUE).next_to(rect, LEFT)
        
        self.play(Write(w_label), Write(h_label))
        self.wait(1)

        formula = MathTex(r"A = \text{width} \times \text{height}", color=GREEN)
        formula.next_to(rect, RIGHT, buff=1).shift(UP * 0.5)
        
        calculation = MathTex(r"A = 5 \times 3", color=WHITE).next_to(formula, DOWN)
        result = MathTex(r"A = 15", color=YELLOW).next_to(calculation, DOWN)

        self.play(Write(formula))
        self.wait(0.5)
        self.play(Write(calculation))
        self.play(rect.animate.set_fill(BLUE, opacity=0.3))
        self.play(Write(result))
        self.wait(2)

        self.play(
            *[FadeOut(m) for m in [rect, w_label, h_label, formula, calculation, result, section_title]]
        )

    def triangle_area(self):
        section_title = Text("3. Triangles", color=YELLOW).to_edge(UP)
        self.play(Write(section_title))

        # Setup bounding box
        box = Rectangle(width=4, height=3, color=GRAY, stroke_style=DASHED)
        self.play(Create(box))
        
        b_label = MathTex("b", color=BLUE).next_to(box, DOWN)
        h_label = MathTex("h", color=BLUE).next_to(box, LEFT)
        self.play(Write(b_label), Write(h_label))

        # Construct Triangle
        triangle = Polygon(
            box.get_corner(DL), box.get_corner(DR), box.get_corner(UR),
            color=RED, fill_opacity=0.4
        )
        diag = Line(box.get_corner(DL), box.get_corner(UR), color=WHITE)
        
        self.play(Create(diag))
        self.wait(0.5)
        self.play(DrawBorderThenFill(triangle))

        explanation = Text("A triangle is exactly half\nof its bounding rectangle.", font_size=24)
        explanation.to_edge(RIGHT, buff=0.5).shift(UP)
        
        formula = MathTex(r"A = \frac{1}{2} \times b \times h", color=RED)
        formula.next_to(explanation, DOWN, buff=0.5)
        
        self.play(Write(explanation))
        self.play(Write(formula))
        self.wait(3)

        self.play(
            *[FadeOut(m) for m in [box, b_label, h_label, diag, triangle, explanation, formula, section_title]]
        )

    def summary_screen(self):
        summary_title = Text("Summary", color=BLUE).to_edge(UP)
        
        # Using discrete Text and MathTex objects for a clean list
        points = VGroup(
            Text("• Area measures surface space.", font_size=32),
            Text("• Units are always squared (e.g. m²).", font_size=32),
            MathTex(r"\text{Rectangle: } A = w \cdot h", color=GREEN),
            MathTex(r"\text{Triangle: } A = \frac{1}{2} b \cdot h", color=RED)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to(ORIGIN)
        
        self.play(Write(summary_title))
        for p in points:
            self.play(FadeIn(p, shift=RIGHT))
            self.wait(0.5)
            
        self.wait(3)
        self.play(*[FadeOut(m) for m in self.mobjects])

if __name__ == "__main__":
    from manim import config
    config.background_color = BLACK
    scene = MainScene()
    scene.render()