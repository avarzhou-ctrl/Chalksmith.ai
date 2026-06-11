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
        self.intro_section()
        self.unit_squares_section()
        self.rectangle_area_section()
        self.circle_area_section()
        self.outro_section()

    def intro_section(self):
        title = Text("Understanding Area", font_size=48, color=BLUE)
        subtitle = Text("Measuring 2D Space", font_size=32, color=GRAY).next_to(title, DOWN)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait(2)
        
        self.play(FadeOut(title), FadeOut(subtitle))

    def unit_squares_section(self):
        concept_text = Text("Area is measured in 'unit squares'", font_size=36).to_edge(UP)
        self.play(Write(concept_text))
        
        # Create a single unit square
        unit_sq = Square(side_length=1, color=YELLOW)
        label = Text("1 unit", font_size=24).next_to(unit_sq, DOWN)
        side_label = Text("1 unit", font_size=24).next_to(unit_sq, LEFT)
        
        self.play(Create(unit_sq))
        self.play(FadeIn(label), FadeIn(side_label))
        self.wait(1)
        
        unit_group = VGroup(unit_sq, label, side_label)
        self.play(unit_group.animate.scale(0.5).to_edge(LEFT, buff=1))
        
        # Create a grid representing a larger shape
        grid_rect = Rectangle(width=4, height=3, color=WHITE).shift(RIGHT * 2)
        grid = VGroup()
        for i in range(4):
            for j in range(3):
                sq = Square(side_length=1).move_to(grid_rect.get_corner(DL) + i*RIGHT + j*UP + 0.5*RIGHT + 0.5*UP)
                sq.set_stroke(BLUE, opacity=0.5)
                grid.add(sq)
        
        self.play(Create(grid_rect))
        self.wait(0.5)
        
        # Fill grid with squares
        self.play(LaggedStart(*[FadeIn(sq) for sq in grid], lag_ratio=0.1))
        
        count_text = Text("Total Area = 12 units²", font_size=36, color=YELLOW).next_to(grid_rect, DOWN)
        self.play(Write(count_text))
        self.wait(2)
        
        self.play(FadeOut(concept_text), FadeOut(unit_group), FadeOut(grid), FadeOut(grid_rect), FadeOut(count_text))

    def rectangle_area_section(self):
        title = Text("The Rectangle Formula", font_size=40, color=BLUE).to_edge(UP)
        self.play(Write(title))
        
        rect = Rectangle(width=5, height=3, color=WHITE).shift(UP * 0.5)
        self.play(Create(rect))
        
        # Dimensions
        base_line = Line(rect.get_corner(DL), rect.get_corner(DR), color=ORANGE)
        height_line = Line(rect.get_corner(DL), rect.get_corner(UL), color=GREEN)
        
        base_label = MathTex("w", color=ORANGE).next_to(rect, DOWN)
        height_label = MathTex("h", color=GREEN).next_to(rect, LEFT)
        
        self.play(Create(base_line), FadeIn(base_label))
        self.play(Create(height_line), FadeIn(height_label))
        self.wait(1)
        
        # Area formula
        formula = MathTex("Area", "=", "w", "\\times", "h", font_size=60)
        formula.set_color_by_tex("w", ORANGE)
        formula.set_color_by_tex("h", GREEN)
        formula.next_to(rect, DOWN, buff=1.5)
        
        self.play(rect.animate.set_fill(BLUE, opacity=0.3))
        self.play(Write(formula))
        self.play(Indicate(formula))
        self.wait(2)
        
        self.play(FadeOut(title), FadeOut(rect), FadeOut(base_line), FadeOut(height_line), 
                  FadeOut(base_label), FadeOut(height_label), FadeOut(formula))

    def circle_area_section(self):
        title = Text("Area of a Circle", font_size=40, color=BLUE).to_edge(UP)
        self.play(Write(title))
        
        circle = Circle(radius=2, color=WHITE).shift(LEFT * 2)
        radius_line = Line(circle.get_center(), circle.get_right(), color=RED)
        radius_label = MathTex("r", color=RED).next_to(radius_line, UP)
        
        self.play(Create(circle), Create(radius_line), Write(radius_label))
        self.play(circle.animate.set_fill(PURPLE, opacity=0.3))
        
        formula = MathTex("Area", "=", "\\pi", "r", "^2", font_size=60)
        formula.set_color_by_tex("r", RED)
        formula.shift(RIGHT * 3)
        
        self.play(Write(formula))
        
        explanation = Text("π (pi) ≈ 3.14159", font_size=24, color=GRAY).next_to(formula, DOWN, buff=0.5)
        self.play(FadeIn(explanation))
        self.wait(2)
        
        self.play(FadeOut(VGroup(*self.mobjects)))

    def outro_section(self):
        summary = Text("Summary", font_size=48, color=BLUE).shift(UP * 2)
        line1 = Text("- Area measures surface space", font_size=32).shift(UP * 0.5)
        line2 = Text("- Rectangles: Width x Height", font_size=32).next_to(line1, DOWN, buff=0.5)
        line3 = Text("- Circles: π × r²", font_size=32).next_to(line2, DOWN, buff=0.5)
        
        group = VGroup(summary, line1, line2, line3).center()
        
        self.play(Write(summary))
        self.wait(0.5)
        self.play(FadeIn(line1))
        self.play(FadeIn(line2))
        self.play(FadeIn(line3))
        self.wait(3)
        
        # Final cleanup
        self.play(FadeOut(VGroup(*self.mobjects)))

if __name__ == "__main__":
    import os
    os.system("manim -pql scene.py MainScene")