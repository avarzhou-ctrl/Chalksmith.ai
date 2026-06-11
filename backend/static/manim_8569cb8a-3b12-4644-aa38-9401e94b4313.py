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



# Standard Color Definitions
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

class MainScene(Scene):
    def construct(self):
        self.intro_section()
        self.square_section()
        self.rectangle_section()
        self.summary_section()

    def intro_section(self):
        # Title and Definition
        title = Text("What is Perimeter?", color=BLUE).scale(1.2)
        definition = Text(
            "The total distance around the outside of a shape.",
            font_size=28
        ).next_to(title, DOWN)
        
        intro_grp = VGroup(title, definition).center()
        
        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(definition, shift=UP))
        self.wait(2)
        
        self.play(FadeOut(intro_grp))

    def square_section(self):
        # Section Header
        header = Text("Example 1: The Square", color=YELLOW).to_edge(UP)
        self.play(Write(header))
        
        # Create Square
        side_length = 3
        square = Square(side_length=side_length, color=WHITE)
        square.shift(LEFT * 2)
        
        # Labels for sides
        s1 = MathTex("3", color=ORANGE).next_to(square, UP)
        s2 = MathTex("3", color=ORANGE).next_to(square, RIGHT)
        s3 = MathTex("3", color=ORANGE).next_to(square, DOWN)
        s4 = MathTex("3", color=ORANGE).next_to(square, LEFT)
        side_labels = VGroup(s1, s2, s3, s4)
        
        self.play(Create(square))
        self.play(Write(side_labels))
        self.wait(1)
        
        # Trace the perimeter
        tracing_rect = square.copy().set_color(YELLOW).set_stroke(width=6)
        
        calc_text = MathTex(
            "P", "=", "3", "+", "3", "+", "3", "+", "3",
            color=WHITE
        ).shift(RIGHT * 3 + UP)
        
        result_text = MathTex(
            "P", "=", "12",
            color=GREEN
        ).next_to(calc_text, DOWN, buff=0.5)
        
        # Animation: Trace sides and add numbers
        self.play(Create(tracing_rect), run_time=3, rate_func=linear)
        self.play(Write(calc_text))
        self.wait(1)
        self.play(ReplacementTransform(calc_text.copy(), result_text))
        self.wait(2)
        
        # Cleanup
        self.play(
            FadeOut(square), 
            FadeOut(side_labels), 
            FadeOut(header), 
            FadeOut(calc_text), 
            FadeOut(result_text), 
            FadeOut(tracing_rect)
        )

    def rectangle_section(self):
        # Section Header
        header = Text("Example 2: The Rectangle", color=YELLOW).to_edge(UP)
        self.play(Write(header))
        
        # Create Rectangle
        rect = Rectangle(width=5, height=2, color=WHITE).shift(LEFT * 1.5)
        
        # Labels
        w1 = MathTex("5", color=ORANGE).next_to(rect, UP)
        w2 = MathTex("5", color=ORANGE).next_to(rect, DOWN)
        h1 = MathTex("2", color=ORANGE).next_to(rect, LEFT)
        h2 = MathTex("2", color=ORANGE).next_to(rect, RIGHT)
        labels = VGroup(w1, w2, h1, h2)
        
        self.play(Create(rect))
        self.play(Write(labels))
        self.wait(1)
        
        # Equation
        formula = MathTex(
            "P = 2(l + w)",
            color=WHITE
        ).to_edge(RIGHT).shift(UP * 1)
        
        calc = MathTex(
            "P = 2(5 + 2)",
            color=WHITE
        ).next_to(formula, DOWN, buff=0.5)
        
        result = MathTex(
            "P = 14",
            color=GREEN
        ).next_to(calc, DOWN, buff=0.5)
        
        self.play(Write(formula))
        self.wait(1)
        self.play(Write(calc))
        self.wait(1)
        # Fixed: Corrected variable reference from calc_text to calc
        self.play(ReplacementTransform(calc.copy(), result))
        self.wait(2)
        
        # Cleanup
        self.play(
            FadeOut(rect), 
            FadeOut(labels), 
            FadeOut(header), 
            FadeOut(formula), 
            FadeOut(calc), 
            FadeOut(result)
        )

    def summary_section(self):
        # Final Summary
        summary_title = Text("Key Takeaways", color=BLUE).to_edge(UP)
        
        point1 = Text("1. Perimeter is the boundary distance.", font_size=32)
        point2 = Text("2. Add all side lengths together.", font_size=32)
        point3 = Text("3. Measured in linear units (m, cm, inches).", font_size=32)
        
        points = VGroup(point1, point2, point3).arrange(DOWN, aligned_edge=LEFT, buff=0.5).center()
        
        self.play(Write(summary_title))
        for point in points:
            self.play(FadeIn(point, shift=RIGHT))
            self.wait(1)
            
        self.wait(2)
        
        # Final Clean up - Fixed: Avoid VGroup(*self.mobjects) to prevent VMobject type errors
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        
        final_note = Text("Perimeter is simple!", color=GOLD).scale(1.5)
        self.play(GrowFromCenter(final_note))
        self.wait(2)
        self.play(FadeOut(final_note))