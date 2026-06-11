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
        self.unit_tiling()
        self.rectangle_area()
        self.triangle_area()
        self.summary()

    def introduction(self):
        title = Text("Understanding Area", color=BLUE).scale(1.2)
        definition = Text("Area is the amount of space inside a 2D shape.", font_size=32)
        
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        square = Square(side_length=3, color=WHITE)
        self.play(Create(square))
        self.play(square.animate.set_fill(BLUE, opacity=0.5))
        
        definition.next_to(square, DOWN, buff=0.5)
        self.play(FadeIn(definition))
        self.wait(2)
        
        self.play(FadeOut(VGroup(title, square, definition)))

    def unit_tiling(self):
        section_title = Text("Measuring with Unit Squares", color=YELLOW).to_edge(UP)
        self.play(Write(section_title))
        
        # Create a grid to show tiling
        grid = VGroup()
        for i in range(3):
            for j in range(3):
                sq = Square(side_length=1).shift(RIGHT * (j - 1) + UP * (i - 1))
                grid.add(sq)
        
        grid.center()
        self.play(Create(grid))
        self.wait(1)
        
        labels = VGroup()
        for i, sq in enumerate(grid):
            label = Text(str(i + 1), font_size=24).move_to(sq.get_center())
            labels.add(label)
            self.play(FadeIn(label), sq.animate.set_fill(GREEN, opacity=0.3), run_time=0.2)
        
        area_text = MathTex(r"\text{Area} = 9 \text{ units}^2").next_to(grid, RIGHT, buff=1)
        self.play(Write(area_text))
        self.wait(2)
        
        self.play(FadeOut(VGroup(section_title, grid, labels, area_text)))

    def rectangle_area(self):
        section_title = Text("The Rectangle Formula", color=GOLD).to_edge(UP)
        self.play(Write(section_title))
        
        rect = Rectangle(width=5, height=3, color=WHITE)
        rect.set_fill(ORANGE, opacity=0.4)
        rect.center()
        
        brace_w = Brace(rect, DOWN)
        label_w = Text("Width (w)", font_size=24).next_to(brace_w, DOWN)
        
        brace_h = Brace(rect, LEFT)
        label_h = Text("Height (h)", font_size=24).next_to(brace_h, LEFT)
        
        formula = MathTex(r"\text{Area} = w \times h").shift(UP * 2)
        
        self.play(Create(rect))
        self.play(GrowFromCenter(brace_w), Write(label_w))
        self.play(GrowFromCenter(brace_h), Write(label_h))
        self.wait(1)
        
        self.play(Write(formula))
        self.play(Indicate(formula))
        
        example_calc = MathTex(r"5 \times 3 = 15 \text{ units}^2").next_to(formula, DOWN)
        self.play(Write(example_calc))
        self.wait(2)
        
        self.play(FadeOut(VGroup(section_title, rect, brace_w, label_w, brace_h, label_h, formula, example_calc)))

    def triangle_area(self):
        section_title = Text("Area of a Triangle", color=PURPLE).to_edge(UP)
        self.play(Write(section_title))
        
        # Draw a rectangle to show the relationship
        # Fixed: Rectangle does not accept stroke_dash_array in __init__
        box_outline = Rectangle(width=4, height=3, color=GRAY)
        box = DashedVMobject(box_outline)
        self.play(Create(box))
        
        # Create a triangle using the same base and height
        points = [
            box.get_corner(DL),
            box.get_corner(DR),
            box.get_corner(UR)
        ]
        tri = Polygon(*points, color=PURPLE, fill_opacity=0.6)
        
        self.play(Create(tri))
        self.wait(1)
        
        label_b = MathTex(r"b").next_to(box, DOWN)
        label_h = MathTex(r"h").next_to(box, RIGHT)
        
        self.play(Write(label_b), Write(label_h))
        
        formula = MathTex(r"\text{Area} = \frac{1}{2} \times b \times h").shift(LEFT * 3)
        explanation = Text("A triangle is half of a rectangle.", font_size=24).next_to(formula, DOWN)
        
        self.play(Write(formula))
        self.play(FadeIn(explanation))
        self.wait(2)
        
        self.play(FadeOut(VGroup(section_title, box, tri, label_b, label_h, formula, explanation)))

    def summary(self):
        summary_title = Text("Summary", color=BLUE).to_edge(UP)
        self.play(Write(summary_title))
        
        line1 = Text("1. Area measures surface coverage.", font_size=32)
        line2 = Text("2. Rectangle: Width x Height", font_size=32)
        line3 = Text("3. Triangle: 1/2 x Base x Height", font_size=32)
        
        lines = VGroup(line1, line2, line3).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        lines.center()
        
        for line in lines:
            self.play(FadeIn(line, shift=RIGHT))
            self.wait(1)
            
        final_msg = Text("Area is measured in square units.", color=YELLOW).next_to(lines, DOWN, buff=1)
        self.play(Write(final_msg))
        self.wait(3)
        
        self.play(FadeOut(VGroup(*self.mobjects)))