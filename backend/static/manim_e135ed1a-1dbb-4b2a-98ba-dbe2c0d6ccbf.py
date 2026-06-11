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
        """
        Main execution method calling sub-sections of the lesson.
        """
        self.show_intro()
        self.define_unit_square()
        self.explain_rectangle_area()
        self.show_formula()
        self.show_summary()

    def show_intro(self):
        """
        Introduces the concept of Area.
        """
        title = Text("Understanding Area", font_size=48, color=BLUE)
        definition = Text("Area is the amount of space inside a 2D shape.", font_size=32)
        
        group = VGroup(title, definition).arrange(DOWN, buff=0.5)
        
        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(definition, shift=UP))
        self.wait(2)
        
        self.play(FadeOut(group))

    def define_unit_square(self):
        """
        Explains that area is measured in unit squares.
        """
        header = Text("The Unit Square", font_size=36, color=YELLOW).to_edge(UP)
        
        # Create a single unit square
        unit_sq = Square(side_length=2.0, color=WHITE)
        unit_sq.set_fill(BLUE, opacity=0.5)
        
        # Dimensions for the square
        label_side1 = MathTex("1 \\text{ unit}").next_to(unit_sq, LEFT)
        label_side2 = MathTex("1 \\text{ unit}").next_to(unit_sq, DOWN)
        
        inner_text = Text("1 Square Unit", font_size=24).move_to(unit_sq.get_center())
        
        self.play(Write(header))
        self.play(Create(unit_sq))
        self.play(Write(label_side1), Write(label_side2))
        self.wait(1)
        self.play(Write(inner_text))
        self.wait(2)
        
        # Clear section
        self.play(FadeOut(header), FadeOut(unit_sq), FadeOut(label_side1), FadeOut(label_side2), FadeOut(inner_text))

    def explain_rectangle_area(self):
        """
        Shows how unit squares fill a rectangle to determine area.
        """
        header = Text("Counting Units", font_size=36, color=YELLOW).to_edge(UP)
        self.play(Write(header))
        
        # Create a 4x3 grid of squares
        rows = 3
        cols = 4
        square_size = 1.0
        
        grid = VGroup()
        for r in range(rows):
            for c in range(cols):
                sq = Square(side_length=square_size, color=GRAY)
                sq.move_to(np.array([c * square_size, r * square_size, 0]))
                grid.add(sq)
        
        grid.center()
        
        # Outer boundary of the rectangle
        rect_outline = Rectangle(width=cols * square_size, height=rows * square_size, color=WHITE, stroke_width=4)
        rect_outline.move_to(grid.get_center())
        
        # Dimensions
        dim_w = MathTex("4 \\text{ units}").next_to(rect_outline, DOWN)
        dim_h = MathTex("3 \\text{ units}").next_to(rect_outline, LEFT)
        
        self.play(Create(rect_outline))
        self.play(Write(dim_w), Write(dim_h))
        self.wait(1)
        
        # Filling the squares one by one
        counter = 0
        counter_text = Text("Count: 0", font_size=36).to_edge(RIGHT, buff=1)
        self.play(Write(counter_text))
        
        for square in grid:
            counter += 1
            new_counter_text = Text(f"Count: {counter}", font_size=36).to_edge(RIGHT, buff=1)
            self.play(
                square.animate.set_fill(TEAL, opacity=0.7),
                Transform(counter_text, new_counter_text),
                run_time=0.15
            )
        
        self.wait(1)
        
        total_msg = Text("Total Area = 12 Square Units", font_size=32, color=GREEN).next_to(rect_outline, UP)
        self.play(Write(total_msg))
        self.wait(2)
        
        # Clear section
        self.play(FadeOut(grid), FadeOut(rect_outline), FadeOut(dim_w), FadeOut(dim_h), FadeOut(counter_text), FadeOut(total_msg), FadeOut(header))

    def show_formula(self):
        """
        Derives and presents the formula A = L x W.
        """
        title = Text("The General Formula", font_size=36, color=YELLOW).to_edge(UP)
        self.play(Write(title))
        
        # Visual rectangle
        rect = Rectangle(width=5, height=3, color=BLUE)
        rect.set_fill(BLUE, opacity=0.2)
        
        l_label = MathTex("Length (L)").next_to(rect, DOWN)
        w_label = MathTex("Width (W)").next_to(rect, LEFT)
        
        formula = MathTex("Area", "=", "Length", "\\times", "Width")
        formula.set_color_by_tex("Area", GREEN)
        formula.set_color_by_tex("Length", WHITE)
        formula.set_color_by_tex("Width", WHITE)
        formula.shift(UP * 2) # Position below title, above rect
        
        short_formula = MathTex("A", "=", "L", "\\times", "W")
        short_formula.set_color_by_tex("A", GREEN)
        short_formula.scale(1.5).move_to(rect.get_center())
        
        self.play(Create(rect))
        self.play(Write(l_label), Write(w_label))
        self.wait(1)
        
        # Move formula to position
        self.play(Write(formula))
        self.wait(1)
        
        # Show shorthand inside the rectangle
        self.play(Write(short_formula))
        self.wait(2)
        
        self.play(FadeOut(rect), FadeOut(l_label), FadeOut(w_label), FadeOut(formula), FadeOut(short_formula), FadeOut(title))

    def show_summary(self):
        """
        Final summary of the key points.
        """
        summary_title = Text("Key Takeaways", font_size=44, color=GOLD).shift(UP * 2)
        
        line1 = Text("1. Area is the space inside a shape.", font_size=32)
        line2 = Text("2. It is measured in unit squares.", font_size=32)
        line3 = Text("3. For rectangles: Area = Length x Width.", font_size=32)
        
        points = VGroup(line1, line2, line3).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        points.next_to(summary_title, DOWN, buff=1)
        
        self.play(Write(summary_title))
        for point in points:
            self.play(FadeIn(point, shift=RIGHT))
            self.wait(1)
            
        self.wait(2)
        
        # Outro
        self.play(FadeOut(points), FadeOut(summary_title))
        thanks = Text("Thanks for Learning!", font_size=48, color=BLUE)
        self.play(Write(thanks))
        self.wait(2)
        self.play(FadeOut(thanks))

# Execution command: manim -pql scene.py MainScene