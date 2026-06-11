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
        self.anatomy_of_error()
        self.resolving_the_issue()
        self.summary_section()

    def intro_section(self):
        # Title and Error Display
        title = Text("Understanding Parsing Errors", color=BLUE).scale(0.8)
        title.to_edge(UP)
        
        error_bg = Rectangle(height=1.5, width=9, color=RED, fill_opacity=0.1)
        error_msg = Text(
            "Internal Error: Failed to parse status update.",
            color=RED,
            font_size=32
        )
        error_group = VGroup(error_bg, error_msg).center()

        self.play(Write(title))
        self.play(Create(error_bg), FadeIn(error_msg))
        self.wait(2)
        
        explanation = Paragraph(
            "This error occurs when a system receives a data",
            "packet that does not match its expected format.",
            alignment="center",
            font_size=28
        ).next_to(error_group, DOWN, buff=0.5)
        
        self.play(Write(explanation))
        self.wait(2)
        self.play(FadeOut(title, error_group, explanation))

    def anatomy_of_error(self):
        # Visualizing the Flow
        source = Rectangle(width=3, height=1.5, color=WHITE).shift(LEFT * 4)
        source_label = Text("Service A", font_size=24).move_to(source.get_center())
        
        parser = Rectangle(width=3, height=1.5, color=WHITE).shift(RIGHT * 4)
        parser_label = Text("Parser B", font_size=24).move_to(parser.get_center())
        
        arrow = Arrow(source.get_right(), parser.get_left(), buff=0.2)
        
        self.play(Create(source), Write(source_label))
        self.play(Create(parser), Write(parser_label))
        self.play(GrowArrow(arrow))
        
        # Data Packet
        packet = Square(side_length=0.6, color=YELLOW, fill_opacity=0.8)
        packet_text = Text("DATA", font_size=16, color=BLACK).move_to(packet.get_center())
        data_packet = VGroup(packet, packet_text).move_to(source.get_center())
        
        self.play(data_packet.animate.move_to(arrow.get_center()))
        
        # Malformed change
        malformed_marker = Text("?", color=RED).scale(2).move_to(packet.get_center())
        self.play(
            packet.animate.set_color(RED),
            Transform(packet_text, malformed_marker)
        )
        self.play(data_packet.animate.move_to(parser.get_center()))
        
        # Error Flash
        failure_x = Text("X", color=RED).scale(3).move_to(parser.get_center())
        self.play(Indicate(parser, color=RED), FadeIn(failure_x))
        
        reason_text = VGroup(
            Text("1. Schema Mismatch", font_size=24, color=YELLOW),
            Text("2. Incomplete Transmission", font_size=24, color=YELLOW),
            Text("3. Unexpected Type", font_size=24, color=YELLOW)
        ).arrange(DOWN, aligned_edge=LEFT).next_to(arrow, DOWN, buff=1)
        
        self.play(Write(reason_text))
        self.wait(2)
        self.play(FadeOut(source, source_label, parser, parser_label, arrow, data_packet, failure_x, reason_text))

    def resolving_the_issue(self):
        step_title = Text("The Fix: Validation Layer", color=GREEN).to_edge(UP)
        self.play(Write(step_title))

        # Code-like representation using Primitives
        code_box = RoundedRectangle(height=4, width=7, color=GRAY)
        
        line1 = MathTex(r"\text{if } \text{is\_valid}(\text{data}):", color=WHITE)
        line2 = MathTex(r"\text{    process\_update}(\text{data})", color=GREEN)
        line3 = MathTex(r"\text{else:}", color=WHITE)
        line4 = MathTex(r"\text{    log\_error}(\text{''Malformed Data''})", color=RED)
        
        code_lines = VGroup(line1, line2, line3, line4).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        code_lines.move_to(code_box.get_center())
        
        self.play(Create(code_box))
        self.play(Write(code_lines))
        self.wait(2)

        # Highlighting the Logic
        highlight = SurroundingRectangle(line1, color=YELLOW)
        self.play(Create(highlight))
        self.play(Indicate(line1))
        self.wait(1)
        
        self.play(FadeOut(code_box, code_lines, highlight, step_title))

    def summary_section(self):
        summary_title = Text("Key Takeaways", color=BLUE).to_edge(UP)
        
        item1 = Text("• Parsing errors signify a structure mismatch.", font_size=28)
        item2 = Text("• Always validate incoming status updates.", font_size=28)
        item3 = Text("• Implement error logging for easier debugging.", font_size=28)
        
        summary_list = VGroup(item1, item2, item3).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        summary_list.center()
        
        self.play(Write(summary_title))
        for item in summary_list:
            self.play(FadeIn(item, shift=RIGHT * 0.5))
            self.wait(1)
            
        self.wait(2)
        # Fixed: Using Group instead of VGroup to handle potential non-VMobject elements
        self.play(FadeOut(Group(*self.mobjects)))

# End of script