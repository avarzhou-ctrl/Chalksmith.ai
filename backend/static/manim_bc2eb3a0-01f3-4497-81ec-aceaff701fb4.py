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
        self.place_values_section()
        self.conversion_example()
        self.hardware_analogy()
        self.conclusion_section()

    def intro_section(self):
        title = Text("Understanding Binary", font_size=48, color=BLUE)
        subtitle = Text("The Language of Computers", font_size=32).next_to(title, DOWN)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait(2)
        
        decimal_text = Text("Decimal (Base 10): 0, 1, 2, 3, 4, 5, 6, 7, 8, 9", font_size=28).shift(UP * 0.5)
        binary_text = Text("Binary (Base 2): 0, 1", font_size=28, color=YELLOW).next_to(decimal_text, DOWN, buff=0.5)
        
        self.play(FadeOut(title), FadeOut(subtitle))
        self.play(Write(decimal_text))
        self.wait(1)
        self.play(Write(binary_text))
        self.wait(2)
        
        self.play(FadeOut(Group(*self.mobjects)))

    def place_values_section(self):
        header = Text("Binary Place Values", font_size=36, color=BLUE).to_edge(UP)
        self.play(Write(header))

        # Create Boxes for bits
        boxes = VGroup(*[Square(side_length=1.5) for _ in range(4)]).arrange(RIGHT, buff=0.2).shift(UP * 0.5)
        
        # Powers of 2 labels
        powers = VGroup(
            MathTex("2^3"), MathTex("2^2"), MathTex("2^1"), MathTex("2^0")
        )
        # Decimal values labels
        values = VGroup(
            Text("8", color=YELLOW), Text("4", color=YELLOW), 
            Text("2", color=YELLOW), Text("1", color=YELLOW)
        )

        for i, box in enumerate(boxes):
            powers[i].move_to(box.get_center())
            values[i].next_to(box, DOWN)
            
        self.play(Create(boxes))
        self.wait(0.5)
        self.play(Write(powers))
        self.wait(1)
        self.play(FadeIn(values, shift=UP))
        self.wait(2)

        self.play(FadeOut(Group(*self.mobjects)))

    def conversion_example(self):
        header = Text("Example: Converting 1011 to Decimal", font_size=36, color=BLUE).to_edge(UP)
        self.play(Write(header))

        # Binary digits
        bits = VGroup(
            Text("1", font_size=60),
            Text("0", font_size=60),
            Text("1", font_size=60),
            Text("1", font_size=60)
        ).arrange(RIGHT, buff=1.2).shift(UP * 0.5)

        # Place value labels
        labels = VGroup(
            Text("8s", font_size=24, color=GRAY),
            Text("4s", font_size=24, color=GRAY),
            Text("2s", font_size=24, color=GRAY),
            Text("1s", font_size=24, color=GRAY)
        )
        
        for i, bit in enumerate(bits):
            labels[i].next_to(bit, DOWN)

        self.play(Write(bits))
        self.play(FadeIn(labels))
        self.wait(1)

        # Calculation steps
        calc_text = MathTex(
            "1 \\times 8", "+", "0 \\times 4", "+", "1 \\times 2", "+", "1 \\times 1",
            font_size=36
        ).shift(DOWN * 1.5)
        
        self.play(Write(calc_text))
        self.wait(1)

        final_sum = MathTex("8 + 0 + 2 + 1 = 11", font_size=48, color=YELLOW).shift(DOWN * 2.5)
        self.play(Write(final_sum))
        self.wait(3)

        self.play(FadeOut(Group(*self.mobjects)))

    def hardware_analogy(self):
        header = Text("Computers use Switches (Transistors)", font_size=36, color=BLUE).to_edge(UP)
        self.play(Write(header))

        # Create two switches
        sw_off_box = Rectangle(height=2, width=1.2, color=WHITE)
        sw_on_box = Rectangle(height=2, width=1.2, color=WHITE)
        
        switches = VGroup(sw_off_box, sw_on_box).arrange(RIGHT, buff=2)
        
        off_label = Text("OFF (0)", color=RED, font_size=24).next_to(sw_off_box, DOWN)
        on_label = Text("ON (1)", color=GREEN, font_size=24).next_to(sw_on_box, DOWN)

        # Visual state inside the "switch"
        off_indicator = Circle(radius=0.3, color=RED, fill_opacity=0).move_to(sw_off_box.get_center())
        on_indicator = Circle(radius=0.3, color=GREEN, fill_opacity=1).move_to(sw_on_box.get_center())

        self.play(Create(switches))
        self.play(FadeIn(off_label), FadeIn(on_label))
        self.play(Create(off_indicator), FadeIn(on_indicator))
        self.wait(2)

        explanation = Text(
            "Billions of these switches represent complex data.",
            font_size=28
        ).shift(DOWN * 2.5)
        
        self.play(Write(explanation))
        self.wait(3)

        self.play(FadeOut(Group(*self.mobjects)))

    def conclusion_section(self):
        summary_title = Text("Binary Summary", color=BLUE).shift(UP * 2)
        
        point1 = Text("• Base 2 system (0 and 1)", font_size=32)
        point2 = Text("• Each digit is a 'bit'", font_size=32).next_to(point1, DOWN, aligned_edge=LEFT)
        point3 = Text("• Computers use it for hardware efficiency", font_size=32).next_to(point2, DOWN, aligned_edge=LEFT)
        
        points = VGroup(point1, point2, point3).center()

        self.play(Write(summary_title))
        for point in points:
            self.play(FadeIn(point, shift=RIGHT))
            self.wait(1)
        
        self.wait(2)
        self.play(FadeOut(Group(*self.mobjects)))
        
        final_msg = Text("Binary: The foundation of the digital world.", font_size=36, color=YELLOW)
        self.play(Write(final_msg))
        self.wait(2)
        self.play(FadeOut(final_msg))