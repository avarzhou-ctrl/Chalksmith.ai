from manim import *
import numpy as np

# Compatibility layer and helper classes
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

class MainScene(Scene):
    def construct(self):
        self.intro_section()
        self.unit_square_concept()
        self.grid_method()
        self.formula_derivation()
        self.final_summary()

    def intro_section(self):
        # Title
        title = Text("Understanding Area", color=BLUE).scale(1.2)
        subtitle = Text("Area of Rectangles", color=WHITE).scale(0.8).next_to(title, DOWN)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(1)
        self.play(FadeOut(title), FadeOut(subtitle))

        # Definition
        definition_text = Text("Area is the amount of space inside a shape.", font_size=36)
        rect = Rectangle(width=5, height=3, color=YELLOW)
        
        self.play(Write(definition_text))
        self.play(definition_text.animate.to_edge(UP))
        self.play(Create(rect))
        
        # Filling the area
        rect_filled = rect.copy().set_fill(YELLOW, opacity=0.4)
        self.play(Transform(rect, rect_filled))
        self.wait(1)
        
        # Cleanup - Using *self.mobjects is safer than wrapping in VGroup
        self.play(FadeOut(*self.mobjects))

    def unit_square_concept(self):
        header = Text("We measure area using 'Unit Squares'", font_size=36).to_edge(UP)
        unit_square = Square(side_length=1.5, color=GREEN)
        unit_square.set_fill(GREEN, opacity=0.3)
        
        label_top = MathTex("1").next_to(unit_square, UP)
        label_side = MathTex("1").next_to(unit_square, LEFT)
        
        unit_text = Text("1 Square Unit", font_size=30).next_to(unit_square, DOWN, buff=0.5)

        self.play(Write(header))
        self.play(Create(unit_square))
        self.play(Write(label_top), Write(label_side))
        self.play(FadeIn(unit_text))
        self.wait(2)
        
        self.play(FadeOut(*self.mobjects))

    def grid_method(self):
        header = Text("Example: A 4x3 Rectangle", font_size=36).to_edge(UP)
        self.play(Write(header))

        # Create a 4x3 grid of squares
        grid = VGroup(*[Square(side_length=1.0, color=WHITE, stroke_width=2) for _ in range(12)])
        grid.arrange_in_grid(rows=3, cols=4, buff=0)
        grid.move_to(ORIGIN)

        # Draw the outline
        outline = Rectangle(width=4, height=3, color=BLUE, stroke_width=4)
        outline.move_to(grid.get_center())
        
        self.play(Create(outline))
        self.wait(0.5)
        
        # Animate the squares filling the rectangle
        self.play(LaggedStart(*[FadeIn(sq) for sq in grid], lag_ratio=0.05))
        
        # Count the squares
        counter_text = Text("Counting squares: ", font_size=32).to_edge(DOWN).shift(LEFT * 0.5)
        count_val = 0
        counter_num = Integer(count_val).next_to(counter_text, RIGHT)
        counter_group = VGroup(counter_text, counter_num).center().to_edge(DOWN)
        
        self.play(Write(counter_group))

        for i, sq in enumerate(grid):
            self.play(
                sq.animate.set_fill(BLUE, opacity=0.5),
                counter_num.animate.set_value(i + 1),
                run_time=0.15
            )
        
        self.wait(1)
        result = Text("Area = 12 Square Units", color=YELLOW).next_to(grid, RIGHT, buff=0.5).scale(0.7)
        self.play(Write(result))
        self.wait(2)

        self.play(FadeOut(*self.mobjects))

    def formula_derivation(self):
        # Create rectangle
        rect = Rectangle(width=5, height=3, color=WHITE)
        rect.move_to(LEFT * 3)
        
        # Labels
        length_label = MathTex("Length = 5").next_to(rect, DOWN)
        width_label = MathTex("Width = 3").next_to(rect, LEFT).rotate(90 * DEGREES).shift(LEFT*0.2)
        
        self.play(Create(rect))
        self.play(Write(length_label), Write(width_label))
        self.wait(1)
        
        # The Formula
        # Index:    0      1    2    3     4
        formula = MathTex("Area", "=", "l", "\\times", "w").scale(1.2)
        formula.to_edge(UP).shift(RIGHT * 2)
        
        self.play(Write(formula))
        self.play(Indicate(formula))
        self.wait(1)

        # Substitution
        # Index:   0      1    2    3     4
        step1 = MathTex("Area", "=", "5", "\\times", "3").scale(1.2)
        step1.next_to(formula, DOWN, buff=0.8)
        
        # Animate values from labels to formula
        self.play(
            TransformFromCopy(formula[0:2], step1[0:2]),
            TransformFromCopy(length_label, step1[2]),
            TransformFromCopy(formula[3], step1[3]),
            TransformFromCopy(width_label, step1[4])
        )
        self.wait(1)

        # Final Calculation
        step2 = MathTex("Area", "=", "15").scale(1.2)
        step2.next_to(step1, DOWN, buff=0.8)
        step2.set_color(YELLOW)
        
        self.play(Write(step2))
        self.play(Circumscribe(step2))
        self.wait(2)

        self.play(FadeOut(*self.mobjects))

    def final_summary(self):
        summary_title = Text("Summary", color=BLUE).to_edge(UP)
        
        point1 = Text("1. Area is the space inside a shape.", font_size=30)
        point2 = Text("2. It is measured in square units.", font_size=30)
        point3 = Text("3. Formula: Area = Length x Width", font_size=30, color=YELLOW)
        
        summary_group = VGroup(point1, point2, point3).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        summary_group.center()

        self.play(Write(summary_title))
        for point in summary_group:
            self.play(FadeIn(point, shift=RIGHT))
            self.wait(0.5)
        
        self.wait(2)
        
        self.play(FadeOut(*self.mobjects))
        thanks = Text("Happy Learning!", color=WHITE).scale(1.5)
        self.play(GrowFromCenter(thanks))
        self.wait(2)
        self.play(FadeOut(thanks))