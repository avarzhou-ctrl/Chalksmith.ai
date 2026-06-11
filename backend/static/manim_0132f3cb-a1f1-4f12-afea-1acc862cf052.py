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
        self.unit_square_explanation()
        self.rectangle_area()
        self.triangle_area()
        self.summary_section()

    def introduction(self):
        title = Text("Understanding Area", color=BLUE, font_size=48)
        subtitle = Text("Measuring 2D Space", color=GRAY, font_size=32).next_to(title, DOWN)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(2)
        
        self.play(FadeOut(title), FadeOut(subtitle))
        self.wait(1)

    def unit_square_explanation(self):
        concept_text = Text("Area is the number of unit squares\nthat fit inside a shape.", font_size=32)
        self.play(Write(concept_text))
        self.wait(2)
        self.play(concept_text.animate.to_edge(UP))

        # Create a single unit square
        unit_square = Square(side_length=1, color=YELLOW)
        unit_square.set_fill(YELLOW, opacity=0.3)
        label = Text("1 Unit", font_size=20).next_to(unit_square, DOWN)
        
        square_group = VGroup(unit_square, label).center()
        
        self.play(Create(unit_square))
        self.play(Write(label))
        self.wait(1)
        
        # Transform into a grid
        grid = VGroup()
        for x in range(3):
            for y in range(2):
                s = Square(side_length=1, color=YELLOW)
                s.set_fill(YELLOW, opacity=0.3)
                s.shift(x * RIGHT + y * UP)
                grid.add(s)
        
        grid.move_to(ORIGIN)
        
        self.play(
            ReplacementTransform(unit_square, grid),
            FadeOut(label)
        )
        
        # Label the squares 1 to 6
        labels = VGroup()
        for i, s in enumerate(grid):
            num = Text(str(i + 1), font_size=24).move_to(s.get_center())
            labels.add(num)
        
        self.play(LaggedStartMap(FadeIn, labels, lag_ratio=0.3))
        self.wait(1)
        
        total_text = Text("Area = 6 Square Units", color=YELLOW).next_to(grid, DOWN, buff=0.5)
        self.play(Write(total_text))
        self.wait(2)
        
        self.play(FadeOut(grid), FadeOut(labels), FadeOut(total_text), FadeOut(concept_text))

    def rectangle_area(self):
        header = Text("Area of a Rectangle", color=BLUE).to_edge(UP)
        self.play(Write(header))
        
        rect = Rectangle(width=5, height=3, color=WHITE)
        rect.set_fill(BLUE, opacity=0.2)
        
        length_brace = Brace(rect, DOWN, color=WHITE)
        width_brace = Brace(rect, LEFT, color=WHITE)
        
        length_text = MathTex("L = 5", color=WHITE).next_to(length_brace, DOWN)
        width_text = MathTex("W = 3", color=WHITE).next_to(width_brace, LEFT)
        
        self.play(Create(rect))
        self.play(
            Create(length_brace),
            Write(length_text),
            Create(width_brace),
            Write(width_text)
        )
        self.wait(1)
        
        # Show formula
        formula = MathTex(r"Area = L \times W", color=YELLOW).shift(UP * 0.5)
        calc1 = MathTex(r"Area = 5 \times 3", color=YELLOW).next_to(formula, DOWN)
        calc2 = MathTex(r"Area = 15", color=YELLOW).next_to(calc1, DOWN)
        
        math_group = VGroup(formula, calc1, calc2).shift(RIGHT * 3)
        
        # Move rectangle to the left to make room
        self.play(
            VGroup(rect, length_brace, width_brace, length_text, width_text).animate.shift(LEFT * 3)
        )
        
        self.play(Write(formula))
        self.wait(1)
        self.play(Write(calc1))
        self.wait(1)
        self.play(Write(calc2))
        self.play(Indicate(calc2))
        self.wait(2)
        
        self.play(FadeOut(Group(*self.mobjects)))

    def triangle_area(self):
        header = Text("Area of a Triangle", color=GREEN).to_edge(UP)
        self.play(Write(header))
        
        # Draw a rectangle to show context
        rect = Rectangle(width=4, height=3, color=WHITE, stroke_dash_array=[5, 5])
        self.play(Create(rect))
        
        # Label base and height
        b_label = MathTex("b").next_to(rect, DOWN)
        h_label = MathTex("h").next_to(rect, LEFT)
        self.play(Write(b_label), Write(h_label))
        
        # Draw the triangle inside
        triangle = Polygon(
            rect.get_corner(DL),
            rect.get_corner(DR),
            rect.get_corner(UR),
            color=GREEN,
            fill_opacity=0.5
        )
        
        self.play(Create(triangle))
        self.wait(1)
        
        explanation = Text("A triangle is half of a rectangle.", font_size=28).to_edge(DOWN, buff=1)
        self.play(Write(explanation))
        self.wait(1)
        
        formula = MathTex(r"Area = \frac{1}{2} \times b \times h", color=GREEN).shift(RIGHT * 3)
        
        # Reposition
        self.play(
            VGroup(rect, triangle, b_label, h_label).animate.shift(LEFT * 2),
            explanation.animate.shift(LEFT * 2)
        )
        self.play(Write(formula))
        self.wait(2)
        
        self.play(FadeOut(Group(*self.mobjects)))

    def summary_section(self):
        summary_title = Text("Summary", color=GOLD, font_size=44).to_edge(UP)
        self.play(Write(summary_title))
        
        # Manually construct a list of points
        point1 = Text("• Area measures the 2D surface of a shape.", font_size=30)
        point2 = Text("• It is measured in square units.", font_size=30)
        point3 = MathTex(r"\bullet \text{ Rectangle: } A = L \times W", font_size=36)
        point4 = MathTex(r"\bullet \text{ Triangle: } A = \frac{1}{2} b \times h", font_size=36)
        
        points = VGroup(point1, point2, point3, point4).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        points.next_to(summary_title, DOWN, buff=1)
        
        for point in points:
            self.play(FadeIn(point, shift=RIGHT))
            self.wait(1)
            
        self.wait(2)
        
        final_msg = Text("Thanks for watching!", color=BLUE, font_size=40).to_edge(DOWN, buff=1)
        self.play(Write(final_msg))
        self.wait(3)
        
        self.play(FadeOut(Group(*self.mobjects)))