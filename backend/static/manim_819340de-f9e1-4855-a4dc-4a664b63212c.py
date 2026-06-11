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
        self.rectangle_area_derivation()
        self.summary()

    def introduction(self):
        # Title and Definition
        title = Text("What is Area?", font_size=48).to_edge(UP)
        definition = Text(
            "Area is the amount of space inside a 2D shape.",
            font_size=32,
            t2c={"Area": YELLOW}
        ).next_to(title, DOWN, buff=0.5)

        # Illustrate with shapes
        circle = Circle(radius=1.5, color=BLUE, fill_opacity=0.3)
        square = Square(side_length=3, color=GREEN, fill_opacity=0.3).shift(RIGHT * 3)
        shapes = VGroup(circle, square).center().shift(DOWN * 0.5)

        self.play(Write(title))
        self.play(FadeIn(definition))
        self.wait(1)
        self.play(Create(circle), Create(square))
        self.play(
            circle.animate.set_fill(BLUE, opacity=0.8), 
            square.animate.set_fill(GREEN, opacity=0.8)
        )
        self.wait(2)

        # Transition
        self.play(FadeOut(title), FadeOut(definition), FadeOut(shapes))

    def unit_square_concept(self):
        title = Text("The Unit Square", font_size=40).to_edge(UP)
        
        # Create a unit square (scaled for visibility)
        unit_sq = Square(side_length=2, color=WHITE)
        unit_sq.set_fill(YELLOW, opacity=0.3)
        
        # Labels
        label_top = Text("1 unit", font_size=24).next_to(unit_sq, UP)
        label_side = Text("1 unit", font_size=24).next_to(unit_sq, LEFT)
        label_center = Text("1 Square Unit", font_size=28, color=YELLOW).move_to(unit_sq.get_center())

        explanation = Text(
            "We measure area by counting how many\n'unit squares' fit inside a shape.",
            font_size=28,
            line_spacing=1
        ).to_edge(DOWN, buff=1)

        self.play(Write(title))
        self.play(Create(unit_sq))
        self.play(Write(label_top), Write(label_side))
        self.wait(1)
        self.play(FadeIn(label_center))
        self.play(Write(explanation))
        self.wait(3)

        self.play(FadeOut(title), FadeOut(unit_sq), FadeOut(label_top), 
                  FadeOut(label_side), FadeOut(label_center), FadeOut(explanation))

    def rectangle_area_derivation(self):
        title = Text("Calculating Rectangle Area", font_size=40).to_edge(UP)
        self.play(Write(title))

        # Create a 4x3 rectangle
        rect_width = 4
        rect_height = 3
        # We scale the rectangle so the "units" are manageable on screen
        main_rect = Rectangle(width=rect_width, height=rect_height, color=WHITE)
        main_rect.shift(LEFT * 2.5)

        # Labels for dimensions
        label_w = MathTex("4", color=BLUE).next_to(main_rect, DOWN)
        label_h = MathTex("3", color=GREEN).next_to(main_rect, LEFT)
        
        self.play(Create(main_rect))
        self.play(Write(label_w), Write(label_h))
        self.wait(1)

        # Fill with unit squares
        grid_squares = VGroup()
        # Calculate the starting corner (Upper Left)
        start_corner = main_rect.get_corner(UL)
        
        for i in range(rect_height):
            for j in range(rect_width):
                sq = Square(side_length=1.0, color=WHITE, stroke_width=2)
                sq.set_fill(YELLOW, opacity=0.4)
                # Position relative to top-left corner
                # Shift by 0.5 to align center of 1-unit square
                sq.move_to(start_corner + RIGHT * (j + 0.5) + DOWN * (i + 0.5))
                grid_squares.add(sq)

        # Animate the tiling process
        self.play(Create(grid_squares, lag_ratio=0.05, run_time=3))
        self.wait(1)

        # Show the calculation text
        calc_text = VGroup(
            Text("Area = Width × Height", font_size=32),
            MathTex(r"\text{Area} = 4 \times 3", color=YELLOW),
            MathTex(r"\text{Area} = 12 \text{ square units}", color=YELLOW)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.5).shift(RIGHT * 3)

        self.play(Write(calc_text[0]))
        self.wait(1)
        
        # Highlight dimensions while showing math
        self.play(Indicate(label_w), Indicate(label_h))
        self.play(Write(calc_text[1]))
        self.wait(1)
        self.play(Write(calc_text[2]))
        self.play(Circumscribe(calc_text[2]))
        self.wait(3)

        self.play(FadeOut(title), FadeOut(main_rect), FadeOut(grid_squares), 
                  FadeOut(label_w), FadeOut(label_h), FadeOut(calc_text))

    def summary(self):
        summary_title = Text("Summary", font_size=48, color=YELLOW).to_edge(UP)
        
        points = VGroup(
            Text("• Area is the 2D space inside a shape.", font_size=32),
            Text("• It is measured in square units.", font_size=32),
            Text("• For rectangles: Area = Length × Width.", font_size=32)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.8).shift(DOWN * 0.2)

        self.play(Write(summary_title))
        for point in points:
            self.play(FadeIn(point, shift=RIGHT * 0.3))
            self.wait(1)

        self.wait(3)
        # Final cleanup: Fade out all remaining VMobjects explicitly
        self.play(*[FadeOut(m) for m in self.mobjects])