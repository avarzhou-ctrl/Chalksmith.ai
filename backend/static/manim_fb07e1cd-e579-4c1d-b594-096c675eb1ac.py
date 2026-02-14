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
        """Main execution sequence."""
        self.show_intro()
        self.show_unit_square()
        self.show_rectangle_area()
        self.show_circle_area()
        self.show_summary()

    def show_intro(self):
        """Introduction to the concept of Area."""
        title = Text("Understanding Area", font_size=48, color=BLUE)
        subtitle = Text("The amount of space inside a 2D shape", font_size=32)
        subtitle.next_to(title, DOWN)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait(2)
        
        self.play(FadeOut(title), FadeOut(subtitle))

    def show_unit_square(self):
        """Explain the fundamental unit of area."""
        section_title = Text("1. The Unit Square", font_size=36, color=GOLD).to_edge(UP)
        self.play(Write(section_title))

        # Create a unit square
        sq = Square(side_length=2.0, color=WHITE)
        sq.set_fill(GREEN, opacity=0.5)
        
        # Labels for sides
        label_bottom = Text("1 unit", font_size=24).next_to(sq, DOWN)
        label_left = Text("1 unit", font_size=24).next_to(sq, LEFT)
        
        # Center label
        area_label = Text("Area = 1", font_size=32).move_to(sq.get_center())

        self.play(Create(sq))
        self.play(Write(label_bottom), Write(label_left))
        self.wait(1)
        self.play(Write(area_label))
        self.wait(2)

        # Clear section
        self.play(FadeOut(sq), FadeOut(label_bottom), FadeOut(label_left), FadeOut(area_label), FadeOut(section_title))

    def show_rectangle_area(self):
        """Demonstrate area of a rectangle by filling with units."""
        section_title = Text("2. Area of a Rectangle", font_size=36, color=GOLD).to_edge(UP)
        self.play(Write(section_title))

        # Create a 5x3 rectangle
        # Using scale of 0.8 for visibility
        rect = Rectangle(width=5.0, height=3.0, color=WHITE)
        rect.shift(LEFT * 1)
        
        base_label = Text("Width = 5", font_size=28).next_to(rect, DOWN)
        height_label = Text("Height = 3", font_size=28).next_to(rect, LEFT)

        self.play(Create(rect))
        self.play(Write(base_label), Write(height_label))
        self.wait(1)

        # Filling with unit squares
        squares = VGroup()
        for i in range(5): # columns
            for j in range(3): # rows
                s = Square(side_length=1.0, color=GREEN, stroke_width=1)
                s.set_fill(GREEN, opacity=0.3)
                # Align square to the bottom-left of the rectangle and shift
                # rectangle is 5x3, so its bottom left is rect.get_center() + [-2.5, -1.5, 0]
                start_pos = rect.get_center() + np.array([-2.5 + i + 0.5, -1.5 + j + 0.5, 0])
                s.move_to(start_pos)
                squares.add(s)

        # Animate filling in groups to save time but show concept
        self.play(LaggedStart(*[FadeIn(s) for s in squares], lag_ratio=0.05))
        self.wait(1)

        # Formula derivation
        formula = MathTex("Area", "=", "Width", "\\times", "Height", font_size=36)
        formula.set_color_by_tex("Width", BLUE)
        formula.set_color_by_tex("Height", RED)
        formula.to_edge(RIGHT).shift(UP * 1)

        calc = MathTex("Area", "=", "5", "\\times", "3", "=", "15", font_size=36)
        calc.next_to(formula, DOWN, buff=0.5)

        self.play(Write(formula))
        self.wait(1)
        self.play(Write(calc))
        self.wait(2)

        self.play(FadeOut(rect), FadeOut(squares), FadeOut(base_label), FadeOut(height_label), FadeOut(formula), FadeOut(calc), FadeOut(section_title))

    def show_circle_area(self):
        """Introduce Area of a Circle."""
        section_title = Text("3. Area of a Circle", font_size=36, color=GOLD).to_edge(UP)
        self.play(Write(section_title))

        circle = Circle(radius=2.0, color=WHITE)
        circle.set_fill(PURPLE, opacity=0.4)
        circle.shift(LEFT * 2)

        # Radius line
        center_dot = Dot(circle.get_center())
        radius_line = Line(circle.get_center(), circle.get_right(), color=YELLOW)
        radius_label = MathTex("r", font_size=32).next_to(radius_line, UP, buff=0.1)

        self.play(Create(circle), Create(center_dot))
        self.play(Create(radius_line), Write(radius_label))
        self.wait(1)

        # Formula
        formula = MathTex("Area", "=", "\\pi", "r^2", font_size=48)
        formula.next_to(circle, RIGHT, buff=1.5)
        
        explanation = Text("Where \u03c0 \u2248 3.14159", font_size=24)
        explanation.next_to(formula, DOWN, buff=0.5)

        self.play(Write(formula))
        self.play(FadeIn(explanation))
        self.wait(3)

        self.play(
            FadeOut(circle), FadeOut(center_dot), FadeOut(radius_line), 
            FadeOut(radius_label), FadeOut(formula), FadeOut(explanation), 
            FadeOut(section_title)
        )

    def show_summary(self):
        """Final summary of formulas."""
        summary_title = Text("Area Formulas Summary", font_size=40, color=GOLD).to_edge(UP)
        
        # Manual list using VGroup
        rect_text = MathTex("\\text{Rectangle: } A = w \\times h", font_size=36)
        square_text = MathTex("\\text{Square: } A = s^2", font_size=36)
        circle_text = MathTex("\\text{Circle: } A = \\pi r^2", font_size=36)
        triangle_text = MathTex("\\text{Triangle: } A = \\frac{1}{2} b \\times h", font_size=36)

        summary_group = VGroup(rect_text, square_text, circle_text, triangle_text).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        summary_group.center()

        self.play(Write(summary_title))
        self.play(FadeIn(summary_group))
        self.wait(3)
        
        outro = Text("Area is always measured in square units!", font_size=32, color=TEAL)
        outro.next_to(summary_group, DOWN, buff=1.0)
        self.play(Write(outro))
        self.wait(3)

        # Final cleanup
        self.play(FadeOut(summary_group), FadeOut(summary_title), FadeOut(outro))
        
        final_msg = Text("Thank You!", font_size=48, color=BLUE)
        self.play(GrowFromCenter(final_msg))
        self.wait(2)
        self.play(FadeOut(final_msg))