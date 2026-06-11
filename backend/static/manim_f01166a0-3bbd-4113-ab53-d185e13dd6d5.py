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
        self.intro()
        self.unit_square()
        self.rectangle_area()
        self.triangle_area()
        self.summary()

    def intro(self):
        # Introduction Title
        title = Text("Understanding Area", font_size=48, color=BLUE)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))

        # Definition
        def_text = Text("Area is the amount of 2D space inside a boundary.", font_size=32)
        self.play(FadeIn(def_text))
        self.wait(2)
        self.play(def_text.animate.shift(UP * 1.5))

        # Comparing 1D and 2D
        line = Line(LEFT * 1.5, RIGHT * 1.5, color=YELLOW)
        line_label = Text("Length (1D)", font_size=24).next_to(line, DOWN)
        
        square = Square(side_length=2.5, color=GREEN, fill_opacity=0.5)
        square_label = Text("Area (2D)", font_size=24).next_to(square, DOWN)
        
        # Group and arrange
        shape_group = VGroup(
            VGroup(line, line_label),
            VGroup(square, square_label)
        ).arrange(RIGHT, buff=3).shift(DOWN * 0.5)
        
        self.play(Create(line), Write(line_label))
        self.wait(1)
        self.play(Create(square), Write(square_label))
        self.wait(3)
        
        # Cleanup using Group to avoid TypeError with non-VMobjects
        self.play(FadeOut(Group(*self.mobjects)))

    def unit_square(self):
        # Section Title
        title = Text("The Unit Square", font_size=48, color=BLUE).to_edge(UP)
        self.play(Write(title))
        
        # Create a unit square
        sq = Square(side_length=2, color=ORANGE, fill_opacity=0.5)
        w_label = Text("1 unit", font_size=24).next_to(sq, DOWN)
        h_label = Text("1 unit", font_size=24).next_to(sq, LEFT)
        
        self.play(Create(sq))
        self.play(Write(w_label), Write(h_label))
        self.wait(1)
        
        # Area text
        area_text = Text("Area = 1 square unit", font_size=32, color=YELLOW).next_to(sq, UP, buff=0.5)
        self.play(FadeIn(area_text))
        self.wait(3)
        
        # Cleanup
        self.play(FadeOut(Group(*self.mobjects)))
        
    def rectangle_area(self):
        # Section Title
        title = Text("Area of a Rectangle", font_size=48, color=BLUE).to_edge(UP)
        self.play(Write(title))
        
        # Create a 4x3 grid of squares
        grid = VGroup()
        for x in range(4):
            for y in range(3):
                cell = Square(
                    side_length=1, 
                    stroke_color=WHITE, 
                    stroke_width=2, 
                    fill_color=TEAL, 
                    fill_opacity=0.6
                )
                cell.move_to(RIGHT * (x - 1.5) + UP * (y - 1))
                grid.add(cell)
        
        grid.shift(DOWN * 1.5)
        
        # Labels for width and height
        w_label = Text("4 units", font_size=24).next_to(grid, DOWN)
        h_label = Text("3 units", font_size=24).next_to(grid, LEFT)
        
        self.play(Create(grid, lag_ratio=0.1))
        self.play(Write(w_label), Write(h_label))
        self.wait(1)
        
        # Formulas
        formula = MathTex(r"\text{Area} = \text{width} \times \text{height}").next_to(title, DOWN, buff=0.5)
        calc = MathTex(r"\text{Area} = 4 \times 3 = 12 \text{ square units}", color=YELLOW).next_to(formula, DOWN, buff=0.3)
        
        self.play(Write(formula))
        self.wait(1)
        self.play(Write(calc))
        self.wait(3)
        
        # Cleanup
        self.play(FadeOut(Group(*self.mobjects)))

    def triangle_area(self):
        # Section Title
        title = Text("Area of a Triangle", font_size=48, color=BLUE).to_edge(UP)
        self.play(Write(title))
        
        # Draw bounding rectangle
        rect = Rectangle(width=4, height=3, color=GRAY, fill_opacity=0)
        rect.shift(DOWN * 1.5)
        self.play(Create(rect))
        
        # Define corners for triangles
        p_dl = rect.get_corner(DL)
        p_dr = rect.get_corner(DR)
        p_ul = rect.get_corner(UL)
        p_ur = rect.get_corner(UR)
        
        # Draw the primary triangle
        tri1 = Polygon(p_dl, p_dr, p_ul, color=GREEN, fill_opacity=0.6)
        # Draw the secondary (complementary) triangle
        tri2 = Polygon(p_ul, p_dr, p_ur, color=RED, fill_opacity=0.2)
        
        self.play(Create(tri1))
        self.wait(1)
        
        # Labels
        b_label = Text("base (b)", font_size=24).next_to(rect, DOWN)
        h_label = Text("height (h)", font_size=24).next_to(rect, LEFT)
        self.play(Write(b_label), Write(h_label))
        self.wait(1)
        
        # Show that triangle is half of rectangle
        self.play(Create(tri2))
        
        note = Text("A triangle is exactly half of a rectangle.", font_size=28).next_to(title, DOWN, buff=0.5)
        self.play(FadeIn(note))
        self.wait(1)
        
        # Formula
        formula = MathTex(r"\text{Area} = \frac{1}{2} \times \text{base} \times \text{height}", color=YELLOW).next_to(note, DOWN, buff=0.3)
        self.play(Write(formula))
        self.wait(3)
        
        # Cleanup
        self.play(FadeOut(Group(*self.mobjects)))

    def summary(self):
        # Section Title
        title = Text("Summary", font_size=48, color=BLUE).to_edge(UP)
        self.play(Write(title))
        
        # Square Group
        s = Square(side_length=1.5, color=ORANGE, fill_opacity=0.6)
        s_f = MathTex(r"A = s^2", font_size=36)
        s_group = VGroup(s, s_f).arrange(DOWN, buff=0.5)
        
        # Rectangle Group
        r = Rectangle(width=2.5, height=1.5, color=TEAL, fill_opacity=0.6)
        r_f = MathTex(r"A = w \times h", font_size=36)
        r_group = VGroup(r, r_f).arrange(DOWN, buff=0.5)
        
        # Triangle Group
        t = Polygon(LEFT, RIGHT, UP*1.5, color=GREEN, fill_opacity=0.6)
        t_f = MathTex(r"A = \frac{1}{2} \times b \times h", font_size=36)
        t_group = VGroup(t, t_f).arrange(DOWN, buff=0.5)
        
        # Arrange all shapes
        shapes = VGroup(s_group, r_group, t_group).arrange(RIGHT, buff=1.5).shift(DOWN * 0.5)
        
        self.play(FadeIn(shapes, shift=UP))
        self.wait(4)
        
        # Final Cleanup
        self.play(FadeOut(Group(*self.mobjects)))