from manim import *

# Compatibility layer for potential missing constants/methods
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
        # Use Text or MathTex as they are VMobjects
        mobjects = [Text(f'{dot}{item}', font_size=32, **kwargs) for item in items]
        super().__init__(*mobjects)
        self.arrange(DOWN, aligned_edge=LEFT, buff=line_spacing)

class MainScene(Scene):
    def construct(self):
        self.introduction()
        self.unit_squares()
        self.rectangle_formula()
        self.circle_area()
        self.summary_scene()

    def introduction(self):
        title = Text("Understanding Area", color=BLUE).scale(1.2)
        definition = Text(
            "Area is the amount of space inside a 2D shape.",
            font_size=30
        ).next_to(title, DOWN)

        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(definition, shift=UP))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(definition))

    def unit_squares(self):
        instruction = Text("We measure area using 'Unit Squares'", font_size=32).to_edge(UP)
        self.play(Write(instruction))

        # Create a 4x3 rectangle
        rect = Rectangle(width=4, height=3, color=WHITE)
        rect.shift(LEFT * 2)
        self.play(Create(rect))

        # Fill with unit squares
        squares = VGroup()
        for i in range(4):
            for j in range(3):
                sq = Square(side_length=1, stroke_width=2, color=YELLOW)
                # Position squares relative to the bottom left corner of the rectangle
                sq.move_to(rect.get_corner(DL) + [i + 0.5, j + 0.5, 0])
                squares.add(sq)

        self.play(Create(squares, run_time=3, lag_ratio=0.1))
        
        counter_text = Text("Total Squares: 12", font_size=36, color=YELLOW)
        counter_text.next_to(rect, RIGHT, buff=1)
        
        self.play(Write(counter_text))
        self.wait(2)

        self.play(FadeOut(instruction), FadeOut(rect), FadeOut(squares), FadeOut(counter_text))

    def rectangle_formula(self):
        header = Text("The Rectangle Formula", color=GREEN).to_edge(UP)
        self.play(Write(header))

        rect = Rectangle(width=5, height=3, color=BLUE, fill_opacity=0.3)
        rect.shift(DOWN * 0.5)
        
        width_label = MathTex("w = 5").next_to(rect, DOWN)
        height_label = MathTex("h = 3").next_to(rect, LEFT)
        
        formula = MathTex("Area", "=", "w", "\\times", "h").scale(1.2)
        formula.next_to(header, DOWN, buff=0.5)

        self.play(Create(rect))
        self.play(Write(width_label), Write(height_label))
        self.wait(1)
        self.play(Write(formula))
        
        # Calculation update
        calc = MathTex("Area", "=", "5", "\\times", "3", "=", "15").scale(1.2)
        calc.move_to(formula)
        
        # Use ReplacementTransform to swap formula for calculation
        self.play(ReplacementTransform(formula, calc))
        self.play(Indicate(calc))
        self.wait(2)

        self.play(FadeOut(header), FadeOut(rect), FadeOut(width_label), FadeOut(height_label), FadeOut(calc))

    def circle_area(self):
        header = Text("Area of a Circle", color=ORANGE).to_edge(UP)
        self.play(Write(header))

        circle = Circle(radius=2, color=ORANGE, fill_opacity=0.4)
        circle.shift(LEFT * 2 + DOWN * 0.5)
        
        radius_line = Line(circle.get_center(), circle.get_right(), color=WHITE)
        radius_label = MathTex("r").next_to(radius_line, UP, buff=0.1)
        
        formula = MathTex("Area", "=", "\\pi", "r^2").scale(1.5)
        formula.next_to(circle, RIGHT, buff=1.5)

        self.play(Create(circle))
        self.play(Create(radius_line), Write(radius_label))
        self.wait(1)
        self.play(Write(formula))
        self.play(Circumscribe(formula))
        self.wait(2)

        self.play(FadeOut(header), FadeOut(circle), FadeOut(radius_line), FadeOut(radius_label), FadeOut(formula))

    def summary_scene(self):
        summary_title = Text("Summary", color=BLUE).to_edge(UP)
        
        point1 = Text("1. Area is the space inside a 2D boundary.", font_size=28)
        point2 = Text("2. Rectangles: Area = Width x Height", font_size=28)
        point3 = Text("3. Circles: Area = \u03c0 \u00d7 r\u00b2", font_size=28)
        
        points = VGroup(point1, point2, point3).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        points.next_to(summary_title, DOWN, buff=1)

        self.play(Write(summary_title))
        for point in points:
            self.play(FadeIn(point, shift=RIGHT))
            self.wait(0.5)
            
        self.wait(2)
        # Fix: Fade out each object currently in the scene to avoid VGroup type errors
        self.play(*[FadeOut(mob) for mob in self.mobjects])